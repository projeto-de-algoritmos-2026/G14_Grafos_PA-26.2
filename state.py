"""Estado global do jogo.

O codigo original guardava o jogador numa variavel global `player1` criada
dentro do bloco `if __name__ == "__main__"` de main.py, e Grid e
traverse_grid liam essa global direto. Com o arquivo quebrado em modulos a
global precisa morar em algum lugar que todos enxerguem, e este modulo e
esse lugar.

Isto e andaime, nao arquitetura: a fase 1 tira o jogador de dentro da matriz
e passa a receber o Player por parametro. Quando isso acontecer, este modulo
deixa de existir.

Note que `player1` NAO e inicializado de proposito: assim como no original,
usar o jogo sem comecar uma partida quebra na hora, em vez de seguir adiante
com um jogador vazio.
"""
