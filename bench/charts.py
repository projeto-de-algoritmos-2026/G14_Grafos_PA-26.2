"""Graficos do benchmark, em SVG escrito a mao.

Por que nao matplotlib: o projeto declara duas dependencias (rich e pytest) e
o grafico que o plano pede e uma linha por algoritmo contra tres tamanhos de
mapa. Isso cabe em SVG da biblioteca padrao, e o arquivo resultante abre no
navegador, entra no relatorio e sobe pro repositorio como texto versionavel.
Se em algum momento o relatorio precisar de escala log, barra de erro ou
regressao, ai sim vale trocar por matplotlib, e a troca e local a este modulo.
"""

import argparse
from pathlib import Path

from .common import SAIDA_PADRAO, ler_csv

LARGURA, ALTURA = 720, 420
MARGEM = {"esquerda": 78, "direita": 150, "topo": 52, "baixo": 62}

CORES = {
    "dfs": "#d1495b",
    "bfs": "#2a9d8f",
    "dijkstra": "#3d5a80",
}
COR_PADRAO = "#6c757d"


def _escala(valor, minimo, maximo, inicio, fim):
    if maximo == minimo:
        return (inicio + fim) / 2
    return inicio + (valor - minimo) * (fim - inicio) / (maximo - minimo)


def _ticks(maximo, quantidade=4):
    if maximo <= 0:
        return [0]
    return [round(maximo * i / quantidade, 2) for i in range(quantidade + 1)]


def grafico_linhas(titulo, rotulo_x, rotulo_y, series, caminho: Path) -> Path:
    """Uma linha por serie. `series` e {nome: [(x, y), ...]} com x numerico."""
    pontos_todos = [ponto for pontos in series.values() for ponto in pontos]
    if not pontos_todos:
        raise ValueError("grafico sem nenhum ponto")

    xs = sorted({ponto[0] for ponto in pontos_todos})
    x_min, x_max = min(xs), max(xs)
    y_max = max(ponto[1] for ponto in pontos_todos) or 1
    y_max = y_max * 1.1

    esquerda = MARGEM["esquerda"]
    direita = LARGURA - MARGEM["direita"]
    topo = MARGEM["topo"]
    base = ALTURA - MARGEM["baixo"]

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{LARGURA}" height="{ALTURA}" '
        f'viewBox="0 0 {LARGURA} {ALTURA}" font-family="system-ui, sans-serif">',
        f'<rect width="{LARGURA}" height="{ALTURA}" fill="#ffffff"/>',
        f'<text x="{esquerda}" y="30" font-size="17" font-weight="600" fill="#1d2733">{titulo}</text>',
    ]

    for valor in _ticks(y_max):
        y = _escala(valor, 0, y_max, base, topo)
        partes.append(
            f'<line x1="{esquerda}" y1="{y:.1f}" x2="{direita}" y2="{y:.1f}" '
            f'stroke="#e4e8ee" stroke-width="1"/>'
        )
        partes.append(
            f'<text x="{esquerda - 10}" y="{y + 4:.1f}" font-size="11" '
            f'text-anchor="end" fill="#66707c">{valor:g}</text>'
        )

    partes.append(
        f'<line x1="{esquerda}" y1="{base}" x2="{direita}" y2="{base}" '
        f'stroke="#96a0ac" stroke-width="1"/>'
    )
    for valor in xs:
        x = _escala(valor, x_min, x_max, esquerda, direita)
        partes.append(
            f'<text x="{x:.1f}" y="{base + 22}" font-size="12" '
            f'text-anchor="middle" fill="#414b57">{valor:g}</text>'
        )

    partes.append(
        f'<text x="{(esquerda + direita) / 2:.0f}" y="{ALTURA - 16}" font-size="12" '
        f'text-anchor="middle" fill="#66707c">{rotulo_x}</text>'
    )
    partes.append(
        f'<text x="18" y="{(topo + base) / 2:.0f}" font-size="12" fill="#66707c" '
        f'text-anchor="middle" transform="rotate(-90 18 {(topo + base) / 2:.0f})">{rotulo_y}</text>'
    )

    for indice, (nome, pontos) in enumerate(series.items()):
        cor = CORES.get(nome, COR_PADRAO)
        coordenadas = [
            (_escala(x, x_min, x_max, esquerda, direita), _escala(y, 0, y_max, base, topo))
            for x, y in sorted(pontos)
        ]
        traco = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordenadas)
        partes.append(
            f'<polyline points="{traco}" fill="none" stroke="{cor}" stroke-width="2.5" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )
        for x, y in coordenadas:
            partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{cor}"/>')
        y_legenda = topo + 6 + indice * 22
        partes.append(
            f'<rect x="{direita + 22}" y="{y_legenda - 8}" width="12" height="12" rx="3" fill="{cor}"/>'
        )
        partes.append(
            f'<text x="{direita + 40}" y="{y_legenda + 2}" font-size="12" fill="#1d2733">{nome}</text>'
        )

    partes.append("</svg>")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(partes), encoding="utf-8")
    return caminho


def series_por_algoritmo(linhas, coluna, filtro=None):
    """{algoritmo: [(tamanho, valor)]} a partir de um CSV de resumo."""
    series: dict[str, list] = {}
    for linha in linhas:
        if filtro and any(linha[chave] != valor for chave, valor in filtro.items()):
            continue
        series.setdefault(linha["algoritmo"], []).append(
            (int(linha["tamanho"]), float(linha[coluna]))
        )
    return series


GRAFICOS_ROTAS = [
    ("custo_medio", "Custo medio da rota por tamanho de mapa", "custo medio", "rotas-custo.svg"),
    ("passos_medio", "Passos medios da rota por tamanho de mapa", "passos medios", "rotas-passos.svg"),
    ("nos_expandidos_medio", "Nos expandidos por tamanho de mapa", "nos expandidos", "rotas-nos.svg"),
]

GRAFICOS_PARTIDAS = [
    ("batalhas_medio", "Batalhas forcadas por partida", "batalhas", "partidas-batalhas.svg"),
    ("hp_perdido_medio", "HP perdido por partida", "HP perdido", "partidas-hp.svg"),
    ("objetivos_medio", "Objetivos concluidos por partida", "objetivos", "partidas-objetivos.svg"),
]


def gerar(saida: Path = SAIDA_PADRAO, estado="hp100") -> list[Path]:
    """Le os resumos ja gravados e escreve os SVGs ao lado deles."""
    gerados = []
    resumo_rotas = saida / "rotas_resumo.csv"
    if resumo_rotas.exists():
        linhas = ler_csv(resumo_rotas)
        for coluna, titulo, rotulo, arquivo in GRAFICOS_ROTAS:
            series = series_por_algoritmo(linhas, coluna, filtro={"estado": estado})
            if series:
                gerados.append(grafico_linhas(
                    f"{titulo} ({estado})", "tamanho do mapa", rotulo, series, saida / arquivo
                ))

    resumo_partidas = saida / "partidas_resumo.csv"
    if resumo_partidas.exists():
        linhas = ler_csv(resumo_partidas)
        for coluna, titulo, rotulo, arquivo in GRAFICOS_PARTIDAS:
            series = series_por_algoritmo(linhas, coluna)
            if series:
                gerados.append(grafico_linhas(
                    titulo, "tamanho do mapa", rotulo, series, saida / arquivo
                ))
    return gerados


def main(argv=None):
    parser = argparse.ArgumentParser(description="Graficos do benchmark (fase 6)")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--estado", default="hp100", help="estado usado nos graficos de rota")
    args = parser.parse_args(argv)

    gerados = gerar(args.saida, args.estado)
    for caminho in gerados:
        print(f"grafico: {caminho}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
