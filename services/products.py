"""Utilities and service layer for product related operations."""

from __future__ import annotations

import inspect
import logging
import sqlite3
from collections.abc import Iterable as IterableABC
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping
import unicodedata
import re
import time
from contextlib import closing, contextmanager
from PIL import Image, UnidentifiedImageError
from openpyxl import Workbook, load_workbook

from data.backup import create_backup, restore_backup
from data.datastore import DataStore
from data.header_map import HEADER_MAP, allowed_headers_for
from data.migration import setup_database
from data.repositories import quote_ident
from domain import Product, Ingredient, FichaTecnica
from utils.paths import get_project_root
from utils.formatting import parse_decimal


logger = logging.getLogger(__name__)


BACKUP_PREFIX_FOR_UPDATES = "ftv-actualizacao-"


_UNSET = object()


IMPORT_FILE_BASENAMES = {
    "Produtos": "Produtos_Base.xlsx",
    "FichasTecnicas": "FichasTecnicas_base.xlsx",
    "PrecosTaxas": "PreçosTaxas_base.xlsx",
}


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
    "preco1",
    "preco2",
    "preco3",
    "preco4",
    "preco5",
    "preco1g",
    "preco2g",
    "preco3g",
    "preco4g",
    "preco5g",
    "ppu",
    "qtd",
    "peso",
    "iva",
    "iva1",
    "iva2",
}


def _is_blank(value: Any) -> bool:
    """Return ``True`` if ``value`` should be treated as missing data."""

    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


_FALLBACK_COMPONENT_MARK = "__fallback__"


def _normalize_code(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    text = str(value).strip()
    return text or None


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_ordem(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return str(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            numeric = float(value)
        except ValueError:
            return value
        else:
            if numeric.is_integer():
                return str(int(numeric))
            return value
    return str(value)


def _ingredient_key(row: Mapping[str, Any]) -> tuple[Any, Any]:
    produto = _normalize_code(row.get("ProdutoCodigo"))
    componente_codigo = _normalize_code(row.get("ComponenteCodigo"))
    if componente_codigo:
        return (produto, componente_codigo)

    componente_nome = _normalize_text(row.get("ComponenteNome"))
    ordem = _normalize_ordem(row.get("Ordem"))
    return (produto, (_FALLBACK_COMPONENT_MARK, componente_nome, ordem))


def canonicalize_header(text: str, table: str | None = None) -> str:
    """Return a canonical CamelCase column name for a spreadsheet header."""

    txt = str(text or "")
    txt = txt.replace("(não necessário p/ importar)", "")
    txt_norm = unicodedata.normalize("NFD", txt)
    txt_norm = "".join(c for c in txt_norm if unicodedata.category(c) != "Mn")
    txt_norm = re.sub(r"[^0-9A-Za-z]+", " ", txt_norm).strip()
    key = "".join(txt_norm.lower().split())

    if key == "produtocodigo":
        result = (
            "ProdutoCodigo"
            if table in {"FichasTecnicas", "ProdutoPreparacao"}
            else "Codigo"
        )
    elif key in {"preco15", "preco1_5"}:
        result = "Preco1"
    elif key == "iva1" or re.fullmatch(r"iva\s*1", txt_norm.lower()):
        result = "Iva1"
    elif key == "iva2" or re.fullmatch(r"iva\s*2", txt_norm.lower()):
        result = "Iva2"
    elif key in {"preco1", "preco2", "preco3", "preco4", "preco5"}:
        result = f"Preco{key[-1]}"
    elif key == "uninvvmmpg":
        result = "UnInvVMMMPG"
    elif key in PRECO_GRAM_LOOKUP:
        preco_g, preco = PRECO_GRAM_LOOKUP[key]
        result = preco_g if table == "Produtos" else preco
    elif txt_norm and re.search(r"[A-Z]", txt_norm[1:]) and " " not in txt_norm:
        # Preserve existing camel-case headers not matched above
        result = txt_norm[0].upper() + txt_norm[1:]
    else:
        result = "".join(word.capitalize() for word in txt_norm.split())

    if table:
        mapping = HEADER_MAP.get(table, {})
        if mapping and result in mapping:
            result = mapping[result]
        allowed = allowed_headers_for(table)
        if allowed and result and result not in allowed:
            allowed_list = ", ".join(sorted(allowed))
            raise ValueError(
                "Cabeçalho inesperado para a tabela "
                f"{table}: '{text}' → '{result}'. "
                "Cabeçalhos permitidos: "
                f"{allowed_list}"
            )

    return result


def sync_table_schema(conn, table: str, headers: list[str]) -> list[str]:
    """Synchronize SQLite table schema with headers from a spreadsheet.

    The ``headers`` are canonicalized before being compared with existing table
    columns. Missing columns are added and obsolete ones trigger a table
    recreation so that the resulting schema matches the spreadsheet exactly.
    """

    cur = conn.cursor()

    norm_headers: list[str] = [
        canonicalize_header(h, table=table) for h in headers
    ]

    cur.execute(f"PRAGMA table_info({quote_ident(table)})")
    info_rows = cur.fetchall()
    info = {
        row[1].lower(): {"orig": row[1], "type": row[2], "pk": row[5]}
        for row in info_rows
    }
    existing = set(info.keys())

    for h in norm_headers:
        key = h.lower()
        if h and key not in existing:
            cur.execute(
                f"ALTER TABLE {quote_ident(table)} ADD COLUMN {quote_ident(h)}"
            )
            info[key] = {"orig": h, "type": "", "pk": 0}
            existing.add(key)

    missing = [
        c
        for c in existing
        if c not in {h.lower() for h in norm_headers}
    ]

    if missing:
        headers_lower = [h.lower() for h in norm_headers]
        pk_order = [
            row[1]
            for row in sorted(info_rows, key=lambda r: r[5])
            if row[5] > 0 and row[1].lower() in headers_lower
        ]
        multi_pk = len(pk_order) > 1

        col_defs = []
        for h in norm_headers:
            col_info = info.get(h.lower(), {})
            name = col_info.get("orig", h)
            col_type = col_info.get("type") or ""
            col_name = quote_ident(name)
            col_def = col_name if not col_type else f"{col_name} {col_type}"
            if col_info.get("pk") and not multi_pk:
                if "PRIMARY KEY" not in col_type.upper():
                    col_def += " PRIMARY KEY"
            col_defs.append(col_def)

        if multi_pk:
            pk_cols = [quote_ident(name) for name in pk_order]
            if pk_cols:
                col_defs.append(f"PRIMARY KEY ({', '.join(pk_cols)})")

        new_table = f"{table}_new"
        cur.execute(
            f"CREATE TABLE {quote_ident(new_table)} ({', '.join(col_defs)})"
        )
        common = [
            info[h.lower()]["orig"]
            for h in norm_headers
            if h.lower() in info
        ]
        if common:
            cols = ",".join(quote_ident(c) for c in common)
            cur.execute(
                f"INSERT INTO {quote_ident(new_table)} ({cols}) "
                f"SELECT {cols} FROM {quote_ident(table)}"
            )
        cur.execute(f"DROP TABLE {quote_ident(table)}")
        cur.execute(
            f"ALTER TABLE {quote_ident(new_table)} "
            f"RENAME TO {quote_ident(table)}"
        )

    conn.commit()
    return norm_headers


def get_image_path(codigo: str) -> Path:
    """Return the path for the product image of ``codigo``."""

    root = get_project_root()
    img_dir = root / "databases" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir / f"{codigo}.png"


def save_product_image(codigo: str, src_path: str | Path) -> Path | None:
    """Save ``src_path`` as the product image for ``codigo``.

    The image is resized to fit within 600×600 and stored as PNG in the
    ``databases/images`` directory.  Returns ``None`` if the image could not
    be processed.
    """

    dest = get_image_path(codigo)
    try:
        with Image.open(src_path) as img:
            img.thumbnail((600, 600))
            img.info.pop("icc_profile", None)
            img.save(dest, format="PNG")
    except (OSError, UnidentifiedImageError) as exc:  # pragma: no cover - logs
        logger.error("[ProductService] Failed to save image %s: %s", src_path, exc)
        return None
    return dest


def delete_product_image(codigo: str) -> Path | None:
    """Archive and remove the image for ``codigo`` if it exists."""

    path = get_image_path(codigo)
    if path.exists():
        ts = int(time.time())
        backup = path.with_name(f"{codigo}.{ts}.png")
        try:
            path.rename(backup)
        except OSError as exc:  # pragma: no cover - logs
            logger.error(
                "[ProductService] Failed to archive image %s: %s", path, exc
            )
            return None
        return backup
    return None


def get_preparacao_image_path(codigo: str, idx: int) -> Path:
    """Return the path for a preparation step image."""

    root = get_project_root()
    img_dir = root / "databases" / "images" / "preparacoes"
    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir / f"{codigo}-{idx}.png"


def save_preparacao_image(
    codigo: str, idx: int, src_path: str | Path
) -> Path | None:
    """Save ``src_path`` as the image for a preparation step.

    Returns ``None`` if the image could not be processed."""

    dest = get_preparacao_image_path(codigo, idx)
    try:
        with Image.open(src_path) as img:
            img.thumbnail((600, 600))
            img.info.pop("icc_profile", None)
            img.save(dest, format="PNG")
    except (OSError, UnidentifiedImageError) as exc:  # pragma: no cover - logs
        logger.error(
            "[ProductService] Failed to save prep image %s: %s", src_path, exc
        )
        return None
    return dest


def delete_preparacao_image(codigo: str, idx: int) -> Path | None:
    """Archive and remove a preparation step image if it exists."""

    path = get_preparacao_image_path(codigo, idx)
    if path.exists():
        ts = int(time.time())
        backup = path.with_name(f"{codigo}-{idx}.{ts}.png")
        try:
            path.rename(backup)
        except OSError as exc:  # pragma: no cover - logs
            logger.error(
                "[ProductService] Failed to archive prep image %s: %s", path, exc
            )
            return None
        return backup
    return None


def _row_to_ingredient(row: dict, codigo: str) -> Ingredient:
    """Convert a raw ingredient ``row`` into an :class:`Ingredient`.

    Shared by different product retrieval helpers to ensure consistent
    handling of missing names and automatic total calculation.
    """

    name = row.get("ComponenteNome") or ""
    if not name:
        logger.warning(
            "[ProductService] Nome do ingrediente vazio em %s: %s",
            codigo,
            row,
        )
    quantity = row.get("Qtd") or 0
    ppu = row.get("Ppu")
    total = row.get("Preco")
    weight = row.get("Peso")
    if total is None and ppu is not None:
        try:
            total = float(ppu) * float(quantity)
        except (TypeError, ValueError):
            total = None
    return Ingredient(
        name=name,
        quantity=quantity,
        unit=row.get("Unidade") or "",
        ppu=ppu,
        total=total,
        code=row.get("ComponenteCodigo"),
        weight=weight,
    )


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

    def set_search_filters(
        self,
        *,
        produto: str | None = None,
        ingrediente: str | None = None,
        familia: object = _UNSET,
        subfamilia: object = _UNSET,
    ) -> None:
        if hasattr(self.ds, "set_search_filters"):
            kwargs = {
                "produto": produto,
                "ingrediente": ingrediente,
            }

            def _coerce_selection(value: object) -> tuple[str, ...] | None:
                if value is None:
                    return None

                def _normalize(entry: object) -> str | None:
                    if entry is None:
                        return None
                    text = str(entry).strip()
                    return text or None

                if isinstance(value, (str, bytes)):
                    cleaned = _normalize(value)
                    return (cleaned,) if cleaned else None

                if isinstance(value, IterableABC):
                    collected: list[str] = []
                    seen: set[str] = set()
                    for entry in value:
                        cleaned = _normalize(entry)
                        if cleaned is None:
                            continue
                        key = cleaned.casefold()
                        if key in seen:
                            continue
                        seen.add(key)
                        collected.append(cleaned)
                    return tuple(collected) if collected else None

                cleaned = _normalize(value)
                return (cleaned,) if cleaned else None

            if familia is not _UNSET:
                coerced = _coerce_selection(familia)
                kwargs["familia"] = coerced
            if subfamilia is not _UNSET:
                coerced = _coerce_selection(subfamilia)
                kwargs["subfamilia"] = coerced
            self.ds.set_search_filters(**kwargs)

    def list_families_with_subfamilies(self) -> dict[str, tuple[str, ...]]:
        if hasattr(self.ds, "list_families_with_subfamilies"):
            return self.ds.list_families_with_subfamilies()
        if hasattr(self.ds, "list_family_hierarchy"):
            return self.ds.list_family_hierarchy()
        return {}

    def list_family_hierarchy(self) -> dict[str, tuple[str, ...]]:
        return self.list_families_with_subfamilies()

    # -- auxiliary tables -------------------------------------------------
    def list_tipos_artigos(self) -> list[tuple[int, str]]:
        return self.ds.list_tipos_artigos()

    def list_validade(self) -> list[tuple[int, str]]:
        return self.ds.list_validade()

    def list_temperaturas(self) -> list[tuple[int, str]]:
        return self.ds.list_temperaturas()

    def list_active_allergens(self):
        return self.ds.list_active_allergens()

    def get_allergen_details(self, aid):
        return self.ds.get_allergen_details(aid)

    def get_product_allergens(self, codigo: str) -> list[int]:
        return self.ds.get_product_allergens(codigo)

    def set_product_allergens(
        self, codigo: str, allergen_ids: Iterable[int | str | None]
    ) -> bool:
        return self.ds.set_product_allergens(codigo, allergen_ids)

    def set_tipo_artigo(self, codigo: str, tipo_cod) -> bool:
        return self.ds.set_tipo_artigo(codigo, tipo_cod)

    def set_validade(self, codigo: str, validade_cod) -> bool:
        return self.ds.set_validade(codigo, validade_cod)

    def set_temperatura(self, codigo: str, temperatura_cod) -> bool:
        return self.ds.set_temperatura(codigo, temperatura_cod)

    # -- images ---------------------------------------------------------
    def get_image_path(self, codigo: str) -> Path:
        return get_image_path(codigo)

    def save_product_image(self, codigo: str, src_path: str | Path) -> Path | None:
        return save_product_image(codigo, src_path)

    def delete_product_image(self, codigo: str) -> Path | None:
        return delete_product_image(codigo)

    def get_preparacao_image_path(self, codigo: str, idx: int) -> Path:
        return get_preparacao_image_path(codigo, idx)

    def save_preparacao_image(
        self, codigo: str, idx: int, src_path: str | Path
    ) -> Path | None:
        return save_preparacao_image(codigo, idx, src_path)

    def delete_preparacao_image(self, codigo: str, idx: int) -> Path | None:
        return delete_preparacao_image(codigo, idx)

    # -- product retrieval ------------------------------------------------
    def get_product_info(self, codigo: str) -> Product:
        return get_product_info(self.ds, codigo)

    def list_fichas_tecnicas(self, codigo: str) -> list[FichaTecnica]:
        """Return technical sheet rows for ``codigo`` as dataclasses."""

        rows = self.ds.get_ingredientes(codigo)
        return [
            FichaTecnica(
                ingredient=ing.name,
                quantity=ing.quantity,
                unit=ing.unit,
                ppu=ing.ppu,
                total=ing.total,
                code=ing.code,
                weight=ing.weight,
            )
            for row in rows
            for ing in [_row_to_ingredient(row, codigo)]
        ]

    # -- cost calculations ------------------------------------------------
    def calculate_cost(
        self,
        product_or_ingredients: Iterable[Ingredient] | Product,
        *,
        include_skipped: bool = False,
    ) -> float | tuple[float, list[dict[str, Any]]]:
        """Calculate total cost from a Product or iterable of Ingredients."""
        if isinstance(product_or_ingredients, Product):
            ingredients = product_or_ingredients.ingredients
        else:
            ingredients = list(product_or_ingredients)
        return calculate_cost(ingredients, include_skipped=include_skipped)

    # -- bulk import ------------------------------------------------------
    def import_from_excel(self) -> None:
        """Import data from Excel files located in the project ``imports``
        folder."""

        import_from_excel(self.ds)

    def update_from_excel(self) -> Path | None:
        """Update existing products from spreadsheets in the ``imports``
        folder."""

        backup_path: Path | None = None
        if self._should_create_backup():
            conn = getattr(self.ds, "conn", None)
            if conn is not None:
                try:
                    conn.commit()
                except sqlite3.Error as exc:
                    logger.debug(
                        "[ProductService] Falha a executar commit antes do backup: %s",
                        exc,
                        exc_info=True,
                    )
            try:
                backup_path = create_backup(prefix=BACKUP_PREFIX_FOR_UPDATES)
            except Exception as exc:
                logger.exception(
                    "[ProductService] Falha ao criar backup antes da atualização: %s",
                    exc,
                )
                raise
        try:
            return update_from_excel(self.ds)
        except Exception:
            conn = getattr(self.ds, "conn", None)
            db_path: str | None = None
            if conn is not None:
                try:
                    rows = conn.execute("PRAGMA database_list").fetchall()
                except sqlite3.Error as exc:
                    logger.debug(
                        "[ProductService] Não foi possível obter caminhos da BD: %s",
                        exc,
                        exc_info=True,
                    )
                    rows = []
                for row in rows or []:
                    try:
                        _, name, file_path = row
                    except (ValueError, TypeError):
                        continue
                    if name == "main" and file_path not in {"", ":memory:"}:
                        db_path = file_path
                        break
            close_fn = getattr(self.ds, "close", None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception as exc:
                    logger.debug(
                        "[ProductService] Falha ao fechar DataStore após erro: %s",
                        exc,
                        exc_info=True,
                    )
            elif conn is not None:
                try:
                    conn.close()
                except sqlite3.Error as exc:
                    logger.debug(
                        "[ProductService] Falha ao fechar ligação SQLite após erro: %s",
                        exc,
                        exc_info=True,
                    )
            if backup_path is not None:
                try:
                    restore_backup(backup_path)
                except Exception as exc:
                    logger.exception(
                        "[ProductService] Falha ao restaurar backup após erro: %s",
                        exc,
                    )
                else:
                    logger.info(
                        "[ProductService] Base de dados restaurada a partir de %s",
                        backup_path,
                    )
            new_ds: DataStore | None = None
            ds_type = type(self.ds)
            ds_kwargs: dict[str, Any] = {}
            if db_path:
                ds_kwargs["db_path"] = db_path
            try:
                sig = inspect.signature(ds_type.__init__)
            except (TypeError, ValueError):
                sig = None
            params: set[str] = set()
            if sig is not None:
                params = {name for name in sig.parameters if name != "self"}
            if "demo" in params and hasattr(self.ds, "demo"):
                ds_kwargs["demo"] = getattr(self.ds, "demo")
            prompt_cb = getattr(self.ds, "_prompt", None)
            if prompt_cb is None and hasattr(self.ds, "prompt"):
                prompt_cb = getattr(self.ds, "prompt")
            if "prompt" in params and prompt_cb is not None:
                ds_kwargs["prompt"] = prompt_cb
            try:
                new_ds = ds_type(**ds_kwargs)
            except Exception as exc:
                logger.debug(
                    "[ProductService] Falha a reinstanciar %s: %s",
                    ds_type.__name__,
                    exc,
                    exc_info=True,
                )
                if ds_type is not DataStore:
                    fallback_kwargs = {
                        key: value
                        for key, value in ds_kwargs.items()
                        if key in {"db_path", "demo", "prompt"}
                    }
                    try:
                        new_ds = DataStore(**fallback_kwargs)
                    except Exception as fallback_exc:
                        logger.debug(
                            "[ProductService] Falha na recuperação com DataStore: %s",
                            fallback_exc,
                            exc_info=True,
                        )
            if new_ds is not None:
                self.ds = new_ds
            if hasattr(self.ds, "reload_ids"):
                try:
                    self.ds.reload_ids()
                except Exception as exc:
                    logger.debug(
                        "[ProductService] reload_ids falhou após restauro: %s",
                        exc,
                        exc_info=True,
                    )
            raise

    def _should_create_backup(self) -> bool:
        conn = getattr(self.ds, "conn", None)
        if conn is None:
            return False
        try:
            rows = conn.execute("PRAGMA database_list").fetchall()
        except sqlite3.Error as exc:
            logger.debug(
                "[ProductService] Não foi possível obter informação da base de dados: %s",
                exc,
                exc_info=True,
            )
            return False
        for _, name, file_path in rows:
            if name == "main":
                return bool(file_path) and file_path not in {"", ":memory:"}
        return False


def get_product_info(ds: DataStore, codigo: str) -> Product:
    """Return product details, prices and ingredients as a :class:`Product`."""
    info = ds.get_produto_info(codigo) if ds else {}
    pvps: dict[str, list[float | None] | float | None] = (
        ds.get_pvps(codigo) if ds else {}
    )
    precos_taxas_row = ds.get_precos_taxas_row(codigo) if ds else {}
    prices = pvps.get("pvps") or []
    iva = pvps.get("iva")
    ing_rows = ds.get_ingredientes(codigo) if ds else []

    ingredients = [_row_to_ingredient(row, codigo) for row in ing_rows]

    additional_info = None
    if isinstance(info, dict):
        normalized_keys: dict[str, Any] = {}
        for key, value in info.items():
            if isinstance(key, str):
                normalized_keys[key.lower()] = value
        for alias in (
            "informacaoadicional",
            "informacao_adicional",
            "informacaoextra",
            "informacaoadic",
        ):
            if alias in info:
                additional_info = info.get(alias)
                break
            if alias in normalized_keys:
                additional_info = normalized_keys.get(alias)
                break

    tipo_artigo_cod = info.get("tipoartigo") if isinstance(info, Mapping) else None
    validade_cod = info.get("validade") if isinstance(info, Mapping) else None
    temperatura_cod = info.get("temperatura") if isinstance(info, Mapping) else None

    def _lookup_description(table: str, value: Any) -> str:
        if value in (None, ""):
            return ""
        conn = getattr(ds, "conn", None)
        if conn is None:
            return ""
        try:
            cur = conn.execute(
                f"SELECT Descricao FROM {table} WHERE Cod = ?", (value,)
            )
            row = cur.fetchone()
        except sqlite3.Error as exc:
            logger.debug(
                "[ProductService] lookup falhou em %s para valor %r: %s",
                table,
                value,
                exc,
                exc_info=True,
            )
            return ""
        if not row:
            return ""
        try:
            description = row["Descricao"]
        except (KeyError, TypeError):
            try:
                description = row[0]
            except (IndexError, TypeError):
                description = None
        return str(description) if description not in (None, "") else ""

    preparacao_html = ""
    if ds:
        try:
            html_value = ds.get_preparacao_html(codigo)
        except Exception:  # pragma: no cover - defensive guard
            html_value = ""
        if isinstance(html_value, str):
            preparacao_html = html_value
        elif html_value is None:
            preparacao_html = ""
        else:
            preparacao_html = str(html_value)

    return Product(
        code=info.get("codigo") or codigo,
        name=info.get("produto"),
        familia=info.get("familia"),
        subfamilia=info.get("subfamilia"),
        informacao_adicional=additional_info,
        tipo_artigo_cod=tipo_artigo_cod,
        tipo_artigo_desc=_lookup_description("TiposArtigos", tipo_artigo_cod),
        validade_cod=validade_cod,
        validade_desc=_lookup_description("Validade", validade_cod),
        temperatura_cod=temperatura_cod,
        temperatura_desc=_lookup_description("Temperaturas", temperatura_cod),
        produto_preparacao_html=preparacao_html,
        pvps=prices,
        iva=iva,
        ingredients=ingredients,
        produtos_row=dict(info) if isinstance(info, dict) else None,
        fichas_tecnicas_rows=list(ing_rows),
        precos_taxas_row=dict(precos_taxas_row)
        if isinstance(precos_taxas_row, dict)
        else None,
    )


def calculate_cost(
    ingredients: Iterable[Ingredient], *, include_skipped: bool = False
) -> float | tuple[float, list[dict[str, Any]]]:
    """Return total cost for a list/iterable of ingredients.

    When ``include_skipped`` is ``True`` the function returns a tuple with the
    total cost and a list describing ingredients that could not be processed
    because of invalid numeric inputs.
    """

    total = 0.0
    skipped: list[dict[str, Any]] = []

    for ing in ingredients:
        identifier = ing.name or ing.code or "<unknown>"
        if ing.total is not None:
            try:
                total += float(ing.total)
                continue
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "[ProductService] Invalid total for %s: %r (%s)",
                    identifier,
                    ing.total,
                    exc,
                )
                if include_skipped:
                    skipped.append(
                        {
                            "ingredient": ing,
                            "identifier": identifier,
                            "stage": "total",
                            "fields": {"total": ing.total},
                            "error": str(exc),
                        }
                    )
        if ing.ppu is not None:
            try:
                quantity = float(ing.quantity)
                total += float(ing.ppu) * quantity
            except (TypeError, ValueError) as exc:
                logger.debug(
                    "[ProductService] Invalid unit cost for %s: ppu=%r quantity=%r (%s)",
                    identifier,
                    ing.ppu,
                    ing.quantity,
                    exc,
                )
                if include_skipped:
                    skipped.append(
                        {
                            "ingredient": ing,
                            "identifier": identifier,
                            "stage": "ppu",
                            "fields": {
                                "ppu": ing.ppu,
                                "quantity": ing.quantity,
                            },
                            "error": str(exc),
                        }
                    )

    if include_skipped:
        return total, skipped
    return total


def calculate_food_cost(total, pvp, iva, product: str | None = None):
    """Return food cost percentage for given total cost and PVP.

    Parameters
    ----------
    total : float | int | str
        Total cost of ingredients.
    pvp : float | int | str
        Product sale price including VAT.
    iva : float | int | str
        VAT percentage (e.g., ``23`` for 23%).
    product : str | None, optional
        Product code or name used in warning messages.

    Returns
    -------
    float | None
        Percentage representing the food cost, or ``None`` when any input is
        invalid or zero.
    """
    # Validate inputs before attempting any numeric conversion. ``None`` or
    # empty string values should short-circuit the calculation without
    # emitting warnings, as they often arise from incomplete data entry.
    for name, value in {"total": total, "pvp": pvp, "iva": iva}.items():
        if value is None or value == "":
            if product:
                logger.debug("%s is missing for %s", name, product)
            else:
                logger.debug("%s is missing", name)
            return None

    try:
        total = float(total)
        pvp = float(pvp)
        iva = float(iva)
    except (TypeError, ValueError) as exc:
        if product:
            logger.warning(
                "invalid numeric value for total, pvp or iva in %s: %s",
                product,
                exc,
            )
        else:
            logger.warning(
                "invalid numeric value for total, pvp or iva: %s",
                exc,
            )
        return None

    if pvp <= 0:
        if product:
            logger.debug("pvp must be greater than zero for %s", product)
        else:
            logger.debug("pvp must be greater than zero")
        return None

    try:
        pvp_sem_iva = pvp / (1 + iva / 100)
    except (ZeroDivisionError, TypeError) as exc:
        if product:
            logger.warning(
                "cannot compute pvp without IVA for %s: %s", product, exc
            )
        else:
            logger.warning("cannot compute pvp without IVA: %s", exc)
        return None
    if pvp_sem_iva == 0:
        if product:
            logger.warning("pvp without IVA is zero for %s", product)
        else:
            logger.warning("pvp without IVA is zero")
        return None
    return (total / pvp_sem_iva) * 100


@contextmanager
def _load_workbook_rows(
    path: Path, table: str, conn
) -> Iterator[tuple[list[str], Iterable[tuple], set[str]]]:
    """Yield canonicalized headers, row iterator and numeric columns for a
    sheet."""

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
            for r in conn.execute(f"PRAGMA table_info({quote_ident(table)})")
            if r[2]
            and any(
                t in r[2].upper()
                for t in ("REAL", "INT", "NUM", "DEC", "FLOAT")
            )
        }
        numeric_cols.update(
            c for c in headers if c and c.lower() in NUMERIC_NAMES
        )
        yield headers, rows, numeric_cols


def import_from_excel(ds: DataStore | None = None) -> None:
    """Import product data from Excel files in ``<root>/imports``.

    The directory must contain ``FichasTecnicas_base.xlsx``,
    ``PreçosTaxas_base.xlsx`` and ``Produtos_Base.xlsx``. Existing data in
    ``Produtos``, ``FichasTecnicas`` e ``PrecosTaxas`` é limpo antes de
    carregar as novas linhas. A informação de preços é carregada para a tabela
    ``PrecosTaxas``.
    """

    ds = ds or DataStore()

    with _manage_import_files(ds) as files:
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
                    mapped = [
                        canonicalize_header(h, table=table) for h in raw_headers
                    ]
                    existing = [
                        r[1]
                        for r in conn.execute(
                            f"PRAGMA table_info({quote_ident(table)})"
                        )
                    ]
                    headers = mapped + [c for c in existing if c not in mapped]
                else:
                    headers = raw_headers
                sync_table_schema(conn, table, headers)

        cur = conn.cursor()
        for tbl in ("Produtos", "FichasTecnicas", "PrecosTaxas"):
            try:
                cur.execute(f"DELETE FROM {quote_ident(tbl)}")
            except sqlite3.Error as exc:
                logger.warning("failed to delete data from %s: %s", tbl, exc)
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
                cols_sql = ",".join(quote_ident(c) for c in cols)
                sql = (
                    f"INSERT INTO {quote_ident(table)} ({cols_sql}) VALUES ({placeholders})"
                )
                data: list[tuple] = []
                id_col = None
                if table == "FichasTecnicas":
                    id_col = "ProdutoCodigo"
                elif table == "Produtos":
                    id_col = "Codigo"
                last_identifier = None
                for row in rows:
                    row_map = {}
                    for i in range(min(len(headers), len(row))):
                        col = headers[i]
                        val = row[i]
                        if col in numeric_cols:
                            val = parse_decimal(val)
                        row_map[col] = val
                    if id_col:
                        identifier = row_map.get(id_col)
                        if isinstance(identifier, str):
                            stripped = identifier.strip()
                            if not stripped:
                                if table == "Produtos":
                                    continue
                                if last_identifier is None:
                                    continue
                                identifier = last_identifier
                            else:
                                identifier = stripped
                            row_map[id_col] = identifier
                        elif _is_blank(identifier):
                            if table == "Produtos":
                                continue
                            if last_identifier is None:
                                continue
                            identifier = last_identifier
                            row_map[id_col] = identifier
                        last_identifier = identifier
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
                existing = [
                    r[1]
                    for r in conn.execute(
                        f"PRAGMA table_info({quote_ident('PrecosTaxas')})"
                    )
                ]
                headers = sync_table_schema(
                    conn,
                    "PrecosTaxas",
                    headers + [c for c in existing if c not in headers],
                )
                cols = [h for h in headers if h]
                if not cols:
                    return
                conn.execute(f"DELETE FROM {quote_ident('PrecosTaxas')}")
                placeholders = ",".join(["?"] * len(cols))
                cols_sql = ",".join(quote_ident(c) for c in cols)
                sql = (
                    f"INSERT INTO {quote_ident('PrecosTaxas')} ({cols_sql}) "
                    f"VALUES ({placeholders})"
                )
                data: list[tuple] = []
                for row in rows:
                    row_map = {}
                    for i in range(min(len(headers), len(row))):
                        col = headers[i]
                        val = row[i]
                        if col in numeric_cols:
                            val = parse_decimal(val)
                        row_map[col] = val
                    codigo = row_map.get("Codigo")
                    if isinstance(codigo, str):
                        stripped = codigo.strip()
                        if not stripped:
                            continue
                        row_map["Codigo"] = stripped
                    elif _is_blank(codigo):
                        continue
                    data.append(tuple(row_map.get(c) for c in cols))
                if data:
                    conn.executemany(sql, data)

        _load_prices(files["PrecosTaxas"])
        conn.commit()
        ds.reload_ids()



@contextmanager
def _manage_import_files(
    ds: DataStore | None,
) -> Iterator[dict[str, Path]]:
    base = get_project_root() / "imports"
    base.mkdir(parents=True, exist_ok=True)

    files = {
        table: base / filename
        for table, filename in IMPORT_FILE_BASENAMES.items()
    }
    missing = [fp.name for fp in files.values() if not fp.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing import files: " + ", ".join(sorted(missing))
        )
    for fp in files.values():
        if fp.suffix.lower() != ".xlsx":
            raise ValueError(f"{fp} is not an .xlsx file")

    try:
        yield files
    except Exception:
        raise
    else:
        conn = getattr(ds, "conn", None)
        if conn is None:
            return
        for fp in files.values():
            content = fp.read_bytes()
            conn.execute(
                "INSERT INTO Uploads (Filename, Content) VALUES (?, ?)",
                (fp.name, sqlite3.Binary(content)),
            )
            fp.unlink()
        conn.commit()


def _snapshot_tables(
    conn: sqlite3.Connection,
) -> tuple[
    dict[Any, dict[str, Any]],
    dict[Any, dict[str, Any]],
    dict[Any, dict[str, Any]],
]:
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {col: row[col] for col in row.keys()}

    def _snapshot(
        table: str,
        key_columns: Iterable[str],
        *,
        key_builder=None,
    ) -> dict[Any, dict[str, Any]]:
        snapshot: dict[Any, dict[str, Any]] = {}
        try:
            existing_rows = conn.execute(
                f"SELECT * FROM {quote_ident(table)}"
            ).fetchall()
        except sqlite3.Error:
            return snapshot
        for row in existing_rows:
            row_dict = _row_to_dict(row)
            if key_builder is not None:
                key = key_builder(row_dict)
            else:
                key_vals = tuple(
                    row_dict.get(col) for col in key_columns if col in row_dict
                )
                if not key_vals:
                    continue
                key = key_vals[0] if len(key_vals) == 1 else key_vals
            snapshot[key] = row_dict
        return snapshot

    produtos_snapshot = _snapshot("Produtos", ("Codigo",))
    fichas_snapshot = _snapshot(
        "FichasTecnicas",
        ("ProdutoCodigo", "ComponenteCodigo", "Ordem"),
        key_builder=_ingredient_key,
    )
    precos_snapshot = _snapshot("PrecosTaxas", ("Codigo", "Loja"))

    produtos_state = {k: dict(v) for k, v in produtos_snapshot.items()}
    fichas_state = {k: dict(v) for k, v in fichas_snapshot.items()}
    precos_state = {k: dict(v) for k, v in precos_snapshot.items()}

    return produtos_state, fichas_state, precos_state


def _collect_changes(
    new_data: dict[str, Any],
    existing: dict[str, Any] | None,
    *,
    key_fields: set[str],
    include_keys_when_new: bool = False,
) -> list[tuple[str, Any, Any]]:
    changes: list[tuple[str, Any, Any]] = []
    if existing is None:
        for col, new_val in new_data.items():
            if col in key_fields and not include_keys_when_new:
                continue
            if col in key_fields and include_keys_when_new:
                changes.append((col, None, new_val))
            elif col not in key_fields:
                changes.append((col, None, new_val))
        return changes
    for col, new_val in new_data.items():
        if col in key_fields:
            continue
        old_val = existing.get(col)
        if old_val != new_val:
            changes.append((col, old_val, new_val))
    return changes


def _apply_updates(
    conn: sqlite3.Connection,
    ds: DataStore,
    files: dict[str, Path],
    produtos_state: dict[Any, dict[str, Any]],
    fichas_state: dict[Any, dict[str, Any]],
    precos_state: dict[Any, dict[str, Any]],
) -> list[dict[str, Any]]:
    report_entries: list[dict[str, Any]] = []

    def _record_change(
        change_type: str,
        table: str,
        product: Any,
        *,
        component_code: Any | None = None,
        component_name: Any | None = None,
        changes: list[tuple[str, Any, Any]] | None = None,
    ) -> None:
        if not changes:
            return
        report_entries.append(
            {
                "type": change_type,
                "table": table,
                "product": product,
                "component_code": component_code,
                "component_name": component_name,
                "changes": changes,
            }
        )

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
            cols_sql = ",".join(quote_ident(c) for c in cols)
            insert_sql = (
                f"INSERT INTO {quote_ident(table)} ({cols_sql}) VALUES ({placeholders})"
            )
            grouped: dict[str, list[tuple]] = {}
            last_codigo: str | None = None
            for row in rows:
                row_map = {
                    headers[i]: row[i]
                    for i in range(min(len(headers), len(row)))
                }
                codigo = row_map.get("ProdutoCodigo")
                if isinstance(codigo, str):
                    codigo = codigo.strip()
                    if not codigo:
                        codigo = None
                if _is_blank(codigo):
                    codigo = last_codigo
                if codigo is None:
                    continue
                row_map["ProdutoCodigo"] = codigo
                last_codigo = codigo
                componente = row_map.get("ComponenteCodigo")
                if isinstance(componente, str):
                    componente = componente.strip() or None
                row_map["ComponenteCodigo"] = componente
                row_data = {c: row_map.get(c) for c in cols}
                key = _ingredient_key(row_data)
                existing = fichas_state.get(key)
                changes = _collect_changes(
                    row_data,
                    existing,
                    key_fields={"ProdutoCodigo"},
                    include_keys_when_new=True,
                )
                if existing is None:
                    _record_change(
                        "Novo Ingrediente",
                        "FichasTecnicas",
                        codigo,
                        component_code=row_data.get("ComponenteCodigo"),
                        component_name=row_data.get("ComponenteNome"),
                        changes=changes,
                    )
                elif changes:
                    _record_change(
                        "Atualização de Ingrediente",
                        "FichasTecnicas",
                        codigo,
                        component_code=row_data.get("ComponenteCodigo"),
                        component_name=row_data.get("ComponenteNome"),
                        changes=changes,
                    )
                updated = dict(existing or {})
                updated.update(row_data)
                fichas_state[key] = updated
                grouped.setdefault(codigo, []).append(
                    tuple(row_data.get(c) for c in cols)
                )
            for codigo, data in grouped.items():
                conn.execute(
                    f"DELETE FROM {quote_ident('FichasTecnicas')} "
                    f"WHERE {quote_ident('ProdutoCodigo')}=?",
                    (codigo,),
                )
                conn.executemany(insert_sql, data)
        else:
            cols_sql = ",".join(quote_ident(c) for c in cols)
            sql = (
                f"INSERT OR REPLACE INTO {quote_ident(table)} ({cols_sql}) "
                f"VALUES ({placeholders})"
            )
            id_col = "Codigo" if table in {"Produtos", "PrecosTaxas"} else None
            for row in rows:
                row_map = {
                    headers[i]: row[i]
                    for i in range(min(len(headers), len(row)))
                }
                identifier = None
                if id_col:
                    identifier = row_map.get(id_col)
                    if isinstance(identifier, str):
                        identifier = identifier.strip()
                        if not identifier:
                            identifier = None
                    if _is_blank(identifier):
                        identifier = None
                    if identifier is None:
                        continue
                    row_map[id_col] = identifier
                row_data = {c: row_map.get(c) for c in cols}
                if table == "Produtos":
                    existing = produtos_state.get(identifier)
                    changes = _collect_changes(
                        row_data,
                        existing,
                        key_fields={"Codigo"},
                        include_keys_when_new=True,
                    )
                    if existing is None:
                        _record_change(
                            "Novo Registo",
                            "Produtos",
                            identifier,
                            changes=changes,
                        )
                    elif changes:
                        _record_change(
                            "Atualização de Registo",
                            "Produtos",
                            identifier,
                            changes=changes,
                        )
                    updated = dict(existing or {})
                    updated.update(row_data)
                    produtos_state[identifier] = updated
                conn.execute(sql, tuple(row_data.get(c) for c in cols))
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
        mapped = [
            canonicalize_header(h, table="PrecosTaxas") for h in raw_headers
        ]
        if "Loja" not in mapped:
            mapped.append("Loja")
            rows = [tuple(list(r) + ["1"]) for r in rows]
        has_codigo = "Codigo" in mapped
        existing = [
            r[1]
            for r in conn.execute(
                f"PRAGMA table_info({quote_ident('PrecosTaxas')})"
            )
        ]
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
            for r in conn.execute(
                f"PRAGMA table_info({quote_ident('PrecosTaxas')})"
            )
            if r[2]
            and any(
                t in r[2].upper()
                for t in ("REAL", "INT", "NUM", "DEC", "FLOAT")
            )
        }
        conn.execute(f"DELETE FROM {quote_ident('PrecosTaxas')}")
        placeholders = ",".join(["?"] * len(cols))
        cols_sql = ",".join(quote_ident(c) for c in cols)
        sql = (
            f"INSERT INTO {quote_ident('PrecosTaxas')} ({cols_sql}) "
            f"VALUES ({placeholders})"
        )
        for row in rows:
            row_map = {}
            for i in range(min(len(headers), len(row))):
                col = headers[i]
                val = row[i]
                if col in numeric_cols:
                    val = parse_decimal(val)
                row_map[col] = val
            codigo = row_map.get("Codigo")
            if isinstance(codigo, str):
                codigo = codigo.strip()
                if not codigo:
                    continue
                row_map["Codigo"] = codigo
            elif _is_blank(codigo):
                continue
            loja = row_map.get("Loja")
            key = (codigo, loja)
            row_data = {c: row_map.get(c) for c in cols}
            existing = precos_state.get(key)
            changes = _collect_changes(
                row_data,
                existing,
                key_fields={"Codigo"},
                include_keys_when_new=True,
            )
            if existing is None:
                _record_change(
                    "Novo Registo",
                    "PrecosTaxas",
                    codigo,
                    changes=changes,
                )
            elif changes:
                _record_change(
                    "Atualização de Registo",
                    "PrecosTaxas",
                    codigo,
                    changes=changes,
                )
            updated = dict(existing or {})
            updated.update(row_data)
            precos_state[key] = updated
            conn.execute(sql, tuple(row_data.get(c) for c in cols))
        wb.close()

    _load_prices(files["PrecosTaxas"])
    conn.commit()
    ds.reload_ids()

    return report_entries


def _write_update_report(report_entries: list[dict[str, Any]]) -> Path:
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    report_path = logs_dir / f"updates-{timestamp}.xlsx"
    wb_report = Workbook()
    ws_report = wb_report.active
    ws_report.title = "Atualizações"
    ws_report.append(
        [
            "Tipo",
            "Tabela",
            "Produto",
            "Componente",
            "Nome Componente",
            "Alterações",
        ]
    )

    def _format_changes(entry: dict[str, Any]) -> str:
        formatted: list[str] = []
        change_type = entry["type"]
        for field, old, new in entry.get("changes", []):
            if change_type.startswith("Novo"):
                formatted.append(f"{field}: {new}")
            else:
                formatted.append(f"{field}: {old} -> {new}")
        return "; ".join(formatted)

    for entry in report_entries:
        ws_report.append(
            [
                entry.get("type"),
                entry.get("table"),
                entry.get("product"),
                entry.get("component_code"),
                entry.get("component_name"),
                _format_changes(entry),
            ]
        )

    wb_report.save(report_path)
    wb_report.close()
    return report_path


def update_from_excel(ds: DataStore | None = None) -> Path | None:
    """Update product data from Excel files in ``<root>/imports``.

    A informação de preços de ``PreçosTaxas_base.xlsx`` é carregada para a
    tabela ``PrecosTaxas``.
    """

    ds = ds or DataStore()
    with _manage_import_files(ds) as files:
        conn = getattr(ds, "conn", None)
        if conn is None:
            return None

        setup_database(conn)

        produtos_state, fichas_state, precos_state = _snapshot_tables(conn)
        report_entries = _apply_updates(
            conn,
            ds,
            files,
            produtos_state,
            fichas_state,
            precos_state,
        )
        return _write_update_report(report_entries)

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
    if "Codigo" not in headers:
        wb.close()
        raise ValueError(
            "Spreadsheet missing 'Codigo' column; found: " + ", ".join(headers)
        )
    code_idx = headers.index("Codigo")
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({quote_ident('Produtos')})")
    db_cols = [r[1].lower() for r in cur.fetchall()]
    name_idx = (
        headers.index("Produto")
        if "Produto" in headers and "produto" in db_cols
        else None
    )
    p1_idx = (
        headers.index("Preco1G")
        if "Preco1G" in headers and "preco1g" in db_cols
        else None
    )
    p2_idx = (
        headers.index("Preco2G")
        if "Preco2G" in headers and "preco2g" in db_cols
        else None
    )
    iva_idx = headers.index("Iva") if "Iva" in headers and "iva" in db_cols else None

    cur.execute(f"DELETE FROM {quote_ident('Produtos')}")
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
    cols_sql = ",".join(quote_ident(c) for c in cols)
    sql = (
        f"INSERT INTO {quote_ident('Produtos')} ({cols_sql}) VALUES ({placeholders})"
    )

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
        cur.execute(f"PRAGMA table_info({quote_ident('Produtos')})")
        db_cols = [r[1] for r in cur.fetchall()]
        if "Produto" in headers and "Produto" not in db_cols:
            cur.execute(
                f"ALTER TABLE {quote_ident('Produtos')} "
                f"ADD COLUMN {quote_ident('Produto')}"
            )
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
            cur.execute(
                f"SELECT 1 FROM {quote_ident('Produtos')} "
                f"WHERE {quote_ident('Codigo')}=?",
                (codigo,),
            )
            exists = cur.fetchone() is not None
            if exists:
                updates = []
                params = []
                if name_idx is not None:
                    updates.append(f"{quote_ident('Produto')}=?")
                    params.append(row[name_idx])
                if p1_idx is not None:
                    val = row[p1_idx]
                    if headers[p1_idx] in numeric_cols:
                        val = parse_decimal(val)
                    updates.append(f"{quote_ident('Preco1G')}=?")
                    params.append(val)
                if p2_idx is not None:
                    val = row[p2_idx]
                    if headers[p2_idx] in numeric_cols:
                        val = parse_decimal(val)
                    updates.append(f"{quote_ident('Preco2G')}=?")
                    params.append(val)
                if iva_idx is not None:
                    val = row[iva_idx]
                    if headers[iva_idx] in numeric_cols:
                        val = parse_decimal(val)
                    updates.append(f"{quote_ident('Iva')}=?")
                    params.append(val)
                if updates:
                    params.append(codigo)
                    cur.execute(
                        f"UPDATE {quote_ident('Produtos')} SET {', '.join(updates)} "
                        f"WHERE {quote_ident('Codigo')}=?",
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
                cols_sql = ",".join(quote_ident(c) for c in cols)
                cur.execute(
                    f"INSERT INTO {quote_ident('Produtos')} ({cols_sql}) "
                    f"VALUES ({placeholders})",
                    vals,
                )
    conn.commit()
    ds.reload_ids()
