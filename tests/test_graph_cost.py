"""custo_entrada(): a tabela de pesos que vai no relatorio."""
import math

import pytest

import grid
from graph.cost import (CUSTO_AGUA, CUSTO_CONCRETO, custo_entrada,
                        custo_grama)
from graph.state import Estado


def celula(conteudo=grid.LIVRE, terreno=grid.CONCRETO):
    q = grid.GridSquare()
    q.occupied_with, q.terrain = conteudo, terreno
    return q


def estado(hp=100, surf=False):
    return Estado(hp_lider=hp, surf=surf)


class TestCustoGrama:
    @pytest.mark.parametrize("hp, esperado", [
        (100, 3),
        (50, 5),   # 3 * 1.5 = 4.5; floor(x + .5) da 5, round() daria 4
        (0, 6),
    ])
    def test_pontos_da_curva(self, hp, esperado):
        assert custo_grama(hp) == esperado

    def test_nunca_fica_mais_barato_que_concreto(self):
        """use_potion() cura 40 sem teto. Com HP 140 a formula crua daria 2,
        ou seja grama mais barata que concreto. O HP e limitado no calculo."""
        assert custo_grama(140) == 3
        assert custo_grama(140) > CUSTO_CONCRETO

    def test_e_monotona_no_hp(self):
        valores = [custo_grama(hp) for hp in range(100, -1, -1)]
        assert valores == sorted(valores)
        assert all(isinstance(v, int) for v in valores)


class TestTabelaDeCusto:
    def test_concreto_e_a_referencia(self):
        assert custo_entrada(celula(terreno=grid.CONCRETO), estado()) == 1

    def test_grama_usa_o_hp_do_lider(self):
        assert custo_entrada(celula(terreno=grid.GRAMA), estado(hp=100)) == 3
        assert custo_entrada(celula(terreno=grid.GRAMA), estado(hp=50)) == 5

    def test_agua_custa_4_e_exige_surf(self):
        agua = celula(terreno=grid.AGUA)
        assert custo_entrada(agua, estado(surf=True)) == CUSTO_AGUA
        with pytest.raises(ValueError):
            custo_entrada(agua, estado(surf=False))

    def test_pokemon_selvagem_cobra_8_alem_do_terreno(self):
        assert custo_entrada(celula(grid.POKEMON, grid.CONCRETO), estado()) == 1 + 8

    def test_cpu_cobra_12_alem_do_terreno(self):
        assert custo_entrada(celula(grid.CPU, grid.CONCRETO), estado()) == 1 + 12

    def test_penalidade_soma_com_o_terreno_e_nao_o_substitui(self):
        """Batalha na grama com o time ferido e o pior caso do mapa."""
        assert custo_entrada(celula(grid.CPU, grid.GRAMA), estado(hp=50)) == 5 + 12

    def test_pokebola_custa_so_o_terreno(self):
        """Recompensa nao vira peso negativo: Dijkstra nao aceita. O beneficio
        da pokebola entra no score do objetivo, na fase 4."""
        assert custo_entrada(celula(grid.POKEBOLA, grid.CONCRETO), estado()) == 1

    def test_item_de_surf_custa_so_o_terreno(self):
        assert custo_entrada(celula(grid.SURF, grid.CONCRETO), estado()) == 1

    def test_visitado_nao_cobra_penalidade_de_batalha(self):
        """A batalha aconteceu na primeira passagem. Por isso o custo de uma
        celula so cai com o tempo, e rota planejada nao fica invalida por tras."""
        assert custo_entrada(celula(grid.VISITADO, grid.GRAMA), estado()) == 3

    def test_celula_bloqueada_e_erro_de_contrato(self):
        """Quem filtra e vizinhos(); chegar aqui e sinal de que alguem furou o
        adapter. O contrato existe pra que os algoritmos nunca vejam inf."""
        with pytest.raises(ValueError):
            custo_entrada(celula(grid.INACESSIVEL), estado())

    def test_custo_nunca_e_negativo_nem_infinito(self):
        for conteudo in (grid.LIVRE, grid.POKEMON, grid.POKEBOLA, grid.CPU,
                         grid.SURF, grid.VISITADO):
            for terreno in (grid.CONCRETO, grid.GRAMA, grid.AGUA):
                for hp in (100, 50, 0):
                    c = custo_entrada(celula(conteudo, terreno),
                                      estado(hp=hp, surf=True))
                    assert 0 < c < math.inf


class TestEstado:
    def test_de_player_tira_um_retrato(self, jogador):
        e = Estado.de(jogador)
        assert (e.hp_lider, e.pokebolas, e.pocoes, e.surf) == (100, 3, 3, False)

    def test_retrato_nao_acompanha_o_player_depois(self, jogador):
        e = Estado.de(jogador)
        jogador.lider.health = 10
        jogador.surf = True
        assert e.hp_lider == 100 and e.surf is False

    def test_e_imutavel(self, jogador):
        import dataclasses
        with pytest.raises(dataclasses.FrozenInstanceError):
            Estado.de(jogador).hp_lider = 1

    def test_time_vazio_da_hp_zero(self, jogador):
        jogador.pokemon_list.clear()
        assert Estado.de(jogador).hp_lider == 0
