CREATE TABLE IF NOT EXISTS Localizacao (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Country TEXT NOT NULL,
    Code TEXT NOT NULL,
    Currency TEXT NOT NULL,
    Symbol TEXT NOT NULL,
    Format TEXT NOT NULL,
    Active INTEGER NOT NULL DEFAULT 0 CHECK (Active IN (0,1))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_localizacao_active
    ON Localizacao(Active)
    WHERE Active = 1;

INSERT OR IGNORE INTO Localizacao (Country, Code, Currency, Symbol, Format, Active) VALUES
    ('Portugal', 'PT', 'Euro', '€', 'pt_PT', 1);
INSERT OR IGNORE INTO Localizacao (Country, Code, Currency, Symbol, Format, Active) VALUES
    ('Brasil', 'BR', 'Real brasileiro', 'R$', 'pt_BR', 0);
INSERT OR IGNORE INTO Localizacao (Country, Code, Currency, Symbol, Format, Active) VALUES
    ('Estados Unidos', 'US', 'Dólar americano', '$', 'en_US', 0);
INSERT OR IGNORE INTO Localizacao (Country, Code, Currency, Symbol, Format, Active) VALUES
    ('Reino Unido', 'GB', 'Libra esterlina', '£', 'en_GB', 0);
INSERT OR IGNORE INTO Localizacao (Country, Code, Currency, Symbol, Format, Active) VALUES
    ('Espanha', 'ES', 'Euro', '€', 'es_ES', 0);
