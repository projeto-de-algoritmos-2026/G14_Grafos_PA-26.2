"""Testes da escolha de objetivos."""

import math

import grid
from bot.objectives import (
    melhor_ordem,
    matriz_distancias,
    planejar_visita,
    pontuar_alvos,
    selecionar_alvos,
    utilidade,
)
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


def test_matriz_de_distancias_tem_origem_e_alvos():
    mapa = mapa_de_teste()
    pontos = [(0, 0), (0, 1), (2, 2)]

    matriz = matriz_distancias(pontos, mapa, Estado(hp_lider=100))

    assert matriz[(0, 0)][(0, 1)] == 1
    assert matriz[(0, 1)][(2, 2)] == 3
    assert matriz[(2, 2)][(2, 2)] == 0


def test_melhor_ordem_testa_as_permutacoes():
    mapa = mapa_de_teste()
    origem = (0, 0)
    alvos = [(0, 2), (2, 0), (2, 2)]

    ordem, custo, matriz = melhor_ordem(
        origem, alvos, mapa, Estado(hp_lider=100)
    )

    assert ordem == [(0, 2), (2, 2), (2, 0)]
    assert custo == 6
    assert len(matriz) == 4


def test_melhor_ordem_ignora_permutacoes_sem_caminho():
    mapa = mapa_de_teste()
    mapa.celula(1, 1).terrain = grid.AGUA
    alvos = [(0, 2), (2, 0), (1, 1)]

    ordem, custo, _ = melhor_ordem(
        (0, 0), alvos, mapa, Estado(hp_lider=100, surf=False)
    )

    assert ordem == []
    assert math.isinf(custo)


def test_replanejamento_remove_objetivo_alcancado():
    mapa = mapa_de_teste()
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA
    mapa.celula(0, 2).occupied_with = grid.POKEMON
    estado = Estado(hp_lider=100)

    primeira, _, _ = planejar_visita((0, 0), mapa, estado, limite=2)
    mapa.celula(*primeira[0]).occupied_with = grid.VISITADO
    segunda, _, _ = planejar_visita(primeira[0], mapa, estado, limite=2)

    assert primeira[0] == (0, 1)
    assert (0, 1) not in segunda
    assert segunda == [(0, 2)]


def test_replanejamento_com_surf_encontra_novo_territorio():
    mapa = mapa_de_teste()
    mapa.celula(0, 1).terrain = grid.AGUA
    mapa.celula(0, 1).occupied_with = grid.SURF
    mapa.celula(0, 2).terrain = grid.AGUA
    mapa.celula(0, 2).occupied_with = grid.POKEMON

    sem_surf, _, _ = planejar_visita(
        (0, 0), mapa, Estado(hp_lider=100, surf=False)
    )
    com_surf, _, _ = planejar_visita(
        (0, 0), mapa, Estado(hp_lider=100, surf=True)
    )

    assert sem_surf == []
    assert com_surf == [(0, 2)]