# Interface do Ninescript

A pasta concentra a IDE, o console, o dicionário, o debugger e a imagem de fundo.
O núcleo da linguagem é independente e fica em `../linguagem.py`.

Na raiz do projeto, execute `python ide.py` ou abra `iniciar_ide.pyw` com dois
cliques, se arquivos Python estiverem associados à instalação no Windows.
Não execute `interface/ide.py` diretamente: use o iniciador da raiz.

## Controles

- **Novo / Abrir / Salvar**: cria ou edita arquivos `.nine`. Há confirmação
  para salvar alterações antes de trocar de arquivo ou fechar.
- **Exemplos**: selecione e clique em Carregar exemplo, ou dê dois cliques.
- **Executar (F5)**: executa o código atual, mesmo sem salvar.
- **Resultado**: mostra saída, erros e retorno. Na solicitação de entrada,
  digite no campo inferior e pressione Enter ou Enviar.
- **Tokens / Python gerado**: mostram as etapas da linguagem. Troque de aba
  e volte a ela para atualizar a análise depois de editar.
- **Dicionário (menu ou F1)**: consulta os 29 termos da linguagem, com busca,
  explicações e exemplos. **Copiar programa** copia um programa completo,
  incluindo `soberania()`, pronto para colar no editor e executar.
  Todos os termos estão implementados.
- **Opacidade do fundo**: ajusta a imagem de 0% a 100%, sem reiniciar.
  O ajuste vale para a janela atual. O padrão fica em `console.py`, no argumento
  `opacidade=0.5`. A propriedade `console.opacidade` também pode ser alterada em execução.

## Debugger

- **Depurar (F6)** pausa antes do primeiro comando.
- **Próximo (F10)** executa a linha amarela e pausa no comando seguinte.
  O debugger entra nas funções chamadas; a tabela mostra as variáveis da
  função atual, incluindo seus parâmetros.
- **Continuar (F5)** retoma até outro ponto de parada ou o fim.
- **Pausar** solicita pausa no próximo comando executável.
- **Parar (Shift+F5)** encerra a execução, inclusive laços infinitos ou espera de entrada.
- Clique no número de uma linha para marcar/desmarcar um ponto de parada.
  Comentários, linhas vazias e chaves isoladas não geram pausas.
- **Variáveis** mostra os valores antes da linha amarela. A tabela mantém
  a última pausa até a próxima execução.

O editor fica bloqueado durante a execução. Editar o código remove os pontos
de parada para evitar posições antigas. Os erros destacam a linha em vermelho.
Para acompanhar claramente os passos, escreva um comando por linha.

## Organização

| Arquivo | Responsabilidade |
|---|---|
| `ide.py` | Janela, controles, editor e arquivos. |
| `console.py` | Texto e imagem de fundo redimensionável. |
| `dicionario.py` | Consulta do vocabulário do `BASE.txt`. |
| `depurador.py` | Processo separado, filas e rastreamento com `sys.settrace`. |
| `assets/` | Imagem local e sua origem. |

Só a janela principal altera os elementos gráficos. O debugger usa o mapa
de linhas fornecido por `linguagem.py`; o núcleo não depende de Tkinter nem
dos mecanismos de pausa. A imagem usa recursos do próprio Tkinter, sem Pillow.
