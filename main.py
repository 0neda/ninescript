"""Interface de terminal: python main.py exemplos/ola.nine"""

import argparse
import sys
from pathlib import Path

from linguagem import ErroLinguagem, analisar, executar, traduzir


def main():
    argumentos = argparse.ArgumentParser(description="Ninescript: linguagem memística baseada no BASE.txt.")
    argumentos.add_argument("arquivo", type=Path, help="Arquivo .nine a executar")
    modo = argumentos.add_mutually_exclusive_group()
    modo.add_argument("--tokens", action="store_true", help="Mostra os tokens sem executar")
    modo.add_argument("--python", action="store_true", help="Mostra o Python gerado sem executar")
    opcoes = argumentos.parse_args()
    try:
        codigo = opcoes.arquivo.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as erro:
        print(f"Não foi possível ler o arquivo: {erro}", file=sys.stderr)
        return 1
    try:
        if opcoes.tokens:
            for token in analisar(codigo):
                print(f"{token.linha}:{token.coluna}\t{token.tipo:<14}\t{token.valor!r}")
        elif opcoes.python:
            print(traduzir(codigo).python, end="")
        else:
            executar(codigo)
    except ErroLinguagem as erro:
        print(erro.formatar(codigo), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nExecução interrompida.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
