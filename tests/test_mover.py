"""mover(): o contrato de passo que o bot da fase 5 e o bench da fase 6 usam.

Substitui o antigo test_traverse.py. A diferenca que importa: aqui ninguem
faz monkeypatch de input, porque mover() nao le do teclado.
"""
import pytest

import game
import grid
import models


@pytest.fixture
def mapa():
    """Grid 8x8 todo pisavel, jogador em (0, 0)."""
    g = grid.Grid(size=8, seed=1)
    for linha in g.grid:
        for celula in linha:
            celula.occupied_with = grid.LIVRE
            celula.terrain = "concrete"
    g.row_pos, g.col_pos = 0, 0
    return g


@pytest.fixture
def andarilho():
    return models.Player("Lucas", "Male", "Fun",
                         [models.Pokemon("Faisca", "Male", "Pikachu", "Electric",
                                         {"Shock": 40, "Tail Whip": 25})],
                         {"pokeball": 0, "potion": 3}, 0)


@pytest.mark.parametrize("tecla, destino", [
    ("W", None), ("A", None),
    ("D", (0, 1)), ("S", (1, 0)),
])
def test_direcoes_a_partir_do_canto(mapa, andarilho, tecla, destino):
    res = game.mover(mapa, andarilho, tecla)
    if destino is None:
        assert res.valido is False
        assert res.motivo == "fora do mapa"
        assert mapa.posicao == (0, 0)
    else:
        assert res.valido is True
        assert res.posicao == destino
        assert mapa.posicao == destino


def test_aceita_minuscula(mapa, andarilho):
    assert game.mover(mapa, andarilho, "d").posicao == (0, 1)


def test_direcao_desconhecida_nao_estoura(mapa, andarilho):
    """Corrigido na fase 1: rr e cc so eram definidos dentro dos ifs de
    W/A/S/D, e qualquer outra tecla levantava UnboundLocalError."""
    res = game.mover(mapa, andarilho, "X")
    assert res.valido is False
    assert res.motivo == "direcao desconhecida"
    assert mapa.posicao == (0, 0)


def test_direcao_vazia_nao_estoura(mapa, andarilho):
    assert game.mover(mapa, andarilho, "").valido is False


def test_celula_inacessivel_e_recusada_sem_mover(mapa, andarilho):
    mapa.celula(0, 1).occupied_with = grid.INACESSIVEL
    res = game.mover(mapa, andarilho, "D")
    assert res.valido is False
    assert res.motivo == "celula inacessivel"
    assert mapa.posicao == (0, 0)


def test_movimento_invalido_nao_consome_nada(mapa, andarilho):
    """O bot vai consultar vizinhos o tempo todo: recusar um passo nao pode
    ter efeito colateral."""
    mapa.celula(0, 1).occupied_with = grid.INACESSIVEL
    antes = [c.occupied_with for lin in mapa.grid for c in lin]
    game.mover(mapa, andarilho, "D")
    assert [c.occupied_with for lin in mapa.grid for c in lin] == antes


def test_celula_pisada_fica_marcada_como_visitada(mapa, andarilho):
    game.mover(mapa, andarilho, "D")
    assert mapa.celula(0, 1).occupied_with == grid.VISITADO
    assert repr(mapa.celula(0, 1)) == "\U00002705"


def test_pokebola_entra_na_bag_e_e_consumida(mapa, andarilho):
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA
    res = game.mover(mapa, andarilho, "D")
    assert res.pegou_pokebola is True
    assert andarilho.bag["pokeball"] == 1
    assert mapa.celula(0, 1).occupied_with == grid.VISITADO


def test_pokebola_nao_pode_ser_pega_duas_vezes(mapa, andarilho):
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA
    game.mover(mapa, andarilho, "D")
    game.mover(mapa, andarilho, "A")
    game.mover(mapa, andarilho, "D")
    assert andarilho.bag["pokeball"] == 1


def test_celula_de_cpu_forca_batalha_e_reporta(mapa, andarilho, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a, **kw: "R")  # foge da batalha
    mapa.celula(0, 1).occupied_with = grid.CPU
    res = game.mover(mapa, andarilho, "D")
    assert res.valido is True
    assert res.batalhou is True


def test_pokemon_selvagem_forca_batalha_e_reporta(mapa, andarilho, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a, **kw: "R")
    mapa.celula(0, 1).occupied_with = grid.POKEMON
    res = game.mover(mapa, andarilho, "D")
    assert res.batalhou is True


def test_hp_perdido_eh_reportado_no_movimento(mapa, andarilho, monkeypatch):
    """A fase 6 mede HP perdido por passo; quem informa e o proprio Movimento."""
    def briga(player, opp):
        player.lider.health -= 30
    monkeypatch.setattr(game, "battle", briga)
    mapa.celula(0, 1).occupied_with = grid.POKEMON
    res = game.mover(mapa, andarilho, "D")
    assert res.hp_perdido == 30


def test_passo_em_celula_livre_nao_cobra_hp(mapa, andarilho):
    res = game.mover(mapa, andarilho, "D")
    assert res.hp_perdido == 0
    assert res.batalhou is False


def test_mover_nao_depende_de_variavel_global(mapa, andarilho):
    """Corrigido na fase 1: o jogador chegava por uma global player1 que so
    existia dentro do bloco __main__. Agora vem por parametro, e por isso o
    bot consegue dirigir a partida."""
    import importlib
    assert importlib.util.find_spec("state") is None
    outro = models.Player("Outro", "Male", "Fun",
                          [models.Pokemon("B", "Male", "Onyx", "Rock", {"S": 1, "T": 2})],
                          {"pokeball": 0}, 0)
    mapa.celula(0, 1).occupied_with = grid.POKEBOLA
    game.mover(mapa, outro, "D")
    assert outro.bag["pokeball"] == 1
    assert andarilho.bag["pokeball"] == 0
