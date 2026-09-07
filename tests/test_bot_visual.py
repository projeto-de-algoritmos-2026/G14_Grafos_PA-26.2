"""Testes da demonstracao visual do bot."""

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


def test_modo_visual_mostra_plano_e_mapa(mapa, jogador, capsys):
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA

    executar_bot(mapa, jogador, visual=True)

    saida = capsys.readouterr().out
    assert "Plano: (0, 0) -> (0, 1)" in saida
    assert grid.EMOJI_JOGADOR in saida


def test_modo_visual_mostra_mapa_mesmo_sem_objetivos(mapa, jogador, capsys):
    executar_bot(mapa, jogador, visual=True)

    saida = capsys.readouterr().out
    assert "Mapa inicial:" in saida
    assert "Nenhum objetivo alcançavel" in saida
    assert grid.EMOJI_JOGADOR in saida