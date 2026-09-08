"""Traducao do trabalho para JSON.

Funcoes puras, sem HTTP: `server.py` e so a casca que as chama. Assim a
serializacao inteira e testavel sem abrir socket.
"""

import queue
import random
import threading
import time

import grid as grid_mod
from bench.common import ALGORITMOS, silencioso
# o jogador vem do benchmark, nao de uma copia local: se os dois divergirem, a
# partida da tela deixa de ser a partida medida, e ninguem percebe
from bench.partidas import novo_jogador
from bot.objectives import planejar_visita, pontuar_alvos
from bot.runner import executar_bot
from graph.search import dijkstra_distancias
from graph.state import Estado
from grid import Grid


# Nome legivel de cada conteudo de celula. A pagina desenha a partir do nome,
# nunca do numero: o inteiro e detalhe interno do grid.
CONTEUDO = {
    grid_mod.INACESSIVEL: "bloqueio",
    grid_mod.LIVRE: "livre",
    grid_mod.POKEMON: "pokemon",
    grid_mod.POKEBOLA: "pokebola",
    grid_mod.CPU: "cpu",
    grid_mod.SURF: "surf",
    grid_mod.VISITADO: "visitado",
}

MAX_TAMANHO = 40
MAX_SEED = 10 ** 6


def limitar(valor, minimo, maximo, padrao):
    """Mantem um parametro de query dentro de faixa util.

    A demo roda numa maquina so, mas a URL e digitavel: size=100000 travaria o
    processo inteiro no meio da apresentacao.
    """
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, numero))


def estado_de(hp=100, surf=False, pokebolas=3, pocoes=3):
    return Estado(hp_lider=hp, pokebolas=pokebolas, pocoes=pocoes, surf=bool(surf))


def serializar_celula(celula):
    return {
        "terreno": celula.terrain,
        "conteudo": CONTEUDO.get(celula.occupied_with, "livre"),
        "pisavel_sem_surf": celula.pisavel(False),
        "pisavel_com_surf": celula.pisavel(True),
    }


def serializar_grid(mapa):
    return {
        "size": mapa.size,
        "seed": mapa.seed,
        "posicao": list(mapa.posicao),
        "celulas": [[serializar_celula(c) for c in linha] for linha in mapa.grid],
    }


def dados_mapa(size, seed, hp=100, surf=False):
    """O mapa, mais o que e alcancavel a partir da origem no estado dado.

    A alcancabilidade vem junto porque e o fato que explica a tela: celula
    cinza nao e bug de desenho, e vertice fora do componente da origem.
    """
    mapa = Grid(size=size, seed=seed)
    estado = estado_de(hp, surf)
    distancias, _ = dijkstra_distancias(mapa.posicao, mapa, estado)
    return {
        **serializar_grid(mapa),
        "estado": {"hp_lider": estado.hp_lider, "surf": estado.surf},
        "alcancaveis": [[r, c] for (r, c) in sorted(distancias)],
        "distancias": {f"{r}-{c}": d for (r, c), d in distancias.items()},
        "itens_surf": _itens_de_surf(mapa, set(distancias)),
    }


def _itens_de_surf(mapa, alcancaveis):
    """Onde estao os itens de Surf e se da pra chegar neles SEM Surf.

    E a pergunta que decide se a demonstracao do Surf e possivel naquela seed.
    A fase 2 mediu que em boa parte dos mapas o item nasce fora do componente
    da origem, e nesse caso ninguem pega: o jogador comeca sem Surf, e sem
    Surf a agua e parede. Isso e resultado do trabalho, nao defeito da demo,
    entao a interface diz em vez de esconder.
    """
    itens = [
        (linha, coluna)
        for linha in range(mapa.size)
        for coluna in range(mapa.size)
        if mapa.celula(linha, coluna).occupied_with == grid_mod.SURF
    ]
    return [
        {"posicao": [linha, coluna], "alcancavel": (linha, coluna) in alcancaveis}
        for linha, coluna in itens
    ]


# Fracao minima do mapa que precisa estar ao alcance da origem pra seed valer
# como demonstracao. Sem esse piso a busca devolve mapas em que o item de Surf
# e pegavel mas o componente inteiro tem meia duzia de celulas: tecnicamente
# atende o pedido e nao da pra jogar nem mostrar rota nenhuma.
COMPONENTE_MINIMO = 0.25


def procurar_seed_com_surf(size, de=0, tentativas=500, componente_minimo=COMPONENTE_MINIMO):
    """Primeira seed, a partir de `de`, com item de Surf pegavel e mapa jogavel.

    Existe porque sem ela a mecanica mais importante da modelagem (o atributo
    que CRIA aresta) fica indemonstravel: o item pode cair num componente
    separado da origem, e ai ninguem chega nele.
    """
    estado = estado_de(100, False)
    piso = max(4, int(size * size * componente_minimo))
    for seed in range(de, de + tentativas):
        mapa = Grid(size=size, seed=seed)
        distancias, _ = dijkstra_distancias(mapa.posicao, mapa, estado)
        alcancaveis = set(distancias)
        if len(alcancaveis) < piso:
            continue
        itens = _itens_de_surf(mapa, alcancaveis)
        if any(item["alcancavel"] for item in itens):
            return {
                "encontrou": True,
                "size": size,
                "seed": seed,
                "itens": itens,
                "alcancaveis": len(alcancaveis),
                "fracao_alcancavel": round(len(alcancaveis) / (size * size), 3),
                "procuradas": seed - de + 1,
            }
    return {"encontrou": False, "size": size, "procuradas": tentativas}


def dados_objetivos(size, seed, hp=100, surf=False, limite=3):
    """Quem a fase 4 escolheu, e em que ordem visitar.

    Alimenta as marcas no mapa: numero dourado nos escolhidos, com a ordem de
    visita, e contorno tracejado em quem disputou e perdeu no score.
    """
    mapa = Grid(size=size, seed=seed)
    estado = estado_de(hp, surf)

    candidatos = pontuar_alvos(mapa.posicao, mapa, estado)
    ordem, custo_total, _ = planejar_visita(mapa.posicao, mapa, estado, limite=limite)
    posicoes_ordem = [list(p) for p in ordem]

    return {
        "size": size,
        "seed": seed,
        "origem": list(mapa.posicao),
        "estado": {"hp_lider": estado.hp_lider, "surf": estado.surf},
        "candidatos": [
            {
                "posicao": list(objetivo.posicao),
                "conteudo": CONTEUDO.get(
                    mapa.celula(*objetivo.posicao).occupied_with, "livre"),
                "utilidade": objetivo.utilidade,
                "distancia": objetivo.distancia,
                "score": round(objetivo.score, 4),
                "selecionado": list(objetivo.posicao) in posicoes_ordem,
                "visita": (posicoes_ordem.index(list(objetivo.posicao)) + 1
                           if list(objetivo.posicao) in posicoes_ordem else None),
            }
            for objetivo in candidatos
        ],
        "ordem": posicoes_ordem,
        "custo_total": None if custo_total == float("inf") else custo_total,
    }


def dados_rota(size, seed, destino, algoritmos=None, hp=100, surf=False):
    """Roda os algoritmos pedidos na MESMA rota e devolve um por chave.

    E a comparacao do trabalho em uma chamada: mesma origem, mesmo destino,
    mesmo estado, so o algoritmo muda.
    """
    mapa = Grid(size=size, seed=seed)
    estado = estado_de(hp, surf)
    escolhidos = [a for a in (algoritmos or list(ALGORITMOS)) if a in ALGORITMOS]

    saida = {}
    for nome in escolhidos:
        inicio = time.perf_counter()
        caminho, custo, nos = ALGORITMOS[nome](mapa.posicao, tuple(destino), mapa, estado)
        decorrido = (time.perf_counter() - inicio) * 1000
        saida[nome] = {
            "encontrou": bool(caminho),
            "caminho": [list(p) for p in caminho],
            "custo": None if not caminho else custo,
            "passos": max(0, len(caminho) - 1),
            "nos_expandidos": nos,
            "tempo_ms": round(decorrido, 4),
        }
    return {
        "size": size, "seed": seed,
        "origem": list(mapa.posicao), "destino": list(destino),
        "estado": {"hp_lider": estado.hp_lider, "surf": estado.surf},
        "rotas": saida,
    }


def _situacao(player):
    """Fim de partida pela regra do jogo, nao por uma regra propria da web.

    `game.partida_encerrada` e a mesma funcao que para o bot. Se a web tivesse
    a sua propria copia, a pagina estaria demonstrando um jogo com regra
    diferente da que o trabalho mede.
    """
    motivo = game.partida_encerrada(player)
    if not motivo:
        return "jogando", ""
    return ("derrota" if motivo == "sem pokemon" else "vitoria"), motivo


def _resumo_jogador(player):
    situacao, motivo = _situacao(player)
    return {
        "situacao": situacao,
        "motivo": motivo,
        "meta": game.POKEMON_PARA_VENCER,
        "pokemon": len(player.pokemon_list),
        "hp_lider": player.lider.health if player.lider else 0,
        "nome_lider": player.lider.name if player.lider else None,
        "pokebolas": player.bag.get("pokeball", 0),
        "surf": player.surf,
    }


def eventos_partida(size, seed, algoritmo, max_passos=None):
    """Gera os eventos de uma partida do bot ENQUANTO ela acontece.

    O bot roda numa thread e empurra evento por gancho (`ao_planejar` e
    `ao_passo`); este gerador drena a fila. Nao ha replay: o passo chega na
    pagina depois de `game.mover()` ter sido chamado de verdade, e nao antes.
    """
    # A MESMA semeadura do `bench.partidas.rodar_partida`. Sem ela o `seed` da
    # tela controla so o mapa: o dado da batalha continua saindo do estado
    # global do `random`, e duas execucoes com os mesmos parametros dao
    # partidas diferentes. Com ela, o que aparece na tela e a mesma partida que
    # o benchmark mediu, e um resultado visto na apresentacao pode ser
    # reproduzido depois.
    random.seed(f"{size}-{seed}")
    mapa = Grid(size=size, seed=seed)
    player = novo_jogador()
    fila: queue.Queue = queue.Queue()

    yield "inicio", {
        **serializar_grid(mapa),
        "algoritmo": algoritmo,
        "jogador": _resumo_jogador(player),
    }

    # O bot replaneja a cada objetivo, e o motivo nunca e "porque sim": alguma
    # coisa mudou no grafo desde o plano anterior. Isso e apurado aqui, no
    # servidor, comparando o estado antes e depois, e nao deduzido na tela.
    desde_o_plano = {"batalhas": 0, "hp_perdido": 0, "surf": False,
                     "pokebola": False, "visitadas": 0, "chegou": False}
    anterior = {"hp": player.lider.health if player.lider else 0, "surf": player.surf}

    def motivos_do_replanejamento():
        if not any(desde_o_plano.values()):
            return ["primeiro plano da partida"]
        motivos = []
        if desde_o_plano["chegou"]:
            motivos.append("objetivo anterior alcancado: a utilidade daquela celula zerou")
        if desde_o_plano["surf"]:
            motivos.append("pegou Surf: a agua deixou de ser parede e virou aresta, "
                           "o grafo mudou de FORMA")
        hp_agora = player.lider.health if player.lider else 0
        if hp_agora < anterior["hp"]:
            motivos.append(f"HP do lider caiu de {anterior['hp']} para {hp_agora}: "
                           "a grama encareceu, o grafo mudou de PESO")
        if desde_o_plano["visitadas"]:
            motivos.append(f"{desde_o_plano['visitadas']} celulas viraram visitadas e "
                           "perderam a penalidade de batalha, entao ficaram mais baratas")
        return motivos or ["o estado do jogador mudou"]

    def ao_planejar(destino, caminho, custo, nos):
        fila.put(("plano", {
            "destino": list(destino),
            "caminho": [list(p) for p in caminho],
            "custo": custo,
            "nos_expandidos": nos,
            "motivos": motivos_do_replanejamento(),
        }))
        anterior["hp"] = player.lider.health if player.lider else 0
        anterior["surf"] = player.surf
        for chave in desde_o_plano:
            desde_o_plano[chave] = False if isinstance(desde_o_plano[chave], bool) else 0

    def ao_passo(movimento, direcao):
        if movimento.valido:
            desde_o_plano["visitadas"] += 1
            desde_o_plano["batalhas"] += 1 if movimento.batalhou else 0
            desde_o_plano["hp_perdido"] += movimento.hp_perdido
            desde_o_plano["surf"] = desde_o_plano["surf"] or movimento.pegou_surf
            desde_o_plano["pokebola"] = desde_o_plano["pokebola"] or movimento.pegou_pokebola
            desde_o_plano["chegou"] = True
        fila.put(("passo", {
            "direcao": direcao,
            "posicao": list(movimento.posicao),
            "valido": movimento.valido,
            "motivo": movimento.motivo,
            "batalhou": movimento.batalhou,
            "pegou_pokebola": movimento.pegou_pokebola,
            "pegou_surf": movimento.pegou_surf,
            "hp_perdido": movimento.hp_perdido,
            "jogador": _resumo_jogador(player),
        }))

    resultado = {}

    def rodar():
        try:
            with silencioso():
                r = executar_bot(
                    mapa, player,
                    max_passos=max_passos or 10 * size * size,
                    buscar=ALGORITMOS[algoritmo],
                    ao_planejar=ao_planejar,
                    ao_passo=ao_passo,
                )
            resultado["fim"] = {
                "algoritmo": algoritmo,
                "objetivos_concluidos": len(r.objetivos_visitados),
                "objetivos": [list(p) for p in r.objetivos_visitados],
                "passos": len(r.movimentos),
                "custo_planejado": r.custo_planejado,
                "nos_expandidos": r.nos_expandidos,
                "replanejamentos": r.replanejamentos,
                "batalhas": sum(1 for m in r.movimentos if m.batalhou),
                "hp_perdido": sum(m.hp_perdido for m in r.movimentos),
                "motivo_parada": r.motivo_parada,
                "jogador": _resumo_jogador(player),
            }
        except Exception as erro:  # a pagina precisa saber, nao ficar girando
            resultado["fim"] = {"algoritmo": algoritmo, "erro": repr(erro)}
        finally:
            fila.put((None, None))

    thread = threading.Thread(target=rodar, daemon=True)
    thread.start()
    while True:
        evento, dados = fila.get()
        if evento is None:
            break
        yield evento, dados
    thread.join()
    yield "fim", resultado["fim"]


# ---------------------------------------------------------------------------
# Modo humano
#
# O bot demonstra o jogo funcionando, mas so de um jeito. Pra alguem poder
# pegar o teclado e andar, o servidor precisa guardar a partida: quem resolve
# um passo e `game.mover()`, e ele muda grid, HP, mochila e batalha. Manter
# isso no navegador seria reescrever a regra do jogo em JavaScript, que e
# exatamente o que este pacote nao faz.
#
# A sessao vive em memoria e morre com o processo. E demo de uso local, nao
# tem login, nao tem persistencia e nao precisa ter.
# ---------------------------------------------------------------------------

import secrets
import threading

import game

_sessoes: dict[str, dict] = {}
_tranca = threading.Lock()
MAX_SESSOES = 20


def criar_jogo(size, seed):
    mapa = Grid(size=size, seed=seed)
    player = novo_jogador()
    identificador = secrets.token_hex(8)
    with _tranca:
        if len(_sessoes) >= MAX_SESSOES:
            # a mais antiga sai; ninguem volta pra uma partida abandonada
            _sessoes.pop(next(iter(_sessoes)))
        _sessoes[identificador] = {"mapa": mapa, "player": player}
    distancias, _ = dijkstra_distancias(mapa.posicao, mapa, Estado(hp_lider=100))
    return {
        "sessao": identificador,
        **serializar_grid(mapa),
        "alcancaveis": [[r, c] for (r, c) in sorted(distancias)],
        "itens_surf": _itens_de_surf(mapa, set(distancias)),
        "jogador": _resumo_jogador(player),
    }


def mover_jogo(identificador, direcao):
    with _tranca:
        sessao = _sessoes.get(identificador)
    if sessao is None:
        return {"erro": "sessao desconhecida, comece uma partida nova"}

    mapa, player = sessao["mapa"], sessao["player"]
    situacao, motivo = _situacao(player)
    if situacao != "jogando":
        return {"erro": f"partida encerrada ({motivo}), comece uma nova"}

    # automatico=True mesmo com humano no teclado. O `battle()` do jogo e um
    # laco interativo que le do stdin: chamado daqui, ele penduraria a conexao
    # esperando uma resposta que nunca chega. Quem anda e a pessoa; o combate
    # resolve sozinho, e a pagina diz isso em voz alta em vez de fingir que a
    # batalha foi jogada pelo jogador.
    with silencioso():
        movimento = game.mover(mapa, player, direcao, automatico=True)

    linha, coluna = movimento.posicao
    return {
        "valido": movimento.valido,
        "motivo": movimento.motivo,
        "posicao": [linha, coluna],
        "batalhou": movimento.batalhou,
        "pegou_pokebola": movimento.pegou_pokebola,
        "pegou_surf": movimento.pegou_surf,
        "hp_perdido": movimento.hp_perdido,
        # so a celula pisada muda de conteudo, entao o navegador nao precisa do
        # grid inteiro a cada tecla
        "celula": {
            "posicao": [linha, coluna],
            **serializar_celula(mapa.celula(linha, coluna)),
        },
        "jogador": _resumo_jogador(player),
    }
