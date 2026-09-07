"""Roda a grade inteira da fase 6: os dois experimentos e os graficos.

    python -m bench
    python -m bench --so rotas --tamanhos 8 15 --seeds 10
"""

import argparse
from pathlib import Path

from . import charts, partidas, rotas
from .common import SAIDA_PADRAO, SEEDS, TAMANHOS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark da fase 6")
    parser.add_argument("--tamanhos", type=int, nargs="+", default=list(TAMANHOS))
    parser.add_argument("--seeds", type=int, default=SEEDS)
    parser.add_argument("--repeticoes", type=int, default=3,
                        help="execucoes por medicao de rota; vale a menor")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--so", choices=["rotas", "partidas", "graficos"], default=None,
                        help="roda so uma etapa, em vez das tres")
    args = parser.parse_args(argv)

    if args.so in (None, "rotas"):
        rotas.main(["--tamanhos", *map(str, args.tamanhos),
                    "--seeds", str(args.seeds),
                    "--repeticoes", str(args.repeticoes),
                    "--saida", str(args.saida)])

    if args.so in (None, "partidas"):
        partidas.main(["--tamanhos", *map(str, args.tamanhos),
                       "--seeds", str(args.seeds),
                       "--saida", str(args.saida)])

    if args.so in (None, "graficos"):
        for caminho in charts.gerar(args.saida):
            print(f"grafico: {caminho}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
