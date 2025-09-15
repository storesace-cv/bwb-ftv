# bwb-ftv
Fichas Técnicas Valorizadas  
*Technical Sheets with Value*

A aplicação permite gerir fichas técnicas de produtos e receitas na restauração.  
The application lets you manage product and recipe technical sheets for food service.

Importa dados a partir de folhas de cálculo Excel exportados do NET-bo,
sincroniza com o ecossistema NET-bo, regista alergénios por ingrediente e
armazena toda a informação numa base de dados SQLite.
It imports data from Excel spreadsheets exported from NET-bo, synchronizes with
the NET-bo ecosystem, records allergens per ingredient, and stores all
information in an SQLite database.

Esta aplicação foi criada pela [BWB - Business with Brains](https://bwb.pt).
This application was created by [BWB - Business with Brains](https://bwb.pt).

## Início Rápido / Quick Start

Sequência mínima para executar a aplicação:  
Minimal sequence to run the application:

**Unix**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp /caminho/para/Produtos_Base.xlsx imports/
cp /caminho/para/FichasTecnicas_base.xlsx imports/
cp /caminho/para/PreçosTaxas_base.xlsx imports/
python bwb-fichas_tecnicas.py
```

**Windows**

```powershell
python -m venv .venv
\.\.venv\Scripts\activate
pip install -r requirements.txt
copy C:\\caminho\\para\\Produtos_Base.xlsx imports\\
copy C:\\caminho\\para\\FichasTecnicas_base.xlsx imports\\
copy C:\\caminho\\para\\PreçosTaxas_base.xlsx imports\\
python bwb-fichas_tecnicas.py
```

Principais funcionalidades:  
Main features:

- Importação de produtos, fichas técnicas e preços via Excel.
  Import of products, technical sheets, and prices via Excel.
- Integração com NET-bo para atualização de preços e taxas através de ficheiros
  Excel exportados.
  Integration with NET-bo for price and tax updates through exported Excel
  files.
- Gestão de alergénios ao nível de ingredientes e produtos finais.
  Allergen management at the ingredient and final product levels.
- Base de dados local em SQLite com suporte a backups e migrações de esquema.
  Local SQLite database with backup and schema migration support.

## Tecnologias / Technologies

- **Python 3 / PyQt5** - Interface gráfica da aplicação.
  Graphical interface of the application.
- **openpyxl** - Leitura e validação dos ficheiros Excel.
  Reading and validation of Excel files.
- **sqlite3** - Armazenamento local dos dados.
  Local data storage.
- **NET-bo** - Fonte externa de produtos, preços e taxas via exportações
  Excel.
  External source of products, prices, and taxes via Excel exports.

## Instalação / Installation

Atualize os pacotes do sistema e instale a biblioteca OpenGL necessária para o PyQt5:  
Update system packages and install the OpenGL library required by PyQt5:

```bash
sudo apt-get update
sudo apt-get install -y libgl1 # use libgl1-mesa-glx se libgl1 não estiver disponível
```

Depois, instale as dependências Python:  
Then install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Configuração / Configuration

Por omissão, a aplicação utiliza a base de dados SQLite em
`<raiz do projeto>/databases/ftv.db`.
O diretório é criado automaticamente e o ficheiro é inicializado caso esteja em falta.
By default, the application uses the SQLite database at
`<project root>/databases/ftv.db`.
The directory is created automatically and the file is initialized if missing.

Para utilizar outro local, defina a variável de ambiente `FTV_DB_PATH` com o
caminho completo para o ficheiro desejado:
To use another location, set the `FTV_DB_PATH` environment variable with the
full path to the desired file:

```bash
export FTV_DB_PATH=/caminho/para/custom.db
```

Para ativar logs detalhados, defina a variável `debug` como `0` ao iniciar a
aplicação:
To enable detailed logs, set the `debug` variable to `0` when launching the application:

```bash
debug=0 python bwb-fichas_tecnicas.py
```

## Execução / Running

Inicie a interface principal com:  
Launch the main interface with:

```bash
python bwb-fichas_tecnicas.py
```

Coloque os ficheiros Excel base em `imports/` para importar dados e, se
necessário, sincronize o esquema com `python tools/cleanup_schema.py`.
Place the base Excel files in `imports/` to import data and, if needed,
synchronize the schema with `python tools/cleanup_schema.py`.

## Importação de dados / Data Import

Para importar ou atualizar dados coloque os três ficheiros Excel dentro do
diretório `imports/` na raiz do projeto. Os nomes são fixos e **sensíveis a
acentuação**:
To import or update data, place the three Excel files inside the `imports/`
directory at the project root. The names are fixed and **accent-sensitive**:

- `FichasTecnicas_base.xlsx`
- `PreçosTaxas_base.xlsx`
- `Produtos_Base.xlsx`

Veja [docs/mapeamento_campos.md](docs/mapeamento_campos.md)
para a correspondência completa de cabeçalhos Excel ↔ campos de base de dados.
Apenas `PrecosTaxas.Iva1` é utilizado em cálculos de IVA.
See [docs/mapeamento_campos.md](docs/mapeamento_campos.md) for the full mapping
of Excel headers ↔ database fields. Only `PrecosTaxas.Iva1` is used in VAT
calculations.

No início da operação os ficheiros são validados: se algum estiver em falta ou não tiver
extensão `.xlsx`, a importação é interrompida com erro.
Após processamento com sucesso, cada ficheiro é movido para `imports/history` com um
carimbo temporal (`YYYYMMDDHHMMSS`) anexado ao nome, permitindo manter um histórico de
cargas.
At the start of the operation the files are validated: if any are missing or not
`.xlsx`, the import stops with an error.
After successful processing, each file is moved to `imports/history` with a timestamp
(`YYYYMMDDHHMMSS`) appended to the name, allowing a history of loads.

Ao importar `FichasTecnicas_base.xlsx` a coluna de custo deve chamar-se
`Preco`, correspondendo diretamente ao campo `Preco` na base de dados.
When importing `FichasTecnicas_base.xlsx`, the cost column must be named
`Preco`, matching the `Preco` field in the database.

## Migração de esquema / Schema Migration

Para bases de dados já existentes, utilize o script `tools/cleanup_schema.py` para
sincronizar as tabelas `Produtos`, `FichasTecnicas` e `PrecosTaxas` com os cabeçalhos
actuais dos ficheiros Excel.
Antes de qualquer alteração é criado um backup (`ftv.db.bak`) da base de dados.
For existing databases, use the `tools/cleanup_schema.py` script to synchronize the
`Produtos`, `FichasTecnicas`, and `PrecosTaxas` tables with the current Excel headers.
Before any change, a backup (`ftv.db.bak`) of the database is created.

```bash
python tools/cleanup_schema.py
```

Certifique-se de que os três ficheiros base se encontram em `imports/`.  
Ensure that the three base files are in `imports/`.

## Segurança / Security

Para recomendações sobre gestão de palavras-passe, encriptação, utilização de
tokens/API keys e políticas de permissões, consulte
[docs/security.md](docs/security.md).
O documento inclui também boas práticas de deploy seguro e orientação para gerir
credenciais em desenvolvimento e produção.
For recommendations on password management, encryption, use of tokens/API keys, and
permission policies, see [docs/security.md](docs/security.md).
The document also includes best practices for secure deployment and guidance on managing
credentials in development and production.

## Resolução de Problemas / Troubleshooting

Se o ficheiro da base de dados estiver ausente, a aplicação cria
automaticamente um ficheiro vazio em `databases/ftv.db`.
If the database file is missing, the application automatically creates an
empty file at `databases/ftv.db`.

Para utilizar a base de dados com conteúdo:  
To use a database with content:

1. **Copie a BD fornecida para o local esperado**
   **Copy the provided DB to the expected location**

   - **Unix**

     ```bash
     cp /caminho/para/ftv.db databases/ftv.db
     ```

   - **Windows**

     ```powershell
     copy C:\\caminho\\para\\ftv.db databases\\ftv.db
     ```

2. **Defina a variável de ambiente `FTV_DB_PATH`**
   **Set the `FTV_DB_PATH` environment variable**

   - **Unix**

     ```bash
     export FTV_DB_PATH=/caminho/para/ftv.db
     ```

   - **Windows**

     ```powershell
     setx FTV_DB_PATH "C:\\caminho\\para\\ftv.db"
     ```

Para diagnosticar problemas, verifique nos logs a mensagem "Base de dados
criada automaticamente..."; ela indica que o ficheiro foi criado vazio e deve
ser substituído pela BD real.
To diagnose issues, check the logs for the message "Base de dados criada
automaticamente..."; it indicates the file was created empty and should be
replaced with the real database.

