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
        """Devolve {'pvp1', 'pvp2', 'pvp3', 'pvp4', 'pvp5'} a partir de precos_taxas."""
        cur = self.conn.cursor()
        try:
            # Preferir ativo=1 se existir; escolher linha mais recente
            cur.execute(
                "SELECT preco1_g, preco2_g FROM precos_taxas "
                "WHERE codigo = ? AND (CASE WHEN EXISTS(SELECT 1 FROM pragma_table_info('precos_taxas') WHERE name='ativo') THEN ativo=1 ELSE 1 END) "
                "ORDER BY rowid DESC LIMIT 1",
                (codigo,)
            )
            r = cur.fetchone()
            p1 = r[0] if r and r[0] not in (None, '') else None
            p2 = r[1] if r and r[1] not in (None, '') else None
            return {'pvp1': p1, 'pvp2': p2, 'pvp3': None, 'pvp4': None, 'pvp5': None}
        except Exception:
            return {'pvp1': None, 'pvp2': None, 'pvp3': None, 'pvp4': None, 'pvp5': None}


class IngredientesRepo:
    def __init__(self, conn):
        self.conn = conn

    def _infer_cols(self):
        """Inferir colunas em 'fichas_tecnicas', com preferências explícitas do teu esquema."""
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA table_info(fichas_tecnicas)")
            cols = [r[1].lower() for r in cur.fetchall()]
        except Exception:
            return None

        def has(name): return name in cols
        def pick(cands):
            for c in cands:
                if c in cols: return c
            # heurística por prefixos
            for c in cols:
                for pref in ('produto_', 'artigo_', 'codigo_', 'cod_', 'fk_'):
                    if c.startswith(pref) and any(k in c for k in ('produto','artigo','codigo','cod')):
                        return c
            return None

        # Preferências baseadas no teu schema real
        prod = 'produto_codigo' if has('produto_codigo') else pick(['codigo_produto','produto','artigo','codigo','cod_produto','codartigo','fk_produto'])
        # ingrediente: prefere 'componente_nome'; admite alternativas
        ingr = 'componente_nome' if has('componente_nome') else pick(['ingrediente','ingredientes','designacao','componente','descricao','nome_ingrediente','componente_codigo'])
        # quantidade & unidade
        qty  = 'qtd' if has('qtd') else pick(['quantidade','qtde','quant','qte'])
        unit = 'unidade' if has('unidade') else pick(['unid','unidade_medida','uom','und','unidad'])

        return {'prod': prod, 'ingr': ingr, 'qty': qty, 'unit': unit}

    def listar_por_produto(self, codigo: str):
        """Devolve [{'ingrediente', 'quantidade', 'unidade'}] para um produto em 'fichas_tecnicas'."""
        """Devolve uma lista de dicts com chaves: ingrediente, quantidade, unidade, ppu, total."""
        cur = self.conn.cursor()
        try:
            # Preferência por nomes reais do teu schema
            cur.execute(
                "SELECT componente_nome, qtd, unidade, ppu, custo "
                "FROM fichas_tecnicas "
                "WHERE produto_codigo = ? "
                "ORDER BY COALESCE(ordem, rowid)",
                (codigo,)
            )
            rows = cur.fetchall()
            out = []
            for r in rows:
                out.append({
                    'ingrediente': r[0],
                    'quantidade': r[1],
                    'unidade': r[2],
                    'ppu': r[3],
                    'total': r[4],
                })
            return out
        except Exception:
            # Fallback heurístico caso schema varie
            try:
                # detectar colunas presentes
                cur.execute("PRAGMA table_info(fichas_tecnicas)")
                cols = [c[1].lower() for c in cur.fetchall()]
                has = lambda x: x in cols
                sel = []
                alias = []
                if has('componente_nome'): sel.append('componente_nome'); alias.append('ingrediente')
                if has('qtd'): sel.append('qtd'); alias.append('quantidade')
                if has('unidade'): sel.append('unidade'); alias.append('unidade')
                if has('ppu'): sel.append('ppu'); alias.append('ppu')
                if has('custo'): sel.append('custo'); alias.append('total')
                if not sel:
                    return []
                sql = "SELECT " + ", ".join(sel) + " FROM fichas_tecnicas WHERE produto_codigo = ? ORDER BY COALESCE(ordem, rowid)"
                cur.execute(sql, (codigo,))
                rows = cur.fetchall()
                out = []
                for r in rows:
                    item = {'ingrediente': None, 'quantidade': None, 'unidade': None, 'ppu': None, 'total': None}
                    for i, a in enumerate(alias):
                        item[a] = r[i]
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
