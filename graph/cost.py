"""Custo de ENTRAR numa celula.

Modelagem que vai no relatorio: o custo depende so do destino, nunca de onde
se veio. Isso e caminho minimo com peso em VERTICE, e converte direto para
peso em ARESTA: toda aresta que chega em v pesa custo_entrada(v, estado).

Recompensa nao entra aqui. Dijkstra nao aceita aresta negativa, entao pokebola
custa o terreno e o beneficio dela vive no score do objetivo (fase 4).
"""
import math

import grid as grid_mod

# Concreto e a referencia de custo 1. Agua custa 4 e so e alcancavel com surf,
# mas quem decide se a aresta existe e o adapter, nao este modulo.
CUSTO_CONCRETO = 1
CUSTO_AGUA = 4
CUSTO_GRAMA_BASE = 3

# Batalha forcada. O premio do CPU e maior, e por isso a penalidade tambem.
PENALIDADE_CONTEUDO = {
    grid_mod.POKEMON: 8,
    grid_mod.CPU: 12,
}


def custo_grama(hp_lider: int) -> int:
    """Grama encarece conforme o HP do lider cai: o risco de encontro pesa mais
    quando o time esta ferido.

    custo = CUSTO_GRAMA_BASE * (1 + (100 - hp) / 100), arredondado.

    HP 100 -> 3, HP 50 -> 5, HP 0 -> 6.

    Duas travas:
    - O HP e limitado a [0, 100] AQUI, nao no jogo. use_potion() soma 40 sem
      teto, e com HP 140 a formula daria 2, ou seja grama mais barata que
      concreto. A poca continua curando acima de 100; o custo e que ignora.
    - O arredondamento e floor(x + 0.5), nao round(): round() do Python
      arredonda 4.5 para 4 (banker's rounding), e a tabela do relatorio nao
      vai depender de qual metade o interpretador escolhe.
    """
    hp = min(100, max(0, hp_lider))
    bruto = CUSTO_GRAMA_BASE * (1 + (100 - hp) / 100)
    return math.floor(bruto + 0.5)


def custo_terreno(celula, estado) -> int:
    if celula.terrain == grid_mod.AGUA:
        return CUSTO_AGUA
    if celula.terrain == grid_mod.GRAMA:
        return custo_grama(estado.hp_lider)
    return CUSTO_CONCRETO


def custo_entrada(celula, estado) -> int:
    """Peso da aresta que entra nesta celula, dado o estado do jogador.

    Levanta ValueError em celula intransponivel: quem filtra e vizinhos(), e
    receber celula impisavel aqui e sinal de que alguem furou o adapter. O
    contrato e esse pra que os tres algoritmos da fase 3 nunca precisem tratar
    peso infinito.

    Celula VISITADO nao cobra penalidade de batalha: a batalha ja aconteceu na
    primeira passagem. Consequencia util pro bot: o custo de uma celula so cai
    com o tempo, entao rota planejada nunca fica invalida por tras.
    """
    if not celula.pisavel(estado.surf):
        raise ValueError(
            "custo_entrada recebeu celula intransponivel; use vizinhos() para filtrar"
        )
    return custo_terreno(celula, estado) + PENALIDADE_CONTEUDO.get(celula.occupied_with, 0)


# Exportado pra quem quiser representar "sem caminho" sem reimportar math.
INFINITO = math.inf
