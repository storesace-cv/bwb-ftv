# Nomenclaturas do projeto

Este documento consolida os termos mais recorrentes encontrados no código-fonte (`*.py`), na documentação (`*.md`) e nos ficheiros de configuração do projeto. O objetivo é alinhar a linguagem das equipas de produto, dados e UI sempre que forem introduzidas novas funcionalidades ou ajustadas integrações.

## Processo de manutenção
- **Responsável principal:** Equipa de Engenharia FTV (ponto focal: responsáveis pelos agentes automatizados descritos em `AGENTS.md`).
- **Como atualizar:** sempre que surgir um novo termo relevante ou quando o significado de um termo existente for alterado, atualizar esta lista no mesmo Pull Request da mudança funcional.
- **Revisão:** confirmar se há exemplos de uso e se o agente/processo responsável reflete quem detém o contexto do termo.

## Dados e tabelas principais
| Termo | Definição | Exemplo de uso | Responsável / Atualização |
|-------|-----------|----------------|---------------------------|
| **Produto** | Registo base que representa um artigo comercial, com código, família, unidades e indicadores de disponibilidade. | Tabela `Produtos` documentada em `SCHEMA.md`. | Data Import Agent valida e importa `Produtos_Base.xlsx`.
| **Ficha Técnica** | Conjunto de componentes de um produto, guardado em `FichasTecnicas` com quantidades, preços e ordem. | `FichasTecnicas.ProdutoCodigo`, `FichasTecnicas.Qtd` e `FichasTecnicas.Ordem`. | Data Import Agent e ProductService.
| **Ficha Técnica de Gestão**<br/>*("FT Gestão", "FT's Gestão", "Ficha de Gestão")* | Variante orientada a custos que, ao ser impressa, exclui os blocos **B4** e **B5** da ficha técnica padrão. | Opções de exportação/ impressão na UI e em prompts de agentes. | Equipa de Produto e UI; alinhar com Data Import Agent quando surgirem novos blocos.
| **Ficha Técnica Operacional**<br/>*("FT Operacional", "FT's Operacional", "Ficha Operacional", "FTs Operacionais")* | Variante focada no processo produtivo que, ao imprimir, exclui o bloco **B3** e a tag **B1.C1.A.3** (“Preços de Venda”). | Documentação de impressão e instruções operacionais de produção. | Equipa de Operações e UI; rever com Data Import Agent ao ajustar blocos.
| **Componente** | Item listado numa ficha técnica, associado a um produto e a uma quantidade/unidade. | Colunas `ComponenteCodigo` e `ComponenteNome` em `FichasTecnicas`. | Data Import Agent.
| **Ingrediente** | Representação em memória (dataclass) de um componente carregado para edição na UI. | Fluxo "Technical sheet creation" em `WORKFLOWS.md`. | ProductService e equipa de UI.
| **PPU (Preço por Unidade)** | Valor unitário de cada ingrediente usado para calcular o custo total. | Campo `Ppu` na tabela `FichasTecnicas`. | ProductService (`calculate_cost`) e Data Import Agent.
| **Preço PVP** | Preços de venda ao público (`PVP1` a `PVP5`) carregados para cada loja. | Colunas `Preco1`–`Preco5` em `PrecosTaxas`. | Data Import Agent e equipa comercial.
| **IVA** | Taxas de imposto aplicáveis aos produtos (`Iva1` principal e `Iva2` auxiliar). | Campos `Iva1` e `Iva2` em `PrecosTaxas`. | Data Import Agent; confirmar regras fiscais com equipa financeira.
| **Alergénios** | Catálogo com identificador, nomes em PT/EN, descrição e notas usado nas fichas técnicas. | Tabela `Alergenios` e importação via JSON descrita no `README.md`. | Data Import Agent e mantenedor de integrações NET-bo.
| **TiposArtigos** | Lista de categorias de artigo que alimenta o campo `TipoArtigo` em `Produtos`. | Tabela auxiliar `TiposArtigos`. | Schema Maintenance Agent ao sincronizar cabeçalhos.
| **Validade** | Referencial de durações padrão (ex.: “24h”, “48h”) associado a `Produtos`. | Tabela `Validade`. | Schema Maintenance Agent.
| **Temperaturas** | Tabela com faixas de temperatura (ex.: “Quente”, “Frio”) para requisitos de conservação. | Tabela `Temperaturas`. | Schema Maintenance Agent.
| **Localização** *("Parâmetros de Moeda")* | Catálogo com país, código ISO, moeda, símbolo e locale; exatamente um registo pode estar ativo para formatar valores monetários. | Tabela `Localizacao` documentada em `SCHEMA.md`. | Schema Maintenance Agent e equipa de Produto/Financeira. |
| **ProdutoPreparacao** | Armazena instruções HTML de preparação ligadas a um produto. | Tabela `ProdutoPreparacao` e migrações correspondentes. | Migration Agent garante existência da tabela; UI atualiza conteúdo.
| **Uploads** | Registo histórico dos ficheiros importados, incluindo nome e data. | Tabela `Uploads` alimentada após importações. | Data Import Agent.

## Aplicação, serviços e agentes
| Termo | Definição | Exemplo de uso | Responsável / Atualização |
|-------|-----------|----------------|---------------------------|
| **DataStore** | Camada de acesso à base de dados SQLite; aplica migrações e expõe métodos como `get_ingredientes`. | Fluxos de login e criação de fichas técnicas em `WORKFLOWS.md`. | Equipa de Engenharia; Migration Agent monitoriza migrações.
| **ProductService** | Serviço que orquestra importações, cálculos de custo e acesso a dados para a UI. | Métodos `import_from_excel` e `calculate_cost` descritos em `WORKFLOWS.md`. | Equipa de Backend/UI; alinhar com Data Import Agent.
| **FTApp** | Janela principal PyQt5 para gerir fichas técnicas e listas auxiliares. | Sequência "Login / application launch" em `WORKFLOWS.md`. | Equipa de UI.
| **Editor de Documentos** | Acesso ao editor ReportBro para criar e ajustar modelos de impressão. | Menu "Menu → Utilitários → Gestão de Documentos → Editor de Documentos" na aplicação; abre o designer integrado num navegador local por omissão, podendo respeitar `FTV_REPORTBRO_EDITOR_URL` ou o modo kiosk activado via `FTV_REPORTBRO_EDITOR_KIOSK`. | Equipa de UI e responsáveis pelas integrações de impressão.
| **SplashScreen** | Janela de entrada que comunica migrações pendentes antes da abertura do `FTApp`. | Passos 3–4 do primeiro fluxo em `WORKFLOWS.md`. | Equipa de UI e Migration Agent.
| **Data Import Agent** | Agente responsável por validar e carregar ficheiros Excel para a BD. | Mandato descrito em `AGENTS.md`. | Owner do agente; atualizar doc ao alterar responsabilidades.
| **Schema Maintenance Agent** | Agente que alinha o esquema da BD com os cabeçalhos atuais. | Definição em `AGENTS.md`. | Owner do agente.
| **Migration Agent** | Agente encarregado de executar migrações SQL de preparação. | Definição em `AGENTS.md`. | Owner do agente.
| **Backup Agent** | Agente que cria e restaura backups antes de operações sensíveis. | Descrição em `AGENTS.md`. | Owner do agente.

## Configurações, integrações e ficheiros
| Termo | Definição | Exemplo de uso | Responsável / Atualização |
|-------|-----------|----------------|---------------------------|
| **NET-bo** | Ecossistema externo que fornece exportações Excel de produtos, preços e taxas. | `README.md` descreve importação de dados a partir do NET-bo. | Equipa de Integração / Produto.
| **FTV_DB_PATH** | Variável de ambiente que permite alterar o caminho da base de dados SQLite. | Seção de configuração no `README.md`. | Equipa de Operações; documentar em deploys.
| **FTV_SEED_ALERGENIOS** | Variável de ambiente para popular a tabela `Alergenios` com dados padrão. | Instruções de seeding no `README.md`. | Equipa de Operações / Data Import Agent.
| **FTV_REPORTBRO_EDITOR_KIOSK** | Variável de ambiente opcional que reativa o modo kiosk QtWebEngine para o editor ReportBro integrado. | Definir para `1`, `true`, `yes` ou `on` quando o QtWebEngine estiver disponível e o modo kiosk for desejado. | Equipa de UI e responsáveis pelas integrações de impressão.
| **imports/history** | Diretório onde os ficheiros Excel importados são arquivados com carimbo temporal. | Processo descrito em `README.md` e `SCHEMA.md`. | Data Import Agent mantém histórico.
| **FichasTecnicas_base.xlsx** | Ficheiro Excel obrigatório com componentes das fichas técnicas. | Listado na secção de importação do `README.md`. | Data Import Agent.
| **PreçosTaxas_base.xlsx** | Ficheiro Excel com preços PVP e taxas de IVA por loja. | Listado na secção de importação do `README.md`. | Data Import Agent e equipa financeira.
| **Produtos_Base.xlsx** | Ficheiro Excel que contém o catálogo de produtos. | Listado na secção de importação do `README.md`. | Data Import Agent.
| **databases/backups/** | Diretório padrão para cópias de segurança geradas automaticamente. | Referenciado em `docs/agent_resources.md`. | Backup Agent / Equipa de Operações.
| **databases/allergens.json** | Ficheiro JSON opcional para importar alergénios antes do seeding automático. | Referenciado no `README.md`. | Data Import Agent.
| **tools/cleanup_schema.py** | Script que sincroniza `Produtos`, `FichasTecnicas` e `PrecosTaxas` com os cabeçalhos atuais. | Documentado em `README.md` e `docs/agent_resources.md`. | Schema Maintenance Agent.
| **tools/run_migration_preparacao.py** | Script CLI que aplica migrações do bloco `[B4]` PREPARAÇÃO e valida a tabela `ProdutoPreparacao`. | Referenciado em `docs/agent_resources.md`. | Migration Agent.

> **Nota:** sempre que um termo deixar de ser utilizado ou sofrer alteração de significado, remova ou ajuste a respetiva linha e notifique os responsáveis indicados.
