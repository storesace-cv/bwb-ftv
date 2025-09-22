# flake8: noqa
"""
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
copy C:\\<caminho para Produtos_Base.xlsx> imports\\
copy C:\\<caminho para FichasTecnicas_base.xlsx> imports\\
copy C:\\<caminho para PreçosTaxas_base.xlsx> imports\\
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

Em instalações onde o Qt é fornecido pelo Homebrew, utilize a variável de
ambiente `FTV_QT_PLUGIN_PATH` para apontar para a raiz do Qt (por exemplo,
`/opt/homebrew/opt/qt`). Quando não definida, a aplicação procura
automaticamente por diretórios `plugins/platforms` em `HOMEBREW_PREFIX` e nos
caminhos habituais do Homebrew (`/opt/homebrew/opt/qt`, `/opt/homebrew/opt/qt@5`
e `/usr/local/opt/qt`).
On systems where Qt is provided by Homebrew, use the `FTV_QT_PLUGIN_PATH`
environment variable to point to the Qt prefix (for example,
`/opt/homebrew/opt/qt`). When unset, the application automatically searches for
`plugins/platforms` directories under `HOMEBREW_PREFIX` and the standard
Homebrew prefixes (`/opt/homebrew/opt/qt`, `/opt/homebrew/opt/qt@5`, and
`/usr/local/opt/qt`).

Para ativar logs detalhados, defina a variável `debug` como `0` ao iniciar a
aplicação:
To enable detailed logs, set the `debug` variable to `0` when launching the application:

```bash
debug=0 python bwb-fichas_tecnicas.py
```

Para preencher a tabela `Alergenios` com os valores padrão, defina a variável
de ambiente `FTV_SEED_ALERGENIOS` com um valor verdadeiro (`1`, `true`, `yes`
ou `on`) antes de iniciar a aplicação. Quando a variável não está definida, o
seeding fica desativado para permitir a importação prévia de um ficheiro JSON
de alergénios.
To populate the `Alergenios` table with the default values, set the
`FTV_SEED_ALERGENIOS` environment variable to a truthy value (`1`, `true`,
`yes`, or `on`) before launching the application. When the variable is not set,
the seeding step remains disabled so that an allergens JSON file can be
imported first.

Os ficheiros de importação de alergénios devem conter uma matriz (array) JSON
de objetos. Cada objeto representa um alergénio com as seguintes chaves:

- `id`: inteiro positivo obrigatório que identifica o registo.
- `nome`: nome em português, obrigatório e não pode estar vazio.
- `nome_ingles`: nome em inglês, obrigatório e não pode estar vazio.
- `descricao`: texto opcional com informação adicional.
- `exemplos`: valor JSON opcional (tipicamente uma lista ou objeto) com
  exemplos de ocorrência; é armazenado como texto JSON.
- `notas`: texto opcional com comentários adicionais.

Em alternativa ao array nu, o ficheiro pode envolver os registos num objeto
que contenha a chave `alergenios` apontada para essa mesma matriz. Uma
estrutura válida em formato de array é a seguinte:

```json
[
  {
    "id": 1,
    "nome": "Glúten",
    "nome_ingles": "Gluten",
    "descricao": "Presente em cereais como trigo e cevada.",
    "exemplos": [
      "Pão de trigo",
      {"produto": "Cevada malteada"}
    ],
    "notas": "Pode ocorrer contaminação cruzada."
  },
  {
    "id": 2,
    "nome": "Leite",
    "nome_ingles": "Milk",
    "descricao": null,
    "exemplos": ["Leite de vaca", "Queijo"],
    "notas": null
  }
]
```

Consulte `databases/allergens.example.json` para um ficheiro de referência que
pode ser duplicado e adaptado às necessidades do seu projeto.

Allergen import files must contain a JSON array of objects. Each object
represents an allergen with the following keys:

- `id`: required positive integer that uniquely identifies the record.
- `nome`: required Portuguese name; it must be a non-empty string.
- `nome_ingles`: required English name; it must be a non-empty string.
- `descricao`: optional free-text description.
- `exemplos`: optional JSON value (typically a list or object) with sample
  occurrences; it is persisted as JSON text.
- `notas`: optional free-text notes.

Instead of a bare array the file may also wrap the entries in an object whose
`alergenios` key points to that array. A valid array-based structure looks as
follows:

```json
[
  {
    "id": 1,
    "nome": "Glúten",
    "nome_ingles": "Gluten",
    "descricao": "Presente em cereais como trigo e cevada.",
    "exemplos": [
      "Pão de trigo",
      {"produto": "Cevada malteada"}
    ],
    "notas": "Pode ocorrer contaminação cruzada."
  },
  {
    "id": 2,
    "nome": "Leite",
    "nome_ingles": "Milk",
    "descricao": null,
    "exemplos": ["Leite de vaca", "Queijo"],
    "notas": null
  }
]
```

See `databases/allergens.example.json` for a ready-to-adapt reference file that
can be duplicated for your project.

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

## Sobreposições de desenvolvimento / Development overlays

Quando a variável de ambiente `BWB_DEV_OVERLAYS` está ativa, as legendas das
zonas passam para o estilo `bwb-style-overlays-on`. Esse estilo remove o fundo,
a borda e o preenchimento dos rótulos para que seja possível comparar o modo
normal com o modo de sobreposição apenas pela alteração de conteúdo. As
métricas de fonte e os alinhamentos mantêm-se, garantindo que quaisquer
diferenças observadas resultam da disposição real do texto.

When the `BWB_DEV_OVERLAYS` environment variable is enabled, zone labels use
the `bwb-style-overlays-on` style. The style removes the background, border, and
padding so that normal and overlay modes can be compared based solely on the
content differences. Font metrics and alignments are preserved, ensuring that
any perceived changes come from the actual text layout.

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
No início da operação os ficheiros são validados: se algum estiver em falta ou não tiver
extensão `.xlsx`, a importação é interrompida com erro.
Após processamento com sucesso, cada ficheiro é movido para `imports/history` com um
carimbo temporal (`YYYYMMDDHHMMSS`) anexado ao nome, permitindo manter um histórico de
cargas.
At the start of the operation the files are validated: if any are missing or not
`.xlsx`, the import stops with an error.
After successful processing, each file is moved to `imports/history` with a timestamp
(`YYYYMMDDHHMMSS`) appended to the name, allowing a history of loads.

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
     copy C:\\<caminho para ftv.db> databases\\ftv.db
     ```

2. **Defina a variável de ambiente `FTV_DB_PATH`**
   **Set the `FTV_DB_PATH` environment variable**

   - **Unix**

     ```bash
     export FTV_DB_PATH=/caminho/para/ftv.db
     ```

   - **Windows**

     ```powershell
     setx FTV_DB_PATH "C:\\<caminho para ftv.db>"
     ```

Para diagnosticar problemas, verifique nos logs a mensagem "Base de dados
criada automaticamente..."; ela indica que o ficheiro foi criado vazio e deve
ser substituído pela BD real.
To diagnose issues, check the logs for the message "Base de dados criada
automaticamente..."; it indicates the file was created empty and should be
replaced with the real database.
"""