from utils import paths


def test_get_project_root_without_markers(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy.py"
    dummy.touch()
    monkeypatch.setattr(paths, "__file__", str(dummy))

    assert paths.get_project_root() == tmp_path
