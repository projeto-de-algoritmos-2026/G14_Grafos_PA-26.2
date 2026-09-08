"""Testes da camada web.

Todos batem nas funcoes puras de `webdemo/api.py` e no trabalhador do
benchmark, sem abrir socket: o `server.py` e casca, e o que precisa de garantia
e a traducao pra JSON e o contrato que a pagina consome.
"""

import queue
import random

import pytest

from bench import partidas
from bench.common import ALGORITMOS
from webdemo import api
from webdemo.benchmark import _trabalhar


def test_limitar_prende_o_parametro_na_faixa():
    assert api.limitar("15", 3, 40, 8) == 15
    assert api.limitar("999999", 3, 40, 8) == 40
    assert api.limitar("-5", 3, 40, 8) == 3
    assert api.limitar("abacaxi", 3, 40, 8) == 8
    assert api.limitar(None, 3, 40, 8) == 8


def test_mapa_traz_o_grid_e_o_que_e_alcancavel():
    dados = api.dados_mapa(8, 42)

    assert dados["size"] == 8
    assert len(dados["celulas"]) == 8 and len(dados["celulas"][0]) == 8
    assert dados["posicao"] == [0, 0]
    assert [0, 0] in dados["alcancaveis"]
    for linha, coluna in dados["alcancaveis"]:
        assert dados["celulas"][linha][coluna]["pisavel_sem_surf"]


def test_surf_nunca_reduz_o_que_e_alcancavel():
    """O Surf so acrescenta aresta. Se a lista encolhesse, a modelagem da fase
    2 estaria sendo contrariada em algum lugar."""
    sem = {tuple(p) for p in api.dados_mapa(15, 7, surf=False)["alcancaveis"]}
    com = {tuple(p) for p in api.dados_mapa(15, 7, surf=True)["alcancaveis"]}

    assert sem <= com


def test_rota_devolve_os_tres_algoritmos_com_as_invariantes():
    mapa = api.dados_mapa(15, 42)
    destino = mapa["alcancaveis"][-1]
    dados = api.dados_rota(15, 42, tuple(destino))

    assert set(dados["rotas"]) == set(ALGORITMOS)
    rotas = dados["rotas"]
    assert all(r["encontrou"] for r in rotas.values())
    assert rotas["dijkstra"]["custo"] <= rotas["bfs"]["custo"]
    assert rotas["dijkstra"]["custo"] <= rotas["dfs"]["custo"]
    assert rotas["bfs"]["passos"] <= rotas["dijkstra"]["passos"]
    for rota in rotas.values():
        assert rota["caminho"][0] == [0, 0]
        assert rota["caminho"][-1] == list(destino)
        assert rota["passos"] == len(rota["caminho"]) - 1


def test_rota_para_destino_fora_do_componente_nao_inventa_caminho(seed_ilhada):
    dados = api.dados_rota(8, seed_ilhada(8), (7, 7))

    for rota in dados["rotas"].values():
        assert rota["encontrou"] is False
        assert rota["caminho"] == []
        assert rota["custo"] is None


def test_rota_aceita_escolher_so_um_algoritmo():
    mapa = api.dados_mapa(8, 42)
    dados = api.dados_rota(8, 42, tuple(mapa["alcancaveis"][-1]), ["dijkstra"])

    assert list(dados["rotas"]) == ["dijkstra"]


def test_partida_transmite_inicio_passos_e_fim():
    eventos = list(api.eventos_partida(15, 42, "dijkstra"))
    nomes = [nome for nome, _ in eventos]

    assert nomes[0] == "inicio"
    assert nomes[-1] == "fim"
    assert "plano" in nomes and "passo" in nomes

    fim = eventos[-1][1]
    assert "erro" not in fim
    assert fim["passos"] == nomes.count("passo")
    assert fim["replanejamentos"] == nomes.count("plano") + (
        0 if fim["motivo_parada"] not in ("sem objetivos alcançaveis",) else 1
    )
    assert fim["motivo_parada"]


def test_partida_num_mapa_ilhado_termina_sem_passo(seed_ilhada):
    eventos = list(api.eventos_partida(8, seed_ilhada(8), "bfs"))
    nomes = [nome for nome, _ in eventos]

    assert nomes == ["inicio", "fim"]
    assert eventos[-1][1]["motivo_parada"] == "sem objetivos alcançaveis"


def test_jogo_humano_anda_e_recusa_agua_sem_surf():
    # O inicial e as batalhas saem do `random` global, que outros testes desta
    # suite semeiam. Sem fixar aqui, o time pode encher no meio do caminho e a
    # partida terminar antes das quatro tentativas, e o teste falha so quando
    # roda acompanhado.
    random.seed(20260907)
    jogo = api.criar_jogo(8, 42)
    assert jogo["jogador"]["pokemon"] == 1

    passo = api.mover_jogo(jogo["sessao"], "D")
    assert passo["valido"] is True
    assert passo["posicao"] == [0, 1]
    assert passo["celula"]["conteudo"] == "visitado"

    # anda ate esbarrar em agua, se houver agua vizinha nesta seed
    respostas = [api.mover_jogo(jogo["sessao"], d) for d in "SSSS"]
    motivos = {r.get("motivo") for r in respostas
               if not r.get("valido") and "erro" not in r}
    assert motivos <= {"agua sem surf", "celula inacessivel", "fora do mapa"}


def test_jogo_humano_termina_pela_regra_do_jogo():
    """Vitoria e derrota do modo humano saem de `game.partida_encerrada`, a
    mesma funcao que para o bot, e nao de uma regra propria da web."""
    from game import POKEMON_PARA_VENCER

    jogo = api.criar_jogo(8, 42)
    assert jogo["jogador"]["meta"] == POKEMON_PARA_VENCER
    assert jogo["jogador"]["situacao"] == "jogando"

    sessao = api._sessoes[jogo["sessao"]]
    sessao["player"].pokemon_list.clear()
    assert "erro" in api.mover_jogo(jogo["sessao"], "D")

    sessao["player"].pokemon_list.extend(
        [object()] * POKEMON_PARA_VENCER)  # time cheio
    resposta = api.mover_jogo(jogo["sessao"], "D")
    assert "erro" in resposta and "encerrada" in resposta["erro"]


def test_jogo_humano_recusa_sessao_desconhecida():
    assert "erro" in api.mover_jogo("nao-existe", "D")


def test_jogo_humano_nao_pendura_esperando_teclado(monkeypatch):
    """`battle()` do jogo le do stdin. Se a sessao web chamar o modo humano,
    a conexao trava esperando uma resposta que nunca chega."""
    def explodir(*args, **kwargs):
        raise AssertionError("input() foi chamado a partir da sessao web")

    monkeypatch.setattr("builtins.input", explodir)
    jogo = api.criar_jogo(10, 42)
    for direcao in "DSDSDSAW":
        api.mover_jogo(jogo["sessao"], direcao)


def _rodar_raia(algoritmo, experimento, seeds=3):
    fila: queue.Queue = queue.Queue()
    _trabalhar(algoritmo, [8], seeds, 1, fila, experimento)
    eventos = []
    while not fila.empty():
        eventos.append(fila.get())
    return eventos


@pytest.mark.parametrize("experimento", ["rotas", "partidas"])
def test_trabalhador_do_benchmark_reporta_progresso_e_fecha(experimento):
    eventos = _rodar_raia("bfs", experimento)
    progressos = [e for e in eventos if e["tipo"] == "progresso"]
    fins = [e for e in eventos if e["tipo"] == "fim"]

    assert len(progressos) == 3, "um evento por mapa da grade"
    assert progressos[-1]["mapas_feitos"] == progressos[-1]["mapas_total"] == 3
    assert len(fins) == 1
    assert fins[0]["algoritmo"] == "bfs"
    assert fins[0]["amostra"] == progressos[-1]["amostra"]
    assert fins[0]["decorrido_s"] >= 0


@pytest.mark.parametrize("experimento", ["rotas", "partidas"])
def test_toda_media_da_raia_se_anuncia_como_media(experimento):
    """O rotulo que a tela mostra vem daqui. Numero solto numa tela grande e
    lido como valor daquela execucao, e todo numero da raia e media."""
    fim = [e for e in _rodar_raia("dijkstra", experimento) if e["tipo"] == "fim"][0]

    assert fim["amostra"] > 0 and fim["unidade"]
    assert fim["medias"], "a raia precisa de pelo menos uma metrica"
    for media in fim["medias"]:
        assert "medi" in media["rotulo"].lower(), media["rotulo"]
        assert isinstance(media["valor"], (int, float))


@pytest.mark.parametrize("experimento", ["rotas", "partidas"])
def test_custo_aparece_nos_dois_experimentos(experimento):
    """Custo e a grandeza que o trabalho mede. Sem ela na tela, a corrida
    mostra tempo e nao mostra o resultado."""
    fim = [e for e in _rodar_raia("dijkstra", experimento) if e["tipo"] == "fim"][0]
    rotulos = [m["rotulo"] for m in fim["medias"]]

    assert any("custo" in rotulo for rotulo in rotulos), rotulos


def test_objetivo_so_existe_no_experimento_de_partida():
    """Na rota pura ha origem e destino, nao ha alvo a escolher. A raia nao
    pode anunciar objetivo num experimento que nao tem objetivo."""
    rotulos = {
        exp: " ".join(m["rotulo"] for m in
                      [e for e in _rodar_raia("bfs", exp) if e["tipo"] == "fim"][0]["medias"])
        for exp in ("rotas", "partidas")
    }

    assert "objetivo" not in rotulos["rotas"]
    assert "objetivo" in rotulos["partidas"]


@pytest.mark.parametrize("experimento", ["rotas", "partidas"])
def test_raias_do_benchmark_medem_o_mesmo_tanto_de_trabalho(experimento):
    """A corrida so significa alguma coisa se as tres raias fizerem o mesmo
    tanto de trabalho sobre os mesmos mapas."""
    contagens = {}
    for nome in ALGORITMOS:
        fins = [e for e in _rodar_raia(nome, experimento, seeds=5) if e["tipo"] == "fim"]
        contagens[nome] = fins[0]["amostra"]

    assert len(set(contagens.values())) == 1, contagens


def test_partida_da_tela_e_reproduzivel_e_bate_com_o_benchmark():
    """Mesmo tamanho e mesma seed tem que dar a mesma partida, e tem que ser a
    partida que o benchmark mede.

    So o mapa vinha semeado: o dado da batalha saia do estado global do
    `random`, entao a tela mostrava uma partida diferente a cada clique e
    nenhuma delas era a medida pelo benchmark.
    """
    def resumo(eventos):
        fim = eventos[-1][1]
        return (fim["objetivos_concluidos"], fim["passos"], fim["batalhas"],
                fim["hp_perdido"], fim["motivo_parada"])

    primeira = resumo(list(api.eventos_partida(15, 2, "dfs")))
    segunda = resumo(list(api.eventos_partida(15, 2, "dfs")))
    assert primeira == segunda

    do_benchmark = partidas.rodar_partida(15, 2, "dfs")
    assert primeira == (
        do_benchmark["objetivos_concluidos"], do_benchmark["passos"],
        do_benchmark["batalhas"], do_benchmark["hp_perdido"],
        do_benchmark["motivo_parada"],
    )
