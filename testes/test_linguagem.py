import io
import unittest
from contextlib import redirect_stdout

from linguagem import ErroLinguagem, analisar, executar, traduzir


class TestLinguagem(unittest.TestCase):
    def rodar(self, corpo, entradas=()):
        dados = iter(entradas)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            executar("soberania() {\n" + corpo + "\n}", entrada=lambda prompt="": next(dados))
        return buffer.getvalue()

    def verificar_erro(self, codigo, etapa, trecho, linha=None):
        with self.assertRaises(ErroLinguagem) as captura:
            executar(codigo)
        erro = captura.exception
        self.assertEqual(erro.etapa, etapa)
        self.assertIn(trecho, erro.mensagem)
        if linha is not None:
            self.assertEqual(erro.linha, linha)
        return erro

    def test_posicao_tokens(self):
        token = analisar('// comentario\n  companheiro x = 1;')[0]
        self.assertEqual((token.tipo, token.linha, token.coluna), ("VAR", 2, 3))

    def test_precedencia(self):
        self.assertEqual(self.rodar('anunciar(2 + 3 * 4, (2 + 3) * 4, 10 - 3 - 2);'), '14 20 5\n')

    def test_texto_nao_sofre_substituicao(self):
        self.assertEqual(self.rodar('anunciar("sim companheiro // soberania");'), 'sim companheiro // soberania\n')

    def test_entrada_e_conversao(self):
        self.assertEqual(self.rodar('companheiro imposto x = imposto(meContaCompanheiro()); anunciar(x + 1);', ['20']), '21\n')

    def test_condicao_e_booleanos(self):
        self.assertEqual(self.rodar('porFavorMeAjuda (sim && !nao) { anunciar("sim"); } picanhaOutraVez { anunciar("nao"); }'), 'sim\n')
        self.assertEqual(self.rodar('porFavorMeAjuda (nao) {} picanhaOutraVez { anunciar(1); }'), '1\n')

    def test_laco_continue_break(self):
        corpo = '''companheiro imposto i = 0;
        maisUmaVez (i < 10) {
            i aumentando;
            porFavorMeAjuda (i == 2) { penseNoLula; }
            porFavorMeAjuda (i desconfiaQueTaCaro 3) { euNaoVouEnganarOPovoMaisUmaVez; }
            anunciar(i taxaBlusinhas 3);
        }'''
        self.assertEqual(self.rodar(corpo), '1\n0\n')

    def test_retorno_e_bloco_vazio(self):
        self.assertEqual(executar('soberania() { jaViviDemais 7; }'), 7)
        self.assertIsNone(executar('soberania() {}'))

    def test_caractere_invalido(self):
        self.verificar_erro('soberania() {\n @\n}', 'léxico', 'Caractere inválido', 2)

    def test_texto_sem_fechar(self):
        self.verificar_erro('soberania() { anunciar("oi); }', 'léxico', 'Texto sem fechamento')

    def test_falta_ponto_virgula(self):
        erro = self.verificar_erro('soberania() {\n companheiro x = 1\n anunciar(x);\n}', 'sintático', "Esperado ';'", 3)
        self.assertIn('^', erro.formatar('soberania() {\n companheiro x = 1\n anunciar(x);\n}'))

    def test_falta_chave_e_parentese(self):
        self.verificar_erro('soberania() {', 'sintático', 'Bloco sem fechamento')
        self.verificar_erro('soberania() { anunciar(1; }', 'sintático', "Esperado ')'")

    def test_expressao_incompleta(self):
        self.verificar_erro('soberania() { companheiro x = 1 + ; }', 'sintático', 'Esperada uma expressão')

    def test_break_fora_de_laco(self):
        self.verificar_erro('soberania() { euNaoVouEnganarOPovoMaisUmaVez; }', 'sintático', 'dentro de um laço')

    def test_comando_desconhecido(self):
        self.verificar_erro('soberania() { comandoInexistente(); }', 'sintático', 'trabalhar comandoInexistente(')

    def test_variavel_inexistente(self):
        self.verificar_erro('soberania() {\n anunciar(inexistente);\n}', 'de execução', 'inexistente', 2)

    def test_divisao_zero_mapeada_em_bloco(self):
        self.verificar_erro('soberania() {\n porFavorMeAjuda (sim) {\n anunciar(1 / 0);\n }\n}', 'de execução', 'zero', 3)

    def test_conversao_e_tipos_invalidos(self):
        self.verificar_erro('soberania() { companheiro imposto x = "abc"; }', 'de execução', 'conversão')
        self.verificar_erro('soberania() { anunciar("abc" + 1); }', 'de execução', 'Tipos incompatíveis')

    def test_nao_executa_texto_como_python(self):
        self.assertEqual(self.rodar('anunciar("__import__(\\\"os\\\")");'), '__import__("os")\n')
        self.verificar_erro('soberania() { anunciar(__import__("os")); }', 'sintático', 'trabalhar __import__(')

    def test_traducao_exibe_operadores(self):
        resultado = traduzir('soberania() { anunciar(5 taxaBlusinhas 2); }')
        self.assertIn('(5 % 2)', resultado.python)

    def test_lacos_e_condicoes_aninhados(self):
        corpo = '''companheiro i = 0;
        maisUmaVez (i < 2) {
            i aumentando;
            companheiro j = 0;
            maisUmaVez (j < 3) {
                j aumentando;
                porFavorMeAjuda (j == 2) { penseNoLula; }
                picanhaOutraVez { anunciar(i * 10 + j); }
                porFavorMeAjuda (j == 3) { euNaoVouEnganarOPovoMaisUmaVez; }
            }
            porFavorMeAjuda (i == 2) { euNaoVouEnganarOPovoMaisUmaVez; }
            picanhaOutraVez { penseNoLula; }
        }'''
        self.assertEqual(self.rodar(corpo), '11\n13\n21\n23\n')

    def test_argumentos_invalidos_e_expressao_no_fim_do_arquivo(self):
        for corpo, mensagem in (
            ('anunciar(meContaCompanheiro("a", "b"));', 'zero ou um argumento'),
            ('anunciar(imposto());', 'exige um argumento'),
            ('anunciar(taxa(1, 2));', 'exige um argumento'),
        ):
            with self.subTest(corpo=corpo):
                self.verificar_erro('soberania() {' + corpo + '}', 'sintático', mensagem)
        self.verificar_erro('soberania() { anunciar(1 +', 'sintático', 'Esperada uma expressão')


if __name__ == '__main__':
    unittest.main()
