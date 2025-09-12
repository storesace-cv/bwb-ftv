#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fase 3 — Teste de fumo para Bloco [B4] Preparação
Uso (na raiz do projeto):
  python3 ftv_project/ftv/tools/test_prep_cli.py --codigo ABC123 --html "<p>Teste</p>"
  python3 ftv_project/ftv/tools/test_prep_cli.py --codigo ABC123 --file ./exemplo.html
  python3 ftv_project/ftv/tools/test_prep_cli.py            # tenta descobrir 1º código existente

O que faz:
- Abre ./databases/ftv.db
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

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ftv_project.ftv.utils import get_project_root
PROJECT_ROOT = get_project_root()

import argparse, sqlite3, traceback

DB_PATH = Path("databases") / "ftv.db"


def _load_preparacao_repo():
    try:
        from ftv_project.ftv.data.repositories import PreparacaoRepo
        return PreparacaoRepo
    except Exception as e:
        print(
            "[TESTE][ERRO] Não consigo importar PreparacaoRepo. Confirme se a Fase 2 foi aplicada corretamente.",
            file=sys.stderr,
        )
        traceback.print_exc()
        sys.exit(2)

def pick_first_codigo(conn):
    try:
        cur = conn.execute("SELECT codigo FROM produtos ORDER BY codigo LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None
    except Exception:
        traceback.print_exc()
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codigo", help="Código do produto (se omisso, tenta obter o 1º existente).")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--html", help="HTML a gravar")
    g.add_argument("--file", help="Ficheiro com HTML a gravar")
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"[TESTE][ERRO] Base de dados não encontrada: {DB_PATH}", file=sys.stderr)
        sys.exit(2)

    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"[TESTE][ERRO] Falha a abrir a BD: {DB_PATH} :: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        PreparacaoRepo = _load_preparacao_repo()
        repo = PreparacaoRepo(conn)

        codigo = args.codigo
        if not codigo:
            codigo = pick_first_codigo(conn)
            if not codigo:
                print("[TESTE][ERRO] Não foi possível descobrir um código em 'produtos'.", file=sys.stderr)
                sys.exit(3)
            print(f"[TESTE] Usar código detetado: {codigo}")

        print(f"[TESTE] Ler HTML atual de '{codigo}'...")
        before = repo.get_html(codigo)
        print(f"[TESTE] HTML atual (primeiros 120 chars): {before[:120]!r}")

        if args.html or args.file:
            new_html = args.html
            if args.file:
                try:
                    new_html = Path(args.file).read_text(encoding="utf-8")
                except Exception as e:
                    print(f"[TESTE][ERRO] Falha a ler ficheiro {args.file}: {e}", file=sys.stderr)
                    sys.exit(3)

            print(f"[TESTE] A gravar novo HTML ({len(new_html)} chars)...")
            repo.upsert_html(codigo, new_html)
            print("[TESTE] Gravado. A reler...")
            after = repo.get_html(codigo)
            ok = (after == new_html)
            print(f"[TESTE] Comparação pós-gravação: {'OK' if ok else 'FALHOU'}")
            if not ok:
                print("[TESTE][ERRO] O HTML lido não corresponde ao gravado.", file=sys.stderr)
                sys.exit(3)
        else:
            print("[TESTE] Sem --html/--file: nada para gravar (apenas leitura).")

        print("[TESTE] Sucesso.")
        sys.exit(0)

    except Exception as e:
        print("[TESTE][ERRO] Exceção inesperada:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(3)
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
