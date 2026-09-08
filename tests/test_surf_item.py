"""O item de surf: capacidade permanente pega no mapa.

Surf tinha que ser item de mapa (e nao flag de configuracao) pra que o grafo
mude de FORMA durante a partida. Antes dele, agua e parede; depois, e aresta.
"""
import pytest

import game
import grid
import models


@pytest.fixture
def mapa():
    g = grid.Grid(size=4, seed=5)
    for linha in g.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO
    g.row_pos, g.col_pos = 0, 0
    return g


@pytest.fixture
def andarilho():
    return models.Player("Lucas", "Male", "Fun",
                         [models.Pokemon("Faisca", "Male", "Pikachu", "Electric",
                                         {"Shock": 40, "Tail Whip": 25})],
                         {"pokeball": 0, "potion": 3}, 0)


def test_player_comeca_sem_surf(andarilho):
    assert andarilho.surf is False


def test_surf_nao_e_item_de_bag(andarilho):
    """Capacidade permanente e campo do Player, nao entrada consumivel."""
    assert "surf" not in andarilho.bag


def test_pisar_no_item_liga_o_surf_e_reporta(mapa, andarilho):
    mapa.celula(0, 1).occupied_with = grid.SURF
    res = game.mover(mapa, andarilho, "D")
    assert res.valido is True
    assert res.pegou_surf is True
    assert andarilho.surf is True
    assert mapa.celula(0, 1).occupied_with == grid.VISITADO


def test_surf_nao_desliga_ao_andar_de_novo(mapa, andarilho):
    mapa.celula(0, 1).occupied_with = grid.SURF
    game.mover(mapa, andarilho, "D")
    game.mover(mapa, andarilho, "D")
    assert andarilho.surf is True


def test_passo_comum_nao_liga_surf(mapa, andarilho):
    assert game.mover(mapa, andarilho, "D").pegou_surf is False
    assert andarilho.surf is False


class TestAguaNoMovimento:
    def test_agua_e_recusada_sem_surf(self, mapa, andarilho):
        """Antes da fase 2 o jogo deixava andar em cima da agua: acessivel so
        olha o conteudo da celula, e agua e terreno."""
        mapa.celula(0, 1).terrain = grid.AGUA
        res = game.mover(mapa, andarilho, "D")
        assert res.valido is False
        assert res.motivo == "agua sem surf"
        assert mapa.posicao == (0, 0)

    def test_agua_recusada_nao_tem_efeito_colateral(self, mapa, andarilho):
        mapa.celula(0, 1).terrain = grid.AGUA
        antes = [c.occupied_with for lin in mapa.grid for c in lin]
        game.mover(mapa, andarilho, "D")
        assert [c.occupied_with for lin in mapa.grid for c in lin] == antes

    def test_agua_e_atravessada_com_surf(self, mapa, andarilho):
        mapa.celula(0, 1).terrain = grid.AGUA
        andarilho.surf = True
        res = game.mover(mapa, andarilho, "D")
        assert res.valido is True
        assert mapa.posicao == (0, 1)

    def test_item_de_surf_destrava_a_agua_na_mesma_partida(self, mapa, andarilho):
        """A partida inteira em duas linhas: parede, item, aresta."""
        mapa.celula(1, 0).occupied_with = grid.SURF
        mapa.celula(0, 1).terrain = grid.AGUA
        assert game.mover(mapa, andarilho, "D").valido is False
        assert game.mover(mapa, andarilho, "S").pegou_surf is True
        assert game.mover(mapa, andarilho, "W").valido is True
        assert game.mover(mapa, andarilho, "D").valido is True
        assert mapa.posicao == (0, 1)


def test_item_de_surf_nunca_nasce_na_agua():
    """Item de Surf em celula de agua exige Surf pra ser alcancado: e
    inatingivel por construcao, nao por topologia do mapa. Nao e o mesmo
    fenomeno que a fase 2 documentou."""
    for size in (8, 15, 30):
        for seed in range(20):
            mapa = grid.Grid(size=size, seed=seed)
            for linha in mapa.grid:
                for celula in linha:
                    if celula.occupied_with == grid.SURF:
                        assert celula.terrain != grid.AGUA, f"{size}x{size} seed {seed}"
