# -*- coding: utf-8 -*-
"""Data access layer for the FTV project."""

import json
import logging
import os
import sqlite3
from pathlib import Path

from utils import get_project_root
from .migration import get_pending_migrations, setup_database

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

    def __init__(self, db_path=None, demo: bool = False):
        self.demo = bool(demo)

        # Caminho default: raiz do projeto /databases/ftv.db
        db_path = db_path or os.getenv("FTV_DB_PATH")
        if db_path is None:
            db_path = base / "databases" / "ftv.db"
        db_path = Path(db_path)

        self.conn = None
        if not self.demo:
            is_memory = str(db_path) == ":memory:" or str(db_path).startswith(
                "file::memory:"
            )
            if not is_memory and not db_path.exists():
                msg = (
                    f"[DataStore] Base de dados não encontrada em '{db_path}'. "
                    "Copie o ficheiro ou defina FTV_DB_PATH."
                )
                from PyQt5.QtWidgets import QApplication
                from ui.startup_dialog import StartupDialog

                if QApplication.instance() is None:
                    QApplication([])
                choice = StartupDialog(
                    "Base de dados não encontrada.",
                    ["Base vazia"],
                ).get_choice()
                try:
                    if choice == "Base vazia":
                        _create_empty_db(db_path)
                    else:
                        logger.error(msg, exc_info=True)
                        raise FileNotFoundError(msg)
                except Exception as exc:
                    logger.error(
                        "[DataStore] Falha a preparar BD: %s", exc, exc_info=True
                    )
                    raise FileNotFoundError(msg) from exc
            try:
                self.conn = sqlite3.connect(str(db_path))
                self.conn.row_factory = sqlite3.Row
                if not is_memory:
                    default_db = base / "databases" / "ftv.db"
                    if db_path.resolve() == default_db.resolve():
                        pending = get_pending_migrations(self.conn)
                        if pending:
                            from PyQt5.QtWidgets import QApplication
                            from ui.startup_dialog import StartupDialog

                            if QApplication.instance() is None:
                                QApplication([])
                            choice = StartupDialog(
                                (
                                    "Foi detetada uma migração da base de dados. "
                                    "Aplicar agora?"
                                ),
                                ["Sim", "Não"],
                            ).get_choice()
                            if choice != "Sim":
                                self.conn.close()
                                raise RuntimeError(
                                    "Migração cancelada pelo utilizador."
                                )
                setup_database(self.conn)
                self._ensure_required_tables()
            except sqlite3.Error as exc:
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
        try:
            from .repositories import (
                ProdutosRepo,
                IngredientesRepo,
                AuxiliaresRepo,
                PreparacaoRepo,
            )

            if self.conn:
                self.produtos = ProdutosRepo(self.conn)
                self.ingredientes = IngredientesRepo(self.conn)
                self.aux = AuxiliaresRepo(self.conn)
                self.prep = PreparacaoRepo(self.conn)
        except (ImportError, sqlite3.Error) as exc:
            logger.error(
                "[DataStore] Falha a instanciar repositórios: %s", exc, exc_info=True
            )

        # Cache de códigos
        self._ids = []
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
            "Alergenios": {"Id", "Nome", "Ativo"},
            "TiposArtigos": {"Cod", "Descricao", "Ativo"},
            "Validade": {"Cod", "Descricao", "Ativo"},
            "Temperaturas": {"Cod", "Descricao", "Ativo"},
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
        """
        ids = []
        # 1) tentar via repositório
        source = None
        if self.produtos:
            try:
                ids = self.produtos.listar_codigos() or []
                if ids:
                    source = "repositorio"
            except sqlite3.Error as exc:
                logger.error(
                    "[DataStore] listar_codigos falhou: %s", exc, exc_info=True
                )
                ids = []
        # 2) fallback direto à BD
        if not ids and self.conn:
            try:
                cur = self.conn.cursor()
                try:
                    cur.execute(
                        """
                        SELECT DISTINCT p.Codigo
                        FROM Produtos p
                        JOIN FichasTecnicas ft ON ft.ProdutoCodigo = p.Codigo
                        WHERE p.TipoVenda = 1
                        ORDER BY p.Codigo
                        """
                    )
                    ids = [r[0] for r in cur.fetchall()]
                    source = "Produtos"
                except sqlite3.Error as exc:
                    logger.warning("[DataStore] fallback para FichasTecnicas: %s", exc)
                    if "no such table: Produtos" in str(exc):
                        # ``Produtos`` não existe: usar códigos diretamente de
                        # ``FichasTecnicas``.
                        logger.info(
                            "[DataStore] tabela 'Produtos' inexistente; "
                            "a usar ProdutoCodigo de FichasTecnicas",
                        )
                        cur.execute(
                            "SELECT DISTINCT ProdutoCodigo FROM FichasTecnicas "
                            "ORDER BY ProdutoCodigo"
                        )
                        ids = [r[0] for r in cur.fetchall()]
                        source = "FichasTecnicas"
                    else:
                        cur.execute(
                            """
                            SELECT DISTINCT p.Codigo
                            FROM FichasTecnicas ft
                            JOIN Produtos p ON ft.ProdutoCodigo = p.Codigo
                            WHERE p.TipoVenda = 1
                            ORDER BY p.Codigo
                            """
                        )
                        ids = [r[0] for r in cur.fetchall()]
                        source = "Produtos"
            except sqlite3.Error as exc:
                logger.error(
                    "[DataStore] reload_ids falhou na BD: %s", exc, exc_info=True
                )
                ids = []
        if source:
            logger.info("[DataStore] reload_ids: códigos via %s", source)
        self._ids = [str(x) for x in ids if x not in (None, "")]
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

    def get_pvps(self, codigo: str) -> dict[str, float | None]:
        if not self.produtos:
            return {
                "pvp1": None,
                "pvp2": None,
                "pvp3": None,
                "pvp4": None,
                "pvp5": None,
            }
        try:
            return self.produtos.get_pvps(codigo)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_pvps(%s) falhou: %s", codigo, exc, exc_info=True
            )
            return {
                "pvp1": None,
                "pvp2": None,
                "pvp3": None,
                "pvp4": None,
                "pvp5": None,
            }

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

    # Preparação (B4)
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
            cur.execute("SELECT id, nome FROM alergenios WHERE ativo=1 ORDER BY id")
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

    def _allergens_from_json(self):
        json_path = base / "allergens.json"
        if not json_path.exists():
            return None
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            payload = (
                data.get("alergenios")
                if isinstance(data, dict) and "alergenios" in data
                else data
            )
            items = []
            if isinstance(payload, list):
                tmp = []
                for idx, item in enumerate(payload, 1):
                    if isinstance(item, str):
                        nm = item.strip()
                        if nm:
                            tmp.append((idx, nm))
                    elif isinstance(item, dict):
                        nm = item.get("nome") or item.get("name")
                        if nm and str(nm).strip():
                            rid = item.get("id")
                            try:
                                rid_int = (
                                    int(rid)
                                    if rid is not None and str(rid).strip() != ""
                                    else idx
                                )
                            except (ValueError, TypeError):
                                rid_int = idx
                            tmp.append((rid_int, str(nm).strip()))
                seen = set()
                for rid, nm in tmp:
                    key = nm.strip().lower()
                    if key not in seen:
                        seen.add(key)
                        items.append((rid, nm))
            if items:
                return [(i + 1, nm) for i, (_, nm) in enumerate(items)]
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            logger.error(
                "[DataStore] list_active_allergens JSON falhou: %s",
                exc,
                exc_info=True,
            )
        return None

    def _default_allergens(self):
        default = [
            "Glúten",
            "Crustáceos",
            "Ovos",
            "Peixe",
            "Amendoins",
            "Soja",
            "Leite",
            "Frutos de casca rija",
            "Aipo",
            "Mostarda",
            "Sementes de sésamo",
            "Dióxido de enxofre e sulfitos",
            "Tremoço",
            "Moluscos",
        ]
        return [(i + 1, nm) for i, nm in enumerate(default)]

    def list_active_allergens(self):
        """
        Devolve lista de tuplos (id, nome) de alergénios ativos.

        Ordem de tentativa:
          1) BD (tabela alergenios: id, nome, ativo)
          2) Ficheiro allergens.json na raiz do projeto
          3) Lista padrão (14 principais)

        Returns:
            list[tuple[int, str]]
        """
        for getter in (
            self._allergens_from_db,
            self._allergens_from_json,
            self._default_allergens,
        ):
            items = getter()
            if items:
                return items
        return []
