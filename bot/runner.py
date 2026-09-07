"""Loop de planejamento e execucao do bot."""

from dataclasses import dataclass, field

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


def executar_bot(mapa, player, limite_objetivos=3, max_passos=None) -> ResultadoBot:
    """Planeja, executa um objetivo e replaneja ate a partida parar."""
    resultado = ResultadoBot()
    passos = 0

    while player.pokemon_list and len(player.pokemon_list) < 4:
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
            break

        destino = ordem[0]
        caminho, _, _ = dijkstra(mapa.posicao, destino, mapa, estado)
        if not caminho:
            resultado.motivo_parada = "objetivo sem caminho"
            break

        movimentos = executar_caminho(mapa, player, caminho, automatico=True)
        resultado.movimentos.extend(movimentos)
        passos += len(movimentos)

        if not movimentos or not movimentos[-1].valido:
            resultado.motivo_parada = "movimento invalido"
            break
        if mapa.posicao != destino:
            resultado.motivo_parada = "caminho interrompido"
            break

        resultado.objetivos_visitados.append(destino)

    if not resultado.motivo_parada:
        if not player.pokemon_list:
            resultado.motivo_parada = "sem pokemon"
        elif len(player.pokemon_list) >= 4:
            resultado.motivo_parada = "quatro pokemon capturados"

    return resultado