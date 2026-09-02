"""
Created on Mon Feb 8
A Pokemon clone for the terminal.
@author: Andrew Alagna

Ponto de entrada. As regras vivem em game.py, o mapa em grid.py e as
entidades em models.py.
"""
from rich import print

import state
from game import playing_game, starting_player_info

# 0 = cant access, 1 =  empty land, 2 = pokemon, 3 = pokeball, 4 = CPU
if __name__ == "__main__":
    state.player1 = starting_player_info()
    print(f"Hello {state.player1.name}, get ready to play Pokemon Py!")
    playing_game(state.player1)
