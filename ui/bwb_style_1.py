"""Centralised stylesheet constants for the BWB style 1 theme."""

OVERLAY_ON_CLASS = "bwb-style-overlays-on"

_ZONE_BASE_DECLARATIONS = (
    "background-color: rgba(255, 255, 255, 0.35);\n"
    "border: 1px solid rgba(0, 0, 0, 0.08);\n"
    "border-radius: 12px;\n"
    "padding: 6px;\n"
)

# ``bwb-style-1-center`` previously used a global ``text-align`` declaration to
# centre values.  This impacted every legend (``QLabel``) in the zone, which is
# now handled explicitly via ``AlignmentVariant`` helpers.  Keep the constant in
# case additional declarations are needed in the future.
_ZONE_CENTER_EXTRA = ""

ZONE_STYLES = {
    "bwb-style-1": _ZONE_BASE_DECLARATIONS,
    "bwb-style-1-center": _ZONE_BASE_DECLARATIONS + _ZONE_CENTER_EXTRA,
}

_FIELD_STYLE_TEMPLATE = (
    "QLineEdit {{\n"
    "{alignment_line}"
    "    border: none;\n"
    "    border-radius: 4px;\n"
    "    background: transparent;\n"
    "}}\n"
)

FIELD_STYLE = _FIELD_STYLE_TEMPLATE.format(alignment_line="")

CENTER_FIELD_STYLE = _FIELD_STYLE_TEMPLATE.format(
    alignment_line="    qproperty-alignment: AlignHCenter | AlignVCenter;\n",
)

_LABEL_STYLE_TEMPLATE = (
    "QLabel {{\n"
    "    background-color: rgba(200,200,200,0.5);\n"
    "    border: 1px solid rgba(0,0,0,0.3);\n"
    "    border-top-color: rgba(255,255,255,0.8);\n"
    "    border-left-color: rgba(255,255,255,0.8);\n"
    "    border-bottom-color: rgba(0,0,0,0.4);\n"
    "    border-right-color: rgba(0,0,0,0.4);\n"
    "    border-radius: 6px;\n"
    "    padding: 4px;\n"
    "{alignment_line}"
    "}}\n"
    "QLabel:pressed {{\n"
    "    background-color: rgba(200,200,200,0.8);\n"
    "}}"
)

LABEL_STYLE = _LABEL_STYLE_TEMPLATE.format(alignment_line="")

CENTER_LABEL_STYLE = _LABEL_STYLE_TEMPLATE.format(
    alignment_line="    qproperty-alignment: AlignHCenter | AlignVCenter;\n",
)

FCFILTER_BUTTON_STYLE_TEMPLATE = (
    "/* bwb-style-fcfilters-btn */\n"
    "QPushButton {{\n"
    "    background-color: rgba({r},{g},{b},{normal_alpha});\n"
    "    border: 1px solid rgba(0,0,0,0.3);\n"
    "    border-top-color: rgba(255,255,255,0.8);\n"
    "    border-left-color: rgba(255,255,255,0.8);\n"
    "    border-bottom-color: rgba(0,0,0,0.4);\n"
    "    border-right-color: rgba(0,0,0,0.4);\n"
    "    border-radius: 6px;\n"
    "    padding: 4px;\n"
    "}}\n"
    "QPushButton:pressed,\n"
    "QPushButton:checked {{\n"
    "    background-color: rgba({r},{g},{b},{active_alpha});\n"
    "}}\n"
)

APP_STYLESHEET = (
    "QWidget {\n"
    "    background-color: rgba(255, 255, 255, 0.25);\n"
    "    border: 1px solid rgba(255, 255, 255, 0.3);\n"
    "    border-radius: 12px;\n"
    "}\n\n"
    f"QLabel.{OVERLAY_ON_CLASS} {{\n"
    "    background: none;\n"
    "    border: none;\n"
    "    padding: 0;\n"
    "    qproperty-alignment: AlignLeft | AlignVCenter;\n"
    "}}\n"
)

__all__ = [
    "ZONE_STYLES",
    "FIELD_STYLE",
    "LABEL_STYLE",
    "CENTER_FIELD_STYLE",
    "CENTER_LABEL_STYLE",
    "OVERLAY_ON_CLASS",
    "FCFILTER_BUTTON_STYLE_TEMPLATE",
    "APP_STYLESHEET",
]
