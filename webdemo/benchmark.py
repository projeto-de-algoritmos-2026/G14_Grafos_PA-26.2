"""A corrida do benchmark, tres processos de verdade.

Por que processo e nao thread: os tres algoritmos sao Python puro, e sob o GIL
tres threads nao correm, se revezam. A tela mostraria uma corrida e o tempo
dela nao significaria nada. Com um processo por algoritmo, a raia que termina
primeiro terminou primeiro, e o numero projetado aguenta a pergunta da banca.

A grade e a mesma de `bench.rotas`: mesmos mapas, mesmos destinos sorteados,
mesmos estados. O que muda e que cada processo roda so o seu algoritmo, em vez
de os tres em sequencia. O sorteio de destino chama `dijkstra_distancias` uma
vez por mapa em TODOS os processos, entao esse custo de preparo e identico nas
tres raias e nao favorece ninguem.
"""

import multiprocessing as mp
import time

from bench.common import ALGORITMOS, TAMANHOS, SEEDS
from bench.partidas import rodar_partida
from bench.rotas import ESTADOS, medir, sortear_destinos
from grid import Grid

# Rotulo e chave de cada numero mostrado na raia. O rotulo diz "medio" de
# proposito: numero solto numa tela grande e lido como valor daquela execucao,
# e todo numero daqui e media sobre a grade.
METRICAS = {
    "rotas": [
        ("custo medio", "custo_medio"),
        ("passos medios", "passos_medio"),
        ("nos medios", "nos_medio"),
    ],
    "partidas": [
        ("objetivos medios", "objetivos_medio"),
        # o custo tambem aparece aqui: e a ponte entre os dois experimentos, e
        # sem ele a tela da partida nao mostra a grandeza que o trabalho mede.
        # E o custo PLANEJADO, somado das rotas que o bot mandou executar, nao
        # o da tabela de rota pura: o mapa muda durante a partida.
        ("custo planejado medio", "custo_medio"),
        ("batalhas medias", "batalhas_medio"),
        ("HP perdido medio", "hp_perdido_medio"),
    ],
}

DESCRICAO = {
    "rotas": "rota pura: mesma origem, mesmo destino, mesmo estado",
    "partidas": "partida completa: o bot joga do inicio ao fim",
    "ambos": ("cada raia roda os dois experimentos: primeiro a rota pura, "
              "depois a partida completa"),
}


def _medias(experimento, somas, amostra):
    """Converte as somas acumuladas nos numeros que a raia mostra."""
    return [
        {"rotulo": rotulo,
         "valor": round(somas.get(chave, 0) / amostra, 2) if amostra else 0}
        for rotulo, chave in METRICAS[experimento]
    ]


def _trabalhar_rotas(algoritmo, tamanhos, seeds, repeticoes, fila):
    """Grade de rota pura, identica a de `bench.rotas`, so para um algoritmo.

    `repeticoes` e o mesmo parametro de `bench.rotas.medir`: cada rota e
    calculada N vezes e vale a MENOR. Subir esse numero melhora a medicao de
    tempo (ruido de agendamento so empurra pra cima) e, de quebra, e o que da
    a corrida uma duracao visivel: com repeticoes=1 a grade inteira acaba em
    menos de meio segundo.
    """
    funcao = ALGORITMOS[algoritmo]
    inicio = time.perf_counter()
    feitos = amostra = 0
    somas = {"custo_medio": 0.0, "passos_medio": 0.0, "nos_medio": 0.0}
    total = len(tamanhos) * seeds

    for tamanho in tamanhos:
        for seed in range(seeds):
            mapa = Grid(size=tamanho, seed=seed)
            destinos = sortear_destinos(mapa)
            feitos += 1
            for destino in destinos:
                for estado in ESTADOS.values():
                    caminho, custo, nos, _ = medir(
                        funcao, destino, mapa, estado, repeticoes
                    )
                    amostra += 1
                    somas["nos_medio"] += nos
                    if caminho:
                        somas["custo_medio"] += custo
                        somas["passos_medio"] += len(caminho) - 1
            fila.put({
                "tipo": "progresso",
                "algoritmo": algoritmo,
                "tamanho": tamanho,
                "seed": seed,
                "mapas_feitos": feitos,
                "mapas_total": total,
                "amostra": amostra,
                "unidade": "medicoes de rota",
                "medias": _medias("rotas", somas, amostra),
                "decorrido_s": round(time.perf_counter() - inicio, 3),
            })

    fila.put({
        "tipo": "fim",
        "algoritmo": algoritmo,
        "amostra": amostra,
        "unidade": "medicoes de rota",
        "mapas_total": total,
        "medias": _medias("rotas", somas, amostra),
        "decorrido_s": round(time.perf_counter() - inicio, 3),
    })


def _trabalhar_partidas(algoritmo, tamanhos, seeds, repeticoes, fila):
    """Grade de partida completa, identica a de `bench.partidas`.

    E o unico experimento em que "objetivo" existe: na rota pura nao ha
    objetivo nenhum, so origem e destino. `repeticoes` nao se aplica aqui, uma
    partida nao se repete sem mudar de estado.
    """
    inicio = time.perf_counter()
    feitos = 0
    somas = {"objetivos_medio": 0.0, "custo_medio": 0.0,
             "batalhas_medio": 0.0, "hp_perdido_medio": 0.0}
    total = len(tamanhos) * seeds

    for tamanho in tamanhos:
        for seed in range(seeds):
            linha = rodar_partida(tamanho, seed, algoritmo)
            feitos += 1
            somas["objetivos_medio"] += linha["objetivos_concluidos"]
            somas["custo_medio"] += linha["custo_planejado"]
            somas["batalhas_medio"] += linha["batalhas"]
            somas["hp_perdido_medio"] += linha["hp_perdido"]
            fila.put({
                "tipo": "progresso",
                "algoritmo": algoritmo,
                "tamanho": tamanho,
                "seed": seed,
                "mapas_feitos": feitos,
                "mapas_total": total,
                "amostra": feitos,
                "unidade": "partidas",
                "medias": _medias("partidas", somas, feitos),
                "decorrido_s": round(time.perf_counter() - inicio, 3),
            })

    fila.put({
        "tipo": "fim",
        "algoritmo": algoritmo,
        "amostra": feitos,
        "unidade": "partidas",
        "mapas_total": total,
        "medias": _medias("partidas", somas, feitos),
        "decorrido_s": round(time.perf_counter() - inicio, 3),
    })


def _trabalhar_ambos(algoritmo, tamanhos, seeds, repeticoes, fila):
    """Roda os dois experimentos na mesma raia, um depois do outro.

    Existe porque separar por um seletor obrigava a escolher entre ver o custo
    da rota e ver os objetivos da partida, e as duas coisas juntas sao o
    resultado do trabalho. Os grupos continuam separados DENTRO da raia: os
    custos dos dois experimentos nao sao comparaveis entre si, porque na
    partida o mapa muda durante a execucao.
    """
    grupos = {}

    class _Coletor:
        """Recebe o que os dois trabalhadores emitiriam e junta num evento so."""

        def __init__(self):
            self.ultimo = {}

        def put(self, dados):
            fase = self.fase
            self.ultimo[fase] = dados
            if dados["tipo"] == "fim":
                grupos[fase] = dados
                return
            fila.put({
                "tipo": "progresso",
                "algoritmo": algoritmo,
                "tamanho": dados["tamanho"],
                "seed": dados["seed"],
                "mapas_feitos": dados["mapas_feitos"] + self.deslocamento,
                "mapas_total": self.total_geral,
                "fase": fase,
                "grupos": self._snapshot(),
                "decorrido_s": round(time.perf_counter() - self.inicio, 3),
            })

        def _snapshot(self):
            saida = []
            for nome in ("rotas", "partidas"):
                dados = grupos.get(nome) or self.ultimo.get(nome)
                if dados is None:
                    saida.append({"titulo": TITULO[nome], "amostra": 0,
                                  "unidade": UNIDADE[nome],
                                  "medias": [{"rotulo": rotulo, "valor": 0}
                                             for rotulo, _ in METRICAS[nome]]})
                else:
                    saida.append({"titulo": TITULO[nome], "amostra": dados["amostra"],
                                  "unidade": dados["unidade"], "medias": dados["medias"]})
            return saida

    coletor = _Coletor()
    coletor.inicio = time.perf_counter()
    total = len(tamanhos) * seeds
    coletor.total_geral = total * 2

    coletor.fase, coletor.deslocamento = "rotas", 0
    _trabalhar_rotas(algoritmo, tamanhos, seeds, repeticoes, coletor)
    coletor.fase, coletor.deslocamento = "partidas", total
    _trabalhar_partidas(algoritmo, tamanhos, seeds, repeticoes, coletor)

    fila.put({
        "tipo": "fim",
        "algoritmo": algoritmo,
        "mapas_total": coletor.total_geral,
        "grupos": coletor._snapshot(),
        "decorrido_s": round(time.perf_counter() - coletor.inicio, 3),
    })


TITULO = {"rotas": "rota pura", "partidas": "partida completa"}
UNIDADE = {"rotas": "medicoes de rota", "partidas": "partidas"}

TRABALHADORES = {
    "rotas": _trabalhar_rotas,
    "partidas": _trabalhar_partidas,
    "ambos": _trabalhar_ambos,
}


def _trabalhar(algoritmo, tamanhos, seeds, repeticoes, fila, experimento="ambos"):
    TRABALHADORES[experimento](algoritmo, tamanhos, seeds, repeticoes, fila)


def eventos_benchmark(tamanhos=TAMANHOS, seeds=SEEDS, algoritmos=None, repeticoes=1,
                      experimento="ambos"):
    """Dispara um processo por algoritmo e gera os eventos conforme chegam."""
    escolhidos = [a for a in (algoritmos or list(ALGORITMOS)) if a in ALGORITMOS]
    contexto = mp.get_context("spawn")
    fila = contexto.Queue()

    processos = [
        contexto.Process(
            target=_trabalhar,
            args=(nome, list(tamanhos), seeds, repeticoes, fila, experimento),
            daemon=True,
        )
        for nome in escolhidos
    ]

    yield "inicio", {
        "algoritmos": escolhidos,
        "tamanhos": list(tamanhos),
        "seeds": seeds,
        "repeticoes": repeticoes,
        "experimento": experimento,
        "descricao": DESCRICAO[experimento],
        # os rotulos saem daqui pra que a pagina nao guarde uma segunda copia
        # da lista de metricas, que sairia de sincronia na primeira mudanca
        "grupos": ([{"titulo": TITULO[nome], "unidade": UNIDADE[nome],
                     "metricas": [rotulo for rotulo, _ in METRICAS[nome]]}
                    for nome in ("rotas", "partidas")]
                   if experimento == "ambos"
                   else [{"titulo": TITULO[experimento], "unidade": UNIDADE[experimento],
                          "metricas": [rotulo for rotulo, _ in METRICAS[experimento]]}]),
        "mapas_total": len(tamanhos) * seeds * (2 if experimento == "ambos" else 1),
    }

    inicio = time.perf_counter()
    for processo in processos:
        processo.start()

    terminados = []
    try:
        while len(terminados) < len(escolhidos):
            dados = fila.get()
            if dados["tipo"] == "fim":
                terminados.append(dados["algoritmo"])
                dados["posicao_chegada"] = len(terminados)
                yield "fim_raia", dados
            else:
                yield "progresso", dados
    finally:
        for processo in processos:
            processo.join(timeout=5)
            if processo.is_alive():
                processo.terminate()

    yield "encerrado", {
        "ordem_de_chegada": terminados,
        "decorrido_s": round(time.perf_counter() - inicio, 3),
    }
