"""Regras da partida: movimento, batalha, itens e criacao do jogador."""
import random

from rich import print

import state
from grid import Grid, GridSquare
from models import CpuPlayer, Player, Pokemon, generate_rand_pokemon


# Dont need to keep track of visited cells, but could be good practice to use the grid teq mentioned by professor.
def traverse_grid(grid):  # 0 = cant access, 1 =  empty land, 2 = pokemon, 3 = pokeball, 4 = CPU
    grid.print_grid()
    dir_row, dir_col = [-1, 0, 1, 0], [0, 1, 0, -1]  # North[0], east[1], south[2], west[3]
    made_move = False
    while made_move is False:
        direction = input("Do you want to go W (up), A (left), S (down), or D (right)? ")
        if direction.upper() == 'W':  # north
            rr = grid.row_pos + dir_row[0]
            cc = grid.col_pos + dir_col[0]
        if direction.upper() == 'D':
            rr = grid.row_pos + dir_row[1]
            cc = grid.col_pos + dir_col[1]
        if direction.upper() == 'S':
            rr = grid.row_pos + dir_row[2]
            cc = grid.col_pos + dir_col[2]
        if direction.upper() == 'A':
            rr = grid.row_pos + dir_row[3]
            cc = grid.col_pos + dir_col[3]
        if rr < 0 or cc < 0 or rr >= 8 or cc >= 8 or grid.grid[rr][
            cc].occupied_with == 0:  # 8 is size of rows and cols or edge of grid
            direction = input("You cannot move there. Try again, Enter W/A/S/D to move in a different direction: ")
        else:
            if grid.grid[rr][cc].occupied_with == 4:
                battle(state.player1, 'cpu')
            if grid.grid[rr][cc].occupied_with == 3:
                state.player1.bag['pokeball'] += 1
                print("Sweet, you found a pokeball!!", "[red]")
            if grid.grid[rr][cc].occupied_with == 2:
                battle(state.player1, 'wild pokemon')
            grid.grid[grid.row_pos][grid.col_pos] = GridSquare()
            grid.grid[grid.row_pos][grid.col_pos].occupied_with = -1
            grid.grid[rr][cc] = state.player1
            grid.row_pos, grid.col_pos = rr, cc
            made_move = True


def throw_pokeball(player, pokemon):
    player.bag['pokeball'] -= 1
    if pokemon.health >= 50:
        if random.random() < .35:
            print(f'Congrats, you captured {pokemon.type_of_pokemon}! His name is {pokemon.name}.')
            player.pokemon_list.append(pokemon)
            return True
        else:
            print(f'You did not capture {pokemon.type_of_pokemon}!')
            return False
    elif pokemon.health < 50:
        if random.random() <= .70:
            print(f'Congrats, you captured {pokemon.type_of_pokemon}! His name is {pokemon.name}.')
            player.pokemon_list.append(pokemon)
            return True
        else:
            print(f'You did not capture {pokemon.type_of_pokemon}!')
            return False


def use_potion(player: Player, pokemon: Pokemon):
    if player.bag['potion'] > 0:
        player.bag['potion'] -= 1
        pokemon.health += 40
        print(f'{pokemon.name} now has {pokemon.health} health!')
    else:
        print("You do not have any more potions!")


def battle(player: Player, opp: str):
    """Batalha contra um CPU ou um pokemon selvagem.

    O `except:` nu que existia aqui engolia qualquer erro e imprimia
    "Your done with this battle!", escondendo bug de verdade. Saiu na fase 1:
    agora a condicao de parada do laco e explicita (time vazio encerra) e o
    que quebrar sobe.

    O que ele estava escondendo, e que continua de pe: o prompt monta
    `list(pokemon.moves.keys())[1]`, ou seja, exige que todo pokemon tenha ao
    menos dois golpes. Em partida normal isso vale (iniciais e sorteados vem
    sempre com dois), mas um Pokemon() sem golpes quebra aqui. Quando a fase 5
    automatizar a escolha de acao, e esse ponto que precisa deixar de assumir
    a quantidade de golpes.
    """
    cpu = None
    if opp == 'cpu':
        cpu = CpuPlayer()
        print(cpu.fact)
        print(f'You will be starting the battle with {player.pokemon_list[0].name} (a {player.pokemon_list[0].type_of_pokemon}), and battling {cpu.pokemon.name} (a {cpu.pokemon.type_of_pokemon})')
        cpu_pokemon = cpu.pokemon
    else:
        cpu_pokemon = generate_rand_pokemon()
        print(f"Get ready fight a wild {cpu_pokemon.type_of_pokemon}!")
    print("You have the first move!")
    caught, run = False, False
    pokemon = player.lider  # We will always start a battle with your first pokemon.
    # O original testava `player.pokemon_list is not None`, que nunca e falso:
    # a lista fica vazia, nao vira None. Ficar sem pokemon nao encerrava o laco.
    while player.pokemon_list and cpu_pokemon.health > 0:
        if opp == 'cpu': move = input(f"Do you want to use move 1 {next(iter(pokemon.moves))} (1), move 2 {list(pokemon.moves.keys())[1]} (2), use a potion (P), switch pokemon (S), or run (R)? ")
        else: move = input(f"Do you want to use move 1 {next(iter(pokemon.moves))} (1), move 2 {list(pokemon.moves.keys())[1]} (2), use a potion (P), throw a pokeball (T), switch pokemon (S), or run (R)? ")

        if move == '1':
            cpu_pokemon.health -= list(pokemon.moves.values())[0]
            print(f"You hit them with {list(pokemon.moves.keys())[0]}. {cpu_pokemon.name} has {cpu_pokemon.health} health left")
            if cpu_pokemon.health <= 0: continue
        elif move == '2':
            cpu_pokemon.health -= list(pokemon.moves.values())[1]
            print(f"You hit them with {list(pokemon.moves.keys())[1]}. Their pokemon has {cpu_pokemon.health} health left")
            if cpu_pokemon.health <= 0: continue
        elif move.upper() == 'P':
            use_potion(player, pokemon)
        elif move.upper() == 'R':
            run = True
            break
        elif move.upper() == 'S':
            print(player.poke_list_names())
            change = input(f"Which pokemon do you want to switch to? ")
            pokemon = player.change_poke(change)
            print(f'{pokemon.name} has {pokemon.health} left. Get ready to fight!')
        elif move.upper() == 'T':
            caught = throw_pokeball(player, cpu_pokemon)
            if caught is True:
                break

        cpu_move = random.choice(list(cpu_pokemon.moves.keys()))
        pokemon.health -= cpu_pokemon.moves[cpu_move]
        print(f"You were hit with {cpu_move} for {cpu_pokemon.moves[cpu_move]} HP! {pokemon.name} has {pokemon.health} health left.")
        if pokemon.health <= 0:
            pokemon.health = 0
            use = input("Your pokemon is about to faint, do you want to use a potion? (Y or N)")
            if player.bag.get('potion', 0) > 0 and use.upper() == 'Y':
                use_potion(player, pokemon)
            else:
                rip = player.pokemon_list.pop(0)
                print(f"{rip.name} has fainted!")
                if player.lider is None:
                    break
                pokemon = player.lider
                print(f'You will now fight with {pokemon.name}!')

    if caught is False and run is False and player.pokemon_list:
        if opp == 'cpu':
            player.money += cpu.cash_award
            print(f"Good job, you defeated {cpu.name}'s! You won ${cpu.cash_award}")

        print(f"You defeated and won {cpu_pokemon.name}! Welcome your new pokemon to the crew.")
        cpu_pokemon.health = 100
        player.pokemon_list.append(cpu_pokemon)
    elif run is True:
        print("You ran from the battle!")


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


def playing_game(player):
    grid = Grid()
    while 0 < len(player.pokemon_list) < 4:
        traverse_grid(grid)
    if len(player.pokemon_list) >= 4:
        print(f"Game over! You captured 4 pokemon {player.poke_list_names()}. Thanks for playing!", ":smile:")
    else:
        print("Game over! You lost all of your pokemon. Thanks for playing!", ":smile:")
