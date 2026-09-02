"""
Created on Mon Feb 8
A Pokemon clone for the terminal.
@author: Andrew Alagna

Ponto de entrada. As regras vivem em game.py, o mapa em grid.py, as entidades
em models.py e a conversa com o jogador em ui.py.
"""
import argparse

from rich import print

from ui import playing_game, starting_player_info


def parse_args():
    p = argparse.ArgumentParser(description="Pokemon Py")
    p.add_argument("--size", type=int, default=8, help="lado do mapa quadrado")
    p.add_argument("--seed", type=int, default=None, help="semente do mapa, para reproduzir uma partida")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    player = starting_player_info()
    print(f"Hello {player.name}, get ready to play Pokemon Py!")
    playing_game(player, size=args.size, seed=args.seed)
