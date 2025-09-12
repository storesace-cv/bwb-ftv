"""Utilities and service layer for product related operations."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import unicodedata

from openpyxl import load_workbook

from data.datastore import DataStore
from domain import Product, Ingredient


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
    def import_from_excel(self, path: str) -> None:
        """Import data from Excel files located at ``path``.

        This simply proxies to :func:`import_from_excel` using the instance's
        :class:`~data.datastore.DataStore`.
        """
        import_from_excel(path, self.ds)

    def update_from_excel(self, path: str) -> None:
        """Update existing products from a spreadsheet.

        Rows are upserted into the ``produtos`` table based on ``codigo``.
        """
        update_from_excel(path, self.ds)


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


def import_from_excel(path: str, ds: DataStore | None = None) -> None:
    """Import product data from a set of Excel files.

    Parameters
    ----------
    path:
        Directory containing the Excel files ``FichasTecnicas_base.xlsx``,
        ``PreçosTaxas_base.xlsx`` and ``Produtos_Base.xlsx``.
    ds:
        Optional :class:`DataStore` to operate on. When omitted a new
        instance is created with default parameters.

    The function clears existing data from ``produtos``, ``fichas_tecnicas``
    and ``precos_taxas`` tables and loads the rows from the Excel files.
    Afterwards ``ds.reload_ids()`` is invoked so that any cached product
    codes are refreshed.
    """

    base = Path(path)
    if not base.exists():
        raise FileNotFoundError(path)

    # Accept passing the direct path to one of the files; in that case use
    # its parent directory as the base folder.
    if base.is_file():
        if base.suffix.lower() != ".xlsx":
            raise ValueError("path must have a .xlsx extension")
        # If the parent directory does not contain the expected base files,
        # treat this as the simple import case where ``path`` points directly
        # to a file with product information.
        parent = base.parent
        prod_file = parent / "Produtos_Base.xlsx"
        if prod_file.exists():
            base = parent
        else:
            _import_single_excel(base, ds)
            return

    # Resolve expected file names (handle possible Unicode normalisation of
    # "Preços").
    precos_candidates = [
        "PreçosTaxas_base.xlsx",
        "PreçosTaxas_base.xlsx",
        "PrecosTaxas_base.xlsx",
    ]
    files = {
        "produtos": base / "Produtos_Base.xlsx",
        "fichas_tecnicas": base / "FichasTecnicas_base.xlsx",
        "precos_taxas": None,
    }
    for cand in precos_candidates:
        p = base / cand
        if p.exists():
            files["precos_taxas"] = p
            break
    if files["precos_taxas"] is None:
        raise FileNotFoundError("PreçosTaxas_base.xlsx not found")

    for fp in files.values():
        if not fp.exists():
            raise FileNotFoundError(str(fp))
        if fp.suffix.lower() != ".xlsx":
            raise ValueError(f"{fp} is not an .xlsx file")

    ds = ds or DataStore()
    conn = getattr(ds, "conn", None)
    if conn is None:
        return

    cur = conn.cursor()
    for tbl in ("produtos", "fichas_tecnicas", "precos_taxas"):
        try:
            cur.execute(f"DELETE FROM {tbl}")
        except Exception:
            # Table might not exist; ignore silently for resilience
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
        except StopIteration:
            wb.close()
            return
        cols = [h for h in headers if h]
        db_cols = _table_columns(table)
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
    _load_insert(files["precos_taxas"], "precos_taxas")
    conn.commit()
    ds.reload_ids()


def update_from_excel(path: str, ds: DataStore | None = None) -> None:
    """Update product data from Excel files.

    ``path`` can point to a directory containing the three base files or to a
    single spreadsheet with product information.  When a simple spreadsheet is
    provided only the ``produtos`` table is affected.  In the base files case
    rows are upserted into ``produtos`` and ``precos_taxas`` and the
    ``fichas_tecnicas`` table is synchronised per product.
    """

    base = Path(path)
    if not base.exists():
        raise FileNotFoundError(path)

    if base.is_file():
        if base.suffix.lower() != ".xlsx":
            raise ValueError("path must have a .xlsx extension")
        parent = base.parent
        prod_file = parent / "Produtos_Base.xlsx"
        if prod_file.exists():
            base = parent
        else:
            _update_from_excel(base, ds)
            return

    precos_candidates = [
        "PreçosTaxas_base.xlsx",
        "PreçosTaxas_base.xlsx",
        "PrecosTaxas_base.xlsx",
    ]
    files = {
        "produtos": base / "Produtos_Base.xlsx",
        "fichas_tecnicas": base / "FichasTecnicas_base.xlsx",
        "precos_taxas": None,
    }
    for cand in precos_candidates:
        p = base / cand
        if p.exists():
            files["precos_taxas"] = p
            break
    if files["precos_taxas"] is None:
        raise FileNotFoundError("PreçosTaxas_base.xlsx not found")

    for fp in files.values():
        if not fp.exists():
            raise FileNotFoundError(str(fp))
        if fp.suffix.lower() != ".xlsx":
            raise ValueError(f"{fp} is not an .xlsx file")

    ds = ds or DataStore()
    conn = getattr(ds, "conn", None)
    if conn is None:
        return

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
        except StopIteration:
            wb.close()
            return
        cols = [h for h in headers if h]
        db_cols = _table_columns(table)
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
    _upsert(files["precos_taxas"], "precos_taxas")
    conn.commit()
    ds.reload_ids()


def _import_single_excel(path: Path, ds: DataStore | None) -> None:
    """Fallback import used for simple single-file spreadsheets.

    The sheet is expected to contain at least ``codigo`` and ``nome`` columns.
    Existing rows in ``produtos`` are removed before inserting new data.
    """

    ds = ds or DataStore()
    conn = getattr(ds, "conn", None)
    if conn is None:
        return

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    try:
        headers = [str(h).strip().lower() for h in next(rows)]
    except StopIteration:
        wb.close()
        return
    try:
        code_idx = headers.index("codigo")
    except ValueError:
        wb.close()
        return
    name_idx = headers.index("nome") if "nome" in headers else None

    cur = conn.cursor()
    cur.execute("DELETE FROM produtos")
    for row in rows:
        codigo = row[code_idx]
        nome = row[name_idx] if name_idx is not None else None
        cur.execute(
            "INSERT INTO produtos (codigo, nome) VALUES (?, ?)",
            (codigo, nome),
        )
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

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    try:
        headers = [str(h).strip().lower() for h in next(rows)]
    except StopIteration:
        wb.close()
        return
    try:
        code_idx = headers.index("codigo")
    except ValueError:
        wb.close()
        return
    name_idx = headers.index("nome") if "nome" in headers else None

    cur = conn.cursor()
    for row in rows:
        codigo = row[code_idx]
        nome = row[name_idx] if name_idx is not None else None
        cur.execute("SELECT 1 FROM produtos WHERE codigo=?", (codigo,))
        if cur.fetchone():
            cur.execute(
                "UPDATE produtos SET nome=? WHERE codigo=?",
                (nome, codigo),
            )
        else:
            cur.execute(
                "INSERT INTO produtos (codigo, nome) VALUES (?, ?)",
                (codigo, nome),
            )
    conn.commit()
    wb.close()
    ds.reload_ids()
