"""Utilities and service layer for product related operations."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator, List
import unicodedata
import re
from contextlib import closing, contextmanager
from openpyxl import load_workbook

from data.datastore import DataStore
from data.migration import setup_database
from domain import Product, Ingredient, FichaTecnica
from utils.paths import get_project_root
from utils.formatting import parse_decimal


logger = logging.getLogger(__name__)


# Historical header aliases have been removed. Imports now rely on
# spreadsheets using the canonical column names directly.

PRECO_GRAM_LOOKUP = {
    "preco1g": ("Preco1G", "Preco1"),
    "preco2g": ("Preco2G", "Preco2"),
    "preco3g": ("Preco3G", "Preco3"),
    "preco4g": ("Preco4G", "Preco4"),
    "preco5g": ("Preco5G", "Preco5"),
}

NUMERIC_NAMES = {
    "preco",
    "preco1_5",
    "preco1g",
    "preco2g",
    "preco3g",
    "preco4g",
    "preco5g",
    "ppu",
    "qtd",
    "peso",
    "iva",
    "iva1_2",
}


def _infer_cols(headers: list[str]):
    """Return indexes for required FichasTecnicas columns.

    Spreadsheets are expected to use the canonical column names directly,
    so this helper simply resolves their positions without considering
    alternative aliases. ``ComponenteCodigo`` is optional and may be absent,
    in which case ``None`` is returned for its index.
    """

    idx = {h: i for i, h in enumerate(headers)}
    return (
        idx["ProdutoCodigo"],
        idx["ComponenteNome"],
        idx["Qtd"],
        idx["Unidade"],
        idx.get("ComponenteCodigo"),
    )


def canonicalize_header(text: str, table: str | None = None) -> str:
    """Return a canonical CamelCase column name for a spreadsheet header."""

    txt = str(text or "")
    txt = txt.replace("(não necessário p/ importar)", "")
    txt_norm = unicodedata.normalize("NFD", txt)
    txt_norm = "".join(c for c in txt_norm if unicodedata.category(c) != "Mn")
    txt_norm = re.sub(r"[^0-9A-Za-z]+", " ", txt_norm).strip()
    key = "".join(txt_norm.lower().split())

    if key == "produtocodigo":
        return (
            "ProdutoCodigo"
            if table in {"FichasTecnicas", "ProdutoPreparacao"}
            else "Codigo"
        )
    if key in {"preco15", "preco1_5"}:
        return "Preco1_5"
    if key in {"iva12", "iva1_2"}:
        return "Iva1_2"
    if key in PRECO_GRAM_LOOKUP:
        preco_g, preco = PRECO_GRAM_LOOKUP[key]
        return preco_g if table == "Produtos" else preco

    # Preserve existing camel-case headers not matched above
    if txt_norm and re.search(r"[A-Z]", txt_norm[1:]) and " " not in txt_norm:
        return txt_norm[0].upper() + txt_norm[1:]

    return "".join(word.capitalize() for word in txt_norm.split())


def sync_table_schema(conn, table: str, headers: list[str]) -> list[str]:
    """Synchronize SQLite table schema with headers from a spreadsheet.

    The ``headers`` are canonicalized before being compared with existing table
    columns. Missing columns are added and obsolete ones trigger a table
    recreation so that the resulting schema matches the spreadsheet exactly.
    """

    cur = conn.cursor()

    norm_headers: list[str] = [canonicalize_header(h, table=table) for h in headers]

    cur.execute(f"PRAGMA table_info({table})")
    info_rows = cur.fetchall()
    info = {
        row[1].lower(): {"orig": row[1], "type": row[2], "pk": row[5]}
        for row in info_rows
    }
    existing = set(info.keys())

    for h in norm_headers:
        key = h.lower()
        if h and key not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {h}")
            info[key] = {"orig": h, "type": "", "pk": 0}
            existing.add(key)

    missing = [c for c in existing if c not in {h.lower() for h in norm_headers}]

    if missing:
        col_defs = []
        for h in norm_headers:
            col_info = info.get(h.lower(), {})
            name = col_info.get("orig", h)
            col_type = col_info.get("type") or ""
            col_def = name if not col_type else f"{name} {col_type}"
            if col_info.get("pk"):
                col_def += " PRIMARY KEY"
            col_defs.append(col_def)

        cur.execute(f"CREATE TABLE {table}_new ({', '.join(col_defs)})")
        common = [info[h.lower()]["orig"] for h in norm_headers if h.lower() in info]
        if common:
            cols = ",".join(common)
            cur.execute(f"INSERT INTO {table}_new ({cols}) SELECT {cols} FROM {table}")
        cur.execute(f"DROP TABLE {table}")
        cur.execute(f"ALTER TABLE {table}_new RENAME TO {table}")

    conn.commit()
    return norm_headers


class ProductService:
    """High level API used by the UI to interact with products and helpers."""

    def __init__(self, ds: DataStore):
        self.ds = ds

    @property
    def conn(self):  # pragma: no cover - simple delegation
        """Return the current database connection from the datastore."""
        return getattr(self.ds, "conn", None)

    # -- pagination / ids -------------------------------------------------
    def total(self) -> int:
        return self.ds.total()

    def codigo_at(self, idx: int):
        return self.ds.codigo_at(idx)

    # -- auxiliary tables -------------------------------------------------
    def list_tipos_artigos(self) -> list[tuple[int, str]]:
        return self.ds.list_tipos_artigos()

    def list_validade(self) -> list[tuple[int, str]]:
        return self.ds.list_validade()

    def list_temperaturas(self) -> list[tuple[int, str]]:
        return self.ds.list_temperaturas()

    def list_active_allergens(self):
        return self.ds.list_active_allergens()

    def set_tipo_artigo(self, codigo: str, tipo_cod) -> bool:
        return self.ds.set_tipo_artigo(codigo, tipo_cod)

    def set_validade(self, codigo: str, validade_cod) -> bool:
        return self.ds.set_validade(codigo, validade_cod)

    def set_temperatura(self, codigo: str, temperatura_cod) -> bool:
        return self.ds.set_temperatura(codigo, temperatura_cod)

    # -- product retrieval ------------------------------------------------
    def get_product_info(self, codigo: str) -> Product:
        return get_product_info(self.ds, codigo)

    def list_fichas_tecnicas(self, codigo: str) -> list[FichaTecnica]:
        """Return technical sheet rows for ``codigo`` as dataclasses."""

        rows = self.ds.get_ingredientes(codigo)
        fichas: list[FichaTecnica] = []
        for row in rows:
            name = row.get("ComponenteNome") or ""
            if not name:
                logger.warning(
                    "[ProductService] Nome do ingrediente vazio em %s: %s",
                    codigo,
                    row,
                )
            fichas.append(
                FichaTecnica(
                    ingredient=name,
                    quantity=row.get("Qtd") or 0,
                    unit=row.get("Unidade") or "",
                    ppu=row.get("Ppu"),
                    total=row.get("Preco"),
                    code=row.get("ComponenteCodigo"),
                )
            )
        return fichas

    # -- cost calculations ------------------------------------------------
    def calculate_cost(
        self, product_or_ingredients: Iterable[Ingredient] | Product
    ) -> float:
        """Calculate total cost from a Product or iterable of Ingredients."""
        if isinstance(product_or_ingredients, Product):
            ingredients = product_or_ingredients.ingredients
        else:
            ingredients = list(product_or_ingredients)
        return calculate_cost(ingredients)

    # -- bulk import ------------------------------------------------------
    def import_from_excel(self) -> None:
        """Import data from Excel files located in the project ``imports`` folder."""

        import_from_excel(self.ds)

    def update_from_excel(self) -> None:
        """Update existing products from spreadsheets in the ``imports`` folder."""

        update_from_excel(self.ds)


def get_product_info(ds: DataStore, codigo: str) -> Product:
    """Retrieve product information, price info and ingredients as a :class:`Product`."""
    info = ds.get_produto_info(codigo) if ds else {}
    pvps: dict[str, float | None] = ds.get_pvps(codigo) if ds else {}
    pvp = pvps.get("pvp")
    iva = pvps.get("iva")
    ing_rows = ds.get_ingredientes(codigo) if ds else []

    ingredients: List[Ingredient] = []
    for row in ing_rows:
        name = row.get("ComponenteNome") or ""
        if not name:
            logger.warning(
                "[ProductService] Nome do ingrediente vazio em %s: %s",
                codigo,
                row,
            )
        ingredients.append(
            Ingredient(
                name=name,
                quantity=row.get("Qtd") or 0,
                unit=row.get("Unidade") or "",
                ppu=row.get("Ppu"),
                total=row.get("Preco"),
                code=row.get("ComponenteCodigo"),
            )
        )

    return Product(
        code=info.get("codigo") or codigo,
        name=info.get("produto"),
        familia=info.get("familia"),
        subfamilia=info.get("subfamilia"),
        tipo_artigo_cod=info.get("tipoartigo"),
        validade_cod=info.get("validade"),
        temperatura_cod=info.get("temperatura"),
        pvp=pvp,
        iva=iva,
        ingredients=ingredients,
    )


def calculate_cost(ingredients: Iterable[Ingredient]) -> float:
    """Return total cost for a list/iterable of ingredients."""
    total = 0.0
    for ing in ingredients:
        if ing.total is not None:
            try:
                total += float(ing.total)
                continue
            except (TypeError, ValueError):
                pass
        if ing.ppu is not None:
            try:
                total += float(ing.ppu) * float(ing.quantity)
            except (TypeError, ValueError):
                pass
    return total


@contextmanager
def _load_workbook_rows(
    path: Path, table: str, conn
) -> Iterator[tuple[list[str], Iterable[tuple], set[str]]]:
    """Yield canonicalized headers, row iterator and numeric columns for a sheet."""

    with closing(load_workbook(path, read_only=True, data_only=True)) as wb:
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            raw_headers = list(next(rows))
        except StopIteration:
            yield [], iter(()), set()
            return
        headers = [canonicalize_header(h, table=table) for h in raw_headers]
        numeric_cols = {
            r[1]
            for r in conn.execute(f"PRAGMA table_info({table})")
            if r[2]
            and any(t in r[2].upper() for t in ("REAL", "INT", "NUM", "DEC", "FLOAT"))
        }
        numeric_cols.update(c for c in headers if c and c.lower() in NUMERIC_NAMES)
        yield headers, rows, numeric_cols


def import_from_excel(ds: DataStore | None = None) -> None:
    """Import product data from Excel files in ``<root>/imports``.

    The directory must contain ``FichasTecnicas_base.xlsx``,
    ``PreçosTaxas_base.xlsx`` and ``Produtos_Base.xlsx``. Existing data in
    ``Produtos``, ``FichasTecnicas`` e ``PrecosTaxas`` é limpo antes de
    carregar as novas linhas. A informação de preços é carregada para a tabela
    ``PrecosTaxas``.
    """

    base = get_project_root() / "imports"
    base.mkdir(parents=True, exist_ok=True)

    files = {
        "Produtos": base / "Produtos_Base.xlsx",
        "FichasTecnicas": base / "FichasTecnicas_base.xlsx",
        "PrecosTaxas": base / "PreçosTaxas_base.xlsx",
    }
    missing = [fp.name for fp in files.values() if not fp.exists()]
    if missing:
        raise FileNotFoundError("Missing import files: " + ", ".join(sorted(missing)))
    for fp in files.values():
        if fp.suffix.lower() != ".xlsx":
            raise ValueError(f"{fp} is not an .xlsx file")

    ds = ds or DataStore()
    conn = getattr(ds, "conn", None)
    if conn is None:
        return

    setup_database(conn)
    for table, fp in files.items():
        with closing(load_workbook(fp, read_only=True, data_only=True)) as wb:
            ws = wb.active
            rows = ws.iter_rows(values_only=True)
            try:
                raw_headers = list(next(rows))
            except StopIteration:
                continue
            if table == "PrecosTaxas":
                mapped = [canonicalize_header(h, table=table) for h in raw_headers]
                existing = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
                headers = mapped + [c for c in existing if c not in mapped]
            else:
                headers = raw_headers
            sync_table_schema(conn, table, headers)

    cur = conn.cursor()
    for tbl in ("Produtos", "FichasTecnicas", "PrecosTaxas"):
        try:
            cur.execute(f"DELETE FROM {tbl}")
        except Exception:
            pass
    conn.commit()

    def _load_insert(file_path: Path, table: str) -> None:
        with _load_workbook_rows(file_path, table, conn) as (
            headers,
            rows,
            numeric_cols,
        ):
            headers = sync_table_schema(conn, table, headers)
            cols = [h for h in headers if h]
            if not cols:
                return
            placeholders = ",".join(["?"] * len(cols))
            sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
            data: list[tuple] = []
            for row in rows:
                row_map = {}
                for i in range(min(len(headers), len(row))):
                    col = headers[i]
                    val = row[i]
                    if col in numeric_cols:
                        val = parse_decimal(val)
                    row_map[col] = val
                data.append(tuple(row_map.get(c) for c in cols))
            if data:
                conn.executemany(sql, data)

    _load_insert(files["Produtos"], "Produtos")
    _load_insert(files["FichasTecnicas"], "FichasTecnicas")

    def _load_prices(file_path: Path) -> None:
        with _load_workbook_rows(file_path, "PrecosTaxas", conn) as (
            headers,
            rows,
            numeric_cols,
        ):
            rows = list(rows)
            if "Loja" not in headers:
                headers.append("Loja")
                rows = [tuple(list(r) + ["1"]) for r in rows]
            if "Codigo" not in headers:
                raise ValueError(
                    "PreçosTaxas_base.xlsx missing 'Codigo' column; found: "
                    + ", ".join(headers)
                )
            existing = [r[1] for r in conn.execute("PRAGMA table_info(PrecosTaxas)")]
            headers = sync_table_schema(
                conn, "PrecosTaxas", headers + [c for c in existing if c not in headers]
            )
            cols = [h for h in headers if h]
            if not cols:
                return
            conn.execute("DELETE FROM PrecosTaxas")
            placeholders = ",".join(["?"] * len(cols))
            sql = f"INSERT INTO PrecosTaxas ({','.join(cols)}) VALUES ({placeholders})"
            data: list[tuple] = []
            for row in rows:
                row_map = {}
                for i in range(min(len(headers), len(row))):
                    col = headers[i]
                    val = row[i]
                    if col in numeric_cols:
                        val = parse_decimal(val)
                    row_map[col] = val
                data.append(tuple(row_map.get(c) for c in cols))
            if data:
                conn.executemany(sql, data)

    _load_prices(files["PrecosTaxas"])
    conn.commit()
    ds.reload_ids()

    for fp in files.values():
        content = fp.read_bytes()
        conn.execute(
            "INSERT INTO Uploads (Filename, Content) VALUES (?, ?)",
            (fp.name, sqlite3.Binary(content)),
        )
        fp.unlink()
    conn.commit()


def update_from_excel(ds: DataStore | None = None) -> None:
    """Update product data from Excel files in ``<root>/imports``.

    A informação de preços de ``PreçosTaxas_base.xlsx`` é carregada para a
    tabela ``PrecosTaxas``.
    """

    base = get_project_root() / "imports"
    base.mkdir(parents=True, exist_ok=True)

    files = {
        "Produtos": base / "Produtos_Base.xlsx",
        "FichasTecnicas": base / "FichasTecnicas_base.xlsx",
        "PrecosTaxas": base / "PreçosTaxas_base.xlsx",
    }
    missing = [fp.name for fp in files.values() if not fp.exists()]
    if missing:
        raise FileNotFoundError("Missing import files: " + ", ".join(sorted(missing)))
    for fp in files.values():
        if fp.suffix.lower() != ".xlsx":
            raise ValueError(f"{fp} is not an .xlsx file")

    ds = ds or DataStore()
    conn = getattr(ds, "conn", None)
    if conn is None:
        return

    setup_database(conn)

    def _upsert(file_path: Path, table: str) -> None:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            headers = list(next(rows))
        except StopIteration:
            wb.close()
            return
        headers = sync_table_schema(conn, table, headers)
        cols = [h for h in headers if h]
        if not cols:
            wb.close()
            return
        placeholders = ",".join(["?"] * len(cols))
        if table == "FichasTecnicas":
            insert_sql = (
                f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
            )
            grouped: dict[str, list[tuple]] = {}
            for row in rows:
                row_map = {
                    headers[i]: row[i] for i in range(min(len(headers), len(row)))
                }
                codigo = row_map.get("ProdutoCodigo")
                if codigo is None:
                    continue
                grouped.setdefault(codigo, []).append(
                    tuple(row_map.get(c) for c in cols)
                )
            for codigo, data in grouped.items():
                conn.execute(
                    "DELETE FROM FichasTecnicas WHERE ProdutoCodigo=?",
                    (codigo,),
                )
                conn.executemany(insert_sql, data)
        else:
            sql = (
                f"INSERT OR REPLACE INTO {table} ({','.join(cols)}) "
                f"VALUES ({placeholders})"
            )
            data: list[tuple] = []
            for row in rows:
                row_map = {
                    headers[i]: row[i] for i in range(min(len(headers), len(row)))
                }
                data.append(tuple(row_map.get(c) for c in cols))
            if data:
                conn.executemany(sql, data)
        wb.close()

    _upsert(files["Produtos"], "Produtos")
    _upsert(files["FichasTecnicas"], "FichasTecnicas")

    def _load_prices(file_path: Path) -> None:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            raw_headers = list(next(rows))
        except StopIteration:
            wb.close()
            return
        rows = list(rows)
        mapped = [canonicalize_header(h, table="PrecosTaxas") for h in raw_headers]
        if "Loja" not in mapped:
            mapped.append("Loja")
            rows = [tuple(list(r) + ["1"]) for r in rows]
        has_codigo = "Codigo" in mapped
        existing = [r[1] for r in conn.execute("PRAGMA table_info(PrecosTaxas)")]
        headers = sync_table_schema(
            conn, "PrecosTaxas", mapped + [c for c in existing if c not in mapped]
        )
        if not has_codigo:
            wb.close()
            raise ValueError(
                "PreçosTaxas_base.xlsx missing 'Codigo' column; found: "
                + ", ".join(mapped)
            )
        cols = [h for h in headers if h]
        if not cols:
            wb.close()
            return
        numeric_cols = {
            r[1]
            for r in conn.execute("PRAGMA table_info(PrecosTaxas)")
            if r[2]
            and any(t in r[2].upper() for t in ("REAL", "INT", "NUM", "DEC", "FLOAT"))
        }
        conn.execute("DELETE FROM PrecosTaxas")
        placeholders = ",".join(["?"] * len(cols))
        sql = f"INSERT INTO PrecosTaxas ({','.join(cols)}) VALUES ({placeholders})"
        data: list[tuple] = []
        for row in rows:
            row_map = {}
            for i in range(min(len(headers), len(row))):
                col = headers[i]
                val = row[i]
                if col in numeric_cols:
                    val = parse_decimal(val)
                row_map[col] = val
            data.append(tuple(row_map.get(c) for c in cols))
        if data:
            conn.executemany(sql, data)
        wb.close()

    _load_prices(files["PrecosTaxas"])
    conn.commit()
    ds.reload_ids()

    for fp in files.values():
        content = fp.read_bytes()
        conn.execute(
            "INSERT INTO Uploads (Filename, Content) VALUES (?, ?)",
            (fp.name, sqlite3.Binary(content)),
        )
        fp.unlink()
    conn.commit()


def _import_single_excel(path: Path, ds: DataStore | None) -> None:
    """Fallback import used for simple single-file spreadsheets.

    The sheet is expected to contain at least ``codigo`` and ``nome`` columns.
    Existing rows in ``Produtos`` are removed before inserting new data.
    """

    ds = ds or DataStore()
    conn = getattr(ds, "conn", None)
    if conn is None:
        return

    setup_database(conn)

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    try:
        headers = [canonicalize_header(h, table="Produtos") for h in next(rows)]
    except StopIteration:
        wb.close()
        return
    if "codigo" not in headers:
        wb.close()
        raise ValueError(
            "Spreadsheet missing 'codigo' column; found: " + ", ".join(headers)
        )
    code_idx = headers.index("codigo")
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(Produtos)")
    db_cols = [r[1].lower() for r in cur.fetchall()]
    name_idx = (
        headers.index("produto")
        if "produto" in headers and "produto" in db_cols
        else None
    )
    p1_idx = (
        headers.index("preco1_g")
        if "preco1_g" in headers and "preco1_g" in db_cols
        else None
    )
    p2_idx = (
        headers.index("preco2_g")
        if "preco2_g" in headers and "preco2_g" in db_cols
        else None
    )
    iva_idx = headers.index("iva") if "iva" in headers and "iva" in db_cols else None

    cur.execute("DELETE FROM Produtos")
    cols = ["Codigo"]
    if name_idx is not None:
        cols.append("Produto")
    if p1_idx is not None:
        cols.append("Preco1G")
    if p2_idx is not None:
        cols.append("Preco2G")
    if iva_idx is not None:
        cols.append("Iva")
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO Produtos ({','.join(cols)}) VALUES ({placeholders})"

    for row in rows:
        codigo = row[code_idx]
        if codigo is None:
            continue
        vals = [codigo]
        if name_idx is not None:
            vals.append(row[name_idx])
        if p1_idx is not None:
            vals.append(row[p1_idx])
        if p2_idx is not None:
            vals.append(row[p2_idx])
        if iva_idx is not None:
            vals.append(row[iva_idx])
        cur.execute(sql, vals)
    conn.commit()
    wb.close()
    ds.reload_ids()


def _update_from_excel(path: Path, ds: DataStore | None) -> None:
    """Upsert products from a simple spreadsheet."""

    if not path.exists():
        raise FileNotFoundError(str(path))
    if path.suffix.lower() != ".xlsx":
        raise ValueError("path must have a .xlsx extension")

    ds = ds or DataStore()
    conn = getattr(ds, "conn", None)
    if conn is None:
        return

    setup_database(conn)

    with _load_workbook_rows(path, "Produtos", conn) as (
        headers,
        rows,
        numeric_cols,
    ):
        if "Codigo" not in headers:
            raise ValueError(
                "Spreadsheet missing 'Codigo' column; found: " + ", ".join(headers)
            )
        code_idx = headers.index("Codigo")

        cur = conn.cursor()
        cur.execute("PRAGMA table_info(Produtos)")
        db_cols = [r[1] for r in cur.fetchall()]
        if "Produto" in headers and "Produto" not in db_cols:
            cur.execute("ALTER TABLE Produtos ADD COLUMN Produto")
            db_cols.append("Produto")
        name_idx = (
            headers.index("Produto")
            if "Produto" in headers and "Produto" in db_cols
            else None
        )
        p1_idx = (
            headers.index("Preco1G")
            if "Preco1G" in headers and "Preco1G" in db_cols
            else None
        )
        p2_idx = (
            headers.index("Preco2G")
            if "Preco2G" in headers and "Preco2G" in db_cols
            else None
        )
        iva_idx = (
            headers.index("Iva") if "Iva" in headers and "Iva" in db_cols else None
        )

        for row in rows:
            codigo = row[code_idx]
            if codigo is None:
                continue
            cur.execute("SELECT 1 FROM Produtos WHERE Codigo=?", (codigo,))
            exists = cur.fetchone() is not None
            if exists:
                updates = []
                params = []
                if name_idx is not None:
                    updates.append("Produto=?")
                    params.append(row[name_idx])
                if p1_idx is not None:
                    val = row[p1_idx]
                    if headers[p1_idx] in numeric_cols:
                        val = parse_decimal(val)
                    updates.append("Preco1G=?")
                    params.append(val)
                if p2_idx is not None:
                    val = row[p2_idx]
                    if headers[p2_idx] in numeric_cols:
                        val = parse_decimal(val)
                    updates.append("Preco2G=?")
                    params.append(val)
                if iva_idx is not None:
                    val = row[iva_idx]
                    if headers[iva_idx] in numeric_cols:
                        val = parse_decimal(val)
                    updates.append("Iva=?")
                    params.append(val)
                if updates:
                    params.append(codigo)
                    cur.execute(
                        f"UPDATE Produtos SET {', '.join(updates)} WHERE Codigo=?",
                        params,
                    )
            else:
                cols = ["Codigo"]
                vals = [codigo]
                if name_idx is not None:
                    cols.append("Produto")
                    vals.append(row[name_idx])
                if p1_idx is not None:
                    val = row[p1_idx]
                    if headers[p1_idx] in numeric_cols:
                        val = parse_decimal(val)
                    cols.append("Preco1G")
                    vals.append(val)
                if p2_idx is not None:
                    val = row[p2_idx]
                    if headers[p2_idx] in numeric_cols:
                        val = parse_decimal(val)
                    cols.append("Preco2G")
                    vals.append(val)
                if iva_idx is not None:
                    val = row[iva_idx]
                    if headers[iva_idx] in numeric_cols:
                        val = parse_decimal(val)
                    cols.append("Iva")
                    vals.append(val)
                placeholders = ",".join(["?"] * len(vals))
                cur.execute(
                    f"INSERT INTO Produtos ({','.join(cols)}) VALUES ({placeholders})",
                    vals,
                )
    conn.commit()
    ds.reload_ids()
