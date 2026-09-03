"""O estado do jogador visto pelo grafo.

Por que existe um objeto separado, em vez de passar o Player: o custo de uma
celula e funcao pura do par (celula, estado), e o Dijkstra da fase 3 nao pode
ver o estado mudar no meio da varredura. Estado e frozen justamente pra tornar
isso impossivel de acontecer por acidente.

Efeito colateral bom: o teste de grafo monta um Estado direto, sem precisar de
Player nem de Pokemon, e a fase 6 varre estados sinteticos (HP 100, 40, 10)
sem simular partida.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Estado:
    hp_lider: int
    pokebolas: int = 0
    pocoes: int = 0
    surf: bool = False

    @classmethod
    def de(cls, player):
        """Tira um retrato do Player. Mudancas posteriores nele nao chegam aqui."""
        return cls(
            hp_lider=player.lider.health if player.lider else 0,
            pokebolas=player.bag.get('pokeball', 0),
            pocoes=player.bag.get('potion', 0),
            surf=player.surf,
        )
