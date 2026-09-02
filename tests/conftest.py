"""
Fixtures compartilhadas da baseline.

Estes testes registram o comportamento do jogo COMO ELE E hoje, antes da
fase 1. Varios deles documentam bugs conhecidos (marcados com BUG). Eles
existem para que a quebra de main.py em modulos possa ser feita sem medo:
se um teste destes quebrar durante um refactor, o refactor mudou
comportamento.
"""
import random

import pytest

import main


@pytest.fixture(autouse=True)
def limpa_estado_global():
    """main.py guarda estado em variavel global e em atributo de classe.

    O Grid() faz `GridSquare.occupied_with = player1`, o que suja a classe
    para todos os testes seguintes. Limpamos antes e depois de cada teste.
    """
    _reset()
    yield
    _reset()


def _reset():
    if hasattr(main, "player1"):
        del main.player1
    if "occupied_with" in main.GridSquare.__dict__:
        del main.GridSquare.occupied_with


@pytest.fixture
def pikachu():
    return main.Pokemon("Faisca", "Male", "Pikachu", "Electric",
                        {"Shock": 40, "Tail Whip": 25})


@pytest.fixture
def jogador(pikachu):
    return main.Player("Lucas", "Male", "Fun", [pikachu],
                       {"potion": 3, "pokeball": 3}, 10000)


@pytest.fixture
def rng_previsivel(monkeypatch):
    """Congela random.random para tornar as chances deterministicas."""
    def _fixar(valor):
        monkeypatch.setattr(random, "random", lambda: valor)
    return _fixar
