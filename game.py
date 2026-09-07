"""Regras da partida: movimento, batalha e itens.

mover() nao le do teclado: recebe a direcao pronta e devolve o que aconteceu.
Quem conversa com o jogador e ui.py. Assim o bot da fase 5 dirige o movimento
por codigo e o benchmark da fase 6 conta metricas por passo.

Ressalva de escopo: battle() ainda le do teclado. O plano so pede o
traverse_grid nesta fase, entao a batalha ficou como estava; quando o bot
tiver que atravessar uma celula com CPU ou pokemon selvagem, a fase 5 vai
precisar decidir como automatizar essas escolhas.
"""
import random
from dataclasses import dataclass

from rich import print

import grid as grid_mod
from models import CpuPlayer, Player, Pokemon, generate_rand_pokemon

# Tecla -> deslocamento (linha, coluna).
DIRECOES = {
    'W': (-1, 0),
    'D': (0, 1),
    'S': (1, 0),
    'A': (0, -1),
}


@dataclass
class Movimento:
    """O que aconteceu numa tentativa de passo.

    E o contrato que o bot (fase 5) e o benchmark (fase 6) consomem: sem isso
    os dois teriam que espiar o estado do jogador antes e depois de cada passo
    pra descobrir se houve batalha ou quanto HP se perdeu.
    """
    valido: bool
    posicao: tuple[int, int]
    motivo: str = ""
    batalhou: bool = False
    pegou_pokebola: bool = False
    pegou_surf: bool = False
    hp_perdido: int = 0


def mover(grid, player: Player, direcao: str, automatico: bool = False) -> Movimento:
    """Tenta mover o jogador uma casa na direcao dada (W, A, S ou D)."""
    tecla = direcao.upper() if direcao else ""
    if tecla not in DIRECOES:
        return Movimento(False, grid.posicao, motivo="direcao desconhecida")

    d_linha, d_coluna = DIRECOES[tecla]
    rr, cc = grid.row_pos + d_linha, grid.col_pos + d_coluna

    if not grid.dentro(rr, cc):
        return Movimento(False, grid.posicao, motivo="fora do mapa")

    destino = grid.celula(rr, cc)
    if not destino.acessivel:
        return Movimento(False, grid.posicao, motivo="celula inacessivel")
    # Agua e recusada aqui desde a fase 2. Antes o jogo deixava andar em cima
    # dela (acessivel so olha o conteudo da celula, e agua e terreno), o que
    # faria o bot planejar rota por um caminho que o grafo diz nao existir.
    if not destino.pisavel(player.surf):
        return Movimento(False, grid.posicao, motivo="agua sem surf")

    hp_antes = player.lider.health if player.lider else 0
    batalhou = False
    pegou_pokebola = False
    pegou_surf = False

    if destino.occupied_with == grid_mod.CPU:
        if automatico:
            battle(player, 'cpu', automatico=True)
        else:
            battle(player, 'cpu')
        batalhou = True
    elif destino.occupied_with == grid_mod.POKEBOLA:
        player.bag['pokeball'] = player.bag.get('pokeball', 0) + 1
        pegou_pokebola = True
    elif destino.occupied_with == grid_mod.SURF:
        player.surf = True
        pegou_surf = True
    elif destino.occupied_with == grid_mod.POKEMON:
        if automatico:
            battle(player, 'wild pokemon', automatico=True)
        else:
            battle(player, 'wild pokemon')
        batalhou = True

    destino.occupied_with = grid_mod.VISITADO
    grid.row_pos, grid.col_pos = rr, cc

    hp_depois = player.lider.health if player.lider else 0
    return Movimento(
        valido=True,
        posicao=(rr, cc),
        batalhou=batalhou,
        pegou_pokebola=pegou_pokebola,
        pegou_surf=pegou_surf,
        hp_perdido=max(0, hp_antes - hp_depois),
    )


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
    else:
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


def battle(player: Player, opp: str, automatico: bool = False):
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
        if automatico:
            if not pokemon.moves:
                run = True
                break
            move = '1'
        elif opp == 'cpu': move = input(f"Do you want to use move 1 {next(iter(pokemon.moves))} (1), move 2 {list(pokemon.moves.keys())[1]} (2), use a potion (P), switch pokemon (S), or run (R)? ")
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
            use = 'N' if automatico else input("Your pokemon is about to faint, do you want to use a potion? (Y or N)")
            if not automatico and player.bag.get('potion', 0) > 0 and use.upper() == 'Y':
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
