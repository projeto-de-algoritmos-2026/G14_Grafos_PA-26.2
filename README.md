# Pokémon CLI com Pathfinding

Projeto de Algoritmos (FGA0124) · Grupo 14

| Matrícula | Aluno |
| --- | --- |
| 190091681 | Lucas Gabriel Antunes |
| 202045965 | Augusto Campos Duarte |

## Apresentação

[Vídeo de apresentação do trabalho](https://youtu.be/YvJO5PkX0QY)

## Sobre

Um jogo de Pokémon de terminal adaptado para comparar algoritmos de busca em
grafos. O jogador anda por um mapa em grade, encontra Pokémon selvagens,
enfrenta treinadores, coleta itens e atravessa terrenos diferentes. Sobre esse
mapa foi construída uma camada de grafo, e sobre ela três algoritmos disputam a
mesma pergunta: qual é o melhor caminho?

- **DFS**, busca em profundidade. Acha um caminho e para. Não otimiza nada.
- **BFS**, busca em largura. Minimiza o número de arestas, porque trata todas
  como equivalentes.
- **Dijkstra**, caminho de menor custo. É o único dos três que enxerga o peso
  do terreno e das batalhas.

A tese do trabalho está na diferença entre os dois últimos: **menos passos não
é menor custo**. O BFS pode escolher um trajeto curto que atravessa grama cara
e batalhas forçadas, enquanto o Dijkstra aceita andar mais para pagar menos.
Os [resultados](#resultados) medem exatamente isso.

## A interface

`python -m webdemo` sobe uma interface local, sem dependência nenhuma além das
que o projeto já usa, com três telas.

### Jogo

Jogável no teclado. Cada tecla vira uma chamada a `game.mover()`, a mesma
função que o bot usa. As casas escurecidas estão fora do componente alcançável
a partir da origem, e a coluna da direita explica o custo de cada terreno e de
cada conteúdo de célula.

![Tela do jogo, com o mapa jogável, o placar e a legenda de custos](docs/imagens/interface-jogo.png)

### Bot

O bot planeja um objetivo, calcula a rota com o algoritmo escolhido, anda passo
a passo e replaneja. Clicar numa célula compara as três rotas até ela no mesmo
estado. O log narra a partida e diz **por que** cada replanejamento aconteceu.

![Tela do bot, com o mapa, o painel de medidas e o log da partida](docs/imagens/interface-bot.png)

### Benchmark

Uma corrida com **um processo por algoritmo**, não thread: sob o GIL três
threads se revezariam e o tempo na tela não significaria nada. Cada raia roda
os dois experimentos e mostra os dois grupos de números.

![Tela do benchmark, com as tres raias correndo e o veredito](docs/imagens/interface-benchmark.png)

## Como executar

### Interface web

```powershell
python -m webdemo               # abre o navegador sozinho
python -m webdemo --porta 8770  # em outra porta
```

### Terminal

O jogo tem dois modos, mutuamente exclusivos, no mesmo executável. Em ambos o
programa pede os dados iniciais do jogador antes de começar.

```powershell
python main.py --human                      # o jogador informa W/A/S/D
python main.py --bot                        # o bot planeja e executa sozinho
python main.py --bot --visual               # mostra o plano e o mapa a cada passo
python main.py --bot --size 15 --seed 42    # mapa reproduzível
```

Sem nenhuma flag, o modo humano é o padrão. `--size` e `--seed` valem para os
dois modos: a mesma semente sempre gera o mesmo mapa.

### Benchmark em lote

```powershell
python -m bench                              # os dois experimentos e os gráficos
python -m bench --so rotas --tamanhos 8 15   # só um recorte
python -m bench --seeds 5                    # grade menor, para iterar
```

A saída vai para `bench/out/`: os CSVs por execução, os resumos agregados e os
gráficos em SVG.

### Testes

```powershell
python -m pytest
```

## Como funciona

O mapa é uma matriz de células. Cada célula tem um terreno (concreto, grama ou
água) e pode conter um Pokémon selvagem, um treinador, uma pokébola, um item de
Surf ou um bloqueio. O custo de **entrar** numa célula depende só dela:

| Célula | Custo | Regra |
| --- | ---: | --- |
| Concreto | 1 | Referência. |
| Grama | 3 a 6 | Sobe conforme o HP do líder cai: mais risco de encontro. |
| Água | 4 | A aresta **não existe** sem Surf. |
| Pokémon selvagem | +8 | Batalha forçada. |
| Treinador | +12 | Batalha forçada, prêmio maior. |
| Pokébola | +0 | Item no chão. |
| Bloqueio | n/a | A aresta não existe. |

Como o custo depende só do destino, isso é caminho mínimo com peso em
**vértice**, que converte direto para peso em **aresta**: toda aresta que chega
em `v` pesa `custo_entrada(v, estado)`. Recompensa não vira peso negativo,
porque Dijkstra não aceita aresta negativa; o benefício de um alvo vive no
score do objetivo, não no peso do caminho.

O Surf é o ponto mais interessante da modelagem: ele **não barateia** a água,
ele **cria** as arestas de água. São dois grafos sobre a mesma matriz, e o
grafo sem Surf pode ser desconexo. Quando isso acontece, "não existe caminho" é
a resposta correta do algoritmo, não uma falha.

Os três algoritmos compartilham a mesma assinatura, o que é o que torna a
comparação possível:

```text
(origem, destino, grid, estado)  ->  (caminho, custo, nos_expandidos)
```

`nos_expandidos` conta quantos vértices o algoritmo tirou da fronteira e
processou, na **saída** da fila e não na descoberta. É a medida de esforço que
não depende da máquina, ao contrário do milissegundo.

A modelagem completa, com as decisões e o porquê de cada uma, está em
[`docs/relatorio.md`](docs/relatorio.md).

## Resultados

São **dois experimentos separados**, porque respondem a perguntas diferentes.

### Rota pura

Mesmo mapa, mesma origem, mesmo destino, mesmo estado do jogador. Só o
algoritmo muda. É o único recorte em que a comparação isola a estratégia de
busca. Média de 30 seeds por tamanho, com HP 100 e sem Surf. Negrito marca o
melhor valor de cada coluna dentro do mesmo mapa.

| Mapa | Algoritmo | Custo | Passos | Nós expandidos |
| --- | --- | ---: | ---: | ---: |
| 8x8 | DFS | 43,3 | 9,5 | 17,6 |
| 8x8 | BFS | 28,0 | **6,5** | 15,1 |
| 8x8 | Dijkstra | **25,1** | 6,7 | **14,9** |
| 15x15 | DFS | 83,8 | 19,8 | **49,8** |
| 15x15 | BFS | 52,1 | **12,8** | 52,7 |
| 15x15 | Dijkstra | **47,2** | 13,4 | 51,9 |
| 30x30 | DFS | 298,0 | 67,6 | 199,6 |
| 30x30 | BFS | 114,6 | **25,8** | 183,1 |
| 30x30 | Dijkstra | **91,7** | 28,3 | **177,6** |

O resultado central está nas duas colunas do meio, e elas trocam de dono: em
30x30 o BFS chega em 25,8 passos e paga 114,6, enquanto o Dijkstra aceita 28,3
passos e paga 91,7. **Menos passos não é menor custo.** O DFS não otimiza
nenhuma das duas e serve de piso.

A coluna de nós expandidos fecha o flanco: BFS e Dijkstra varrem
aproximadamente o mesmo tanto de mapa (183,1 contra 177,6 em 30x30), então a
rota melhor do Dijkstra **não vem de olhar mais**, vem de olhar o mesmo mapa
com peso. Em 15x15 quem expande menos é o DFS, o que é esperado: ele para no
primeiro caminho que encontra, por pior que seja.

O Surf mostra o atributo mudando a **forma** do grafo. Em 30x30, ligar o Surf
derruba o custo do Dijkstra de 91,7 para 51,4, porque a água vira atalho. O
mesmo Surf faz o DFS saltar de 298,0 para 1103,5: o grafo fica maior e o DFS
passeia por ele. Se o Surf apenas baratasse uma aresta que já existia, o efeito
sobre um algoritmo que não otimiza custo seria pequeno.

Mapa cuja origem nasce cercada de água não tem destino possível e vai para
`rotas_descartes.csv` em vez de sumir da amostra: 4 seeds em 8x8, 9 em 15x15 e
8 em 30x30, de 30 cada.

### Partida completa

O bot joga do início ao fim e o algoritmo em teste calcula a rota de cada
objetivo. Não se mede a rota, e sim a consequência dela. A escolha de qual alvo
perseguir é sempre a da fase 4 (score por Dijkstra) nos três casos: trocar rota
e alvo ao mesmo tempo impediria dizer de onde veio a diferença.

| Mapa | Algoritmo | Objetivos | Passos | Batalhas | HP perdido |
| --- | --- | ---: | ---: | ---: | ---: |
| 8x8 | DFS | 4,4 | 20,7 | 5,3 | 144,7 |
| 8x8 | BFS | 6,7 | 16,5 | 5,3 | 152,3 |
| 8x8 | Dijkstra | **6,9** | 16,7 | 5,3 | 151,0 |
| 15x15 | DFS | 1,3 | 9,8 | 2,6 | 76,3 |
| 15x15 | BFS | 3,6 | 8,7 | 2,6 | 78,5 |
| 15x15 | Dijkstra | **3,9** | 9,0 | 2,5 | 76,5 |
| 30x30 | DFS | 1,9 | 13,2 | 3,1 | 100,5 |
| 30x30 | BFS | 4,1 | 11,1 | 3,1 | 102,0 |
| 30x30 | Dijkstra | **4,5** | 12,4 | 3,2 | 101,3 |

Aqui o negrito marca só a coluna de objetivos, e a razão é o próprio resultado:
**batalhas e HP não distinguem os algoritmos**, e isso é estrutural. A partida
termina quando o time completa quatro Pokémon, e a única forma de completar o
time é vencendo batalhas, então o número de batalhas até o fim é
aproximadamente fixo, qualquer que seja a rota. Marcar um vencedor nessas
colunas sugeriria uma diferença que a medição não sustenta.

O que discrimina é objetivos, lido junto com passos: em 30x30 o DFS anda 13,2
passos e conclui 1,9 objetivos, enquanto o Dijkstra anda 12,4 e conclui 4,5.
**O DFS caminha mais e realiza menos.** A vantagem do Dijkstra nesta tabela é
de aproveitamento do percurso, não de sobrevivência.

Duas ressalvas que acompanham a tabela. Os custos deste experimento **não são
comparáveis** com os da rota pura, porque o mapa muda durante a partida: célula
visitada perde a penalidade de batalha, o Surf abre a água e o HP cai e
encarece a grama. E a batalha sorteia dano, então qualquer diferença de HP
entre algoritmos é tendência sobre 30 seeds, não resultado de uma linha.

A coluna `partidas_sem_objetivo` do resumo conta as partidas em que a origem
nasceu ilhada e o bot parou sem sair do lugar (4, 16 e 11 de 30, por tamanho).
Elas puxam as médias de objetivos para baixo em todos os algoritmos por igual,
e ficam explícitas em vez de descartadas.

## Testes

A suíte cobre mapa, movimento, itens, camada de grafo, algoritmos, bot,
benchmark e a interface web. Os testes do benchmark rodam numa grade mínima e
verificam o contrato, não o tempo: as colunas do CSV, uma linha por algoritmo,
a agregação, e as duas invariantes que sustentam o relatório, de que o Dijkstra
nunca custa mais e o BFS nunca anda mais passos na mesma rota.

## Referência

Este projeto parte do jogo original criado por
[elchic00](https://github.com/elchic00/pokemon). A implementação atual foi
adaptada pelos alunos para a disciplina.
