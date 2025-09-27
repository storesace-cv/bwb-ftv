# Debug e Logging no ReportBro e ReportBro Edit

## Debug no ReportBro (Biblioteca Python)

O **ReportBro** possui um **modo de debug** que ativa verificações extras durante a geração de relatórios, ajudando a identificar erros lógicos, problemas em expressões (como cálculos ou condições) e falhas na renderização. Ele exibe warnings ou erros detalhados no console.

### Como ativar:
- Na inicialização da classe `Report`, passe o parâmetro `debug=True`:
  ```python
  from reportbro import Report

  report = Report(template_source, debug=True)  # Ativa o modo debug
  report.generate()  # Gera o relatório com logs de debug
  ```
- Isso imprime mensagens no console (stdout/stderr), como erros em parâmetros, expressões inválidas ou problemas de layout.
- **Benefícios**: Facilita o troubleshooting em desenvolvimento, mostrando, por exemplo, o traceback de falhas em cálculos.
- **Limitações**: Logs vão para o console, não são persistentes. Para logging robusto, use o módulo `logging` do Python:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  # Exceções do ReportBro serão logadas com detalhes
  ```
- **Integração na aplicação**: defina a variável de ambiente `FTV_REPORTBRO_DEBUG=1` (ou qualquer valor não vazio) para forçar o modo debug no pipeline de geração de PDFs. Em alternativa, ativar `logging` em nível `DEBUG` também ativa automaticamente esta flag.

### Mais informações:
- Consulte o guia oficial: [Debug Mode no Framework ReportBro](https://www.reportbro.com/framework/guide/6/debug-mode).

## Debug no ReportBro Edit/Designer (Editor JavaScript)

O **ReportBro Edit** (ou Designer) é uma ferramenta visual para criar/editar templates no browser. O debug é feito principalmente via **ferramentas de desenvolvedor do navegador** (ex.: Chrome DevTools).

### Como debugar:
- Abra o console (F12 > Console) e execute o Designer. Erros em templates, previews ou integrações aparecem no console.
  - Exemplo de erro comum: `TypeError: $(...).reportBro is not a function` – indica falha na inclusão do script `reportbro.js`. Verifique se os arquivos JS/CSS estão carregados.
- **Modo Preview**: Teste templates com dados de amostra no Designer. Erros (ex.: expressões inválidas) são exibidos na interface ou console.
- **Modo de Desenvolvimento**: Para debug avançado, use `npm run dev` no build do Designer para gerar logs detalhados no console.
- **Logging**: Não há logging built-in, mas adicione `console.log()` em callbacks personalizados (ex.: ao carregar templates). Para produção, evite logs; use ferramentas como Sentry para logging remoto.

## Tratamento Geral de Erros e Logging

- **Captura de Exceções**: No ReportBro Lib, erros são lançados como `ReportBroError`. Capture e logue:
  ```python
  try:
      report.generate()
  except Exception as e:
      print(f"Erro no ReportBro: {e}")  # Ou use logging.error(e)
  ```
- **Sem Logging Nativo Avançado**: Não há configurações para levels de log (debug/info/warn). No Python, use o módulo `logging`. No Designer JS, use `console.debug()` em scripts customizados.
- **Problemas Comuns**:
  - Erros em templates: Verifique expressões no preview do Designer.
  - Falhas na geração: Ative debug e inspecione o dict de dados de entrada.
  - Consulte o [Google Group do ReportBro](https://groups.google.com/g/reportbro) para dicas comunitárias.

## Recursos Adicionais
- [Documentação oficial do ReportBro](https://www.reportbro.com/docs/)
- [GitHub do reportbro-lib](https://github.com/jobsta/reportbro-lib)

# ReportBro — schema inferido do template

## Chaves de topo do documento

- `docElements`
- `documentProperties`
- `parameters`
- `reportId`
- `styles`
- `version`
- `watermarks`


## `docElements` — tipos encontrados

- `image`
- `text`
- `table`


## `docElements` — chaves e valores (global)

| key | types | present_% | exemplos/intervalo |
|---|---|---:|---|
| `backgroundColor` | str | 100.0% | .. |
| `containerId` | str | 100.0% | 0_content |
| `elementType` | str | 100.0% | image, table, text |
| `height` | int | 100.0% | 140, 18 |
| `horizontalAlignment` | str | 100.0% | left |
| `id` | int | 100.0% | 1, 10, 2, 3, 4, 5, 6, 7, 8, 9 |
| `link` | str | 100.0% | .. |
| `printIf` | null, str | 100.0% | .. |
| `removeEmptyElement` | bool | 100.0% | false |
| `spreadsheet_addEmptyRow` | bool | 100.0% | false |
| `spreadsheet_column` | str | 100.0% | .. |
| `spreadsheet_hide` | bool | 100.0% | false |
| `styleId` | int, str | 100.0% | 1.0..2.0 |
| `verticalAlignment` | str | 100.0% | top |
| `width` | int | 100.0% | 140, 160, 169, 515 |
| `x` | int | 100.0% | 0, 150, 350 |
| `y` | int | 100.0% | 100, 112, 136, 160, 64, 88 |
| `alwaysPrintOnSamePage` | bool | 98.1% | true |
| `bold` | bool | 98.1% | false, true |
| `borderAll` | bool | 98.1% | false |
| `borderBottom` | bool | 98.1% | false |
| `borderColor` | str | 98.1% | #000000 |
| `borderLeft` | bool | 98.1% | false |
| `borderRight` | bool | 98.1% | false |
| `borderTop` | bool | 98.1% | false |
| `borderWidth` | int | 98.1% | 0 |
| `content` | str | 98.1% | ${product_codigo}, ${product_familia}, ${product_nome}, ${product_subfamilia}, CÓDIGO:, FAMÍLIA:, FICHA DE ARTIGO, NOME DO ARTIGO:, SUB-FAMÍLIA:, TIPOS ARTIGOS |
| `cs_additionalRules` | str | 98.1% | .. |
| `cs_backgroundColor` | str | 98.1% | .. |
| `cs_bold` | bool | 98.1% | false, true |
| `cs_borderAll` | bool | 98.1% | false |
| `cs_borderBottom` | bool | 98.1% | false |
| `cs_borderColor` | str | 98.1% | #000000 |
| `cs_borderLeft` | bool | 98.1% | false |
| `cs_borderRight` | bool | 98.1% | false |
| `cs_borderTop` | bool | 98.1% | false |
| `cs_borderWidth` | str | 98.1% | 0 |
| `cs_condition` | str | 98.1% | .. |
| `cs_font` | str | 98.1% | Helvetica |
| `cs_fontSize` | int | 98.1% | 12, 16 |
| `cs_horizontalAlignment` | str | 98.1% | left |
| `cs_italic` | bool | 98.1% | false |
| `cs_lineSpacing` | int | 98.1% | 1 |
| `cs_paddingBottom` | int | 98.1% | 0 |
| `cs_paddingLeft` | int | 98.1% | 0 |
| `cs_paddingRight` | int | 98.1% | 0 |
| `cs_paddingTop` | int | 98.1% | 0 |
| `cs_strikethrough` | bool | 98.1% | false |
| `cs_styleId` | str | 98.1% | .. |
| `cs_textColor` | str | 98.1% | #000000 |
| `cs_underline` | bool | 98.1% | false |
| `cs_verticalAlignment` | str | 98.1% | top |
| `eval` | bool | 98.1% | false |
| `font` | str | 98.1% | Helvetica |
| `fontSize` | int | 98.1% | 12, 16 |
| `italic` | bool | 98.1% | false |
| `lineSpacing` | int | 98.1% | 1 |
| `paddingBottom` | int | 98.1% | 0 |
| `paddingLeft` | int | 98.1% | 0 |
| `paddingRight` | int | 98.1% | 0 |
| `paddingTop` | int | 98.1% | 0 |
| `pattern` | str | 98.1% | .. |
| `richText` | bool | 98.1% | false |
| `richTextContent` | null | 98.1% | None |
| `richTextHtml` | str | 98.1% | .. |
| `spreadsheet_colspan` | str | 98.1% | .. |
| `spreadsheet_pattern` | str | 98.1% | .. |
| `spreadsheet_textWrap` | bool | 98.1% | false |
| `spreadsheet_type` | str | 98.1% | .. |
| `strikethrough` | bool | 98.1% | false |
| `textColor` | str | 98.1% | #000000 |
| `underline` | bool | 98.1% | false |
| `image` | str | 1.9% | .. |
| `imageFilename` | str | 1.9% | .. |
| `source` | str | 1.9% | product_image |

> ℹ️ **FT Gestão e imagens de produto** — o template atualizado deixa de
> depender da `source` "product_image" e passa a recorrer ao atributo
> `imageFilename`. O resolver `resolve_product_image` define esse valor com base
> no código do produto, produzindo o caminho absoluto
> `/databases/images/{Produtos_Codigo}.png`. Ao introduzir novos elementos de
> imagem, garanta que apontam para o mesmo padrão de ficheiro através desse
> resolver.

## Campos de imagem

- **product_image_filename** (string) — caminho absoluto da imagem do produto, construído como `/databases/images/{Produtos_Codigo}.png`.
- Não usar `source` para este caso. O binding deve ser sempre `imageFilename`.

## `table` — tabela de ingredientes

- O template `reporting/templates/ft_gestao_00_base.json` define uma tabela com seis
  colunas: `FichasTecnicas_ComponenteNome`, `FichasTecnicas_Qtd`,
  `FichasTecnicas_Unidade`, `FichasTecnicas_Ppu`, `FichasTecnicas_Preco` e
  `FichasTecnicas_Peso`.
- Cada linha é preenchida a partir do dataset `${ingredientes}` construído em
  `reporting/ft_gestao.build_reportbro_context`, que converte os valores
  localizados em `float` antes de enviar para o template.
- Os testes de `tests/test_reportbro_export.py` cobrem a montagem deste dataset
  e evitam regressões na renderização da tabela.

## Dataset `${ingredientes}`

- Tipo: array de mapas com as chaves `FichasTecnicas_ComponenteNome`,
  `FichasTecnicas_Qtd`, `FichasTecnicas_Unidade`, `FichasTecnicas_Ppu`,
  `FichasTecnicas_Preco`, `FichasTecnicas_Peso` e `FichasTecnicas_Ordem`.
- Origem: `build_reportbro_context` copia `block_b2["ingredientes"]`, aplica
  `replace_localized_decimal` e `decimal_to_float` aos campos numéricos e ordena
  pelo índice `FichasTecnicas_Ordem`.
- Erros conhecidos: enviar strings com unidades ou símbolos monetários impede a
  conversão para `float`; conjuntos incompletos de ingredientes originam linhas
  vazias. Siga os testes de `tests/test_reportbro_export.py` como referência ao
  preparar novos dados.

