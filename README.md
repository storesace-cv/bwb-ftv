# bwb-ftv
Fichas Técnicas Valorizadas

A aplicação permite gerir fichas técnicas de produtos e receitas na restauração.
Importa dados a partir de folhas de cálculo Excel exportados do NET-bo,
sincroniza com o ecossistema NET-bo, regista alergénios por ingrediente e armazena toda a
informação numa base de dados SQLite.
Esta aplicação foi criada pela [BWB – Business with Brains](https://bwb.pt).

Principais funcionalidades:

- Importação de produtos, fichas técnicas e preços via Excel.
- Integração com NET-bo para atualização de preços e taxas através de ficheiros Excel exportados.
- Gestão de alergénios ao nível de ingredientes e produtos finais.
- Base de dados local em SQLite com suporte a backups e migrações de esquema.

## Tecnologias

- **Python 3 / PyQt5** – Interface gráfica da aplicação.
- **openpyxl** – Leitura e validação dos ficheiros Excel.
- **sqlite3** – Armazenamento local dos dados.
- **NET-bo** – Fonte externa de produtos, preços e taxas via exportações Excel.

## Instalação

Atualize os pacotes do sistema e instale a biblioteca OpenGL necessária para o
PyQt5:

```bash
sudo apt-get update
sudo apt-get install -y libgl1 # use libgl1-mesa-glx se libgl1 não estiver disponível
```

Depois, instale as dependências Python:

```bash
pip install -r requirements.txt
```

## Configuração

Por omissão, a aplicação utiliza a base de dados SQLite em
`<raiz do projeto>/databases/ftv.db`. O diretório é criado automaticamente e o
ficheiro é inicializado caso esteja em falta.

Para utilizar outro local, defina a variável de ambiente
`FTV_DB_PATH` com o caminho completo para o ficheiro desejado:

```bash
export FTV_DB_PATH=/caminho/para/custom.db
```

Para ativar logs detalhados, defina a variável `debug` como `0` ao iniciar a
aplicação:

```bash
debug=0 python bwb-fichas_tecnicas.py
```

## Execução

Inicie a interface principal com:

```bash
python bwb-fichas_tecnicas.py
```

Coloque os ficheiros Excel base em `imports/` para importar dados e, se
necessário, sincronize o esquema com `python tools/cleanup_schema.py`.

## Importação de dados

Para importar ou atualizar dados coloque os três ficheiros Excel dentro do diretório `imports/` na raiz do projeto. Os nomes são fixos e **sensíveis a acentuação**:

- `FichasTecnicas_base.xlsx`
- `PreçosTaxas_base.xlsx`
- `Produtos_Base.xlsx`

No início da operação os ficheiros são validados: se algum estiver em falta ou não tiver extensão `.xlsx`, a importação é interrompida com erro. Após processamento com sucesso, cada ficheiro é movido para `imports/history` com um carimbo temporal (`YYYYMMDDHHMMSS`) anexado ao nome, permitindo manter um histórico de cargas.

Ao importar `FichasTecnicas_base.xlsx` a coluna de custo pode surgir como
`custo` ou `total`; ambas são automaticamente mapeadas para o campo `total`
na base de dados.

## Migração de esquema

Para bases de dados já existentes, utilize o script `tools/cleanup_schema.py`
para sincronizar as tabelas `Produtos`, `FichasTecnicas` e `PrecosTaxas` com
os cabeçalhos actuais dos ficheiros Excel. Antes de qualquer alteração é
criado um backup (`ftv.db.bak`) da base de dados.

```bash
python tools/cleanup_schema.py
```

Certifique-se de que os três ficheiros base se encontram em `imports/`.

## Segurança

Para recomendações sobre gestão de palavras-passe, encriptação, utilização de tokens/API keys e políticas de permissões, consulte [docs/security.md](docs/security.md). O documento inclui também boas práticas de deploy seguro e orientação para gerir credenciais em desenvolvimento e produção.

## Troubleshooting

Se o ficheiro da base de dados estiver ausente, a aplicação cria
automaticamente um ficheiro vazio em `databases/ftv.db`.

Para utilizar a base de dados com conteúdo:

1. **Copie a BD fornecida para o local esperado**

   - **Unix**

     ```bash
     cp /caminho/para/ftv.db databases/ftv.db
     ```

   - **Windows**

     ```powershell
     copy C:\\caminho\\para\\ftv.db databases\ftv.db
     ```

2. **Defina a variável de ambiente `FTV_DB_PATH`**

   - **Unix**

     ```bash
     export FTV_DB_PATH=/caminho/para/ftv.db
     ```

   - **Windows**

     ```powershell
     setx FTV_DB_PATH "C:\\caminho\\para\\ftv.db"
     ```

Para diagnosticar problemas, verifique nos logs a mensagem
"Base de dados criada automaticamente..."; ela indica que o ficheiro foi
criado vazio e deve ser substituído pela BD real.
