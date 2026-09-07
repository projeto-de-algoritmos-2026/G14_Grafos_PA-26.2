"""Testes do loop de planejamento do bot."""

import grid
import pytest

from bot.runner import executar_bot


@pytest.fixture
def mapa():
    mapa = grid.Grid(size=3, seed=1)
    for linha in mapa.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO
    return mapa


def test_bot_planeja_executa_e_replaneja_apos_um_objetivo(mapa, jogador):
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA
    mapa.celula(2, 2).occupied_with = grid.POKEBOLA

    resultado = executar_bot(mapa, jogador)

    assert resultado.objetivos_visitados == [(0, 1), (2, 2)]
    assert resultado.replanejamentos == 3
    assert mapa.posicao == (2, 2)
    assert len(resultado.movimentos) == 4
    assert resultado.motivo_parada == "sem objetivos alcançaveis"


def test_bot_respeita_limite_de_passos(mapa, jogador):
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA

    resultado = executar_bot(mapa, jogador, max_passos=0)

    assert resultado.movimentos == []
    assert resultado.objetivos_visitados == []
    assert resultado.motivo_parada == "limite de passos"