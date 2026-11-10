"""Comportamentos dos novos comandos, incluindo combinações e erros."""

import io
import unittest
from contextlib import redirect_stdout

from linguagem import ErroLinguagem, executar


class TestRecursos(unittest.TestCase):
    def rodar(self, corpo, funcoes=""):
        saida = io.StringIO()
        with redirect_stdout(saida):
            executar(funcoes + "\nsoberania() {\n" + corpo + "\n}")
        return saida.getvalue()

    def erro(self, codigo, etapa, trecho):
        with self.assertRaises(ErroLinguagem) as captura:
            executar(codigo)
        self.assertEqual(captura.exception.etapa, etapa)
        self.assertIn(trecho, captura.exception.mensagem)
        return captura.exception

    def test_for_intervalos_e_passo_negativo(self):
        self.assertEqual(self.rodar('''
            vocesNasceramSoPraTrabalhar(i, 0, 3) { anunciar(i); }
            vocesNasceramSoPraTrabalhar(j, 4, 0, -2) { anunciar(j); }
        '''), '0\n1\n2\n4\n2\n')

    def test_for_colecoes_continue_e_break(self):
        self.assertEqual(self.rodar('''
            vocesNasceramSoPraTrabalhar(item, mensalao[1, 2, 3, 4]) {
                porFavorMeAjuda (item == 2) { penseNoLula; }
                porFavorMeAjuda (item == 4) { euNaoVouEnganarOPovoMaisUmaVez; }
                anunciar(item);
            }
            vocesNasceramSoPraTrabalhar(chave, petrolao{"a": 1, "b": 2}) { anunciar(chave); }
        '''), '1\n3\na\nb\n')

    def test_array_dicionario_acesso_e_atribuicao_aninhada(self):
        self.assertEqual(self.rodar('''
            companheiro dados = petrolao{"nome": "Ana", "notas": mensalao[5, 7]};
            dados["notas"][0] = 9;
            dados["notas"][1] aumentando;
            dados["nome"] = "Bia";
            anunciar(dados["nome"], dados["notas"][0], dados["notas"][1]);
            anunciar(mensalao[], petrolao{});
        '''), 'Bia 9 8\n[] {}\n')

    def test_funcoes_parametros_retorno_e_chamada_como_comando(self):
        funcoes = '''
            pobreNaoPrecisaEstudar soma(a, b) { jaViviDemais a + b; }
            pobreNaoPrecisaEstudar mostrar(valor) { anunciar(valor); }
        '''
        self.assertEqual(self.rodar('''
            companheiro resultado = trabalhar soma(2, trabalhar soma(3, 4));
            trabalhar mostrar(resultado);
        ''', funcoes), '9\n')

    def test_funcao_depois_do_main_recursao_e_escopo(self):
        codigo = '''
            soberania() { companheiro n = 99; anunciar(trabalhar fatorial(5), n); }
            pobreNaoPrecisaEstudar fatorial(n) {
                porFavorMeAjuda (n <= 1) { jaViviDemais 1; }
                jaViviDemais n * trabalhar fatorial(n - 1);
            }
        '''
        saida = io.StringIO()
        with redirect_stdout(saida):
            executar(codigo)
        self.assertEqual(saida.getvalue(), '120 99\n')

    def test_funcao_modifica_colecao_compartilhada(self):
        self.assertEqual(self.rodar('''
            companheiro itens = mensalao[0];
            trabalhar alterar(itens);
            anunciar(itens[0]);
        ''', 'pobreNaoPrecisaEstudar alterar(itens) { itens[0] = 8; }'), '8\n')

    def test_try_catch_divisao_e_continuacao(self):
        self.assertEqual(self.rodar('''
            socorroXandao { anunciar(1 / 0); }
            quandoTiverDesanimado (erro) { anunciar(erro); }
            anunciar("continua");
        '''), 'Divisão ou resto por zero.\ncontinua\n')

    def test_throw_em_funcao_e_catch_aninhado(self):
        self.assertEqual(self.rodar('''
            socorroXandao {
                socorroXandao { trabalhar falhar(); }
                quandoTiverDesanimado (erro) { euToErrando("externo: " + erro); }
            } quandoTiverDesanimado (erro) { anunciar(erro); }
        ''', 'pobreNaoPrecisaEstudar falhar() { euToErrando("falha"); }'), 'externo: falha\n')

    def test_catch_indice_chave_e_passo_zero(self):
        for comando, trecho in (
            ('anunciar(mensalao[1][5]);', 'Índice'),
            ('anunciar(petrolao{}["ausente"]);', 'ausente'),
            ('vocesNasceramSoPraTrabalhar(i, 0, 3, 0) {}', 'passo'),
        ):
            with self.subTest(comando=comando):
                saida = self.rodar('socorroXandao {' + comando + '} quandoTiverDesanimado (e) { anunciar(e); }')
                self.assertIn(trecho, saida)

    def test_throw_sem_catch_mantem_posicao_da_funcao(self):
        erro = self.erro('''pobreNaoPrecisaEstudar falhar() {
    euToErrando("erro proposital");
}
soberania() { trabalhar falhar(); }''', 'de execução', 'erro proposital')
        self.assertEqual((erro.linha, erro.coluna), (2, 5))

    def test_funcao_inexistente_e_argumentos_errados(self):
        self.erro('soberania() { trabalhar ausente(); }', 'de execução', 'Função')
        self.erro('pobreNaoPrecisaEstudar f(x) {} soberania() { trabalhar f(); }', 'de execução', 'argumentos')

    def test_erros_de_sintaxe_nos_novos_comandos(self):
        casos = [
            ('soberania() { socorroXandao {} }', 'quandoTiverDesanimado'),
            ('soberania() { companheiro x = mensalao[1, 2; }', "']'"),
            ('soberania() { companheiro x = petrolao{"a" 1}; }', "':'"),
            ('soberania() { euToErrando(); }', 'um argumento'),
            ('soberania() { vocesNasceramSoPraTrabalhar(i, 0, 1, 2, 3) {} }', 'for'),
            ('pobreNaoPrecisaEstudar f(x, x) {} soberania() {}', 'Parâmetro'),
            ('pobreNaoPrecisaEstudar f() {} pobreNaoPrecisaEstudar f() {} soberania() {}', 'Função'),
            ('soberania() { pobreNaoPrecisaEstudar f() {} }', 'fora'),
            ('soberania() {} soberania() {}', 'soberania'),
        ]
        for codigo, trecho in casos:
            with self.subTest(codigo=codigo):
                self.erro(codigo, 'sintático', trecho)

    def test_erros_sintaticos_nao_sao_capturados(self):
        self.erro('soberania() { socorroXandao { anunciar(1) } quandoTiverDesanimado(e) {} }',
                  'sintático', "Esperado ';'")

    def test_mensagem_do_erro_sem_nome_no_catch(self):
        self.assertEqual(self.rodar('''
            socorroXandao { anunciar(1 / 0); }
            quandoTiverDesanimado { anunciar(naoTaEntregando()); }
        '''), 'Divisão ou resto por zero.\n')

    def test_mensagem_atual_preserva_erros_aninhados(self):
        self.assertEqual(self.rodar('''
            socorroXandao { euToErrando("externo"); }
            quandoTiverDesanimado (erro) {
                erro = "alterado";
                anunciar(naoTaEntregando());
                socorroXandao { euToErrando("interno"); }
                quandoTiverDesanimado { anunciar(naoTaEntregando()); }
                anunciar(naoTaEntregando());
            }
        '''), 'externo\ninterno\nexterno\n')

    def test_mensagem_em_condicao_dentro_do_catch(self):
        self.assertEqual(self.rodar('''
            socorroXandao { euToErrando("falha"); }
            quandoTiverDesanimado {
                porFavorMeAjuda (naoTaEntregando() == "falha") { anunciar("ok"); }
            }
        '''), 'ok\n')

    def test_consulta_do_erro_exige_catch_e_nao_aceita_argumentos(self):
        self.erro('soberania() { anunciar(naoTaEntregando()); }', 'sintático', 'dentro de um catch')
        self.erro('soberania() { socorroXandao {} quandoTiverDesanimado { anunciar(naoTaEntregando(1)); } }',
                  'sintático', 'não aceita argumentos')


if __name__ == '__main__':
    unittest.main()
