"""Loop de planejamento e execucao do bot."""

from dataclasses import dataclass, field

import game
from grid import Grid
from graph.search import dijkstra
from graph.state import Estado

from .movement import executar_caminho
from .objectives import planejar_visita


@dataclass
class ResultadoBot:
    """Resumo de uma execucao do bot para a UI e o benchmark."""

    movimentos: list = field(default_factory=list)
    objetivos_visitados: list[tuple[int, int]] = field(default_factory=list)
    replanejamentos: int = 0
    motivo_parada: str = ""
    # Somas das buscas de rota, que a fase 6 compara entre algoritmos. Ficam
    # aqui porque so o loop ve todas as chamadas: quem olha de fora enxerga o
    # resultado final da partida, nao o custo de cada replanejamento.
    custo_planejado: float = 0.0
    nos_expandidos: int = 0


def executar_bot(
    mapa,
    player,
    limite_objetivos=3,
    max_passos=None,
    visual: bool = False,
    buscar=dijkstra,
    ao_planejar=None,
    ao_passo=None,
) -> ResultadoBot:
    """Planeja, executa um objetivo e replaneja ate a partida parar.

    `buscar` e a funcao de rota, com a assinatura da fase 3
    (origem, destino, grid, estado) -> (caminho, custo, nos_expandidos).
    O default e o Dijkstra; o benchmark da fase 6 troca por dfs_path e
    bfs_path pra medir a mesma partida com rotas diferentes.

    A ESCOLHA dos objetivos continua sendo a da fase 4 (score por Dijkstra)
    em qualquer caso. E de proposito: trocar os dois de uma vez mistura duas
    variaveis e nao da pra dizer se a diferenca veio da rota ou do alvo.

    `ao_planejar(destino, caminho, custo, nos)` e `ao_passo(movimento, direcao)`
    sao ganchos de observacao, chamados enquanto a partida acontece. A interface
    web transmite o bot por eles, em vez de reproduzir um resultado pronto. Sem
    eles o comportamento e identico.
    """
    resultado = ResultadoBot()
    passos = 0

    if visual:
        print("Mapa inicial:")
        mapa.print_grid()

    while not game.partida_encerrada(player):
        if max_passos is not None and passos >= max_passos:
            resultado.motivo_parada = "limite de passos"
            break

        estado = Estado.de(player)
        ordem, _, _ = planejar_visita(
            mapa.posicao, mapa, estado, limite=limite_objetivos
        )
        resultado.replanejamentos += 1
        if not ordem:
            resultado.motivo_parada = "sem objetivos alcançaveis"
            if visual:
                print("Nenhum objetivo alcançavel a partir da posicao atual.")
            break

        destino = ordem[0]
        caminho, custo, nos = buscar(mapa.posicao, destino, mapa, estado)
        resultado.nos_expandidos += nos
        if not caminho:
            resultado.motivo_parada = "objetivo sem caminho"
            break
        resultado.custo_planejado += custo
        if ao_planejar is not None:
            ao_planejar(destino, caminho, custo, nos)

        if visual:
            print(f"\nPlano: {mapa.posicao} -> {destino}")
            print(f"Caminho: {caminho}")
            mapa.print_grid()

        movimentos = executar_caminho(
            mapa, player, caminho, automatico=True, visual=visual, ao_passo=ao_passo
        )
        resultado.movimentos.extend(movimentos)
        passos += len(movimentos)

        if mapa.posicao == destino:
            resultado.objetivos_visitados.append(destino)

        # O fim de partida e checado ANTES dos motivos de caminho. Vencer no
        # meio de uma rota corta o caminho, e sem esta ordem o resultado diria
        # "caminho interrompido" numa partida que na verdade foi ganha.
        encerrada = game.partida_encerrada(player)
        if encerrada:
            resultado.motivo_parada = encerrada
            break
        if not movimentos or not movimentos[-1].valido:
            resultado.motivo_parada = "movimento invalido"
            break
        if mapa.posicao != destino:
            resultado.motivo_parada = "caminho interrompido"
            break

    resultado.motivo_parada = resultado.motivo_parada or game.partida_encerrada(player)
    return resultado


def jogar_com_bot(
    player, size=8, seed=None, max_passos=None, visual: bool = False, buscar=dijkstra,
    ao_planejar=None, ao_passo=None,
) -> ResultadoBot:
    """Cria o mapa e executa uma partida controlada pelo bot."""
    mapa = Grid(size=size, seed=seed)
    return executar_bot(mapa, player, max_passos=max_passos, visual=visual,
                        buscar=buscar, ao_planejar=ao_planejar, ao_passo=ao_passo)
