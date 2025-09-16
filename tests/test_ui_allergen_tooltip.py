from types import SimpleNamespace

from PyQt5.QtWidgets import QCheckBox

from domain.models import Product
from ui.ui_editor_fonte import FTApp


class _MissingPath:
    def exists(self):
        return False


class AllergenServiceStub:
    def __init__(self):
        aux_stub = SimpleNamespace(
            list_tipos_artigos_admin=lambda: [],
            add_tipo_artigo=lambda *args, **kwargs: None,
            set_tipo_artigo_ativo=lambda *args, **kwargs: None,
            update_tipo_artigo=lambda *args, **kwargs: None,
            list_validade_admin=lambda: [],
            add_validade=lambda *args, **kwargs: None,
            set_validade_ativo=lambda *args, **kwargs: None,
            update_validade=lambda *args, **kwargs: None,
            list_temperaturas_admin=lambda: [],
            add_temperatura=lambda *args, **kwargs: None,
            set_temperatura_ativo=lambda *args, **kwargs: None,
            update_temperatura=lambda *args, **kwargs: None,
            list_alergenios_admin=lambda: [],
            add_alergenio=lambda *args, **kwargs: None,
            update_alergenio=lambda *args, **kwargs: None,
        )
        self.ds = SimpleNamespace(
            aux=aux_stub,
            fcost=None,
            get_preparacao_html=lambda codigo: "",
            save_preparacao_html=lambda codigo, html: None,
            set_fcost_level=lambda level: None,
        )

    def total(self):
        return 1

    def codigo_at(self, idx):
        return "001"

    def list_tipos_artigos(self):
        return []

    def list_validade(self):
        return []

    def list_temperaturas(self):
        return []

    def list_active_allergens(self):
        return [(1, "Glúten")]

    def get_allergen_details(self, aid):
        return {"Exemplos": '["Pão", "Massa"]', "Notas": "Evitar contaminação"}

    def get_product_info(self, codigo):
        return Product(code=codigo or "001", name="Produto", pvps=[0], iva=23, ingredients=[])

    def calculate_cost(self, product):
        return 0

    def get_image_path(self, codigo):
        return _MissingPath()

    def save_product_image(self, codigo, src_path):
        return None

    def delete_product_image(self, codigo):
        return None

    def get_preparacao_image_path(self, codigo, idx):
        return _MissingPath()

    def save_preparacao_image(self, codigo, idx, src_path):
        return None

    def delete_preparacao_image(self, codigo, idx):
        return None


def test_allergen_checkbox_tooltip(qapp):
    service = AllergenServiceStub()
    ft = FTApp(service)
    try:
        checkboxes = ft.C5.findChildren(QCheckBox)
        tooltip_by_name = {cb.text(): cb.toolTip() for cb in checkboxes}
        expected = "Pão, Massa\nEvitar contaminação"
        assert tooltip_by_name["Glúten"] == expected
    finally:
        ft.close()
