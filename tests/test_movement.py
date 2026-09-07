"""Testes da conversao de caminhos para comandos do jogo."""

import pytest

from bot.movement import caminho_para_direcoes


def test_converte_movimentos_nas_quatro_direcoes():
    caminho = [(1, 1), (0, 1), (0, 2), (1, 2), (1, 1)]

    assert caminho_para_direcoes(caminho) == ["W", "D", "S", "A"]


def test_caminho_vazio_ou_com_uma_posicao_nao_move():
    assert caminho_para_direcoes([]) == []
    assert caminho_para_direcoes([(2, 3)]) == []


def test_rejeita_trecho_nao_adjacente():
    with pytest.raises(ValueError, match="nao adjacente"):
        caminho_para_direcoes([(0, 0), (2, 0)])


def test_rejeita_movimento_diagonal():
    with pytest.raises(ValueError, match="nao adjacente"):
        caminho_para_direcoes([(0, 0), (1, 1)])