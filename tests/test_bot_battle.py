"""Testes do modo automatico de batalha."""

import pytest

import game
import grid
import models


@pytest.fixture
def mapa():
    mapa = grid.Grid(size=8, seed=1)
    for linha in mapa.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = grid.CONCRETO
    return mapa


def test_batalha_automatica_nao_le_do_teclado(monkeypatch, jogador):
    adversario = models.Pokemon(
        "Selvagem", "Male", "Rattata", "Normal", {"Investida": 1}, health=20
    )
    monkeypatch.setattr(game, "generate_rand_pokemon", lambda: adversario)
    monkeypatch.setattr(
        "builtins.input",
        lambda *args: (_ for _ in ()).throw(AssertionError("input inesperado")),
    )

    game.battle(jogador, "wild pokemon", automatico=True)

    assert len(jogador.pokemon_list) == 2
    assert jogador.pokemon_list[-1] is adversario


def test_mover_pode_atravessar_batalha_no_modo_automatico(mapa, jogador, monkeypatch):
    adversario = models.Pokemon(
        "Selvagem", "Male", "Rattata", "Normal", {"Investida": 1}, health=20
    )
    monkeypatch.setattr(game, "generate_rand_pokemon", lambda: adversario)
    mapa.celula(0, 1).occupied_with = grid.POKEMON

    movimento = game.mover(mapa, jogador, "D", automatico=True)

    assert movimento.valido is True
    assert movimento.batalhou is True
    assert mapa.posicao == (0, 1)

def test_battle_sem_time_nao_estoura(jogador):
    """O ultimo pokemon pode desmaiar no meio do caminho e o passo seguinte
    cair numa celula de CPU. Antes isso levantava IndexError em
    pokemon_list[0]; achado rodando a grade da fase 6."""
    jogador.pokemon_list.clear()

    assert game.battle(jogador, "cpu", automatico=True) is None
    assert jogador.pokemon_list == []
