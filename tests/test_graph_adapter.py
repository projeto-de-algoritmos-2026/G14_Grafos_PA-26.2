"""vizinhos() e arestas(): a ponte entre a matriz e o grafo.

O que estes testes sustentam na apresentacao: surf nao muda o peso da agua,
ele cria as arestas de agua. Sao dois grafos sobre a mesma matriz, e o sem
surf pode ser desconexo. Nesse caso "nao existe caminho" e o resultado certo
do algoritmo, nao um mapa defeituoso.
"""
import pytest

import grid
from graph.adapter import arestas, vizinhos
from graph.state import Estado


@pytest.fixture
def mapa():
    """3x3 de concreto livre, sem nada sorteado."""
    g = grid.Grid(size=3, seed=7)
    for linha in g.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO
    return g


def sem_surf(hp=100):
    return Estado(hp_lider=hp, surf=False)


def com_surf(hp=100):
    return Estado(hp_lider=hp, surf=True)


class TestVizinhos:
    def test_no_meio_tem_quatro_vizinhos(self, mapa):
        assert set(vizinhos((1, 1), mapa, sem_surf())) == {(0, 1), (1, 2), (2, 1), (1, 0)}

    def test_canto_tem_dois(self, mapa):
        assert set(vizinhos((0, 0), mapa, sem_surf())) == {(0, 1), (1, 0)}

    def test_borda_tem_tres(self, mapa):
        assert len(vizinhos((0, 1), mapa, sem_surf())) == 3

    def test_ordem_e_fixa_w_d_s_a(self, mapa):
        """DFS e BFS dependem da ordem de exploracao: se ela variar entre
        execucoes, o benchmark da fase 6 compara coisas diferentes."""
        assert vizinhos((1, 1), mapa, sem_surf()) == [(0, 1), (1, 2), (2, 1), (1, 0)]

    def test_celula_bloqueada_nao_aparece(self, mapa):
        mapa.celula(0, 1).occupied_with = grid.INACESSIVEL
        assert (0, 1) not in vizinhos((0, 0), mapa, sem_surf())

    def test_celula_cercada_nao_tem_vizinho(self, mapa):
        for pos in ((0, 1), (1, 0), (1, 2), (2, 1)):
            mapa.celula(*pos).occupied_with = grid.INACESSIVEL
        assert vizinhos((1, 1), mapa, sem_surf()) == []

    def test_conteudo_de_batalha_continua_sendo_vizinho(self, mapa):
        """CPU e pokemon selvagem sao caros, nao intransponiveis: o custo cobra,
        o adapter nao esconde."""
        mapa.celula(0, 1).occupied_with = grid.CPU
        mapa.celula(1, 0).occupied_with = grid.POKEMON
        assert set(vizinhos((0, 0), mapa, sem_surf())) == {(0, 1), (1, 0)}


class TestSurfMudaOGrafo:
    def test_agua_nao_e_vizinha_sem_surf_e_e_com_surf(self, mapa):
        mapa.celula(0, 1).terrain = grid.AGUA
        assert vizinhos((0, 0), mapa, sem_surf()) == [(1, 0)]
        assert set(vizinhos((0, 0), mapa, com_surf())) == {(0, 1), (1, 0)}

    def test_sem_surf_o_grafo_pode_ser_desconexo(self, mapa):
        """Coluna de agua no meio do 3x3 corta o mapa em dois componentes.

        Sem surf, (0, 0) nao alcanca (0, 2) de jeito nenhum, e nada no projeto
        tenta evitar que um mapa sorteado fique assim. Quem tem que dizer isso
        e o algoritmo da fase 3, devolvendo "sem caminho".
        """
        for row in range(3):
            mapa.celula(row, 1).terrain = grid.AGUA

        def alcancaveis(estado):
            vistos, pilha = {(0, 0)}, [(0, 0)]
            while pilha:
                for viz in vizinhos(pilha.pop(), mapa, estado):
                    if viz not in vistos:
                        vistos.add(viz)
                        pilha.append(viz)
            return vistos

        assert alcancaveis(sem_surf()) == {(0, 0), (1, 0), (2, 0)}
        assert len(alcancaveis(com_surf())) == 9

    def test_surf_nao_altera_a_travessia_em_terra(self, mapa):
        """Ligar surf so acrescenta aresta, nunca muda peso de terra firme."""
        assert arestas((1, 1), mapa, sem_surf()) == arestas((1, 1), mapa, com_surf())


class TestArestas:
    def test_pareia_vizinho_com_o_custo_de_entrar_nele(self, mapa):
        mapa.celula(0, 1).terrain = grid.GRAMA
        mapa.celula(1, 0).occupied_with = grid.CPU
        assert dict(arestas((0, 0), mapa, sem_surf())) == {(0, 1): 3, (1, 0): 13}

    def test_grama_encarece_com_o_time_ferido(self, mapa):
        mapa.celula(0, 1).terrain = grid.GRAMA
        assert dict(arestas((0, 0), mapa, sem_surf(hp=100)))[(0, 1)] == 3
        assert dict(arestas((0, 0), mapa, sem_surf(hp=50)))[(0, 1)] == 5

    def test_agua_entra_com_custo_4_quando_tem_surf(self, mapa):
        mapa.celula(0, 1).terrain = grid.AGUA
        assert dict(arestas((0, 0), mapa, com_surf()))[(0, 1)] == 4

    def test_nunca_devolve_aresta_que_o_jogo_recusaria(self, mapa):
        """O contrato que impede o bot de planejar rota impossivel: se o
        adapter oferece a aresta, mover() aceita o passo."""
        import game
        import models
        mapa.celula(0, 1).terrain = grid.AGUA
        jogador = models.Player("L", "Male", "Fun",
                                [models.Pokemon("F", "Male", "Pikachu", "Electric",
                                                {"Shock": 40, "Whip": 25})],
                                {"pokeball": 0, "potion": 0}, 0)
        for pos, _ in arestas((0, 0), mapa, Estado.de(jogador)):
            assert pos != (0, 1)
        assert game.mover(mapa, jogador, "D").valido is False

        jogador.surf = True
        assert (0, 1) in dict(arestas((0, 0), mapa, Estado.de(jogador)))
        assert game.mover(mapa, jogador, "D").valido is True
