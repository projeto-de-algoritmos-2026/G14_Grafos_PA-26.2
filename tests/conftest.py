"""Fixtures compartilhadas.

A fase 1 tirou o jogador de dentro da matriz e matou a global player1, entao
nao ha mais estado de modulo para limpar entre testes: cada teste monta o seu
Grid e o seu Player.
"""
import random

import pytest

import models


@pytest.fixture
def pikachu():
    return models.Pokemon("Faisca", "Male", "Pikachu", "Electric",
                          {"Shock": 40, "Tail Whip": 25})


@pytest.fixture
def jogador(pikachu):
    return models.Player("Lucas", "Male", "Fun", [pikachu],
                         {"potion": 3, "pokeball": 3}, 10000)


@pytest.fixture
def rng_previsivel(monkeypatch):
    """Congela random.random para tornar as chances deterministicas."""
    def _fixar(valor):
        monkeypatch.setattr(random, "random", lambda: valor)
    return _fixar
