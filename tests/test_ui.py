"""A camada que fala com o jogador humano."""
import pytest

import game
import grid
import models
import ui


@pytest.fixture
def mapa():
    g = grid.Grid(size=8, seed=1)
    for linha in g.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
    g.row_pos, g.col_pos = 0, 0
    return g


@pytest.fixture
def andarilho():
    return models.Player("Lucas", "Male", "Fun",
                         [models.Pokemon("Faisca", "Male", "Pikachu", "Electric",
                                         {"Shock": 40, "Tail Whip": 25})],
                         {"pokeball": 0, "potion": 3}, 0)


def responde(monkeypatch, *entradas):
    fila = list(entradas)
    monkeypatch.setattr("builtins.input", lambda *a, **kw: fila.pop(0))


def test_passo_do_jogador_aplica_a_direcao_digitada(mapa, andarilho, monkeypatch):
    responde(monkeypatch, "D")
    assert ui.passo_do_jogador(mapa, andarilho).posicao == (0, 1)


def test_a_resposta_ao_prompt_de_erro_agora_vale(mapa, andarilho, monkeypatch):
    """Corrigido na fase 1: no original o laco voltava ao prompt do topo e
    sobrescrevia a direcao, entao o que o jogador respondia ao aviso de
    movimento invalido era jogado fora."""
    responde(monkeypatch, "W", "S")
    assert ui.passo_do_jogador(mapa, andarilho).posicao == (1, 0)


def test_insiste_ate_receber_direcao_valida(mapa, andarilho, monkeypatch):
    responde(monkeypatch, "W", "X", "A", "D")
    assert ui.passo_do_jogador(mapa, andarilho).posicao == (0, 1)


def test_avisa_ao_pegar_pokebola(mapa, andarilho, monkeypatch, capsys):
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA
    responde(monkeypatch, "D")
    ui.passo_do_jogador(mapa, andarilho)
    assert "found a pokeball" in capsys.readouterr().out


def test_o_aviso_de_pokebola_saiu_das_regras(mapa, andarilho, capsys):
    """game.mover nao imprime nada: quem narra e a UI. E o que permite o
    benchmark da fase 6 rodar milhares de partidas em silencio."""
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA
    game.mover(mapa, andarilho, "D")
    assert capsys.readouterr().out == ""
