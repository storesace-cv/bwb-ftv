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
    Iva1 DECIMAL(10,2),
    Iva2 DECIMAL(10,2),
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

CREATE TABLE IF NOT EXISTS Alergenios (
    Id         INTEGER PRIMARY KEY,
    Nome       TEXT NOT NULL,
    NomeIngles TEXT NOT NULL,
    Descricao  TEXT,
    Exemplos   TEXT,
    Notas      TEXT
);

CREATE TABLE IF NOT EXISTS FcostValues (
    Nivel INTEGER PRIMARY KEY,
    Nome TEXT NOT NULL,
    ValorMin REAL NOT NULL,
    ValorMax REAL NOT NULL,
    Comentario TEXT NOT NULL,
    CHECK (ValorMin < ValorMax),
    UNIQUE (Nivel)
);

INSERT INTO FcostValues (Nivel, Nome, ValorMin, ValorMax, Comentario) VALUES
    (1, 'Bom', 25, 30, 'Garante margem confortável para cobrir restantes custos (pessoal, energia, renda) e ainda gerar lucro.'),
    (2, 'Aceitável', 30, 35, 'Ainda viável, mas menos folga; comum em pratos mais caros ou com ingredientes premium.'),
    (3, 'Mau', 35, 100, 'Normalmente insustentável, a não ser que tenha função estratégica (atrair clientes, completar menu).');
