/* Quiz com respostas tiradas dos próprios dados (data/indicators.json), não digitadas à mão. */
(async function () {
  'use strict';
  var box = document.getElementById('quiz');
  if (!box) return;
  var data;
  try {
    data = await fetch('data/indicators.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  } catch (e) {
    box.innerHTML = '<p>Não foi possível carregar o quiz. Sirva a pasta web/ por HTTP.</p>';
    return;
  }
  var years = data.meta.years, M = data.municipios;
  var ref = years.indexOf(2021);
  var rows = Object.keys(M).map(function (c) {
    return { nome: M[c].name, pop: M[c].exposure.pop_radiance[ref], area: M[c].mean[ref] };
  }).filter(function (r) { return r.pop != null && r.area != null; });
  var porPop = rows.slice().sort(function (a, b) { return b.pop - a.pop; });
  var estado = data.state.mean[ref];
  var acima = rows.filter(function (r) { return r.area > estado; }).length;
  var nomes = porPop.map(function (r) { return r.nome; });

  function embaralhar(arr, seed) {
    var a = arr.slice(), s = seed;
    for (var i = a.length - 1; i > 0; i--) {
      s = (s * 9301 + 49297) % 233280;
      var j = Math.floor((s / 233280) * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  function opcoesNomes(correta, outros, seed) {
    var extra = outros.filter(function (n) { return n !== correta; }).slice(0, 3);
    return embaralhar([correta].concat(extra), seed);
  }

  var perguntas = [
    {
      texto: 'Em 2021, qual município tem a maior luz onde as pessoas vivem?',
      opcoes: opcoesNomes(porPop[0].nome, nomes.slice(1, 8), 11),
      correta: porPop[0].nome,
      explica: 'A medida pondera cada pixel pela população do Censo 2022. Um município pode ter muita área escura e ainda assim muita luz onde mora gente.'
    },
    {
      texto: 'Em 2021, qual município tem a menor luz onde as pessoas vivem?',
      opcoes: opcoesNomes(porPop[porPop.length - 1].nome, nomes.slice(-8, -1), 23),
      correta: porPop[porPop.length - 1].nome,
      explica: 'Valores baixos indicam pouca luz nas áreas onde a população está. Compare com a média na área no cartão do município.'
    },
    (function () {
      var certa = acima;
      var ops = [certa, certa + 7, Math.max(1, certa - 5), certa + 15].filter(function (v, i, a) { return a.indexOf(v) === i; });
      return {
        texto: 'Em 2021, quantos municípios têm luz média na área acima da média do estado?',
        opcoes: embaralhar(ops.map(String), 37),
        correta: String(certa),
        explica: 'A média do estado inclui todo o território, inclusive áreas muito escuras. Por isso muitos municípios ficam acima dela.'
      };
    })(),
    {
      texto: 'A partir de que ano o sensor Suomi NPP passa a ter mais ruído em áreas escuras?',
      opcoes: ['2019', '2020', '2022', '2024'],
      correta: '2022',
      explica: 'Por isso o projeto usa 2021 como referência e marca a faixa a partir de 2022 nos gráficos.'
    }
  ];

  var atual = 0, acertos = 0;
  function mostrar() {
    var p = perguntas[atual];
    box.innerHTML = '<p class="muted small">Pergunta ' + (atual + 1) + ' de ' + perguntas.length + '</p>' +
      '<p class="pergunta">' + p.texto + '</p><div class="opcoes">' +
      p.opcoes.map(function (o, i) { return '<button type="button" class="opcao" data-i="' + i + '">' + o + '</button>'; }).join('') +
      '</div><div class="explica" id="explica"></div>' +
      '<div class="proxima"></div><p class="placar" aria-live="polite"></p>';
    box.querySelectorAll('.opcao').forEach(function (b) {
      b.addEventListener('click', function () { responder(b, p); });
    });
  }
  function responder(botao, p) {
    var escolhida = p.opcoes[Number(botao.dataset.i)];
    var certa = escolhida === p.correta;
    if (certa) acertos++;
    box.querySelectorAll('.opcao').forEach(function (b) {
      b.disabled = true;
      if (p.opcoes[Number(b.dataset.i)] === p.correta) b.classList.add('certa');
    });
    if (!certa) botao.classList.add('errada');
    var ex = document.getElementById('explica');
    ex.innerHTML = '<strong>' + (certa ? 'Isso mesmo!' : 'Quase: a resposta é ' + p.correta + '.') + '</strong> ' + p.explica;
    ex.classList.add('on');
    var prox = box.querySelector('.proxima');
    prox.innerHTML = '<button type="button" class="btn">' + (atual + 1 < perguntas.length ? 'Próxima' : 'Ver resultado') + '</button>';
    prox.querySelector('button').addEventListener('click', function () {
      atual++;
      if (atual < perguntas.length) mostrar(); else final();
    });
  }
  function final() {
    box.innerHTML = '<p class="pergunta">Você acertou ' + acertos + ' de ' + perguntas.length + '.</p>' +
      '<p>Quer conferir no mapa? <a href="explorar.html?l=mun&amp;i=mean&amp;y=2021&amp;s=snpp">Abrir o mapa de 2021</a>.</p>' +
      '<button type="button" class="btn secundario" id="refazer">Refazer</button>';
    document.getElementById('refazer').addEventListener('click', function () { atual = 0; acertos = 0; mostrar(); });
  }
  mostrar();
})();
