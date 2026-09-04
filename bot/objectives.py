"""Escolha de objetivos alcançáveis para o bot."""

from dataclasses import dataclass

import grid as grid_mod

from graph.search import dijkstra_distancias


UTILIDADES = {
    grid_mod.POKEMON: 100,
    grid_mod.CPU: 80,
    grid_mod.POKEBOLA: 60,
    grid_mod.SURF: 90,
}


@dataclass(frozen=True)
class Objetivo:
    posicao: tuple[int, int]
    utilidade: int
    distancia: int
    score: float


def utilidade(celula, estado) -> int:
    """Retorna o benefício de visitar uma célula no estado atual."""
    if celula.occupied_with == grid_mod.SURF and estado.surf:
        return 0
    return UTILIDADES.get(celula.occupied_with, 0)


def pontuar_alvos(origem, mapa, estado) -> list[Objetivo]:
    """Calcula score para cada objetivo alcançável no mapa."""
    distancias, _ = dijkstra_distancias(origem, mapa, estado)
    objetivos = []

    for posicao, distancia in distancias.items():
        if posicao == origem:
            continue
        valor = utilidade(mapa.celula(*posicao), estado)
        if valor == 0:
            continue
        objetivos.append(Objetivo(posicao, valor, distancia, valor / distancia))

    return sorted(
        objetivos,
        key=lambda objetivo: (-objetivo.score, objetivo.distancia, objetivo.posicao),
    )


def selecionar_alvos(origem, mapa, estado, limite=3) -> list[tuple[int, int]]:
    """Seleciona até ``limite`` objetivos pela maior utilidade por custo."""
    return [objetivo.posicao for objetivo in pontuar_alvos(origem, mapa, estado)[:limite]]