"""Testes da execucao de caminhos pelo bot."""

from unittest import mock

import pytest

import game
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

def test_executar_caminho_para_quando_o_time_acaba(jogador):
    """Sem pokemon a partida acabou: o executor nao segue andando o resto da
    rota. Quem decide o proximo passo e o runner."""
    mapa = grid.Grid(size=3, seed=1)
    for linha in mapa.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO

    def derruba_o_time(*args, **kwargs):
        jogador.pokemon_list.clear()

    mapa.celula(0, 1).occupied_with = grid.CPU
    with mock.patch.object(game, "battle", side_effect=derruba_o_time):
        movimentos = executar_caminho(
            mapa, jogador, [(0, 0), (0, 1), (0, 2)], automatico=True
        )

    assert len(movimentos) == 1
    assert mapa.posicao == (0, 1)


def test_executar_caminho_para_quando_o_time_enche(jogador, pikachu):
    """Vencer no meio de um caminho encerra a partida ali.

    A checagem so existia entre planos, e um caminho do DFS tem dezenas de
    passos: o bot seguia jogando um jogo ja ganho, e as batalhas e o HP
    perdidos depois da vitoria entravam no benchmark como se fossem
    consequencia da rota.
    """
    mapa = grid.Grid(size=3, seed=1)
    for linha in mapa.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO

    def completa_o_time(*args, **kwargs):
        while len(jogador.pokemon_list) < game.POKEMON_PARA_VENCER:
            jogador.pokemon_list.append(pikachu)

    mapa.celula(0, 1).occupied_with = grid.POKEMON
    with mock.patch.object(game, "battle", side_effect=completa_o_time):
        movimentos = executar_caminho(
            mapa, jogador, [(0, 0), (0, 1), (0, 2)], automatico=True
        )

    assert len(movimentos) == 1
    assert mapa.posicao == (0, 1)
    assert game.partida_encerrada(jogador) == "quatro pokemon capturados"
