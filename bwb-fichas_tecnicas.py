#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Caminhos robustos ---
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FTV_PROJ = ROOT / "ftv_project"
for p in (FTV_PROJ, ROOT):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# --- Qt ---
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from ftv.ui.ui_editor_fonte import FTApp
from ftv.utils.autosave import wire_autosave_aux

# --- DataStore (duas rotas possíveis) ---
def import_datastore():
    try:
        from ftv.data.datastore import DataStore
        return DataStore, "ftv.data.datastore"
    except ModuleNotFoundError:
        pass
    try:
        from ftv_project.ftv.data.datastore import DataStore
        return DataStore, "ftv_project.ftv.data.datastore"
    except ModuleNotFoundError as e:
        print("[LAUNCHER][ERRO] Não consegui importar DataStore nem de ftv.data.datastore nem de ftv_project.ftv.data.datastore")
        print("  sys.path inclui:", sys.path[:3], "…")
        raise

# --- UI principal ---

def _apply_global_theme(app):
    try:
        f = QFont()
        f.setPointSize(12)  # tamanho global 12pt
        app.setFont(f)
        # pode-se adicionar QSS leve aqui se precisares
    except Exception as e:
        print(f"[THEME] Falha a aplicar fonte global: {e}")


def main():
    # Qt app
    app = QApplication(sys.argv)
    _apply_global_theme(app)

    # DataStore
    DS, origin = import_datastore()
    print(f"[LAUNCHER] DataStore importado de: {origin}")
    ds = DS()

    # Janela
    wire_autosave_aux(FTApp, ds)

    win = FTApp(ds=ds)
    win.show()

    # Loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
