# NET-BO API V2

Documentação completa da API, convertida do PDF original.  
Inclui autenticação, tabelas, clientes, documentos, relatórios, helpers e tickets.

---

## Autenticação

### Obter servidor da empresa
`GET https://companies.api.net-bo.com/companies/detailed?company=<dbname>`

- **Parâmetros obrigatórios**:
  - `dbname`: nome da base de dados.
- **Resposta (JSON)**: contém informação da empresa e servidor.

### Obter token de acesso
`GET https://<server>.api.net-bo.com/api/auth?db=<dbname>&login=<login>&passwd=<password>`

- **Parâmetros obrigatórios**:
  - `db`: nome da base de dados.
  - `login`: utilizador NET-BO.
  - `passwd`: password.
- **Parâmetros opcionais**:
  - `user_type=pos` para validar um utilizador POS.
- **Resposta (JSON)**: devolve `token` e dados do utilizador.

---

## Tabelas

### Produtos
`GET /api/tables/products?db=<dbname>`  
Parâmetros opcionais: `is_sale`, `is_merc`, `is_prod`, `is_menu`, `deleted`.

### Produtos por loja
`GET /api/tables/store_sale_products?db=<dbname>&store_id=<store_id>`  
Lista produtos disponíveis por loja.

### Lojas
`GET /api/tables/stores?db=<dbname>`  
Pode filtrar por `id`, `ids`, `by_id`.

### Unidades
`GET /api/tables/units?db=<dbname>`  
Lista todas as unidades com abreviações, fatores, etc.

### Atualizar utilizador
`GET /api/tables/user_update?db=<dbname>`  
Permite atualizar dados do utilizador via JSON.

### Utilizadores
`GET /api/tables/users?db=<dbname>`  
Permite listar utilizadores, com filtros (`id`, `ids`, `by_id`, `by_fo_id`, `pos_users`, `netbo_users`).

### Clientes
`GET /api/tables/clients?db=<dbname>`  
Permite listar clientes, com filtros (`id`, `fo_id`, `ncontrib`).

### Criar cliente
`POST /api/tables/create_client?db=<dbname>`  
Cria novo cliente via JSON.

---

## Configurações

### Empresa
`GET /api/configurations/company?db=<dbname>`  
Devolve as configurações da empresa, módulos ativos, layout do dashboard, impostos, etc.

### Regiões fiscais e impostos
`GET /api/configurations/fiscal_regions_and_taxes?db=<dbname>`  
Lista regiões fiscais, taxas disponíveis e mapeamento por códigos SAF-T.

### Métodos de pagamento
`GET /api/configurations/payment_methods?db=<dbname>`  
Lista métodos de pagamento (`NU`, `MB`, `CC`, `TB`).

### Teclado de loja
`GET /api/configurations/store_keyboard?db=<dbname>&store_id=<store_id>`  
Lista produtos do teclado de uma loja.

### Propriedades de produtos do teclado
`GET /api/configurations/keyboard_products_properties?db=<dbname>&keyboard_id=<id>`

### Propriedades de grupos do teclado
`GET /api/configurations/keyboard_groups_properties?db=<dbname>&keyboard_id=<id>`

---

## Documentos

### Listar documentos
`GET /api/data/documents?db=<dbname>&date_from=&date_to=`  
Parâmetros opcionais: `document_types`, `export`, `get_products`, `store_fo_ids`.

### Criar fatura
`POST /api/documents/create_invoice?db=<dbname>`  
Corpo JSON com `headers`, `details`, `footers`. Documentos FS, FR ou FT.

### Criar nota de crédito a partir de fatura
`POST /api/documents/create_nc_from_invoice`  
Corpo JSON com `invoice_fo_doc_number`.

### Criar nota de crédito
Não implementado.

### Criar guia de transporte
Não implementado.

### Criar recibo
`POST /api/documents/create_receipt?db=<dbname>`  
Corpo JSON com `headers`, `documents`, `footers`.

---

## Movimentos

### Listar movimentos
`GET /movements/list?db=<dbname>&date_from=&date_to=&stores=`  
Lista transações num intervalo de datas.

### Movimento detalhado
`GET /movements/detailed?db=<dbname>&id=<id>&type=<type>`  
Tipos: `sales`, `transport_documents`, `working_documents`.

---

## Relatórios

### Vendas por dia
`GET /reports/sales/by_day?db=<dbname>&stores=&date_from=&date_to=`

### Stocks por armazém
`GET /reports/stocks/extract_per_warehouse?db=<dbname>&stores=&date=YYYY-MM-DD`

### Vendas por produto
`GET /api/sales_by_product?db=<dbname>&stores=&date_from=&date_to=`

### Vendas por data
`GET /api/sales_by_date?db=<dbname>&stores=&date_from=&date_to=`

### Vendas por meio de pagamento
`GET /api/sales_by_media?db=<dbname>&stores=&date_from=&date_to=`

### Vendas por cliente
`GET /api/sales_by_customer?db=<dbname>&stores=&date_from=&date_to=&export_to=json`

### Vendas detalhadas
`GET /api/sales_detailed?db=<dbname>&stores=&date_from=&date_to=`

### Vendas por documento/IVA
`GET /api/sales_by_doc_vat?db=<dbname>&stores=&date_from=&date_to=`

### Encomendas
`GET /api/orders?db=<dbname>&stores=&date_from=&date_to=&suppliers=&authorized=`

### Stock resumido por armazém
`GET /reports/stocks/stract_per_warehouse?db=<dbname>&stores=&date=YYYY-MM-DD`

---

## Helpers (Imagens e Ficheiros)

### Listar ficheiros de artigos
`GET /helpers/list_files?db=<dbname>&table=articles_images&id=<article_id>`

### Pré-visualizar ficheiro
`GET /helpers/preview_file?db=<dbname>&table=articles_images&id=<article_id>&filename=<file>`

### Download de ficheiro
`POST /helpers/download_file?db=<dbname>`  
Form-data: `table=articles_images`, `id=<article_id>`, `file=<filename>`.

---

## Tickets

### Criar ticket
`POST /tickets/ticket_create`

- **Headers**:
  - `Authorization: Bearer <token>`
  - `db: <dbname>`
- **Form-data**:
  - `title`: título
  - `description`: HTML
  - `external_name`
  - `external_email`
  - `store_id`
  - `project_id`
  - `status`: opened | ongoing | waiting
  - `due_date`: YYYY-MM-DD
  - Outros: `labels`, `assigned_user_id`, `participants`, `attachments`.

---

## Observações finais
- Todos os endpoints requerem o **token** obtido via `/api/auth`.  
- A maioria dos métodos suporta filtros opcionais.  
- As respostas vêm em **JSON** (com opção `csv`/`xls` em relatórios).  
- Documentos são **SAF-T prontos** (legais para Portugal).  
