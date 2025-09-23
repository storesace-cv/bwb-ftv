from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets")

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from data.datastore import DataStore
from services.products import ProductService
from ui.ui_editor_fonte import FTApp
from ui.utilities import FOOD_COST_LEVEL_RGB_MAP, food_cost_lineedit_stylesheet
from utils.formatting import parse_decimal


def _setup_ds():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Produtos")
    cur.execute("DELETE FROM FichasTecnicas")
    cur.execute("DELETE FROM PrecosTaxas")
    cur.execute("DELETE FROM FcostValues")
    cur.executemany(
        "INSERT INTO FcostValues (Nivel, Nome, ValorMin, ValorMax, Comentario) VALUES (?, ?, ?, ?, '')",
        [
            (1, 'Bom', 20, 30),
            (2, 'Aceitável', 31, 60),
            (3, 'Mau', 61, 100),
        ],
    )
    cur.executemany(
        "INSERT INTO Produtos (Codigo, Produto, TipoVenda) VALUES (?, ?, 1)",
        [
            ('P1', 'Produto 1'),
            ('P2', 'Produto 2'),
            ('P3', 'Produto 3'),
        ],
    )
    cur.executemany(
        "INSERT INTO FichasTecnicas (ProdutoCodigo, Preco) VALUES (?, ?)",
        [
            ('P1', 10),
            ('P2', 10),
            ('P3', 10),
        ],
    )
    # Helper to compute price for desired food cost percentage
    def pvp_for(fc):
        return 1230 / fc
    cur.executemany(
        (
            "INSERT INTO PrecosTaxas (Codigo, Loja, Preco1, Preco2, Preco3, Preco4, Preco5, Iva1) "
            "VALUES (?, '1', ?, ?, ?, ?, ?, 23)"
        ),
        [
            # P1: FCs within 20-30
            (
                'P1',
                pvp_for(25),
                pvp_for(26),
                pvp_for(27),
                pvp_for(28),
                pvp_for(29),
            ),
            # P2: FCs within 31-60
            (
                'P2',
                pvp_for(35),
                pvp_for(40),
                pvp_for(45),
                pvp_for(50),
                pvp_for(55),
            ),
            # P3: FCs within 61-100
            (
                'P3',
                pvp_for(65),
                pvp_for(70),
                pvp_for(75),
                pvp_for(80),
                pvp_for(90),
            ),
        ],
    )
    ds.conn.commit()
    ds.reload_ids()
    return ds


def _assert_fc_in_range(ft, vmin, vmax):
    for lbl in ft.lbFoodCosts:
        val = parse_decimal(lbl.text())
        if isinstance(val, float):
            assert vmin <= val <= vmax


def test_fcost_filter_levels(qapp):
    ds = _setup_ds()
    service = ProductService(ds)
    ft = FTApp(service)
    assert service.ds._ids == ['P1', 'P2', 'P3']

    expected_styles = {
        1: food_cost_lineedit_stylesheet(FOOD_COST_LEVEL_RGB_MAP['Bom']),
        2: food_cost_lineedit_stylesheet(FOOD_COST_LEVEL_RGB_MAP['Aceitável']),
        3: food_cost_lineedit_stylesheet(FOOD_COST_LEVEL_RGB_MAP['Mau']),
    }

    ft._on_fcost_filter_selected(1)
    assert service.ds._ids == ['P1']
    assert ft.current_product.code == 'P1'
    _assert_fc_in_range(ft, 20, 30)
    assert {lbl.styleSheet() for lbl in ft.lbFoodCosts} == {expected_styles[1]}

    ft._on_fcost_filter_selected(2)
    assert service.ds._ids == ['P2']
    assert ft.current_product.code == 'P2'
    _assert_fc_in_range(ft, 31, 60)
    assert {lbl.styleSheet() for lbl in ft.lbFoodCosts} == {expected_styles[2]}

    ft._on_fcost_filter_selected(3)
    assert service.ds._ids == ['P3']
    assert ft.current_product.code == 'P3'
    _assert_fc_in_range(ft, 61, 100)
    assert {lbl.styleSheet() for lbl in ft.lbFoodCosts} == {expected_styles[3]}

    # toggle off filter
    ft._on_fcost_filter_selected(3)
    assert service.ds._ids == ['P1', 'P2', 'P3']
    assert ft.current_product.code == 'P1'
    ft.close()
    ds.close()


def test_fcost_filter_reset(qapp):
    ds = _setup_ds()
    service = ProductService(ds)
    ft = FTApp(service)
    ft._on_fcost_filter_selected(2)
    assert service.ds._ids == ['P2']
    ft.btFcostReset.click()
    assert service.ds._ids == ['P1', 'P2', 'P3']
    assert ft._active_fcost_filter is None
    ft.close()
    ds.close()


def test_fcost_field_style_missing_values(qapp):
    ds = _setup_ds()
    service = ProductService(ds)
    ft = FTApp(service)

    neutral_style = food_cost_lineedit_stylesheet(FOOD_COST_LEVEL_RGB_MAP['Todos'])

    product = ft.current_product
    ft.edCustoTotal.setText('10')
    product.pvps = [None] * 5
    product.iva = 23
    ft._update_food_costs()
    assert {lbl.styleSheet() for lbl in ft.lbFoodCosts} == {neutral_style}
    assert all(lbl.text() == '--N/A--' for lbl in ft.lbFoodCosts)

    product.pvps = [10] * 5
    product.iva = None
    ft._update_food_costs()
    assert {lbl.styleSheet() for lbl in ft.lbFoodCosts} == {neutral_style}
    assert all(lbl.text() == '--' for lbl in ft.lbFoodCosts)

    ft.close()
    ds.close()
