"""Centralised stylesheet constants for the BWB style 1 theme."""

FIELD_STYLE = (
    "border:none;\n"
    "border-radius:4px;\n"
    "background-color: rgba(0, 0, 0, 0.1);\n"
    "qproperty-alignment: AlignLeft | AlignVCenter;\n"
)

LABEL_STYLE = (
    "QLabel {\n"
    "    background-color: rgba(200,200,200,0.5);\n"
    "    border: 1px solid rgba(0,0,0,0.3);\n"
    "    border-top-color: rgba(255,255,255,0.8);\n"
    "    border-left-color: rgba(255,255,255,0.8);\n"
    "    border-bottom-color: rgba(0,0,0,0.4);\n"
    "    border-right-color: rgba(0,0,0,0.4);\n"
    "    border-radius: 6px;\n"
    "    padding: 4px;\n"
    "    qproperty-alignment: AlignLeft | AlignVCenter;\n"
    "}\n"
    "QLabel:pressed {\n"
    "    background-color: rgba(200,200,200,0.8);\n"
    "}"
)

APP_STYLESHEET = (
    "QWidget {\n"
    "    background-color: rgba(255, 255, 255, 0.25);\n"
    "    border: 1px solid rgba(255, 255, 255, 0.3);\n"
    "    border-radius: 12px;\n"
    "}"
)

__all__ = ["FIELD_STYLE", "LABEL_STYLE", "APP_STYLESHEET"]
