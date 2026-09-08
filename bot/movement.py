"""Conversao de caminhos do grafo para comandos do jogo."""

import game


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


def executar_caminho(
    mapa, player, caminho, automatico: bool = False, visual: bool = False,
    ao_passo=None,
) -> list[game.Movimento]:
    """Executa um caminho e devolve o resultado de cada tentativa de passo.

    `ao_passo`, quando dado, e chamado com (movimento, direcao) logo depois de
    cada passo. Existe para quem precisa acompanhar a partida enquanto ela
    acontece, em vez de receber a lista no fim: a interface web transmite o bot
    andando por esse gancho. Sem ele, nada muda.
    """
    movimentos = []
    for direcao in caminho_para_direcoes(caminho):
        movimento = game.mover(mapa, player, direcao, automatico=automatico)
        movimentos.append(movimento)
        if ao_passo is not None:
            ao_passo(movimento, direcao)
        if visual:
            mapa.print_grid()
        if not movimento.valido:
            break
        # Partida encerrada para o caminho na hora, seja por derrota (time
        # zerado) ou por VITORIA (time cheio). A checagem so existia entre
        # planos, e como um caminho do DFS tem dezenas de passos, o bot
        # continuava jogando um jogo ja ganho: em 30x30, 80% dos passos do DFS
        # aconteciam depois da vitoria, com as batalhas e o HP perdido ali
        # entrando no benchmark como se fossem consequencia da rota.
        if game.partida_encerrada(player):
            break
    return movimentos