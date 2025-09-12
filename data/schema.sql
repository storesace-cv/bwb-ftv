-- Minimal schema for FTV
CREATE TABLE IF NOT EXISTS produtos (
    codigo TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS fichas_tecnicas (
    produto_codigo TEXT
);
