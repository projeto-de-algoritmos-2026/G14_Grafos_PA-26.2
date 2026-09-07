"""Experimento 1: rota pura.

Mesmo mapa, mesma origem, mesmo destino, mesmo estado. So o algoritmo muda.
E o unico recorte em que "o BFS anda menos passos e paga mais caro" pode ser
afirmado sem ressalva, porque nada alem da estrategia de busca varia entre as
tres medicoes de uma linha.

Duas escolhas de desenho que precisam estar no relatorio:

1. Os destinos sao sorteados dentro do componente alcancavel SEM surf. Como
   surf so acrescenta arestas, um destino escolhido assim continua alcancavel
   nos tres estados, e a mesma linha pode ser comparada entre eles. Sortear no
   componente com surf daria destino inalcancavel nas linhas sem surf.
2. Mapa cuja origem nasce cercada de agua nao entra: sem surf o componente e
   so {(0,0)} e nao existe destino nenhum. Esses mapas vao pra
   `rotas_descartes.csv` em vez de sumirem, porque a frequencia deles e
   resultado do trabalho (a agua de fato ilha a origem em boa parte das seeds
   pequenas), nao ruido a esconder.
"""

import argparse
import random
import time
from pathlib import Path

from graph.search import dijkstra_distancias
from graph.state import Estado
from grid import Grid

from .common import (
    ALGORITMOS,
    SAIDA_PADRAO,
    SEEDS,
    TAMANHOS,
    agrupar,
    escrever_csv,
    media,
)

ORIGEM = (0, 0)
DESTINOS_POR_MAPA = 3

# HP 40 encarece a grama (3 -> 5) sem mexer na topologia; surf cria as arestas
# de agua. Sao os dois jeitos distintos de o estado do jogador mudar o grafo,
# e o benchmark mede os dois.
ESTADOS = {
    "hp100": Estado(hp_lider=100),
    "hp40": Estado(hp_lider=40),
    "hp100_surf": Estado(hp_lider=100, surf=True),
}

CAMPOS = [
    "tamanho", "seed", "estado", "hp_lider", "surf", "destino",
    "algoritmo", "encontrou", "custo", "passos", "nos_expandidos", "tempo_ms",
]

CAMPOS_RESUMO = [
    "tamanho", "estado", "algoritmo", "execucoes",
    "custo_medio", "passos_medio", "nos_expandidos_medio", "tempo_ms_medio",
]

CAMPOS_DESCARTE = ["tamanho", "seed", "motivo"]


def sortear_destinos(mapa, quantidade=DESTINOS_POR_MAPA):
    """Destinos alcancaveis a partir de (0,0) sem surf, sorteio reproduzivel."""
    distancias, _ = dijkstra_distancias(ORIGEM, mapa, ESTADOS["hp100"])
    alcancaveis = sorted(posicao for posicao in distancias if posicao != ORIGEM)
    if not alcancaveis:
        return []
    rng = random.Random(f"{mapa.size}-{mapa.seed}")
    return rng.sample(alcancaveis, min(quantidade, len(alcancaveis)))


def medir(algoritmo, destino, mapa, estado, repeticoes=1):
    """Roda a busca e devolve (caminho, custo, nos, tempo em ms).

    O tempo e o MENOR de `repeticoes` execucoes, nao a media: o que se quer
    medir e o custo do algoritmo, e ruido de agendamento do sistema so
    consegue empurrar uma medicao pra cima.
    """
    melhor_tempo = None
    caminho = custo = nos = None
    for _ in range(max(1, repeticoes)):
        inicio = time.perf_counter()
        caminho, custo, nos = algoritmo(ORIGEM, destino, mapa, estado)
        decorrido = (time.perf_counter() - inicio) * 1000
        melhor_tempo = decorrido if melhor_tempo is None else min(melhor_tempo, decorrido)
    return caminho, custo, nos, melhor_tempo


def rodar(tamanhos=TAMANHOS, seeds=SEEDS, repeticoes=1):
    """Roda a grade inteira e devolve (linhas, descartes)."""
    linhas, descartes = [], []
    for tamanho in tamanhos:
        for seed in range(seeds):
            mapa = Grid(size=tamanho, seed=seed)
            destinos = sortear_destinos(mapa)
            if not destinos:
                descartes.append({
                    "tamanho": tamanho,
                    "seed": seed,
                    "motivo": "origem sem componente alcancavel sem surf",
                })
                continue
            for destino in destinos:
                for nome_estado, estado in ESTADOS.items():
                    for nome_algoritmo, algoritmo in ALGORITMOS.items():
                        caminho, custo, nos, tempo = medir(
                            algoritmo, destino, mapa, estado, repeticoes
                        )
                        linhas.append({
                            "tamanho": tamanho,
                            "seed": seed,
                            "estado": nome_estado,
                            "hp_lider": estado.hp_lider,
                            "surf": int(estado.surf),
                            "destino": f"{destino[0]}-{destino[1]}",
                            "algoritmo": nome_algoritmo,
                            "encontrou": int(bool(caminho)),
                            "custo": custo,
                            "passos": max(0, len(caminho) - 1),
                            "nos_expandidos": nos,
                            "tempo_ms": round(tempo, 4),
                        })
    return linhas, descartes


def resumir(linhas):
    """Média por (tamanho, estado, algoritmo). É o que alimenta os gráficos."""
    resumo = []
    for (tamanho, estado, algoritmo), grupo in agrupar(
        linhas, ["tamanho", "estado", "algoritmo"]
    ).items():
        resumo.append({
            "tamanho": tamanho,
            "estado": estado,
            "algoritmo": algoritmo,
            "execucoes": len(grupo),
            "custo_medio": media(grupo, "custo"),
            "passos_medio": media(grupo, "passos"),
            "nos_expandidos_medio": media(grupo, "nos_expandidos"),
            "tempo_ms_medio": media(grupo, "tempo_ms"),
        })
    return resumo


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark de rota pura (fase 6)")
    parser.add_argument("--tamanhos", type=int, nargs="+", default=list(TAMANHOS))
    parser.add_argument("--seeds", type=int, default=SEEDS)
    parser.add_argument("--repeticoes", type=int, default=1)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args(argv)

    linhas, descartes = rodar(args.tamanhos, args.seeds, args.repeticoes)
    escrever_csv(args.saida / "rotas.csv", CAMPOS, linhas)
    escrever_csv(args.saida / "rotas_resumo.csv", CAMPOS_RESUMO, resumir(linhas))
    escrever_csv(args.saida / "rotas_descartes.csv", CAMPOS_DESCARTE, descartes)
    print(f"rotas: {len(linhas)} medicoes, {len(descartes)} mapas descartados -> {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
