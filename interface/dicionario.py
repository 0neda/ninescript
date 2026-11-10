"""Consulta do vocabulário do BASE.txt, sem alterar o código do editor."""

import tkinter as tk
import unicodedata
from pathlib import Path
from tkinter import ttk

from linguagem import PALAVRAS


AJUDA = {
    "soberania": ("Bloco principal e obrigatório do programa.", 'soberania() {\n    anunciar("Ola!");\n}'),
    "companheiro": ("Cria uma variável. O tipo antes do nome é opcional.", 'companheiro nome = "Ana";\ncompanheiro imposto idade = 21;'),
    "imposto": ("Converte um valor para inteiro. Na declaração, converte apenas o valor inicial.", 'companheiro imposto idade = imposto(meContaCompanheiro("Idade: "));'),
    "taxa": ("Converte um valor para número decimal. Use ponto como separador.", 'companheiro taxa preco = 12.50;'),
    "picanha": ("Converte um valor para texto. Textos literais usam aspas duplas.", 'companheiro picanha nome = "Ana";\nanunciar(picanha(123));'),
    "meRespondaSoComSimOuNao": ("Converte um valor para booleano pelas regras de Python: zero, texto vazio e nulo são falsos. Um texto não vazio, inclusive \"nao\", é verdadeiro.", 'companheiro meRespondaSoComSimOuNao ativo = sim;'),
    "sim": ("Valor booleano verdadeiro.", 'porFavorMeAjuda (sim) {\n    anunciar("Verdadeiro");\n}'),
    "nao": ("Valor booleano falso.", 'companheiro ativo = nao;'),
    "zeGotinha": ("Representa ausência de valor (None em Python).", 'companheiro valor = zeGotinha;'),
    "aumentando": ("Soma 1 ao valor de uma variável. Usado como comando, depois do nome.", 'companheiro contador = 0;\ncontador aumentando;'),
    "taxaBlusinhas": ("Calcula o resto da divisão, como o operador %.", 'anunciar(7 taxaBlusinhas 2); // imprime 1'),
    "desconfiaQueTaCaro": ("Compara se o valor à esquerda é maior que o da direita.", 'porFavorMeAjuda (10 desconfiaQueTaCaro 5) {\n    anunciar("Ta caro!");\n}'),
    "porFavorMeAjuda": ("Executa um bloco se a condição for verdadeira.", 'porFavorMeAjuda (2 > 1) {\n    anunciar("Sim");\n}'),
    "picanhaOutraVez": ("Bloco alternativo de uma condição; deve vir depois de um if.", 'porFavorMeAjuda (nao) {\n    anunciar("Sim");\n} picanhaOutraVez {\n    anunciar("Nao");\n}'),
    "maisUmaVez": ("Repete o bloco enquanto a condição for verdadeira.", 'companheiro i = 0;\nmaisUmaVez (i < 3) {\n    anunciar(i);\n    i aumentando;\n}'),
    "penseNoLula": ("Pula para a próxima repetição. Só pode ser usado dentro de um laço.", 'companheiro i = 0;\nmaisUmaVez (i < 3) {\n    i aumentando;\n    porFavorMeAjuda (i == 2) {\n        penseNoLula;\n    }\n    anunciar(i);\n}'),
    "euNaoVouEnganarOPovoMaisUmaVez": ("Encerra o laço atual. Só pode ser usado dentro de um laço.", 'maisUmaVez (sim) {\n    anunciar("Uma vez");\n    euNaoVouEnganarOPovoMaisUmaVez;\n}'),
    "jaViviDemais": ("Encerra a função atual e devolve um valor. Em soberania, devolve ao executor. Não é o código de saída do terminal.", 'jaViviDemais 0;'),
    "meContaCompanheiro": ("Pede uma entrada e retorna texto. Na IDE, digite no campo Entrada e pressione Enter ou Enviar. Para números, use imposto(...) ou taxa(...).", 'companheiro nome = meContaCompanheiro("Nome: ");\nanunciar("Ola,", nome);'),
    "anunciar": ("Mostra valores no resultado. Acrescentado ao projeto porque o BASE.txt não define saída.", 'anunciar("Ola!", 2 + 3);'),
    "vocesNasceramSoPraTrabalhar": ("Percorre uma coleção ou um intervalo de inteiros. O fim do intervalo é exclusivo; o passo é opcional e não pode ser zero. Em dicionários, percorre as chaves.", 'vocesNasceramSoPraTrabalhar(i, 0, 3) {\n    anunciar(i);\n}\nvocesNasceramSoPraTrabalhar(item, mensalao[10, 20]) {\n    anunciar(item);\n}'),
    "socorroXandao": ("Executa um bloco e permite tratar erros de execução no catch obrigatório. Erros de sintaxe são detectados antes de executar e não podem ser capturados.", 'socorroXandao {\n    anunciar(1 / 0);\n} quandoTiverDesanimado (erro) {\n    anunciar(erro);\n}'),
    "quandoTiverDesanimado": ("Vem depois de socorroXandao. Pode receber a mensagem em (erro) ou omitir o nome e consultar naoTaEntregando(). Não executa se o try terminar sem erro.", 'socorroXandao {\n    euToErrando("Falha proposital.");\n} quandoTiverDesanimado {\n    anunciar(naoTaEntregando());\n}'),
    "naoTaEntregando": ("Retorna a mensagem do erro atual como texto, sem argumentos. Só funciona dentro de um catch, inclusive nos blocos aninhados. Em catches aninhados, consulta o erro mais interno e volta ao externo ao sair.", 'socorroXandao {\n    anunciar(1 / 0);\n} quandoTiverDesanimado {\n    anunciar("Erro:", naoTaEntregando());\n}'),
    "euToErrando": ("Lança um erro com um valor ou mensagem. Procura o catch mais próximo; sem catch, encerra com a posição original do erro.", 'euToErrando("Valor invalido.");'),
    "mensalao": ("Cria um array (lista Python). Índices começam em zero; permite leitura, alteração e coleções aninhadas. O índice -1 acessa o último item.", 'companheiro notas = mensalao[7, 8, 9];\nnotas[0] = 10;\nanunciar(notas[0]);'),
    "petrolao": ("Cria um dicionário de pares chave: valor. Permite ler, alterar e acrescentar chaves; uma chave inexistente gera erro capturável.", 'companheiro pessoa = petrolao{"nome": "Ana", "idade": 21};\npessoa["idade"] aumentando;\nanunciar(pessoa["nome"], pessoa["idade"]);'),
    "pobreNaoPrecisaEstudar": ("Declara uma função com parâmetros, fora de soberania e de outros blocos. Pode vir antes ou depois de soberania. Suporta retorno, chamadas aninhadas e recursão.", 'pobreNaoPrecisaEstudar soma(a, b) {\n    jaViviDemais a + b;\n}\nsoberania() {\n    anunciar(trabalhar soma(2, 3));\n}'),
    "trabalhar": ("Chama uma função declarada pelo programa. Pode ser usado como comando ou dentro de uma expressão; recebe argumentos por posição.", 'pobreNaoPrecisaEstudar dobro(valor) {\n    jaViviDemais valor * 2;\n}\nsoberania() {\n    companheiro resultado = trabalhar dobro(5);\n    anunciar(resultado);\n}'),
}


def carregar_verbetes(arquivo):
    verbetes = []
    for linha in Path(arquivo).read_text(encoding="utf-8-sig").splitlines():
        if linha.startswith("Referências usadas:"):
            break
        if "=" not in linha:
            continue
        palavra, equivalente = (parte.strip() for parte in linha.split("=", 1))
        if palavra not in PALAVRAS:
            continue
        descricao, exemplo = AJUDA[palavra]
        verbetes.append({"palavra": palavra, "equivalente": equivalente,
                         "descricao": descricao, "exemplo": exemplo})
    descricao, exemplo = AJUDA["anunciar"]
    verbetes.append({"palavra": "anunciar", "equivalente": "print / saída",
                     "descricao": descricao, "exemplo": exemplo})
    return sorted(verbetes, key=lambda item: item["palavra"].lower())


def normalizar(texto):
    return "".join(letra for letra in unicodedata.normalize("NFD", texto.casefold())
                   if not unicodedata.combining(letra))


class Dicionario:
    def __init__(self, pai, arquivo):
        self.verbetes = carregar_verbetes(arquivo)
        self.janela = tk.Toplevel(pai)
        self.janela.title("Dicionário — Ninescript")
        self.janela.geometry("940x660")
        self.janela.minsize(700, 520)
        self.janela.transient(pai)
        self.exemplo_atual = ""
        quadro = ttk.Frame(self.janela, padding=16)
        quadro.pack(fill="both", expand=True)
        ttk.Label(quadro, text="Dicionário da linguagem", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(quadro, text="Consulte o significado e a sintaxe dos comandos do BASE.txt.").pack(anchor="w", pady=(3, 12))
        filtros = ttk.Frame(quadro)
        filtros.pack(fill="x", pady=(0, 10))
        ttk.Label(filtros, text="Buscar:").pack(side="left", padx=(0, 8))
        self.busca = tk.StringVar()
        self.campo_busca = ttk.Entry(filtros, textvariable=self.busca)
        self.campo_busca.pack(side="left", fill="x", expand=True)

        rodape = ttk.Frame(quadro)
        rodape.pack(side="bottom", fill="x", pady=(10, 0))
        self.contagem = ttk.Label(rodape)
        self.contagem.pack(side="left")
        ttk.Button(rodape, text="Fechar", command=self.janela.destroy).pack(side="right")
        self.copiar = ttk.Button(rodape, text="Copiar programa", command=self.copiar_exemplo)
        self.copiar.pack(side="right", padx=8)
        detalhes = ttk.LabelFrame(quadro, text="Significado e exemplo de uso", padding=8)
        detalhes.pack(side="bottom", fill="x", pady=(10, 0))
        self.detalhes = tk.Text(detalhes, height=10, wrap="word", state="disabled",
                                relief="flat", font=("Consolas", 10), padx=6, pady=6)
        rolagem = ttk.Scrollbar(detalhes, command=self.detalhes.yview)
        rolagem.pack(side="right", fill="y")
        self.detalhes.pack(fill="both", expand=True)
        self.detalhes.configure(yscrollcommand=rolagem.set)
        lista = ttk.Frame(quadro)
        lista.pack(fill="both", expand=True)
        self.tabela = ttk.Treeview(lista, columns=("palavra", "equivalente"), show="headings", selectmode="browse")
        for coluna, titulo, largura in (("palavra", "Comando", 420), ("equivalente", "Equivalente", 280)):
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(coluna, width=largura, minwidth=90)
        barra = ttk.Scrollbar(lista, command=self.tabela.yview)
        barra.pack(side="right", fill="y")
        self.tabela.pack(fill="both", expand=True)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.bind("<<TreeviewSelect>>", lambda evento: self.selecionar())
        self.busca.trace_add("write", lambda *args: self.filtrar())
        self.janela.bind("<Escape>", lambda evento: self.janela.destroy())
        self.filtrar()
        self.campo_busca.focus_set()

    def filtrar(self):
        consulta = normalizar(self.busca.get().strip())
        self.tabela.delete(*self.tabela.get_children())
        for indice, item in enumerate(self.verbetes):
            texto = " ".join(item[chave] for chave in ("palavra", "equivalente", "descricao"))
            if consulta in normalizar(texto):
                self.tabela.insert("", "end", iid=str(indice),
                                    values=(item["palavra"], item["equivalente"]))
        resultados = self.tabela.get_children()
        self.contagem.configure(text=f"{len(resultados)} de {len(self.verbetes)} comandos")
        if resultados:
            self.tabela.selection_set(resultados[0])
        self.selecionar()

    def selecionar(self):
        selecao = self.tabela.selection()
        self.exemplo_atual = ""
        texto = "Nenhum comando encontrado. Altere a busca ou o filtro."
        if selecao:
            item = self.verbetes[int(selecao[0])]
            texto = f"{item['palavra']} → {item['equivalente']}\n\n{item['descricao']}"
            self.exemplo_atual = item["exemplo"]
            if self.exemplo_atual:
                completo = item["palavra"] in {"soberania", "pobreNaoPrecisaEstudar", "trabalhar"}
                if not completo:
                    corpo = "\n".join("    " + linha for linha in self.exemplo_atual.splitlines())
                    self.exemplo_atual = "soberania() {\n" + corpo + "\n}"
                texto += f"\n\nPrograma completo:\n{self.exemplo_atual}"
        self.detalhes.configure(state="normal")
        self.detalhes.delete("1.0", "end")
        self.detalhes.insert("1.0", texto)
        self.detalhes.configure(state="disabled")
        self.copiar.configure(state="normal" if self.exemplo_atual else "disabled")

    def copiar_exemplo(self):
        if self.exemplo_atual:
            self.janela.clipboard_clear()
            self.janela.clipboard_append(self.exemplo_atual)
