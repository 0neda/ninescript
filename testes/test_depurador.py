import multiprocessing as mp
import sys
import unittest
from contextlib import contextmanager

from interface.depurador import executar_processo, rastrear
from linguagem import ErroLinguagem, executar


@contextmanager
def processo(codigo, depurar=False, pontos=()):
    contexto = mp.get_context("spawn")
    comandos = contexto.Queue()
    eventos = contexto.Queue()
    filho = contexto.Process(target=executar_processo,
                              args=(codigo, depurar, pontos, comandos, eventos))
    filho.start()
    try:
        yield comandos, eventos, filho
    finally:
        filho.join(timeout=0.1)
        if filho.is_alive():
            filho.terminate()
            filho.join(timeout=3)
        filho.close()
        for fila in (comandos, eventos):
            fila.cancel_join_thread()
            fila.close()


class TestDepurador(unittest.TestCase):
    def test_passo_mostra_valores_antes_da_linha(self):
        codigo = 'soberania() {\n companheiro x = 1;\n x aumentando;\n anunciar(x);\n}'
        with processo(codigo, depurar=True) as (comandos, eventos, _):
            evento, (linha, _, valores) = eventos.get(timeout=5)
            self.assertEqual((evento, linha, valores), ("pausa", 2, {}))
            comandos.put(("passo", None))
            evento, (linha, _, valores) = eventos.get(timeout=5)
            self.assertEqual((evento, linha), ("pausa", 3))
            self.assertEqual(valores["x"], ("int", "1"))
            comandos.put(("passo", None))
            _, (linha, _, valores) = eventos.get(timeout=5)
            self.assertEqual((linha, valores["x"]), (4, ("int", "2")))
            comandos.put(("continuar", None))
            self.assertEqual(eventos.get(timeout=5), ("saida", "2\n"))
            self.assertEqual(eventos.get(timeout=5), ("fim", "None"))

    def test_ponto_de_parada(self):
        codigo = 'soberania() {\n companheiro x = 9;\n anunciar(x);\n}'
        with processo(codigo, pontos=[3]) as (comandos, eventos, _):
            evento, (linha, _, valores) = eventos.get(timeout=5)
            self.assertEqual((evento, linha, valores["x"]), ("pausa", 3, ("int", "9")))
            comandos.put(("continuar", None))
            self.assertEqual(eventos.get(timeout=5), ("saida", "9\n"))
            self.assertEqual(eventos.get(timeout=5)[0], "fim")

    def test_entrada_interativa(self):
        codigo = 'soberania() { anunciar(imposto(meContaCompanheiro("Idade: ")) + 1); }'
        with processo(codigo) as (comandos, eventos, _):
            self.assertEqual(eventos.get(timeout=5), ("entrada", "Idade: "))
            comandos.put(("entrada", "21"))
            self.assertEqual(eventos.get(timeout=5), ("saida", "21\n"))
            self.assertEqual(eventos.get(timeout=5), ("saida", "22\n"))
            self.assertEqual(eventos.get(timeout=5)[0], "fim")

    def test_erro_com_posicao_original(self):
        with processo('soberania() {\n anunciar(1 / 0);\n}') as (_, eventos, _):
            evento, (mensagem, linha, coluna) = eventos.get(timeout=5)
            self.assertEqual((evento, linha, coluna), ("erro", 2, 2))
            self.assertIn("zero", mensagem)

    def test_pausa_e_interrupcao_de_laco_infinito(self):
        with processo('soberania() { maisUmaVez (sim) {} }') as (comandos, eventos, filho):
            comandos.put(("pausar", None))
            self.assertEqual(eventos.get(timeout=5)[0], "pausa")
            comandos.put(("continuar", None))
            filho.terminate()
            filho.join(timeout=3)
            self.assertFalse(filho.is_alive())

    def test_rastreamento_anterior_restaurado_apos_erro(self):
        anterior = sys.gettrace()
        with self.assertRaises(ErroLinguagem):
            codigo = 'soberania() { anunciar(1 / 0); }'
            with rastrear(codigo, lambda token, variaveis: None):
                executar(codigo)
        self.assertIs(sys.gettrace(), anterior)

    def test_ponto_de_parada_dentro_de_funcao(self):
        codigo = '''pobreNaoPrecisaEstudar dobro(valor) {
    companheiro resultado = valor * 2;
    jaViviDemais resultado;
}
soberania() { anunciar(trabalhar dobro(5)); }'''
        with processo(codigo, pontos=[3]) as (comandos, eventos, _):
            evento, (linha, _, valores) = eventos.get(timeout=5)
            self.assertEqual((evento, linha), ("pausa", 3))
            self.assertEqual(valores["valor"], ("int", "5"))
            self.assertEqual(valores["resultado"], ("int", "10"))
            comandos.put(("continuar", None))
            self.assertEqual(eventos.get(timeout=5), ("saida", "10\n"))
            self.assertEqual(eventos.get(timeout=5)[0], "fim")

    def test_erro_tratado_em_funcao_nao_encerra_processo(self):
        codigo = '''pobreNaoPrecisaEstudar falhar() { euToErrando("falha"); }
soberania() {
    socorroXandao { trabalhar falhar(); }
    quandoTiverDesanimado (erro) { anunciar(erro); }
    anunciar("continua");
}'''
        with processo(codigo) as (_, eventos, _):
            self.assertEqual(eventos.get(timeout=5), ("saida", "falha\n"))
            self.assertEqual(eventos.get(timeout=5), ("saida", "continua\n"))
            self.assertEqual(eventos.get(timeout=5)[0], "fim")


if __name__ == "__main__":
    unittest.main()
