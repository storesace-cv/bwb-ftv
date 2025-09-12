# Auto-gerado pela Fase 2 — repositories
import logging
import sqlite3


logger = logging.getLogger(__name__)


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
        if hasattr(row, "keys"):
            return {k: row[k] for k in row.keys()}
        return {}

    def get_pvps(self, codigo: str):
        """Devolve {'pvp1', 'pvp2', 'pvp3', 'pvp4', 'pvp5'} a partir de produtos."""
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT preco1_g, preco2_g FROM produtos WHERE codigo = ?",
                (codigo,),
            )
            r = cur.fetchone()
            p1 = r[0] if r and r[0] not in (None, "") else None
            p2 = r[1] if r and r[1] not in (None, "") else None
            return {"pvp1": p1, "pvp2": p2, "pvp3": None, "pvp4": None, "pvp5": None}
        except sqlite3.Error as exc:
            logger.error("[ProdutosRepo] get_pvps(%s) falhou: %s", codigo, exc)
            return {
                "pvp1": None,
                "pvp2": None,
                "pvp3": None,
                "pvp4": None,
                "pvp5": None,
            }


class IngredientesRepo:
    def __init__(self, conn):
        self.conn = conn

    def _infer_cols(self):
        """Inferir colunas em 'fichas_tecnicas' com as preferências do esquema."""
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA table_info(fichas_tecnicas)")
            cols = [r[1].lower() for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error("[IngredientesRepo] _infer_cols falhou: %s", exc)
            return None

        def has(name):
            return name in cols

        def pick(cands):
            for c in cands:
                if c in cols:
                    return c
            # heurística por prefixos
            for c in cols:
                for pref in ("produto_", "artigo_", "codigo_", "cod_", "fk_"):
                    if c.startswith(pref) and any(
                        k in c for k in ("produto", "artigo", "codigo", "cod")
                    ):
                        return c
            return None

        # Preferências baseadas no teu schema real
        prod = (
            "produto_codigo"
            if has("produto_codigo")
            else pick(
                [
                    "codigo_produto",
                    "produto",
                    "artigo",
                    "codigo",
                    "cod_produto",
                    "codartigo",
                    "fk_produto",
                ]
            )
        )
        # ingrediente: prefere 'componente_nome'; admite alternativas
        ingr = (
            "componente_nome"
            if has("componente_nome")
            else pick(
                [
                    "ingrediente",
                    "ingredientes",
                    "designacao",
                    "componente",
                    "descricao",
                    "nome_ingrediente",
                    "componente_codigo",
                ]
            )
        )
        # quantidade & unidade
        qty = "qtd" if has("qtd") else pick(["quantidade", "qtde", "quant", "qte"])
        unit = (
            "unidade"
            if has("unidade")
            else pick(["unid", "unidade_medida", "uom", "und", "unidad"])
        )

        return {"prod": prod, "ingr": ingr, "qty": qty, "unit": unit}

    def listar_por_produto(self, codigo: str):
        """Devolve dados do produto em fichas_tecnicas."""
        """Lista dicts com chaves: ingrediente, nome, designacao, quantidade,
        qtd, QTD, unidade, ppu e total.
        """
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT componente_nome, qtd, unidade, ppu, custo "
                "FROM fichas_tecnicas "
                "WHERE produto_codigo = ? "
                "ORDER BY COALESCE(ordem, rowid)",
                (codigo,),
            )
            rows = cur.fetchall()
            out = []
            for r in rows:
                nome = r[0]
                qtd = r[1]
                unidade = r[2]
                ppu = r[3]
                total = r[4]
                item = {
                    "ingrediente": nome,
                    "nome": nome,
                    "designacao": nome,
                    "quantidade": qtd,
                    "qtd": qtd,
                    "QTD": qtd,
                    "unidade": unidade,
                    "ppu": ppu,
                    "total": total,
                }
                out.append(item)
            return out
        except sqlite3.Error as exc:
            logger.error(
                "[IngredientesRepo] listar_por_produto(%s) falhou: %s", codigo, exc
            )
            try:
                cur.execute("PRAGMA table_info(fichas_tecnicas)")
                cols = [c[1].lower() for c in cur.fetchall()]

                def has(x):
                    return x in cols

                sel = []
                alias = []
                if has("componente_nome"):
                    sel.append("componente_nome")
                    alias.append("nome")
                if has("qtd"):
                    sel.append("qtd")
                    alias.append("qtd")
                if has("unidade"):
                    sel.append("unidade")
                    alias.append("unidade")
                if has("ppu"):
                    sel.append("ppu")
                    alias.append("ppu")
                if has("custo"):
                    sel.append("custo")
                    alias.append("total")
                if not sel:
                    return []
                sql = "SELECT " + ", ".join(sel)
                cur.execute(sql, (codigo,))
                rows = cur.fetchall()
                out = []
                for r in rows:
                    base = {
                        "ingrediente": None,
                        "nome": None,
                        "designacao": None,
                        "quantidade": None,
                        "qtd": None,
                        "QTD": None,
                        "unidade": None,
                        "ppu": None,
                        "total": None,
                    }
                    tmp = {}
                    for i, a in enumerate(alias):
                        tmp[a] = r[i]
                    # preencher aliases
                    if "nome" in tmp and tmp["nome"] is not None:
                        base["ingrediente"] = base["nome"] = base["designacao"] = tmp[
                            "nome"
                        ]
                    if "qtd" in tmp and tmp["qtd"] is not None:
                        base["quantidade"] = base["qtd"] = base["QTD"] = tmp["qtd"]
                    for k in ("unidade", "ppu", "total"):
                        if k in tmp:
                            base[k] = tmp[k]
                    out.append(base)
                return out
            except sqlite3.Error as exc2:
                logger.error(
                    "[IngredientesRepo] fallback listar_por_produto(%s) falhou: %s",
                    codigo,
                    exc2,
                )
                return []


class AuxiliaresRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_tipos_artigos(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT cod, descricao FROM tipos_artigos WHERE ativo=1 ORDER BY cod"
            )
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] list_tipos_artigos falhou: %s", exc)
            return [(None, "—")]

    def list_validade(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT cod, descricao FROM validade WHERE ativo=1 ORDER BY cod"
            )
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] list_validade falhou: %s", exc)
            return [(None, "—")]

    def list_temperaturas(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT cod, descricao FROM temperaturas WHERE ativo=1 ORDER BY cod"
            )
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] list_temperaturas falhou: %s", exc)
            return [(None, "—")]

    # --- Métodos administrativos adicionados (CRUD) ---
    def list_tipos_artigos_admin(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao, ativo FROM tipos_artigos ORDER BY cod")
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] list_tipos_artigos_admin falhou: %s", exc)
            return []

    def add_tipo_artigo(self, descricao: str):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO tipos_artigos (descricao, ativo) VALUES (?, 1)",
                (descricao,),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] add_tipo_artigo falhou: %s", exc)
            return None

    def update_tipo_artigo(self, cod, descricao: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE tipos_artigos SET descricao=? WHERE cod=?",
                (descricao, cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] update_tipo_artigo(%s) falhou: %s", cod, exc)
            return False

    def set_tipo_artigo_ativo(self, cod, ativo: int) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE tipos_artigos SET ativo=? WHERE cod=?",
                (int(ativo), cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] set_tipo_artigo_ativo(%s) falhou: %s", cod, exc
            )
            return False

    def list_validade_admin(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao, ativo FROM validade ORDER BY cod")
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] list_validade_admin falhou: %s", exc)
            return []

    def add_validade(self, descricao: str):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO validade (descricao, ativo) VALUES (?, 1)",
                (descricao,),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] add_validade falhou: %s", exc)
            return None

    def update_validade(self, cod, descricao: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE validade SET descricao=? WHERE cod=?",
                (descricao, cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] update_validade(%s) falhou: %s", cod, exc)
            return False

    def set_validade_ativo(self, cod, ativo: int) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE validade SET ativo=? WHERE cod=?",
                (int(ativo), cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] set_validade_ativo(%s) falhou: %s", cod, exc)
            return False

    def list_temperaturas_admin(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao, ativo FROM temperaturas ORDER BY cod")
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] list_temperaturas_admin falhou: %s", exc)
            return []

    def add_temperatura(self, descricao: str):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO temperaturas (descricao, ativo) VALUES (?, 1)",
                (descricao,),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] add_temperatura falhou: %s", exc)
            return None

    def update_temperatura(self, cod, descricao: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE temperaturas SET descricao=? WHERE cod=?",
                (descricao, cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] update_temperatura(%s) falhou: %s", cod, exc)
            return False

    def set_temperatura_ativo(self, cod, ativo: int) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE temperaturas SET ativo=? WHERE cod=?",
                (int(ativo), cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] set_temperatura_ativo(%s) falhou: %s", cod, exc
            )
            return False

    # --- Produto Auxiliar (tabela canónica de FK de auxiliares) ---
    def get_produto_auxiliares(self, codigo: str):
        """Devolve (tipo_artigo_id, validade_id, temperatura_id) ou (None,None,None)."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT tipo_artigo_id, validade_id, temperatura_id "
                "FROM produto_auxiliar WHERE produto_codigo = ?",
                (codigo,),
            )
            row = cur.fetchone()
            if not row:
                return (None, None, None)
            try:
                return (
                    row["tipo_artigo_id"],
                    row["validade_id"],
                    row["temperatura_id"],
                )
            except (KeyError, IndexError, TypeError):
                return (
                    row[0] if len(row) > 0 else None,
                    row[1] if len(row) > 1 else None,
                    row[2] if len(row) > 2 else None,
                )
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] get_produto_auxiliares(%s) falhou: %s", codigo, exc
            )
            return (None, None, None)

    def set_produto_auxiliares(
        self, codigo: str, tipo_artigo_id, validade_id, temperatura_id
    ) -> None:
        """Upsert para a tabela produto_auxiliar."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO produto_auxiliar (produto_codigo, tipo_artigo_id, "
                "validade_id, temperatura_id) VALUES (?, ?, ?, ?) ON "
                "CONFLICT(produto_codigo) DO UPDATE SET "
                "tipo_artigo_id=excluded.tipo_artigo_id, "
                "validade_id=excluded.validade_id, "
                "temperatura_id=excluded.temperatura_id",
                (codigo, tipo_artigo_id, validade_id, temperatura_id),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] set_produto_auxiliares(%s) falhou: %s", codigo, exc
            )


class PreparacaoRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_html(self, codigo: str) -> str:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT html FROM produto_preparacao WHERE produto_codigo = ?", (codigo,)
        )
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
