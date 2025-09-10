# Fichas Técnicas Valorizadas — UI (Single-file)
#
# Regras Aprovadas (manter sempre no topo e cumprir em TODO o código)
# -------------------------------------------------------------------
# 1) Nomenclatura de Blocos e Células
#    - Blocos: [B1] Dados Gerais, [B2] Ingredientes, [B3] Custos, [B4] Preparação, [B5] Nutrição / Alergénios.
#    - Célula raiz do bloco: Cn (ex.: C1, C2, C3, C4, C5).
#    - Divisão horizontal: sufixos .A (esq.) e .B (dir.).
#    - Divisão vertical: sufixos .1 (topo) e .2 (base).
#    - Subdivisões encadeiam-se mantendo a regra (ex.: C1.A.2.B).
#    - NÃO usar nomes ad hoc (ex.: C3.X, C3AA, C3AB).
#
# 2) Changelog: toda alteração documentada deve incluir data/hora (Europe/Lisbon)
#    - Formato: YYYY-MM-DD HH:MM — descrição.
#
# Changelog
# ---------
# 2025-09-08 16:06 — v3.64 — Alinhamento de nomenclatura em B3 (C3) & reforço de comentários; split vertical em C1.A.2 com dados no topo; Custo Total = soma da coluna "Total".
# 2025-09-08 17:35 — v3.73 — Restabelecido: botão Overlay no topo esquerdo; navegação no rodapé; scroll vertical; mantidas alterações pedidas (C3 swap, remoção C1.A.2.B.2, tags visíveis).
# 2025-09-08 18:05 — v3.80 — Reintroduzidos [B4] Preparação e [B5] Alergénios; overlays/cores preservados; footer com contador.
# 2025-09-08 18:40 — v3.82 — C1.A.2.B ligado à BD (tipos/validade/temperaturas) com pré-seleção por FK; preservado layout.
# 2025-09-08 19:05 — v3.84 — Menu → Tabelas abre diálogos de gestão (listar ativos, adicionar, inativar) para Tipos/Validade/Temperaturas.
# 2025-09-08 19:30 — v3.87 — Consolidação parcial das alterações sem tocar no layout base.
# 2025-09-08 19:45 — v3.88 — CONSOLIDAÇÃO FINAL:
#    • C1.A.2.A dividido (topo: Família/Sub-família; base: PVP1..PVP5 com etiqueta por cima e valor por baixo; leitura PVP1..2 de precos_taxas).
#    • C1.A.2.B: combos ligados às tabelas auxiliares (ativo=1, ordenadas) com pré-seleção por FK do produto.
#    • B2: grelha 50/10/10/14/16 + Código oculto; cálculo Total por linha quando necessário.
#    • B3: C3.A.A = Custo Total (soma da coluna “Total”); C3.A.B = “Food Cost:” (placeholder).
#    • B4: editor de Preparação com toolbar simples; B5: Alergénios 2×N com persistência N–N.
#    • Menu: QToolButton (InstantPopup) sem caret; Base de Dados / Tabelas / Utilitários; diálogos de gestão nas Tabelas.
#    • Overlays/cores preservados; navegação centrada no rodapé; scroll vertical; cabeçalho em comentários.

import os, sys, json, sqlite3
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QPushButton, QSizePolicy, QTableWidget,
    QTableWidgetItem, QMessageBox, QScrollArea, QShortcut, QTextEdit, QCheckBox
)
from ftv.data.datastore import DataStore

APP_TITLE = "Fichas Técnicas Valorizadas"
DEV_OVERLAYS = True  # Ctrl+D alterna

# ------------------------ Data Layer ------------------------
