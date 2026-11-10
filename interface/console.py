"""Componente da interface: console com imagem de fundo, usando apenas Tkinter.

O Canvas desenha a imagem e o texto em camadas. Um Text oculto mantém as
operações de texto usadas pela IDE. A imagem tem opacidade ajustável sobre o
fundo escuro e cabe no painel, preservando as proporções.
"""

import tkinter as tk


class Console(tk.Canvas):
    def __init__(self, pai, imagem, fundo="#29171c", cor_texto="#fae9ed", opacidade=0.5):
        super().__init__(pai, bg=fundo, highlightthickness=0, height=180,
                         selectbackground="#c52232", selectforeground="white")
        self.buffer = tk.Text(self, state="disabled")
        self._imagem = self.create_image(0, 0, anchor="center")
        self._texto = self.create_text(10, 8, anchor="nw", fill=cor_texto,
                                       font=("Consolas", 11), text="")
        self._foto = None
        self._render_pendente = None
        self._resize_pendente = None
        self._seguir_fim = False
        self._tamanho = None

        original = tk.PhotoImage(master=self, data=imagem.read_bytes())
        self._largura_original, self._altura_original = original.width(), original.height()
        composta = tk.PhotoImage(master=self, width=original.width(), height=original.height())
        composta.put(fundo, to=(0, 0, original.width(), original.height()))
        composta.tk.call(str(composta), "copy", str(original), "-compositingrule", "overlay")
        ppm = composta.tk.call(str(composta), "data", "-format", "ppm")
        self._pixels_base = ppm.split(b"\n", 3)[3]
        self._rgb_fundo = tuple(int(fundo[i:i + 2], 16) for i in (1, 3, 5))
        self._opacidade = None
        self.opacidade = opacidade

        self.bind("<Configure>", self._redimensionar)
        self.bind("<MouseWheel>", self._roda)
        self.bind("<Button-4>", lambda evento: self.yview("scroll", -3, "units"))
        self.bind("<Button-5>", lambda evento: self.yview("scroll", 3, "units"))
        self.bind("<Button-1>", self._iniciar_selecao)
        self.bind("<B1-Motion>", self._selecionar)
        self.bind("<Control-c>", self._copiar)
        self.bind("<Control-a>", self._selecionar_tudo)
        self.menu = tk.Menu(self, tearoff=False)
        self.menu.add_command(label="Copiar", command=self._copiar)
        self.menu.add_command(label="Selecionar tudo", command=self._selecionar_tudo)
        self.bind("<Button-3>", lambda evento: self.menu.tk_popup(evento.x_root, evento.y_root))

    @property
    def opacidade(self):
        return self._opacidade

    @opacidade.setter
    def opacidade(self, valor):
        valor = float(valor)
        if not 0 <= valor <= 1:
            raise ValueError("A opacidade deve estar entre 0 e 1.")
        if valor == self._opacidade:
            return
        self._opacidade = valor
        pixels = bytearray(len(self._pixels_base))
        for canal, fundo in enumerate(self._rgb_fundo):
            tabela = bytes(round(cor * valor + fundo * (1 - valor)) for cor in range(256))
            pixels[canal::3] = self._pixels_base[canal::3].translate(tabela)
        self._pixels = bytes(pixels)
        self._tamanho = None
        if self._resize_pendente:
            self.after_cancel(self._resize_pendente)
        self._resize_pendente = self.after(60, self._desenhar_imagem)

    def configure(self, cnf=None, **opcoes):
        if "state" in opcoes:
            self.buffer.configure(state=opcoes.pop("state"))
        return super().configure(cnf, **opcoes)

    config = configure

    def get(self, inicio, fim):
        return self.buffer.get(inicio, fim)

    def index(self, indice):
        return self.buffer.index(indice)

    def insert(self, indice, texto):
        self.buffer.insert(indice, texto)
        self._agendar_texto()

    def delete(self, inicio, fim):
        self.buffer.delete(inicio, fim)
        self.select_clear()
        self._agendar_texto()

    def see(self, indice):
        self._seguir_fim = True
        self._agendar_texto()

    def _agendar_texto(self):
        if self._render_pendente is None:
            self._render_pendente = self.after_idle(self._desenhar_texto)

    def _desenhar_texto(self):
        self._render_pendente = None
        self.itemconfigure(self._texto, text=self.buffer.get("1.0", "end-1c"))
        self._atualizar_regiao()
        if self._seguir_fim:
            self.yview("moveto", 1)
            self._seguir_fim = False
        self._posicionar_imagem()

    def _atualizar_regiao(self):
        caixa = self.bbox(self._texto) or (0, 0, 0, 0)
        self.configure(scrollregion=(0, 0, max(self.winfo_width(), caixa[2] + 10),
                                      max(self.winfo_height(), caixa[3] + 8)))

    def _redimensionar(self, evento):
        self._atualizar_regiao()
        self._posicionar_imagem()
        if self._resize_pendente:
            self.after_cancel(self._resize_pendente)
        self._resize_pendente = self.after(100, self._desenhar_imagem)

    def _desenhar_imagem(self):
        self._resize_pendente = None
        largura_painel, altura_painel = self.winfo_width(), self.winfo_height()
        if largura_painel <= 1 or altura_painel <= 1:
            return
        escala = min(largura_painel / self._largura_original, altura_painel / self._altura_original)
        largura = max(1, round(self._largura_original * escala))
        altura = max(1, round(self._altura_original * escala))
        if self._tamanho != (largura, altura):
            colunas = [min(self._largura_original - 1, x * self._largura_original // largura) * 3
                       for x in range(largura)]
            linhas = []
            for y in range(altura):
                origem = min(self._altura_original - 1, y * self._altura_original // altura)
                inicio = origem * self._largura_original * 3
                linha = self._pixels[inicio:inicio + self._largura_original * 3]
                linhas.append(b"".join(linha[x:x + 3] for x in colunas))
            dados = f"P6\n{largura} {altura}\n255\n".encode("ascii") + b"".join(linhas)
            self._foto = tk.PhotoImage(master=self, data=dados, format="PPM")
            self.itemconfigure(self._imagem, image=self._foto)
            self._tamanho = (largura, altura)
        self._posicionar_imagem()

    def _posicionar_imagem(self):
        self.coords(self._imagem, self.canvasx(self.winfo_width() / 2),
                    self.canvasy(self.winfo_height() / 2))

    def xview(self, *args):
        resultado = super().xview(*args)
        self._posicionar_imagem()
        return resultado

    def yview(self, *args):
        resultado = super().yview(*args)
        self._posicionar_imagem()
        return resultado

    def _roda(self, evento):
        self.yview("scroll", -int(evento.delta / 120) * 3, "units")
        return "break"

    def _indice_mouse(self, evento):
        return super().index(self._texto, f"@{self.canvasx(evento.x)},{self.canvasy(evento.y)}")

    def _iniciar_selecao(self, evento):
        self.focus_set()
        self.select_clear()
        self.select_from(self._texto, self._indice_mouse(evento))

    def _selecionar(self, evento):
        self.select_to(self._texto, self._indice_mouse(evento))

    def _selecionar_tudo(self, evento=None):
        texto = self.buffer.get("1.0", "end-1c")
        if texto:
            self.select_from(self._texto, 0)
            self.select_to(self._texto, len(texto) - 1)
        return "break"

    def _copiar(self, evento=None):
        texto = self.buffer.get("1.0", "end-1c")
        if self.select_item() == self._texto:
            inicio = super().index(self._texto, "sel.first")
            fim = super().index(self._texto, "sel.last")
            texto = texto[inicio:fim + 1]
        if texto:
            self.clipboard_clear()
            self.clipboard_append(texto)
        return "break"

    def destroy(self):
        for agendamento in (self._render_pendente, self._resize_pendente):
            if agendamento:
                self.after_cancel(agendamento)
        super().destroy()
