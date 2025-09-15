-- Create FcostValues table with initial cost level ranges
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
