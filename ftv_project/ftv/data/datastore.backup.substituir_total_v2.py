# -*- coding: utf-8 -*-
from pathlib import Path

class DataStore:
    """
    DataStore mínimo (reconstruído):
    - Liga à BD (por omissão: <raiz>/databases/ftv.db)
    - Instancia repositórios de produtos, ingredientes, auxiliares e preparação
    - Mantém cache de códigos (_ids) com reload_ids()
    - Fornece paginação (total, codigo_at)
    - Delegações para UI (info produto, PVPs, ingredientes, listas auxiliares, preparação)
    """

    def __init__(self, db_path=None, demo: bool=False):
        import sqlite3
        self.demo = bool(demo)

        # Caminho default: raiz do projeto /databases/ftv.db
        try:
            base = Path(__file__).resolve().parents[3]
        except Exception:
            base = Path('.').resolve()

        if db_path is None:
            db_path = str(base / 'databases' / 'ftv.db')

        self.conn = None
        if not self.demo:
            try:
                self.conn = sqlite3.connect(db_path)
                self.conn.row_factory = sqlite3.Row
            except Exception as e:
                print(f"[DataStore][AVISO] Falha a ligar à BD '{db_path}': {e}")
                self.conn = None

        # Repositórios
        self.produtos = None
        self.ingredientes = None
        self.aux = None
        self.prep = None
        try:
            from .repositories import ProdutosRepo, IngredientesRepo, AuxiliaresRepo, PreparacaoRepo
            if self.conn:
                self.produtos = ProdutosRepo(self.conn)
                self.ingredientes = IngredientesRepo(self.conn)
                self.aux = AuxiliaresRepo(self.conn)
                self.prep = PreparacaoRepo(self.conn)
        except Exception as e:
            print(f"[DataStore][AVISO] Falha a instanciar repositórios: {e}")

        # Cache de códigos
        self._ids = []
        try:
            self.reload_ids()
        except Exception as e:
            print(f"[DataStore][AVISO] reload_ids falhou: {e}")
            self._ids = []

    # ----------------------------
    # Cache / paginação
    # ----------------------------
    def reload_ids(self):
        """Recarrega a lista de códigos (_ids). Tenta repos 'produtos'; senão usa fichas_tecnicas."""
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
                    cur.execute("SELECT DISTINCT produto_codigo FROM fichas_tecnicas ORDER BY produto_codigo")
                    ids = [r[0] for r in cur.fetchall()]
            except Exception:
                ids = []
        self._ids = [str(x) for x in ids if x not in (None, "")]
        return len(self._ids)

    def total(self) -> int:
        return len(self._ids)

    def codigo_at(self, idx: int):
        if idx is None: return None
        if idx < 0 or idx >= len(self._ids): return None
        return self._ids[idx]

    # ----------------------------
    # Delegações principais
    # ----------------------------
    def get_produto_info(self, codigo: str):
        if not self.produtos: return {}
        try: return self.produtos.get_info(codigo)
        except Exception: return {}

    def get_pvps(self, codigo: str):
        if not self.produtos:
            return {"pvp1": None, "pvp2": None, "pvp3": None, "pvp4": None, "pvp5": None}
        try: return self.produtos.get_pvps(codigo)
        except Exception: return {"pvp1": None, "pvp2": None, "pvp3": None, "pvp4": None, "pvp5": None}

    def get_ingredientes(self, codigo: str):
        if not self.ingredientes: return []
        try: return self.ingredientes.listar_por_produto(codigo)
        except Exception: return []

    # Auxiliares (combos na UI)
    def list_tipos_artigos(self):
        if not self.aux: return [(None, "—")]
        try: return self.aux.list_tipos_artigos()
        except Exception: return [(None, "—")]

    def list_validade(self):
        if not self.aux: return [(None, "—")]
        try: return self.aux.list_validade()
        except Exception: return [(None, "—")]

    def list_temperaturas(self):
        if not self.aux: return [(None, "—")]
        try: return self.aux.list_temperaturas()
        except Exception: return [(None, "—")]

    # Preparação (B4)
    def get_preparacao_html(self, codigo: str) -> str:
        if not self.prep: return ""
        try: return self.prep.get_html(codigo)
        except Exception: return ""

    def save_preparacao_html(self, codigo: str, html: str) -> None:
        if not self.prep: return None
        try: self.prep.upsert_html(codigo, html)
        except Exception: pass
