-- Minimal schema for FTV
CREATE TABLE IF NOT EXISTS Produtos (
    Codigo TEXT PRIMARY KEY,
    Produto TEXT,
    Familia TEXT,
    SubFamilia TEXT,
    AfetaStk TEXT,
    Menu TEXT,
    CodBarras TEXT,
    TipoMercad TEXT,
    TipoVenda TEXT,
    TipoProducao TEXT,
    TipoGener TEXT,
    UnStockVMPG TEXT,
    UnVendaVMV TEXT,
    UnInvVMMMPG TEXT,
    UnProduFtPV TEXT,
    CodAuxiliar TEXT,
    CodAuxiliar2 TEXT,
    PCU TEXT,
    PCM TEXT,
    Descontinuado TEXT,
    DispLojas TEXT
);

CREATE TABLE IF NOT EXISTS FichasTecnicas (
    FamiliaSubfamilia TEXT,
    ProdutoCodigo TEXT,
    ProdutoNome TEXT,
    ComponenteCodigo TEXT,
    ComponenteNome TEXT,
    Qtd REAL,
    Unidade TEXT,
    Ppu REAL,
    Preco REAL,
    Peso REAL
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
