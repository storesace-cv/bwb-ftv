# Project Agents

## Data Import Agent
- **Role**: Load products and technical sheets from Excel into the SQLite database.
- **Responsibilities**:
  - Validate base spreadsheets.
  - Synchronize table schemas.
  - Upsert product and ingredient data.
- **Inputs**: `imports/Produtos_Base.xlsx`, `imports/FichasTecnicas_base.xlsx`, `imports/PreçosTaxas_base.xlsx`.
- **Outputs**: Updated `databases/ftv.db` and archived files in `imports/history`.
- **Accessible tools**: `services/products.py`, `data/datastore.py`, `openpyxl`.
- **Interactions**: Coordinates with the Schema Maintenance Agent and may trigger the Backup Agent before large updates.

## Schema Maintenance Agent
- **Role**: Align the database schema with the latest spreadsheet headers.
- **Responsibilities**:
  - Compare table columns with spreadsheet headers.
  - Add missing columns and recreate tables when necessary.
- **Inputs**: Base Excel files in `imports/` and the current database schema.
- **Outputs**: Modified schema within `databases/ftv.db`.
- **Accessible tools**: `tools/cleanup_schema.py`, `services/products.canonicalize_header`, `services/products.sync_table_schema`, `openpyxl`.
- **Interactions**: Works with the Data Import Agent and consults the Backup Agent to safeguard data.

## Migration Agent
- **Role**: Apply SQL migrations for preparation-related tables.
- **Responsibilities**:
  - Execute migration scripts.
  - Verify that required tables exist after migration.
- **Inputs**: `data/migrations/preparacao.sql` and the target database.
- **Outputs**: Database with new or updated preparation tables.
- **Accessible tools**: `tools/run_migration_preparacao.py`, `sqlite3`.
- **Interactions**: May prompt the Schema Maintenance Agent to revalidate the schema after migrations.

## Backup Agent
- **Role**: Create and restore backups of the database.
- **Responsibilities**:
  - Generate timestamped backups.
  - Restore the database from a selected backup.
- **Inputs**: Current `databases/ftv.db` or files in `databases/backups/`.
- **Outputs**: Backup copies or a restored database file.
- **Accessible tools**: `data/backup.py`, `shutil`, `pathlib`.
- **Interactions**: Invoked by other agents before potentially destructive operations.

## Guia de nomenclaturas
- Consulte `nomenclaturas.md` na raiz do repositório como fonte de verdade para termos de domínio, variáveis de ambiente e
  nomes de ficheiros.
- Ao introduzir novos conceitos ou alterar significados existentes, atualize `nomenclaturas.md` no mesmo PR para manter o
  vocabulário alinhado entre equipas.

## Nomenclatura de widgets
- `QLabel` = "legenda"/"legendas".
- `QLineEdit` = "campo"/"campos".


## ReportBro Image Verification Agent
- **Role**: Verify that the application integrates product images correctly in ReportBro templates.
- **Responsibilities**:
  - Ensure that when using template `app/templates_store/templates/ft_gestao_02.json`, the application sets the parameter `product_image_filename` correctly.
  - Validate that the path is always `/databases/images/{Produtos_Codigo}.png` (fixed directory, `.png` extension, filename = product code).
  - Confirm that the code fills this parameter before calling ReportBro, with a safe fallback (`""`) if missing, and logs warnings instead of crashing.
  - Ensure that `source` is not used for this case and that missing files do not cause crashes.
- **Inputs**: Templates in `app/templates_store/templates/ft_gestao_02.json`.
- **Outputs**: Verified compliance in code and warnings if misconfigured.
- **Interactions**: Works alongside the ReportBro Context Agent to enforce schema conformity.

## ReportBro information update
The ReportBro documentation can be found in `reportbro_documentation.md`.
This file replaces the previous `reportbro_schema_from_template.md` and
includes additional information about debugging.
