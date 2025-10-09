# Overlay Naming Scheme

This project uses a structured naming scheme for identifying overlay segments:

- **Blocks**: `B{n}` denote top-level blocks (e.g., `B1`, `B4`). Cada bloco agrupa um conjunto
  coeso de informações (dados gerais, ficha técnica, etc.).
- **Cells**: `C{n}` denotes root cells (e.g., `C1`, `C2`). Cell names are prefixed by their parent
  block, and each block resets cell numbering to 1 (e.g., `B1.C1`, `B4.C1`).
- **Horizontal subdivisions**: `.A` for the left section and `.B` for the right.
- **Vertical subdivisions**: `.1`, `.2`, etc.
- **Order**: Start with the block identifier followed by the cell name, then alternate horizontal and vertical markers as needed
  (e.g., `B2.C1.B.1`).

Overlays can obscure the underlying UI, so these names should only be visible when the **Overlays** toggle is switched ON. Click the **Overlays** button or press **Ctrl+D** in the application to toggle these labels.


## Interface QML

A interface QML carrega os módulos `QtQuick 2.15`, `QtQuick.Controls 2.15`, `QtQuick.Layouts 1.15` e `QtQuick.Window 2.15`, garantindo que todos os elementos visuais são disponibilizados exclusivamente pela família Qt Quick.
O contêiner principal é um `ApplicationWindow` com `id: root`, largura 1180, altura 860 e título "Ficha Técnica (Qt Quick)", que também expõe propriedades como `product`, `hasPrevious` e `hasNext` para gerir a navegação interna.
Este `ApplicationWindow` define `background: Rectangle` para pintar o fundo e implementa funções como `loadPrevious()` e `loadNext()` que controlam os botões de navegação, ilustrando como a lógica fica embebida no próprio componente Qt Quick.
A propriedade `menuBar` desse `ApplicationWindow` instancia um `MenuBar` que por sua vez cria um menu `Menu { title: "Ficheiro" }` recheado de `MenuItem` cuja ação `onTriggered` abre (`aboutWindow.open()`) ou fecha (`aboutWindow.close()`) a janela de informação e finaliza a aplicação com `Qt.quit()`.
O segundo `Menu` chamado "Navegação" liga cada `MenuItem` às funções `root.loadPrevious()` e `root.loadNext()`, ativando-os com `enabled: root.hasPrevious` e `enabled: root.hasNext`, demonstrando a ligação direta entre estado e apresentação via propriedades Qt Quick.

### Hierarquia da barra de menus

```
MenuBar (ApplicationWindow.menuBar)
│
├── Menu "Ficheiro"
│   │
│   ├── MenuItem "Sobre…" (abre a janela modal "Sobre")
│   ├── MenuItem "Fechar Sobre" (fecha a janela modal "Sobre")
│   ├── MenuSeparator
│   └── MenuItem "Sair" (termina a aplicação)
│
└── Menu "Navegação"
    │
    ├── MenuItem "Anterior" (chama `root.loadPrevious()`)
    └── MenuItem "Seguinte" (chama `root.loadNext()`)
```

A janela "Sobre" é um `Window` separado com `id: aboutWindow`, `modality: Qt.WindowModal` e `flags: Qt.Dialog`, tornando-se visível apenas quando chamado pelo menu e hospedando um `Rectangle` com cantos arredondados para estruturar o conteúdo.
Dentro desse `Rectangle`, uma árvore de layout `ColumnLayout` organiza `Label` e `Button` provenientes de Qt Quick Controls, incluindo um botão que fecha a janela ao executar `aboutWindow.close()`.
O cabeçalho da janela principal usa `header: ToolBar` contendo um `RowLayout` com `ToolButton` para avançar ou recuar na listagem, cada um com `ToolTip` configurado através das propriedades do mesmo módulo.
Assim, a janela principal, a barra de menus, os submenus de navegação e o diálogo "Sobre" demonstram uma hierarquia coerente de QML construída apenas com componentes importados de Qt Quick e seus módulos complementares.
