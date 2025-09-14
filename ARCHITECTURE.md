# Fichas Técnicas BWB

## 1. Camada Frontend
- **Framework:** PyQt5  
- **Launcher:** `bwb-fichas_tecnicas.py`  
- **Fluxo:** aplica tema global, mostra `StartupDialog` e abre a janela principal `FTApp` (`ui/ui_editor_fonte.py`)  
- **Funcionalidades:**  
  - Importação, backups e atualização → `ui/dialogs.py`  
  - Gestão de layout → `ui/layout.py`  

## 2. Camada Backend
- **Serviço principal:** `ProductService` (`services/products.py`)  
  - Normaliza cabeçalhos (`canonicalize_header`)  
  - Sincroniza esquemas (`sync_table_schema`)  
  - Importa/atualiza produtos e fichas técnicas a partir de Excel  
  - Calcula custos e expõe APIs usadas pela UI  
- **Persistência:** `DataStore` (`data/datastore.py`)  
  - Liga ao SQLite  
  - Aplica migrações (`data/migration.py`)  
  - Expõe repositórios  

## 3. Base de Dados
- **Ficheiro local:** `databases/ftv.db`  
- **Tabelas principais:**  
  - `Produtos`  
  - `FichasTecnicas`  
  - `PrecosTaxas`  
  - `Alergenios`  
  - `TiposArtigos`  
  - `Validade`  
  - `Temperaturas`  
  - `Uploads`  
  - `Config`  
  - `ProdutoPreparacao` (via migrações)  
- **Migrações:** `data/migrations/*.sql`  
- **Seed de dados auxiliares:** `Validade`, `Temperaturas`  

## 4. AI / Automação
- **Agente de Importação**  
  - Lê `Produtos_Base.xlsx`, `FichasTecnicas_base.xlsx`, `PreçosTaxas_base.xlsx`  
  - Carrega dados via `services/products.import_from_excel`  
- **Agente de Manutenção de Esquema**  
  - Garante correspondência entre cabeçalhos Excel e colunas SQLite  
  - (`services.products.sync_table_schema`, `tools/cleanup_schema.py`)  
- **Agente de Migração**  
  - Aplica scripts pendentes e cria tabelas auxiliares  
  - (`data/migration.setup_database`, `data/migrations/`)  
- **Agente de Backup**  
  - Cria/restaura cópias de `ftv.db`  
  - (`data/backup.create_backup`, `data/backup.restore_backup`)  

## 5. Dependências & Integrações Externas
- **Dependências:**  
  - PyQt5  
  - openpyxl  
  - sqlite3  
  - pytest  
  - flake8  
  - black  
- **Integração externa:**  
  - **NET-bo** fornece produtos, preços e taxas via exportações Excel  
  - Não existe ligação direta ao ZoneSoft, dependência de exportações manuais  

## 6. Interações entre Componentes
graph LR
    subgraph UI
        A[FTApp & diálogos PyQt5]
    end
    subgraph Backend
        B[ProductService]
        C[DataStore]
    end
    subgraph DB
        D[(SQLite ftv.db)]
    end
    subgraph Agents
        AI1[Importação]
        AI2[Manutenção]
        AI3[Migração]
        AI4[Backup]
    end

    %% Nó externo (fonte Excel)
    E[NET-bo (Excel)]

    A --> B
    B --> C
    C --> D
    AI1 --> B
    AI2 --> B
    AI3 --> C
    AI4 --> C
    B --> E
    E --> B
