# Interface Qt Quick (legado)

Mantemos os artefactos QML apenas por motivos históricos e de referência, mas
o fluxo atual da aplicação está centrado no front-end Qt Widgets e no back-end
Python. O ``Main.qml`` e os helpers em ``ui/qquick_app.py`` não são carregados
no arranque normal (não há chamadas para ``load_qquick_app`` no código), pelo
que quaisquer estruturas ou ordenações de blocos descritas para a interface Qt
Quick já não refletem o produto entregue.
