-- Split legacy Preco1_5 into individual price columns
ALTER TABLE PrecosTaxas RENAME COLUMN Preco1_5 TO Preco1;
ALTER TABLE PrecosTaxas ADD COLUMN Preco2 DECIMAL(10,2);
ALTER TABLE PrecosTaxas ADD COLUMN Preco3 DECIMAL(10,2);
ALTER TABLE PrecosTaxas ADD COLUMN Preco4 DECIMAL(10,2);
ALTER TABLE PrecosTaxas ADD COLUMN Preco5 DECIMAL(10,2);

