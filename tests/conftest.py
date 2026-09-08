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


@pytest.fixture
def seed_ilhada():
    """Acha uma seed cuja origem nasce cercada de agua, em vez de cravar uma.

    Qualquer numero de seed decorado aqui vira teste falso no dia em que a
    geracao do mapa mudar: o que os testes precisam e de UM mapa com a origem
    ilhada, nao daquele mapa especifico.
    """
    from graph.search import dijkstra_distancias
    from graph.state import Estado
    from grid import Grid

    def _achar(size=8, tentativas=200):
        estado = Estado(hp_lider=100)
        for seed in range(tentativas):
            mapa = Grid(size=size, seed=seed)
            distancias, _ = dijkstra_distancias(mapa.posicao, mapa, estado)
            if len(distancias) == 1:
                return seed
        raise AssertionError(f"nenhuma seed ilhada em {tentativas} tentativas ({size}x{size})")

    return _achar
