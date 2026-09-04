# Pokémon CLI com Pathfinding

## Projeto de Algoritmos

| Matrícula | Aluno |
| --- | --- |
| 190091681 | Lucas Gabriel Antunes |
| 202045965 | Augusto Campos Duarte |

## Sobre

Este projeto é um jogo de Pokémon executado no terminal, adaptado para o
estudo e a comparação de algoritmos de busca em grafos. O jogador explora um
mapa em formato de grade, encontra Pokémon selvagens, enfrenta treinadores,
coleta itens e percorre diferentes tipos de terreno.

O objetivo do trabalho é implementar e analisar estratégias de pathfinding
para encontrar caminhos entre posições do mapa. São comparados três
algoritmos:

- **DFS (Depth-First Search)**, que realiza uma busca em profundidade;
- **BFS (Breadth-First Search)**, que encontra caminhos com menor número de
	passos;
- **Dijkstra**, que encontra caminhos de menor custo considerando os pesos do
	terreno e os custos de batalhas.

O projeto mostra a diferença entre o caminho com menos passos e o caminho com
menor custo. Assim, o BFS pode escolher um trajeto curto que atravessa uma
região cara, enquanto o Dijkstra pode escolher um caminho com mais passos e
menor custo total.

## Como funciona

O mapa é uma matriz de células. Cada célula possui um terreno, como concreto,
grama ou água, e pode conter um Pokémon selvagem, um treinador, uma pokébola,
um item de Surf ou um bloqueio.

A camada de grafo transforma o mapa em posições conectadas por vizinhanças. O
estado do jogador informa atributos que afetam o grafo, como o HP do Pokémon
líder e a capacidade de usar Surf. Sem Surf, células de água são inacessíveis;
com Surf, elas passam a fazer parte do grafo.

O custo de entrar em uma célula é calculado pelo terreno e pelo conteúdo da
célula. Grama pode ficar mais cara quando o Pokémon líder está com pouco HP,
enquanto batalhas contra Pokémon selvagens e treinadores adicionam penalidades
ao caminho.

Cada algoritmo recebe a mesma entrada:

```text
(origem, destino, grid, estado)
```

e retorna:

```text
(caminho, custo, nos_expandidos)
```

Essa padronização permite comparar os algoritmos usando os mesmos mapas,
origens, destinos e estados do jogador.


## Testes

```powershell
python -m pytest
```

Os testes verificam o funcionamento do mapa, movimento, itens, camada de
grafo e algoritmos de busca, incluindo um caso em que BFS e Dijkstra escolhem
caminhos diferentes.

## Referência

Este projeto parte do jogo original criado por
[elchic00](https://github.com/elchic00/pokemon). A implementação atual foi
adaptada pelos alunos para a disciplina.

