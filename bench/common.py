"""Peças compartilhadas pelos dois experimentos da fase 6."""

import csv
import io
import contextlib
from pathlib import Path
from statistics import mean

from graph.search import bfs_path, dfs_path, dijkstra

TAMANHOS = (8, 15, 30)
SEEDS = 30

# A ordem importa: e a ordem das colunas dos resumos e das series dos
# graficos, e o DFS vem primeiro porque e o piso da comparacao.
ALGORITMOS = {
    "dfs": dfs_path,
    "bfs": bfs_path,
    "dijkstra": dijkstra,
}

SAIDA_PADRAO = Path(__file__).resolve().parent / "out"


@contextlib.contextmanager
def silencioso():
    """Engole o que o jogo imprime.

    O `battle()` do jogo narra a partida inteira no terminal, e uma grade de
    270 partidas enterraria qualquer saida do benchmark. O texto e descartado,
    nao redirecionado pra arquivo: nada nele vira metrica.
    """
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def escrever_csv(caminho: Path, campos: list[str], linhas: list[dict]) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)
    return caminho


def ler_csv(caminho: Path) -> list[dict]:
    with Path(caminho).open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def agrupar(linhas: list[dict], chaves: list[str]) -> dict:
    """Agrupa linhas por uma tupla de colunas, preservando a ordem de chegada."""
    grupos: dict = {}
    for linha in linhas:
        grupos.setdefault(tuple(linha[chave] for chave in chaves), []).append(linha)
    return grupos


def media(linhas: list[dict], coluna: str) -> float:
    """Média de uma coluna, ignorando o que não for número.

    Linha sem caminho guarda custo infinito, e infinito contamina a média
    inteira. O resumo conta essas linhas à parte, na coluna `execucoes`.
    """
    valores = [float(linha[coluna]) for linha in linhas
               if linha[coluna] not in ("", "inf", "-inf", "nan")]
    return round(mean(valores), 3) if valores else 0.0
