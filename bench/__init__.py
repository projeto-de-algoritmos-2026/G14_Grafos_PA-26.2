"""Benchmark comparativo (fase 6).

Sao DOIS experimentos, e a separacao e o ponto principal do desenho:

- `bench.rotas`: rota pura. Mesma origem, mesmo destino, mesmo estado, tres
  algoritmos. E o experimento que sustenta a tese do trabalho, porque isola a
  unica variavel que interessa (a estrategia de busca) e mede custo, passos e
  nos expandidos sem nada mais no meio.

- `bench.partidas`: partida completa. O bot da fase 5 joga do inicio ao fim
  com cada algoritmo escolhendo a rota, e o que se mede e a consequencia:
  batalhas forcadas, HP perdido, objetivos concluidos. Aqui o mapa muda
  durante a execucao (celula virou VISITADO, surf apareceu, HP caiu), entao os
  numeros nao sao comparaveis linha a linha com os do outro experimento.

Grade dos dois: tamanhos 8, 15 e 30 x 30 seeds x 3 algoritmos. Saida em CSV em
`bench/out/`, mais graficos SVG em `bench.charts`.
"""
