# Agent Resource Reference

This document summarizes the APIs, databases, libraries, and external services available to the project's automation agents.

## Databases
- **SQLite `ftv.db`** – Primary data store located at `databases/ftv.db`. Set `FTV_DB_PATH` to override the location.
- A missing database triggers interactive creation of an empty file.

### Usage
```python
from data.datastore import DataStore
with DataStore() as ds:
    items = ds.list_active_allergens()
    print(items)
```

## Backup Utilities
- `data.backup.create_backup()` – creates timestamped copies under `databases/backups/`.
- `data.backup.restore_backup(path)` – restores a selected backup.

```python
from data.backup import create_backup, restore_backup
backup_path = create_backup()
restore_backup(backup_path)
```

## Schema Tools
- `python tools/cleanup_schema.py` – syncs `Produtos`, `FichasTecnicas`, and `PrecosTaxas` schemas with current Excel headers, creating a `.bak` backup beforehand.
- `python tools/run_migration_preparacao.py` – applies SQL migrations for preparation tables and exits with codes 0–4 depending on success.

## Data Import Helpers
- `services.products.canonicalize_header(text, table=None)` – normalizes spreadsheet headers.
- `services.products.sync_table_schema(conn, table, headers)` – adds or recreates columns to match given headers.

## Libraries
- **PyQt5** – GUI and user prompts.
- **openpyxl** – Excel parsing.
- **sqlite3** – local database access.

## External Services
- **NET-bo** – external source for products, prices, and taxes provided via Excel exports. Credentials are required but not stored in the repository.

## Known Limitations
- Import files must be `.xlsx` and use exact Portuguese names with accents.
- Backup and migration scripts expect the database at `<root>/databases/ftv.db` unless `FTV_DB_PATH` is set.
- There is no direct integration with ZoneSoft; the process relies on manually exported Excel files from NET-bo.
