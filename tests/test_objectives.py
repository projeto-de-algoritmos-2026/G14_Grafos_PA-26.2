"""Testes da escolha de objetivos."""

import grid
from bot.objectives import pontuar_alvos, selecionar_alvos, utilidade
from graph.state import Estado


def mapa_de_teste():
    mapa = grid.Grid(size=3, seed=1)
    for linha in mapa.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO
    return mapa


def test_score_e_utilidade_dividida_pela_distancia():
    mapa = mapa_de_teste()
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA
    mapa.celula(2, 2).occupied_with = grid.POKEMON

    objetivos = pontuar_alvos((0, 0), mapa, Estado(hp_lider=100))

    assert objetivos[0].posicao == (0, 1)
    assert objetivos[0].score == 60
    assert objetivos[1].posicao == (2, 2)
    assert objetivos[1].score == 100 / 12


def test_seleciona_no_maximo_tres_alvos():
    mapa = mapa_de_teste()
    for posicao in ((0, 1), (0, 2), (1, 0), (1, 1)):
        mapa.celula(*posicao).occupied_with = grid.CPU

    assert len(selecionar_alvos((0, 0), mapa, Estado(hp_lider=100))) == 3


def test_objetivos_inalcancaveis_nao_sao_selecionados():
    mapa = mapa_de_teste()
    mapa.celula(0, 1).terrain = grid.AGUA
    mapa.celula(0, 1).occupied_with = grid.POKEMON

    assert selecionar_alvos((0, 0), mapa, Estado(hp_lider=100, surf=False)) == []


def test_surf_nao_e_objetivo_depois_de_obtido():
    mapa = mapa_de_teste()
    mapa.celula(0, 1).occupied_with = grid.SURF

    assert utilidade(mapa.celula(0, 1), Estado(hp_lider=100, surf=True)) == 0