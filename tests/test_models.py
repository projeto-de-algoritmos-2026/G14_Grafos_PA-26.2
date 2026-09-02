"""Baseline: Pokemon, Player e CpuPlayer."""
import main


class TestPokemon:
    def test_defaults(self):
        p = main.Pokemon()
        assert p.name == "PokeMon"
        assert p.type_of_pokemon == "Rando"
        assert p.nature == "normal"
        assert p.health == 100
        assert p.moves == {}

    def test_moves_nao_sao_compartilhados_entre_instancias(self):
        a, b = main.Pokemon(), main.Pokemon()
        a.moves["Tackle"] = 10
        assert b.moves == {}

    def test_gender_default_eh_sorteado_uma_vez_so(self):
        """BUG (fase 1): random.choice roda na definicao da dataclass, entao
        todo Pokemon criado sem genero nasce com o MESMO genero na execucao
        inteira."""
        assert main.Pokemon().gender == main.Pokemon().gender


class TestGenerateRandPokemon:
    NOMES = {"fuego", "rocky", "mew", "snore", "coolio", "charred"}

    def test_sorteia_do_elenco_conhecido(self):
        for _ in range(50):
            p = main.generate_rand_pokemon()
            assert p.name in self.NOMES
            assert len(p.moves) == 2
            assert p.health == 100

    def test_devolve_objeto_novo_a_cada_chamada(self):
        assert main.generate_rand_pokemon() is not main.generate_rand_pokemon()


class TestPlayer:
    def test_defaults(self):
        p = main.Player()
        assert p.name == "Player"
        assert p.nature == "Fun"
        assert p.money == 10000
        assert p.pokemon_list == []
        assert p.bag == {}

    def test_poke_list_names(self, jogador, pikachu):
        assert jogador.poke_list_names() == [pikachu.name]

    def test_change_poke_devolve_o_objeto_pelo_nome(self, jogador, pikachu):
        outro = main.Pokemon("Bulba", "Male", "Bulbasaur", "Grass", {"Vine": 20})
        jogador.pokemon_list.append(outro)
        assert jogador.change_poke("Bulba") is outro
        assert jogador.change_poke("Faisca") is pikachu

    def test_repr_eh_o_emoji_de_saudacao(self, jogador):
        assert repr(jogador) == "\U0001FAE1"


class TestCpuPlayer:
    def test_name_e_fact_sao_congelados_na_definicao(self):
        """BUG (fase 1): name e fact sao avaliados uma vez so, entao todo CPU
        da execucao tem o mesmo nome e a mesma fala."""
        a, b = main.CpuPlayer(), main.CpuPlayer()
        assert a.name == b.name
        assert a.fact == b.fact
        assert a.fact == f"My name is {a.name}, get ready to battle me!"

    def test_cash_award_tambem_eh_congelado(self):
        """BUG (fase 1): o premio de todo CPU da execucao e identico."""
        assert main.CpuPlayer().cash_award == main.CpuPlayer().cash_award

    def test_cada_cpu_tem_o_proprio_pokemon(self):
        """Corrigido na fase 0: era default mutavel compartilhado, o que
        derrubava o import no Python 3.11+."""
        assert main.CpuPlayer().pokemon is not main.CpuPlayer().pokemon

    def test_poke_gift_eh_o_mesmo_objeto_do_pokemon(self):
        cpu = main.CpuPlayer()
        assert cpu.poke_gift is cpu.pokemon
