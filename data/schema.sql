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
    PCU DECIMAL(10,2),
    PCM DECIMAL(10,2),
    Descontinuado TEXT,
    DispLojas TEXT,
    TipoArtigo INTEGER,
    Validade INTEGER,
    Temperatura INTEGER
);

CREATE TABLE IF NOT EXISTS FichasTecnicas (
    FamiliaSubfamilia TEXT,
    ProdutoCodigo TEXT,
    ProdutoNome TEXT,
    ComponenteCodigo TEXT,
    ComponenteNome TEXT,
    Qtd DECIMAL(10,2),
    Unidade TEXT,
    Ppu DECIMAL(10,2),
    Preco DECIMAL(10,2),
    Peso DECIMAL(10,2),
    Ordem INTEGER
);

CREATE TABLE IF NOT EXISTS PrecosTaxas (
    Codigo TEXT NOT NULL,
    Loja TEXT NOT NULL,
    Ativo TEXT,
    Preco1 DECIMAL(10,2),
    Preco2 DECIMAL(10,2),
    Preco3 DECIMAL(10,2),
    Preco4 DECIMAL(10,2),
    Preco5 DECIMAL(10,2),
    Iva1_2 DECIMAL(10,2),
    IsencaoIva TEXT,
    NomeProdVenda TEXT,
    Familia TEXT,
    SubFamilia TEXT,
    PRIMARY KEY (Codigo, Loja)
);
CREATE TABLE IF NOT EXISTS Uploads (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Filename TEXT NOT NULL,
    Content BLOB NOT NULL,
    UploadedAt TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Config (
    Key TEXT PRIMARY KEY,
    Value TEXT
);
