import ast
import re
import traceback
from dataclasses import dataclass


class ErroLinguagem(Exception):
    """Transporta o mesmo formato de erro do núcleo ao terminal ou à IDE."""
    def __init__(self, etapa, mensagem, linha=1, coluna=1):
        super().__init__(mensagem)
        self.etapa, self.mensagem = etapa, mensagem
        self.linha, self.coluna = linha, coluna

    def formatar(self, codigo):
        linhas = codigo.splitlines()
        trecho = linhas[self.linha - 1] if 0 < self.linha <= len(linhas) else ""
        return (f"Erro {self.etapa} na linha {self.linha}, coluna {self.coluna}: {self.mensagem}\n"
                f"  {trecho}\n  {' ' * (self.coluna - 1)}^")


TIPOS = {"imposto": "int", "taxa": "float", "picanha": "str", "meRespondaSoComSimOuNao": "bool"}
PALAVRAS = {
    "soberania": "MAIN", "companheiro": "VAR",
    "sim": "VERDADEIRO", "nao": "FALSO", "zeGotinha": "NULO",
    "teta": "IF", "porFavorMeAjuda": "IF", "picanhaOutraVez": "ELSE",
    "maisUmaVez": "WHILE", "aumentando": "INCREMENTO",
    "taxaBlusinhas": "%", "desconfiaQueTaCaro": ">",
    "penseNoLula": "CONTINUE", "euNaoVouEnganarOPovoMaisUmaVez": "BREAK",
    "jaViviDemais": "RETURN", "meContaCompanheiro": "INPUT", "anunciar": "OUTPUT",
    "vocesNasceramSoPraTrabalhar": "FOR", "socorroXandao": "TRY",
    "quandoTiverDesanimado": "CATCH", "euToErrando": "THROW",
    "naoTaEntregando": "ERRORINFO",
    "mensalao": "ARRAY", "petrolao": "MAP",
    "pobreNaoPrecisaEstudar": "FUNCTION", "trabalhar": "CALL",
}
PALAVRAS.update(dict.fromkeys(TIPOS, "TIPO"))
PADRAO = re.compile(
    r'(?P<ESPACO>[ \t\r]+)|(?P<LINHA>\n)|(?P<COMENTARIO>//[^\n]*)'
    r'|(?P<TEXTO>"(?:\\[^\n]|[^"\\\n])*")|(?P<NUMERO>[0-9]+(?:\.[0-9]+)?)'
    r'|(?P<ID>[A-Za-z_][A-Za-z_0-9]*)'
    r'|(?P<SIMBOLO>==|!=|<=|>=|&&|\|\||[{}\[\]():;,+\-*/%=<>!])|(?P<INVALIDO>.)'
)


@dataclass
class Token:
    """Uma unidade do código: categoria, texto original e posição de origem."""
    tipo: str
    valor: str
    linha: int
    coluna: int

def analisar(codigo):
    tokens, linha, inicio_linha = [], 1, 0
    for resultado in PADRAO.finditer(codigo):
        tipo, valor = resultado.lastgroup, resultado.group()
        coluna = resultado.start() - inicio_linha + 1
        if tipo == "LINHA":
            linha, inicio_linha = linha + 1, resultado.end()
        elif tipo == "INVALIDO":
            mensagem = 'Texto sem fechamento: use aspas duplas ("...").' if valor == '"' else f"Caractere inválido: {valor!r}."
            raise ErroLinguagem("léxico", mensagem, linha, coluna)
        elif tipo not in {"ESPACO", "COMENTARIO"}:
            if tipo == "TEXTO":
                try:
                    ast.literal_eval(valor)
                except (SyntaxError, ValueError):
                    raise ErroLinguagem("léxico", "Sequência de escape inválida no texto.", linha, coluna) from None
            if tipo == "ID":
                tipo = PALAVRAS.get(valor, "ID")
            elif tipo == "SIMBOLO":
                tipo = valor
            tokens.append(Token(tipo, valor, linha, coluna))
    tokens.append(Token("EOF", "fim do arquivo", linha, len(codigo) - inicio_linha + 1))
    return tokens


PRECEDENCIA = {"||": 1, "&&": 2, "==": 3, "!=": 3, "<": 4, ">": 4,
               "<=": 4, ">=": 4, "+": 5, "-": 5, "*": 6, "/": 6, "%": 6}
OPERADORES = {"||": "or", "&&": "and"}
LITERAIS = {"VERDADEIRO": "True", "FALSO": "False", "NULO": "None"}

NOMES_TOKENS = {tipo: repr(palavra) for palavra, tipo in PALAVRAS.items()}
NOMES_TOKENS.update({"MAIN": "o bloco 'soberania() { ... }'", "ID": "um nome de variável ou função",
                     "EOF": "o fim do arquivo", "TIPO": "um tipo de dado",
                     "NUMERO": "um número", "TEXTO": "um texto entre aspas duplas"})

@dataclass
class Traducao:
    python: str
    origens: dict


class Parser:
    """Descida recursiva: métodos leem comandos, blocos e expressões aninhados."""
    def __init__(self, tokens):
        self.tokens, self.posicao = tokens, 0
        self.linhas, self.origens = [], {}
        self.nivel, self.lacos = 0, 0
        self.funcoes = set()
        self.capturas = 0
        self.erros_ativos = []

    @property
    def atual(self):
        return self.tokens[self.posicao]

    def erro(self, mensagem, token=None):
        token = token or self.atual
        raise ErroLinguagem("sintático", mensagem, token.linha, token.coluna)

    def consumir(self, tipo=None, descricao=None):
        """Avança um token; se uma categoria foi exigida, confere antes de avançar."""
        token = self.atual
        if tipo is not None and token.tipo != tipo:
            esperado = descricao or NOMES_TOKENS.get(tipo, repr(tipo))
            encontrado = "fim do arquivo" if token.tipo == "EOF" else repr(token.valor)
            self.erro(f"Esperado {esperado}, encontrado {encontrado}.")
        self.posicao += 1
        return token

    def aceitar(self, tipo):
        """Consome apenas se combinar; caso contrário, não avança nem gera erro."""
        if self.atual.tipo == tipo:
            return self.consumir(tipo)

    def emitir(self, texto, token):
        self.linhas.append("    " * self.nivel + texto)
        self.origens[len(self.linhas)] = token

    def traduzir(self):
        inicio = None
        while self.atual.tipo != "EOF":
            if self.atual.tipo == "FUNCTION":
                self.declarar_funcao()
                continue
            if self.atual.tipo != "MAIN":
                self.erro(f"Comando {self.atual.valor!r} fora de um bloco. "
                          "Coloque os comandos dentro de 'soberania() { ... }' ou de uma função.")
            token = self.consumir("MAIN")
            if inicio is not None:
                self.erro("O programa deve ter apenas um bloco soberania().", token)
            inicio = token
            self.consumir("(")
            self.consumir(")")
            self.emitir("def _principal():", inicio)
            self.bloco()
        if inicio is None:
            self.erro("Falta o bloco obrigatório soberania().")
        self.consumir("EOF")
        self.emitir("_resultado = _principal()", inicio)
        return Traducao("\n".join(self.linhas) + "\n", self.origens)

    def declarar_funcao(self):
        token = self.consumir("FUNCTION")
        nome = self.consumir("ID", "um nome para a função")
        if nome.valor in self.funcoes:
            self.erro(f"Função {nome.valor!r} já declarada.", nome)
        self.funcoes.add(nome.valor)
        self.consumir("(")
        parametros = []
        if self.atual.tipo != ")":
            while True:
                parametro = self.consumir("ID", "um nome de parâmetro")
                if parametro.valor in parametros:
                    self.erro(f"Parâmetro {parametro.valor!r} repetido.", parametro)
                parametros.append(parametro.valor)
                if not self.aceitar(","):
                    break
        self.consumir(")")
        argumentos = ", ".join("_v_" + nome for nome in parametros)
        self.emitir(f"def _f_{nome.valor}({argumentos}):", token)
        self.bloco()

    def bloco(self, preparo=None):
        inicio = self.consumir("{")
        self.nivel += 1
        quantidade = len(self.linhas)
        if preparo:
            self.emitir(*preparo)
        while self.atual.tipo != "}":
            if self.atual.tipo == "EOF":
                self.erro("Bloco sem fechamento: esperado '}'.")
            self.comando()
        self.consumir("}")
        if len(self.linhas) == quantidade:
            self.emitir("pass", inicio)
        self.nivel -= 1

    def comando(self):
        token = self.consumir()
        if token.tipo == "VAR":
            tipo = self.aceitar("TIPO")
            nome = self.consumir("ID", "um nome para a variável").valor
            self.consumir("=")
            valor = self.expressao()
            if tipo:
                valor = f"{TIPOS[tipo.valor]}({valor})"
            codigo = f"_v_{nome} = {valor}"
        elif token.tipo == "ID":
            if self.atual.tipo == "(":
                self.erro(f"Para chamar uma função, use 'trabalhar {token.valor}(...)'.", token)
            alvo = self.indices(f"_v_{token.valor}")
            if self.aceitar("INCREMENTO"):
                codigo = f"{alvo} += 1"
            else:
                self.consumir("=")
                codigo = f"{alvo} = {self.expressao()}"
        elif token.tipo == "OUTPUT":
            codigo = f"print({', '.join(self.argumentos())})"
        elif token.tipo == "CALL":
            codigo = self.chamada()
        elif token.tipo == "THROW":
            valores = self.argumentos()
            if len(valores) != 1:
                self.erro("euToErrando exige um argumento.", token)
            codigo = f"raise _Falha({valores[0]})"
        elif token.tipo == "TRY":
            self.emitir("try:", token)
            self.bloco()
            captura = self.consumir("CATCH", "'quandoTiverDesanimado' após o bloco 'socorroXandao'")
            nome = None
            if self.aceitar("("):
                nome = self.consumir("ID", "um nome para a mensagem do erro").valor
                self.consumir(")")
            self.capturas += 1
            temporario = f"_captura_{self.capturas}"
            self.emitir(f"except _Erros as {temporario}:", captura)
            preparo = (f"_v_{nome} = _mensagem_erro({temporario})", captura) if nome else None
            self.erros_ativos.append(temporario)
            self.bloco(preparo)
            self.erros_ativos.pop()
            return
        elif token.tipo == "FOR":
            self.para(token)
            return
        elif token.tipo in {"IF", "WHILE"}:
            self.consumir("(")
            condicao = self.expressao()
            self.consumir(")")
            palavra = "if" if token.tipo == "IF" else "while"
            self.emitir(f"{palavra} {condicao}:", token)
            if token.tipo == "WHILE":
                self.lacos += 1
            self.bloco()
            if token.tipo == "WHILE":
                self.lacos -= 1
            if token.tipo == "IF" and self.aceitar("ELSE"):
                self.emitir("else:", self.tokens[self.posicao - 1])
                self.bloco()
            return
        elif token.tipo in {"BREAK", "CONTINUE"}:
            if self.lacos == 0:
                self.erro(f"{token.valor!r} só pode ser usado dentro de um laço.", token)
            codigo = "break" if token.tipo == "BREAK" else "continue"
        elif token.tipo == "RETURN":
            codigo = "return " + ("None" if self.atual.tipo == ";" else self.expressao())
        elif token.tipo == "FUNCTION":
            self.erro("Declare as funções fora de soberania() e dos outros blocos.", token)
        else:
            self.erro(f"Comando inesperado: {token.valor!r}.", token)
        self.consumir(";")
        self.emitir(codigo, token)

    def para(self, token):
        self.consumir("(")
        nome = self.consumir("ID", "um nome para a variável do laço").valor
        self.consumir(",")
        valores = [self.expressao()]
        while self.aceitar(","):
            valores.append(self.expressao())
        self.consumir(")")
        if len(valores) not in {1, 2, 3}:
            self.erro("O for exige uma coleção ou início, fim e passo opcional.", token)
        iteravel = valores[0] if len(valores) == 1 else f"range({', '.join(valores)})"
        self.emitir(f"for _v_{nome} in {iteravel}:", token)
        self.lacos += 1
        self.bloco()
        self.lacos -= 1

    def chamada(self):
        nome = self.consumir("ID", "um nome de função depois de 'trabalhar'").valor
        return f"_f_{nome}({', '.join(self.argumentos())})"

    def indices(self, valor):
        while self.aceitar("["):
            valor += f"[{self.expressao()}]"
            self.consumir("]")
        return valor

    def argumentos(self, abre="(", fecha=")"):
        self.consumir(abre)
        valores = []
        if self.atual.tipo != fecha:
            valores.append(self.expressao())
            while self.aceitar(","):
                valores.append(self.expressao())
        self.consumir(fecha)
        return valores

    def expressao(self, minimo=1):
        esquerda = self.primario()
        while PRECEDENCIA.get(self.atual.tipo, 0) >= minimo:
            operador = self.consumir()
            direita = self.expressao(PRECEDENCIA[operador.tipo] + 1)
            esquerda = f"({esquerda} {OPERADORES.get(operador.tipo, operador.tipo)} {direita})"
        return esquerda

    def primario(self):
        return self.indices(self.atomo())

    def atomo(self):
        token = self.consumir()
        if token.tipo in {"!", "-", "+"}:
            operador = "not " if token.tipo == "!" else token.tipo
            return f"({operador}{self.primario()})"
        if token.tipo == "NUMERO":
            return repr(float(token.valor) if "." in token.valor else int(token.valor))
        if token.tipo == "TEXTO":
            return repr(ast.literal_eval(token.valor))
        if token.tipo in LITERAIS:
            return LITERAIS[token.tipo]
        if token.tipo == "ID":
            if self.atual.tipo == "(":
                self.erro(f"Para chamar uma função, use 'trabalhar {token.valor}(...)'.", token)
            return f"_v_{token.valor}"
        if token.tipo == "CALL":
            return self.chamada()
        if token.tipo == "ERRORINFO":
            if self.argumentos():
                self.erro("naoTaEntregando não aceita argumentos.", token)
            if not self.erros_ativos:
                self.erro("naoTaEntregando() só pode ser usado dentro de um catch.", token)
            return f"_mensagem_erro({self.erros_ativos[-1]})"
        if token.tipo == "ARRAY":
            return "[" + ", ".join(self.argumentos("[", "]")) + "]"
        if token.tipo == "MAP":
            self.consumir("{")
            pares = []
            if self.atual.tipo != "}":
                while True:
                    chave = self.expressao()
                    self.consumir(":")
                    pares.append(f"{chave}: {self.expressao()}")
                    if not self.aceitar(","):
                        break
            self.consumir("}")
            return "{" + ", ".join(pares) + "}"
        if token.tipo == "(":
            valor = self.expressao()
            self.consumir(")")
            return f"({valor})"
        if token.tipo in {"INPUT", "TIPO"}:
            argumentos = self.argumentos()
            if token.tipo == "INPUT" and len(argumentos) > 1:
                self.erro("meContaCompanheiro aceita zero ou um argumento.", token)
            if token.tipo == "TIPO" and len(argumentos) != 1:
                self.erro(f"{token.valor} exige um argumento.", token)
            nome = "input" if token.tipo == "INPUT" else TIPOS[token.valor]
            return f"{nome}({', '.join(argumentos)})"
        if token.tipo == "IF":
            self.erro(f"{token.valor!r} inicia uma condição. Para ler dados, use 'meContaCompanheiro(...)'.", token)
        self.erro(f"Esperada uma expressão, encontrado {token.valor!r}.", token)


ARQUIVO_GERADO = "<linguagem-memistica>"


class FalhaPrograma(Exception):
    """Erro criado explicitamente pelo comando euToErrando."""


ERROS_EXECUCAO = {
    NameError: "Nome usado antes de receber um valor.",
    ZeroDivisionError: "Divisão ou resto por zero.",
    ValueError: "Valor inválido para conversão ou operação.",
    TypeError: "Tipos incompatíveis para a operação.",
    EOFError: "Não há mais dados de entrada disponíveis.",
    OverflowError: "Limite numérico excedido.",
    RecursionError: "Limite de execução excedido.",
    IndexError: "Índice fora dos limites da coleção.",
    KeyError: "Chave não encontrada no dicionário.",
    FalhaPrograma: "Erro informado pelo programa.",
}
ERROS_CAPTURAVEIS = tuple(ERROS_EXECUCAO)


def mensagem_erro(erro):
    """A mesma mensagem aparece no catch e nos erros não tratados."""
    if isinstance(erro, FalhaPrograma):
        return str(erro)
    if isinstance(erro, NameError):
        nome = getattr(erro, "name", None)
        if nome and nome.startswith("_f_"):
            return f"Função {nome.removeprefix('_f_')!r} não definida."
        identificacao = f" {nome.removeprefix('_v_')!r}" if nome else ""
        return f"Variável{identificacao} usada antes de receber um valor."
    if isinstance(erro, KeyError):
        return f"Chave {erro.args[0]!r} não encontrada no dicionário."
    if isinstance(erro, ValueError) and "range() arg 3" in str(erro):
        return "O passo do for não pode ser zero."
    if isinstance(erro, TypeError) and "_f_" in str(erro):
        return "Quantidade de argumentos ou tipos incompatíveis na chamada de função."
    for tipo, mensagem in ERROS_EXECUCAO.items():
        if isinstance(erro, tipo):
            return mensagem
    return str(erro)


def traduzir(codigo):
    return Parser(analisar(codigo)).traduzir()


def executar(codigo, entrada=input, saida=print):
    traducao = traduzir(codigo)
    ambiente = {"__builtins__": {}, "input": entrada, "print": saida,
                "int": int, "float": float, "str": str, "bool": bool, "range": range,
                "_Falha": FalhaPrograma, "_Erros": ERROS_CAPTURAVEIS,
                "_mensagem_erro": mensagem_erro}
    try:
        exec(compile(traducao.python, ARQUIVO_GERADO, "exec"), ambiente)
    except ERROS_CAPTURAVEIS as erro:
        mensagem = mensagem_erro(erro)
        for quadro in traceback.extract_tb(erro.__traceback__):
            if quadro.filename == ARQUIVO_GERADO:
                origem = traducao.origens[quadro.lineno]
        raise ErroLinguagem("de execução", mensagem, origem.linha, origem.coluna) from None
    return ambiente.get("_resultado")
