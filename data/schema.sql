-- Minimal schema for FTV
CREATE TABLE IF NOT EXISTS produtos (
    codigo TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS fichas_tecnicas (
    produto_codigo TEXT
);

CREATE TABLE IF NOT EXISTS precos_taxas (
    codigo TEXT PRIMARY KEY,
    loja TEXT,
    ativo TEXT,
    preco_1 TEXT,
    preco_2 TEXT,
    preco_3 TEXT,
    preco_4 TEXT,
    preco_5 TEXT,
    iva_1 TEXT,
    iva_2 TEXT,
    isencao_iva TEXT,
    nome_prod_venda_nao_necessario_p__importar TEXT,
    familia_nao_necessario_p__importar TEXT,
    sub_familia_nao_necessario_p__importar TEXT
);
