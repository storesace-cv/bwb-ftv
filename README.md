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
