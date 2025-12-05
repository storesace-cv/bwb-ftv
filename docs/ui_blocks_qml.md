# Ordem dos blocos na interface Qt Quick

A interface experimental em Qt Quick apresenta os blocos de informação na seguinte ordem vertical:

1. **Identificação do Produto** — código e designação do artigo (``Block`` `identificationBlock`).
2. **Dados Técnicos** — estado e validade (``Block`` `technicalBlock`).
3. **Ficha Técnica** — lista de ingredientes (``Block`` `ingredientsBlock`).
4. **Informação Complementar** — observações do Food Cost (``Block`` `overlayBlock`).

Os blocos estão declarados sequencialmente no ficheiro `ui/qml/Main.qml`, em ``ColumnLayout`` que estrutura a página.
