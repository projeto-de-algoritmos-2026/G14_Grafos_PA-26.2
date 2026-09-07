"""Conversao de caminhos do grafo para comandos do jogo."""


DIRECAO_POR_DELTA = {
    (-1, 0): "W",
    (0, 1): "D",
    (1, 0): "S",
    (0, -1): "A",
}


def caminho_para_direcoes(caminho: list[tuple[int, int]]) -> list[str]:
    """Converte uma sequencia de posicoes em comandos W/A/S/D."""
    direcoes = []
    for atual, proxima in zip(caminho, caminho[1:]):
        delta = (proxima[0] - atual[0], proxima[1] - atual[1])
        try:
            direcoes.append(DIRECAO_POR_DELTA[delta])
        except KeyError as erro:
            raise ValueError(
                f"caminho possui trecho nao adjacente: {atual} -> {proxima}"
            ) from erro
    return direcoes