from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets", "PyQt5.QtCore")

from data.datastore import DataStore
from services.products import ProductService, _UNSET
from ui.layout import Zone
from ui.ui_editor_fonte import FTApp


def _setup_ds():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Produtos")
    cur.execute("DELETE FROM FichasTecnicas")
    cur.execute("DELETE FROM PrecosTaxas")
    products = [
        ("P1", "Produto 1", 1, "Pratos Quentes", "Hambúrgueres"),
        ("P2", "Salada Fresca", 1, "Pratos Frios", "Saladas"),
        ("P3", "Sopa do Dia", 1, None, None),
    ]
    cur.executemany(
        (
            "INSERT INTO Produtos "
            "(Codigo, Produto, TipoVenda, Familia, SubFamilia) "
            "VALUES (?, ?, ?, ?, ?)"
        ),
        products,
    )
    fichas = [
        (
            "P1",
            "Produto 1",
            "Tomate",
            "Pratos Quentes > Hambúrgueres",
        ),
        (
            "P2",
            "Salada Fresca",
            "Alface",
            "Pratos Frios > Saladas",
        ),
        ("P3", "Sopa do Dia", "Cenoura", "Sopas > Cremes"),
    ]
    cur.executemany(
        (
            "INSERT INTO FichasTecnicas (ProdutoCodigo, ProdutoNome, ComponenteNome, FamiliaSubfamilia) "
            "VALUES (?, ?, ?, ?)"
        ),
        fichas,
    )
    cur.execute(
        (
            "INSERT INTO PrecosTaxas (Codigo, Loja, Preco1, Preco2, Preco3, Preco4, Preco5, Iva1) "
            "VALUES ('P1', '1', 10, 10, 10, 10, 10, 23)"
        )
    )
    ds.conn.commit()
    ds.reload_ids()
    return ds


class RecordingService(ProductService):
    def __init__(self, ds):
        super().__init__(ds)
        self.search_filters_calls: list[
            tuple[
                str | None,
                str | None,
                tuple[str, ...] | None,
                tuple[str, ...] | None,
            ]
        ] = []
        self._family_data = {
            "Pratos Quentes": ("Hambúrgueres",),
            "Sopas": ("Cremes",),
            "Pratos Frios": ("Saladas",),
        }

    def set_search_filters(
        self,
        *,
        produto: str | None = None,
        ingrediente: str | None = None,
        familia: object = _UNSET,
        subfamilia: object = _UNSET,
    ) -> None:
        super().set_search_filters(
            produto=produto,
            ingrediente=ingrediente,
            familia=familia,
            subfamilia=subfamilia,
        )
        self.search_filters_calls.append(
            (
                getattr(self.ds, "_product_filter", None),
                getattr(self.ds, "_ingredient_filter", None),
                getattr(self.ds, "_family_filter", None),
                getattr(self.ds, "_subfamily_filter", None),
            )
        )

    def list_family_hierarchy(self) -> dict[str, tuple[str, ...]]:
        return self._family_data


def test_search_panel_toggle_and_submit(qapp):
    ds = _setup_ds()
    service = RecordingService(ds)
    ft = FTApp(service)
    try:
        assert not ft.searchContainer.isVisible()
        assert not ft.btSearchToggle.isChecked()

        ft.btSearchToggle.click()
        qapp.processEvents()

        assert ft.searchContainer.isVisible()
        assert ft.btSearchToggle.isChecked()
        assert ft.searchProductField.hasFocus()
        assert isinstance(ft.searchLeftZone, Zone)
        assert ft.searchResetButton.text() == "Mostrar todos os registos"
        assert ft.searchFamilyResetButton.text() == "Mostrar todas as famílias"
        assert ft.searchFamilyCombo.selected_items() == []
        assert ft.searchSubfamilyCombo.selected_items() == []

        ft.searchProductField.setText("  Produto 1  ")
        ft.searchIngredientField.setText(" tomate ")
        ft.searchFamilyCombo.select_items(["Pratos Quentes", "Sopas"])
        qapp.processEvents()
        subfamily_model = ft.searchSubfamilyCombo.model()
        assert subfamily_model is not None
        available_subs = {
            subfamily_model.item(i).text()
            for i in range(subfamily_model.rowCount())
            if subfamily_model.item(i) is not None
        }
        assert available_subs == {"Cremes", "Hambúrgueres"}
        assert ft.searchSubfamilyCombo.selected_items() == []
        ft.searchSubfamilyCombo.select_items(["Hambúrgueres", "Cremes"])
        qapp.processEvents()
        ft.searchProductButton.click()
        qapp.processEvents()

        assert service.search_filters_calls[-1] == (
            "Produto 1",
            "tomate",
            ("Pratos Quentes", "Sopas"),
            ("Cremes", "Hambúrgueres"),
        )
        assert ft.cur_index == 0

        ft.btSearchToggle.click()
        qapp.processEvents()
        assert not ft.searchContainer.isVisible()
        assert not ft.btSearchToggle.isChecked()

        ft.btSearchToggle.click()
        qapp.processEvents()
        assert ft.searchProductField.text() == "  Produto 1  "
        assert ft.searchFamilyCombo.selected_items() == ["Pratos Quentes", "Sopas"]
        assert ft.searchSubfamilyCombo.selected_items() == [
            "Cremes",
            "Hambúrgueres",
        ]

        ft.searchIngredientField.setText("Queijo")
        ft.searchIngredientButton.click()
        qapp.processEvents()
        assert service.search_filters_calls[-1] == (
            "Produto 1",
            "Queijo",
            ("Pratos Quentes", "Sopas"),
            ("Cremes", "Hambúrgueres"),
        )

        ft.searchProductField.setText("   ")
        ft.searchProductField.returnPressed.emit()
        qapp.processEvents()
        assert service.search_filters_calls[-1] == (
            None,
            "Queijo",
            ("Pratos Quentes", "Sopas"),
            ("Cremes", "Hambúrgueres"),
        )

        ft.searchProductField.setText("Produto 1")
        ft.searchIngredientField.setText("Cebola")
        ft.searchResetButton.click()
        qapp.processEvents()

        assert ft.searchProductField.text() == ""
        assert ft.searchIngredientField.text() == ""
        assert ft.searchFamilyCombo.selected_items() == ["Pratos Quentes", "Sopas"]
        assert ft.searchSubfamilyCombo.selected_items() == [
            "Cremes",
            "Hambúrgueres",
        ]
        assert service.search_filters_calls[-1] == (
            None,
            None,
            ("Pratos Quentes", "Sopas"),
            ("Cremes", "Hambúrgueres"),
        )
        assert ft.cur_index == 0

        ft.searchProductField.setText("Produto 2")
        ft.searchIngredientField.setText("Alface")
        ft.searchFamilyResetButton.click()
        qapp.processEvents()

        assert ft.searchProductField.text() == "Produto 2"
        assert ft.searchIngredientField.text() == "Alface"
        assert ft.searchFamilyCombo.selected_items() == []
        assert ft.searchSubfamilyCombo.selected_items() == []
        assert service.search_filters_calls[-1] == (
            "Produto 2",
            "Alface",
            None,
            None,
        )
    finally:
        ft.close()
        ds.close()
