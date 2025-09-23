#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fase 3 — Executar migração do bloco [B4] PREPARAÇÃO (produto_preparacao)
Uso: python3 tools/run_migration_preparacao.py
(pode ser executado a partir de qualquer diretório)

- Procura a BD em <root>/databases/ftv.db
- Procura o SQL em <root>/data/migrations/preparacao.sql
  - Não altera UI nem código da app. Apenas cria/valida a tabela necessária.
  - Fornece mensagens de debug detalhadas em caso de erro
    (linha/coluna do SQL e contexto).

Exit codes:
  0 = sucesso
  2 = ficheiro(s) em falta
  3 = erro de execução SQL
  4 = BD não é um ficheiro SQLite válido ou não abriu
  5 = falha ao fechar a base de dados após a migração
"""
import logging
import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.paths import get_project_root  # noqa: E402
from data.datastore import DataStore  # noqa: E402
import data.migration as migration  # noqa: E402

base = get_project_root()
DB_PATH = base / "databases" / "ftv.db"
SQL_PATH = base / "data" / "migrations" / "preparacao.sql"


logger = logging.getLogger(__name__)


def die(code, msg):
    logger.error("[MIGRAÇÃO][ERRO] %s", msg)
    sys.exit(code)


def main():
    if not SQL_PATH.exists():
        die(2, f"Ficheiro SQL de migração não encontrado: {SQL_PATH}")
    if not DB_PATH.exists():
        die(2, f"Base de dados não encontrada: {DB_PATH}")

    pending = DataStore.pending_migrations(DB_PATH)
    if not any(p.name == SQL_PATH.name for p in pending):
        logger.info("[MIGRAÇÃO] Nenhuma migração 'preparacao.sql' pendente.")
        return

    sql = SQL_PATH.read_text(encoding="utf-8")
    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        die(4, f"Falha ao abrir a base de dados {DB_PATH}: {e}")

    try:
        with conn:
            conn.executescript(sql)
            table = migration._ensure_schema_table(conn)
            conn.execute(
                f"INSERT INTO {table}(Filename) VALUES (?)", (SQL_PATH.name,)
            )
        try:
            cur = conn.execute("SELECT 1 FROM produto_preparacao LIMIT 1")
            cur.fetchone()
        except sqlite3.Error:
            die(3, "Tabela 'produto_preparacao' ausente após migração")
        logger.info("[MIGRAÇÃO] Sucesso. Tabela 'produto_preparacao' pronta.")
    except sqlite3.Error as e:
        logger.debug("[MIGRAÇÃO][DEBUG] Traceback completo:", exc_info=True)
        die(3, f"Erro SQLite ao executar migração: {e}")
    finally:
        try:
            conn.close()
        except sqlite3.Error as exc:
            logger.warning(
                "[MIGRAÇÃO][AVISO] Falha ao fechar a base de dados: %s", exc
            )
            sys.exit(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
