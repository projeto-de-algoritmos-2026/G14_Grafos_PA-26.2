"""Baseline: traverse_grid, o unico ponto onde o jogador se move.

E a funcao que o bot da fase 5 vai ter que dirigir. Hoje ela le do teclado
dentro do proprio corpo, e por isso nao da para chama-la programaticamente
sem monkeypatch de input.
"""
import pytest

import game
import grid
import models
import state


@pytest.fixture
def grid_livre():
    """Grid 8x8 todo em terreno livre, com o player em (0, 0)."""
    state.player1 = models.Player("Lucas", "Male", "Fun", [], {"pokeball": 0}, 0)
    g = grid.Grid()
    for r in range(8):
        for c in range(8):
            celula = grid.GridSquare()
            celula.occupied_with = 1
            celula.terrain = "concrete"
            g.grid[r][c] = celula
    g.grid[0][0] = state.player1
    g.row_pos, g.col_pos = 0, 0
    return g


def responde(monkeypatch, *entradas):
    fila = list(entradas)
    monkeypatch.setattr("builtins.input", lambda *a, **kw: fila.pop(0))


@pytest.mark.parametrize("tecla, destino", [
    ("D", (0, 1)),
    ("S", (1, 0)),
])
def test_move_para_a_direcao_pedida(grid_livre, monkeypatch, tecla, destino):
    responde(monkeypatch, tecla)
    game.traverse_grid(grid_livre)
    assert (grid_livre.row_pos, grid_livre.col_pos) == destino
    assert grid_livre.grid[destino[0]][destino[1]] is state.player1


def test_a_celula_de_origem_fica_marcada_como_visitada(grid_livre, monkeypatch):
    responde(monkeypatch, "D")
    game.traverse_grid(grid_livre)
    assert grid_livre.grid[0][0].occupied_with == -1
    assert repr(grid_livre.grid[0][0]) == "\U00002705"


def test_aceita_letra_minuscula(grid_livre, monkeypatch):
    responde(monkeypatch, "d")
    game.traverse_grid(grid_livre)
    assert (grid_livre.row_pos, grid_livre.col_pos) == (0, 1)


def test_nao_sai_da_borda(grid_livre, monkeypatch):
    responde(monkeypatch, "W", "descartado", "D")
    game.traverse_grid(grid_livre)
    assert (grid_livre.row_pos, grid_livre.col_pos) == (0, 1)


def test_nao_entra_em_celula_inacessivel(grid_livre, monkeypatch):
    grid_livre.grid[0][1].occupied_with = 0
    responde(monkeypatch, "D", "descartado", "S")
    game.traverse_grid(grid_livre)
    assert (grid_livre.row_pos, grid_livre.col_pos) == (1, 0)


def test_a_resposta_do_prompt_de_erro_eh_jogada_fora(grid_livre, monkeypatch):
    """BUG (fase 1): quando o movimento e invalido, a funcao pergunta de novo
    em `direction = input("You cannot move there...")`, mas o `while` volta ao
    prompt do topo e sobrescreve `direction` antes de usa-la. A resposta dada
    ao prompt de erro nunca vale nada: o jogador digita uma direcao a toa.

    Abaixo, o 'S' respondido ao prompt de erro e ignorado e quem move o
    jogador e o 'D' seguinte."""
    responde(monkeypatch, "W", "S", "D")
    game.traverse_grid(grid_livre)
    assert (grid_livre.row_pos, grid_livre.col_pos) == (0, 1)  # e nao (1, 0)


def test_pokebola_no_chao_entra_na_bag(grid_livre, monkeypatch):
    grid_livre.grid[0][1].occupied_with = 3
    responde(monkeypatch, "D")
    game.traverse_grid(grid_livre)
    assert state.player1.bag["pokeball"] == 1


def test_direcao_invalida_estoura(grid_livre, monkeypatch):
    """BUG (fase 1): rr e cc so sao definidos dentro dos ifs de W/A/S/D.
    Qualquer outra tecla cai no `if rr < 0` com as variaveis inexistentes."""
    responde(monkeypatch, "X")
    with pytest.raises(UnboundLocalError):
        game.traverse_grid(grid_livre)


def test_a_funcao_depende_de_input_e_do_global_player1(grid_livre, monkeypatch):
    """BUG (fase 1): sem monkeypatch de input nao ha como mover o jogador por
    codigo. E o que impede o bot de jogar.

    Sem o jogador definido a funcao quebra na hora, como no original. Unica
    diferenca da fase 0: antes a global vivia em main.py e o erro era
    NameError; agora ela vive em state.py e o erro e AttributeError."""
    del state.player1
    responde(monkeypatch, "D")
    with pytest.raises(AttributeError):
        game.traverse_grid(grid_livre)
