#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Caminhos robustos ---
import sys
import logging

# --- Qt ---
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from ftv.data.datastore import DataStore
from ftv.services.products import ProductService
from ftv.utils.autosave import wire_autosave_aux
from ftv.ui.ui_editor_fonte import FTApp


logger = logging.getLogger(__name__)
# --- UI principal ---


def _apply_global_theme(app):
    try:
        f = QFont()
        f.setPointSize(12)  # tamanho global 12pt
        app.setFont(f)
        # pode-se adicionar QSS leve aqui se precisares
    except Exception as e:
        logger.warning("[THEME] Falha a aplicar fonte global: %s", e)


def main():
    # Qt app
    app = QApplication(sys.argv)
    _apply_global_theme(app)

    # DataStore
    ds = DataStore()
    logger.info("[LAUNCHER] DataStore importado de: %s", DataStore.__module__)
    svc = ProductService(ds)

    # Janela
    wire_autosave_aux(FTApp, ds)

    win = FTApp(svc)
    win.show()

    # Loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
