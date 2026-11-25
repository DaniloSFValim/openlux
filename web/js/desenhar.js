/* "Desenhe uma área": o leitor marca vértices no mapa e vê quantos pixels de cada faixa de luz caem dentro da área.
   Conta classes, não valores: o site publica só a classe de cada pixel. Usa Turf (teste ponto-em-polígono e área). */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var api = null, pontos = [], linha = null, marcas = [], desenhando = false, ouvinte = null, inicializado = false;

  function ativarQuandoPronto() {
    if (inicializado) return;
    if (!window.OpenLuxMapApi || !window.OpenLuxDraw || typeof L === 'undefined') return;
    inicializado = true;
    api = window.OpenLuxMapApi;
    $('desenhar-iniciar').addEventListener('click', iniciar);
    $('desenhar-desfazer').addEventListener('click', desfazer);
    $('desenhar-concluir').addEventListener('click', concluir);
    $('desenhar-limpar').addEventListener('click', limpar);
    document.addEventListener('keydown', function (e) {
      if (!desenhando) return;
      if (e.key === 'Enter' && pontos.length >= 3) { e.preventDefault(); concluir(); }
      if (e.key === 'Escape') { e.preventDefault(); cancelar(); }
    });
  }

  function atualizarBotoes() {
    $('desenhar-concluir').disabled = pontos.length < 3;
    $('desenhar-desfazer').disabled = pontos.length === 0;
  }

  function desenharPrevia() {
    if (linha) { api.map.removeLayer(linha); linha = null; }
    marcas.forEach(function (m) { api.map.removeLayer(m); });
    marcas = pontos.map(function (p) {
      return L.circleMarker(p, { radius: 4, color: '#0b1020', weight: 2, fillColor: '#ffb703', fillOpacity: 1, interactive: false }).addTo(api.map);
    });
    if (pontos.length >= 2) {
      linha = L.polygon(pontos, { color: '#0b1020', weight: 2, fillColor: '#ffb703', fillOpacity: 0.25, dashArray: pontos.length < 3 ? '6 4' : null, interactive: false }).addTo(api.map);
    }
    atualizarBotoes();
  }

  function aoClicarNoMapa(e) {
    pontos.push([e.latlng.lat, e.latlng.lng]);
    desenharPrevia();
    $('desenhar-status').textContent = pontos.length < 3
      ? 'Marque mais ' + (3 - pontos.length) + ' vértice(s) para formar uma área.'
      : 'Continue marcando ou toque em "Concluir área".';
  }

  function iniciar() {
    if (!api.viewIsRadiance()) {
      $('desenhar-status').textContent = 'Para contar as faixas de luz, escolha "Radiância por ano" em Mostrar.';
      return;
    }
    limpar();
    desenhando = true;
    ouvinte = aoClicarNoMapa;
    api.map.on('click', ouvinte);
    api.map.getContainer().style.cursor = 'crosshair';
    var mapa = $('mapa');
    if (mapa && mapa.scrollIntoView) mapa.scrollIntoView({ behavior: 'smooth', block: 'center' });
    ['desenhar-desfazer', 'desenhar-concluir', 'desenhar-limpar'].forEach(function (id) { $(id).hidden = false; });
    $('desenhar-resultado').hidden = true;
    $('desenhar-status').textContent = 'Clique no mapa para marcar o primeiro vértice.';
    atualizarBotoes();
  }

  function desfazer() {
    pontos.pop();
    desenharPrevia();
    $('desenhar-status').textContent = pontos.length ? '' : 'Clique no mapa para marcar o primeiro vértice.';
  }

  function encerrarDesenho() {
    desenhando = false;
    if (ouvinte) { api.map.off('click', ouvinte); ouvinte = null; }
    api.map.getContainer().style.cursor = '';
  }

  function cancelar() {
    encerrarDesenho();
    limpar();
    $('desenhar-status').textContent = 'Desenho cancelado.';
  }

  function limpar() {
    encerrarDesenho();
    pontos = [];
    if (linha) { api.map.removeLayer(linha); linha = null; }
    marcas.forEach(function (m) { api.map.removeLayer(m); });
    marcas = [];
    ['desenhar-desfazer', 'desenhar-concluir'].forEach(function (id) { $(id).hidden = true; });
    $('desenhar-limpar').hidden = true;
    $('desenhar-resultado').hidden = true;
    $('desenhar-status').textContent = '';
  }

  function concluir() {
    if (pontos.length < 3) return;
    encerrarDesenho();
    var anel = pontos.map(function (p) { return [p[1], p[0]]; });
    anel.push(anel[0]);
    var area = window.OpenLuxDraw.turf.polygon([anel]);
    $('desenhar-concluir').disabled = true;
    $('desenhar-desfazer').hidden = true;
    $('desenhar-status').textContent = 'Contando os pixels dentro da área…';
    contar(area).then(mostrar, function () {
      $('desenhar-status').textContent = 'Não foi possível carregar a grade de pixels. Tente de novo.';
    });
  }

  function contar(feature) {
    var T = window.OpenLuxDraw.turf, path = api.currentPath();
    return api.getGrid(path).then(function (grid) {
      var g = api.pxMeta.grid, pd = g.pixel_deg, cod = {};
      for (var k = 2; k <= 7; k++) cod[k] = 0;
      var b = T.bbox(feature);                       // [oeste, sul, leste, norte]
      var c0 = Math.max(0, Math.floor((b[0] - g.lon_west) / pd));
      var c1 = Math.min(g.cols - 1, Math.floor((b[2] - g.lon_west) / pd));
      var r0 = Math.max(0, Math.floor((g.lat_north - b[3]) / pd));
      var r1 = Math.min(g.rows - 1, Math.floor((g.lat_north - b[1]) / pd));
      var dentro = 0;
      for (var r = r0; r <= r1; r++) {
        var lat = g.lat_north - (r + 0.5) * pd;
        for (var c = c0; c <= c1; c++) {
          var code = grid[r * g.cols + c];
          if (code < 2 || code > 7) continue;        // 0 = fora do estado; 1 = sem dado válido
          var lon = g.lon_west + (c + 0.5) * pd;
          if (T.booleanPointInPolygon([lon, lat], feature)) {
            cod[code]++;
            dentro++;
          }
        }
      }
      return { cod: cod, dentro: dentro, km2: T.area(feature) / 1e6, path: path };
    });
  }

  function mostrar(res) {
    var labels = api.pxMeta.classes.labels, total = res.dentro;
    var linhas = '';
    for (var k = 2; k <= 7; k++) {
      var n = res.cod[k] || 0, pct = total ? (100 * n / total) : 0;
      linhas += '<tr><th scope="row">' + labels[k - 2] + '</th><td class="num">' + n.toLocaleString('pt-BR') + '</td>' +
        '<td><span class="barra" style="width:' + pct.toFixed(1) + '%"></span><span class="pct">' + pct.toFixed(1).replace('.', ',') + '%</span></td></tr>';
    }
    var ano = res.path.split('/')[1] || '';
    var aviso = (res.path.indexOf('snpp') === 0 && Number(ano) >= 2022)
      ? '<p class="aviso">Ano de 2022 em diante, sensor S-NPP: mais ruído em áreas escuras. Não interprete a faixa como mudança real.</p>' : '';
    var box = $('desenhar-resultado');
    box.innerHTML =
      '<h3>Área desenhada: ' + res.km2.toFixed(1).replace('.', ',') + ' km²</h3>' +
      '<p>' + total.toLocaleString('pt-BR') + ' pixels (de cerca de 460 m) caem dentro da área, em ' + ano + '.</p>' +
      '<div class="dados-tabela"><table><thead><tr><th>Faixa de luz</th><th class="num">Pixels</th><th>Participação</th></tr></thead><tbody>' + linhas + '</tbody></table></div>' +
      '<p class="ajuda">Mostra a contagem de classes, não a média de luz. Pixels fora do estado e sem dado válido não entram no total.</p>' + aviso;
    box.hidden = false;
    $('desenhar-status').textContent = total ? 'Área concluída. Use "Limpar" para desenhar outra.' : 'Nenhum pixel válido dentro da área. Desenhe sobre o território do estado.';
    $('desenhar-limpar').hidden = false;
  }

  document.addEventListener('openlux:mapa-pronto', ativarQuandoPronto);
  ativarQuandoPronto();
})();
