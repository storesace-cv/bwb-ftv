"""Repositories for data access."""

import logging
import sqlite3
from collections.abc import Iterable

from utils.formatting import parse_decimal


logger = logging.getLogger(__name__)


def quote_ident(name: str) -> str:
    """Return *name* quoted as an SQL identifier.

    Any existing double quotes are doubled to preserve them inside the
    identifier.
    """
    return '"' + name.replace('"', '""') + '"'


class ProdutosRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def listar_codigos(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT p.Codigo
            FROM Produtos p
            JOIN FichasTecnicas ft ON ft.ProdutoCodigo = p.Codigo
            WHERE p.TipoVenda = 1
            ORDER BY p.Codigo
            """
        )
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

    def get_pvps(self, codigo: str) -> dict[str, list[float | None] | float | None]:
        """Devolve ``{"pvps", "iva"}`` a partir de ``PrecosTaxas``."""

        cur = self.conn.cursor()
        try:
            cur.execute(
                (
                    "SELECT Preco1, Preco2, Preco3, Preco4, Preco5, Iva1, Iva2 "
                    "FROM PrecosTaxas WHERE Codigo = ?"
                ),
                (codigo,),
            )
            r = cur.fetchone()
            if not r:
                return {"pvps": [], "iva": None}

            prices_raw = r[:5]
            iva_raw = r[5]

            pvps: list[float | None] = []
            for price in prices_raw:
                if price in (None, ""):
                    pvps.append(None)
                    continue
                if isinstance(price, str):
                    price = parse_decimal(price)
                    if isinstance(price, str):
                        try:
                            price = float(price)
                        except ValueError:
                            price = None
                pvps.append(price)

            iva = iva_raw if iva_raw not in (None, "") else None
            if isinstance(iva, str):
                iva = parse_decimal(iva)
                if isinstance(iva, str):
                    try:
                        iva = float(iva)
                    except ValueError:
                        iva = None

            return {"pvps": pvps, "iva": iva}
        except sqlite3.Error as exc:
            logger.error(
                "[ProdutosRepo] get_pvps(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )
            return {"pvps": [], "iva": None}

    def set_tipo_artigo(self, codigo: str, tipo_cod) -> bool:
        """Atualiza o campo ``TipoArtigo`` de um produto."""
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE Produtos SET TipoArtigo = ? WHERE Codigo = ?",
                (tipo_cod, codigo),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[ProdutosRepo] set_tipo_artigo(%s, %s) falhou: %s",
                codigo,
                tipo_cod,
                exc,
                exc_info=True,
            )
            return False

    def set_validade(self, codigo: str, validade_cod) -> bool:
        """Atualiza o campo ``Validade`` de um produto."""
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE Produtos SET Validade = ? WHERE Codigo = ?",
                (validade_cod, codigo),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[ProdutosRepo] set_validade(%s, %s) falhou: %s",
                codigo,
                validade_cod,
                exc,
                exc_info=True,
            )
            return False

    def set_temperatura(self, codigo: str, temperatura_cod) -> bool:
        """Atualiza o campo ``Temperatura`` de um produto."""
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE Produtos SET Temperatura = ? WHERE Codigo = ?",
                (temperatura_cod, codigo),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[ProdutosRepo] set_temperatura(%s, %s) falhou: %s",
                codigo,
                temperatura_cod,
                exc,
                exc_info=True,
            )
            return False

    def get_product_allergens(self, codigo: str) -> list[int]:
        """Return allergen identifiers associated with ``codigo``."""

        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT AlergenioId
            FROM ProdutoAlergenio
            WHERE ProdutoCodigo = ?
            ORDER BY AlergenioId
            """,
            (codigo,),
        )
        result: list[int] = []
        for row in cur.fetchall():
            try:
                value = row["AlergenioId"]  # type: ignore[index]
            except (KeyError, TypeError):
                value = row[0] if row else None
            try:
                if value is not None and str(value).strip() != "":
                    result.append(int(value))
            except (TypeError, ValueError):
                continue
        return result

    def set_product_allergens(
        self, codigo: str, allergen_ids: Iterable[int | str | None]
    ) -> bool:
        """Persist the allergen identifiers associated with ``codigo``."""

        if not codigo:
            return False

        normalised: list[int] = []
        for aid in allergen_ids:
            if aid in (None, ""):
                continue
            try:
                normalised.append(int(aid))
            except (TypeError, ValueError):
                continue
        unique_ids = sorted(set(normalised))

        cur = self.conn.cursor()
        try:
            cur.execute(
                "DELETE FROM ProdutoAlergenio WHERE ProdutoCodigo = ?",
                (codigo,),
            )
            if unique_ids:
                cur.executemany(
                    "INSERT INTO ProdutoAlergenio (ProdutoCodigo, AlergenioId) "
                    "VALUES (?, ?)",
                    [(codigo, aid) for aid in unique_ids],
                )
            self.conn.commit()
            return True
        except sqlite3.Error as exc:
            self.conn.rollback()
            logger.error(
                "[ProdutosRepo] set_product_allergens(%s, %s) falhou: %s",
                codigo,
                unique_ids,
                exc,
                exc_info=True,
            )
            return False


class IngredientesRepo:
    def __init__(self, conn):
        self.conn = conn

    def listar_por_produto(self, codigo: str):
        """Devolve dados do produto em ``FichasTecnicas``.

        Retorna uma lista de dicts com as chaves canónicas
        ``ComponenteNome``, ``Qtd``, ``Unidade``, ``Ppu``, ``Preco``,
        ``Peso`` e ``ComponenteCodigo``.

        Pode ainda incluir as chaves suplementares ``FamiliaSubfamilia``,
        ``Familia`` e ``Subfamilia`` quando presentes na base de dados.
        """

        cur = self.conn.cursor()
        pragma_rows = self.conn.execute("PRAGMA table_info(FichasTecnicas)").fetchall()
        known_columns = {row[1].lower() for row in pragma_rows}

        has_peso = "peso" in known_columns
        has_familia = "familiasubfamilia" in known_columns

        peso_expression = "Peso" if has_peso else "NULL AS Peso"
        familia_sub_expr = (
            "FamiliaSubfamilia" if has_familia else "NULL AS FamiliaSubfamilia"
        )
        if has_familia:
            familia_expr = """
                TRIM(
                    CASE
                        WHEN instr(COALESCE(FamiliaSubfamilia, ''), '>') > 0 THEN SUBSTR(
                            COALESCE(FamiliaSubfamilia, ''),
                            1,
                            instr(COALESCE(FamiliaSubfamilia, ''), '>') - 1
                        )
                        ELSE COALESCE(FamiliaSubfamilia, '')
                    END
                ) AS Familia
            """
            subfamilia_expr = """
                TRIM(
                    CASE
                        WHEN instr(COALESCE(FamiliaSubfamilia, ''), '>') > 0 THEN SUBSTR(
                            COALESCE(FamiliaSubfamilia, ''),
                            instr(COALESCE(FamiliaSubfamilia, ''), '>') + 1
                        )
                        ELSE ''
                    END
                ) AS Subfamilia
            """
        else:
            familia_expr = "NULL AS Familia"
            subfamilia_expr = "NULL AS Subfamilia"

        query = f"""
            SELECT
                ComponenteNome,
                Qtd,
                Unidade,
                Ppu,
                Preco,
                {peso_expression},
                ComponenteCodigo,
                {familia_sub_expr},
                {familia_expr},
                {subfamilia_expr}
            FROM FichasTecnicas
            WHERE TRIM(ProdutoCodigo) = TRIM(?)
            ORDER BY Familia, Subfamilia, Ordem, ComponenteNome
        """

        try:
            cur.execute(query, (codigo,))
            rows = cur.fetchall()
            columns = [col[0] for col in cur.description or []]
        except sqlite3.Error as exc:
            logger.error(
                "[IngredientesRepo] listar_por_produto(%s) falhou: %s",
                codigo,
                exc,
                exc_info=True,
            )
            return []

        out = []
        for row in rows:
            out.append({name: row[idx] for idx, name in enumerate(columns)})
        return out


class AuxiliaresRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --- Helpers para operações administrativas genericamente ---

    def _admin_list(
        self,
        table: str,
        log_label: str,
        *,
        id_col: str = "cod",
        desc_col: str = "descricao",
        active_col: str = "ativo",
    ):
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"SELECT {id_col}, {desc_col}, {active_col} "
                f"FROM {table} ORDER BY {id_col}"
            )
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error(f"[AuxiliaresRepo] {log_label} falhou: %s", exc, exc_info=True)
            return []

    def _admin_add(
        self,
        table: str,
        log_label: str,
        descricao: str,
        *,
        desc_col: str = "descricao",
        active_col: str = "ativo",
    ):
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"INSERT INTO {table} ({desc_col}, {active_col}) VALUES (?, 1)",
                (descricao,),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            logger.error(f"[AuxiliaresRepo] {log_label} falhou: %s", exc, exc_info=True)
            return None

    def _admin_set_active(
        self,
        table: str,
        log_label: str,
        cod,
        ativo: int,
        *,
        id_col: str = "cod",
        active_col: str = "ativo",
    ) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"UPDATE {table} SET {active_col}=? WHERE {id_col}=?",
                (int(ativo), cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                f"[AuxiliaresRepo] {log_label}(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def list_tipos_artigos(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT Cod, Descricao FROM TiposArtigos")
            rows = cur.fetchall()
            return [(r[0], r[1]) for r in rows]
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_tipos_artigos falhou: %s", exc, exc_info=True
            )
            return []

    def list_validade(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT Cod, Descricao FROM Validade ORDER BY Cod")
            rows = cur.fetchall()
            return [(None, "—")] + [(r[0], r[1]) for r in rows]
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "no such table" in msg:
                logger.warning(
                    "[AuxiliaresRepo] tabela Validade ausente; execute migrations"
                )
                raise RuntimeError("Tabela Validade ausente") from exc
            logger.error(
                "[AuxiliaresRepo] list_validade falhou: %s", exc, exc_info=True
            )
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_validade falhou: %s", exc, exc_info=True
            )
        return [(None, "—")]

    def list_temperaturas(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT Cod, Descricao FROM Temperaturas ORDER BY Cod")
            rows = cur.fetchall()
            return [(r[0], r[1]) for r in rows]
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "no such table" in msg:
                logger.warning(
                    "[AuxiliaresRepo] tabela Temperaturas ausente; execute migrations"
                )
                raise RuntimeError("Tabela Temperaturas ausente") from exc
            logger.error(
                "[AuxiliaresRepo] list_temperaturas falhou: %s", exc, exc_info=True
            )
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_temperaturas falhou: %s", exc, exc_info=True
            )
        return []

    # --- Métodos administrativos adicionados (CRUD) ---
    def list_tipos_artigos_admin(self):
        return self._admin_list("TiposArtigos", "list_tipos_artigos_admin")

    def add_tipo_artigo(self, descricao: str):
        return self._admin_add("TiposArtigos", "add_tipo_artigo", descricao)

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
        return self._admin_set_active(
            "TiposArtigos", "set_tipo_artigo_ativo", cod, ativo
        )

    def delete_tipo_artigo(self, cod) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM Produtos WHERE TipoArtigo = ?", (cod,))
            if cur.fetchone()[0]:
                return False
            cur.execute("DELETE FROM TiposArtigos WHERE cod = ?", (cod,))
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] delete_tipo_artigo(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def list_validade_admin(self):
        return self._admin_list("Validade", "list_validade_admin")

    def add_validade(self, descricao: str):
        return self._admin_add("Validade", "add_validade", descricao)

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
        return self._admin_set_active("Validade", "set_validade_ativo", cod, ativo)

    def delete_validade(self, cod) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM Produtos WHERE Validade = ?", (cod,))
            if cur.fetchone()[0]:
                return False
            cur.execute("DELETE FROM Validade WHERE cod = ?", (cod,))
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] delete_validade(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def list_temperaturas_admin(self):
        return self._admin_list("Temperaturas", "list_temperaturas_admin")

    def add_temperatura(self, descricao: str):
        return self._admin_add("Temperaturas", "add_temperatura", descricao)

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
        return self._admin_set_active(
            "Temperaturas", "set_temperatura_ativo", cod, ativo
        )

    def delete_temperatura(self, cod) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM Produtos WHERE Temperatura = ?", (cod,))
            if cur.fetchone()[0]:
                return False
            cur.execute("DELETE FROM Temperaturas WHERE cod = ?", (cod,))
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] delete_temperatura(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def list_alergenios_admin(self):
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA table_info(Alergenios)")
            columns = {row[1] for row in cur.fetchall()}
            if "Ativo" in columns:
                return self._admin_list(
                    "Alergenios",
                    "list_alergenios_admin",
                    id_col="Id",
                    desc_col="Nome",
                    active_col="Ativo",
                )
            cur.execute("SELECT Id, Nome FROM Alergenios ORDER BY Id")
            return [(r[0], r[1], 1) for r in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] list_alergenios_admin falhou: %s",
                exc,
                exc_info=True,
            )
            return []

    def add_alergenio(self, nome: str, nome_ingles: str | None = None):
        nome_ingles = nome if nome_ingles is None else nome_ingles
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO Alergenios (Nome, NomeIngles) VALUES (?, ?)",
                (nome, nome_ingles),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] add_alergenio falhou: %s",
                exc,
                exc_info=True,
            )
            return None

    def update_alergenio(
        self, cod, nome: str, nome_ingles: str | None = None
    ) -> bool:
        nome_ingles = nome if nome_ingles is None else nome_ingles
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE Alergenios SET Nome=?, NomeIngles=? WHERE Id=?",
                (nome, nome_ingles, cod),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] update_alergenio(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False

    def set_alergenio_ativo(self, cod, ativo: int) -> bool:
        return self._admin_set_active(
            "Alergenios",
            "set_alergenio_ativo",
            cod,
            ativo,
            id_col="Id",
            active_col="Ativo",
        )

    def delete_alergenio(self, cod) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute("DELETE FROM Alergenios WHERE Id = ?", (cod,))
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                "[AuxiliaresRepo] delete_alergenio(%s) falhou: %s",
                cod,
                exc,
                exc_info=True,
            )
            return False


class PreparacaoRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ProdutoPreparacao (
                    ProdutoCodigo TEXT PRIMARY KEY,
                    Html          TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.commit()
        except sqlite3.Error as exc:
            logger.error(
                "[PreparacaoRepo] falha a criar tabela ProdutoPreparacao: %s",
                exc,
                exc_info=True,
            )

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


class FcostValuesRepo:
    """Repository for accessing and updating ``FcostValues`` levels."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_levels(self):
        """Return all cost levels ordered by ``Nivel``."""

        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT Nivel, Nome, ValorMin, ValorMax, Comentario "
                "FROM FcostValues ORDER BY Nivel"
            )
            return cur.fetchall()
        except sqlite3.Error as exc:
            logger.error(
                "[FcostValuesRepo] list_levels() falhou: %s", exc, exc_info=True
            )
            return []

    def get_range(self, nivel: int) -> tuple[float, float] | None:
        """Return ``(ValorMin, ValorMax)`` for ``nivel`` or ``None`` if missing."""

        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT ValorMin, ValorMax FROM FcostValues WHERE Nivel = ?",
                (nivel,),
            )
            row = cur.fetchone()
            if not row:
                return None

            vmin, vmax = row[0], row[1]
            vmin = parse_decimal(vmin)
            vmax = parse_decimal(vmax)
            try:
                return float(vmin), float(vmax)
            except (TypeError, ValueError):
                return None
        except sqlite3.Error as exc:
            logger.error(
                "[FcostValuesRepo] get_range(%s) falhou: %s",
                nivel,
                exc,
                exc_info=True,
            )
            return None

    def update_range(self, nivel: int, vmin, vmax) -> bool:
        """Update the ``ValorMin`` and ``ValorMax`` for a level."""

        vmin = parse_decimal(vmin)
        vmax = parse_decimal(vmax)
        try:
            vmin_f = float(vmin)
            vmax_f = float(vmax)
        except (TypeError, ValueError):
            return False

        cur = self.conn.cursor()
        try:
            cur.execute("BEGIN")

            if not (vmin_f < vmax_f):
                self.conn.rollback()
                return False

            # Verify previous level
            cur.execute(
                "SELECT ValorMax FROM FcostValues WHERE Nivel < ? "
                "ORDER BY Nivel DESC LIMIT 1",
                (nivel,),
            )
            prev = cur.fetchone()
            if prev and vmin_f < prev[0]:
                self.conn.rollback()
                return False

            # Verify next level
            cur.execute(
                "SELECT ValorMin FROM FcostValues WHERE Nivel > ? "
                "ORDER BY Nivel ASC LIMIT 1",
                (nivel,),
            )
            nxt = cur.fetchone()
            if nxt and vmax_f > nxt[0]:
                self.conn.rollback()
                return False

            cur.execute(
                "UPDATE FcostValues SET ValorMin = ?, ValorMax = ? WHERE Nivel = ?",
                (vmin_f, vmax_f, nivel),
            )
            if cur.rowcount == 0:
                self.conn.rollback()
                return False

            self.conn.commit()
            return True
        except sqlite3.Error as exc:
            logger.error(
                "[FcostValuesRepo] update_range(%s, %s, %s) falhou: %s",
                nivel,
                vmin,
                vmax,
                exc,
                exc_info=True,
            )
            self.conn.rollback()
            return False
