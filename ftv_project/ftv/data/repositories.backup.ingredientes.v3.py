# Auto-gerado pela Fase 2 — repositories
import sqlite3

class ProdutosRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def listar_codigos(self):
        cur = self.conn.cursor()
        cur.execute("SELECT codigo FROM produtos ORDER BY codigo")
        return [r[0] for r in cur.fetchall()]

    def get_info(self, codigo: str):
        cur = self.conn.cursor()
        # Ajusta conforme o teu esquema real (mantemos simples e não destrutivo):
        cur.execute("SELECT * FROM produtos WHERE codigo = ?", (codigo,))
        row = cur.fetchone()
        if not row:
            return {}
        if hasattr(row, 'keys'):
            return {k: row[k] for k in row.keys()}
        return {}

    def get_pvps(self, codigo: str):
        cur = self.conn.cursor()
        # Ajusta conforme o teu esquema real (mantemos campos mais comuns):
        try:
            cur.execute("SELECT preco1, preco2 FROM produtos WHERE codigo = ?", (codigo,))
            r = cur.fetchone()
            p1 = r[0] if r and r[0] not in (None, "") else None
            p2 = r[1] if r and r[1] not in (None, "") else None
            return {"pvp1": p1, "pvp2": p2, "pvp3": None, "pvp4": None, "pvp5": None}
        except Exception:
            return {"pvp1": None, "pvp2": None, "pvp3": None, "pvp4": None, "pvp5": None}


class IngredientesRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def listar_por_produto(self, codigo: str):
        cur = self.conn.cursor()
        # Ajusta conforme o teu esquema real:
        try:
            cur.execute("SELECT ingrediente, quantidade, unidade FROM ingredientes WHERE produto_codigo = ?", (codigo,))
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception:
            return []


class AuxiliaresRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_tipos_artigos(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao FROM tipos_artigos WHERE ativo=1 ORDER BY descricao")
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except Exception:
            return [(None, "—")]

    def list_validade(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao FROM validade WHERE ativo=1 ORDER BY descricao")
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except Exception:
            return [(None, "—")]

    def list_temperaturas(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao FROM temperaturas WHERE ativo=1 ORDER BY descricao")
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except Exception:
            return [(None, "—")]


class PreparacaoRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_html(self, codigo: str) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT html FROM produto_preparacao WHERE produto_codigo = ?", (codigo,))
        row = cur.fetchone()
        return row[0] if row and row[0] else ""

    def upsert_html(self, codigo: str, html: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO produto_preparacao (produto_codigo, html) VALUES (?, ?) "
            "ON CONFLICT(produto_codigo) DO UPDATE SET html=excluded.html",
            (codigo, html),
        )
        self.conn.commit()
