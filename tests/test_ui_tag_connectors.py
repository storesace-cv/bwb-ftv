from __future__ import annotations

import types

import pytest
from PyQt5.QtWidgets import QCheckBox

from services.products import ProductService
from ui.layout import Zone
from ui.tagging import zone_tag, zone_tag_map
from ui.ui_editor_fonte import FTApp
from utils.formatting import format_pt_number


class TagAwareDataStore:
    """Data store stub exposing the API exercised by :class:`FTApp`."""

    def __init__(self) -> None:
        self._saved_allergens: list[tuple[str, list[int]]] = []
        self.aux = types.SimpleNamespace()
        self.fcost = None

    # -- navigation -----------------------------------------------------
    def total(self) -> int:
        return 1

    def codigo_at(self, idx: int) -> str:
        return "P1"

    # -- lookup tables --------------------------------------------------
    def list_tipos_artigos(self):
        return [(1, "Base"), (2, "Premium")]

    def list_validade(self):
        return [(3, "7 dias"), (4, "30 dias")]

    def list_temperaturas(self):
        return [(5, "Frio"), (6, "Congelado")]

    def list_active_allergens(self):
        return [(10, "Ovos"), (11, "Leite")]

    def get_allergen_details(self, aid):
        if aid == 10:
            return {"Exemplos": '["Omelete"]', "Notas": "Evitar contaminação"}
        if aid == 11:
            return {"Exemplos": "", "Notas": "Traços possíveis"}
        return {}

    # -- product payload ------------------------------------------------
    def get_produto_info(self, codigo):
        return {
            "codigo": codigo,
            "produto": "Produto Especial",
            "familia": "Pastelaria",
            "subfamilia": "Doces",
            "tipoartigo": 2,
            "validade": 3,
            "temperatura": 5,
        }

    def get_pvps(self, codigo):
        return {"pvps": [12.5, 9.75], "iva": 23}

    def get_ingredientes(self, codigo):
        return [
            {
                "ComponenteNome": "Farinha",
                "Qtd": 1,
                "Unidade": "kg",
                "Ppu": 2.0,
                "Preco": 2.0,
                "ComponenteCodigo": "A1",
            }
        ]

    def get_product_allergens(self, codigo):
        return [10]

    # -- mutations ------------------------------------------------------
    def set_product_allergens(self, codigo, allergen_ids):
        self._saved_allergens.append((codigo, [int(a) for a in allergen_ids]))
        return True

    def set_tipo_artigo(self, *_args, **_kwargs):
        return True

    def set_validade(self, *_args, **_kwargs):
        return True

    def set_temperatura(self, *_args, **_kwargs):
        return True

    # -- preparation html -----------------------------------------------
    def get_preparacao_html(self, _codigo):
        return ""

    def save_preparacao_html(self, _codigo, _html):
        return None

    def set_fcost_level(self, _level):
        return None


@pytest.fixture
def tag_service():
    ds = TagAwareDataStore()
    return ProductService(ds)


_ZONE_TAG_CACHE = dict(zone_tag_map())


def _tag_with_fallback(key: str, fallback: str) -> str:
    return _ZONE_TAG_CACHE.get(key, fallback)


def _collect_zone_tags(ft: FTApp, include_header: bool = False) -> set[str]:
    return {
        zone.tag
        for zone in ft._iter_layout_children(Zone, include_header=include_header)
    }


def test_iter_layout_children_covers_block_roots(qapp, tag_service):
    ft = FTApp(tag_service)
    try:
        block_tags = {
            zone_tag("general_root"),
            zone_tag("family_root"),
            _tag_with_fallback("pvps_root", "B1.C1.A.2.B.B"),
            zone_tag("ingredients_root"),
            zone_tag("food_cost_root"),
            zone_tag("preparation_root"),
            zone_tag("allergens_root"),
        }
        assert block_tags.issubset(_collect_zone_tags(ft))
        pvps_column_tags = {
            _tag_with_fallback("pvps_grid", "B1.C1.A.2.B.B.1"),
            _tag_with_fallback("pvps_col_1", "B1.C1.A.2.B.B.1.1"),
            _tag_with_fallback("pvps_col_2", "B1.C1.A.2.B.B.1.2"),
            _tag_with_fallback("pvps_col_3", "B1.C1.A.2.B.B.1.3"),
            _tag_with_fallback("pvps_col_4", "B1.C1.A.2.B.B.1.4"),
            _tag_with_fallback("pvps_col_5", "B1.C1.A.2.B.B.1.5"),
        }
        assert pvps_column_tags.issubset(_collect_zone_tags(ft))
        header_tags = _collect_zone_tags(ft, include_header=True)
        assert zone_tag("header_root") in header_tags
        for tag in block_tags | pvps_column_tags:
            assert ft.findChild(Zone, tag) is not None
        combos_wrapper = ft.findChild(
            Zone, _tag_with_fallback("family_combos_wrapper", "B1.C1.A.2.B")
        )
        combos_section = ft.findChild(
            Zone, _tag_with_fallback("family_combos_section", "B1.C1.A.2.B.A")
        )
        pvps_zone = ft.findChild(
            Zone, _tag_with_fallback("pvps_root", "B1.C1.A.2.B.B")
        )
        pvps_grid_zone = ft.findChild(
            Zone, _tag_with_fallback("pvps_grid", "B1.C1.A.2.B.B.1")
        )
        assert combos_wrapper is not None
        assert combos_section is not None
        assert pvps_zone is not None
        assert pvps_grid_zone is not None
        assert combos_section.parentWidget() is combos_wrapper
        assert pvps_zone.parentWidget() is combos_wrapper
        assert pvps_grid_zone.parentWidget() is pvps_zone
    finally:
        ft.close()


def test_load_record_populates_new_tag_widgets(qapp, tag_service):
    ft = FTApp(tag_service)
    try:
        assert ft.lbFamiliaVal.text() == "Pastelaria"
        assert ft.lbSubFamiliaVal.text() == "Doces"
        assert ft.cbTipos.currentText() == "Premium"
        assert ft.cbValidade.currentText() == "7 dias"
        assert ft.cbTemp.currentText() == "Frio"
        assert ft.lbPVPs[0].text() == format_pt_number(12.5)
        assert ft.lbPVPs[1].text() == format_pt_number(9.75)
        checkboxes = ft._allergen_checkboxes
        assert 10 in checkboxes and 11 in checkboxes
        assert checkboxes[10].isChecked()
        assert isinstance(ft.B7_C1.findChild(QCheckBox), QCheckBox)
    finally:
        ft.close()
