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


## Como executar

O jogo tem dois modos, mutuamente exclusivos, no mesmo executável. Em ambos o
programa pede os dados iniciais do jogador antes de começar.

```powershell
python main.py --human                      # o jogador informa W/A/S/D
python main.py --bot                        # o bot planeja e executa sozinho
python main.py --bot --visual               # mostra o plano e o mapa a cada passo
python main.py --bot --size 15 --seed 42    # mapa reproduzível
```

Sem nenhuma flag, o modo humano é o padrão. `--size` e `--seed` valem para os
dois modos: a mesma semente sempre gera o mesmo mapa, que é o que torna o
benchmark reproduzível.

## Benchmark

A fase 6 mede os três algoritmos em dois experimentos separados, porque eles
respondem a perguntas diferentes.

```powershell
python -m bench                                   # os dois experimentos e os gráficos
python -m bench --so rotas --tamanhos 8 15        # só um recorte
python -m bench --seeds 5                         # grade menor, para iterar
```

A saída vai para `bench/out/`: os CSVs por execução, os resumos agregados e os
gráficos em SVG.

**Rota pura** (`bench/rotas.py`). Mesmo mapa, mesma origem, mesmo destino,
mesmo estado do jogador. Só o algoritmo muda. É o único recorte em que a
comparação isola a estratégia de busca. Os destinos são sorteados dentro do
componente alcançável sem Surf, para que a mesma linha continue válida quando
o Surf é ligado. Mapa cuja origem nasce cercada de água não tem destino
possível e vai para `rotas_descartes.csv` em vez de sumir da amostra: 5 seeds
em 8x8, 9 em 15x15 e 8 em 30x30, de 30 cada.

**Partida completa** (`bench/partidas.py`). O bot joga do início ao fim e o
algoritmo em teste calcula a rota de cada objetivo. Aqui não se mede a rota, e
sim a consequência dela: batalhas forçadas, HP perdido, objetivos concluídos.
A escolha dos objetivos continua sendo a da fase 4 (score por Dijkstra) nos
três casos, de propósito: trocar rota e alvo ao mesmo tempo impediria dizer de
onde veio a diferença.

### Resultados

Rota pura, HP 100 e sem Surf, média de 30 seeds por tamanho:

| Tamanho | Algoritmo | Custo | Passos | Nós expandidos |
| --- | --- | --- | --- | --- |
| 8 | DFS | 43,0 | 9,4 | 16,9 |
| 8 | BFS | 28,4 | 6,6 | 15,0 |
| 8 | Dijkstra | **25,8** | 6,7 | 14,8 |
| 15 | DFS | 82,5 | 19,1 | 48,5 |
| 15 | BFS | 55,5 | **13,0** | 51,9 |
| 15 | Dijkstra | **49,0** | 13,7 | 52,3 |
| 30 | DFS | 242,3 | 56,6 | 167,1 |
| 30 | BFS | 112,0 | **24,5** | 167,2 |
| 30 | Dijkstra | **86,4** | 26,7 | 158,3 |

O resultado central do trabalho está nas duas colunas do meio: em 30x30 o BFS
chega em 24,5 passos e paga 112,0, enquanto o Dijkstra aceita 26,7 passos e
paga 86,4. **Menos passos não é menor custo.** O BFS otimiza a quantidade de
arestas porque trata todas como iguais; o Dijkstra é o único que enxerga o
terreno. O DFS não otimiza nada e serve de piso da comparação.

O Surf mostra o efeito do atributo sobre a forma do grafo. Em 30x30, ligar o
Surf derruba o custo do Dijkstra de 86,4 para 53,1, porque a água deixa de ser
parede e abre atalhos. O mesmo Surf faz o DFS saltar de 242,3 para 996,2: o
grafo fica maior e o DFS passeia por ele.

Partida completa, média de 30 seeds por tamanho:

| Tamanho | Algoritmo | Objetivos | Batalhas | HP perdido |
| --- | --- | --- | --- | --- |
| 8 | DFS | 4,6 | 5,9 | 149,8 |
| 8 | BFS | 6,4 | 5,0 | 140,7 |
| 8 | Dijkstra | **6,5** | 4,9 | 139,3 |
| 15 | DFS | 1,8 | 6,2 | 145,0 |
| 15 | BFS | 3,7 | 2,7 | 78,2 |
| 15 | Dijkstra | **3,9** | 2,5 | **76,5** |
| 30 | DFS | 2,4 | 15,0 | 336,3 |
| 30 | BFS | 4,0 | 3,2 | 98,8 |
| 30 | Dijkstra | **4,4** | 3,2 | **96,8** |

A penalidade de batalha no custo da aresta se traduz em partida: em 30x30 o
DFS força 15,0 batalhas e perde 336,3 de HP, contra 3,2 batalhas e 96,8 de HP
do Dijkstra. Como o time desmaia, o DFS conclui menos objetivos apesar de
andar mais passos.

A coluna `partidas_sem_objetivo` do resumo conta as partidas em que a origem
nasceu ilhada e o bot parou sem sair do lugar (5, 16 e 12 de 30, por tamanho).
Elas puxam as médias de objetivos para baixo em todos os algoritmos por igual,
e ficam explícitas em vez de descartadas.

## Testes

```powershell
python -m pytest
```

Os testes verificam o funcionamento do mapa, movimento, itens, camada de
grafo, algoritmos de busca, o bot e o benchmark, incluindo um caso em que BFS
e Dijkstra escolhem caminhos diferentes. Os testes do benchmark rodam numa
grade mínima e verificam o contrato, não o tempo: as colunas do CSV, uma linha
por algoritmo, a agregação e as duas invariantes que sustentam o relatório, de
que o Dijkstra nunca custa mais e o BFS nunca anda mais passos.

## Referência

Este projeto parte do jogo original criado por
[elchic00](https://github.com/elchic00/pokemon). A implementação atual foi
adaptada pelos alunos para a disciplina.

