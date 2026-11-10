"""Verificações da interface real; ignoradas se não houver ambiente gráfico."""

import time
import tkinter as tk
import unittest

from interface.ide import IDE, PASTA


class TestIDE(unittest.TestCase):
    def setUp(self):
        try:
            self.janela = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(str(erro))
        self.janela.withdraw()
        self.ide = IDE(self.janela)
        self.janela.update()

    def tearDown(self):
        if not hasattr(self, "ide"):
            return
        self.ide.parar()
        self.ide.alterado = False
        self.ide.fechar()

    def esperar(self, estado):
        limite = time.monotonic() + 8
        while time.monotonic() < limite:
            self.janela.update()
            if self.ide.estado == estado:
                return
            time.sleep(0.01)
        self.fail(f"Estado esperado: {estado}; atual: {self.ide.estado}")

    def test_exemplo_e_abas(self):
        self.ide.executar()
        self.esperar("pronto")
        self.assertIn("Resultado: 14", self.ide.console.get("1.0", "end"))
        self.ide.abas.select(1)
        self.janela.update()
        self.assertGreater(len(self.ide.tokens.get_children()), 0)
        self.ide.abas.select(2)
        self.janela.update()
        self.assertIn("def _principal", self.ide.python.get("1.0", "end"))

    def test_erro_destacado(self):
        self.ide.carregar(PASTA / "exemplos" / "erro_execucao.nine")
        self.ide.executar()
        self.esperar("pronto")
        self.assertIn("zero", self.ide.console.get("1.0", "end"))
        self.assertEqual(str(self.ide.editor.tag_ranges("erro")[0]), "3.0")

    def test_debug_e_interrupcao(self):
        self.ide.depurar()
        self.esperar("pausado")
        self.assertTrue(self.ide.editor.tag_ranges("atual"))
        self.ide.passo()
        self.esperar("pausado")
        self.ide.parar()
        self.assertEqual(self.ide.estado, "pronto")
        self.assertEqual(str(self.ide.editor.cget("state")), "normal")

    def test_entrada(self):
        self.ide.definir_codigo('soberania() { anunciar(meContaCompanheiro("Nome: ")); }')
        self.ide.executar()
        self.esperar("entrada")
        self.ide.campo_entrada.insert(0, "Ana")
        self.ide.enviar_entrada()
        self.esperar("pronto")
        self.assertIn("Nome: Ana\nAna", self.ide.console.get("1.0", "end"))

    def test_campo_visivel_e_duas_entradas_pelos_controles(self):
        self.janela.deiconify()
        self.janela.geometry("850x600")
        self.janela.update()
        self.ide.carregar(PASTA / "exemplos" / "entrada.nine")
        self.ide.executar()
        self.esperar("entrada")
        self.assertTrue(self.ide.campo_entrada.winfo_viewable())
        self.assertTrue(self.ide.botao_entrada.winfo_viewable())
        self.assertGreater(self.ide.campo_entrada.winfo_height(), 10)
        self.assertLessEqual(
            self.ide.campo_entrada.winfo_rooty() + self.ide.campo_entrada.winfo_height(),
            self.ide.aba_saida.winfo_rooty() + self.ide.aba_saida.winfo_height(),
        )
        self.ide.campo_entrada.insert(0, "Ana")
        self.ide.botao_entrada.invoke()
        self.esperar("entrada")
        self.assertEqual(self.ide.campo_entrada.get(), "")
        self.ide.campo_entrada.focus_force()
        self.janela.update()
        self.ide.campo_entrada.insert(0, "21")
        self.ide.campo_entrada.event_generate("<Return>")
        self.esperar("pronto")
        resultado = self.ide.console.get("1.0", "end")
        self.assertIn("Seu nome: Ana", resultado)
        self.assertIn("Sua idade: 21", resultado)
        self.assertIn("Ola, Ana", resultado)
        self.assertIn("Maior de idade.", resultado)


if __name__ == "__main__":
    unittest.main()
