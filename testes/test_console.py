"""Regressão: mudar a opacidade deve alterar os pixels sem redimensionar a janela."""

import time
import tkinter as tk
import unittest

from interface.ide import IDE


class TestOpacidade(unittest.TestCase):
    def setUp(self):
        try:
            self.janela = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(str(erro))
        self.ide = IDE(self.janela)
        self.atualizar()

    def tearDown(self):
        if hasattr(self, "ide"):
            self.ide.alterado = False
            self.ide.fechar()

    def atualizar(self):
        self.janela.update()
        time.sleep(0.15)
        self.janela.update()

    def pixel_central(self):
        foto = self.ide.console._foto
        return foto.get(foto.width() // 2, foto.height() // 2)

    def test_controle_altera_pixels_sem_mudar_tamanho(self):
        console = self.ide.console
        tamanho = console._tamanho
        self.ide.saida("Texto permanece legível.\n")
        self.ide.controle_opacidade.set(0)
        self.atualizar()
        self.assertEqual(self.pixel_central(), (41, 23, 28))
        self.assertEqual(self.ide.rotulo_opacidade.cget("text"), "0%")
        self.ide.controle_opacidade.set(100)
        self.atualizar()
        original = self.pixel_central()
        self.assertNotEqual(original, (41, 23, 28))
        self.ide.controle_opacidade.set(50)
        self.atualizar()
        esperado = tuple(round((cor + fundo) / 2) for cor, fundo in zip(original, (41, 23, 28)))
        self.assertEqual(self.pixel_central(), esperado)
        self.assertEqual(console._tamanho, tamanho)
        self.assertIn("Texto permanece legível.", console.get("1.0", "end"))
        self.assertTrue(self.ide.campo_entrada.winfo_viewable())

    def test_propriedade_atualiza_imagem_e_rejeita_valor_invalido(self):
        self.ide.console.opacidade = 0
        self.atualizar()
        self.assertEqual(self.pixel_central(), (41, 23, 28))
        self.ide.console.opacidade = 0.75
        self.atualizar()
        self.assertNotEqual(self.pixel_central(), (41, 23, 28))
        with self.assertRaises(ValueError):
            self.ide.console.opacidade = 50
        self.assertEqual(self.ide.console.opacidade, 0.75)


if __name__ == "__main__":
    unittest.main()
