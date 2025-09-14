# PROMPTS

## System Prompts

| Prompt | Objective | Key Instructions | Expected Input Format | Output Structure | Example |
|--------|-----------|------------------|-----------------------|------------------|---------|
| **Data Import Agent** | Load products and technical sheets from Excel into the SQLite database | Validate base spreadsheets; synchronize table schemas; upsert product and ingredient data | Excel files: `imports/Produtos_Base.xlsx`, `imports/FichasTecnicas_base.xlsx`, `imports/PreçosTaxas_base.xlsx` | Updated `databases/ftv.db` and archived files in `imports/history` | *System:* “You are the Data Import Agent. Load the provided spreadsheets into the database.” |
| **Schema Maintenance Agent** | Align the database schema with the latest spreadsheet headers | Compare table columns with spreadsheet headers; add missing columns and recreate tables when necessary | Base Excel files in `imports/` and the current database schema | Modified schema within `databases/ftv.db` | *System:* “You keep the database schema synchronized with incoming spreadsheet formats.” |
| **Migration Agent** | Apply SQL migrations for preparation-related tables | Execute migration scripts; verify that required tables exist after migration | `data/migrations/preparacao.sql` and the target database | Database with new or updated preparation tables | *System:* “Run the preparation migration script and ensure tables exist afterward.” |
| **Backup Agent** | Create and restore backups of the database | Generate timestamped backups; restore the database from a selected backup | Current `databases/ftv.db` or files in `databases/backups/` | Backup copies or a restored database file | *System:* “Safeguard the database by creating or restoring backups as requested.” |

## User Prompts

| Objective | Instructions | Expected Input Format | Output Structure | Example |
|-----------|--------------|-----------------------|------------------|---------|
| Request an agent to perform its task | Describe the desired operation (import, schema sync, migration, backup) and supply necessary file paths or parameters | Natural-language command with required file paths or options | Confirmation message and logs describing success or errors | *User:* “Please import `imports/Produtos_Base.xlsx` and update the database.” |

## Context Prompts

| Prompt (Agent) | Objective | Content Provided as Context | Expected Input Format | Output Structure | Example |
|----------------|-----------|---------------------------|-----------------------|------------------|---------|
| **Data Import Agent** | Supply tools and coordination details | Accessible tools: `services/products.py`, `data/datastore.py`, `openpyxl`; interacts with Schema Maintenance Agent and may trigger Backup Agent | Paths to tools and other agents’ names | Updated database and archived files | *Context:* “Accessible tools: services/products.py, data/datastore.py. Interacts with Schema Maintenance Agent.” |
| *(Similar context prompts are defined for other agents with their respective tools and interactions.)* |

*No tests were run—this was a repository inspection only.*
