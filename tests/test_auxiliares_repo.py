import sqlite3

from ftv.data.repositories import AuxiliaresRepo


def _make_repo():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE tipos_artigos (
            cod INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            ativo INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE validade (
            cod INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            ativo INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE temperaturas (
            cod INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            ativo INTEGER
        )
        """
    )
    conn.commit()
    return conn, AuxiliaresRepo(conn)


def _make_repo_no_tables():
    conn = sqlite3.connect(":memory:")
    return conn, AuxiliaresRepo(conn)


def test_tipos_artigos_crud_success():
    conn, repo = _make_repo()
    tid = repo.add_tipo_artigo("TipoA")
    assert tid == 1
    assert repo.list_tipos_artigos_admin() == [(1, "TipoA", 1)]
    assert repo.update_tipo_artigo(1, "TipoB") is True
    assert repo.list_tipos_artigos_admin()[0][1] == "TipoB"
    assert repo.set_tipo_artigo_ativo(1, 0) is True
    assert repo.list_tipos_artigos_admin()[0][2] == 0


def test_tipos_artigos_crud_failure():
    conn, repo = _make_repo()
    assert repo.update_tipo_artigo(999, "Foo") is False
    assert repo.set_tipo_artigo_ativo(999, 0) is False
    conn2, repo2 = _make_repo_no_tables()
    assert repo2.add_tipo_artigo("X") is None
    assert repo2.list_tipos_artigos_admin() == []
    conn.close()
    conn2.close()


def test_validade_crud_success():
    conn, repo = _make_repo()
    vid = repo.add_validade("24h")
    assert vid == 1
    assert repo.list_validade_admin() == [(1, "24h", 1)]
    assert repo.update_validade(1, "48h") is True
    assert repo.list_validade_admin()[0][1] == "48h"
    assert repo.set_validade_ativo(1, 0) is True
    assert repo.list_validade_admin()[0][2] == 0
    conn.close()


def test_validade_crud_failure():
    conn, repo = _make_repo()
    assert repo.update_validade(999, "no") is False
    assert repo.set_validade_ativo(999, 0) is False
    conn2, repo2 = _make_repo_no_tables()
    assert repo2.add_validade("x") is None
    assert repo2.list_validade_admin() == []
    conn.close()
    conn2.close()


def test_temperaturas_crud_success():
    conn, repo = _make_repo()
    tid = repo.add_temperatura("Quente")
    assert tid == 1
    assert repo.list_temperaturas_admin() == [(1, "Quente", 1)]
    assert repo.update_temperatura(1, "Frio") is True
    assert repo.list_temperaturas_admin()[0][1] == "Frio"
    assert repo.set_temperatura_ativo(1, 0) is True
    assert repo.list_temperaturas_admin()[0][2] == 0
    conn.close()


def test_temperaturas_crud_failure():
    conn, repo = _make_repo()
    assert repo.update_temperatura(999, "nada") is False
    assert repo.set_temperatura_ativo(999, 0) is False
    conn2, repo2 = _make_repo_no_tables()
    assert repo2.add_temperatura("x") is None
    assert repo2.list_temperaturas_admin() == []
    conn.close()
    conn2.close()
