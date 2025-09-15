import pytest
from data.datastore import DataStore


def _get_level(repo, nivel):
    levels = repo.list_levels()
    return next(r for r in levels if r["Nivel"] == nivel)


def test_list_levels_returns_ordered_ranges():
    with DataStore(db_path=":memory:") as store:
        repo = store.fcost
        levels = repo.list_levels()
        result = [
            (r["Nivel"], r["ValorMin"], r["ValorMax"]) for r in levels
        ]
        assert result == [
            (1, 25.0, 30.0),
            (2, 30.0, 35.0),
            (3, 35.0, 100.0),
        ]


def test_update_range_valid_updates_bounds():
    with DataStore(db_path=":memory:") as store:
        repo = store.fcost
        assert repo.update_range(2, 31, 33) is True
        lvl2 = _get_level(repo, 2)
        assert lvl2["ValorMin"] == 31.0
        assert lvl2["ValorMax"] == 33.0


@pytest.mark.parametrize(
    "vmin, vmax",
    [
        (40, 30),  # ValorMin >= ValorMax
        (29, 31),  # overlaps previous level
        (31, 36),  # overlaps next level
    ],
)
def test_update_range_invalid_does_not_change_values(vmin, vmax):
    with DataStore(db_path=":memory:") as store:
        repo = store.fcost
        before = _get_level(repo, 2)
        assert repo.update_range(2, vmin, vmax) is False
        after = _get_level(repo, 2)
        assert (after["ValorMin"], after["ValorMax"]) == (
            before["ValorMin"],
            before["ValorMax"],
        )
