# Relatório final: Pokémon CLI com Pathfinding

**Disciplina:** Projeto e Análise de Algoritmos (FGA0124), UnB/FGA
**Grupo 14**

| Matrícula | Aluno | Fases |
| --- | --- | --- |
| 190091681 | Lucas Gabriel Antunes | 0, 1, 2, 6, 7 |
| 202045965 | Augusto Campos Duarte | 3, 4, 5, 7 |

## 1. Introdução

O projeto parte de um jogo de Pokémon em linha de comando, fork de
[elchic00/pokemon](https://github.com/elchic00/pokemon), e adiciona sobre ele
uma camada de grafo. O mapa já existia como matriz de células com terreno,
Pokémon selvagens, treinadores e itens; o que não existia era uma
representação desse mapa que os algoritmos clássicos de busca pudessem
consumir sem conhecer a estrutura interna do jogo. As fases 0 e 1, prepararam essa base: o fork do repositório original e o planejamento das etapas seguintes do grupo.

O objetivo central é comparar três estratégias de busca (DFS, BFS e Dijkstra)
num mesmo grafo cujos pesos dependem do estado do jogador, e medir essa
comparação de dois jeitos distintos: isolando a rota em si, e observando o
efeito da rota dentro de uma partida jogada por um bot até o fim. O
argumento que sustenta o trabalho inteiro é simples de enunciar e difícil de
provar sem medição: número de passos e custo do caminho não são a mesma
coisa quando o terreno pesa, e só um algoritmo dos três enxerga isso.

Este relatório segue a ordem das fases. A seção 2 descreve a arquitetura em
camadas que separa o jogo do grafo. A seção 3 apresenta a modelagem do grafo,
incluindo as três decisões que o plano original exigia: peso em aresta em vez
de peso em vértice, recompensa fora do custo do caminho, e o grafo que muda
de forma conforme o estado do jogador. As seções 4, 5 e 6 cobrem os
algoritmos de busca, a seleção de objetivos e o bot, respectivamente. A seção 7 descreve o
benchmark da fase 6 e apresenta os resultados. A seção 8 reúne as
limitações conhecidas, e a seção 9 fecha com a conclusão.

## 2. Arquitetura em camadas

A camada de grafo vive em `graph/` e não conhece o jogo por dentro. Ela
expõe duas funções, `vizinhos()` e `arestas()`, e um objeto de estado,
`Estado`, e é só isso que os três algoritmos de busca enxergam. O
`Estado` é um `dataclass` congelado (`frozen=True`) que guarda HP do líder,
pokébolas, poções e se o jogador tem Surf. A razão de ser congelado não é
estilística: o custo de uma célula é função pura do par (célula, estado), e
o Dijkstra não pode ver esse estado mudar no meio de uma varredura, porque
isso invalidaria a invariante de menor custo que sustenta o algoritmo. Um
efeito colateral dessa escolha é que os testes de grafo constroem um
`Estado` direto, sem precisar montar um `Player`, e o benchmark da fase 6
varre estados sintéticos (HP 100, 40, com e sem Surf) sem simular uma
partida inteira.

Essa separação também é o que torna a fase 5 possível sem reescrever a fase
3: o bot chama a mesma função `dijkstra(origem, destino, grid, estado)` que
o benchmark chama, com a mesma assinatura `(caminho, custo, nós_expandidos)`
de saída. Nenhuma das duas camadas precisou ser adaptada para a outra.

## 3. Modelagem do grafo

### 3.1 Peso em vértice convertido para peso em aresta

O custo de atravessar o mapa depende do terreno da célula de destino, nunca
da célula de origem nem da direção do movimento. Essa é, por definição, uma
formulação de caminho mínimo com peso em vértice. A camada de grafo converte
isso direto para peso em aresta: toda aresta que chega num vértice `v` pesa
`custo_entrada(v, estado)`, função implementada em `graph/cost.py`. A tabela
de custo por terreno é:

| Célula | Custo |
| --- | --- |
| Concreto | 1 |
| Grama | `3 * (1 + (100 - hp) / 100)`, arredondado: 3 com HP cheio, 5 com HP 50, 6 com HP zerado |
| Água | 4, e só existe como aresta quando o jogador tem Surf |
| + Pokémon selvagem no destino | +8 |
| + treinador (CPU) no destino | +12 |
| Célula já visitada | só o terreno, sem penalidade de batalha |

Dois detalhes de implementação fecham essa conversão. Primeiro, quem decide
se uma aresta existe é `graph/adapter.py`, não `graph/cost.py`: a função
`vizinhos()` filtra o que é intransponível em vez de devolver peso
infinito, de forma que DFS, BFS e Dijkstra nunca precisam de um teste
`if peso == inf`. Segundo, o arredondamento da fórmula de grama usa
`math.floor(x + 0.5)` em vez do `round()` nativo do Python, porque
`round(4.5)` em Python aplica arredondamento bancário e devolve 4, e o
custo da grama com HP 50 cai exatamente nesse ponto de metade inteira.

### 3.2 Por que a recompensa não vira peso negativo

Pokébolas e itens de Surf têm valor para o jogador, mas esse valor nunca
entra como peso negativo de aresta. A razão é algorítmica, não estilística:
Dijkstra pressupõe pesos não negativos, e aceitar aresta negativa quebra a
invariante que garante que o primeiro nó retirado da fila de prioridade já
tem seu menor custo definitivo. A consequência prática é uma divisão de
responsabilidade explícita: o custo de entrar numa célula com pokébola é só
o custo do terreno daquela célula, e o benefício de pegar o item vive fora
do caminho mínimo, no score de objetivo calculado na fase 4
(`utilidade / distância`, em `bot/objectives.py`). O caminho mínimo resolve
"quanto custa chegar"; o score de objetivo resolve "vale a pena ir".

### 3.3 Dois grafos sobre a mesma matriz: o Surf muda a forma, não o peso

A decisão de modelagem mais consequente do trabalho é que o Surf não altera
o custo da água, ele cria a aresta da água. Sem Surf, toda célula de água é
parede e nem aparece na lista que `vizinhos()` devolve; com Surf, a água
passa a valer 4 de custo, o mesmo padrão de qualquer outro terreno. São,
portanto, dois grafos distintos sobre a mesma matriz de células, `G_sem_surf`
e `G_com_surf`, e o segundo é sempre um superconjunto de arestas do
primeiro. Essa é a razão de o grafo sem Surf poder ser desconexo: se a água
particiona o mapa em componentes isolados, "não existe caminho" é a
resposta correta do algoritmo, não um defeito do mapa ou do código. O
projeto não faz nenhuma tentativa de garantir que o item de Surf nasça no
mesmo componente da origem, decisão de modelagem tomada na fase 2 e mantida
até o fim.

Essa distinção entre "criar aresta" e "baratear aresta" não é apenas
conceitual: o benchmark da fase 6 (seção 7.4) mede o efeito prático dela, e
o sinal nos dois algoritmos que exploram o grafo de forma diferente (DFS e
Dijkstra) é oposto, o que confirma que o Surf está de fato mudando a
topologia do grafo e não apenas reduzindo pesos existentes.

### 3.4 Correções exigidas no jogo pela camada de grafo

Construir a camada de grafo expôs quatro problemas no código herdado do
jogo original, corrigidos na fase 2:

1. O jogo permitia andar sobre água. A checagem de passabilidade olhava só
`occupied_with`, e água é um atributo de `terrain`, não de conteúdo da
célula. A correção unificou a regra numa única função,
`GridSquare.pisavel(surf)`, usada tanto por `mover()` quanto por
`vizinhos()`. Sem essa unificação, o bot da fase 5 poderia planejar uma
rota que o grafo considera inexistente, ou o inverso.
2. `use_potion()` cura 40 de HP sem impor teto de 100. Com HP 140, a fórmula
de custo de grama daria 2, deixando a grama mais barata que o concreto. O
HP é limitado ao intervalo [0, 100] dentro do cálculo de custo
(`graph/cost.py`), sem alterar o comportamento da poção em si.
3. `(0, 0)` nasce forçosamente em concreto. Sortear água na origem prenderia
o jogador no canto do mapa, já que ele começa sem Surf.
4. O arredondamento por `round()` foi substituído por `floor(x + 0.5)`, pelo
motivo descrito na seção 3.1.

### 3.5 Alcançabilidade sem Surf: medição em 200 seeds

A fase 2 também mediu, e não apenas presumiu, o quanto a exigência de Surf
restringe o mapa alcançável. Com água ocupando um terço das células, a
medição em 200 seeds por tamanho de mapa deu:

| Tamanho | Alcançável sem Surf | Alcançável com Surf | Item de Surf alcançável |
| --- | --- | --- | --- |
| 8x8 | 40% do mapa | 98% | 66% das seeds com item |
| 15x15 | 33% | 98% | 62% |
| 30x30 | 30% | 98% | 62% |

A leitura direta desses números é que em cerca de um terço dos mapas o
jogador nunca chega ao item de Surf, porque o item caiu num componente
separado da origem. Essa leitura é favorável ao argumento central do
trabalho, porque isola de forma limpa o efeito do Surf sobre a topologia do
grafo, mas também é a limitação que mais reduz o rendimento do benchmark
(seção 8). A decisão de rebalancear ou não a distribuição de terreno foi
deliberadamente adiada para a fase 6, e nunca foi tomada: a distribuição
original do jogo permanece intacta.

Uma restrição foi acrescentada à geração do mapa, e ela é de natureza
diferente de um rebalanceamento: **o item de Surf não nasce em célula de
água**. Um item de Surf sobre água exige Surf para ser alcançado, ou seja,
é inatingível por construção, e não por topologia. Os dois casos produzem
o mesmo sintoma na tela e têm causas distintas: um é o resultado que a
modelagem quer mostrar, o outro é uma contradição interna da geração. A
correção troca o terreno da célula, não a posição do item, porque o que
está errado é o par `(conteúdo, terreno)` e não onde o item caiu; a
distribuição de conteúdo do mapa fica intacta. Antes da restrição, 34% dos
itens de Surf gerados na grade do benchmark estavam sobre água.

## 4. Algoritmos de busca (fase 3, Augusto Campos Duarte)

Os três algoritmos vivem em `graph/search.py` e compartilham a mesma
assinatura de entrada e saída: `(origem, destino, grid, estado)` para
`(caminho, custo, nós_expandidos)`. DFS usa uma pilha e explora os vizinhos
em ordem reversa da lista fixa W, D, S, A; BFS usa uma fila e reconstrói o
caminho por um dicionário de predecessores; Dijkstra usa uma fila de
prioridade (`heapq`) com deleção preguiçosa, descartando entradas obsoletas
quando o custo já registrado para um nó é menor do que o retirado da fila.
A ordem fixa de exploração dos vizinhos não é um detalhe estético: como o
DFS depende da ordem em que visita vizinhos para decidir qual caminho
encontra primeiro, uma ordem instável tornaria o benchmark da fase 6
incapaz de comparar execuções.

O projeto valida a divergência entre BFS e Dijkstra com um mapa fixo
construído para esse fim e duas invariantes cobertas por teste automatizado:
o Dijkstra nunca custa mais do que BFS ou DFS na mesma rota
(`test_dijkstra_nunca_custa_mais_que_bfs_ou_dfs_na_mesma_rota`), e o BFS
nunca dá mais passos do que Dijkstra ou DFS
(`test_bfs_nunca_da_mais_passos_que_dijkstra_ou_dfs`). Essas duas
invariantes são, na prática, a formalização em teste do argumento central
do trabalho, e reaparecem confirmadas nos números do benchmark (seção 7.3).

## 5. Seleção e ordenação de objetivos (fase 4, Augusto Campos Duarte)

Antes de decidir qual caminho seguir, o bot precisa decidir para onde ir.
Essa escolha, implementada em `bot/objectives.py`, atribui uma utilidade
fixa a cada tipo de conteúdo de célula (Pokémon selvagem 100, treinador 80,
item de Surf 90, pokébola 60) e calcula, para cada célula alcançável, um
score de `utilidade / distância`, usando a distância de menor custo obtida
por uma variante do Dijkstra que devolve as distâncias a todos os pontos
alcançáveis a partir da origem (`dijkstra_distancias`). Os objetivos são
ordenados por esse score, com distância e posição como critérios de
desempate, e os três melhores (`limite=3`) são selecionados como candidatos.

A ordem de visita entre esses candidatos não é a ordem do score: a função
`melhor_ordem()` testa todas as permutações desses até três alvos e escolhe
a sequência de menor custo total, usando uma matriz de distâncias par a par
calculada com o mesmo `dijkstra_distancias`. É, na prática, uma instância
pequena do problema do caixeiro viajante resolvida por força bruta, viável
porque o conjunto de alvos por rodada é limitado a três. O item de Surf já
coletado deixa de contar utilidade (`utilidade()` retorna 0 se
`estado.surf` já é verdadeiro), o que evita que o bot planeje uma segunda
visita a um item que não existe mais.

## 6. O bot (fase 5, Augusto Campos Duarte)

O bot fecha o circuito entre grafo, algoritmos e jogo executável. O loop
principal, em `bot/runner.py`, repete quatro passos até não haver mais
Pokémon vivo, até capturar quatro Pokémon, ou até esbarrar num limite de
passos: tira um retrato do estado atual do jogador (`Estado.de(player)`),
chama `planejar_visita()` para escolher e ordenar objetivos, calcula a rota
até o primeiro objetivo com a função de busca configurada (Dijkstra por
padrão) e executa essa rota célula a célula. Depois de cada rota executada,
o loop tira um novo retrato do estado e replaneja: uma batalha pode reduzir
o HP do líder, um Pokémon pode desmaiar, uma pokébola pode ser coletada, e
o item de Surf pode abrir células de água que antes eram parede, e qualquer
uma dessas mudanças pode invalidar a rota que fazia sentido um passo atrás.

A implementação foi dividida em cinco commits incrementais, cada um
mantendo a suíte de testes verde:

| Commit | Responsabilidade | O que entrega |
| --- | --- | --- |
| `cb7f18a` | Conversão de rota | `caminho_para_direcoes()` converte uma sequência de posições em comandos W/A/S/D; um trecho diagonal ou não adjacente levanta `ValueError` em vez de gerar um comando inválido. |
| `ff0f0d7` | Execução passo a passo | `executar_caminho()` converte a rota e chama `game.mover()` para cada direção, parando no primeiro movimento inválido para preservar o estado real do jogo. |
| `17a08f9` | Batalha automática | Parâmetro `automatico` em `battle()`, `mover()` e no executor; no modo automático o bot usa o primeiro golpe disponível e não chama `input()`, sem duplicar a lógica de movimento do modo humano. |
| `bbaa8df` | Loop de planejamento | `ResultadoBot` e `executar_bot()`, que registram movimentos, objetivos visitados, número de replanejamentos e motivo de parada. |
| `ca4007d` | Modos de CLI | `main.py` passa a aceitar `--bot` e `--human`, mutuamente exclusivos, preservando `--size` e `--seed` para reprodutibilidade; sem flag, o modo humano continua padrão. |

A execução de um caminho para no primeiro passo inválido ou no momento em
que o time do jogador esvazia (`bot/movement.py`), decisão que evita que o
executor continue processando uma rota depois que o jogo já terminou para
aquele jogador. A mesma garantia vale do lado do combate: `battle()` retorna
imediatamente quando o time está vazio, porque batalha sem Pokémon não é
batalha válida para nenhum chamador. As duas travas têm teste de regressão
próprio.

Uma limitação foi documentada pelo próprio Augusto na fase 5, e é a mesma
que a modelagem da fase 2 já havia previsto: algumas combinações de tamanho
e semente geram origem cercada de água, e como o jogador começa sem Surf, o
componente alcançável nesses casos é apenas `(0, 0)`. O bot responde com
"sem objetivos alcançáveis" nessa situação, e o registro da fase 5 é
explícito de que isso não é falha do Dijkstra: o algoritmo está refletindo
corretamente o grafo que o mapa produziu.

## 7. Benchmark (fase 6, Lucas Gabriel Antunes)

### 7.1 Por que dois experimentos, e não um

O plano original previa uma única grade de medição. Rodar essa grade tornou
claro que ela responderia duas perguntas ao mesmo tempo e misturaria as
respostas. A primeira pergunta é sobre o algoritmo isolado: dado o mesmo
mapa, a mesma origem, o mesmo destino e o mesmo estado do jogador, o que
muda quando só o algoritmo muda. A segunda é sobre a consequência de uma
rota dentro de uma partida real, em que o mapa muda enquanto o bot joga. O
benchmark foi dividido em dois módulos, `bench/rotas.py` e
`bench/partidas.py`, para que cada um respondesse a uma pergunta só.

### 7.2 Decisões de desenho

Seis decisões sustentam a validade da comparação:

1. Os destinos do experimento de rota são sorteados dentro do componente
alcançável sem Surf. Como o Surf só acrescenta arestas, um destino
escolhido nesse componente permanece alcançável nos três estados testados,
o que permite comparar a mesma linha entre HP 100, HP 40 e HP 100 com Surf.
2. Um mapa cuja origem nasce cercada de água não é descartado em silêncio:
vai para `rotas_descartes.csv`, porque a frequência desse evento é
resultado do trabalho, não ruído da amostra.
3. A escolha dos objetivos no experimento de partida é sempre a da fase 4
(score por Dijkstra), nos três algoritmos testados. Só a rota até o alvo
muda. Trocar rota e alvo ao mesmo tempo misturaria duas variáveis e
impediria dizer de onde veio a diferença observada.
4. O experimento de rota testa três estados de jogador: HP 100, HP 40 e HP
100 com Surf. São os dois jeitos distintos, e independentes, de o estado do
jogador alterar o grafo: HP encarece a grama sem tocar a topologia, e Surf
cria arestas sem tocar o custo de nenhuma aresta pré-existente.
5. O tempo medido é o menor entre repetições da mesma medição, não a
média, porque ruído de agendamento do sistema operacional só consegue
empurrar uma medição de tempo para cima, nunca para baixo.
6. Os gráficos foram escritos em SVG puro, sem `matplotlib`, porque o
projeto já declara duas dependências e o gráfico pedido é uma linha por
algoritmo contra três tamanhos de mapa, o que cabe na biblioteca padrão do
Python e resulta num arquivo versionável como texto.

### 7.3 Resultado: rota pura, HP 100, sem Surf, média de 30 seeds

| Tamanho | Algoritmo | Custo médio | Passos médios | Nós expandidos |
| --- | --- | --- | --- | --- |
| 8 | DFS | 43,3 | 9,5 | 17,6 |
| 8 | BFS | 28,0 | 6,5 | 15,1 |
| 8 | Dijkstra | 25,1 | 6,7 | 14,9 |
| 15 | DFS | 83,8 | 19,8 | 49,8 |
| 15 | BFS | 52,1 | 12,8 | 52,7 |
| 15 | Dijkstra | 47,2 | 13,4 | 51,9 |
| 30 | DFS | 298,0 | 67,6 | 199,6 |
| 30 | BFS | 114,6 | 25,8 | 183,1 |
| 30 | Dijkstra | 91,7 | 28,3 | 177,6 |

O dado que sustenta o argumento central está nas duas colunas do meio da
última linha: em mapas 30x30 o BFS chega ao destino em 25,8 passos e paga
114,6 de custo, enquanto o Dijkstra aceita andar mais, 28,3 passos, e paga
menos, 91,7. A leitura desse contraste é que menos passos não é o mesmo que
menor custo: o BFS otimiza a quantidade de arestas percorridas porque trata
todas como equivalentes, e o Dijkstra é o único dos três que enxerga o peso
do terreno ao decidir o caminho. O DFS não otimiza nenhuma das duas
métricas e funciona como piso de comparação, sempre com o maior custo e
mais passos nos três tamanhos medidos.

### 7.4 Resultado: o Surf muda a forma do grafo, não o peso

Em mapas 30x30, ligar o Surf derruba o custo médio do Dijkstra de 91,7 para
51,4: a água deixa de ser parede e passa a oferecer atalho. O mesmo Surf
faz o custo médio do DFS saltar de 298,0 para 1103,5. A leitura desse
contraste, e não apenas do número isolado, é a evidência direta da
modelagem da seção 3.3: se o Surf apenas baixasse o preço de uma aresta que
já existia, o efeito sobre um algoritmo que não otimiza custo (o DFS)
deveria ser neutro ou pequeno. O efeito é o oposto do observado no
Dijkstra porque o grafo, não o preço, mudou de tamanho, e o DFS passeia por
um grafo maior sem qualquer critério de poda.

### 7.5 Resultado: partida completa, média de 30 seeds

| Tamanho | Algoritmo | Objetivos médios | Passos médios | Batalhas médias | HP perdido médio |
| --- | --- | --- | --- | --- | --- |
| 8 | DFS | 4,4 | 20,7 | 5,3 | 144,7 |
| 8 | BFS | 6,7 | 16,5 | 5,3 | 152,3 |
| 8 | Dijkstra | 6,9 | 16,7 | 5,3 | 151,0 |
| 15 | DFS | 1,3 | 9,8 | 2,6 | 76,3 |
| 15 | BFS | 3,6 | 8,7 | 2,6 | 78,5 |
| 15 | Dijkstra | 3,9 | 9,0 | 2,5 | 76,5 |
| 30 | DFS | 1,9 | 13,2 | 3,1 | 100,5 |
| 30 | BFS | 4,1 | 11,1 | 3,1 | 102,0 |
| 30 | Dijkstra | 4,5 | 12,4 | 3,2 | 101,3 |

A leitura desta tabela precisa começar pelo que ela **não** mostra. As
colunas de batalhas e de HP perdido praticamente não distinguem os três
algoritmos: em mapas 30x30 são 3,1 batalhas do DFS contra 3,2 do Dijkstra, e
100,5 de HP contra 101,3. Isso tem uma explicação estrutural, e não é ruído
de amostra: a partida termina quando o time completa quatro Pokémon, e a
única forma de completar o time é vencendo batalhas. O número de batalhas
até o fim é, portanto, aproximadamente fixo por construção, independente da
rota escolhida para chegar até elas.

A coluna que discrimina é a de objetivos concluídos, lida junto com a de
passos. Em mapas 30x30 o DFS anda 13,2 passos e conclui 1,9 objetivos,
enquanto o Dijkstra anda 12,4 passos e conclui 4,5. O DFS caminha mais e
realiza menos: como cada rota dele é um desvio longo, o time se completa
antes que os objetivos seguintes sejam alcançados, e a partida acaba com o
mapa pouco explorado. A vantagem do Dijkstra nesta tabela é de
aproveitamento do percurso, não de sobrevivência.

Três ressalvas metodológicas precisam acompanhar essa tabela, e nenhuma
delas foi suavizada para fortalecer o resultado:

- A batalha sorteia dano. A semente global de aleatoriedade é fixada por
partida, de modo que os três algoritmos começam com o mesmo fluxo de
sorteio, mas essa igualdade se rompe assim que o número de batalhas diverge
entre eles. Qualquer diferença de HP perdido entre algoritmos é, portanto,
uma tendência sobre 30 sementes, não um resultado exato reproduzível de uma
única linha, e as diferenças observadas nesta tabela são pequenas demais
para sustentar afirmação de superioridade em HP.
- A condição de vitória limita o que este experimento consegue medir. Como o
time se completa vencendo batalhas, o número de batalhas por partida é
aproximadamente constante, e por isso batalhas e HP não são métricas
discriminantes aqui. O experimento de rota pura (seção 7.3) continua sendo
o que compara custo de caminho.
- Os custos desta tabela não são comparáveis com os da tabela de rota pura
(seção 7.3), porque o mapa muda durante a execução da partida: uma célula
visitada perde a penalidade de batalha, o Surf abre água conforme é
coletado, e o HP cai e encarece a grama ao longo do jogo.
- A escolha de qual objetivo perseguir é sempre a da fase 4, calculada por
Dijkstra, nos três algoritmos testados. O que muda entre as linhas da
tabela é só a rota até esse objetivo, nunca o objetivo em si.

A coluna que o resumo agregado chama de `partidas_sem_objetivo` registra as
partidas em que a origem nasceu ilhada e o bot parou sem sair do lugar: 4,
16 e 11 partidas em 30, para os tamanhos 8, 15 e 30 respectivamente. Essas
partidas puxam a média de objetivos concluídos para baixo igualmente nos
três algoritmos, e por isso ficam explícitas na tabela agregada em vez de
descartadas da amostra.

## 8. Limitações

A limitação mais estrutural do trabalho não é um defeito de código: é a
consequência direta e prevista da decisão de modelagem da seção 3.3. Sem
Surf, um mapa pode nascer com a origem cercada de água, o componente
alcançável se reduz a `(0, 0)`, e "não existe caminho" é a resposta
correta do algoritmo diante desse grafo, não um erro a corrigir. Essa
limitação foi medida, não escondida: no experimento de rota pura, 21 dos 90
mapas gerados (4 em 8x8, 9 em 15x15 e 8 em 30x30) foram descartados por
falta de destino alcançável sem Surf; no experimento de partida completa,
4, 16 e 11 partidas em 30 por tamanho terminaram sem nenhum objetivo
concluído pelo mesmo motivo. A distribuição de terreno do jogo original,
com água ocupando um terço das células, não foi alterada em nenhuma fase do
trabalho; rebalancear essa distribuição é um ajuste possível para trabalhos
futuros, não uma correção que o grupo considerou obrigatória.

Uma segunda limitação é metodológica e afeta apenas o experimento de
partida completa: a própria condição de vitória, completar quatro Pokémon
vencendo batalhas, fixa aproximadamente o número de batalhas por partida.
Com isso, batalhas e HP perdido não separam os algoritmos, e o que este
experimento consegue medir é aproveitamento de percurso, ou seja quantos
objetivos o bot conclui antes de a partida terminar. Somado ao dano
sorteado da batalha, isso significa que qualquer diferença de HP entre DFS,
BFS e Dijkstra é tendência sobre 30 sementes, não resultado determinístico.
Ampliar essa amostra, ou fixar sementes de batalha independentes por
algoritmo, é um ajuste que poderia reduzir essa variância em um trabalho
futuro.

Uma terceira limitação é de escopo, herdada da fase 5: a batalha automática
do bot sempre usa o primeiro golpe disponível, sem nenhuma estratégia de
seleção. Essa simplicidade foi deliberada para permitir que o bot
atravessasse encontros sem travar em `input()`, e uma estratégia de batalha
mais sofisticada permanece como extensão possível, não como parte do
escopo desta fase.

## 9. Conclusão

O trabalho respondeu à pergunta que motivou a modelagem do grafo: número de
passos e custo do caminho divergem assim que o terreno carrega peso, e
apenas o Dijkstra otimiza o segundo. Essa divergência foi comprovada em
código, com duas invariantes cobertas por teste automatizado, e medida em
benchmark, com o Dijkstra pagando 91,7 de custo contra 114,6 do BFS em
mapas 30x30 percorrendo uma rota apenas 2,2 passos mais longa. A decisão de
representar Surf como criação de aresta, e não como redução de peso, foi
igualmente confirmada pelo experimento: o mesmo Surf que derruba o custo do
Dijkstra em mapas 30x30 de 91,7 para 51,4 faz o DFS, que não otimiza custo
algum, saltar de 298,0 para 1103,5, porque o que mudou foi o tamanho do
grafo, não o preço de uma aresta já existente.

A separação em dois experimentos, rota pura e partida completa, mostrou que
a vantagem do Dijkstra não fica restrita ao papel, mas também delimitou até
onde ela vai. Em partida completa, batalhas e HP perdido não separam os
três algoritmos, porque a condição de vitória fixa aproximadamente o número
de batalhas necessárias. O que se traduz em jogo é o aproveitamento do
percurso: em mapas 30x30 o DFS anda 13,2 passos e conclui 1,9 objetivos,
enquanto o Dijkstra anda 12,4 e conclui 4,5. Ao mesmo tempo, a limitação de alcançabilidade sem Surf, que
descarta entre 27% e 30% dos mapas do experimento de rota pura, mostra que
o argumento do trabalho depende de uma escolha de modelagem que tem custo
real sobre o rendimento do próprio benchmark, custo que o grupo optou por
medir e relatar em vez de contornar rebalanceando a geração de mapas.

Como extensão futura, os dois pontos mais concretos deixados em aberto pelo
próprio trabalho são a estratégia de batalha automática do bot, atualmente
reduzida ao primeiro golpe disponível, e o rebalanceamento da proporção de
água no mapa, que hoje limita a amostra útil do benchmark de rota em mapas
pequenos a pouco mais de dois terços das sementes geradas.
