from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets")

from data.datastore import DataStore
from services.products import ProductService
from ui.ui_editor_fonte import FTApp


def test_temperatura_persist_and_combo_update(qapp):
    ds = DataStore(db_path=":memory:")
    try:
        cur = ds.conn.cursor()
        cur.execute(
            "INSERT INTO Produtos "
            "(Codigo, Produto, TipoVenda, Temperatura) "
            "VALUES (?, ?, ?, ?)",
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
            assert ft.cbTemp.count() == 3
            assert ft.cbTemp.currentData() == 1
            ft.cbTemp.setCurrentIndex(2)
            qapp.processEvents()
            cur.execute(
                "SELECT Temperatura FROM Produtos WHERE Codigo = ?",
                ("P1",),
            )
            assert cur.fetchone()[0] == 2
            assert ft.cbTemp.currentData() == 2
        finally:
            ft.close()
    finally:
        ds.close()
