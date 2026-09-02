"""O mapa do jogo: a celula (GridSquare) e a matriz (Grid)."""
import random

from rich import print

# Conteudo possivel de uma celula.
INACESSIVEL = 0
LIVRE = 1
POKEMON = 2
POKEBOLA = 3
CPU = 4
VISITADO = -1

EMOJI = {
    INACESSIVEL: "\U0001F6B7",
    LIVRE: "\U0001F334",
    POKEMON: "\U0001F994",
    POKEBOLA: "\U000026D4",
    CPU: "\U0001F94A",
    VISITADO: "\U00002705",
}

EMOJI_JOGADOR = "\U0001FAE1"

# Peso de terreno usado pelo custo do grafo na fase 2. O jogo ja sorteava o
# terreno e nunca lia esse campo.
TERRENOS = ['grass', 'water', 'concrete']


class GridSquare:
    OPCOES = [INACESSIVEL, LIVRE, POKEMON, POKEBOLA, CPU]
    DISTRIBUICAO = [.02, .60, .13, .05, .10]

    def __init__(self, rng=None):
        """rng permite reproduzir um mapa: veja Grid(size, seed)."""
        rng = rng or random
        self.terrain = rng.choice(TERRENOS)
        self.occupied_with = rng.choices(self.OPCOES, self.DISTRIBUICAO)[0]

    @property
    def acessivel(self):
        return self.occupied_with != INACESSIVEL

    def __repr__(self):
        return EMOJI.get(self.occupied_with, "")


class Grid:
    def __init__(self, size=8, seed=None):
        """size e seed sao o que torna o benchmark da fase 6 reproduzivel.

        O RNG e proprio do Grid: dois mapas com a mesma seed sao iguais mesmo
        que outra parte do programa sorteie coisas entre a criacao dos dois.
        """
        self.size = size
        self.seed = seed
        self.rng = random.Random(seed)
        self.grid = [[GridSquare(self.rng) for _ in range(size)] for _ in range(size)]
        # A posicao de partida precisa ser pisavel, e o jogador NAO mora dentro
        # da matriz: a posicao dele vive so em row_pos/col_pos.
        self.grid[0][0].occupied_with = LIVRE
        self.row_pos, self.col_pos = 0, 0

    @property
    def posicao(self):
        return self.row_pos, self.col_pos

    def dentro(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    def celula(self, row, col):
        return self.grid[row][col]

    def desenhar(self):
        """Devolve o mapa como texto, com o jogador desenhado na posicao dele."""
        linhas = []
        for r, linha in enumerate(self.grid):
            simbolos = []
            for c, celula in enumerate(linha):
                if (r, c) == self.posicao:
                    simbolos.append(EMOJI_JOGADOR)
                else:
                    simbolos.append(str(celula))
            linhas.append(" ".join(simbolos))
        return "\n".join(linhas)

    def print_grid(self):
        print(self.desenhar())
