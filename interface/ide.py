"""IDE desktop didática. Inicie com: python ide.py"""

import multiprocessing as mp
import math
import tkinter as tk
from pathlib import Path
from queue import Empty
from tkinter import filedialog, messagebox, ttk

from .console import Console
from .depurador import executar_processo
from .dicionario import Dicionario
from linguagem import ErroLinguagem, PADRAO, PALAVRAS, analisar, traduzir


PASTA = Path(__file__).resolve().parent.parent
RECURSOS = Path(__file__).resolve().parent / "assets"
VERMELHO = "#c52232"
FUNDO = "#faf4f4"
TEXTO = "#321c23"
MODELO = 'soberania() {\n    anunciar("Ola, companheiro!");\n}\n'


class IDE:
    def __init__(self, janela):
        self.janela = janela
        self.arquivo = None
        self.alterado = False
        self.pontos = set()
        self.processo = None
        self.comandos = None
        self.eventos = None
        self.estado = "pronto"
        self.agendamento = None
        self.fechando = False
        self.atualizacao = None
        self.dicionario = None
        self.contexto = mp.get_context("spawn")
        janela.title("Ninescript")
        janela.geometry("1180x800")
        janela.minsize(850, 600)
        janela.configure(bg=FUNDO)
        janela.protocol("WM_DELETE_WINDOW", self.fechar)
        self.criar_interface()
        self.atalhos()
        self.carregar_inicial()
        self.agendamento = janela.after(60, self.receber_eventos)

    def criar_interface(self):
        self.menu = tk.Menu(self.janela, tearoff=False)
        self.menu.add_command(label="Dicionário", command=self.abrir_dicionario, accelerator="F1")
        self.janela.configure(menu=self.menu)
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TFrame", background=FUNDO)
        estilo.configure("TLabel", background=FUNDO, foreground=TEXTO, font=("Segoe UI", 10))
        estilo.configure("TButton", padding=(10, 6), font=("Segoe UI", 10))
        estilo.configure("Principal.TButton", background=VERMELHO, foreground="white")
        estilo.map("Principal.TButton", background=[("active", "#a51b29"), ("disabled", "#cba6ab")])
        estilo.configure("TNotebook.Tab", padding=(14, 7), font=("Segoe UI", 10))
        estilo.map("TNotebook.Tab", background=[("selected", "#fbe2e5")], foreground=[("selected", "#991b29")])
        estilo.configure("Treeview", rowheight=25, font=("Consolas", 10))
        estilo.map("Treeview", background=[("selected", VERMELHO)], foreground=[("selected", "white")])
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        topo = tk.Frame(self.janela, bg=VERMELHO, padx=18, pady=10)
        topo.pack(fill="x")
        self.emblema = tk.Canvas(topo, width=62, height=58, bg=VERMELHO, highlightthickness=0)
        self.emblema.pack(side="left", padx=(0, 12))
        estrela = []
        for ponta in range(10):
            angulo = -math.pi / 2 + ponta * math.pi / 5
            raio = 28 if ponta % 2 == 0 else 13
            estrela.extend((31 + math.cos(angulo) * raio, 29 + math.sin(angulo) * raio))
        self.emblema.create_polygon(estrela, fill="white", outline="white")
        self.emblema.create_text(31, 31, text="13", fill=VERMELHO, font=("Segoe UI", 11, "bold"))
        tk.Label(topo, text="NINESCRIPT", bg=VERMELHO, fg="white", font=("Segoe UI", 20, "bold")).pack(side="left")
        tk.Label(topo, text="EDITOR  /  EXECUÇÃO  /  DEPURAÇÃO", bg=VERMELHO, fg="#ffe3e6",
                 font=("Segoe UI", 9)).pack(side="left", padx=22)

        barra = ttk.Frame(self.janela, padding=(12, 8))
        barra.pack(fill="x")
        for titulo, acao in (("Novo", self.novo), ("Abrir…", self.abrir), ("Salvar", self.salvar)):
            ttk.Button(barra, text=titulo, command=acao).pack(side="left", padx=3)
        ttk.Separator(barra, orient="vertical").pack(side="left", fill="y", padx=10)
        self.botoes = {}
        for nome, titulo, acao in (
            ("executar", "Executar · F5", self.executar),
            ("depurar", "Depurar · F6", self.depurar),
            ("passo", "Próximo · F10", self.passo),
            ("pausar", "Pausar", self.pausar),
            ("parar", "Parar · Shift+F5", self.parar),
        ):
            botao = ttk.Button(barra, text=titulo, command=acao,
                               style="Principal.TButton" if nome == "executar" else "TButton")
            botao.pack(side="left", padx=3)
            self.botoes[nome] = botao

        corpo = ttk.Panedwindow(self.janela, orient="horizontal")
        corpo.pack(fill="both", expand=True, padx=12)
        lateral = ttk.Frame(corpo, padding=(8, 12))
        corpo.add(lateral, weight=0)
        ttk.Label(lateral, text="EXEMPLOS", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))
        self.exemplos = sorted((PASTA / "exemplos").glob("*.nine"))
        self.lista = tk.Listbox(lateral, width=23, height=12, bg="white", fg=TEXTO,
                               relief="flat", font=("Segoe UI", 10), activestyle="none",
                               selectbackground=VERMELHO, selectforeground="white", exportselection=False)
        self.lista.pack(fill="x")
        for exemplo in self.exemplos:
            self.lista.insert("end", exemplo.name)
        self.lista.bind("<Double-Button-1>", lambda evento: self.abrir_exemplo())
        self.lista.bind("<Return>", lambda evento: self.abrir_exemplo())
        ttk.Button(lateral, text="Carregar exemplo", command=self.abrir_exemplo).pack(fill="x", pady=8)
        ttk.Separator(lateral).pack(fill="x", pady=14)
        ttk.Label(lateral, text="COMO DEPURAR", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(lateral, text="1. Clique em Depurar.\n2. Use Próximo (F10).\n3. Veja as Variáveis.\n\nClique no número da linha\npara marcar uma parada.\n\nAmarelo: próxima linha.\nVermelho: linha com erro.\n● Ponto de parada.",
                  justify="left", wraplength=185).pack(anchor="w", pady=9)

        principal = ttk.Panedwindow(corpo, orient="vertical")
        corpo.add(principal, weight=1)
        area_editor = ttk.Frame(principal)
        principal.add(area_editor, weight=3)
        self.rotulo_arquivo = ttk.Label(area_editor, text="Novo arquivo", padding=(8, 6))
        self.rotulo_arquivo.pack(fill="x")
        caixa = tk.Frame(area_editor, bg="white")
        caixa.pack(fill="both", expand=True)
        self.numeros = tk.Canvas(caixa, width=64, bg="#f2e7e9", highlightthickness=0)
        self.numeros.pack(side="left", fill="y")
        self.editor = tk.Text(caixa, wrap="none", undo=True, font=("Consolas", 12),
                              bg="white", fg=TEXTO, insertbackground=VERMELHO,
                              relief="flat", padx=10, pady=8, tabs=(32,))
        vertical = ttk.Scrollbar(caixa, orient="vertical", command=self.editor.yview)
        vertical.pack(side="right", fill="y")
        self.editor.pack(fill="both", expand=True)
        self.editor.configure(yscrollcommand=lambda primeiro, ultimo: self.rolar(vertical, primeiro, ultimo))
        horizontal = ttk.Scrollbar(area_editor, orient="horizontal", command=self.editor.xview)
        horizontal.pack(fill="x")
        self.editor.configure(xscrollcommand=horizontal.set)
        self.editor.tag_configure("palavra", foreground="#6d28d9")
        self.editor.tag_configure("texto", foreground="#08785d")
        self.editor.tag_configure("numero", foreground="#b45309")
        self.editor.tag_configure("comentario", foreground="#7b8799")
        self.editor.tag_configure("erro", background="#ffe0df")
        self.editor.tag_configure("atual", background="#fff0b3")
        self.editor.bind("<<Modified>>", self.modificado)
        self.editor.bind("<Configure>", lambda evento: self.desenhar_numeros())
        self.editor.bind("<KeyRelease>", lambda evento: self.atualizar_cursor())
        self.editor.bind("<ButtonRelease-1>", lambda evento: self.atualizar_cursor())
        self.editor.bind("<Tab>", self.inserir_tab)
        self.numeros.bind("<Button-1>", self.marcar_ponto)

        inferior = ttk.Frame(principal)
        principal.add(inferior, weight=2)
        self.abas = ttk.Notebook(inferior)
        self.abas.pack(fill="both", expand=True, pady=(8, 0))
        self.aba_saida = ttk.Frame(self.abas)
        self.abas.add(self.aba_saida, text="Resultado")
        entrada = ttk.Frame(self.aba_saida, padding=6)
        entrada.pack(side="bottom", fill="x")
        ttk.Label(entrada, text="Entrada:").pack(side="left", padx=(0, 7))
        self.campo_entrada = ttk.Entry(entrada, state="disabled", font=("Consolas", 11))
        self.campo_entrada.pack(side="left", fill="x", expand=True)
        self.campo_entrada.bind("<Return>", lambda evento: self.enviar_entrada())
        self.botao_entrada = ttk.Button(entrada, text="Enviar", command=self.enviar_entrada, state="disabled")
        self.botao_entrada.pack(side="left", padx=(7, 0))
        ajustes_console = ttk.Frame(self.aba_saida, padding=(8, 3))
        ajustes_console.pack(side="bottom", fill="x")
        quadro_console = ttk.Frame(self.aba_saida)
        quadro_console.pack(fill="both", expand=True)
        self.console = Console(quadro_console, RECURSOS / "topo.png")
        ttk.Label(ajustes_console, text="Opacidade do fundo:").pack(side="left", padx=(0, 8))
        self.opacidade_fundo = tk.DoubleVar(value=self.console.opacidade * 100)
        self.rotulo_opacidade = ttk.Label(ajustes_console, text=f"{self.console.opacidade:.0%}", width=5)
        self.controle_opacidade = ttk.Scale(ajustes_console, from_=0, to=100,
            variable=self.opacidade_fundo, command=self.atualizar_opacidade_fundo, length=180)
        self.controle_opacidade.pack(side="left", padx=(0, 8))
        self.rotulo_opacidade.pack(side="left")
        barra_console = ttk.Scrollbar(quadro_console, command=self.console.yview)
        barra_console.pack(side="right", fill="y")
        barra_console_x = ttk.Scrollbar(quadro_console, orient="horizontal", command=self.console.xview)
        barra_console_x.pack(side="bottom", fill="x")
        self.console.pack(fill="both", expand=True)
        self.console.configure(yscrollcommand=barra_console.set, xscrollcommand=barra_console_x.set)

        aba_tokens = ttk.Frame(self.abas)
        self.abas.add(aba_tokens, text="Tokens")
        self.tokens = self.tabela(aba_tokens, ("posição", "tipo", "valor"), (90, 140, 340))
        aba_python = ttk.Frame(self.abas)
        self.abas.add(aba_python, text="Python gerado")
        self.python = self.texto_leitura(aba_python)
        aba_variaveis = ttk.Frame(self.abas)
        self.abas.add(aba_variaveis, text="Variáveis")
        ttk.Label(aba_variaveis, text="Valores antes da linha destacada; atualizados quando a execução pausa.",
                  padding=6).pack(fill="x")
        self.variaveis = self.tabela(aba_variaveis, ("nome", "tipo", "valor"), (170, 100, 340))
        self.abas.bind("<<NotebookTabChanged>>", lambda evento: self.atualizar_analise())
        rodape = ttk.Frame(self.janela, padding=(14, 7))
        rodape.pack(fill="x")
        self.status = ttk.Label(rodape, text="Pronto")
        self.status.pack(side="left")
        self.cursor = ttk.Label(rodape, text="Linha 1, coluna 1")
        self.cursor.pack(side="right")
        self.atualizar_botoes()

    def texto_leitura(self, pai, **cores):
        quadro = ttk.Frame(pai)
        quadro.pack(fill="both", expand=True)
        texto = tk.Text(quadro, wrap="none", state="disabled", relief="flat",
                        font=("Consolas", 11), padx=10, pady=8,
                        bg=cores.get("bg", "white"), fg=cores.get("fg", TEXTO))
        barra = ttk.Scrollbar(quadro, command=texto.yview)
        barra.pack(side="right", fill="y")
        texto.pack(fill="both", expand=True)
        texto.configure(yscrollcommand=barra.set)
        barra_x = ttk.Scrollbar(quadro, orient="horizontal", command=texto.xview)
        barra_x.pack(fill="x")
        texto.configure(xscrollcommand=barra_x.set)
        return texto

    def atualizar_opacidade_fundo(self, porcentagem):
        valor = round(float(porcentagem))
        self.console.opacidade = valor / 100
        self.rotulo_opacidade.configure(text=f"{valor}%")

    def tabela(self, pai, colunas, larguras):
        quadro = ttk.Frame(pai)
        quadro.pack(fill="both", expand=True)
        tabela = ttk.Treeview(quadro, columns=colunas, show="headings")
        for coluna, largura in zip(colunas, larguras):
            tabela.heading(coluna, text=coluna.capitalize())
            tabela.column(coluna, width=largura, minwidth=60)
        barra = ttk.Scrollbar(quadro, command=tabela.yview)
        barra.pack(side="right", fill="y")
        tabela.pack(fill="both", expand=True)
        tabela.configure(yscrollcommand=barra.set)
        return tabela

    def atalhos(self):
        for tecla, acao in (("<F1>", self.abrir_dicionario), ("<Control-n>", self.novo), ("<Control-o>", self.abrir),
                            ("<Control-s>", self.salvar), ("<F5>", self.executar),
                            ("<F6>", self.depurar), ("<F10>", self.passo),
                            ("<Shift-F5>", self.parar)):
            self.janela.bind(tecla, lambda evento, funcao=acao: self.atalho(funcao))

    def abrir_dicionario(self):
        if self.dicionario is not None and self.dicionario.janela.winfo_exists():
            self.dicionario.janela.deiconify()
            self.dicionario.janela.lift()
            self.dicionario.campo_busca.focus_set()
            return
        try:
            self.dicionario = Dicionario(self.janela, PASTA / "BASE.txt")
        except (OSError, UnicodeError) as erro:
            messagebox.showerror("Não foi possível abrir o dicionário", str(erro))

    def atalho(self, funcao):
        funcao()
        return "break"

    def inserir_tab(self, evento):
        if self.estado == "pronto":
            self.editor.insert("insert", "    ")
        return "break"

    def codigo(self):
        return self.editor.get("1.0", "end-1c")

    def escrever(self, widget, texto):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", texto)
        widget.configure(state="disabled")

    def saida(self, texto):
        self.console.configure(state="normal")
        self.console.insert("end", texto)
        linhas = int(self.console.index("end-1c").split(".")[0])
        if linhas > 2000:
            self.console.delete("1.0", f"{linhas - 2000}.0")
        self.console.see("end")
        self.console.configure(state="disabled")

    def carregar_inicial(self):
        arquivo = PASTA / "exemplos" / "ola.nine"
        if arquivo.exists():
            self.carregar(arquivo)
        else:
            self.definir_codigo(MODELO)

    def definir_codigo(self, codigo, arquivo=None):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", codigo)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.arquivo = arquivo
        self.alterado = False
        self.pontos.clear()
        self.limpar_marcas()
        self.escrever(self.console, "")
        self.variaveis.delete(*self.variaveis.get_children())
        self.colorir()
        self.atualizar_titulo()
        self.atualizar_analise()
        self.editor.focus_set()

    def pode_trocar(self):
        if self.estado != "pronto":
            messagebox.showinfo("Execução em andamento", "Pare a execução antes de trocar de arquivo.")
            return False
        if self.alterado:
            resposta = messagebox.askyesnocancel("Salvar alterações?", "Deseja salvar o código antes de continuar?")
            if resposta is None:
                return False
            if resposta and not self.salvar():
                return False
        return True

    def novo(self):
        if self.pode_trocar():
            self.definir_codigo(MODELO)

    def abrir(self):
        if not self.pode_trocar():
            return
        nome = filedialog.askopenfilename(initialdir=PASTA, filetypes=[("Código Ninescript", "*.nine"), ("Todos", "*.*")])
        if nome:
            self.carregar(Path(nome))

    def abrir_exemplo(self):
        selecao = self.lista.curselection()
        if selecao and self.pode_trocar():
            self.carregar(self.exemplos[selecao[0]])

    def carregar(self, arquivo):
        try:
            codigo = arquivo.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as erro:
            messagebox.showerror("Não foi possível abrir", str(erro))
            return
        self.definir_codigo(codigo, arquivo)

    def salvar(self):
        nome = self.arquivo
        if nome is None:
            selecionado = filedialog.asksaveasfilename(initialdir=PASTA, defaultextension=".nine",
                                                      filetypes=[("Código Ninescript", "*.nine")])
            if not selecionado:
                return False
            nome = Path(selecionado)
        try:
            nome.write_text(self.codigo(), encoding="utf-8")
        except OSError as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return False
        self.arquivo = nome
        self.alterado = False
        self.atualizar_titulo()
        return True

    def atualizar_titulo(self):
        nome = self.arquivo.name if self.arquivo else "Novo arquivo.nine"
        marca = " *" if self.alterado else ""
        self.rotulo_arquivo.configure(text=nome + marca)
        self.janela.title(f"{nome}{marca} — Ninescript")

    def modificado(self, evento=None):
        if not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        self.alterado = True
        self.atualizar_titulo()
        self.limpar_marcas()
        self.pontos.clear()
        if self.atualizacao:
            self.janela.after_cancel(self.atualizacao)
        self.atualizacao = self.janela.after(180, self.colorir)

    def colorir(self):
        self.atualizacao = None
        for tag in ("palavra", "texto", "numero", "comentario"):
            self.editor.tag_remove(tag, "1.0", "end")
        for resultado in PADRAO.finditer(self.codigo()):
            tipo = resultado.lastgroup
            tag = {"TEXTO": "texto", "NUMERO": "numero", "COMENTARIO": "comentario"}.get(tipo)
            if tipo == "ID" and resultado.group() in PALAVRAS:
                tag = "palavra"
            if tag:
                self.editor.tag_add(tag, f"1.0+{resultado.start()}c", f"1.0+{resultado.end()}c")
        self.desenhar_numeros()
        self.atualizar_cursor()

    def rolar(self, barra, primeiro, ultimo):
        barra.set(primeiro, ultimo)
        self.desenhar_numeros()

    def desenhar_numeros(self):
        self.numeros.delete("all")
        indice = self.editor.index("@0,0")
        while True:
            dados = self.editor.dlineinfo(indice)
            if dados is None:
                break
            linha = int(indice.split(".")[0])
            y = dados[1]
            if linha in self.pontos:
                self.numeros.create_oval(7, y + 4, 17, y + 14, fill="#db3c46", outline="")
            self.numeros.create_text(54, y, text=str(linha), anchor="ne",
                                     fill="#66758c", font=("Consolas", 12))
            indice = self.editor.index(f"{indice}+1line")

    def marcar_ponto(self, evento):
        linha = int(self.editor.index(f"@0,{evento.y}").split(".")[0])
        if linha in self.pontos:
            self.pontos.remove(linha)
        else:
            self.pontos.add(linha)
        if self.processo:
            self.comandos.put(("pontos", sorted(self.pontos)))
        self.desenhar_numeros()

    def atualizar_cursor(self):
        linha, coluna = self.editor.index("insert").split(".")
        self.cursor.configure(text=f"Linha {linha}, coluna {int(coluna) + 1}")

    def limpar_marcas(self):
        self.editor.tag_remove("erro", "1.0", "end")
        self.editor.tag_remove("atual", "1.0", "end")

    def destacar(self, linha, coluna, tag):
        self.limpar_marcas()
        self.editor.tag_add(tag, f"{linha}.0", f"{linha}.end+1c")
        self.editor.mark_set("insert", f"{linha}.{coluna - 1}")
        self.editor.see(f"{linha}.0")
        self.atualizar_cursor()

    def atualizar_analise(self):
        aba = self.abas.index(self.abas.select())
        if aba not in (1, 2):
            return
        try:
            if aba == 1:
                self.tokens.delete(*self.tokens.get_children())
                for token in analisar(self.codigo()):
                    self.tokens.insert("", "end", values=(f"{token.linha}:{token.coluna}", token.tipo, repr(token.valor)))
            else:
                self.escrever(self.python, traduzir(self.codigo()).python)
        except ErroLinguagem as erro:
            if aba == 1:
                self.tokens.insert("", "end", values=(f"{erro.linha}:{erro.coluna}", "ERRO", erro.mensagem))
            else:
                self.escrever(self.python, erro.formatar(self.codigo()))
            self.destacar(erro.linha, erro.coluna, "erro")

    def executar(self):
        if self.estado == "pausado":
            self.comandos.put(("continuar", None))
            self.definir_estado("executando", "Executando…")
            self.limpar_marcas()
        elif self.estado == "pronto":
            self.iniciar(False)

    def depurar(self):
        if self.estado == "pronto":
            self.iniciar(True)

    def passo(self):
        if self.estado == "pausado":
            self.comandos.put(("passo", None))
            self.definir_estado("executando", "Executando próximo comando…")
        elif self.estado == "pronto":
            self.iniciar(True)

    def iniciar(self, depurar):
        self.limpar_marcas()
        self.escrever(self.console, "")
        self.variaveis.delete(*self.variaveis.get_children())
        self.abas.select(0)
        self.comandos = self.contexto.Queue()
        self.eventos = self.contexto.Queue(maxsize=300)
        self.processo = self.contexto.Process(target=executar_processo,
            args=(self.codigo(), depurar, sorted(self.pontos), self.comandos, self.eventos), daemon=True)
        try:
            self.processo.start()
        except (OSError, RuntimeError) as erro:
            self.saida(f"Não foi possível iniciar a execução: {erro}\n")
            self.finalizar()
            return
        self.definir_estado("executando", "Iniciando depuração…" if depurar else "Executando…")

    def pausar(self):
        if self.estado == "executando":
            self.comandos.put(("pausar", None))
            self.status.configure(text="Pausa solicitada; aguardando o próximo comando…")

    def enviar_entrada(self):
        if self.estado != "entrada":
            return
        self.comandos.put(("entrada", self.campo_entrada.get()))
        self.campo_entrada.delete(0, "end")
        self.definir_estado("executando", "Executando…")

    def definir_estado(self, estado, mensagem):
        self.estado = estado
        self.status.configure(text=mensagem)
        self.editor.configure(state="normal" if estado == "pronto" else "disabled")
        self.campo_entrada.configure(state="normal" if estado == "entrada" else "disabled")
        self.botao_entrada.configure(state="normal" if estado == "entrada" else "disabled")
        self.atualizar_botoes()

    def atualizar_botoes(self):
        for nome, botao in self.botoes.items():
            ativo = {"executar": self.estado in {"pronto", "pausado"},
                     "depurar": self.estado == "pronto", "passo": self.estado in {"pronto", "pausado"},
                     "pausar": self.estado == "executando", "parar": self.estado != "pronto"}[nome]
            botao.configure(state="normal" if ativo else "disabled")
        self.botoes["executar"].configure(text="Continuar · F5" if self.estado == "pausado" else "Executar · F5")

    def receber_eventos(self):
        self.agendamento = None
        if self.eventos is not None:
            for _ in range(100):
                try:
                    evento, valor = self.eventos.get_nowait()
                except Empty:
                    break
                self.tratar_evento(evento, valor)
                if self.eventos is None:
                    break
            if self.processo is not None and self.processo.exitcode is not None:
                try:
                    evento, valor = self.eventos.get_nowait()
                except Empty:
                    self.saida("\nProcesso encerrado sem resultado.\n")
                    self.finalizar()
                else:
                    self.tratar_evento(evento, valor)
        if not self.fechando:
            self.agendamento = self.janela.after(60, self.receber_eventos)

    def tratar_evento(self, evento, valor):
        if evento == "saida":
            self.saida(valor)
        elif evento == "entrada":
            self.saida(valor)
            self.abas.select(0)
            self.definir_estado("entrada", "Aguardando entrada: digite abaixo e pressione Enter.")
            self.campo_entrada.focus_set()
        elif evento == "pausa":
            linha, coluna, valores = valor
            self.destacar(linha, coluna, "atual")
            self.variaveis.delete(*self.variaveis.get_children())
            for nome, (tipo, representacao) in sorted(valores.items()):
                self.variaveis.insert("", "end", values=(nome, tipo, representacao))
            self.definir_estado("pausado", f"Pausado antes da linha {linha}. F10 avança; F5 continua.")
        elif evento in {"erro", "falha"}:
            self.abas.select(0)
            if evento == "erro":
                mensagem, linha, coluna = valor
                self.saida(mensagem + "\n")
                self.destacar(linha, coluna, "erro")
            else:
                self.saida(valor + "\n")
            self.finalizar()
            self.status.configure(text="Execução encerrada com erro.")
        elif evento == "fim":
            self.saida(f"\nExecução concluída. Retorno: {valor}\n")
            self.limpar_marcas()
            self.finalizar()
            self.status.configure(text="Execução concluída.")

    def finalizar(self):
        if self.processo is not None:
            if self.processo.pid is not None:
                self.processo.join(timeout=0.05)
                if self.processo.is_alive():
                    self.processo.terminate()
                    self.processo.join(timeout=1)
            self.processo.close()
        for fila in (self.comandos, self.eventos):
            if fila is not None:
                fila.cancel_join_thread()
                fila.close()
        self.processo = self.comandos = self.eventos = None
        self.definir_estado("pronto", "Pronto")

    def parar(self):
        if self.processo is not None:
            self.finalizar()
            self.limpar_marcas()
            self.saida("\nExecução interrompida pelo usuário.\n")
            self.status.configure(text="Execução interrompida.")

    def fechar(self):
        if self.estado != "pronto":
            if not messagebox.askyesno("Fechar IDE?", "Há uma execução em andamento. Interromper e fechar?"):
                return
            self.parar()
        if not self.pode_trocar():
            return
        self.fechando = True
        if self.agendamento:
            self.janela.after_cancel(self.agendamento)
        if self.atualizacao:
            self.janela.after_cancel(self.atualizacao)
        self.janela.destroy()


def main():
    mp.freeze_support()
    janela = tk.Tk()
    IDE(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()
