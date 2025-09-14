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
