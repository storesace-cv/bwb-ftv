# -*- coding: utf-8 -*-
"""Data access layer for the FTV project."""

import json
import logging
import os
import sqlite3
from pathlib import Path

from utils import get_project_root
from .migration import ensure_core_tables

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
                        logger.error(msg)
                        raise FileNotFoundError(msg)
                except Exception as exc:
                    logger.error("[DataStore] Falha a preparar BD: %s", exc)
                    raise FileNotFoundError(msg) from exc
            try:
                self.conn = sqlite3.connect(str(db_path))
                self.conn.row_factory = sqlite3.Row
                if not is_memory:
                    default_db = base / "databases" / "ftv.db"
                    if db_path.resolve() == default_db.resolve():
                        from .migration import (
                            apply_pending_migrations,
                            get_pending_migrations,
                        )

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
                            if choice == "Sim":
                                apply_pending_migrations(self.conn)
                            else:
                                self.conn.close()
                                raise RuntimeError(
                                    "Migração cancelada pelo utilizador."
                                )
                ensure_core_tables(self.conn)
                self._ensure_required_tables()
            except sqlite3.Error as exc:
                logger.error("[DataStore] Falha a ligar à BD '%s': %s", db_path, exc)
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
            logger.error("[DataStore] Falha a instanciar repositórios: %s", exc)

        # Cache de códigos
        self._ids = []
        try:
            self.reload_ids()
        except sqlite3.Error as exc:
            logger.error("[DataStore] reload_ids falhou: %s", exc)
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
            "produtos": {"codigo"},
            "fichas_tecnicas": {"produto_codigo"},
            "alergenios": {"id", "nome", "ativo"},
            "tipos_artigos": {"cod", "descricao", "ativo"},
            "validade": {"cod", "descricao", "ativo"},
            "temperaturas": {"cod", "descricao", "ativo"},
            "produto_auxiliar": {
                "produto_codigo",
                "tipo_artigo_id",
                "validade_id",
                "temperatura_id",
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
            logger.error("[DataStore] Falha ao verificar tabelas essenciais: %s", exc)
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
        fichas_tecnicas.
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
                logger.error("[DataStore] listar_codigos falhou: %s", exc)
                ids = []
        # 2) fallback direto à BD
        if not ids and self.conn:
            try:
                cur = self.conn.cursor()
                try:
                    cur.execute("SELECT DISTINCT codigo FROM produtos ORDER BY codigo")
                    ids = [r[0] for r in cur.fetchall()]
                    source = "produtos"
                except sqlite3.Error as exc:
                    logger.warning("[DataStore] fallback para fichas_tecnicas: %s", exc)
                    cur.execute(
                        "SELECT DISTINCT produto_codigo FROM fichas_tecnicas "
                        "ORDER BY produto_codigo"
                    )
                    ids = [r[0] for r in cur.fetchall()]
                    source = "fichas_tecnicas"
            except sqlite3.Error as exc:
                logger.error("[DataStore] reload_ids falhou na BD: %s", exc)
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
            logger.error("[DataStore] get_produto_info(%s) falhou: %s", codigo, exc)
            return {}

    def get_pvps(self, codigo: str):
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
            logger.error("[DataStore] get_pvps(%s) falhou: %s", codigo, exc)
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
            logger.error("[DataStore] get_ingredientes(%s) falhou: %s", codigo, exc)
            return []

    # Auxiliares (combos na UI)
    def list_tipos_artigos(self):
        if not self.aux:
            return [(None, "—")]
        try:
            return self.aux.list_tipos_artigos()
        except sqlite3.Error as exc:
            logger.error("[DataStore] list_tipos_artigos falhou: %s", exc)
            return [(None, "—")]

    def list_validade(self):
        if not self.aux:
            return [(None, "—")]
        try:
            return self.aux.list_validade()
        except sqlite3.Error as exc:
            logger.error("[DataStore] list_validade falhou: %s", exc)
            return [(None, "—")]

    def list_validades(self):
        """Alias para :meth:`list_validade` mantendo compatibilidade."""
        return self.list_validade()

    def list_temperaturas(self):
        if not self.aux:
            return [(None, "—")]
        try:
            return self.aux.list_temperaturas()
        except sqlite3.Error as exc:
            logger.error("[DataStore] list_temperaturas falhou: %s", exc)
            return [(None, "—")]

    # Preparação (B4)
    def get_preparacao_html(self, codigo: str) -> str:
        if not self.prep:
            return ""
        try:
            return self.prep.get_html(codigo)
        except sqlite3.Error as exc:
            logger.error("[DataStore] get_preparacao_html(%s) falhou: %s", codigo, exc)
            return ""

    def save_preparacao_html(self, codigo: str, html: str) -> None:
        if not self.prep:
            return None
        try:
            self.prep.upsert_html(codigo, html)
        except sqlite3.Error as exc:
            logger.error("[DataStore] save_preparacao_html(%s) falhou: %s", codigo, exc)

    # Alergénios ativos: lista de tuplos (id, nome)
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
        # 1) BD
        if self.conn and not self.demo:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT id, nome FROM alergenios WHERE ativo=1 ORDER BY id")
                rows = cur.fetchall()
                result = []
                for r in rows or []:
                    try:
                        rid = r["id"] if hasattr(r, "keys") else r[0]
                        nm = r["nome"] if hasattr(r, "keys") else r[1]
                    except (KeyError, IndexError, TypeError):
                        try:
                            rid, nm = r[0], r[1]
                        except (IndexError, TypeError):
                            rid, nm = None, None
                    if nm is not None and str(nm).strip():
                        try:
                            rid_int = (
                                int(rid)
                                if rid is not None and str(rid).strip() != ""
                                else None
                            )
                        except (ValueError, TypeError):
                            rid_int = None
                        result.append(
                            (
                                rid_int if rid_int is not None else len(result) + 1,
                                str(nm).strip(),
                            )
                        )
                if result:
                    return result
            except sqlite3.Error as exc:
                logger.error("[DataStore] list_active_allergens BD falhou: %s", exc)

        # 2) JSON
        json_path = base / "allergens.json"
        if json_path.exists():
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
                    # remover duplicados por nome (case-insensitive), mantendo ordem
                    seen = set()
                    for rid, nm in tmp:
                        key = nm.strip().lower()
                        if key not in seen:
                            seen.add(key)
                            items.append((rid, nm))
                if items:
                    # normalizar ids sequenciais 1..N mantendo ordem
                    return [(i + 1, nm) for i, (_, nm) in enumerate(items)]
            except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
                logger.error("[DataStore] list_active_allergens JSON falhou: %s", exc)

        # 3) Padrão
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

    def _read_auxiliares(self, codigo: str):
        """Lê (tipo_id, validade_id, temperatura_id) a partir do repo Auxiliares."""
        if (
            getattr(self, "demo", False)
            or not getattr(self, "conn", None)
            or getattr(self, "aux", None) is None
        ):
            return (None, None, None)
        try:
            return self.aux.get_produto_auxiliares(codigo)
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] get_produto_auxiliares(%s) falhou: %s", codigo, exc
            )
            return (None, None, None)

    def _write_auxiliares(
        self, codigo: str, tipo_id, validade_id, temperatura_id
    ) -> bool:
        """Grava no repo Auxiliares (upsert)."""
        if (
            getattr(self, "demo", False)
            or not getattr(self, "conn", None)
            or getattr(self, "aux", None) is None
        ):
            return False
        try:
            self.aux.set_produto_auxiliares(
                codigo, tipo_id, validade_id, temperatura_id
            )
            return True
        except sqlite3.Error as exc:
            logger.error(
                "[DataStore] set_produto_auxiliares(%s) falhou: %s", codigo, exc
            )
            return False

    def get_auxiliares_for(self, codigo: str):
        """Obtém (tipo_id, validade_id, temperatura_id) para um produto."""
        return self._read_auxiliares(codigo)

    def save_auxiliares_for(
        self, codigo: str, tipo_id, validade_id, temperatura_id
    ) -> bool:
        """Guarda auxiliares para um produto. Devolve *True* se bem sucedido."""
        return self._write_auxiliares(codigo, tipo_id, validade_id, temperatura_id)
