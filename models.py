"""Entidades do jogo: Pokemon, Player e CpuPlayer."""
import random
from dataclasses import dataclass, field


def _genero_aleatorio():
    return random.choice(['Male', 'Female'])


@dataclass
class Pokemon:
    name: str = 'PokeMon'
    gender: str = field(default_factory=_genero_aleatorio)
    type_of_pokemon: str = "Rando"
    nature: str = 'normal'
    moves: dict[str, int] = field(default_factory=dict)
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
    gender: str = field(default_factory=_genero_aleatorio)
    nature: str = 'Fun'
    pokemon_list: list[Pokemon] = field(default_factory=list)
    bag: dict[str, int] = field(default_factory=dict)
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

    @property
    def lider(self):
        """O pokemon que entra na batalha, ou None se o time acabou."""
        return self.pokemon_list[0] if self.pokemon_list else None

    def __repr__(self): return "\U0001FAE1"


def _nome_de_cpu():
    return random.choice(['Jenny', 'James', 'Jamal', 'Drizzy', 'Sam', 'Rachel'])


def _premio_de_cpu():
    return random.randint(10000, 100000)


@dataclass
class CpuPlayer:
    name: str = field(default_factory=_nome_de_cpu)
    pokemon: Pokemon = field(default_factory=generate_rand_pokemon)
    cash_award: int = field(default_factory=_premio_de_cpu)
    poke_gift: Pokemon | None = None
    fact: str = ""

    def __post_init__(self):
        # poke_gift e o mesmo objeto de pokemon, como no jogo original.
        if self.poke_gift is None:
            self.poke_gift = self.pokemon
        # fact precisa do nome ja sorteado desta instancia, entao so pode ser
        # montado aqui: como default de campo ele congelava o primeiro nome
        # da execucao e todo CPU se apresentava com o nome errado.
        if not self.fact:
            self.fact = f"My name is {self.name}, get ready to battle me!"
