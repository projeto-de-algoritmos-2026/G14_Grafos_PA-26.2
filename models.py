"""Entidades do jogo: Pokemon, Player e CpuPlayer."""
import random
from dataclasses import dataclass, field


@dataclass
class Pokemon:
    name: str = 'PokeMon'
    gender: str = random.choice(['Male', 'Female'])
    type_of_pokemon: str = "Rando"
    nature: str = 'normal'
    moves: dict[str:int] = field(default_factory=dict)
    health: int = 100


def generate_rand_pokemon():
    fuego = Pokemon('fuego', 'female', "Charzard", 'Fire', {'Flamethrower': 20, 'Claw': 15})
    rocko = Pokemon('rocky', 'male', 'Geodude', 'Rock', {'Rock-throw': 20, 'head-butt': 15})
    mew = Pokemon('mew', 'neutral', 'Mew', 'Psychic', {'Mind-beam': 20, 'Psychic-slam': 25})
    snore = Pokemon('snore', 'male', 'Snorlax', 'Normal', {'Body-slam': 20, 'Slap': 15})
    rocky = Pokemon('rocky', 'female', 'Onyx', 'Normal', {'Body-slam': 20, 'Slap': 15})
    coolio = Pokemon('coolio', 'male', 'Squirtle', 'Water', {"Hydropump": 35, 'Bite': 20})
    charred = Pokemon('charred', 'female', 'Charmander', 'Fire', {'Bite': 20, 'Fire-blast': 25})
    return random.choice([fuego, rocko, mew, snore, rocky, coolio, charred])


@dataclass
class Player:
    name: str = "Player"
    gender: str = random.choice(['Male', 'Female'])
    nature: str = 'Fun'
    pokemon_list: list[Pokemon] = field(default_factory=list)
    bag: dict[str:int] = field(default_factory=dict)
    money: int = 10000

    def poke_list_names(self):
        names = []
        for poke in self.pokemon_list:
            names.append(poke.name)
        return names

    def change_poke(self, name):
        names = self.poke_list_names()
        ind = names.index(name)
        return self.pokemon_list[ind]

    def __repr__(self): return "\U0001FAE1"


@dataclass
class CpuPlayer:
    name: str = random.choice(['Jenny', 'James', 'Jamal', 'Drizzy', 'Sam', 'Rachel'])
    pokemon: Pokemon = field(default_factory=generate_rand_pokemon)
    cash_award: int = random.randint(10000, 100000)
    poke_gift: Pokemon | None = None
    fact: str = f"My name is {name}, get ready to battle me!"

    def __post_init__(self):
        # No original, poke_gift era o MESMO objeto de pokemon (poke_gift: Pokemon = pokemon).
        # Mantemos esse aliasing por instancia em vez de sortear um segundo pokemon.
        if self.poke_gift is None:
            self.poke_gift = self.pokemon
