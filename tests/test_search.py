"""Testes dos algoritmos"""

import math

import grid
from graph.search import bfs_path, dijkstra, dfs_path
from graph.state import Estado


def mapa_de_teste():
    mapa = grid.Grid(size=3, seed=1)
    for linha in mapa.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO
    return mapa


def test_os_tres_algoritmos_encontram_um_caminho():
    mapa = mapa_de_teste()
    estado = Estado(hp_lider=100)

    for algoritmo in (dfs_path, bfs_path, dijkstra):
        caminho, custo, nos_expandidos = algoritmo((0, 0), (2, 2), mapa, estado)

        assert caminho[0] == (0, 0)
        assert caminho[-1] == (2, 2)
        assert custo == len(caminho) - 1
        assert nos_expandidos > 0


def test_bfs_e_dijkstra_divergem_em_terreno_caro():
    mapa = mapa_de_teste()
    mapa.celula(0, 1).terrain = grid.GRAMA
    estado = Estado(hp_lider=0)

    caminho_bfs, custo_bfs, _ = bfs_path((0, 0), (0, 2), mapa, estado)
    caminho_dijkstra, custo_dijkstra, _ = dijkstra((0, 0), (0, 2), mapa, estado)

    assert caminho_bfs == [(0, 0), (0, 1), (0, 2)]
    assert caminho_dijkstra == [(0, 0), (1, 0), (1, 1), (1, 2), (0, 2)]
    assert len(caminho_bfs) < len(caminho_dijkstra)
    assert custo_dijkstra < custo_bfs


def test_dfs_devolve_um_caminho_valido_sem_promessa_de_otimo():
    mapa = mapa_de_teste()

    caminho, custo, nos_expandidos = dfs_path((0, 0), (2, 2), mapa, Estado(hp_lider=100))

    assert caminho[0] == (0, 0)
    assert caminho[-1] == (2, 2)
    assert custo >= 0
    assert nos_expandidos > 0


def test_sem_caminho_retorna_infinito():
    mapa = mapa_de_teste()
    for linha in mapa.grid:
        linha[1].terrain = grid.AGUA

    for algoritmo in (dfs_path, bfs_path, dijkstra):
        caminho, custo, nos_expandidos = algoritmo(
            (0, 0), (0, 2), mapa, Estado(hp_lider=100, surf=False)
        )

        assert caminho == []
        assert custo == math.inf
        assert nos_expandidos == 3


def test_origem_igual_ao_destino():
    mapa = mapa_de_teste()

    for algoritmo in (dfs_path, bfs_path, dijkstra):
        assert algoritmo((1, 1), (1, 1), mapa, Estado(hp_lider=100)) == (
            [(1, 1)], 0, 1
        )