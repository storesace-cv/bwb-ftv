# -*- coding: utf-8 -*-
"""Data access layer for the FTV project."""

import logging

from ..utils import get_project_root

base = get_project_root()


logger = logging.getLogger(__name__)


class DataStore:
    """
    DataStore mínimo (reconstruído e compatível com UI):
    - Liga à BD (por omissão: <raiz>/databases/ftv.db)
    - Instancia repositórios de produtos, ingredientes, auxiliares e preparação
    - Mantém cache de códigos (_ids) com reload_ids()
    - Fornece paginação (total, codigo_at)
    - Delegações para UI (info produto, PVPs, ingredientes,
      listas auxiliares, preparação, alergénios)
    """

    def __init__(self, db_path=None, demo: bool = False):
        import sqlite3

        self.demo = bool(demo)

        # Caminho default: raiz do projeto /databases/ftv.db
        if db_path is None:
            db_path = str(base / "databases" / "ftv.db")

        self.conn = None
        if not self.demo:
            try:
                self.conn = sqlite3.connect(db_path)
                self.conn.row_factory = sqlite3.Row
            except Exception as e:
                logger.warning(
                    "[DataStore][AVISO] Falha a ligar à BD '%s': %s", db_path, e
                )
                self.conn = None

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
        except Exception as e:
            logger.warning("[DataStore][AVISO] Falha a instanciar repositórios: %s", e)

        # Cache de códigos
        self._ids = []
        try:
            self.reload_ids()
        except Exception as e:
            logger.warning("[DataStore][AVISO] reload_ids falhou: %s", e)
            self._ids = []

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
        if self.produtos:
            try:
                ids = self.produtos.listar_codigos() or []
            except Exception:
                ids = []
        # 2) fallback direto à BD
        if not ids and self.conn:
            try:
                cur = self.conn.cursor()
                try:
                    cur.execute("SELECT DISTINCT codigo FROM produtos ORDER BY codigo")
                    ids = [r[0] for r in cur.fetchall()]
                except Exception:
                    cur.execute(
                        "SELECT DISTINCT produto_codigo FROM fichas_tecnicas "
                        "ORDER BY produto_codigo"
                    )
                    ids = [r[0] for r in cur.fetchall()]
            except Exception:
                ids = []
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
        except Exception:
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
        except Exception:
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
        except Exception:
            return []

    # Auxiliares (combos na UI)
    def list_tipos_artigos(self):
        if not self.aux:
            return [(None, "—")]
        try:
            return self.aux.list_tipos_artigos()
        except Exception:
            return [(None, "—")]

    def list_validade(self):
        if not self.aux:
            return [(None, "—")]
        try:
            return self.aux.list_validade()
        except Exception:
            return [(None, "—")]

    def list_validades(self):
        """Alias para :meth:`list_validade` mantendo compatibilidade."""
        return self.list_validade()

    def list_temperaturas(self):
        if not self.aux:
            return [(None, "—")]
        try:
            return self.aux.list_temperaturas()
        except Exception:
            return [(None, "—")]

    # Preparação (B4)
    def get_preparacao_html(self, codigo: str) -> str:
        if not self.prep:
            return ""
        try:
            return self.prep.get_html(codigo)
        except Exception:
            return ""

    def save_preparacao_html(self, codigo: str, html: str) -> None:
        if not self.prep:
            return None
        try:
            self.prep.upsert_html(codigo, html)
        except Exception:
            pass

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
                cur.execute(
                    "SELECT id, nome FROM alergenios "
                    "WHERE COALESCE(ativo,1)=1 ORDER BY nome"
                )
                rows = cur.fetchall()
                result = []
                for r in rows or []:
                    try:
                        rid = r["id"] if hasattr(r, "keys") else r[0]
                        nm = r["nome"] if hasattr(r, "keys") else r[1]
                    except Exception:
                        try:
                            rid, nm = r[0], r[1]
                        except Exception:
                            rid, nm = None, None
                    if nm is not None and str(nm).strip():
                        try:
                            rid_int = (
                                int(rid)
                                if rid is not None and str(rid).strip() != ""
                                else None
                            )
                        except Exception:
                            rid_int = None
                        result.append(
                            (
                                rid_int if rid_int is not None else len(result) + 1,
                                str(nm).strip(),
                            )
                        )
                if result:
                    return result
            except Exception:
                pass

        # 2) JSON
        json_path = base / "allergens.json"
        if json_path.exists():
            try:
                import json

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
                                except Exception:
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
            except Exception:
                pass

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
        except Exception:
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
        except Exception:
            return False

    def get_auxiliares_for(self, codigo: str):
        """Obtém (tipo_id, validade_id, temperatura_id) para um produto."""
        return self._read_auxiliares(codigo)

    def save_auxiliares_for(
        self, codigo: str, tipo_id, validade_id, temperatura_id
    ) -> bool:
        """Guarda auxiliares para um produto. Devolve *True* se bem sucedido."""
        return self._write_auxiliares(codigo, tipo_id, validade_id, temperatura_id)
