"""Baseline: throw_pokeball e use_potion."""
import pytest

import game
import models


class TestThrowPokeball:
    def test_gasta_uma_pokebola_mesmo_quando_falha(self, jogador, rng_previsivel):
        alvo = models.Pokemon("Selvagem", "Male", "Onyx", "Rock", {"Slam": 20})
        rng_previsivel(0.99)
        assert game.throw_pokeball(jogador, alvo) is False
        assert jogador.bag["pokeball"] == 2
        assert alvo not in jogador.pokemon_list

    def test_pokemon_saudavel_tem_35_por_cento_de_chance(self, jogador, rng_previsivel):
        alvo = models.Pokemon("Selvagem", "Male", "Onyx", "Rock", {"Slam": 20}, health=100)
        rng_previsivel(0.34)
        assert game.throw_pokeball(jogador, alvo) is True
        assert jogador.pokemon_list[-1] is alvo

    def test_pokemon_ferido_tem_70_por_cento_de_chance(self, jogador, rng_previsivel):
        alvo = models.Pokemon("Selvagem", "Male", "Onyx", "Rock", {"Slam": 20}, health=49)
        rng_previsivel(0.69)
        assert game.throw_pokeball(jogador, alvo) is True

        outro = models.Pokemon("Outro", "Male", "Onyx", "Rock", {"Slam": 20}, health=49)
        rng_previsivel(0.71)
        assert game.throw_pokeball(jogador, outro) is False

    def test_o_limiar_de_saude_eh_50(self, jogador, rng_previsivel):
        """Com 50 de vida cai no ramo dos 35%, com 49 no ramo dos 70%."""
        rng_previsivel(0.50)
        saudavel = models.Pokemon("A", "Male", "Onyx", "Rock", {"S": 1}, health=50)
        ferido = models.Pokemon("B", "Male", "Onyx", "Rock", {"S": 1}, health=49)
        assert game.throw_pokeball(jogador, saudavel) is False
        assert game.throw_pokeball(jogador, ferido) is True


class TestUsePotion:
    def test_cura_40_e_gasta_uma_pocao(self, jogador, pikachu):
        pikachu.health = 30
        game.use_potion(jogador, pikachu)
        assert pikachu.health == 70
        assert jogador.bag["potion"] == 2

    def test_cura_pode_passar_de_100(self, jogador, pikachu):
        """BUG conhecido: nao ha teto de vida."""
        pikachu.health = 100
        game.use_potion(jogador, pikachu)
        assert pikachu.health == 140

    def test_sem_pocao_nao_altera_nada(self, jogador, pikachu, capsys):
        jogador.bag["potion"] = 0
        pikachu.health = 30
        game.use_potion(jogador, pikachu)
        assert pikachu.health == 30
        assert jogador.bag["potion"] == 0
        assert "do not have any more potions" in capsys.readouterr().out

    def test_pocao_negativa_seria_um_erro_de_chave_ausente(self, pikachu):
        """A bag e um dict solto: jogador sem a chave 'potion' quebra."""
        sem_bag = models.Player("X", "Male", "Fun", [pikachu], {}, 10)
        with pytest.raises(KeyError):
            game.use_potion(sem_bag, pikachu)
