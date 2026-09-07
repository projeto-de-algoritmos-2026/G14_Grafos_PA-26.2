"""Testes do benchmark da fase 6.

Os testes rodam numa grade minuscula de proposito: o que precisa ser garantido
e o contrato (colunas do CSV, uma linha por algoritmo, agregacao correta,
descarte registrado em vez de sumido), nao o tempo da grade real.
"""

import math

import pytest

from bench import charts, common, partidas, rotas
from graph.search import dijkstra_distancias


def test_media_ignora_infinito():
    """Rota sem caminho guarda custo infinito, e infinito contamina a media
    inteira. A coluna `execucoes` do resumo e quem conta essas linhas."""
    linhas = [{"custo": "10"}, {"custo": str(math.inf)}, {"custo": "20"}]

    assert common.media(linhas, "custo") == 15.0


def test_csv_ida_e_volta(tmp_path):
    linhas = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    caminho = common.escrever_csv(tmp_path / "t.csv", ["a", "b"], linhas)

    assert common.ler_csv(caminho) == [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]


def test_sortear_destinos_e_reproduzivel_e_fica_no_componente_sem_surf():
    from grid import Grid

    mapa = Grid(size=8, seed=7)
    primeiro = rotas.sortear_destinos(mapa)
    segundo = rotas.sortear_destinos(Grid(size=8, seed=7))

    assert primeiro == segundo
    distancias, _ = dijkstra_distancias(rotas.ORIGEM, mapa, rotas.ESTADOS["hp100"])
    assert all(destino in distancias for destino in primeiro)


def test_rotas_gera_uma_linha_por_algoritmo_e_estado():
    linhas, _ = rotas.rodar(tamanhos=(6,), seeds=2)

    assert linhas, "a grade minima precisa produzir alguma medicao"
    assert set(linha["algoritmo"] for linha in linhas) == set(common.ALGORITMOS)
    esperado = len(common.ALGORITMOS) * len(rotas.ESTADOS)
    por_destino = common.agrupar(linhas, ["tamanho", "seed", "destino"])
    assert all(len(grupo) == esperado for grupo in por_destino.values())


def test_rotas_registra_mapa_com_origem_ilhada_em_vez_de_ignorar():
    # A seed 0 em 8x8 nasce com a origem cercada de agua: sem surf o
    # componente e so (0,0) e nao ha destino possivel.
    linhas, descartes = rotas.rodar(tamanhos=(8,), seeds=1)

    assert linhas == []
    assert descartes == [
        {"tamanho": 8, "seed": 0,
         "motivo": "origem sem componente alcancavel sem surf"}
    ]


def test_dijkstra_nunca_custa_mais_que_bfs_ou_dfs_na_mesma_rota():
    """Primeira das duas invariantes que sustentam o relatorio."""
    linhas, _ = rotas.rodar(tamanhos=(8, 15), seeds=4)

    for grupo in common.agrupar(linhas, ["tamanho", "seed", "destino", "estado"]).values():
        custos = {linha["algoritmo"]: linha["custo"] for linha in grupo}
        assert custos["dijkstra"] <= custos["bfs"]
        assert custos["dijkstra"] <= custos["dfs"]


def test_bfs_nunca_da_mais_passos_que_dijkstra_ou_dfs():
    """Segunda invariante. Junto com a anterior, e a tese do trabalho virada
    em teste: quem ganha em passos nao e quem ganha em custo."""
    linhas, _ = rotas.rodar(tamanhos=(8, 15), seeds=4)

    for grupo in common.agrupar(linhas, ["tamanho", "seed", "destino", "estado"]).values():
        passos = {linha["algoritmo"]: linha["passos"] for linha in grupo}
        assert passos["bfs"] <= passos["dijkstra"]
        assert passos["bfs"] <= passos["dfs"]


def test_resumo_de_rotas_agrega_por_tamanho_estado_e_algoritmo():
    linhas, _ = rotas.rodar(tamanhos=(6,), seeds=2)
    resumo = rotas.resumir(linhas)

    assert len(resumo) == len(rotas.ESTADOS) * len(common.ALGORITMOS)
    assert sum(item["execucoes"] for item in resumo) == len(linhas)
    assert set(resumo[0]) == set(rotas.CAMPOS_RESUMO)


def test_partida_do_bot_produz_a_linha_completa_sem_imprimir(capsys):
    linha = partidas.rodar_partida(8, 1, "dijkstra")

    assert set(linha) == set(partidas.CAMPOS)
    assert linha["motivo_parada"]
    assert linha["passos"] >= 0
    assert capsys.readouterr().out == "", "a narracao da batalha nao pode vazar"


def test_partida_e_reproduzivel_com_a_mesma_semente():
    """Duas execucoes iguais precisam dar a mesma partida.

    `tempo_ms` fica de fora da comparacao: e medicao de relogio, nao resultado
    do algoritmo, e varia entre execucoes por definicao.
    """
    def sem_tempo(linha):
        return {chave: valor for chave, valor in linha.items() if chave != "tempo_ms"}

    primeira = partidas.rodar_partida(8, 3, "bfs")
    segunda = partidas.rodar_partida(8, 3, "bfs")

    assert sem_tempo(primeira) == sem_tempo(segunda)


def test_resumo_de_partidas_conta_as_partidas_sem_objetivo():
    linhas = partidas.rodar(tamanhos=(8,), seeds=3)
    resumo = partidas.resumir(linhas)

    assert len(resumo) == len(common.ALGORITMOS)
    for item in resumo:
        do_algoritmo = [l for l in linhas if l["algoritmo"] == item["algoritmo"]]
        assert item["partidas_sem_objetivo"] == sum(
            1 for l in do_algoritmo if l["objetivos_concluidos"] == 0
        )


def test_grafico_sai_com_uma_linha_por_serie(tmp_path):
    series = {"dfs": [(8, 10), (15, 20)], "dijkstra": [(8, 5), (15, 9)]}
    caminho = charts.grafico_linhas("t", "x", "y", series, tmp_path / "g.svg")
    conteudo = caminho.read_text(encoding="utf-8")

    assert conteudo.startswith("<svg") and conteudo.rstrip().endswith("</svg>")
    assert conteudo.count("<polyline") == 2
    assert charts.CORES["dijkstra"] in conteudo


def test_grafico_recusa_serie_vazia(tmp_path):
    with pytest.raises(ValueError):
        charts.grafico_linhas("t", "x", "y", {}, tmp_path / "g.svg")


def test_gerar_graficos_le_os_resumos_gravados(tmp_path):
    linhas, _ = rotas.rodar(tamanhos=(6, 8), seeds=3)
    common.escrever_csv(tmp_path / "rotas_resumo.csv", rotas.CAMPOS_RESUMO,
                        rotas.resumir(linhas))

    gerados = charts.gerar(tmp_path)

    assert [caminho.name for caminho in gerados] == [
        "rotas-custo.svg", "rotas-passos.svg", "rotas-nos.svg"
    ]
