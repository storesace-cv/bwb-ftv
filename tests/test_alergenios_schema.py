"""Testa o esquema da tabela Alergenios criada pelo DataStore."""

from __future__ import annotations

from data.datastore import DataStore


def test_datastore_cria_tabela_alergenios_com_colunas_obrigatorias():
    """Garante que a tabela ``Alergenios`` é criada com o esquema esperado."""

    with DataStore(db_path=":memory:") as datastore:
        rows = datastore.conn.execute("PRAGMA table_info(Alergenios)").fetchall()

    assert rows, "A tabela Alergenios deve existir após inicializar o DataStore."

    colunas = {row[1]: row for row in rows}
    tipos = {nome: (info[2] or "").upper() for nome, info in colunas.items()}

    obrigatorias = {
        "Id": "INTEGER",
        "Nome": "TEXT",
        "NomeIngles": "TEXT",
        "Descricao": "TEXT",
        "Exemplos": "TEXT",
        "Notas": "TEXT",
    }
    for nome, tipo_esperado in obrigatorias.items():
        assert nome in tipos, f"Coluna obrigatória '{nome}' em falta na tabela Alergenios."
        assert (
            tipos[nome] == tipo_esperado
        ), f"Coluna '{nome}' deveria ser do tipo {tipo_esperado!r}, obteve {tipos[nome]!r}."

    opcionais = {"Ativo": "INTEGER"}
    for nome, tipo_esperado in opcionais.items():
        if nome in tipos:
            assert (
                tipos[nome] == tipo_esperado
            ), f"Coluna '{nome}' deveria ser do tipo {tipo_esperado!r}, obteve {tipos[nome]!r}."
