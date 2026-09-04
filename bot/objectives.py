"""Escolha e ordenação de objetivos alcançáveis para o bot."""

from dataclasses import dataclass
from itertools import permutations
import math

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


def matriz_distancias(pontos, mapa, estado) -> dict:
    """Calcula os menores custos entre cada par de pontos do planejamento."""
    matriz = {}
    for origem in pontos:
        distancias, _ = dijkstra_distancias(origem, mapa, estado)
        matriz[origem] = {
            destino: distancias.get(destino, math.inf)
            for destino in pontos
        }
    return matriz


def melhor_ordem(origem, alvos, mapa, estado) -> tuple[list[tuple[int, int]], float, dict]:
    """Escolhe a permutação de alvos com menor custo total desde a origem."""
    pontos = [origem, *alvos]
    matriz = matriz_distancias(pontos, mapa, estado)
    melhor = None

    for permutacao in permutations(alvos):
        sequencia = (origem, *permutacao)
        custo = sum(
            matriz[anterior][proximo]
            for anterior, proximo in zip(sequencia, sequencia[1:])
        )
        if math.isinf(custo):
            continue
        chave = (custo, permutacao)
        if melhor is None or chave < melhor[0]:
            melhor = (chave, list(permutacao), custo)

    if melhor is None:
        return [], math.inf, matriz
    return melhor[1], melhor[2], matriz