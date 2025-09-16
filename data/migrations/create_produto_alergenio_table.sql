-- Create association table between products and allergens
CREATE TABLE IF NOT EXISTS ProdutoAlergenio (
    ProdutoCodigo TEXT NOT NULL,
    AlergenioId   INTEGER NOT NULL,
    PRIMARY KEY (ProdutoCodigo, AlergenioId),
    FOREIGN KEY (ProdutoCodigo) REFERENCES Produtos (Codigo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (AlergenioId) REFERENCES Alergenios (Id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
