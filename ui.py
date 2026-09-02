"""Camada de interacao com o jogador humano.

Tudo que le do teclado e escreve na tela durante a exploracao mora aqui. O
game.py nao sabe que existe terminal, e e isso que permite o bot da fase 5
jogar a mesma partida sem ninguem digitando.
"""
import random

from rich import print

from game import DIRECOES, mover
from grid import Grid
from models import Player, Pokemon

PROMPT_DIRECAO = "Do you want to go W (up), A (left), S (down), or D (right)? "
PROMPT_ERRO = "You cannot move there. Try again, Enter W/A/S/D to move in a different direction: "


def passo_do_jogador(grid, player):
    """Pede direcoes ate uma valer, aplica e devolve o Movimento.

    No original, a resposta dada ao prompt de erro era descartada: o laco
    voltava ao prompt do topo e sobrescrevia a direcao antes de usa-la. Aqui a
    resposta ao prompt de erro e a proxima tentativa de verdade.
    """
    grid.print_grid()
    prompt = PROMPT_DIRECAO
    while True:
        direcao = input(prompt)
        movimento = mover(grid, player, direcao)
        if movimento.valido:
            if movimento.pegou_pokebola:
                print("Sweet, you found a pokeball!!", "[red]")
            return movimento
        prompt = PROMPT_ERRO


def starting_player_info():
    player_name = input("Hello there! What is your name?: ")
    gender = input("What is your gender?: ")
    nature = input("How would you describe your nature?: ")
    starter_pokemon = input("Which pokemon do you want to start with? P - Pikachu, C - Charmander, or S - Squirtle?: ")
    starter_pokemon = choose_starter_pokemon(starter_pokemon)
    return Player(player_name, gender, nature, [starter_pokemon], {'potion': 3, 'pokeball': 3}, 10000)


def choose_starter_pokemon(starter_pokemon):
    while starter_pokemon is None and starter_pokemon[0].upper() != 'P' and starter_pokemon[0].upper() != 'C' and \
            starter_pokemon[0].upper() != 'S':
        starter_pokemon = input("Please enter the first letter P (Pikachu) , C (Charmander), or S (Squirtle) to choose "
                                "your starter pokemon")
    name = input('What do you want to name your pokemon?: ')
    if starter_pokemon == 'P' or starter_pokemon[0].upper() == 'P':
        return Pokemon(name, random.choice(["Male", "Female"]), "Pikachu", 'Electric', {'Shock': 40, 'Tail Whip': 25})
    elif starter_pokemon == 'C' or starter_pokemon[0].upper() == 'C':
        return Pokemon(name, random.choice(["Male", "Female"]), "Charmander", 'Fire', {'Flamethrower': 40, 'Claw': 25})
    elif starter_pokemon == 'S' or starter_pokemon[0].upper() == 'S':
        return Pokemon(name, random.choice(["Male", "Female"]), "Squirtle", 'Water', {'Hydropump': 40, 'Tackle': 25})


def playing_game(player, size=8, seed=None):
    grid = Grid(size=size, seed=seed)
    while 0 < len(player.pokemon_list) < 4:
        passo_do_jogador(grid, player)
    if len(player.pokemon_list) >= 4:
        print(f"Game over! You captured 4 pokemon {player.poke_list_names()}. Thanks for playing!", ":smile:")
    else:
        print("Game over! You lost all of your pokemon. Thanks for playing!", ":smile:")
