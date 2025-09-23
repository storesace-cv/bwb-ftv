# -*- coding: utf-8 -*-
"""Data access layer for the FTV project."""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Callable, Iterable

from utils import get_project_root
from .migration import (
    MIGRATIONS_DIR,
    get_pending_migrations as _get_pending_migrations,
    setup_database,
)

base = get_project_root()


logger = logging.getLogger(__name__)


def _create_empty_db(db_path: Path) -> None:
    schema_file = base / "data" / "schema.sql"
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        sql = schema_file.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.commit()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS SchemaVersion (Filename TEXT PRIMARY KEY)"
            )
            if MIGRATIONS_DIR.exists():
                filenames = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
                if filenames:
                    conn.executemany(
                        "INSERT OR IGNORE INTO SchemaVersion (Filename) VALUES (?)",
                        [(name,) for name in filenames],
                    )
            conn.commit()
        except sqlite3.Error as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "[DataStore] Falha a registar migrações iniciais: %s", exc,
                exc_info=True,
            )
    finally:
        conn.close()


class DataStore:
    """
    DataStore mínimo (reconstruído e compatível com UI):
    - Liga à BD (por omissão: <raiz>/databases/ftv.db)
    - Instancia repositórios de produtos, ingredientes, auxiliares e preparação
    - Mantém cache de códigos (_ids) com reload_ids()
    - Fornece paginação (total, codigo_at)
    - Delegações para UI (info produto, PVPs, ingredientes,
      listas auxiliares, preparação, alergénios)
    - Pode ser usado como context manager e possui ``close()`` para encerrar
      a ligação à BD
    """

    @classmethod
    def pending_migrations(cls, db_path=None):
        """Return a list of pending migration files for ``db_path``."""
        db_path = Path(db_path or base / "databases" / "ftv.db")
        if not db_path.exists():
            return []
        conn = sqlite3.connect(str(db_path))
        try:
            return _get_pending_migrations(conn)
        finally:
            conn.close()

    @classmethod
    def apply_migrations(cls, db_path=None) -> list[str]:
        """Apply migrations for ``db_path`` and ensure core tables.

        Returns a list with the filenames of the migrations that were executed.
        """

        db_path = db_path or base / "databases" / "ftv.db"
        conn = sqlite3.connect(str(db_path))
        try:
            pending = _get_pending_migrations(conn)
            if pending:
                names = ", ".join(p.name for p in pending)
                logger.info("[DataStore] Migrações pendentes: %s", names)
            setup_database(conn)
            return [p.name for p in pending]
        finally:
            conn.close()

    def __init__(
        self,
        db_path=None,
        demo: bool = False,
        prompt: Callable[[str, Iterable[str]], str] | None = None,
    ):
        self.demo = bool(demo)
        self._prompt = prompt

        # Caminho default: raiz do projeto /databases/ftv.db
        db_path = db_path or os.getenv("FTV_DB_PATH")
        if db_path is None:
            db_path = base / "databases" / "ftv.db"
        db_path = Path(db_path)

        self.conn = None
        setup_error: sqlite3.Error | None = None
        if not self.demo:
            is_memory = str(db_path) == ":memory:" or str(db_path).startswith(
                "file::memory:"
            )
            if not is_memory and not db_path.exists():
                msg = (
                    f"[DataStore] Base de dados não encontrada em '{db_path}'. "
                    "Copie o ficheiro ou defina FTV_DB_PATH."
                )
                create_db = True
                if self._prompt is not None:
                    try:
                        choice = self._prompt(
                            "Base de dados não encontrada.", ["Base vazia"]
                        )
                    except Exception as exc:
                        logger.error(
                            "[DataStore] Falha no callback de prompt: %s", exc,
                            exc_info=True,
                        )
                        raise FileNotFoundError(msg) from exc
                    if choice != "Base vazia":
                        create_db = False
                if create_db:
                    try:
                        logger.info(
                            "[DataStore] Base inexistente em '%s'. "
                            "A criar base vazia padrão.",
                            db_path,
                        )
                        _create_empty_db(db_path)
                    except Exception as exc:
                        logger.error(
                            "[DataStore] Falha a preparar BD: %s", exc,
                            exc_info=True,
                        )
                        raise FileNotFoundError(msg) from exc
                else:
                    logger.error(msg)
                    raise FileNotFoundError(msg)
            try:
                self.conn = sqlite3.connect(str(db_path))
                self.conn.row_factory = sqlite3.Row
                try:
                    setup_database(self.conn)
                except sqlite3.Error as exc:
                    try:
                        self.conn.rollback()
                    except sqlite3.Error:
                        pass
                    logger.error(
                        "[DataStore] setup_database falhou: %s",
                        exc,
                        exc_info=True,
                    )
                    setup_error = exc
                self._ensure_required_tables()
                if setup_error is not None:
                    raise setup_error
            except sqlite3.Error as exc:
                if setup_error is None or exc is not setup_error:
                    logger.error(
                        "[DataStore] Falha a ligar à BD '%s': %s",
                        db_path,
                        exc,
                        exc_info=True,
                    )
                raise

        # Repositórios
        self.produtos = None
        self.ingredientes = None
        self.aux = None
        self.prep = None
        self.fcost = None
        self.fcost_level: int | None = None
        try:
            from .repositories import (
                ProdutosRepo,
                IngredientesRepo,
                AuxiliaresRepo,
                PreparacaoRepo,
                FcostValuesRepo,
            )

            if self.conn:
                self.produtos = ProdutosRepo(self.conn)
                self.ingredientes = IngredientesRepo(self.conn)
                self.aux = AuxiliaresRepo(self.conn)
                self.prep = PreparacaoRepo(self.conn)
                self.fcost = FcostValuesRepo(self.conn)
        except (ImportError, sqlite3.Error) as exc:
            logger.error(
                "[DataStore] Falha a instanciar repositórios: %s", exc, exc_info=True
            )

        # Cache de códigos
        self._ids = []
        self._product_filter: str | None = None
        self._ingredient_filter: str | None = None
        self._family_filter: str | None = None
        self._subfamily_filter: str | None = None
        try:
            self.reload_ids()
        except sqlite3.Error as exc:
            logger.error("[DataStore] reload_ids falhou: %s", exc, exc_info=True)
            self._ids = []

    def close(self):
        """Fecha a ligação à base de dados, se existir."""
        conn = getattr(self, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except sqlite3.Error as exc:
                logger.warning("[DataStore] Falha a fechar a BD: %s", exc)
            finally:
                self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def set_fcost_level(self, level: int | None):
        """Definir nível de Food Cost para filtragem e recarregar códigos."""

        self.fcost_level = level
        self.reload_ids()

    def set_search_filters(
        self,
        *,
        produto: str | None = None,
        ingrediente: str | None = None,
        familia: str | Iterable[str] | None = None,
        subfamilia: str | Iterable[str] | None = None,
    ) -> None:
        """Atualizar filtros de pesquisa e recarregar códigos se necessário."""

        def _clean(value: str | Iterable[str] | None):
            if value is None:
                return None
            if isinstance(value, str):
                cleaned = value.strip()
                return cleaned or None
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                collected: list[str] = []
                seen: set[str] = set()
                for entry in value:
                    if entry is None:
                        continue
                    text = str(entry).strip()
                    if not text:
                        continue
                    key = text.casefold()
                    if key in seen:
                        continue
                    seen.add(key)
                    collected.append(text)
                return tuple(collected) or None
            cleaned = str(value).strip()
            return cleaned or None

        produto_val = _clean(produto)
        ingrediente_val = _clean(ingrediente)
        familia_val = _clean(familia)
        subfamilia_val = _clean(subfamilia)

        if (
            produto_val == self._product_filter
            and ingrediente_val == self._ingredient_filter
            and familia_val == self._family_filter
            and subfamilia_val == self._subfamily_filter
        ):
            return

        self._product_filter = produto_val
        self._ingredient_filter = ingrediente_val
        self._family_filter = familia_val
        self._subfamily_filter = subfamilia_val
        self.reload_ids()

    def list_family_hierarchy(self) -> dict[str, tuple[str, ...]]:
        """Obter mapa ``{família: (subfamílias...)}`` a partir da base de dados."""

        results: dict[str, set[str]] = {}
        if not self.conn:
            return {}

        def _add_entry(family: str | None, subfamily: str | None) -> None:
            family_name = (family or "").strip()
            if not family_name:
                return
            bucket = results.setdefault(family_name, set())
            sub_name = (subfamily or "").strip()
            if sub_name:
                bucket.add(sub_name)

        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Produtos'"
            )
            has_produtos = cur.fetchone() is not None

            if has_produtos:
                cur.execute(
                    "SELECT DISTINCT "
                    "COALESCE(NULLIF(TRIM(Familia), ''), '') AS Familia, "
                    "COALESCE(NULLIF(TRIM(SubFamilia), ''), '') AS SubFamilia "
                    "FROM Produtos "
                    "WHERE TipoVenda = 1"
                )
                for familia, subfamilia in cur.fetchall():
                    _add_entry(familia, subfamilia)

            fallback_family = (
                "COALESCE(TRIM(CASE "
                "WHEN instr(ft.FamiliaSubfamilia, '>') > 0 "
                "THEN SUBSTR(ft.FamiliaSubfamilia, 1, instr(ft.FamiliaSubfamilia, '>') - 1) "
                "ELSE ft.FamiliaSubfamilia "
                "END), '')"
            )
            fallback_subfamily = (
                "COALESCE(TRIM(CASE "
                "WHEN instr(ft.FamiliaSubfamilia, '>') > 0 "
                "THEN SUBSTR(ft.FamiliaSubfamilia, instr(ft.FamiliaSubfamilia, '>') + 1) "
                "ELSE '' "
                "END), '')"
            )

            if has_produtos:
                cur.execute(
                    "SELECT DISTINCT "
                    "COALESCE(NULLIF(TRIM(p.Familia), ''), "
                    + fallback_family
                    + ") AS Familia, "
                    "COALESCE(NULLIF(TRIM(p.SubFamilia), ''), "
                    + fallback_subfamily
                    + ") AS SubFamilia "
                    "FROM FichasTecnicas ft "
                    "LEFT JOIN Produtos p ON ft.ProdutoCodigo = p.Codigo "
                    "WHERE p.TipoVenda = 1"
                )
            else:
                cur.execute(
                    "SELECT DISTINCT "
                    + fallback_family
                    + " AS Familia, "
                    + fallback_subfamily
                    + " AS SubFamilia "
                    "FROM FichasTecnicas ft"
                )

            for familia, subfamilia in cur.fetchall():
                _add_entry(familia, subfamilia)

        except sqlite3.Error as exc:  # pragma: no cover - defensive logging
            logger.error(
                "[DataStore] list_family_hierarchy falhou: %s", exc, exc_info=True
            )
            return {}

        normalized: dict[str, tuple[str, ...]] = {}
        for family_name in sorted(results.keys(), key=str.casefold):
            subs = tuple(sorted(results[family_name], key=str.casefold))
            normalized[family_name] = subs
        return normalized

    def get_active_fcost_range(self) -> tuple[float, float] | None:
        """Obter ``(ValorMin, ValorMax)`` do nível de Food Cost ativo."""

        if self.fcost_level is None or not self.fcost:
            return None
        try:
            return self.fcost.get_range(self.fcost_level)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_active_fcost_range falhou: %s", exc, exc_info=True
            )
            return None

    def _ensure_required_tables(self):
        """Verifica se tabelas e colunas essenciais existem na base de dados."""

        required = {
            # Campos mínimos esperados em ``Produtos``.  Estes refletem o
            # esquema expandido utilizado pelo projeto e são essenciais para a
            # importação e apresentação de dados.
            "Produtos": {
                "Codigo",
                "Produto",
                "Familia",
                "SubFamilia",
                "AfetaStk",
                "Menu",
                "CodBarras",
                "TipoMercad",
                "TipoVenda",
                "TipoProducao",
                "TipoGener",
                "UnStockVMPG",
                "UnVendaVMV",
                "UnInvVMMMPG",
                "UnProduFtPV",
                "CodAuxiliar",
                "CodAuxiliar2",
                "PCU",
                "PCM",
                "Descontinuado",
                "DispLojas",
                "TipoArtigo",
                "Validade",
                "Temperatura",
            },
            # ``FichasTecnicas`` deve incluir colunas essenciais de relação
            # produto/componente e custos.
            "FichasTecnicas": {
                "FamiliaSubfamilia",
                "ProdutoCodigo",
                "ProdutoNome",
                "ComponenteCodigo",
                "ComponenteNome",
                "Qtd",
                "Unidade",
                "Ppu",
                "Preco",
                "Peso",
            },
            "PrecosTaxas": {"Codigo", "Loja"},
            "Alergenios": {"Id", "Nome"},
            "ProdutoAlergenio": {"ProdutoCodigo", "AlergenioId"},
            "TiposArtigos": {"Cod", "Descricao", "Ativo"},
            "Validade": {"Cod", "Descricao", "Ativo"},
            "Temperaturas": {"Cod", "Descricao", "Ativo"},
            "FcostValues": {
                "Nivel",
                "Nome",
                "ValorMin",
                "ValorMax",
                "Comentario",
            },
        }

        try:
            cur = self.conn.cursor()
            missing_tables = []
            missing_cols = []
            for table, cols in required.items():
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                if cur.fetchone() is None:
                    missing_tables.append(table)
                    continue
                cur.execute(f"PRAGMA table_info({table})")
                existing = {r[1] for r in cur.fetchall()}
                diff = cols - existing
                if diff:
                    missing_cols.append(f"{table}: {', '.join(sorted(diff))}")
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] Falha ao verificar tabelas essenciais: %s",
                exc,
                exc_info=True,
            )
            raise

        if missing_tables or missing_cols:
            parts = []
            if missing_tables:
                parts.append("tabelas: " + ", ".join(sorted(missing_tables)))
            if missing_cols:
                parts.append("colunas: " + "; ".join(sorted(missing_cols)))
            msg = "[DataStore] Tabelas essenciais em falta: " + ", ".join(parts)
            logger.error(msg)
            raise RuntimeError(msg)

    # ----------------------------
    # Cache / paginação
    # ----------------------------
    def reload_ids(self):
        """
        Recarrega a lista de códigos (_ids). Tenta repos 'produtos'; senão usa
        FichasTecnicas.

        Placeholder para futura filtragem baseada em ``FcostValues``.
        """
        ids: list[str] = []
        source = None

        produto_filtro = getattr(self, "_product_filter", None)
        ingrediente_filtro = getattr(self, "_ingredient_filter", None)
        familia_filtro = getattr(self, "_family_filter", None)
        subfamilia_filtro = getattr(self, "_subfamily_filter", None)
        filtros_ativos = bool(
            produto_filtro or ingrediente_filtro or familia_filtro or subfamilia_filtro
        )

        # 1) tentar via repositório (apenas sem filtros)
        if self.produtos and not filtros_ativos:
            try:
                ids = self.produtos.listar_codigos() or []
                if ids:
                    source = "repositorio"
            except sqlite3.Error as exc:
                logger.error(
                    "[DataStore] listar_codigos falhou: %s", exc, exc_info=True
                )
                ids = []

        # 2) fallback direto à BD (ou se filtros ativos)
        if (filtros_ativos or not ids) and self.conn:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Produtos'"
                )
                has_produtos = cur.fetchone() is not None

                def _like(term: str | None) -> str:
                    if not term:
                        return "%"
                    value = term.replace("\\", "\\\\").replace("%", "\\%").replace(
                        "_", "\\_"
                    )
                    return f"%{value}%"

                produto_like = _like(produto_filtro)
                ingrediente_like = _like(ingrediente_filtro)

                def _build_clause(expression: str, value):
                    if value is None:
                        return "1=1", []
                    if isinstance(value, tuple):
                        lowered = [entry.casefold() for entry in value if entry]
                        if not lowered:
                            return "1=1", []
                        placeholders = ", ".join("?" for _ in lowered)
                        clause = f"LOWER({expression}) IN ({placeholders})"
                        return clause, lowered
                    like_value = _like(value)
                    return (
                        f"{expression} LIKE ? ESCAPE '\\' COLLATE NOCASE",
                        [like_value],
                    )

                fallback_family = (
                    "COALESCE(TRIM(CASE "
                    "WHEN instr(ft.FamiliaSubfamilia, '>') > 0 "
                    "THEN SUBSTR(ft.FamiliaSubfamilia, 1, instr(ft.FamiliaSubfamilia, '>') - 1) "
                    "ELSE ft.FamiliaSubfamilia "
                    "END), '')"
                )
                fallback_subfamily = (
                    "COALESCE(TRIM(CASE "
                    "WHEN instr(ft.FamiliaSubfamilia, '>') > 0 "
                    "THEN SUBSTR(ft.FamiliaSubfamilia, instr(ft.FamiliaSubfamilia, '>') + 1) "
                    "ELSE '' "
                    "END), '')"
                )

                family_expr_produtos = (
                    "COALESCE(NULLIF(TRIM(p.Familia), ''), " + fallback_family + ")"
                )
                subfamily_expr_produtos = (
                    "COALESCE(NULLIF(TRIM(p.SubFamilia), ''), "
                    + fallback_subfamily
                    + ")"
                )
                family_clause_produtos, family_params_produtos = _build_clause(
                    family_expr_produtos, familia_filtro
                )
                subfamily_clause_produtos, subfamily_params_produtos = _build_clause(
                    subfamily_expr_produtos, subfamilia_filtro
                )
                family_clause_ft, family_params_ft = _build_clause(
                    fallback_family, familia_filtro
                )
                subfamily_clause_ft, subfamily_params_ft = _build_clause(
                    fallback_subfamily, subfamilia_filtro
                )

                if has_produtos:
                    query = (
                        "SELECT DISTINCT COALESCE(p.Codigo, ft.ProdutoCodigo) AS Codigo "
                        "FROM FichasTecnicas ft "
                        "LEFT JOIN Produtos p ON ft.ProdutoCodigo = p.Codigo "
                        "WHERE p.TipoVenda = 1 "
                        "AND COALESCE(p.Produto, ft.ProdutoNome, '') "
                        "LIKE ? ESCAPE '\\' COLLATE NOCASE "
                        "AND COALESCE(ft.ComponenteNome, '') "
                        "LIKE ? ESCAPE '\\' COLLATE NOCASE "
                        "AND "
                        + family_clause_produtos
                        + " "
                        "AND "
                        + subfamily_clause_produtos
                        + " "
                        "ORDER BY Codigo"
                    )
                    params = (
                        produto_like,
                        ingrediente_like,
                        *family_params_produtos,
                        *subfamily_params_produtos,
                    )
                    source = (
                        "sql:Produtos filtrado"
                        if filtros_ativos
                        else "sql:Produtos"
                    )
                else:
                    query = (
                        "SELECT DISTINCT ft.ProdutoCodigo AS Codigo "
                        "FROM FichasTecnicas ft "
                        "WHERE COALESCE(ft.ProdutoNome, '') LIKE ? ESCAPE '\\' COLLATE NOCASE "
                        "AND COALESCE(ft.ComponenteNome, '') LIKE ? ESCAPE '\\' COLLATE NOCASE "
                        "AND "
                        + family_clause_ft
                        + " "
                        "AND "
                        + subfamily_clause_ft
                        + " "
                        "ORDER BY ft.ProdutoCodigo"
                    )
                    params = (
                        produto_like,
                        ingrediente_like,
                        *family_params_ft,
                        *subfamily_params_ft,
                    )
                    source = (
                        "sql:FichasTecnicas filtrado"
                        if filtros_ativos
                        else "sql:FichasTecnicas"
                    )

                cur.execute(query, params)
                ids = [r[0] for r in cur.fetchall()]
            except sqlite3.Error as exc:
                logger.error(
                    "[DataStore] reload_ids falhou na BD: %s", exc, exc_info=True
                )
                ids = []

        if source:
            logger.info("[DataStore] reload_ids: códigos via %s", source)

        cleaned_ids = [str(x) for x in ids if x not in (None, "")]
        ids = list(dict.fromkeys(cleaned_ids))

        if self.fcost_level is not None and self.fcost:
            rng = self.get_active_fcost_range()
            if rng:
                from services.products import calculate_food_cost

                vmin, vmax = rng
                filtered: list[str] = []
                for codigo in ids:
                    ingredientes = self.get_ingredientes(codigo)
                    total = 0.0
                    for ing in ingredientes:
                        preco = ing.get("Preco")
                        if preco not in (None, ""):
                            try:
                                total += float(preco)
                                continue
                            except (TypeError, ValueError):
                                pass
                        ppu = ing.get("Ppu")
                        qtd = ing.get("Qtd")
                        try:
                            total += float(ppu) * float(qtd)
                        except (TypeError, ValueError):
                            pass

                    pvps_info = self.get_pvps(codigo)
                    iva = pvps_info.get("iva")
                    pvps = pvps_info.get("pvps") or []
                    info = self.get_produto_info(codigo) or {}
                    nome = info.get("produto") or codigo

                    for pvp in pvps:
                        pct = calculate_food_cost(total, pvp, iva, product=nome)
                        if pct is not None and vmin <= pct <= vmax:
                            filtered.append(codigo)
                            break
                ids = filtered

        self._ids = ids
        return len(self._ids)

    def total(self) -> int:
        return len(self._ids)

    def codigo_at(self, idx: int):
        if idx is None:
            return None
        if idx < 0 or idx >= len(self._ids):
            return None
        return self._ids[idx]

    # ----------------------------
    # Delegações principais
    # ----------------------------
    def get_produto_info(self, codigo: str):
        if not self.produtos:
            return {}
        try:
            return self.produtos.get_info(codigo)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_produto_info(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )
            return {}

    def get_pvps(self, codigo: str) -> dict[str, list[float | None] | float | None]:
        if not self.produtos:
            return {"pvps": [], "iva": None}
        try:
            return self.produtos.get_pvps(codigo)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_pvps(%s) falhou: %s", codigo, exc, exc_info=True
            )
            return {"pvps": [], "iva": None}

    def get_ingredientes(self, codigo: str):
        if not self.ingredientes:
            return []
        try:
            return self.ingredientes.listar_por_produto(codigo)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_ingredientes(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )
            return []

    # Auxiliares (combos na UI)
    def list_tipos_artigos(self):
        if not self.aux:
            return [(None, "—")]
        try:
            return self.aux.list_tipos_artigos()
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] list_tipos_artigos falhou: %s", exc, exc_info=True
            )
            return [(None, "—")]

    def list_validade(self):
        if not self.aux:
            return []
        try:
            return self.aux.list_validade()[1:]
        except sqlite3.Error as exc:
            logger.error("[DataStore] list_validade falhou: %s", exc, exc_info=True)
            return []

    def list_validades(self):
        """Alias para :meth:`list_validade` mantendo compatibilidade."""
        return self.list_validade()

    def list_temperaturas(self):
        if not self.aux:
            return [(None, "—")]
        try:
            return self.aux.list_temperaturas()
        except sqlite3.Error as exc:
            logger.error("[DataStore] list_temperaturas falhou: %s", exc, exc_info=True)
            return [(None, "—")]

    def set_tipo_artigo(self, codigo: str, tipo_cod) -> bool:
        """Atualiza o ``TipoArtigo`` de um produto."""
        if not self.produtos:
            return False
        try:
            return self.produtos.set_tipo_artigo(codigo, tipo_cod)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] set_tipo_artigo(%s, %s) falhou: %s",
                codigo,
                tipo_cod,
                exc,
                exc_info=True,
            )
            return False

    def set_validade(self, codigo: str, validade_cod) -> bool:
        """Atualiza o ``Validade`` de um produto."""
        if not self.produtos:
            return False
        try:
            return self.produtos.set_validade(codigo, validade_cod)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] set_validade(%s, %s) falhou: %s",
                codigo,
                validade_cod,
                exc,
                exc_info=True,
            )
            return False

    def set_temperatura(self, codigo: str, temperatura_cod) -> bool:
        """Atualiza o ``Temperatura`` de um produto."""
        if not self.produtos:
            return False
        try:
            return self.produtos.set_temperatura(codigo, temperatura_cod)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] set_temperatura(%s, %s) falhou: %s",
                codigo,
                temperatura_cod,
                exc,
                exc_info=True,
            )
            return False

    def get_product_allergens(self, codigo: str) -> list[int]:
        """Return allergen identifiers linked to ``codigo``."""

        if not self.produtos or not codigo:
            return []
        try:
            return self.produtos.get_product_allergens(codigo)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_product_allergens(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )
            return []

    def set_product_allergens(
        self, codigo: str, allergen_ids: Iterable[int | str | None]
    ) -> bool:
        """Persist allergen identifiers for ``codigo``."""

        if not self.produtos or not codigo:
            return False
        ids = list(allergen_ids)
        try:
            return self.produtos.set_product_allergens(codigo, ids)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] set_product_allergens(%s, %s) falhou: %s",
                codigo,
                ids,
                exc,
                exc_info=True,
            )
            return False

    # Preparação (B6)
    def get_preparacao_html(self, codigo: str) -> str:
        if not self.prep:
            return ""
        try:
            return self.prep.get_html(codigo)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_preparacao_html(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )
            return ""

    def save_preparacao_html(self, codigo: str, html: str) -> None:
        if not self.prep:
            return None
        try:
            self.prep.upsert_html(codigo, html)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] save_preparacao_html(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )

    # Alergénios ativos: helpers
    def _allergens_from_db(self):
        if not self.conn or self.demo:
            return None
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT Id, Nome FROM Alergenios ORDER BY Id")
            rows = cur.fetchall()
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] list_active_allergens BD falhou: %s",
                exc,
                exc_info=True,
            )
            return None

        result = []
        for r in rows or []:
            try:
                rid = r["id"] if hasattr(r, "keys") else r[0]
                nm = r["nome"] if hasattr(r, "keys") else r[1]
            except (KeyError, IndexError, TypeError):
                try:
                    rid, nm = r[0], r[1]
                except (IndexError, TypeError):
                    continue
            if nm is None or str(nm).strip() == "":
                continue
            try:
                rid_int = (
                    int(rid) if rid is not None and str(rid).strip() != "" else None
                )
            except (ValueError, TypeError):
                rid_int = None
            result.append(
                (rid_int if rid_int is not None else len(result) + 1, str(nm).strip())
            )
        return result or None

    def list_active_allergens(self):
        """Devolve lista de tuplos ``(id, nome)`` de alergénios disponíveis."""
        items = self._allergens_from_db()
        return items or []

    def get_allergen_details(self, aid):
        """Obter campos ``Exemplos`` e ``Notas`` de um alergénio."""

        if not self.conn or self.demo:
            return {}
        if aid in (None, ""):
            return {}
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT Exemplos, Notas FROM Alergenios WHERE Id = ?",
                (aid,),
            )
            row = cur.fetchone()
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_allergen_details(%s) BD falhou: %s",
                aid,
                exc,
                exc_info=True,
            )
            return {}
        if not row:
            return {}
        try:
            exemplos = row["Exemplos"]  # type: ignore[index]
        except (KeyError, IndexError, TypeError):
            try:
                exemplos = row[0]
            except (IndexError, TypeError):
                exemplos = None
        try:
            notas = row["Notas"]  # type: ignore[index]
        except (KeyError, IndexError, TypeError):
            try:
                notas = row[1]
            except (IndexError, TypeError):
                notas = None
        return {"Exemplos": exemplos, "Notas": notas}
