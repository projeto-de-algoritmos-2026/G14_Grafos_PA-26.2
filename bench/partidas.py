"""Experimento 2: partida completa.

O bot da fase 5 joga do inicio ao fim e a rota de cada objetivo e calculada
pelo algoritmo em teste. O que se mede aqui nao e a rota, e a CONSEQUENCIA
dela na partida: quantas batalhas o caminho forcou, quanto HP custou, quantos
objetivos deram tempo de concluir.

Tres avisos que precisam ir pro relatorio junto com os numeros:

1. A escolha dos objetivos e sempre a da fase 4 (score por Dijkstra), nos tres
   casos. So a rota ate o alvo muda. Trocar as duas coisas ao mesmo tempo
   tornaria impossivel dizer de onde veio a diferenca.
2. O mapa muda durante a partida (celula visitada perde a penalidade de
   batalha, surf abre a agua, HP cai e encarece a grama), entao os custos
   daqui NAO sao comparaveis com os de `bench.rotas`.
3. A batalha sorteia dano. A semente global e fixada por partida, entao os
   tres algoritmos comecam com o mesmo fluxo de aleatoriedade, mas eles se
   separam assim que o numero de batalhas diverge. Diferenca de HP entre
   algoritmos e tendencia sobre 30 seeds, nao resultado exato de uma linha.
"""

import argparse
import random
import time
from pathlib import Path

from grid import Grid
from models import Player, generate_rand_pokemon

from bot.runner import executar_bot

from .common import (
    ALGORITMOS,
    SAIDA_PADRAO,
    SEEDS,
    TAMANHOS,
    agrupar,
    escrever_csv,
    media,
    silencioso,
)

# Teto de seguranca. O DFS pode devolver rota que passeia pelo mapa inteiro, e
# sem teto uma partida ruim segura a grade toda.
PASSOS_POR_CELULA = 10

CAMPOS = [
    "tamanho", "seed", "algoritmo", "objetivos_concluidos", "passos",
    "custo_planejado", "nos_expandidos", "replanejamentos", "batalhas",
    "hp_perdido", "pokebolas", "pegou_surf", "tempo_ms", "motivo_parada",
]

CAMPOS_RESUMO = [
    "tamanho", "algoritmo", "execucoes", "objetivos_medio", "passos_medio",
    "custo_planejado_medio", "nos_expandidos_medio", "batalhas_medio",
    "hp_perdido_medio", "tempo_ms_medio", "partidas_sem_objetivo",
]


def novo_jogador():
    """Jogador de benchmark: um inicial sorteado e a mochila do jogo."""
    return Player(
        name="Bot",
        pokemon_list=[generate_rand_pokemon()],
        bag={"pokeball": 3, "potion": 3},
    )


def rodar_partida(tamanho, seed, algoritmo):
    """Uma partida do bot com um algoritmo de rota. Devolve a linha do CSV."""
    # Mesma semente global pros tres algoritmos: o inicial sorteado e o
    # primeiro dano da primeira batalha sao iguais em todos.
    random.seed(f"{tamanho}-{seed}")
    mapa = Grid(size=tamanho, seed=seed)
    player = novo_jogador()

    inicio = time.perf_counter()
    with silencioso():
        resultado = executar_bot(
            mapa,
            player,
            max_passos=PASSOS_POR_CELULA * tamanho * tamanho,
            buscar=ALGORITMOS[algoritmo],
        )
    tempo = (time.perf_counter() - inicio) * 1000

    movimentos = resultado.movimentos
    return {
        "tamanho": tamanho,
        "seed": seed,
        "algoritmo": algoritmo,
        "objetivos_concluidos": len(resultado.objetivos_visitados),
        "passos": len(movimentos),
        "custo_planejado": resultado.custo_planejado,
        "nos_expandidos": resultado.nos_expandidos,
        "replanejamentos": resultado.replanejamentos,
        "batalhas": sum(1 for movimento in movimentos if movimento.batalhou),
        "hp_perdido": sum(movimento.hp_perdido for movimento in movimentos),
        "pokebolas": sum(1 for movimento in movimentos if movimento.pegou_pokebola),
        "pegou_surf": int(any(movimento.pegou_surf for movimento in movimentos)),
        "tempo_ms": round(tempo, 4),
        "motivo_parada": resultado.motivo_parada,
    }


def rodar(tamanhos=TAMANHOS, seeds=SEEDS):
    linhas = []
    for tamanho in tamanhos:
        for seed in range(seeds):
            for algoritmo in ALGORITMOS:
                linhas.append(rodar_partida(tamanho, seed, algoritmo))
    return linhas


def resumir(linhas):
    """Média por (tamanho, algoritmo).

    `partidas_sem_objetivo` conta a parte que a média esconde: partida em que
    a origem nasceu ilhada e o bot parou sem sair do lugar. Media de zero
    objetivo puxa toda a coluna pra baixo, e sem esse contador ninguem sabe se
    o algoritmo foi ruim ou se o mapa nao deixou jogar.
    """
    resumo = []
    for (tamanho, algoritmo), grupo in agrupar(linhas, ["tamanho", "algoritmo"]).items():
        resumo.append({
            "tamanho": tamanho,
            "algoritmo": algoritmo,
            "execucoes": len(grupo),
            "objetivos_medio": media(grupo, "objetivos_concluidos"),
            "passos_medio": media(grupo, "passos"),
            "custo_planejado_medio": media(grupo, "custo_planejado"),
            "nos_expandidos_medio": media(grupo, "nos_expandidos"),
            "batalhas_medio": media(grupo, "batalhas"),
            "hp_perdido_medio": media(grupo, "hp_perdido"),
            "tempo_ms_medio": media(grupo, "tempo_ms"),
            "partidas_sem_objetivo": sum(
                1 for linha in grupo if int(linha["objetivos_concluidos"]) == 0
            ),
        })
    return resumo


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark de partida completa (fase 6)")
    parser.add_argument("--tamanhos", type=int, nargs="+", default=list(TAMANHOS))
    parser.add_argument("--seeds", type=int, default=SEEDS)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args(argv)

    linhas = rodar(args.tamanhos, args.seeds)
    escrever_csv(args.saida / "partidas.csv", CAMPOS, linhas)
    escrever_csv(args.saida / "partidas_resumo.csv", CAMPOS_RESUMO, resumir(linhas))
    print(f"partidas: {len(linhas)} execucoes -> {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
