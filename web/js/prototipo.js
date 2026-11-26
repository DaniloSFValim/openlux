/* OpenLux — página principal. Mapa Leaflet interativo (zoom, arrastar, consulta, clique para o cartão),
   controle de ano, viagem no tempo e lente de comparação entre dois anos (mesma técnica do explorador).
   Lê só os arquivos publicados em data/: indicators_noaa20.json (padrão) ou indicators.json (S-NPP, ?s=snpp)
   e municipios.geojson. Cores em quantis dos próprios valores do sensor escolhido (mesma escala em todos os anos). */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const COR = ['#0b1530', '#2b2a5e', '#7a3d7c', '#e0604f', '#ffb347', '#fff4c2'];
  const params = new URLSearchParams(location.search);
  const ARQ = { noaa20: 'data/indicators_noaa20.json', snpp: 'data/indicators.json' };

  Promise.all([fetch(ARQ.noaa20).then((r) => r.json()), fetch(ARQ.snpp).then((r) => r.json()), fetch('data/municipios.geojson').then((r) => r.json())])
    .then(([N, S, geo]) => {
      const DADOS = { noaa20: N, snpp: S };
      let sk = params.get('s') === 'snpp' ? 'snpp' : 'noaa20';
      let D = DADOS[sk];
      const anos = D.meta.years;
      let ano = anos.length - 1, anoLente = 0, lenteOn = false, cursor = 0.5, timer = null, selecionado = null;
      const codigos = Object.keys(N.municipios);

      // quantis dos valores do sensor escolhido: mesma escala em todos os anos
      let limites = [];
      function calcularLimites() {
        const todos = [];
        codigos.forEach((c) => D.municipios[c].mean.forEach((v) => { if (v != null && isFinite(v)) todos.push(v); }));
        todos.sort((a, b) => a - b);
        limites = [1, 2, 3, 4, 5].map((i) => todos[Math.floor((i / 6) * (todos.length - 1))]);
        $('barra').style.background = `linear-gradient(90deg, ${COR.slice(0, 6).join(',')})`;
      }
      const classe = (v) => { if (v == null || !isFinite(v)) return -1; let i = 0; while (i < limites.length && v > limites[i]) i++; return i; };
      const corDe = (cd, a) => { const c = classe(D.municipios[cd].mean[a]); return c < 0 ? '#1b2540' : COR[c]; };
      const estilo = (cd, a) => ({ fillColor: corDe(cd, a), fillOpacity: 0.92, color: 'rgba(255,255,255,.18)', weight: 0.6 });

      // mapa
      // a roda do mouse só dá zoom depois que o visitante clica no mapa; antes, ela rola a página
      const map = L.map('mapa', { zoomControl: false, attributionControl: true, minZoom: 8, maxZoom: 14, zoomSnap: 0.25, scrollWheelZoom: false });
      map.on('focus', () => map.scrollWheelZoom.enable());
      map.on('blur', () => map.scrollWheelZoom.disable());
      L.control.zoom({ position: 'bottomleft' }).addTo(map);
      map.attributionControl.setPrefix(false).addAttribution('Dados: NASA Black Marble (VIIRS) · IBGE Malha 2024 e Censo 2022');
      map.createPane('lentePane');
      map.getPane('lentePane').style.zIndex = 450;
      map.getPane('lentePane').style.pointerEvents = 'none';

      const camada = L.geoJSON(geo, {
        style: (f) => estilo(f.properties.CD_MUN, ano),
        onEachFeature: (f, layer) => {
          const cd = f.properties.CD_MUN;
          layer.bindTooltip(() => `${N.municipios[cd].name}: ${fmt(D.municipios[cd].mean[ano], 2)}`, { sticky: true, direction: 'top' });
          layer.on('click', () => abrir(cd));
          layer.on('mouseover', () => layer.setStyle({ weight: 1.6, color: '#ffffff' }));
          layer.on('mouseout', () => camada.resetStyle(layer));
        },
      }).addTo(map);
      // o Leaflet cria os caminhos SVG só ao desenhar: marca o código do município a cada redesenho
      function marcarCodigos() { camada.eachLayer((l) => { const el = l.getElement && l.getElement(); if (el) el.setAttribute('data-cd', l.feature.properties.CD_MUN); }); }
      map.on('moveend zoomend viewreset', marcarCodigos);
      map.fitBounds(camada.getBounds(), { padding: [20, 20] });
      marcarCodigos();

      // lente: mesmo desenho no ano da lente, recortado à esquerda do cursor (ano da lente à esquerda)
      const lentePane = map.getPane('lentePane');
      const lenteLayer = L.geoJSON(geo, {
        pane: 'lentePane', interactive: false,
        style: (f) => ({ fillColor: corDe(f.properties.CD_MUN, anoLente), fillOpacity: 1, color: 'none', weight: 0 }),
      });
      function pintarLente() {
        lenteLayer.setStyle((f) => ({ fillColor: corDe(f.properties.CD_MUN, anoLente) }));
        const w = map.getSize().x, x = cursor * w, off = map._getMapPanePos();
        lentePane.style.clipPath = `polygon(${-off.x}px ${-off.y - 5000}px, ${x - off.x}px ${-off.y - 5000}px, ${x - off.x}px ${-off.y + 5000}px, ${-off.x}px ${-off.y + 5000}px)`;
        const linha = $('lente'); linha.style.left = x + 'px'; linha.style.display = 'block';
      }
      function alternarLente() {
        lenteOn = !lenteOn;
        $('lenteBtn').setAttribute('aria-pressed', String(lenteOn));
        if (lenteOn) { lenteLayer.addTo(map); pintarLente(); }
        else { map.removeLayer(lenteLayer); lentePane.style.clipPath = ''; $('lente').style.display = 'none'; }
      }
      function arrastar(e) {
        const r = map.getContainer().getBoundingClientRect();
        cursor = Math.min(0.98, Math.max(0.02, (e.clientX - r.left) / r.width));
        pintarLente();
      }
      map.on('move zoom', () => { if (lenteOn) pintarLente(); });
      $('lente').addEventListener('pointerdown', (e) => { $('lente').setPointerCapture(e.pointerId); arrastar(e); });
      $('lente').addEventListener('pointermove', (e) => { if (e.buttons) arrastar(e); });

      function pintar() {
        camada.setStyle((f) => estilo(f.properties.CD_MUN, ano));
        $('anoNum').textContent = anos[ano];
        const aviso = $('avisoRuido');
        if (sk === 'snpp' && anos[ano] >= 2022) { aviso.hidden = false; aviso.textContent = 'A partir de 2022 o sensor S-NPP tem mais ruído em áreas escuras: não leia a diferença como mudança real.'; }
        else if (sk === 'noaa20') { aviso.hidden = false; aviso.textContent = 'NOAA-20: sensor primário desta análise. Dados de 2018 a 2025.'; }
        else aviso.hidden = true;
        $('ano').value = ano;
        if (lenteOn) pintarLente();
        if (selecionado) atualizarCartao(selecionado);
      }

      // cartão
      function serieSvg(cd) {
        const NS = 'http://www.w3.org/2000/svg';
        const s = $('cSerie'); s.innerHTML = '';
        const vals = D.municipios[cd].mean;
        const max = Math.max(...vals.filter((v) => v != null), 1e-9);
        const pts = vals.map((v, i) => (v == null ? null : `${(i / (vals.length - 1)) * 300},${90 - (v / max) * 80}`)).filter(Boolean).join(' ');
        const linha = document.createElementNS(NS, 'polyline');
        linha.setAttribute('points', pts); linha.setAttribute('fill', 'none'); linha.setAttribute('stroke', '#ffd166');
        linha.setAttribute('stroke-width', '2'); linha.setAttribute('vector-effect', 'non-scaling-stroke');
        s.appendChild(linha);
      }
      function atualizarCartao(cd) {
        const m = D.municipios[cd];
        $('cNome').textContent = N.municipios[cd].name;
        $('cHab').textContent = m.population != null ? `${nf(0).format(m.population)} habitantes (Censo 2022)` : '';
        $('cAno').textContent = anos[ano];
        $('cMedia').textContent = fmt(m.mean[ano], 3);
        const ord = codigos.filter((c) => D.municipios[c].mean[ano] != null).sort((a, b) => D.municipios[b].mean[ano] - D.municipios[a].mean[ano]);
        $('cPos').textContent = `${ord.indexOf(cd) + 1}º de ${ord.length}`;
        serieSvg(cd);
      }
      function abrir(cd) {
        selecionado = cd;
        atualizarCartao(cd);
        $('cartao').classList.add('on');
        $('cExplorar').href = `explorar.html?s=${sk}&y=${anos[ano]}&m=${cd}`;
        const u = new URL(location.href); u.search = `?s=${sk}&y=${anos[ano]}&m=${cd}`;
        history.replaceState(null, '', u.search);
      }
      $('fechar').addEventListener('click', () => { selecionado = null; $('cartao').classList.remove('on'); });
      $('cCompartilhar').addEventListener('click', () => {
        navigator.clipboard.writeText(location.href).catch(() => {});
      });

      // linha do tempo e viagem
      $('ano').min = 0; $('ano').max = anos.length - 1;
      $('ano').addEventListener('input', (e) => { ano = Number(e.target.value); pintar(); });
      function parar() { clearInterval(timer); timer = null; $('play').textContent = '▶ Viajar no tempo'; $('play').setAttribute('aria-pressed', 'false'); }
      $('play').addEventListener('click', () => {
        if (timer) return parar();
        $('play').textContent = '■ Parar'; $('play').setAttribute('aria-pressed', 'true');
        timer = setInterval(() => { ano = (ano + 1) % anos.length; pintar(); }, 900);
      });
      $('lenteBtn').addEventListener('click', alternarLente);
      $('sensor').addEventListener('change', (e) => {
        const u = new URL(location.href); u.searchParams.set('s', e.target.value); u.searchParams.delete('y'); u.searchParams.delete('m');
        location.assign(u.href);
      });

      // estado inicial
      $('sensor').value = sk;
      const y0 = Number(params.get('y'));
      if (anos.includes(y0)) ano = anos.indexOf(y0);
      calcularLimites();
      pintar();
      const cd0 = params.get('m');
      if (cd0 && D.municipios[cd0]) abrir(cd0);
    })
    .catch((e) => {
      console.error(e);
      const aviso = document.createElement('p');
      aviso.setAttribute('role', 'alert'); aviso.className = 'erro-prot';
      aviso.textContent = 'Não foi possível carregar os dados publicados. Tente recarregar a página.';
      document.body.prepend(aviso);
    });
})();
