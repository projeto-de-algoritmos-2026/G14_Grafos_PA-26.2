"""Testes das opções de modo da linha de comando."""

import pytest

import main


def test_modo_humano_e_o_padrao(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py"])

    args = main.parse_args()

    assert args.bot is False
    assert args.human is False


def test_flag_bot(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py", "--bot", "--seed", "42"])

    args = main.parse_args()

    assert args.bot is True
    assert args.seed == 42


def test_flag_visual(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py", "--bot", "--visual"])

    args = main.parse_args()

    assert args.visual is True


def test_bot_e_human_nao_podem_ser_usados_juntos(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py", "--bot", "--human"])

    with pytest.raises(SystemExit):
        main.parse_args()