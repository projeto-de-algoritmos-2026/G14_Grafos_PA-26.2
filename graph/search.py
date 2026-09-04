"""Algoritmos de busca sobre o grafo do mapa."""

from collections import deque
import heapq
import math
from itertools import count

from .adapter import arestas, vizinhos


def _custo_do_caminho(caminho, grid, estado):
    """Soma o custo de entrar em cada célula depois da origem."""
    return sum(dict(arestas(posicao_anterior, grid, estado))[posicao]
               for posicao_anterior, posicao in zip(caminho, caminho[1:]))


def _reconstruir(came_from, destino):
    caminho = [destino]
    while caminho[-1] in came_from:
        caminho.append(came_from[caminho[-1]])
    caminho.reverse()
    return caminho


def dfs_path(origem, destino, grid, estado):
    """Encontra um caminho com busca em profundidade."""
    pilha = [(origem, [origem])]
    visitados = {origem}
    nos_expandidos = 0

    while pilha:
        atual, caminho = pilha.pop()
        nos_expandidos += 1
        if atual == destino:
            return caminho, _custo_do_caminho(caminho, grid, estado), nos_expandidos

        for vizinho in reversed(vizinhos(atual, grid, estado)):
            if vizinho not in visitados:
                visitados.add(vizinho)
                pilha.append((vizinho, caminho + [vizinho]))

    return [], math.inf, nos_expandidos


def bfs_path(origem, destino, grid, estado):
    """Encontra o caminho com menos passos usando busca em largura."""
    fila = deque([origem])
    came_from = {}
    visitados = {origem}
    nos_expandidos = 0

    while fila:
        atual = fila.popleft()
        nos_expandidos += 1
        if atual == destino:
            caminho = _reconstruir(came_from, destino)
            return caminho, _custo_do_caminho(caminho, grid, estado), nos_expandidos

        for vizinho in vizinhos(atual, grid, estado):
            if vizinho not in visitados:
                visitados.add(vizinho)
                came_from[vizinho] = atual
                fila.append(vizinho)

    return [], math.inf, nos_expandidos


def dijkstra(origem, destino, grid, estado):
    """Encontra o caminho de menor custo usando Dijkstra."""
    distancias = {origem: 0}
    came_from = {}
    ordem = count()
    fila = [(0, next(ordem), origem)]
    nos_expandidos = 0

    while fila:
        custo_atual, _, atual = heapq.heappop(fila)
        if custo_atual != distancias.get(atual):
            continue

        nos_expandidos += 1
        if atual == destino:
            caminho = _reconstruir(came_from, destino)
            return caminho, custo_atual, nos_expandidos

        for vizinho, custo in arestas(atual, grid, estado):
            novo_custo = custo_atual + custo
            if novo_custo < distancias.get(vizinho, math.inf):
                distancias[vizinho] = novo_custo
                came_from[vizinho] = atual
                heapq.heappush(fila, (novo_custo, next(ordem), vizinho))

    return [], math.inf, nos_expandidos