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


## `docElements` — chaves e valores (global)

| key | types | present_% | exemplos/intervalo |
|---|---|---:|---|
| `backgroundColor` | str | 100.0% | .. |
| `containerId` | str | 100.0% | 0_content |
| `elementType` | str | 100.0% | image, text |
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

