# Mapeamento de campos Excel ↔ Base de dados

Lista de correspondências entre cabeçalhos dos ficheiros Excel de importação e os campos das tabelas SQLite.

## `Produtos_Base.xlsx`

| Cabeçalho Excel | Tabela.Campo |
|---|---|
| Codigo | Produtos.Codigo |
| Produto | Produtos.Produto |
| Familia | Produtos.Familia |
| SubFamilia | Produtos.SubFamilia |
| AfetaStk | Produtos.AfetaStk |
| Menu | Produtos.Menu |
| CodBarras | Produtos.CodBarras |
| TipoMercad | Produtos.TipoMercad |
| TipoVenda | Produtos.TipoVenda |
| TipoProducao | Produtos.TipoProducao |
| TipoGener | Produtos.TipoGener |
| UnStockVMPG | Produtos.UnStockVMPG |
| UnVendaVMV | Produtos.UnVendaVMV |
| UnInvVMMMPG | Produtos.UnInvVMMMPG |
| UnProduFtPV | Produtos.UnProduFtPV |
| CodAuxiliar | Produtos.CodAuxiliar |
| CodAuxiliar2 | Produtos.CodAuxiliar2 |
| PCU | Produtos.PCU |
| PCM | Produtos.PCM |
| Descontinuado | Produtos.Descontinuado |
| DispLojas | Produtos.DispLojas |

## `FichasTecnicas_base.xlsx`

| Cabeçalho Excel | Tabela.Campo |
|---|---|
| FamiliaSubfamilia | FichasTecnicas.FamiliaSubfamilia |
| ProdutoCodigo | FichasTecnicas.ProdutoCodigo |
| ProdutoNome | FichasTecnicas.ProdutoNome |
| ComponenteCodigo | FichasTecnicas.ComponenteCodigo |
| ComponenteNome | FichasTecnicas.ComponenteNome |
| Qtd | FichasTecnicas.Qtd |
| Unidade | FichasTecnicas.Unidade |
| Ppu | FichasTecnicas.Ppu |
| Preco | FichasTecnicas.Preco |
| Peso | FichasTecnicas.Peso |
| Ordem | FichasTecnicas.Ordem |

## `PreçosTaxas_base.xlsx`

| Cabeçalho Excel | Tabela.Campo |
|---|---|
| Codigo | PrecosTaxas.Codigo |
| Loja | PrecosTaxas.Loja |
| Preco1 | PrecosTaxas.Preco1 |
| Preco2 | PrecosTaxas.Preco2 |
| Preco3 | PrecosTaxas.Preco3 |
| Preco4 | PrecosTaxas.Preco4 |
| Preco5 | PrecosTaxas.Preco5 |
| Iva1 | PrecosTaxas.Iva1 |
| Iva2 | PrecosTaxas.Iva2 |
| IsencaoIva | PrecosTaxas.IsencaoIva |
| NomeProdVenda | PrecosTaxas.NomeProdVenda |
| Familia | PrecosTaxas.Familia |
| SubFamilia | PrecosTaxas.SubFamilia |
| Ativo | PrecosTaxas.Ativo |

> **Nota**: Apenas `PrecosTaxas.Iva1` é usado nos cálculos de IVA. As colunas `Iva2` e `IsencaoIva` são importadas apenas para referência.

