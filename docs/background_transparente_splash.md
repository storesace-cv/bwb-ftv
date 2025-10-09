# Exportação do splash com imagem de fundo transparente

Este guia documenta, passo a passo, como o projeto FTV implementa o ecrã inicial com
uma imagem PNG transparente aplicada como fundo. A intenção é permitir que outro
repositório (também automatizado pelo Codex) replique o mesmo comportamento apenas
ajustando o ficheiro gráfico.

## 1. Estrutura base do `SplashScreen`

A classe `SplashScreen` vive em `ui/splashscreen.py` e é uma subclasse de
`QDialog`. Durante a inicialização são aplicados três pontos cruciais para
respeitar o canal alfa da imagem:

1. Flags da janela `Qt.SplashScreen | Qt.FramelessWindowHint` para remover
   moldura e apresentá-la como splash.
2. Atributo `Qt.WA_TranslucentBackground` + `setStyleSheet("background: transparent;")`
   para que o Qt desenhe o diálogo sem preencher o fundo.
3. Um `QLabel` filho cobre toda a área (`800×500`) e recebe o `QPixmap` criado a
   partir de `bwb-Splash.png`. O próprio `QLabel` também recebe
   `background: transparent;` para não opacar a imagem. 【F:ui/splashscreen.py†L16-L27】

O resultado é uma janela cuja forma fica totalmente definida pelo PNG com
transparência.

## 2. Preparação da imagem

* **Localização**: a imagem é colocada na mesma pasta do módulo (`ui/`). O
  carregamento usa `Path(__file__).with_name(...)`, evitando caminhos absolutos e
  facilitando a portabilidade entre projetos. 【F:ui/splashscreen.py†L23-L27】
* **Dimensões**: o `setFixedSize` do diálogo deve coincidir com a resolução da
  imagem para impedir esticamentos inesperados. Se o novo ficheiro tiver outro
  tamanho, ajuste este valor em conformidade.
* **Nomes diferentes**: noutro repositório basta copiar a classe e trocar o
  nome do ficheiro PNG. Ex.: `Path(__file__).with_name("minha-app-splash.png")`.

## 3. Mensagens e overlays opcionais

A classe pode sobrepor texto e botões sem destruir a transparência:

* `show_message` cria um `QLabel` adicional, aplica um estilo só de texto e
  posiciona-o acima do fundo. Como este widget é independente do
  `QLabel` base, o PNG permanece visível. 【F:ui/splashscreen.py†L37-L50】
* `overlay` e `add_button_box` permitem adicionar botões temporários sem
  alterar o fundo, mantendo a noção de que a imagem continua “atrás” das
  interações. 【F:ui/splashscreen.py†L52-L79】

Estas funcionalidades são opcionais; caso não sejam necessárias, podem ser
removidas, mas nada nelas compromete o fundo transparente.

## 4. Integração no ciclo de arranque

O entrypoint `bwb-fichas_tecnicas.py` demonstra como criar e mostrar o splash
sem perder a transparência:

1. Cria a `QApplication` através de `ensure_ftv_app()`, que também aplica a folha
   de estilos global da aplicação. 【F:ui/app_launcher.py†L42-L70】
2. Instancia `SplashScreen()` e exibe mensagens enquanto correm tarefas de
   arranque (como migrações). 【F:bwb-fichas_tecnicas.py†L66-L78】
3. Chama `exec_modal` quando não existem tarefas pendentes, deixando o utilizador
   fechar o splash manualmente. 【F:bwb-fichas_tecnicas.py†L69-L78】

Se levar a classe para outro repositório, siga a mesma ordem: criar a aplicação
Qt, instanciar o splash, mostrar mensagens conforme necessário e só depois abrir
as restantes janelas.

## 5. Passos para reutilização noutro repositório

1. Copie `ui/splashscreen.py` e ajuste o nome do PNG na linha do `QPixmap`.
2. Acrescente o novo ficheiro de imagem (com transparência) ao lado do módulo.
3. Confirme que o tamanho definido em `setFixedSize` corresponde à nova arte.
4. No entrypoint da outra aplicação, importe `SplashScreen`, crie a instância e
   siga o mesmo fluxo de exibição descrito acima.
5. Garanta que a folha de estilos global (se existir) não atribui cores sólidas
   ao splash ou ao `QLabel` de fundo.

Com estes passos, qualquer outro projeto conseguirá replicar um splash screen com
imagem de fundo transparente, apenas alterando o ficheiro gráfico e mantendo o
mesmo comportamento visual. Isto permite que a automação (Codex) leia o presente
manual, aplique as alterações e gere um arranque visualmente idêntico.
