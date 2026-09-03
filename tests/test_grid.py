"""GridSquare e Grid depois do saneamento da fase 1."""
import grid


class TestGridSquare:
    def test_terreno_e_ocupacao_saem_do_dominio_esperado(self):
        for _ in range(200):
            q = grid.GridSquare()
            assert q.terrain in {"grass", "water", "concrete"}
            assert q.occupied_with in {0, 1, 2, 3, 4, 5}

    def test_repr_de_cada_ocupacao(self):
        esperado = {
            grid.INACESSIVEL: "\U0001F6B7",
            grid.LIVRE: "\U0001F334",
            grid.POKEMON: "\U0001F994",
            grid.POKEBOLA: "\U000026D4",
            grid.CPU: "\U0001F94A",
            grid.SURF: "\U0001F3C4",
            grid.VISITADO: "\U00002705",
        }
        q = grid.GridSquare()
        for codigo, emoji in esperado.items():
            q.occupied_with = codigo
            assert repr(q) == emoji

    def test_acessivel_so_eh_falso_em_celula_bloqueada(self):
        q = grid.GridSquare()
        q.occupied_with = grid.INACESSIVEL
        assert q.acessivel is False
        for codigo in (grid.LIVRE, grid.POKEMON, grid.POKEBOLA, grid.CPU,
                       grid.SURF, grid.VISITADO):
            q.occupied_with = codigo
            assert q.acessivel is True


class TestGrid:
    def test_tamanho_eh_parametrizavel(self):
        """A fase 6 precisa rodar em 8, 15 e 30. Fixo em 8 o grafico do
        benchmark sai sem forma."""
        for n in (8, 15, 30):
            g = grid.Grid(size=n, seed=1)
            assert g.size == n
            assert len(g.grid) == n
            assert all(len(linha) == n for linha in g.grid)

    def test_a_mesma_seed_reproduz_o_mapa_inteiro(self):
        a, b = grid.Grid(size=10, seed=42), grid.Grid(size=10, seed=42)
        for r in range(10):
            for c in range(10):
                assert a.grid[r][c].occupied_with == b.grid[r][c].occupied_with
                assert a.grid[r][c].terrain == b.grid[r][c].terrain

    def test_seeds_diferentes_dao_mapas_diferentes(self):
        a, b = grid.Grid(size=10, seed=1), grid.Grid(size=10, seed=2)
        assert any(a.grid[r][c].occupied_with != b.grid[r][c].occupied_with
                   for r in range(10) for c in range(10))

    def test_o_rng_do_grid_nao_depende_do_random_global(self):
        """Sorteios de outras partes do programa nao podem desalinhar o mapa,
        senao rodar varias seeds na fase 6 fica impossivel."""
        import random
        a = grid.Grid(size=8, seed=99)
        [random.random() for _ in range(100)]
        b = grid.Grid(size=8, seed=99)
        assert [c.occupied_with for lin in a.grid for c in lin] == \
               [c.occupied_with for lin in b.grid for c in lin]

    def test_toda_celula_eh_um_gridsquare(self):
        """Corrigido na fase 1: o original colocava um Player em grid[0][0], e
        qualquer varredura que esperasse GridSquare em toda celula quebrava
        ali. E o que destrava a camada de grafo da fase 2."""
        g = grid.Grid(size=8, seed=3)
        assert all(isinstance(cel, grid.GridSquare) for linha in g.grid for cel in linha)

    def test_a_posicao_de_partida_eh_pisavel(self):
        """Sem surf tambem: agua na origem prenderia o jogador no canto."""
        for semente in range(30):
            g = grid.Grid(size=8, seed=semente)
            assert g.celula(0, 0).acessivel
            assert g.celula(0, 0).pisavel(surf=False)


class TestPisavel:
    """Passabilidade tem UMA definicao, e e esta. mover() e vizinhos() usam a
    mesma, pra que jogo e grafo nunca discordem sobre o que e caminho."""

    def test_agua_nao_e_pisavel_sem_surf(self):
        q = grid.GridSquare()
        q.occupied_with, q.terrain = grid.LIVRE, grid.AGUA
        assert q.acessivel is True
        assert q.pisavel(surf=False) is False
        assert q.pisavel(surf=True) is True

    def test_bloqueada_nao_e_pisavel_nem_com_surf(self):
        q = grid.GridSquare()
        q.occupied_with, q.terrain = grid.INACESSIVEL, grid.CONCRETO
        assert q.pisavel(surf=True) is False

    def test_terra_firme_e_pisavel_com_ou_sem_surf(self):
        for terreno in (grid.GRAMA, grid.CONCRETO):
            q = grid.GridSquare()
            q.occupied_with, q.terrain = grid.LIVRE, terreno
            assert q.pisavel(surf=False) is True
            assert q.pisavel(surf=True) is True

    def test_posicao_inicial_e_propriedade_posicao(self):
        g = grid.Grid(size=8, seed=3)
        assert (g.row_pos, g.col_pos) == (0, 0)
        assert g.posicao == (0, 0)

    def test_construir_o_grid_nao_suja_atributo_de_classe(self):
        """Corrigido na fase 1: `GridSquare.occupied_with = player1` mudava o
        default de todas as celulas criadas depois."""
        grid.Grid(size=8, seed=3)
        assert "occupied_with" not in grid.GridSquare.__dict__

    def test_dentro_respeita_as_bordas(self):
        g = grid.Grid(size=8, seed=3)
        assert g.dentro(0, 0) and g.dentro(7, 7)
        assert not g.dentro(-1, 0)
        assert not g.dentro(0, 8)

    def test_desenhar_mostra_o_jogador_na_posicao_atual(self):
        """O jogador saiu da matriz, entao quem o coloca na tela e o desenho."""
        g = grid.Grid(size=8, seed=3)
        g.row_pos, g.col_pos = 2, 3
        linhas = g.desenhar().splitlines()
        assert len(linhas) == 8
        assert linhas[2].split(" ")[3] == grid.EMOJI_JOGADOR
        assert g.desenhar().count(grid.EMOJI_JOGADOR) == 1

    def test_print_grid_imprime_o_mapa(self, capsys):
        grid.Grid(size=8, seed=3).print_grid()
        assert len(capsys.readouterr().out.strip().splitlines()) == 8
