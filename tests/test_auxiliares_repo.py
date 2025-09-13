import sqlite3

from data.repositories import AuxiliaresRepo, ProdutosRepo


def _make_repo():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE TiposArtigos (
            Cod INTEGER PRIMARY KEY AUTOINCREMENT,
            Descricao TEXT,
            Ativo INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE Validade (
            Cod INTEGER PRIMARY KEY AUTOINCREMENT,
            Descricao TEXT,
            Ativo INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE Temperaturas (
            Cod INTEGER PRIMARY KEY AUTOINCREMENT,
            Descricao TEXT,
            Ativo INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE Produtos (
            Cod INTEGER PRIMARY KEY AUTOINCREMENT,
            TipoArtigo INTEGER,
            Validade INTEGER,
            Temperatura INTEGER
        )
        """
    )
    conn.commit()
    return conn, AuxiliaresRepo(conn)


def _make_repo_no_tables():
    conn = sqlite3.connect(":memory:")
    return conn, AuxiliaresRepo(conn)


def test_list_validade_returns_records():
    conn, repo = _make_repo()
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO Validade (Descricao, Ativo) VALUES (?, 1)",
        [("24h",), ("48h",)],
    )
    conn.commit()
    assert repo.list_validade()[1:] == [(1, "24h"), (2, "48h")]
    conn.close()


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


def test_delete_tipo_artigo():
    conn, repo = _make_repo()
    tid1 = repo.add_tipo_artigo("A")
    assert repo.delete_tipo_artigo(tid1) is True
    assert repo.list_tipos_artigos_admin() == []
    tid2 = repo.add_tipo_artigo("B")
    conn.execute("INSERT INTO Produtos (TipoArtigo) VALUES (?)", (tid2,))
    conn.commit()
    assert repo.delete_tipo_artigo(tid2) is False
    assert repo.list_tipos_artigos_admin() == [(tid2, "B", 1)]
    conn.close()


def test_delete_validade():
    conn, repo = _make_repo()
    vid1 = repo.add_validade("24h")
    assert repo.delete_validade(vid1) is True
    assert repo.list_validade_admin() == []
    vid2 = repo.add_validade("48h")
    conn.execute("INSERT INTO Produtos (Validade) VALUES (?)", (vid2,))
    conn.commit()
    assert repo.delete_validade(vid2) is False
    assert repo.list_validade_admin() == [(vid2, "48h", 1)]
    conn.close()


def test_delete_temperatura():
    conn, repo = _make_repo()
    tid1 = repo.add_temperatura("Quente")
    assert repo.delete_temperatura(tid1) is True
    assert repo.list_temperaturas_admin() == []
    tid2 = repo.add_temperatura("Frio")
    conn.execute("INSERT INTO Produtos (Temperatura) VALUES (?)", (tid2,))
    conn.commit()
    assert repo.delete_temperatura(tid2) is False
    assert repo.list_temperaturas_admin() == [(tid2, "Frio", 1)]
    conn.close()


def test_produtos_repo_setters_persist():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE TiposArtigos (
            Cod INTEGER PRIMARY KEY AUTOINCREMENT,
            Descricao TEXT,
            Ativo INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE Validade (
            Cod INTEGER PRIMARY KEY AUTOINCREMENT,
            Descricao TEXT,
            Ativo INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE Temperaturas (
            Cod INTEGER PRIMARY KEY AUTOINCREMENT,
            Descricao TEXT,
            Ativo INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE Produtos (
            Codigo TEXT PRIMARY KEY,
            Produto TEXT,
            TipoArtigo INTEGER,
            Validade INTEGER,
            Temperatura INTEGER
        )
        """
    )
    cur.execute("INSERT INTO Produtos (Codigo, Produto) VALUES ('P1', 'Prod')")
    conn.commit()
    aux = AuxiliaresRepo(conn)
    prod = ProdutosRepo(conn)
    tid = aux.add_tipo_artigo("A")
    vid = aux.add_validade("24h")
    tpid = aux.add_temperatura("Frio")
    assert prod.set_tipo_artigo("P1", tid) is True
    assert prod.set_validade("P1", vid) is True
    assert prod.set_temperatura("P1", tpid) is True
    row = conn.execute(
        "SELECT TipoArtigo, Validade, Temperatura FROM Produtos WHERE Codigo='P1'"
    ).fetchone()
    assert row == (tid, vid, tpid)
    conn.close()
