-- Minimal schema for FTV
CREATE TABLE IF NOT EXISTS Produtos (
    Codigo TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS FichasTecnicas (
    ProdutoCodigo TEXT
);

CREATE TABLE IF NOT EXISTS PrecosTaxas (
    Codigo TEXT PRIMARY KEY,
    Loja TEXT,
    Ativo TEXT,
    Preco1 TEXT,
    Preco2 TEXT,
    Preco3 TEXT,
    Preco4 TEXT,
    Preco5 TEXT,
    Iva1 TEXT,
    Iva2 TEXT,
    IsencaoIva TEXT,
    NomeProdVenda TEXT,
    Familia TEXT,
    SubFamilia TEXT
);
