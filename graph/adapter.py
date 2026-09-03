"""A ponte entre a matriz do jogo e o grafo.

Nenhum algoritmo da fase 3 sabe o que e um GridSquare: eles falam com
vizinhos() e arestas(). E aqui tambem que fica a decisao que sustenta a tese
do trabalho: surf nao muda o peso da agua, ele CRIA as arestas de agua.

Sao dois grafos sobre a mesma matriz:
- G_sem_surf, onde toda celula de agua e parede. Pode ser desconexo, e nesse
  caso "nao existe caminho" e o resultado correto do algoritmo, nao uma falha
  do mapa. Nao ha nenhuma tentativa de garantir que o item de surf nasca no
  componente da origem (decisao do Lucas).
- G_surf, onde a agua e travessia caro mas legal.

vizinhos() FILTRA o que e intransponivel em vez de devolver tudo com peso
infinito. Assim DFS, BFS e Dijkstra ficam sem nenhum `if peso == inf`.
"""
from game import DIRECOES

from .cost import custo_entrada


def vizinhos(pos, grid, estado):
    """Celulas alcancaveis em um passo a partir de pos, na ordem W, D, S, A.

    A ordem e fixa pra que DFS e BFS sejam reproduziveis: mudar a ordem de
    exploracao muda o caminho que o DFS encontra, e o benchmark da fase 6
    precisa comparar execucoes iguais.
    """
    row, col = pos
    saida = []
    for d_linha, d_coluna in DIRECOES.values():
        rr, cc = row + d_linha, col + d_coluna
        if not grid.dentro(rr, cc):
            continue
        if not grid.celula(rr, cc).pisavel(estado.surf):
            continue
        saida.append((rr, cc))
    return saida


def arestas(pos, grid, estado):
    """(vizinho, custo_de_entrar_nele) para cada vizinho de pos.

    E o que o Dijkstra consome. Existe pra que ninguem precise casar vizinhos()
    com custo_entrada() na mao e errar o par.
    """
    return [((rr, cc), custo_entrada(grid.celula(rr, cc), estado))
            for rr, cc in vizinhos(pos, grid, estado)]
