"""Mensagens devem orientar quem escreve Ninescript, sem expor tokens internos."""

import io
import tkinter as tk
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from linguagem import ErroLinguagem, executar, traduzir
from interface.dicionario import Dicionario


class TestDiagnosticos(unittest.TestCase):
    def obter_erro(self, codigo):
        with self.assertRaises(ErroLinguagem) as captura:
            traduzir(codigo)
        return captura.exception

    def test_comando_solto_exige_soberania_sem_expor_main(self):
        erro = self.obter_erro('anunciar("Ola!", 2 + 3);')
        self.assertIn('soberania()', erro.mensagem)
        self.assertIn('fora', erro.mensagem)
        self.assertNotIn('MAIN', erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 1))

    def test_nomes_esperados_descrevem_seu_papel(self):
        casos = [
            ('soberania() { companheiro imposto = 1; }', 'variável'),
            ('pobreNaoPrecisaEstudar (x) {} soberania() {}', 'função'),
            ('pobreNaoPrecisaEstudar soma(1) {} soberania() {}', 'parâmetro'),
            ('soberania() { trabalhar (); }', 'função'),
        ]
        for codigo, papel in casos:
            with self.subTest(codigo=codigo):
                mensagem = self.obter_erro(codigo).mensagem
                self.assertIn(papel, mensagem)
                self.assertNotIn("'ID'", mensagem)

    def test_catch_faltante_indica_comando_real(self):
        mensagem = self.obter_erro('soberania() { socorroXandao {} }').mensagem
        self.assertIn('quandoTiverDesanimado', mensagem)
        self.assertNotIn('CATCH', mensagem)

    def test_comando_apos_main_continua_sendo_rejeitado(self):
        erro = self.obter_erro('soberania() {}\nanunciar(1);')
        self.assertEqual(erro.linha, 2)
        self.assertIn('fora', erro.mensagem)
        self.assertNotIn('MAIN', erro.mensagem)

    def test_chamada_sem_trabalhar_indica_sintaxe(self):
        erro = self.obter_erro('soberania() { soma(1, 2); }')
        self.assertIn('trabalhar soma(', erro.mensagem)

    def test_condicao_usada_como_entrada_indica_comando_correto(self):
        erro = self.obter_erro('soberania() { companheiro nome = porFavorMeAjuda("Nome: "); }')
        self.assertIn('condição', erro.mensagem)
        self.assertIn('meContaCompanheiro', erro.mensagem)

    def test_simbolos_continuam_legiveis_e_fim_de_arquivo_nao_vaza_token(self):
        erro = self.obter_erro('soberania() { anunciar(1; }')
        self.assertIn("Esperado ')'", erro.mensagem)
        erro = self.obter_erro('soberania(')
        self.assertIn('fim do arquivo', erro.mensagem)
        self.assertNotIn('EOF', erro.mensagem)


class TestExemplosDicionario(unittest.TestCase):
    def test_copiar_exemplo_entrega_programa_completo(self):
        try:
            janela = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(str(erro))
        janela.withdraw()
        try:
            dicionario = Dicionario(janela, Path(__file__).resolve().parent.parent / 'BASE.txt')
            indice = next(i for i, item in enumerate(dicionario.verbetes) if item['palavra'] == 'anunciar')
            dicionario.tabela.selection_set(str(indice))
            dicionario.selecionar()
            dicionario.copiar.invoke()
            codigo = janela.clipboard_get()
            self.assertTrue(codigo.startswith('soberania() {'))
            saida = io.StringIO()
            with redirect_stdout(saida):
                executar(codigo)
            self.assertEqual(saida.getvalue(), 'Ola! 5\n')
            for indice in dicionario.tabela.get_children():
                dicionario.tabela.selection_set(indice)
                dicionario.selecionar()
                traduzir(dicionario.exemplo_atual)
        finally:
            janela.update()
            janela.destroy()


if __name__ == '__main__':
    unittest.main()
