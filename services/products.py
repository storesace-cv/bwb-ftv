"""Utilities and service layer for product related operations."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List
import unicodedata

from openpyxl import load_workbook

from data.datastore import DataStore
from data.migration import setup_database
from domain import Product, Ingredient
from utils.paths import get_project_root


# Maps normalized header variants to canonical database column names.
HEADER_MAP: dict[str, str] = {
    "codigo": "codigo",
    "produto_codigo": "codigo",
    "codigo_do_produto": "codigo",
    "cod_produto": "codigo",
    "prod_venda": "codigo",
    "preco1_g": "preco1_g",
    "preco1": "preco1_g",
    "preco1g": "preco1_g",
    "preco2_g": "preco2_g",
    "preco2": "preco2_g",
    "preco2g": "preco2_g",
    "iva": "iva",
    "iva1": "iva",
    "iva_1": "iva",
}


def _normalize(text: str) -> str:
    """Return a normalized, ASCII-only, lower-case header name."""
    txt = unicodedata.normalize("NFD", str(text or ""))
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = txt.replace("-", "_").replace("/", "_").replace(" ", "_")
    txt = txt.replace("(", "").replace(")", "").replace(".", "")
    return txt.lower()


def sync_table_schema(conn, table: str, headers: list[str]) -> list[str]:
    """Synchronize SQLite table schema with headers from a spreadsheet.

    The ``headers`` are normalized (and mapped via :data:`HEADER_MAP` for
    ``produtos``) before being compared with existing table columns. Missing
    columns are added and obsolete ones trigger a table recreation so that the
    resulting schema matches the spreadsheet exactly.
    """

    cur = conn.cursor()

    norm_headers: list[str] = []
    for h in headers:
        nh = _normalize(h)
        if table == "produtos":
            nh = HEADER_MAP.get(nh, nh)
        norm_headers.append(nh)

    cur.execute(f"PRAGMA table_info({table})")
    info_rows = cur.fetchall()
    info = {row[1].lower(): {"type": row[2], "pk": row[5]} for row in info_rows}
    existing = set(info.keys())

    for h in norm_headers:
        if h and h not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {h}")
            info[h] = {"type": "", "pk": 0}

    existing = set(info.keys())
    missing = [c for c in existing if c not in norm_headers]

    if missing:
        col_defs = []
        for h in norm_headers:
            col_info = info.get(h, {})
            col_type = col_info.get("type") or ""
            col_def = h if not col_type else f"{h} {col_type}"
            if col_info.get("pk"):
                col_def += " PRIMARY KEY"
            col_defs.append(col_def)

        cur.execute(f"CREATE TABLE {table}_new ({', '.join(col_defs)})")
        common = [c for c in norm_headers if c in existing]
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
        self.conn = getattr(ds, "conn", None)

    # -- pagination / ids -------------------------------------------------
    def total(self) -> int:
        return self.ds.total()

    def codigo_at(self, idx: int):
        return self.ds.codigo_at(idx)

    # -- auxiliary tables -------------------------------------------------
    def list_tipos_artigos(self):
        return self.ds.list_tipos_artigos()

    def list_validade(self):
        return self.ds.list_validade()

    def list_temperaturas(self):
        return self.ds.list_temperaturas()

    def list_active_allergens(self):
        return self.ds.list_active_allergens()

    # -- product retrieval ------------------------------------------------
    def get_product_info(self, codigo: str) -> Product:
        return get_product_info(self.ds, codigo)

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
    """Retrieve product information, pvps and ingredients as a :class:`Product`."""
    info = ds.get_produto_info(codigo) if ds else {}
    pvps = ds.get_pvps(codigo) if ds else {}
    ing_rows = ds.get_ingredientes(codigo) if ds else []

    ingredients: List[Ingredient] = []
    for row in ing_rows:
        ingredients.append(
            Ingredient(
                name=row.get("nome")
                or row.get("ingrediente")
                or row.get("designacao")
                or "",
                quantity=row.get("qtd") or row.get("quantidade") or row.get("QTD") or 0,
                unit=row.get("unidade") or "",
                ppu=row.get("ppu"),
                total=row.get("total"),
                code=row.get("codigo"),
            )
        )

    return Product(
        code=info.get("codigo") or codigo,
        name=info.get("nome"),
        familia=info.get("familia"),
        subfamilia=info.get("subfamilia"),
        tipo_artigo_cod=info.get("tipo_artigo_cod"),
        validade_cod=info.get("validade_cod"),
        temperatura_cod=info.get("temperatura_cod"),
        pvps=pvps,
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


def import_from_excel(ds: DataStore | None = None) -> None:
    """Import product data from Excel files in ``<root>/imports``.

    The directory must contain ``FichasTecnicas_base.xlsx``,
    ``PreçosTaxas_base.xlsx`` and ``Produtos_Base.xlsx``. Existing data in
    ``produtos``, ``fichas_tecnicas`` e ``precos_taxas`` é limpo antes de
    carregar as novas linhas. A informação de preços é carregada para a tabela
    ``precos_taxas``.
    """

    base = get_project_root() / "imports"
    history_dir = base / "history"
    base.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "produtos": base / "Produtos_Base.xlsx",
        "fichas_tecnicas": base / "FichasTecnicas_base.xlsx",
        "precos_taxas": base / "PreçosTaxas_base.xlsx",
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

    cur = conn.cursor()
    for tbl in ("produtos", "fichas_tecnicas", "precos_taxas"):
        try:
            cur.execute(f"DELETE FROM {tbl}")
        except Exception:
            pass
    conn.commit()

    def _load_insert(file_path: Path, table: str) -> None:
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
        sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        data: list[tuple] = []
        for row in rows:
            row_map = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
            data.append(tuple(row_map.get(c) for c in cols))
        if data:
            conn.executemany(sql, data)
        wb.close()

    _load_insert(files["produtos"], "produtos")
    _load_insert(files["fichas_tecnicas"], "fichas_tecnicas")

    def _load_prices(file_path: Path) -> None:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            raw_headers = list(next(rows))
        except StopIteration:
            wb.close()
            return
        price_map = {
            "preco1_g": "preco_1",
            "preco1": "preco_1",
            "preco1g": "preco_1",
            "preco2_g": "preco_2",
            "preco2": "preco_2",
            "preco2g": "preco_2",
            "preco3_g": "preco_3",
            "preco3": "preco_3",
            "preco3g": "preco_3",
            "preco4_g": "preco_4",
            "preco4": "preco_4",
            "preco4g": "preco_4",
            "preco5_g": "preco_5",
            "preco5": "preco_5",
            "preco5g": "preco_5",
        }
        mapped = []
        for h in raw_headers:
            norm = _normalize(h)
            mapped.append(price_map.get(norm, HEADER_MAP.get(norm, h)))
        has_codigo = "codigo" in mapped
        existing = [
            r[1].lower() for r in conn.execute("PRAGMA table_info(precos_taxas)")
        ]
        headers = sync_table_schema(
            conn, "precos_taxas", mapped + [c for c in existing if c not in mapped]
        )
        if not has_codigo:
            wb.close()
            raise ValueError(
                "PreçosTaxas_base.xlsx missing 'codigo' column; found: "
                + ", ".join(mapped)
            )
        cols = [h for h in headers if h]
        if not cols:
            wb.close()
            return
        conn.execute("DELETE FROM precos_taxas")
        placeholders = ",".join(["?"] * len(cols))
        sql = f"INSERT INTO precos_taxas ({','.join(cols)}) VALUES ({placeholders})"
        data: list[tuple] = []
        for row in rows:
            row_map = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
            data.append(tuple(row_map.get(c) for c in cols))
        if data:
            conn.executemany(sql, data)
        wb.close()

    _load_prices(files["precos_taxas"])
    conn.commit()
    ds.reload_ids()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for fp in files.values():
        fp.rename(history_dir / f"{fp.name}.{timestamp}")


def update_from_excel(ds: DataStore | None = None) -> None:
    """Update product data from Excel files in ``<root>/imports``.

    A informação de preços de ``PreçosTaxas_base.xlsx`` é carregada para a
    tabela ``precos_taxas``.
    """

    base = get_project_root() / "imports"
    history_dir = base / "history"
    base.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "produtos": base / "Produtos_Base.xlsx",
        "fichas_tecnicas": base / "FichasTecnicas_base.xlsx",
        "precos_taxas": base / "PreçosTaxas_base.xlsx",
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
        if table == "fichas_tecnicas":
            insert_sql = (
                f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
            )
            grouped: dict[str, list[tuple]] = {}
            for row in rows:
                row_map = {
                    headers[i]: row[i] for i in range(min(len(headers), len(row)))
                }
                codigo = row_map.get("produto_codigo")
                if codigo is None:
                    continue
                grouped.setdefault(codigo, []).append(
                    tuple(row_map.get(c) for c in cols)
                )
            for codigo, data in grouped.items():
                conn.execute(
                    "DELETE FROM fichas_tecnicas WHERE produto_codigo=?",
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

    _upsert(files["produtos"], "produtos")
    _upsert(files["fichas_tecnicas"], "fichas_tecnicas")

    def _load_prices(file_path: Path) -> None:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            raw_headers = list(next(rows))
        except StopIteration:
            wb.close()
            return
        price_map = {
            "preco1_g": "preco_1",
            "preco1": "preco_1",
            "preco1g": "preco_1",
            "preco2_g": "preco_2",
            "preco2": "preco_2",
            "preco2g": "preco_2",
            "preco3_g": "preco_3",
            "preco3": "preco_3",
            "preco3g": "preco_3",
            "preco4_g": "preco_4",
            "preco4": "preco_4",
            "preco4g": "preco_4",
            "preco5_g": "preco_5",
            "preco5": "preco_5",
            "preco5g": "preco_5",
        }
        mapped = []
        for h in raw_headers:
            norm = _normalize(h)
            mapped.append(price_map.get(norm, HEADER_MAP.get(norm, h)))
        has_codigo = "codigo" in mapped
        existing = [
            r[1].lower() for r in conn.execute("PRAGMA table_info(precos_taxas)")
        ]
        headers = sync_table_schema(
            conn, "precos_taxas", mapped + [c for c in existing if c not in mapped]
        )
        if not has_codigo:
            wb.close()
            raise ValueError(
                "PreçosTaxas_base.xlsx missing 'codigo' column; found: "
                + ", ".join(mapped)
            )
        cols = [h for h in headers if h]
        if not cols:
            wb.close()
            return
        conn.execute("DELETE FROM precos_taxas")
        placeholders = ",".join(["?"] * len(cols))
        sql = f"INSERT INTO precos_taxas ({','.join(cols)}) VALUES ({placeholders})"
        data: list[tuple] = []
        for row in rows:
            row_map = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
            data.append(tuple(row_map.get(c) for c in cols))
        if data:
            conn.executemany(sql, data)
        wb.close()

    _load_prices(files["precos_taxas"])
    conn.commit()
    ds.reload_ids()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for fp in files.values():
        fp.rename(history_dir / f"{fp.name}.{timestamp}")


def _import_single_excel(path: Path, ds: DataStore | None) -> None:
    """Fallback import used for simple single-file spreadsheets.

    The sheet is expected to contain at least ``codigo`` and ``nome`` columns.
    Existing rows in ``produtos`` are removed before inserting new data.
    """

    ds = ds or DataStore()
    conn = getattr(ds, "conn", None)
    if conn is None:
        return

    setup_database(conn)

    def _normalize(text: str) -> str:
        txt = unicodedata.normalize("NFD", str(text or ""))
        txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
        txt = txt.replace("-", "_").replace("/", "_").replace(" ", "_")
        txt = txt.replace("(", "").replace(")", "").replace(".", "")
        return txt.lower()

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    try:
        headers = [_normalize(h) for h in next(rows)]
        headers = [HEADER_MAP.get(h, h) for h in headers]
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
    cur.execute("PRAGMA table_info(produtos)")
    db_cols = [r[1].lower() for r in cur.fetchall()]
    name_idx = (
        headers.index("nome") if "nome" in headers and "nome" in db_cols else None
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

    cur.execute("DELETE FROM produtos")
    cols = ["codigo"]
    if name_idx is not None:
        cols.append("nome")
    if p1_idx is not None:
        cols.append("preco1_g")
    if p2_idx is not None:
        cols.append("preco2_g")
    if iva_idx is not None:
        cols.append("iva")
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO produtos ({','.join(cols)}) VALUES ({placeholders})"

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

    def _normalize(text: str) -> str:
        txt = unicodedata.normalize("NFD", str(text or ""))
        txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
        txt = txt.replace("-", "_").replace("/", "_").replace(" ", "_")
        txt = txt.replace("(", "").replace(")", "").replace(".", "")
        return txt.lower()

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    try:
        headers = [_normalize(h) for h in next(rows)]
        headers = [HEADER_MAP.get(h, h) for h in headers]
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
    cur.execute("PRAGMA table_info(produtos)")
    db_cols = [r[1].lower() for r in cur.fetchall()]
    name_idx = (
        headers.index("nome") if "nome" in headers and "nome" in db_cols else None
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

    for row in rows:
        codigo = row[code_idx]
        if codigo is None:
            continue
        cur.execute("SELECT 1 FROM produtos WHERE codigo=?", (codigo,))
        exists = cur.fetchone() is not None
        if exists:
            updates = []
            params = []
            if name_idx is not None:
                updates.append("nome=?")
                params.append(row[name_idx])
            if p1_idx is not None:
                updates.append("preco1_g=?")
                params.append(row[p1_idx])
            if p2_idx is not None:
                updates.append("preco2_g=?")
                params.append(row[p2_idx])
            if iva_idx is not None:
                updates.append("iva=?")
                params.append(row[iva_idx])
            if updates:
                params.append(codigo)
                cur.execute(
                    f"UPDATE produtos SET {', '.join(updates)} WHERE codigo=?",
                    params,
                )
        else:
            cols = ["codigo"]
            vals = [codigo]
            if name_idx is not None:
                cols.append("nome")
                vals.append(row[name_idx])
            if p1_idx is not None:
                cols.append("preco1_g")
                vals.append(row[p1_idx])
            if p2_idx is not None:
                cols.append("preco2_g")
                vals.append(row[p2_idx])
            if iva_idx is not None:
                cols.append("iva")
                vals.append(row[iva_idx])
            placeholders = ",".join(["?"] * len(vals))
            cur.execute(
                f"INSERT INTO produtos ({','.join(cols)}) VALUES ({placeholders})",
                vals,
            )
    conn.commit()
    wb.close()
    ds.reload_ids()
