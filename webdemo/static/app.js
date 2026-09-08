/* Demo do G14. Nenhuma regra de jogo aqui: esta camada so desenha o que o
   Python manda e devolve cliques e teclas. Se uma conta aparecer neste
   arquivo, ela esta no lugar errado. */

"use strict";

const $ = (sel, raiz = document) => raiz.querySelector(sel);
const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];

/* Os mesmos simbolos do terminal, pra quem ja viu o jogo rodando reconhecer
   a tela. Vem de grid.EMOJI. */
const GLIFO = {
  bloqueio: "\u{1F6B7}",
  livre: "\u{1F334}",
  pokemon: "\u{1F994}",
  pokebola: "\u{26D4}",
  cpu: "\u{1F94A}",
  surf: "\u{1F3C4}",
  visitado: "✅",
};
const JOGADOR = "\u{1FAE1}";
const CORES = { dfs: "#f0798a", bfs: "#4fc7b6", dijkstra: "#7ea8dd" };
const TERRENO = { concrete: "concreto", grass: "grama", water: "agua" };
const NOMES = { dfs: "DFS", bfs: "BFS", dijkstra: "Dijkstra" };

async function pedir(rota, parametros = {}) {
  const url = new URL(rota, location.origin);
  Object.entries(parametros).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });
  const resposta = await fetch(url);
  if (!resposta.ok) throw new Error(`${rota} respondeu ${resposta.status}`);
  return resposta.json();
}

/* ============================ tabuleiro ============================ */

class Tabuleiro {
  constructor(elemento) {
    this.el = elemento;
    this.celulas = [];
    this.size = 0;
    this.aoClicar = null;
  }

  montar(dados) {
    this.size = dados.size;
    this.el.replaceChildren();
    this.el.style.gridTemplateColumns = `repeat(${this.size}, 1fr)`;
    this.celulas = [];

    const alcancaveis = new Set((dados.alcancaveis || []).map(([r, c]) => `${r}-${c}`));
    const temAlcance = alcancaveis.size > 0;

    for (let r = 0; r < this.size; r += 1) {
      const linha = [];
      for (let c = 0; c < this.size; c += 1) {
        const celula = document.createElement("div");
        celula.className = "celula";
        celula.dataset.r = r;
        celula.dataset.c = c;
        const info = dados.celulas[r][c];
        celula.title = `(${r}, ${c}) ${info.conteudo} sobre ${TERRENO[info.terreno] || info.terreno}`;
        if (temAlcance && !alcancaveis.has(`${r}-${c}`) && !(r === 0 && c === 0)) {
          celula.classList.add("inalcancavel");
          celula.title += " | fora do alcance da origem neste estado";
        }
        celula.addEventListener("click", () => {
          if (this.aoClicar) this.aoClicar(r, c);
        });
        this.el.appendChild(celula);
        linha.push(celula);
        this.pintar(r, c, dados.celulas[r][c]);
      }
      this.celulas.push(linha);
    }

    this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    this.svg.setAttribute("class", "rota-svg");
    this.svg.setAttribute("viewBox", `0 0 ${this.size} ${this.size}`);
    this.svg.setAttribute("preserveAspectRatio", "none");
    this.el.appendChild(this.svg);

    this.moverJogador(dados.posicao);
  }

  pintar(r, c, dadosCelula) {
    const celula = this.celulas[r] && this.celulas[r][c];
    const alvo = celula || this.el.children[r * this.size + c];
    if (!alvo) return;
    alvo.classList.remove("grass", "water", "bloqueio", "visitado");
    if (dadosCelula.conteudo === "bloqueio") alvo.classList.add("bloqueio");
    else if (dadosCelula.conteudo === "visitado") alvo.classList.add("visitado");
    else if (dadosCelula.terreno === "grass") alvo.classList.add("grass");
    else if (dadosCelula.terreno === "water") alvo.classList.add("water");
    // o glifo proprio da celula fica guardado: o jogador passa por cima dela e
    // precisa devolver o simbolo certo ao sair, senao cada casa por onde ele
    // andou fica com a cara dele
    alvo.dataset.glifo = GLIFO[dadosCelula.conteudo] || "";
    alvo.textContent = alvo.dataset.glifo;
  }

  moverJogador([r, c]) {
    if (this.jogador) {
      this.jogador.classList.remove("jogador");
      this.jogador.textContent = this.jogador.dataset.glifo || "";
    }
    const celula = this.celulas[r] && this.celulas[r][c];
    if (celula) {
      celula.classList.add("jogador");
      celula.textContent = JOGADOR;
      this.jogador = celula;
    }
    this.posicao = [r, c];
  }

  marcarDestino([r, c]) {
    if (this.destino) this.destino.classList.remove("destino");
    const celula = this.celulas[r] && this.celulas[r][c];
    if (celula) {
      celula.classList.add("destino");
      this.destino = celula;
    }
  }

  limparRotas() {
    if (this.svg) this.svg.replaceChildren();
  }

  marcarObjetivos(candidatos) {
    this.el.querySelectorAll(".alvo").forEach((e) => e.remove());
    this.el.querySelectorAll(".candidato").forEach((e) => e.classList.remove("candidato"));
    candidatos.forEach((alvo) => {
      const [r, c] = alvo.posicao;
      const celula = this.celulas[r] && this.celulas[r][c];
      if (!celula) return;
      if (!alvo.selecionado) {
        celula.classList.add("candidato");
        return;
      }
      const marca = document.createElement("span");
      marca.className = "alvo";
      marca.textContent = alvo.visita;
      marca.title = `objetivo ${alvo.visita}: ${alvo.conteudo}, utilidade ${alvo.utilidade}, distancia ${alvo.distancia}`;
      celula.appendChild(marca);
    });
  }

  /* Desenha um caminho como polilinha ligando o centro das celulas. As tres
     rotas saem com espessura decrescente pra que trecho comum nao esconda
     ninguem: o DFS por baixo e mais grosso, o Dijkstra por cima e mais fino. */
  desenharRota(caminho, cor, espessura = 0.22, opacidade = 1) {
    if (!this.svg || !caminho || caminho.length < 2) return;
    const linha = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    linha.setAttribute("points", caminho.map(([r, c]) => `${c + 0.5},${r + 0.5}`).join(" "));
    linha.setAttribute("fill", "none");
    linha.setAttribute("stroke", cor);
    linha.setAttribute("stroke-width", espessura);
    linha.setAttribute("stroke-linejoin", "round");
    linha.setAttribute("stroke-linecap", "round");
    linha.setAttribute("opacity", opacidade);
    this.svg.appendChild(linha);
  }
}

function preencherHud(elemento, pares) {
  elemento.replaceChildren();
  pares.forEach(([rotulo, valor]) => {
    const bloco = document.createElement("div");
    const dt = document.createElement("dt");
    dt.textContent = rotulo;
    const dd = document.createElement("dd");
    dd.textContent = valor;
    bloco.append(dt, dd);
    elemento.appendChild(bloco);
  });
}

/* ============================ abas ============================ */

function trocarVista(nome) {
  $$(".aba").forEach((a) => a.classList.toggle("ativa", a.dataset.vista === nome));
  $$(".vista").forEach((v) => v.classList.toggle("ativa", v.id === `vista-${nome}`));
  // a legenda so faz sentido onde existe mapa; no benchmark ela vira espaco
  // morto e o layout precisa da largura inteira pras tres raias.
  document.body.classList.toggle("vista-bench", nome === "bench");
}

$$(".aba").forEach((aba) => {
  aba.addEventListener("click", () => trocarVista(aba.dataset.vista));
});

/* O item de Surf e a mecanica que faz o grafo mudar de forma, e e a que mais
   frustra na demo: ele pode nascer num componente separado da origem e ai
   ninguem pega. A tela diz isso, e oferece uma seed onde da pra pegar. */
function descreverSurf(itens) {
  if (!itens || !itens.length) return "este mapa nao tem item de Surf.";
  const pegaveis = itens.filter((i) => i.alcancavel);
  const onde = (i) => `(${i.posicao.join(", ")})`;
  if (!pegaveis.length) {
    return `item de Surf em ${itens.map(onde).join(" ")}: fora do componente da origem, nao da pra pegar sem Surf. E a limitacao medida na fase 2, nao um defeito.`;
  }
  return `item de Surf pegavel em ${pegaveis.map(onde).join(" ")}${
    pegaveis.length < itens.length ? ` (os outros estao fora do alcance)` : ""}.`;
}

async function acharSeedComSurf(vista) {
  const campoSize = $(`#${vista}-size`);
  const campoSeed = $(`#${vista}-seed`);
  const destino = vista === "jogo" ? $("#jogo-surf") : $("#bot-surf-status");
  destino.textContent = "procurando...";
  const dados = await pedir("/api/seed-com-surf", {
    size: campoSize.value,
    de: Number(campoSeed.value) + 1,
  });
  if (!dados.encontrou) {
    destino.textContent = `nenhuma seed com Surf pegavel em ${dados.procuradas} tentativas.`;
    return;
  }
  campoSeed.value = dados.seed;
  if (vista === "jogo") await novoJogo();
  else await carregarMapaBot();
}

$$("button[data-surf]").forEach((botao) => {
  botao.addEventListener("click", () => acharSeedComSurf(botao.dataset.surf));
});

/* ============================ vista: jogo ============================ */

const jogo = {
  tabuleiro: new Tabuleiro($("#jogo-grade")),
  sessao: null,
};

async function novoJogo() {
  const dados = await pedir("/api/jogo/novo", {
    size: $("#jogo-size").value,
    seed: $("#jogo-seed").value,
  });
  jogo.sessao = dados.sessao;
  jogo.tabuleiro.montar(dados);
  atualizarHudJogo(dados.jogador);
  $("#jogo-surf").textContent = descreverSurf(dados.itens_surf);
  $("#jogo-msg").textContent =
    `partida nova. objetivo: capturar ${dados.jogador.meta} pokemon, a mesma condicao de fim do bot.`;
}

function atualizarHudJogo(jogador) {
  preencherHud($("#jogo-hud"), [
    ["objetivo", `${jogador.pokemon} de ${jogador.meta} pokemon`],
    ["hp do lider", jogador.hp_lider],
    ["pokebolas", jogador.pokebolas],
    ["surf", jogador.surf ? "sim" : "nao"],
    ["situacao", jogador.situacao],
  ]);
}

const TECLAS = {
  w: "W", a: "A", s: "S", d: "D",
  ArrowUp: "W", ArrowLeft: "A", ArrowDown: "S", ArrowRight: "D",
};

document.addEventListener("keydown", async (evento) => {
  if (!$("#vista-jogo").classList.contains("ativa")) return;
  if (evento.target.tagName === "INPUT") return;
  const direcao = TECLAS[evento.key] || TECLAS[evento.key.toLowerCase()];
  if (!direcao || !jogo.sessao) return;
  evento.preventDefault();

  const resposta = await pedir("/api/jogo/mover", { sessao: jogo.sessao, direcao });
  if (resposta.erro) {
    $("#jogo-msg").textContent = resposta.erro;
    return;
  }
  if (resposta.valido) {
    const [r, c] = resposta.posicao;
    jogo.tabuleiro.pintar(r, c, resposta.celula);
    jogo.tabuleiro.moverJogador(resposta.posicao);
    const eventos = [];
    if (resposta.batalhou) eventos.push(`batalha (${resposta.hp_perdido} de HP)`);
    if (resposta.pegou_pokebola) eventos.push("pegou uma pokebola");
    if (resposta.pegou_surf) eventos.push("aprendeu Surf, a agua abriu");
    $("#jogo-msg").textContent = eventos.length
      ? `${direcao}: ${eventos.join(", ")}`
      : `${direcao}: ok`;
  } else {
    $("#jogo-msg").textContent = `${direcao}: recusado (${resposta.motivo})`;
  }
  atualizarHudJogo(resposta.jogador);
  if (resposta.jogador.situacao === "vitoria") {
    $("#jogo-msg").textContent = `venceu: ${resposta.jogador.motivo}. e a mesma condicao que encerra o bot.`;
  } else if (resposta.jogador.situacao === "derrota") {
    $("#jogo-msg").textContent = `fim: ${resposta.jogador.motivo}. comece uma partida nova.`;
  }
});

$("#jogo-novo").addEventListener("click", novoJogo);

/* ============================ vista: bot ============================ */

const bot = {
  tabuleiro: new Tabuleiro($("#bot-grade")),
  fonte: null,
  fila: [],
  tocando: false,
};

function parametrosBot() {
  return {
    size: $("#bot-size").value,
    seed: $("#bot-seed").value,
    hp: $("#bot-hp").value,
    surf: $("#bot-surf").checked ? 1 : 0,
  };
}

async function carregarMapaBot() {
  const dados = await pedir("/api/mapa", parametrosBot());
  bot.tabuleiro.montar(dados);
  bot.tabuleiro.aoClicar = compararRota;
  preencherHud($("#bot-hud"), [
    ["mapa", `${dados.size}x${dados.size}`],
    ["seed", dados.seed],
    ["alcancaveis", `${dados.alcancaveis.length}/${dados.size * dados.size}`],
    ["surf", dados.estado.surf ? "sim" : "nao"],
  ]);
  $("#bot-surf-status").textContent = descreverSurf(dados.itens_surf);
  $("#bot-msg").textContent = "clique numa celula alcancavel pra comparar as tres rotas.";
  $("#bot-rotas").replaceChildren();
  $("#bot-status").replaceChildren();
  await carregarObjetivos();
}

async function carregarObjetivos() {
  const dados = await pedir("/api/objetivos", parametrosBot());
  // So os candidatos que disputam de perto ganham marca no mapa. Marcar todos
  // significa tracejar quase toda celula com pokemon, treinador ou item, e ai
  // a marca deixa de distinguir coisa nenhuma.
  const disputando = dados.candidatos.slice(0, 6);
  bot.objetivos = disputando;
  bot.tabuleiro.marcarObjetivos(disputando);
}

async function compararRota(r, c) {
  const dados = await pedir("/api/rota", { ...parametrosBot(), destino: `${r}-${c}` });
  bot.tabuleiro.limparRotas();
  bot.tabuleiro.marcarDestino([r, c]);

  const rotas = dados.rotas;
  const achadas = Object.entries(rotas).filter(([, v]) => v.encontrou);
  const menorCusto = Math.min(...achadas.map(([, v]) => v.custo), Infinity);
  const menosPassos = Math.min(...achadas.map(([, v]) => v.passos), Infinity);

  const espessuras = { dfs: 0.3, bfs: 0.2, dijkstra: 0.12 };
  ["dfs", "bfs", "dijkstra"].forEach((nome) => {
    if (rotas[nome] && rotas[nome].encontrou) {
      bot.tabuleiro.desenharRota(rotas[nome].caminho, CORES[nome], espessuras[nome], 0.95);
    }
  });

  const alvo = $("#bot-rotas");
  alvo.replaceChildren();
  ["dfs", "bfs", "dijkstra"].forEach((nome) => {
    const rota = rotas[nome];
    if (!rota) return;
    const cartao = document.createElement("div");
    cartao.className = `cartao ${nome}${rota.encontrou ? "" : " sem-rota"}`;
    cartao.innerHTML = `
      <b>${NOMES[nome]}</b>
      <span><span class="metrica">custo</span>
        <span class="valor ${rota.custo === menorCusto ? "melhor" : ""}">${rota.encontrou ? rota.custo : "-"}</span></span>
      <span><span class="metrica">passos</span>
        <span class="valor ${rota.passos === menosPassos && rota.encontrou ? "melhor" : ""}">${rota.encontrou ? rota.passos : "-"}</span></span>
      <span><span class="metrica">nos</span>
        <span class="valor">${rota.nos_expandidos}</span></span>`;
    alvo.appendChild(cartao);
  });

  $("#bot-msg").textContent = achadas.length
    ? `destino (${r}, ${c}): amarelo marca quem ganhou cada coluna.`
    : `destino (${r}, ${c}) nao tem caminho neste estado. sem Surf, a agua e parede.`;
}

/* O stream chega instantaneo; o passo e desenhado num ritmo legivel. O dado
   nao muda, so a velocidade com que ele aparece. */
function enfileirar(acao) {
  bot.fila.push(acao);
  if (!bot.tocando) tocarFila();
}

function tocarFila() {
  bot.tocando = true;
  const proximo = bot.fila.shift();
  if (!proximo) {
    bot.tocando = false;
    return;
  }
  proximo();
  setTimeout(tocarFila, Number($("#bot-ritmo").value));
}

/* A linha de status sozinha nao conta a historia: ela e sobrescrita a cada
   passo e some. O log guarda a sequencia de decisoes, que e o que a plateia
   precisa pra entender por que o bot foi pra onde foi. */
function registrar(tipo, texto, marcador = "") {
  const lista = $("#bot-log");
  const item = document.createElement("li");
  item.className = tipo;
  item.innerHTML = `<span class="passo">${marcador}</span><span>${texto}</span>`;
  lista.appendChild(item);
  while (lista.children.length > 60) lista.removeChild(lista.firstChild);
  lista.scrollTop = lista.scrollHeight;
}

function verBotJogar(algoritmo) {
  if (bot.fonte) bot.fonte.close();
  bot.fila = [];
  bot.tocando = false;
  $$("#vista-bot button[data-algoritmo]").forEach((b) => { b.disabled = true; });
  $("#bot-status").replaceChildren();
  $("#bot-log").replaceChildren();
  $("#bot-msg").textContent = `${NOMES[algoritmo]} planejando...`;
  registrar("plano", `${NOMES[algoritmo]} assume o mapa. Objetivo do jogo: 4 pokemon.`, "0");

  const url = new URL("/api/partida", location.origin);
  Object.entries({ ...parametrosBot(), algoritmo }).forEach(([k, v]) =>
    url.searchParams.set(k, v));
  const fonte = new EventSource(url);
  bot.fonte = fonte;
  let objetivos = 0;
  let passoGlobal = 0;
  let passoNoPlano = 0;
  let passosDoPlano = 0;
  let alvoAtual = null;

  fonte.addEventListener("inicio", (evento) => {
    const dados = JSON.parse(evento.data);
    bot.tabuleiro.montar(dados);
    bot.tabuleiro.aoClicar = compararRota;
    if (bot.objetivos) bot.tabuleiro.marcarObjetivos(bot.objetivos);
    atualizarHudBot(dados.jogador, 0, 0, 0, 0, null);
  });

  fonte.addEventListener("plano", (evento) => {
    const dados = JSON.parse(evento.data);
    enfileirar(() => {
      bot.tabuleiro.limparRotas();
      bot.tabuleiro.marcarDestino(dados.destino);
      bot.tabuleiro.desenharRota(dados.caminho, CORES[algoritmo], 0.18, 0.9);
      objetivos += 1;
      passoNoPlano = 0;
      passosDoPlano = dados.caminho.length - 1;
      alvoAtual = dados.destino;
      $("#bot-msg").textContent =
        `plano ${objetivos}: ate (${dados.destino.join(", ")}), ${passosDoPlano} passos, custo ${dados.custo}.`;
      registrar("plano",
        `<b>replaneja</b> porque ${dados.motivos.join("; ")}. Escolhe (${dados.destino.join(", ")}): ${passosDoPlano} passos, custo ${dados.custo}, ${dados.nos_expandidos} nos expandidos.`,
        `#${objetivos}`);
    });
  });

  fonte.addEventListener("passo", (evento) => {
    const dados = JSON.parse(evento.data);
    enfileirar(() => {
      passoGlobal += 1;
      if (!dados.valido) {
        $("#bot-msg").textContent = `passo recusado: ${dados.motivo}`;
        registrar("batalha", `passo recusado pelo jogo: ${dados.motivo}.`, passoGlobal);
        return;
      }
      passoNoPlano += 1;
      const [r, c] = dados.posicao;
      bot.tabuleiro.pintar(r, c, { terreno: "concrete", conteudo: "visitado" });
      bot.tabuleiro.moverJogador(dados.posicao);
      atualizarHudBot(dados.jogador, objetivos, passoGlobal, passoNoPlano, passosDoPlano, alvoAtual);

      const eventos = [];
      if (dados.batalhou) eventos.push(`batalha, ${dados.hp_perdido} de HP`);
      if (dados.pegou_pokebola) eventos.push("pegou pokebola");
      if (dados.pegou_surf) eventos.push("APRENDEU SURF, a agua virou aresta");
      const chegou = alvoAtual && r === alvoAtual[0] && c === alvoAtual[1];

      const tipo = dados.pegou_surf || dados.pegou_pokebola
        ? "item" : (dados.batalhou ? "batalha" : "");
      const cauda = eventos.length ? ` | ${eventos.join(", ")}` : "";
      registrar(tipo,
        `${dados.direcao} para (${r}, ${c})${cauda}${chegou ? " | objetivo alcancado" : ""}`,
        passoGlobal);

      $("#bot-msg").textContent = eventos.length
        ? `passo ${passoNoPlano}/${passosDoPlano}: ${eventos.join(", ")}.`
        : `passo ${passoNoPlano}/${passosDoPlano} rumo a (${alvoAtual ? alvoAtual.join(", ") : "?"}).`;
    });
  });

  fonte.addEventListener("fim", (evento) => {
    const dados = JSON.parse(evento.data);
    /* Fecha AGORA, nao no fim da animacao. O EventSource reconecta sozinho
       quando o servidor encerra a resposta, e uma fonte ainda aberta enquanto
       a fila toca faria a partida inteira recomecar sozinha. */
    fonte.close();
    enfileirar(() => {
      $$("#vista-bot button[data-algoritmo]").forEach((b) => { b.disabled = false; });
      if (dados.erro) {
        $("#bot-msg").textContent = `erro no servidor: ${dados.erro}`;
        return;
      }
      $("#bot-msg").textContent = `fim: ${dados.motivo_parada}.`;
      registrar("fim",
        `fim: ${dados.motivo_parada}. ${dados.objetivos_concluidos} objetivos, ${dados.passos} passos, ${dados.batalhas} batalhas, ${dados.hp_perdido} de HP perdido, ${dados.replanejamentos} replanejamentos.`,
        passoGlobal);
      const cartao = document.createElement("div");
      cartao.className = `cartao ${algoritmo}`;
      cartao.innerHTML = `
        <b>${NOMES[algoritmo]}</b>
        <span><span class="metrica">objetivos</span><span class="valor">${dados.objetivos_concluidos}</span></span>
        <span><span class="metrica">batalhas</span><span class="valor">${dados.batalhas}</span></span>
        <span><span class="metrica">hp perdido</span><span class="valor">${dados.hp_perdido}</span></span>`;
      $("#bot-status").appendChild(cartao);
      atualizarHudBot(dados.jogador, dados.objetivos_concluidos, dados.passos, 0, 0, null);
    });
  });

  fonte.onerror = () => {
    // fechamento normal tambem passa por aqui; so importa se a partida nao
    // chegou ao fim, e nesse caso o botao precisa voltar.
    if (fonte.readyState !== EventSource.CLOSED) fonte.close();
    $$("#vista-bot button[data-algoritmo]").forEach((b) => { b.disabled = false; });
  };
}

function atualizarHudBot(jogador, objetivos, passos, noPlano, doPlano, alvo) {
  preencherHud($("#bot-hud"), [
    ["pokemon", `${jogador.pokemon} de ${jogador.meta || 4}`],
    ["hp do lider", jogador.hp_lider],
    ["planos feitos", objetivos],
    ["indo para", alvo ? `(${alvo.join(", ")})` : "-"],
    ["passo do plano", doPlano ? `${noPlano} de ${doPlano}` : "-"],
    ["surf", jogador.surf ? "sim" : "nao"],
    ["passos", passos === null ? "-" : passos],
  ]);
}

$$("#vista-bot button[data-algoritmo]").forEach((botao) => {
  botao.addEventListener("click", () => verBotJogar(botao.dataset.algoritmo));
});
$("#bot-ritmo").addEventListener("input", (evento) => {
  $("#bot-ritmo-valor").textContent = `${evento.target.value}ms`;
});
["#bot-size", "#bot-seed", "#bot-hp", "#bot-surf"].forEach((sel) => {
  $(sel).addEventListener("change", carregarMapaBot);
});

/* ============================ vista: benchmark ============================ */

const bench = { fonte: null, raias: {} };

function montarRaia(algoritmo, grupos) {
  const raia = document.createElement("section");
  raia.className = `raia ${algoritmo}`;
  raia.innerHTML = `
    <h2>${NOMES[algoritmo]} <span class="posto">correndo</span></h2>
    <div class="relogio">0,00<small>s</small></div>
    <div class="barra"><i></i></div>
    <div class="progresso-texto">aguardando</div>
    ${grupos.map((g) => `
      <div class="grupo-metrica esperando" data-titulo="${g.titulo}">
        <h3>${g.titulo}<span class="amostra">aguardando</span></h3>
        <dl class="numeros">
          ${g.metricas.map((rotulo) => `<div><dt>${rotulo}</dt><dd>-</dd></div>`).join("")}
        </dl>
      </div>`).join("")}`;
  return {
    el: raia,
    relogio: $(".relogio", raia),
    barra: $(".barra i", raia),
    texto: $(".progresso-texto", raia),
    posto: $(".posto", raia),
    grupos: $$(".grupo-metrica", raia),
  };
}

function pintarGrupos(raia, dados) {
  dados.grupos.forEach((grupo, i) => {
    const alvo = raia.grupos[i];
    if (!alvo) return;
    const valores = $$("dd", alvo);
    grupo.medias.forEach((media, j) => {
      if (valores[j]) valores[j].textContent = media.valor.toFixed(1).replace(".", ",");
    });
    $(".amostra", alvo).textContent = grupo.amostra
      ? `media de ${grupo.amostra} ${grupo.unidade}`
      : "aguardando";
    alvo.classList.toggle("esperando", !grupo.amostra);
  });
}

function rodarBenchmark() {
  if (bench.fonte) bench.fonte.close();
  $("#bench-veredito").replaceChildren();
  $("#bench-rodar").disabled = true;

  const url = new URL("/api/benchmark", location.origin);
  url.searchParams.set("tamanhos", $("#bench-tamanhos").value.replace(/\s/g, ""));
  url.searchParams.set("seeds", $("#bench-seeds").value);
  url.searchParams.set("repeticoes", $("#bench-rep").value);

  const fonte = new EventSource(url);
  bench.fonte = fonte;
  const resultados = {};

  fonte.addEventListener("inicio", (evento) => {
    const dados = JSON.parse(evento.data);
    const container = $("#bench-raias");
    container.replaceChildren();
    bench.raias = {};
    dados.algoritmos.forEach((nome) => {
      const raia = montarRaia(nome, dados.grupos);
      bench.raias[nome] = raia;
      container.appendChild(raia.el);
      raia.texto.textContent = `0 de ${dados.mapas_total} etapas`;
    });
  });

  fonte.addEventListener("progresso", (evento) => {
    const dados = JSON.parse(evento.data);
    const raia = bench.raias[dados.algoritmo];
    if (!raia) return;
    const fracao = dados.mapas_feitos / dados.mapas_total;
    raia.barra.style.width = `${(fracao * 100).toFixed(1)}%`;
    raia.relogio.innerHTML = `${dados.decorrido_s.toFixed(2).replace(".", ",")}<small>s</small>`;
    raia.texto.textContent =
      `${dados.fase} | ${dados.mapas_feitos} de ${dados.mapas_total} | mapa ${dados.tamanho}x${dados.tamanho} seed ${dados.seed}`;
    pintarGrupos(raia, dados);
  });

  fonte.addEventListener("fim_raia", (evento) => {
    const dados = JSON.parse(evento.data);
    resultados[dados.algoritmo] = dados;
    const raia = bench.raias[dados.algoritmo];
    if (!raia) return;
    raia.el.classList.add("chegou");
    raia.barra.style.width = "100%";
    raia.posto.textContent = `${dados.posicao_chegada}o a chegar`;
    raia.relogio.innerHTML = `${dados.decorrido_s.toFixed(2).replace(".", ",")}<small>s</small>`;
    raia.texto.textContent = "os dois experimentos concluidos";
    pintarGrupos(raia, dados);
  });

  fonte.addEventListener("encerrado", (evento) => {
    const dados = JSON.parse(evento.data);
    fonte.close();
    $("#bench-rodar").disabled = false;
    mostrarVeredito(dados, resultados);
  });

  fonte.onerror = () => {
    if (fonte.readyState !== EventSource.CLOSED) fonte.close();
    $("#bench-rodar").disabled = false;
  };
}

/* O ponto da tela: a corrida mede TEMPO, e o trabalho mede CUSTO. Quando o
   primeiro a chegar nao e o de menor custo, e isso que precisa estar escrito,
   nao subentendido. */
function mostrarVeredito(dados, resultados) {
  const primeiro = dados.ordem_de_chegada[0];
  const nomes = Object.keys(resultados);
  if (!nomes.length) return;

  /* Busca por rotulo, nao por posicao: a ordem das metricas muda entre grupos e
     indice fixo aqui vira veredito trocado sem ninguem perceber. */
  const achar = (pedaco) => {
    for (let g = 0; g < resultados[nomes[0]].grupos.length; g += 1) {
      const i = resultados[nomes[0]].grupos[g].medias.findIndex((m) => m.rotulo.includes(pedaco));
      if (i >= 0) return { g, i, rotulo: resultados[nomes[0]].grupos[g].medias[i].rotulo };
    }
    return null;
  };
  const valor = (algo, ref) => resultados[algo].grupos[ref.g].medias[ref.i].valor;
  const menor = (ref) => nomes.reduce((a, b) => (valor(a, ref) <= valor(b, ref) ? a : b));
  const maior = (ref) => nomes.reduce((a, b) => (valor(a, ref) >= valor(b, ref) ? a : b));
  const numero = (v) => v.toFixed(1).replace(".", ",");
  const linha = (texto) => `<p>${texto}</p>`;

  const custo = achar("custo medio");
  const passos = achar("passos");
  const objetivos = achar("objetivos");
  const hp = achar("HP perdido");

  const linhas = [linha(
    `Chegou primeiro: <span class="destaque">${NOMES[primeiro]}</span>, em ${resultados[primeiro].decorrido_s.toFixed(2).replace(".", ",")}s de relogio de parede.`)];

  if (custo && passos) {
    const maisBarato = menor(custo);
    const menosPassos = menor(passos);
    linhas.push(linha(`Rota pura, menor ${custo.rotulo}: <span class="destaque">${NOMES[maisBarato]}</span>, ${numero(valor(maisBarato, custo))}. Menos passos: <span class="destaque">${NOMES[menosPassos]}</span>, ${numero(valor(menosPassos, passos))}.`));
    if (maisBarato !== menosPassos) {
      linhas.push(`<p class="nota">O que anda menos nao e o que paga menos: o ${NOMES[menosPassos]} minimiza arestas porque trata todas como iguais, e o ${NOMES[maisBarato]} e o unico que le o peso da celula. Esse par e a tese do trabalho.</p>`);
    }
  }
  if (objetivos && hp) {
    const maisObjetivos = maior(objetivos);
    const menosHp = menor(hp);
    linhas.push(linha(`Partida completa, mais objetivos: <span class="destaque">${NOMES[maisObjetivos]}</span>, ${numero(valor(maisObjetivos, objetivos))}. Menor HP perdido: <span class="destaque">${NOMES[menosHp]}</span>, ${numero(valor(menosHp, hp))}.`));
    linhas.push(`<p class="nota">A penalidade de batalha no peso da aresta vira consequencia de jogo: a rota que atravessa batalha custa HP, o time desmaia e a partida acaba antes.</p>`);
  }
  if (custo && primeiro !== menor(custo)) {
    linhas.push(`<p class="nota">A corrida nao premia a melhor rota: o ${NOMES[primeiro]} terminou de calcular antes e ainda assim nao entrega o caminho mais barato, que e do ${NOMES[menor(custo)]}. Tempo de execucao e custo de caminho sao eixos diferentes.</p>`);
  }
  $("#bench-veredito").innerHTML = linhas.join("");
}

$("#bench-rodar").addEventListener("click", rodarBenchmark);

/* ============================ arranque ============================ */

novoJogo().catch((e) => { $("#jogo-msg").textContent = String(e); });
carregarMapaBot().catch((e) => { $("#bot-msg").textContent = String(e); });
