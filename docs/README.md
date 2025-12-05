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


## Interface QML (legado)

A interface QML permanece no repositório apenas como referência histórica. O
arranque padrão da aplicação usa exclusivamente o front-end Qt Widgets e não
há pontos de entrada que chamem ``load_qquick_app`` ou carreguem ``Main.qml``.
Qualquer documentação anterior sobre navegação ou menus em Qt Quick deve ser
interpretada como obsoleta.

### Hierarquia da barra de menus

```
MenuBar (ApplicationWindow.menuBar)
│
├── Menu (title: "Ficheiro")
│   │
│   ├── MenuItem (text: "Sobre…") — abre a janela modal "Sobre"
│   ├── MenuItem (text: "Fechar Sobre") — fecha a janela modal "Sobre"
│   ├── MenuSeparator
│   └── MenuItem (text: "Sair") — termina a aplicação
│
└── Menu (title: "Navegação")
    │
    ├── MenuItem (text: "Anterior") — chama `root.loadPrevious()`
    └── MenuItem (text: "Seguinte") — chama `root.loadNext()`
```

### Hierarquia do menu Qt Widgets (botão "Menu")

O botão **Menu** no canto superior direito da interface Qt Widgets abre um `QMenu`
em cascata com os rótulos exatamente como apresentados ao utilizador:

```
QToolButton (text: "Menu")
│
├── QMenu (title: "Base de Dados")
│   │
│   ├── QAction (text: "Atualizar Dados") — executa `_on_update_data()`
│   ├── QAction (text: "Importar Dados") — chama `_on_import_data()`
│   └── QMenu (title: "Segurança")
│       │
│       ├── QAction (text: "Segurança") — invoca `backup_database()`
│       └── QAction (text: "Reposição") — invoca `restore_database()`
│
├── QMenu (title: "Tabelas")
│   │
│   ├── QAction (text: "Tipos Artigos") — abre o gestor de "Tipos de Artigos"
│   ├── QAction (text: "Validade") — abre o gestor de "Validade"
│   ├── QAction (text: "Temperaturas") — abre o gestor de "Temperaturas"
│   └── QAction (text: "Alergénios") — abre o gestor de "Alergénios"
│
├── QMenu (title: "Utilitários")
│   │
│   ├── QMenu (title: "Gestão de Documentos")
│   │   │
│   │   ├── QAction (text: "Editor de Documentos") — abre o editor ReportBro
│   │   ├── QAction (text: "Modelos Activos") — mostra os modelos activos
│   │   └── QAction (text: "Actualizar Documentos") — sincroniza os modelos
│   │
│   ├── QMenuSeparator
│   └── QAction (text: "Tema") — apresenta a mensagem sobre alternância de tema
│
└── QMenu (title: "Configurações")
    │
    └── QMenu (title: "Parametrizações")
        │
        ├── QAction (text: "Food Cost") — abre o editor de valores de food cost
        └── QAction (text: "Moeda") — abre a gestão de localização/moeda
```

A janela "Sobre" é um `Window` separado com `id: aboutWindow`, `modality: Qt.WindowModal` e `flags: Qt.Dialog`, tornando-se visível apenas quando chamado pelo menu e hospedando um `Rectangle` com cantos arredondados para estruturar o conteúdo.
Dentro desse `Rectangle`, uma árvore de layout `ColumnLayout` organiza `Label` e `Button` provenientes de Qt Quick Controls, incluindo um botão que fecha a janela ao executar `aboutWindow.close()`.
O cabeçalho da janela principal usa `header: ToolBar` contendo um `RowLayout` com `ToolButton` para avançar ou recuar na listagem, cada um com `ToolTip` configurado através das propriedades do mesmo módulo.
Assim, a janela principal, a barra de menus, os submenus de navegação e o diálogo "Sobre" demonstram uma hierarquia coerente de QML construída apenas com componentes importados de Qt Quick e seus módulos complementares.
