"""
Created on Mon Feb 8
A Pokemon clone for the terminal.
@author: Andrew Alagna

Ponto de entrada. As regras vivem em game.py, o mapa em grid.py, as entidades
em models.py e a conversa com o jogador em ui.py.
"""
import argparse

from rich import print

from bot.runner import jogar_com_bot
from ui import playing_game, starting_player_info


def parse_args():
    p = argparse.ArgumentParser(description="Pokemon Py")
    p.add_argument("--size", type=int, default=8, help="lado do mapa quadrado")
    p.add_argument("--seed", type=int, default=None, help="semente do mapa, para reproduzir uma partida")
    modos = p.add_mutually_exclusive_group()
    modos.add_argument("--bot", action="store_true", help="joga automaticamente")
    modos.add_argument("--human", action="store_true", help="joga com comandos no terminal")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    player = starting_player_info()
    print(f"Hello {player.name}, get ready to play Pokemon Py!")
    if args.bot:
        resultado = jogar_com_bot(player, size=args.size, seed=args.seed)
        print(
            f"Bot finished: {len(resultado.objetivos_visitados)} objectives, "
            f"{len(resultado.movimentos)} steps ({resultado.motivo_parada})."
        )
    else:
        playing_game(player, size=args.size, seed=args.seed)
