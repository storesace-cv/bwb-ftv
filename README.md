# bwb-ftv
Fichas Técnicas Valorizadas

## Database configuration

Por omissão a aplicação utiliza a base de dados SQLite em
`<raiz do projeto>/databases/ftv.db`. O diretório é criado automaticamente e o
ficheiro é inicializado caso esteja em falta.


Para alterar o local da base de dados defina a variável de ambiente
`FTV_DB_PATH` com o caminho completo para o ficheiro desejado:

```bash
export FTV_DB_PATH=/caminho/para/custom.db
```

## Importação de dados

Para importar ou atualizar dados coloque os três ficheiros Excel dentro do diretório `imports/` na raiz do projeto. Os nomes são fixos e **sensíveis a acentuação**:

- `FichasTecnicas_base.xlsx`
- `PreçosTaxas_base.xlsx`
- `Produtos_Base.xlsx`

No início da operação os ficheiros são validados: se algum estiver em falta ou não tiver extensão `.xlsx`, a importação é interrompida com erro. Após processamento com sucesso, cada ficheiro é movido para `imports/history` com um carimbo temporal (`YYYYMMDDHHMMSS`) anexado ao nome, permitindo manter um histórico de cargas.

Ao importar `FichasTecnicas_base.xlsx` a coluna de custo pode surgir como
`custo` ou `total`; ambas são automaticamente mapeadas para o campo `total`
na base de dados.

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
