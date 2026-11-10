"""Executa e depura em outro processo. Este módulo não depende da interface.

A IDE envia comandos por uma fila e recebe eventos por outra. O processo pode
ser encerrado mesmo quando o programa tem um laço infinito ou aguarda entrada.
"""

from queue import Empty
from contextlib import contextmanager
import sys

from linguagem import ARQUIVO_GERADO, ErroLinguagem, executar, traduzir


@contextmanager
def rastrear(codigo, observar):
    """O rastreamento pertence ao debugger, não às etapas da linguagem."""
    origens = traduzir(codigo).origens

    def visitar(frame, evento, argumento):
        nome = frame.f_code.co_name
        if frame.f_code.co_filename != ARQUIVO_GERADO or not (nome == "_principal" or nome.startswith("_f_")):
            return None
        if evento == "line":
            token = origens.get(frame.f_lineno)
            if token:
                variaveis = {nome.removeprefix("_v_"): valor
                             for nome, valor in frame.f_locals.items() if nome.startswith("_v_")}
                observar(token, variaveis)
        return visitar

    anterior = sys.gettrace()
    sys.settrace(visitar)
    try:
        yield
    finally:
        sys.settrace(anterior)


def executar_processo(codigo, depurar, pontos, comandos, eventos):
    parar_na_proxima = depurar
    pontos = set(pontos)

    def atualizar(comando):
        nonlocal parar_na_proxima, pontos
        acao, valor = comando
        if acao == "pausar":
            parar_na_proxima = True
        elif acao == "pontos":
            pontos = set(valor)

    def observar(token, variaveis):
        nonlocal parar_na_proxima
        while True:
            try:
                atualizar(comandos.get_nowait())
            except Empty:
                break
        if not parar_na_proxima and token.linha not in pontos:
            return
        valores = {nome: (type(valor).__name__, repr(valor)[:500])
                   for nome, valor in variaveis.items()}
        eventos.put(("pausa", (token.linha, token.coluna, valores)))
        while True:
            comando = comandos.get()
            acao, valor = comando
            if acao in {"continuar", "passo"}:
                parar_na_proxima = acao == "passo"
                return
            atualizar(comando)

    def entrada(mensagem=""):
        eventos.put(("entrada", str(mensagem)))
        while True:
            comando = comandos.get()
            if comando[0] == "entrada":
                eventos.put(("saida", str(comando[1]) + "\n"))
                return comando[1]
            atualizar(comando)

    def saida(*valores, sep=" ", end="\n"):
        eventos.put(("saida", sep.join(str(valor) for valor in valores) + end))

    try:
        with rastrear(codigo, observar):
            retorno = executar(codigo, entrada=entrada, saida=saida)
        eventos.put(("fim", repr(retorno)))
    except ErroLinguagem as erro:
        eventos.put(("erro", (erro.formatar(codigo), erro.linha, erro.coluna)))
    except Exception as erro:
        eventos.put(("falha", f"Falha interna: {type(erro).__name__}: {erro}"))
