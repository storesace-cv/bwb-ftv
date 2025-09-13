from ui.ui_editor_fonte import FTApp
from services.products import ProductService
from data.datastore import DataStore


def test_validade_persist_and_combo_update(qapp):
    ds = DataStore(db_path=":memory:")
    try:
        cur = ds.conn.cursor()
        cur.execute(
            "INSERT INTO Produtos "
            "(Codigo, Produto, TipoVenda, Validade) VALUES (?, ?, ?, ?)",
            ("P1", "Prod", 1, 1),
        )
        cur.execute(
            "INSERT INTO FichasTecnicas (ProdutoCodigo) VALUES (?)",
            ("P1",),
        )
        ds.conn.commit()
        ds.reload_ids()

        service = ProductService(ds)
        ft = FTApp(service)
        try:
            assert ft.cbValidade.count() == 3
            assert ft.cbValidade.currentData() == 1
            ft.cbValidade.setCurrentIndex(2)
            qapp.processEvents()
            cur.execute(
                "SELECT Validade FROM Produtos WHERE Codigo = ?",
                ("P1",),
            )
            assert cur.fetchone()[0] == 2
            assert ft.cbValidade.currentData() == 2
        finally:
            ft.close()
    finally:
        ds.close()
