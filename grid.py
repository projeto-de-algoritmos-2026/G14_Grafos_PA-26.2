"""O mapa do jogo: a celula (GridSquare) e a matriz (Grid)."""
import random

from rich import print

import state
from models import Player


class GridSquare:
    def __init__(self):
        possible_options = [0, 1, 2, 3, 4]  # 0 = cant access, 1 =  empty land, 2 = pokemon, 3 = pokeball, 4 = CPU
        distribution = [.02, .60, .13, .05, .10]
        self.terrain = random.choice(['grass', 'water', 'concrete'])
        self.occupied_with = random.choices(possible_options, distribution)[0]

    def __repr__(self):
        if self.occupied_with == 0: return "\U0001F6B7"
        if self.occupied_with == 1: return "\U0001F334"
        if self.occupied_with == 2: return '\U0001F994'
        if self.occupied_with == 3: return "\U000026D4"
        if self.occupied_with == 4: return "\U0001F94A"
        if self.occupied_with == Player: return "\U0001FAE1"
        if self.occupied_with == -1: return "\U00002705"


class Grid:
    def __init__(self):
        self.grid = [[GridSquare() for i in range(8)] for i in range(8)]
        self.grid[0][0] = GridSquare.occupied_with = state.player1  # The starting player is represented as 9, and visited squares will be marked as -1.
        self.row_pos, self.col_pos = 0, 0

    def print_grid(self):
        for row in self.grid:
            print(" ".join(map(str, row)))
