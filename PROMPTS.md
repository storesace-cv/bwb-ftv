# PROMPTS

<!-- Atualizado em 2025-09-26: adicionada referência explícita ao modelo app/templates_store/templates/ft_gestao_02.json -->

## System Prompts

| Prompt | Objective | Key Instructions | Expected Input Format | Output Structure | Example |
|--------|-----------|------------------|-----------------------|------------------|---------|
| **Data Import Agent** | Load products and technical sheets from Excel into the SQLite database | Validate base spreadsheets; synchronize table schemas; upsert product and ingredient data | Excel files: `imports/Produtos_Base.xlsx`, `imports/FichasTecnicas_base.xlsx`, `imports/PreçosTaxas_base.xlsx` | Updated `databases/ftv.db` and archived files in `imports/history` | *System:* “You are the Data Import Agent. Load the provided spreadsheets into the database.” |
| **Schema Maintenance Agent** | Align the database schema with the latest spreadsheet headers | Compare table columns with spreadsheet headers; add missing columns and recreate tables when necessary | Base Excel files in `imports/` and the current database schema | Modified schema within `databases/ftv.db` | *System:* “You keep the database schema synchronized with incoming spreadsheet formats.” |
| **Migration Agent** | Apply SQL migrations for preparation-related tables | Execute migration scripts; verify that required tables exist after migration | `data/migrations/preparacao.sql` and the target database | Database with new or updated preparation tables | *System:* “Run the preparation migration script and ensure tables exist afterward.” |
| **Backup Agent** | Create and restore backups of the database | Generate timestamped backups; restore the database from a selected backup | Current `databases/ftv.db` or files in `databases/backups/` | Backup copies or a restored database file | *System:* “Safeguard the database by creating or restoring backups as requested.” |
| **ReportBro Context Agent** | Orient Codex when working with ReportBro JSON templates | Always consult `/docs/reportbro_schema_from_template.md` which contains the inferred schema. In addition, there is a concrete model file at `app/templates_store/templates/ft_gestao_02.json` that must be supported. Validate keys and values against this schema; maintain consistency with documented structure; do not persist extra fields inside JSON saved by the ReportBro Designer (use sidecar/auxiliary storage if needed). | ReportBro JSON files in `reporting/templates/` or related documentation | Validated ReportBro JSON files consistent with schema | *System:* “When handling ReportBro documents, consult `/docs/reportbro_schema_from_template.md` and enforce schema conformity.” |
| **ReportBro Image Verification Agent** | Verify app code complies with product image integration rules | Ensure that when using template `app/templates_store/templates/ft_gestao_02.json`, the application sets `product_image_filename` according to rules: path `/databases/images`, extension `.png`, filename = `Produtos_Codigo`. Check code fills this param before printing, with fallback `""` if missing, and logs warnings instead of crashing. Validate that no `source` is used for this case. | App source code (backend for ReportBro integration) | Report with compliance status, missing parts, risks, and test suggestions | *System:* “Verify code builds product_image_filename = '/databases/images/{Produtos_Codigo}.png' and handles missing values safely.” |

## User Prompts

| Objective | Instructions | Expected Input Format | Output Structure | Example |
|-----------|--------------|-----------------------|------------------|---------|
| Request an agent to perform its task | Describe the desired operation (import, schema sync, migration, backup) and supply necessary file paths or parameters | Natural-language command with required file paths or options | Confirmation message and logs describing success or errors | *User:* “Please import `imports/Produtos_Base.xlsx` and update the database.” |

## Context Prompts

| Prompt (Agent) | Objective | Content Provided as Context | Expected Input Format | Output Structure | Example |
|----------------|-----------|---------------------------|-----------------------|------------------|---------|
| **Data Import Agent** | Supply tools and coordination details | Accessible tools: `services/products.py`, `data/datastore.py`, `openpyxl`; interacts with Schema Maintenance Agent and may trigger Backup Agent | Paths to tools and other agents’ names | Updated database and archived files | *Context:* “Accessible tools: services/products.py, data/datastore.py. Interacts with Schema Maintenance Agent.” |
| **ReportBro Context Agent** | Ensure schema conformity for ReportBro | Context file: `/docs/reportbro_schema_from_template.md` must always be consulted; Codex should validate existing JSON against this schema and enforce conformity. Furthermore, the model file `app/templates_store/templates/ft_gestao_02.json` must be treated as a reference template that has to be supported by the application. | ReportBro JSON template paths | ReportBro JSON handled consistently with schema | *Context:* “Schema reference available at /docs/reportbro_schema_from_template.md. Use it whenever you modify or validate ReportBro templates.” |
