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
    def __init__(self, conn):
        self.conn = conn

    def _infer_cols(self):
        """Lê o schema de 'fichas_tecnicas' e tenta inferir:
        - coluna do produto (produto_codigo / codigo_produto / produto / artigo / codigo …)
        - coluna do ingrediente (ingrediente / designacao / componente …)
        - coluna da quantidade (quantidade / qtd / qtde …)
        - coluna da unidade (unidade / unid / unidade_medida / uom …)
        Devolve um dicionário com os nomes reais: {prod, ingr, qty, unit}
        """
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA table_info(fichas_tecnicas)")
            cols = [r[1].lower() for r in cur.fetchall()]
        except Exception:
            return None

        def pick(cands):
            for c in cands:
                if c in cols:
                    return c
            for c in cols:
                for pref in ('produto_', 'artigo_', 'codigo_', 'cod_', 'fk_'):
                    if c.startswith(pref) and ('produto' in c or 'artigo' in c or 'codigo' in c or 'cod' in c):
                        return c
            return None

        prod = pick(['produto_codigo','codigo_produto','produto','artigo','codigo','cod_produto','codartigo','fk_produto'])
        ingr = pick(['ingrediente','ingredientes','designacao','componente','descricao','nome_ingrediente'])
        qty  = pick(['quantidade','qtd','qtde','quant','qte'])
        unit = pick(['unidade','unid','unidade_medida','uom','und','unidad'])

        return {'prod': prod, 'ingr': ingr, 'qty': qty, 'unit': unit}

    def listar_por_produto(self, codigo: str):
        """Devolve uma lista de dicts: [{'ingrediente':..., 'quantidade':..., 'unidade':...}, ...]
        Lê de 'fichas_tecnicas'. Em falta de colunas, devolve o que for possível.
        """
        cur = self.conn.cursor()
        cols = self._infer_cols()
        if not cols or not cols.get('prod'):
            return []

        prod_col = cols['prod']
        ingr_col = cols.get('ingr')
        qty_col  = cols.get('qty')
        unit_col = cols.get('unit')

        select_cols = []
        alias_map = {}

        if ingr_col:
            select_cols.append(ingr_col)
            alias_map[ingr_col] = 'ingrediente'
        if qty_col:
            select_cols.append(qty_col)
            alias_map[qty_col] = 'quantidade'
        if unit_col:
            select_cols.append(unit_col)
            alias_map[unit_col] = 'unidade'

        if not select_cols:
            try:
                cur.execute(f"SELECT COUNT(*) FROM fichas_tecnicas WHERE {prod_col} = ?", (codigo,))
                n = cur.fetchone()[0]
                return [{'ingrediente': None, 'quantidade': None, 'unidade': None} for _ in range(n)]
            except Exception:
                return []

        cols_sql = ", ".join(select_cols)
        try:
            cur.execute(f"SELECT {cols_sql} FROM fichas_tecnicas WHERE {prod_col} = ?", (codigo,))
            rows = cur.fetchall()
            out = []
            for r in rows:
                item = {'ingrediente': None, 'quantidade': None, 'unidade': None}
                for i, c in enumerate(select_cols):
                    item[alias_map.get(c, c)] = r[i]
                out.append(item)
            return out
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
