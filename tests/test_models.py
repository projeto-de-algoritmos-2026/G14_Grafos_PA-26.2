"""Baseline: Pokemon, Player e CpuPlayer."""
import models


class TestPokemon:
    def test_defaults(self):
        p = models.Pokemon()
        assert p.name == "PokeMon"
        assert p.type_of_pokemon == "Rando"
        assert p.nature == "normal"
        assert p.health == 100
        assert p.moves == {}

    def test_moves_nao_sao_compartilhados_entre_instancias(self):
        a, b = models.Pokemon(), models.Pokemon()
        a.moves["Tackle"] = 10
        assert b.moves == {}

    def test_gender_eh_sorteado_por_instancia(self):
        """Corrigido na fase 1: antes o random.choice rodava uma vez so, na
        definicao da dataclass, e todo Pokemon da execucao nascia com o mesmo
        genero. Com default_factory o sorteio volta a ser por instancia."""
        generos = {models.Pokemon().gender for _ in range(60)}
        assert generos == {"Male", "Female"}


class TestGenerateRandPokemon:
    NOMES = {"fuego", "rocky", "mew", "snore", "coolio", "charred"}

    def test_sorteia_do_elenco_conhecido(self):
        for _ in range(50):
            p = models.generate_rand_pokemon()
            assert p.name in self.NOMES
            assert len(p.moves) == 2
            assert p.health == 100

    def test_devolve_objeto_novo_a_cada_chamada(self):
        assert models.generate_rand_pokemon() is not models.generate_rand_pokemon()


class TestPlayer:
    def test_defaults(self):
        p = models.Player()
        assert p.name == "Player"
        assert p.nature == "Fun"
        assert p.money == 10000
        assert p.pokemon_list == []
        assert p.bag == {}

    def test_poke_list_names(self, jogador, pikachu):
        assert jogador.poke_list_names() == [pikachu.name]

    def test_change_poke_devolve_o_objeto_pelo_nome(self, jogador, pikachu):
        outro = models.Pokemon("Bulba", "Male", "Bulbasaur", "Grass", {"Vine": 20})
        jogador.pokemon_list.append(outro)
        assert jogador.change_poke("Bulba") is outro
        assert jogador.change_poke("Faisca") is pikachu

    def test_repr_eh_o_emoji_de_saudacao(self, jogador):
        assert repr(jogador) == "\U0001FAE1"


class TestCpuPlayer:
    def test_cada_cpu_sorteia_o_proprio_nome(self):
        """Corrigido na fase 1: name era avaliado uma vez so e todo adversario
        da execucao se chamava igual."""
        nomes = {models.CpuPlayer().name for _ in range(80)}
        assert len(nomes) > 1

    def test_a_fala_usa_o_nome_da_propria_instancia(self):
        """Corrigido na fase 1: fact era montado na definicao da classe, com o
        primeiro nome sorteado, entao o CPU se apresentava com nome alheio."""
        for _ in range(20):
            cpu = models.CpuPlayer()
            assert cpu.fact == f"My name is {cpu.name}, get ready to battle me!"

    def test_cada_cpu_sorteia_o_proprio_premio(self):
        """Corrigido na fase 1: o premio de todo CPU da execucao era identico."""
        premios = {models.CpuPlayer().cash_award for _ in range(80)}
        assert len(premios) > 1

    def test_cada_cpu_tem_o_proprio_pokemon(self):
        """Corrigido na fase 0: era default mutavel compartilhado, o que
        derrubava o import no Python 3.11+."""
        assert models.CpuPlayer().pokemon is not models.CpuPlayer().pokemon

    def test_poke_gift_eh_o_mesmo_objeto_do_pokemon(self):
        cpu = models.CpuPlayer()
        assert cpu.poke_gift is cpu.pokemon
