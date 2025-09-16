ALTER TABLE Alergenios ADD COLUMN NomeIngles TEXT NOT NULL DEFAULT '';
ALTER TABLE Alergenios ADD COLUMN Descricao TEXT;
ALTER TABLE Alergenios ADD COLUMN Exemplos TEXT;
ALTER TABLE Alergenios ADD COLUMN Notas TEXT;
UPDATE Alergenios SET NomeIngles = Nome WHERE NomeIngles = '';
