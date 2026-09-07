"""Testes da execucao de caminhos pelo bot."""

import pytest

import grid

from bot.movement import executar_caminho


@pytest.fixture
def mapa():
    mapa = grid.Grid(size=8, seed=1)
    for linha in mapa.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO
    return mapa


def test_executa_caminho_passo_a_passo(mapa, jogador):
    caminho = [(0, 0), (0, 1), (0, 2)]

    movimentos = executar_caminho(mapa, jogador, caminho)

    assert [movimento.posicao for movimento in movimentos] == [(0, 1), (0, 2)]
    assert all(movimento.valido for movimento in movimentos)
    assert mapa.posicao == (0, 2)


def test_para_no_primeiro_passo_invalido(mapa, jogador):
    mapa.celula(0, 1).occupied_with = grid.INACESSIVEL
    caminho = [(0, 0), (0, 1), (0, 2)]

    movimentos = executar_caminho(mapa, jogador, caminho)

    assert len(movimentos) == 1
    assert movimentos[0].valido is False
    assert movimentos[0].motivo == "celula inacessivel"
    assert mapa.posicao == (0, 0)


def test_caminho_com_uma_posicao_nao_executa_passo(mapa, jogador):
    assert executar_caminho(mapa, jogador, [(0, 0)]) == []