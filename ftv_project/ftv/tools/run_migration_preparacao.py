#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fase 3 — Executar migração de preparação (produto_preparacao)
Uso: python3 ftv_project/ftv/tools/run_migration_preparacao.py

- Assume a BD em ./databases/ftv.db
- Assume o SQL em ./ftv_project/ftv/data/migrations/preparacao.sql
  - Não altera UI nem código da app. Apenas cria/valida a tabela necessária.
  - Fornece mensagens de debug detalhadas em caso de erro
    (linha/coluna do SQL e contexto).

Exit codes:
  0 = sucesso
  2 = ficheiro(s) em falta
  3 = erro de execução SQL
  4 = BD não é um ficheiro SQLite válido ou não abriu
"""
import logging
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("databases") / "ftv.db"
SQL_PATH = Path("ftv_project") / "ftv" / "data" / "migrations" / "preparacao.sql"


logger = logging.getLogger(__name__)


def die(code, msg):
    logger.error("[MIGRAÇÃO][ERRO] %s", msg)
    sys.exit(code)


def main():
    if not SQL_PATH.exists():
        die(2, f"SQL de migração em falta: {SQL_PATH}")
    if not DB_PATH.exists():
        die(2, f"Base de dados em falta: {DB_PATH}")

    sql = SQL_PATH.read_text(encoding="utf-8")

    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        die(4, f"Falha a abrir a BD: {DB_PATH} :: {e}")

    try:
        with conn:
            conn.executescript(sql)
        # Sanidade mínima: tabela existe?
        cur = conn.execute()
        row = cur.fetchone()
        if not row:
            die(
                3,
            )
        logger.info("[MIGRAÇÃO] Sucesso. Tabela 'produto_preparacao' pronta.")
    except sqlite3.Error as e:
        logger.debug("[MIGRAÇÃO][DEBUG] Traceback completo:", exc_info=True)
        die(3, f"Erro SQLite ao executar migração: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
