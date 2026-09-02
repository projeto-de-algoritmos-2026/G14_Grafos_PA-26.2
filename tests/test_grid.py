"""Baseline: GridSquare e Grid."""
import main


class TestGridSquare:
    def test_terreno_e_ocupacao_saem_do_dominio_esperado(self):
        for _ in range(200):
            q = main.GridSquare()
            assert q.terrain in {"grass", "water", "concrete"}
            assert q.occupied_with in {0, 1, 2, 3, 4}

    def test_repr_de_cada_ocupacao(self):
        esperado = {
            0: "\U0001F6B7",   # inacessivel
            1: "\U0001F334",   # terreno livre
            2: "\U0001F994",   # pokemon selvagem
            3: "\U000026D4",   # pokebola
            4: "\U0001F94A",   # CPU
            -1: "\U00002705",  # ja visitado
        }
        q = main.GridSquare()
        for codigo, emoji in esperado.items():
            q.occupied_with = codigo
            assert repr(q) == emoji

    def test_terrain_e_sorteado_mas_nunca_lido_pelo_jogo(self):
        """O peso do grafo (fase 2) ja existe no jogo: o campo esta la e
        ninguem consome. Se algum dia alguem passar a ler, este teste vira
        documentacao do ponto de partida."""
        assert hasattr(main.GridSquare(), "terrain")


class TestGrid:
    def test_dimensao_e_posicao_inicial(self):
        main.player1 = main.Player()
        g = main.Grid()
        assert len(g.grid) == 8
        assert all(len(linha) == 8 for linha in g.grid)
        assert (g.row_pos, g.col_pos) == (0, 0)

    def test_celula_inicial_guarda_um_player_e_nao_um_gridsquare(self):
        """BUG (fase 1): `self.grid[0][0] = GridSquare.occupied_with = player1`
        coloca um Player dentro da matriz. Qualquer varredura que espere um
        GridSquare em toda celula quebra aqui."""
        main.player1 = main.Player()
        g = main.Grid()
        assert g.grid[0][0] is main.player1
        assert not isinstance(g.grid[0][0], main.GridSquare)

    def test_construir_o_grid_suja_o_atributo_de_classe_do_gridsquare(self):
        """BUG (fase 1): a mesma linha faz `GridSquare.occupied_with = player1`,
        mudando o default de TODAS as celulas criadas depois."""
        main.player1 = main.Player()
        assert "occupied_with" not in main.GridSquare.__dict__
        main.Grid()
        assert main.GridSquare.occupied_with is main.player1

    def test_print_grid_imprime_oito_linhas(self, capsys):
        main.player1 = main.Player()
        main.Grid().print_grid()
        assert len(capsys.readouterr().out.strip().splitlines()) == 8
