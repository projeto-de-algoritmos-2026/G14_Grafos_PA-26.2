"""Testes do loop de planejamento do bot."""

from unittest import mock

import game
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

def test_vencer_no_meio_do_caminho_reporta_vitoria_e_nao_caminho_cortado(mapa, jogador, pikachu):
    """Vencer corta a rota em execucao, e o motivo tem que ser a vitoria.

    Sem a ordem certa das checagens, o resultado diria "caminho interrompido"
    numa partida ganha, porque o bot parou antes de chegar ao destino.
    """
    mapa.celula(0, 1).occupied_with = grid.POKEMON
    mapa.celula(2, 2).occupied_with = grid.POKEBOLA

    def completa_o_time(*args, **kwargs):
        while len(jogador.pokemon_list) < game.POKEMON_PARA_VENCER:
            jogador.pokemon_list.append(pikachu)

    with mock.patch.object(game, "battle", side_effect=completa_o_time):
        resultado = executar_bot(mapa, jogador)

    assert resultado.motivo_parada == "quatro pokemon capturados"
    assert resultado.objetivos_visitados == [(0, 1)]
