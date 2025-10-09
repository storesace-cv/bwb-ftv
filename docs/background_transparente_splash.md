# Exportação do splash com imagem de fundo transparente

Este guia documenta, passo a passo, como o projeto FTV implementa o ecrã inicial com
uma imagem PNG transparente aplicada como fundo. A intenção é permitir que outro
repositório (também automatizado pelo Codex) replique o mesmo comportamento apenas
ajustando o ficheiro gráfico.

## 1. Estrutura base do `SplashScreen`

A classe `SplashScreen` vive em `ui/splashscreen.py` e é uma subclasse de
`QDialog`. Durante a inicialização são aplicados quatro pontos cruciais para
respeitar o canal alfa da imagem e permitir que o Qt mantenha o fundo
totalmente transparente:

1. Flags da janela `Qt.SplashScreen | Qt.FramelessWindowHint` para remover
   moldura e apresentá-la como splash.
2. Importante para o ambiente transparente: o atributo
   `Qt.WA_TranslucentBackground` é ativado **antes** de qualquer widget filho e
   combinado com `setStyleSheet("background: transparent;")`, garantindo que o
   Qt não pinta o contentor com uma cor sólida.
3. Um `QLabel` filho cobre toda a área (`800×500`) e recebe o `QPixmap` criado a
   partir de `bwb-Splash.png`. O próprio `QLabel` também recebe
   `background: transparent;` para não opacar a imagem.
4. O tamanho fixo (`setFixedSize`) mantém o diálogo com a mesma dimensão da
   imagem, evitando que o Qt escale o PNG e introduza artefactos de transparência.
   【F:ui/splashscreen.py†L16-L27】

O resultado é uma janela cuja forma fica totalmente definida pelo PNG com
transparência, sem flicker nem barras pretas durante o arranque.

## 2. Preparação da imagem

* **Localização**: a imagem é colocada na mesma pasta do módulo (`ui/`). O
  carregamento usa `Path(__file__).with_name(...)`, evitando caminhos absolutos e
  facilitando a portabilidade entre projetos. 【F:ui/splashscreen.py†L23-L27】
* **Dimensões**: o `setFixedSize` do diálogo deve coincidir com a resolução da
  imagem para impedir esticamentos inesperados. Se o novo ficheiro tiver outro
  tamanho, ajuste este valor em conformidade.
* **Nomes diferentes**: noutro repositório basta copiar a classe e trocar o
  nome do ficheiro PNG. Ex.: `Path(__file__).with_name("minha-app-splash.png")`.
* **Canal alfa**: confirme que o PNG exportado mantém transparência total (por
  exemplo, verificando no editor que o fundo continua em “checkerboard”). Sem
  canal alfa, o Qt preencherá a janela com a cor sólida da imagem.

## 3. Mensagens e overlays opcionais

A classe pode sobrepor texto e botões sem destruir a transparência:

* `show_message` cria um `QLabel` adicional, aplica um estilo só de texto e
  posiciona-o acima do fundo. Como este widget é independente do
  `QLabel` base, o PNG permanece visível. 【F:ui/splashscreen.py†L37-L50】
* `overlay` e `add_button_box` permitem adicionar botões temporários sem
  alterar o fundo, mantendo a noção de que a imagem continua “atrás” das
  interações. 【F:ui/splashscreen.py†L52-L79】

Estas funcionalidades são opcionais; caso não sejam necessárias, podem ser
removidas. O importante é manter os estilos dos widgets adicionais em
`background: transparent;` sempre que não for desejada opacidade.

## 4. Integração no ciclo de arranque

O entrypoint `bwb-fichas_tecnicas.py` demonstra como criar e mostrar o splash
sem perder a transparência:

1. **Bootstrap obrigatório**: importar `qt_bootstrap` logo no topo do módulo
   principal configura variáveis de ambiente Qt (plugins, fontes) antes de criar
   a aplicação. 【F:bwb-fichas_tecnicas.py†L9-L18】
2. **Criação da aplicação**: chamar `ensure_ftv_app()` cria (ou reutiliza) a
   instância de `QApplication`, ativa `Qt.AA_ShareOpenGLContexts` e aplica a
   folha de estilos partilhada. Sem este passo o tema global pode repintar o
   splash com cor sólida. 【F:ui/app_launcher.py†L41-L95】
3. **Instanciação do splash**: criar `SplashScreen()` e exibir mensagens enquanto
   correm tarefas de arranque (como migrações). Use `app.processEvents()` logo
   após `show_message` para garantir que o Qt desenha a mensagem sobre a imagem.
   【F:bwb-fichas_tecnicas.py†L60-L86】
4. **Encerramento controlado**: quando não existem tarefas pendentes, chamar
   `exec_modal(splash)` para deixar o utilizador fechar o splash manualmente sem
   piscar ou perder a transparência. 【F:ui/qt_compat.py†L17-L33】

Se levar a classe para outro repositório, siga a mesma ordem: bootstrap do Qt,
criação da aplicação, instanciar o splash, mostrar mensagens conforme necessário
e só depois abrir as restantes janelas.

## 5. Ambiente transparente consistente

Para que a transparência se mantenha em todas as plataformas suportadas, confirme
os pontos seguintes:

1. `Qt.WA_TranslucentBackground` está ativo tanto no diálogo como em qualquer
   widget que cubra a imagem base (ex.: legendas de progresso). 【F:ui/splashscreen.py†L18-L50】
2. Os estilos globais carregados por `ensure_ftv_app` não reintroduzem fundos
   opacos no splash. Se adicionar folhas de estilos adicionais, use regras mais
   específicas (`#SplashScreen QLabel { background: transparent; }`) para
   preservar o canal alfa. 【F:ui/app_launcher.py†L77-L95】
3. Teste o splash em cada sistema operativo alvo (Windows, Linux, macOS) e com
   diferentes GPUs. Sistemas sem compositor podem exigir a variável de ambiente
   `QT_QPA_PLATFORM=windows:darkmode=0` ou equivalentes — valide se a sua
   pipeline precisa de ajustes.
4. Ao substituir o PNG, confirme que os limites da imagem não contêm pixels
   semi-transparentes indesejados (bordos cinzentos). Estes serão exibidos porque
   o Qt respeita integralmente o canal alfa.

## 6. Passos para reutilização noutro repositório

1. Copie `ui/splashscreen.py` e ajuste o nome do PNG na linha do `QPixmap`.
2. Acrescente o novo ficheiro de imagem (com transparência) ao lado do módulo.
3. Confirme que o tamanho definido em `setFixedSize` corresponde à nova arte.
4. No entrypoint da outra aplicação, importe `qt_bootstrap` e `ensure_ftv_app`
   antes de instanciar o `SplashScreen`, replicando o fluxo descrito acima.
5. Garanta que a folha de estilos global (se existir) não atribui cores sólidas
   ao splash ou ao `QLabel` de fundo; prefira regras específicas para os widgets
   adicionais.
6. Execute a aplicação em cada plataforma suportada para confirmar que a
   transparência se mantém durante o arranque completo.

Com estes passos, qualquer outro projeto conseguirá replicar um splash screen com
imagem de fundo transparente, apenas alterando o ficheiro gráfico e mantendo o
mesmo comportamento visual. Isto permite que a automação (Codex) leia o presente
manual, aplique as alterações e gere um arranque visualmente idêntico.
