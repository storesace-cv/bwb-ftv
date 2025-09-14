-- Rename tables and columns to CamelCase

ALTER TABLE schema_version RENAME TO SchemaVersion;
ALTER TABLE SchemaVersion RENAME COLUMN filename TO Filename;

ALTER TABLE produtos RENAME TO Produtos;
ALTER TABLE Produtos RENAME COLUMN codigo TO Codigo;

ALTER TABLE fichas_tecnicas RENAME TO FichasTecnicas;
ALTER TABLE FichasTecnicas RENAME COLUMN produto_codigo TO ProdutoCodigo;

ALTER TABLE precos_taxas RENAME TO PrecosTaxas;
ALTER TABLE PrecosTaxas RENAME COLUMN codigo TO Codigo;
ALTER TABLE PrecosTaxas RENAME COLUMN loja TO Loja;
ALTER TABLE PrecosTaxas RENAME COLUMN ativo TO Ativo;
ALTER TABLE PrecosTaxas RENAME COLUMN preco_1_5 TO Preco1_5;
ALTER TABLE PrecosTaxas RENAME COLUMN iva_1_2 TO Iva1_2;
ALTER TABLE PrecosTaxas RENAME COLUMN isencao_iva TO IsencaoIva;
ALTER TABLE PrecosTaxas RENAME COLUMN nome_prod_venda_nao_necessario_p__importar TO NomeProdVenda;
ALTER TABLE PrecosTaxas RENAME COLUMN familia_nao_necessario_p__importar TO Familia;
ALTER TABLE PrecosTaxas RENAME COLUMN sub_familia_nao_necessario_p__importar TO SubFamilia;

ALTER TABLE produto_preparacao RENAME TO ProdutoPreparacao;
ALTER TABLE ProdutoPreparacao RENAME COLUMN produto_codigo TO ProdutoCodigo;
ALTER TABLE ProdutoPreparacao RENAME COLUMN html TO Html;

ALTER TABLE alergenios RENAME TO Alergenios;
ALTER TABLE Alergenios RENAME COLUMN id TO Id;
ALTER TABLE Alergenios RENAME COLUMN nome TO Nome;
ALTER TABLE Alergenios RENAME COLUMN ativo TO Ativo;

ALTER TABLE tipos_artigos RENAME TO TiposArtigos;
ALTER TABLE TiposArtigos RENAME COLUMN cod TO Cod;
ALTER TABLE TiposArtigos RENAME COLUMN descricao TO Descricao;
ALTER TABLE TiposArtigos RENAME COLUMN ativo TO Ativo;

ALTER TABLE validade RENAME TO Validade;
ALTER TABLE Validade RENAME COLUMN cod TO Cod;
ALTER TABLE Validade RENAME COLUMN descricao TO Descricao;
ALTER TABLE Validade RENAME COLUMN ativo TO Ativo;

ALTER TABLE temperaturas RENAME TO Temperaturas;
ALTER TABLE Temperaturas RENAME COLUMN cod TO Cod;
ALTER TABLE Temperaturas RENAME COLUMN descricao TO Descricao;
ALTER TABLE Temperaturas RENAME COLUMN ativo TO Ativo;

