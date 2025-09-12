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
    ``produtos`` and ``fichas_tecnicas`` tables is cleared before loading the
    new rows. Price information is merged from ``PreçosTaxas_base.xlsx``.
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
    for tbl in ("produtos", "fichas_tecnicas"):
        try:
            cur.execute(f"DELETE FROM {tbl}")
        except Exception:
            pass
    conn.commit()

    def _normalize(text: str) -> str:
        txt = unicodedata.normalize("NFD", str(text or ""))
        txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
        txt = txt.replace("-", "_").replace("/", "_").replace(" ", "_")
        txt = txt.replace("(", "").replace(")", "").replace(".", "")
        return txt.lower()

    def _table_columns(table: str) -> list[str]:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return [r[1].lower() for r in cur.fetchall()]

    def _load_insert(file_path: Path, table: str) -> None:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            headers = [_normalize(h) for h in next(rows)]
            if table == "produtos":
                headers = [HEADER_MAP.get(h, h) for h in headers]
        except StopIteration:
            wb.close()
            return
        db_cols = _table_columns(table)
        if table == "fichas_tecnicas":
            if "total" in db_cols and "total" not in headers and "custo" in headers:
                headers = ["total" if h == "custo" else h for h in headers]
            elif "custo" in db_cols and "custo" not in headers and "total" in headers:
                headers = ["custo" if h == "total" else h for h in headers]
        cols = [h for h in headers if h]
        used_cols = [c for c in cols if c in db_cols]
        if not used_cols:
            wb.close()
            return
        placeholders = ",".join(["?"] * len(used_cols))
        sql = f"INSERT INTO {table} ({','.join(used_cols)}) VALUES ({placeholders})"
        data: list[tuple] = []
        for row in rows:
            row_map = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
            data.append(tuple(row_map.get(c) for c in used_cols))
        if data:
            conn.executemany(sql, data)
        wb.close()

    _load_insert(files["produtos"], "produtos")
    _load_insert(files["fichas_tecnicas"], "fichas_tecnicas")

    def _merge_prices(file_path: Path) -> None:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            headers = [_normalize(h) for h in next(rows)]
            headers = [HEADER_MAP.get(h, h) for h in headers]
        except StopIteration:
            wb.close()
            return
        db_cols = _table_columns("produtos")
        if "codigo" not in headers:
            wb.close()
            raise ValueError(
                "PreçosTaxas_base.xlsx missing 'codigo' column; found: "
                + ", ".join(headers)
            )
        idx_cod = headers.index("codigo")
        idx_p1 = (
            headers.index("preco1_g")
            if "preco1_g" in headers and "preco1_g" in db_cols
            else None
        )
        idx_p2 = (
            headers.index("preco2_g")
            if "preco2_g" in headers and "preco2_g" in db_cols
            else None
        )
        idx_iva = (
            headers.index("iva") if "iva" in headers and "iva" in db_cols else None
        )
        if idx_p1 is None and idx_p2 is None and idx_iva is None:
            wb.close()
            return
        cur2 = conn.cursor()
        for row in rows:
            codigo = row[idx_cod]
            if codigo is None:
                continue
            updates = []
            params = []
            if idx_p1 is not None:
                updates.append("preco1_g=?")
                params.append(row[idx_p1])
            if idx_p2 is not None:
                updates.append("preco2_g=?")
                params.append(row[idx_p2])
            if idx_iva is not None:
                updates.append("iva=?")
                params.append(row[idx_iva])
            params.append(codigo)
            cur2.execute(
                f"UPDATE produtos SET {', '.join(updates)} WHERE codigo=?",
                params,
            )
            if cur2.rowcount == 0:
                cols = ["codigo"]
                vals = [codigo]
                if idx_p1 is not None:
                    cols.append("preco1_g")
                    vals.append(row[idx_p1])
                if idx_p2 is not None:
                    cols.append("preco2_g")
                    vals.append(row[idx_p2])
                if idx_iva is not None:
                    cols.append("iva")
                    vals.append(row[idx_iva])
                placeholders = ",".join(["?"] * len(vals))
                cur2.execute(
                    f"INSERT INTO produtos ({','.join(cols)}) VALUES ({placeholders})",
                    vals,
                )
        wb.close()

    _merge_prices(files["precos_taxas"])
    conn.commit()
    ds.reload_ids()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for fp in files.values():
        fp.rename(history_dir / f"{fp.name}.{timestamp}")


def update_from_excel(ds: DataStore | None = None) -> None:
    """Update product data from Excel files in ``<root>/imports``."""

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

    def _normalize(text: str) -> str:
        txt = unicodedata.normalize("NFD", str(text or ""))
        txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
        txt = txt.replace("-", "_").replace("/", "_").replace(" ", "_")
        txt = txt.replace("(", "").replace(")", "").replace(".", "")
        return txt.lower()

    def _table_columns(table: str) -> list[str]:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return [r[1].lower() for r in cur.fetchall()]

    def _upsert(file_path: Path, table: str) -> None:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            headers = [_normalize(h) for h in next(rows)]
            if table == "produtos":
                headers = [HEADER_MAP.get(h, h) for h in headers]
        except StopIteration:
            wb.close()
            return
        db_cols = _table_columns(table)
        if table == "fichas_tecnicas":
            if "total" in db_cols and "total" not in headers and "custo" in headers:
                headers = ["total" if h == "custo" else h for h in headers]
            elif "custo" in db_cols and "custo" not in headers and "total" in headers:
                headers = ["custo" if h == "total" else h for h in headers]
        cols = [h for h in headers if h]
        used_cols = [c for c in cols if c in db_cols]
        if not used_cols:
            wb.close()
            return
        placeholders = ",".join(["?"] * len(used_cols))
        if table == "fichas_tecnicas":
            insert_sql = (
                f"INSERT INTO {table} ({','.join(used_cols)}) VALUES ({placeholders})"
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
                    tuple(row_map.get(c) for c in used_cols)
                )
            for codigo, data in grouped.items():
                conn.execute(
                    "DELETE FROM fichas_tecnicas WHERE produto_codigo=?",
                    (codigo,),
                )
                conn.executemany(insert_sql, data)
        else:
            sql = (
                f"INSERT OR REPLACE INTO {table} ({','.join(used_cols)}) "
                f"VALUES ({placeholders})"
            )
            data: list[tuple] = []
            for row in rows:
                row_map = {
                    headers[i]: row[i] for i in range(min(len(headers), len(row)))
                }
                data.append(tuple(row_map.get(c) for c in used_cols))
            if data:
                conn.executemany(sql, data)
        wb.close()

    _upsert(files["produtos"], "produtos")
    _upsert(files["fichas_tecnicas"], "fichas_tecnicas")

    def _merge_prices(file_path: Path) -> None:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            headers = [_normalize(h) for h in next(rows)]
            headers = [HEADER_MAP.get(h, h) for h in headers]
        except StopIteration:
            wb.close()
            return
        db_cols = _table_columns("produtos")
        if "codigo" not in headers:
            wb.close()
            raise ValueError(
                "PreçosTaxas_base.xlsx missing 'codigo' column; found: "
                + ", ".join(headers)
            )
        idx_cod = headers.index("codigo")
        idx_p1 = (
            headers.index("preco1_g")
            if "preco1_g" in headers and "preco1_g" in db_cols
            else None
        )
        idx_p2 = (
            headers.index("preco2_g")
            if "preco2_g" in headers and "preco2_g" in db_cols
            else None
        )
        idx_iva = (
            headers.index("iva") if "iva" in headers and "iva" in db_cols else None
        )
        if idx_p1 is None and idx_p2 is None and idx_iva is None:
            wb.close()
            return
        cur2 = conn.cursor()
        for row in rows:
            codigo = row[idx_cod]
            if codigo is None:
                continue
            updates = []
            params = []
            if idx_p1 is not None:
                updates.append("preco1_g=?")
                params.append(row[idx_p1])
            if idx_p2 is not None:
                updates.append("preco2_g=?")
                params.append(row[idx_p2])
            if idx_iva is not None:
                updates.append("iva=?")
                params.append(row[idx_iva])
            params.append(codigo)
            cur2.execute(
                f"UPDATE produtos SET {', '.join(updates)} WHERE codigo=?",
                params,
            )
            if cur2.rowcount == 0:
                cols = ["codigo"]
                vals = [codigo]
                if idx_p1 is not None:
                    cols.append("preco1_g")
                    vals.append(row[idx_p1])
                if idx_p2 is not None:
                    cols.append("preco2_g")
                    vals.append(row[idx_p2])
                if idx_iva is not None:
                    cols.append("iva")
                    vals.append(row[idx_iva])
                placeholders = ",".join(["?"] * len(vals))
                cur2.execute(
                    f"INSERT INTO produtos ({','.join(cols)}) VALUES ({placeholders})",
                    vals,
                )
        wb.close()

    _merge_prices(files["precos_taxas"])
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
