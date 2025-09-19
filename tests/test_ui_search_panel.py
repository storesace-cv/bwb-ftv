from data.datastore import DataStore
from services.products import ProductService
from ui.ui_editor_fonte import FTApp


def _setup_ds():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Produtos")
    cur.execute("DELETE FROM FichasTecnicas")
    cur.execute("DELETE FROM PrecosTaxas")
    cur.execute(
        "INSERT INTO Produtos (Codigo, Produto, TipoVenda) VALUES (?, ?, 1)",
        ("P1", "Produto 1"),
    )
    cur.execute(
        (
            "INSERT INTO FichasTecnicas (ProdutoCodigo, ProdutoNome, ComponenteNome) "
            "VALUES (?, ?, ?)"
        ),
        ("P1", "Produto 1", "Tomate"),
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
        self.search_filters_calls: list[tuple[str | None, str | None]] = []

    def set_search_filters(
        self,
        *,
        produto: str | None = None,
        ingrediente: str | None = None,
    ) -> None:
        self.search_filters_calls.append((produto, ingrediente))
        super().set_search_filters(produto=produto, ingrediente=ingrediente)


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

        ft.searchProductField.setText("  Produto 1  ")
        ft.searchIngredientField.setText(" tomate ")
        ft.searchProductButton.click()
        qapp.processEvents()

        assert service.search_filters_calls[-1] == ("Produto 1", "tomate")
        assert ft.cur_index == 0

        ft.btSearchToggle.click()
        qapp.processEvents()
        assert not ft.searchContainer.isVisible()
        assert not ft.btSearchToggle.isChecked()

        ft.btSearchToggle.click()
        qapp.processEvents()
        assert ft.searchProductField.text() == "  Produto 1  "

        ft.searchIngredientField.setText("Queijo")
        ft.searchIngredientButton.click()
        qapp.processEvents()
        assert service.search_filters_calls[-1] == ("Produto 1", "Queijo")

        ft.searchProductField.setText("   ")
        ft.searchProductField.returnPressed.emit()
        qapp.processEvents()
        assert service.search_filters_calls[-1] == (None, "Queijo")
    finally:
        ft.close()
        ds.close()
