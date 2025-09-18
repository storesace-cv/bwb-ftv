"""Compatibility layer keeping the legacy centred style module importable."""

from .bwb_style_1 import APP_STYLESHEET, FIELD_STYLE, LABEL_STYLE

__all__ = ["FIELD_STYLE", "LABEL_STYLE", "APP_STYLESHEET"]
