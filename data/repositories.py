# Auto-gerado pela Fase 2 — repositories
import logging
import sqlite3


logger = logging.getLogger(__name__)


class ProdutosRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def listar_codigos(self):
        cur = self.conn.cursor()
        cur.execute("SELECT Codigo FROM Produtos ORDER BY Codigo")
        return [r[0] for r in cur.fetchall()]

    def get_info(self, codigo: str):
        cur = self.conn.cursor()
        # Ajusta conforme o teu esquema real (mantemos simples e não destrutivo):
        cur.execute("SELECT * FROM Produtos WHERE Codigo = ?", (codigo,))
        row = cur.fetchone()
        if not row:
            return {}
        if hasattr(row, "keys"):
            # Normalise keys to lowercase for consistent access downstream.
            return {k.lower(): row[k] for k in row.keys()}
        return {}

    def get_pvps(self, codigo: str):
        """Devolve {'pvp1', 'pvp2', 'pvp3', 'pvp4', 'pvp5'} a partir de PrecosTaxas."""
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT Preco1, Preco2, Preco3, Preco4, Preco5 "
                "FROM PrecosTaxas WHERE Codigo = ?",
                (codigo,),
            )
            r = cur.fetchone()
            vals = []
            for i in range(5):
                val = r[i] if r and r[i] not in (None, "") else None
                if isinstance(val, str):
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                vals.append(val)
            return {
                "pvp1": vals[0],
                "pvp2": vals[1],
                "pvp3": vals[2],
                "pvp4": vals[3],
                "pvp5": vals[4],
            }
        except sqlite3.Error as exc:
            logger.error(
                "[ProdutosRepo] get_pvps(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )
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
        """Inferir colunas em 'FichasTecnicas' com as preferências do esquema."""
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA table_info(FichasTecnicas)")
            cols_raw = [r[1] for r in cur.fetchall()]
            cols = [c.lower() for c in cols_raw]
        except sqlite3.Error as exc:
            logger.error(
                "[IngredientesRepo] _infer_cols falhou: %s", exc, exc_info=True
            )
            return None

        def has(name: str) -> bool:
            return name.lower() in cols

        def pick(cands):
            for c in cands:
                if c.lower() in cols:
                    return cols_raw[cols.index(c.lower())]
            # heurística por prefixos
            for orig, c in zip(cols_raw, cols):
                for pref in ("produto", "artigo", "codigo", "cod", "fk"):
                    if c.startswith(pref) and any(
                        k in c for k in ("produto", "artigo", "codigo", "cod")
                    ):
                        return orig
            return None

        # Preferências baseadas no teu schema real
        prod = (
            "ProdutoCodigo"
            if has("ProdutoCodigo")
            else pick(
                [
                    "CodigoProduto",
                    "produto_codigo",
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
        """Devolve dados do produto em FichasTecnicas."""
        """Lista dicts com chaves: ingrediente, nome, designacao, quantidade,
        qtd, QTD, unidade, ppu e total.
        """
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA table_info(FichasTecnicas)")
            cols = [c[1].lower() for c in cur.fetchall()]
            if "total" in cols:
                cost_col = "total"
            elif "custo" in cols:
                cost_col = "custo"
            else:
                return []
            order_col = "ordem" if "ordem" in cols else "rowid"
            cur.execute(
                f"SELECT componente_nome, qtd, unidade, ppu, {cost_col} "
                "FROM FichasTecnicas "
                "WHERE ProdutoCodigo = ? "
                f"ORDER BY {order_col}",
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
                "[IngredientesRepo] listar_por_produto(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )
            try:
                cur.execute("PRAGMA table_info(FichasTecnicas)")
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
                if has("total"):
                    sel.append("total")
                    alias.append("total")
                elif has("custo"):
                    sel.append("custo")
                    alias.append("total")
                if not sel:
                    return []
                sql = (
                    "SELECT "
                    + ", ".join(sel)
                    + " FROM FichasTecnicas WHERE ProdutoCodigo=?"
                )
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
                    exc_info=True,
                )
                return []


class AuxiliaresRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_tipos_artigos(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT cod, descricao FROM TiposArtigos WHERE ativo=1 ORDER BY cod"
            )
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_tipos_artigos falhou: %s", exc, exc_info=True
            )
            return [(None, "—")]

    def list_validade(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT cod, descricao FROM Validade WHERE ativo=1 ORDER BY cod"
            )
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_validade falhou: %s", exc, exc_info=True
            )
            return [(None, "—")]

    def list_temperaturas(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT cod, descricao FROM Temperaturas WHERE ativo=1 ORDER BY cod"
            )
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_temperaturas falhou: %s", exc, exc_info=True
            )
            return [(None, "—")]

    # --- Métodos administrativos adicionados (CRUD) ---
    def list_tipos_artigos_admin(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao, ativo FROM TiposArtigos ORDER BY cod")
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_tipos_artigos_admin falhou: %s",
                exc,
                exc_info=True,
            )
            return []

    def add_tipo_artigo(self, descricao: str):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO TiposArtigos (descricao, ativo) VALUES (?, 1)",
                (descricao,),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] add_tipo_artigo falhou: %s", exc, exc_info=True
            )
            return None

    def update_tipo_artigo(self, cod, descricao: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE TiposArtigos SET descricao=? WHERE cod=?",
                (descricao, cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] update_tipo_artigo(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def set_tipo_artigo_ativo(self, cod, ativo: int) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE TiposArtigos SET ativo=? WHERE cod=?",
                (int(ativo), cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] set_tipo_artigo_ativo(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def list_validade_admin(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao, ativo FROM Validade ORDER BY cod")
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_validade_admin falhou: %s",
                exc,
                exc_info=True,
            )
            return []

    def add_validade(self, descricao: str):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO Validade (descricao, ativo) VALUES (?, 1)",
                (descricao,),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            logger.error("[AuxiliaresRepo] add_validade falhou: %s", exc, exc_info=True)
            return None

    def update_validade(self, cod, descricao: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE Validade SET descricao=? WHERE cod=?",
                (descricao, cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] update_validade(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def set_validade_ativo(self, cod, ativo: int) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE Validade SET ativo=? WHERE cod=?",
                (int(ativo), cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] set_validade_ativo(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def list_temperaturas_admin(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT cod, descricao, ativo FROM Temperaturas ORDER BY cod")
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_temperaturas_admin falhou: %s",
                exc,
                exc_info=True,
            )
            return []

    def add_temperatura(self, descricao: str):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO Temperaturas (descricao, ativo) VALUES (?, 1)",
                (descricao,),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] add_temperatura falhou: %s", exc, exc_info=True
            )
            return None

    def update_temperatura(self, cod, descricao: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE Temperaturas SET descricao=? WHERE cod=?",
                (descricao, cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] update_temperatura(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def set_temperatura_ativo(self, cod, ativo: int) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE Temperaturas SET ativo=? WHERE cod=?",
                (int(ativo), cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] set_temperatura_ativo(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False


class PreparacaoRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_html(self, codigo: str) -> str:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT Html FROM ProdutoPreparacao WHERE ProdutoCodigo = ?", (codigo,)
        )
        row = cur.fetchone()
        return row[0] if row and row[0] else ""

    def upsert_html(self, codigo: str, html: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO ProdutoPreparacao (ProdutoCodigo, Html) VALUES (?, ?) "
            "ON CONFLICT(ProdutoCodigo) DO UPDATE SET Html=excluded.Html",
            (codigo, html),
        )
        self.conn.commit()
