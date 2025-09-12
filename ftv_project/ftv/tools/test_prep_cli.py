#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fase 3 — Teste de fumo para Bloco [B4] Preparação
Uso (executar como módulo):
  python -m ftv.tools.test_prep_cli --codigo ABC123 --html "<p>Teste</p>"
  python -m ftv.tools.test_prep_cli --codigo ABC123 --file ./exemplo.html
  python -m ftv.tools.test_prep_cli            # tenta descobrir 1º código existente

O que faz:
- Abre <raiz do projeto>/databases/ftv.db (usando get_project_root)
- Usa PreparacaoRepo diretamente (sem UI) para ler e escrever HTML
- Mostra debug detalhado de cada passo e falhas com traceback

Exit codes:
  0 = sucesso
  2 = ficheiros em falta
  3 = erro na operação
"""
__test__ = False
from pathlib import Path
import sys
import logging

from ftv.utils import get_project_root

import argparse, sqlite3

DB_PATH = get_project_root() / "databases" / "ftv.db"


logger = logging.getLogger(__name__)


def _load_preparacao_repo():
    try:
        from ftv.data.repositories import PreparacaoRepo
        return PreparacaoRepo
    except Exception:
        logger.exception(
            "[TESTE][ERRO] Não consigo importar PreparacaoRepo. Confirme se a Fase 2 foi aplicada corretamente."
        )
        sys.exit(2)

def pick_first_codigo(conn):
    try:
        cur = conn.execute("SELECT codigo FROM produtos ORDER BY codigo LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None
    except Exception:
        logger.exception("Erro ao obter primeiro código")
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codigo", help="Código do produto (se omisso, tenta obter o 1º existente).")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--html", help="HTML a gravar")
    g.add_argument("--file", help="Ficheiro com HTML a gravar")
    args = ap.parse_args()

    if not DB_PATH.exists():
        logger.error("[TESTE][ERRO] Base de dados não encontrada: %s", DB_PATH)
        sys.exit(2)

    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        logger.error("[TESTE][ERRO] Falha a abrir a BD: %s :: %s", DB_PATH, e)
        sys.exit(2)

    try:
        PreparacaoRepo = _load_preparacao_repo()
        repo = PreparacaoRepo(conn)

        codigo = args.codigo
        if not codigo:
            codigo = pick_first_codigo(conn)
            if not codigo:
                logger.error("[TESTE][ERRO] Não foi possível descobrir um código em 'produtos'.")
                sys.exit(3)
            logger.info("[TESTE] Usar código detetado: %s", codigo)

        logger.info("[TESTE] Ler HTML atual de '%s'...", codigo)
        before = repo.get_html(codigo)
        logger.debug("[TESTE] HTML atual (primeiros 120 chars): %r", before[:120])

        if args.html or args.file:
            new_html = args.html
            if args.file:
                try:
                    new_html = Path(args.file).read_text(encoding="utf-8")
                except Exception as e:
                    logger.error("[TESTE][ERRO] Falha a ler ficheiro %s: %s", args.file, e)
                    sys.exit(3)

            logger.info("[TESTE] A gravar novo HTML (%d chars)...", len(new_html))
            repo.upsert_html(codigo, new_html)
            logger.info("[TESTE] Gravado. A reler...")
            after = repo.get_html(codigo)
            ok = (after == new_html)
            logger.info("[TESTE] Comparação pós-gravação: %s", "OK" if ok else "FALHOU")
            if not ok:
                logger.error("[TESTE][ERRO] O HTML lido não corresponde ao gravado.")
                sys.exit(3)
        else:
            logger.info("[TESTE] Sem --html/--file: nada para gravar (apenas leitura).")

        logger.info("[TESTE] Sucesso.")
        sys.exit(0)

    except Exception:
        logger.exception("[TESTE][ERRO] Exceção inesperada:")
        sys.exit(3)
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
