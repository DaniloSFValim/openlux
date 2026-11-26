/* OpenLux — explorador cartográfico. Lê só os arquivos publicados em data/ e downloads/.
   - municipal: indicators_noaa20.json (padrão) ou indicators.json (?s=snpp)
   - pixels: pixels/<sensor>/<ano>.bin (uint8: 0 fora do estado, 1 sem dado válido, 2–7 classes), pixels/meta.json
   - percentis: downloads/openlux_percentis_pixels_<sensor>.csv
   - geometria: municipios.geojson
   Não há valor de radiância por pixel nem qualidade publicados: o pixel mostra apenas a classe. */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const COR = ['#0b1530', '#2b2a5e', '#7a3d7c', '#e0604f', '#ffb347', '#fff4c2'];      // radiância municipal (6 classes)
  const COR_PIX = ['#2b2a5e', '#7a3d7c', '#e0604f', '#ffb347', '#fff4c2', '#ffffff'];  // classes de pixel 2–7
  const DENS = ['#0e2a3a', '#1b4f5c', '#2f7a72', '#7fb36a', '#e4c25c', '#f7e9a8'];
  const ARQ = { noaa20: 'data/indicators_noaa20.json', snpp: 'data/indicators.json' };
  const PERC = { noaa20: 'data/downloads/openlux_percentis_pixels_noaa20.csv', snpp: 'data/downloads/openlux_percentis_pixels_snpp.csv' };
  const T = window.OpenLuxDraw.turf;
  const params = new URLSearchParams(location.search);

  const getJSON = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
  const getText = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.text(); });

  Promise.all([getJSON('data/municipios.geojson'), getJSON('data/pixels/meta.json'), getJSON(ARQ.noaa20), getJSON(ARQ.snpp), getText(PERC.noaa20), getText(PERC.snpp)])
    .then(([geo, pm, N, S, pN, pS]) => iniciar({ geo, pm, DADOS: { noaa20: N, snpp: S }, PERC: { noaa20: parseCSV(pN), snpp: parseCSV(pS) } }))
    .catch((e) => {
      console.error(e);
      const a = document.createElement('p'); a.setAttribute('role', 'alert');
      a.style.cssText = 'position:absolute;top:90px;left:50%;transform:translateX(-50%);background:#3a1820;padding:10px 14px;border-radius:8px;z-index:999';
      a.textContent = 'Não foi possível carregar os dados publicados. Tente recarregar a página.';
      document.body.appendChild(a);
    });

  function parseCSV(txt) {
    const linhas = txt.replace(/^﻿/, '').trim().split('\n');
    const cab = linhas[0].split(',');
    const out = {};
    linhas.slice(1).forEach((l) => {
      const v = l.split(','); const r = {};
      cab.forEach((c, i) => { r[c] = c === 'CD_MUN' ? v[i] : Number(v[i]); });
      (out[r.CD_MUN] = out[r.CD_MUN] || {})[r.year] = r;
    });
    return out;
  }

  function iniciar({ geo, pm, DADOS, PERC }) {
    let sk = params.get('s') === 'snpp' ? 'snpp' : 'noaa20';
    let D = DADOS[sk];
    let anos = D.meta.years;
    const codigos = Object.keys(D.municipios).sort((a, b) => D.municipios[a].name.localeCompare(D.municipios[b].name, 'pt-BR'));
    const nome = (cd) => D.municipios[cd].name;
    let ano = Math.max(0, anos.indexOf(Number(params.get('y'))) >= 0 ? anos.indexOf(Number(params.get('y'))) : anos.length - 1);
    let anoL = null, lenteOn = false, selecionado = null, timer = null;
    const camadas = new Set((params.get('l') || 'mun,est,rad').split(','));
    let limites = [], limitesDens = [], cursorX = 0.5;
    const grade = pm.grid;

    // áreas (km²) e densidade (2022)
    const area = {};
    geo.features.forEach((f) => { area[f.properties.CD_MUN] = T.area(f) / 1e6; });
    const densidade = {};
    codigos.forEach((cd) => { const p = D.municipios[cd].population; densidade[cd] = p != null && area[cd] ? p / area[cd] : null; });

    // mapa
    const map = L.map('mapa', { zoomControl: true, attributionControl: true, minZoom: 8, maxZoom: 14 });
    map.attributionControl.setPrefix(false).addAttribution('Dados: NASA Black Marble (VIIRS) · IBGE Malha 2024 e Censo 2022 · CNUC/MMA');
    const pInfo = $('pixelInfo');
    map.createPane('lentePane'); map.getPane('lentePane').style.zIndex = 450; map.getPane('lentePane').style.pointerEvents = 'none';
    map.createPane('pixelPane'); map.getPane('pixelPane').style.zIndex = 380;
    const cenarioLimites = L.geoJSON(geo, { style: { color: 'rgba(255,255,255,.22)', weight: .6, fillOpacity: 0 }, pane: 'overlayPane' });
    const municipios = {};
    const camadaMun = L.geoJSON(geo, {
      style: (f) => estiloMun(f.properties.CD_MUN, ano),
      onEachFeature: (f, layer) => {
        const cd = f.properties.CD_MUN; municipios[cd] = layer;
        layer.bindTooltip(() => `${nome(cd)}: ${fmt(D.municipios[cd].mean[ano], 2)}`, { sticky: true, direction: 'top', className: 'tt-exp' });
        layer.on('click', () => abrir(cd));
        layer.on('mouseover', () => layer.setStyle({ weight: 2.2, color: '#ffd166' }));
        layer.on('mouseout', () => layer.setStyle({ weight: .6, color: 'rgba(255,255,255,.22)' }));
      },
    });
    const estadoGeo = unirEstado(geo);
    const camadaEstado = L.geoJSON(estadoGeo, { style: { color: '#ffd166', weight: 1.6, fill: false }, interactive: false });
    const camadaLente = L.geoJSON(geo, { style: (f) => ({ fillColor: corMun(f.properties.CD_MUN, anoL ?? ano), fillOpacity: .95, weight: 0, color: 'transparent' }), pane: 'lentePane', interactive: false });
    let camadaPix = null, camadaPixMeta = null;

    // limites de cor (radiância): quintis do conjunto inteiro do sensor, iguais em todos os anos
    function calcLimites() {
      const todos = [];
      codigos.forEach((cd) => D.municipios[cd].mean.forEach((v) => { if (v != null && isFinite(v)) todos.push(v); }));
      todos.sort((a, b) => a - b);
      limites = [1, 2, 3, 4, 5].map((i) => todos[Math.floor((i / 6) * (todos.length - 1))]);
      const dens = codigos.map((cd) => densidade[cd]).filter((v) => v != null).sort((a, b) => a - b);
      limitesDens = [1, 2, 3, 4, 5].map((i) => dens[Math.floor((i / 6) * (dens.length - 1))]);
    }
    function classeRad(v) { if (v == null || !isFinite(v)) return -1; let i = 0; while (i < limites.length && v > limites[i]) i++; return i; }
    function classeDens(v) { if (v == null || !isFinite(v)) return -1; let i = 0; while (i < limitesDens.length && v > limitesDens[i]) i++; return i; }
    function modoDens() { return camadas.has('dens'); }
    function corMun(cd, a) {
      if (modoDens()) { const c = classeDens(densidade[cd]); return c < 0 ? '#1b2540' : DENS[c]; }
      const c = classeRad(D.municipios[cd].mean[a]); return c < 0 ? '#1b2540' : COR[c];
    }
    function estiloMun(cd, a) {
      const visivel = camadas.has('mun');
      const pixels = camadas.has('pix');
      const preenche = camadas.has('rad') || camadas.has('dens');
      return { fillColor: corMun(cd, a), fillOpacity: preenche ? (pixels ? .25 : .92) : 0, weight: visivel ? .6 : 0, color: visivel ? 'rgba(255,255,255,.25)' : 'transparent' };
    }

    function repintar() {
      Object.keys(municipios).forEach((cd) => municipios[cd].setStyle(estiloMun(cd, ano)));
      if (lenteOn && anoL != null) { camadaLente.clearLayers(); camadaLente.addData(geo); camadaLente.setStyle((f) => ({ fillColor: corMun(f.properties.CD_MUN, anoL), fillOpacity: .95, weight: 0 })); }
      $('anoNum').textContent = anos[ano];
      $('ano').value = ano;
      atualizarLegenda();
      atualizarAviso();
      if (selecionado) atualizarCartao(selecionado);
      atualizarLente();
      atualizarPixels();
      atualizarLink();
    }

    function atualizarAviso() {
      const a = $('avisoSensor');
      if (sk === 'snpp' && anos[ano] >= 2022) { a.hidden = false; a.textContent = 'S-NPP: a partir de 2022 há mais ruído em áreas escuras. Não leia a diferença como mudança real.'; }
      else if (sk === 'noaa20') { a.hidden = false; a.textContent = 'NOAA-20: sensor primário. Série de 2018 a 2025.'; }
      else a.hidden = true;
    }

    function atualizarLegenda() {
      const ol = $('legClasses');
      if (camadas.has('pix') && !modoDens()) {
        $('legTitulo').textContent = 'Classe de luz por pixel (' + (sk === 'noaa20' ? 'NOAA-20' : 'S-NPP') + ')';
        ol.innerHTML = pm.classes.labels.map((l, i) => `<li><span class="sw" style="background:${COR_PIX[i]}"></span>${esc(l)}</li>`).join('');
        $('legNota').textContent = 'Classes fixas em todos os anos. Pixel de 15 arco-segundos (≈ 460 m). Valor e qualidade do pixel não são publicados.';
        return;
      }
      if (modoDens()) {
        $('legTitulo').textContent = 'Densidade demográfica, Censo 2022 (hab./km²)';
        ol.innerHTML = DENS.map((c, i) => `<li><span class="sw" style="background:${c}"></span>${fmt(limitesDens[i - 1] ?? 0, 0)} a ${fmt(limitesDens[i] ?? limitesDens[limitesDens.length - 1], 0)}</li>`).join('').replace(/^/, '');
        $('legNota').textContent = 'Densidade = população (2022) / área do município. Classes de quintis, fixas em todos os anos.';
        return;
      }
      $('legTitulo').textContent = 'Luz média por município (nW·cm⁻²·sr⁻¹)';
      const rot = (i) => (i === 0 ? '< ' + fmt(limites[0], 2) : i === 5 ? '≥ ' + fmt(limites[4], 2) : fmt(limites[i - 1], 2) + ' a ' + fmt(limites[i], 2));
      ol.innerHTML = COR.map((c, i) => `<li><span class="sw" style="background:${c}"></span>${rot(i)}</li>`).join('');
      $('legNota').textContent = 'Classes fixas em todos os anos (quintis do conjunto do sensor). Estimativa, não medição do brilho do céu.';
    }

    // pixels: imagem gerada a partir do arquivo .bin do ano, com cache
    const cachePix = {};
    function binDoAno(s, y) {
      const k = s + y;
      if (!cachePix[k]) cachePix[k] = fetch(`data/pixels/${s}/${y}.bin`).then((r) => { if (!r.ok) throw new Error('bin ' + r.status); return r.arrayBuffer(); }).then((b) => new Uint8Array(b));
      return cachePix[k];
    }
    let pixToken = 0;
    function atualizarPixels() {
      const on = camadas.has('pix');
      if (!on) { if (camadaPix) { map.removeLayer(camadaPix); camadaPix = null; } pInfo.textContent = 'Passe o cursor sobre o mapa para ver a classe do pixel.'; return; }
      const token = ++pixToken, y = anos[ano];
      binDoAno(sk, y).then((bin) => {
        if (token !== pixToken || !camadas.has('pix')) return;
        const cv = document.createElement('canvas'); cv.width = grade.cols; cv.height = grade.rows;
        const ctx = cv.getContext('2d'); const img = ctx.createImageData(grade.cols, grade.rows);
        for (let i = 0; i < bin.length; i++) {
          const c = bin[i]; const j = i * 4;
          if (c < 2 || c > 7) { img.data[j + 3] = 0; continue; }
          const rgb = COR_PIX[c - 2]; const n = parseInt(rgb.slice(1), 16);
          img.data[j] = n >> 16; img.data[j + 1] = (n >> 8) & 255; img.data[j + 2] = n & 255; img.data[j + 3] = 225;
        }
        ctx.putImageData(img, 0, 0);
        const sul = grade.lat_north - grade.rows * grade.pixel_deg, leste = grade.lon_west + grade.cols * grade.pixel_deg;
        if (camadaPix) map.removeLayer(camadaPix);
        camadaPix = L.imageOverlay(cv.toDataURL('image/png'), [[sul, grade.lon_west], [grade.lat_north, leste]], { pane: 'pixelPane', className: 'pixel-canvas', interactive: false });
        camadaPix.addTo(map);
        camadaPixMeta = { bin, y };
        atualizarLegenda();
        atualizarLink();
      }).catch((e) => { console.error(e); pInfo.textContent = 'Pixels deste ano indisponíveis.'; });
    }

    function leituraPixel(lat, lon) {
      if (!camadaPixMeta) return null;
      const c = Math.floor((lon - grade.lon_west) / grade.pixel_deg), r = Math.floor((grade.lat_north - lat) / grade.pixel_deg);
      if (c < 0 || r < 0 || c >= grade.cols || r >= grade.rows) return null;
      return camadaPixMeta.bin[r * grade.cols + c];
    }
    map.on('mousemove', (e) => {
      if (!camadas.has('pix') || !camadaPixMeta) return;
      const code = leituraPixel(e.latlng.lat, e.latlng.lng);
      if (code == null) { pInfo.textContent = ''; return; }
      if (code === 0) pInfo.textContent = 'Fora do estado';
      else if (code === 1) pInfo.textContent = 'Sem dado válido neste pixel';
      else pInfo.textContent = `Classe de luz: ${pm.classes.labels[code - 2]} · ${sk === 'noaa20' ? 'NOAA-20' : 'S-NPP'} · ${camadaPixMeta.y}`;
    });

    // lente: ano da lente à esquerda do cursor, ano atual à direita (recorte no painel do Leaflet)
    const divisor = document.createElement('div'); divisor.className = 'lente-divisor';
    const alca = document.createElement('div'); alca.className = 'lente-alca'; alca.setAttribute('role', 'slider'); alca.setAttribute('aria-label', 'Posição da lente'); alca.tabIndex = 0;
    const rotuloL = document.createElement('div'); rotuloL.className = 'rotulo-lente';
    document.body.append(divisor, alca, rotuloL);
    function atualizarLente() {
      const on = lenteOn && anoL != null;
      camadaLente.setStyle(() => ({ fillOpacity: on ? .95 : 0 }));
      if (!on) { if (map.hasLayer(camadaLente)) map.removeLayer(camadaLente); divisor.style.display = alca.style.display = rotuloL.style.display = 'none'; return; }
      if (!map.hasLayer(camadaLente)) camadaLente.addTo(map);
      const w = map.getSize().x, h = map.getSize().y, x = cursorX * w;
      const off = map._getMapPanePos();
      const pane = map.getPane('lentePane');
      pane.style.clipPath = `polygon(${-off.x}px ${-off.y - 5000}px, ${x - off.x}px ${-off.y - 5000}px, ${x - off.x}px ${-off.y + 5000}px, ${-off.x}px ${-off.y + 5000}px)`;
      divisor.style.display = 'block'; divisor.style.left = x + 'px';
      alca.style.display = 'block'; alca.style.left = x + 'px'; alca.style.top = (h / 2) + 'px';
      rotuloL.style.display = 'block'; rotuloL.style.left = Math.max(8, x - 130) + 'px'; rotuloL.textContent = `Ano ${anoL}`;
      $('notaLente').textContent = `Comparando ${anoL} (esquerda) com ${anos[ano]} (direita). Mesma escala de cores.`;
    }
    function arrastarLente(e) {
      const r = map.getContainer().getBoundingClientRect();
      cursorX = Math.min(.98, Math.max(.02, (e.clientX - r.left) / r.width));
      atualizarLente(); atualizarLink();
    }
    alca.addEventListener('pointerdown', (e) => { alca.setPointerCapture(e.pointerId); arrastarLente(e); });
    alca.addEventListener('pointermove', (e) => { if (e.buttons) arrastarLente(e); });
    map.on('move zoom', () => { if (lenteOn) atualizarLente(); });

    // cartão municipal
    function atualizarCartao(cd) {
      const m = D.municipios[cd];
      $('cNome').textContent = nome(cd);
      const c = T.centroid(geo.features.find((f) => f.properties.CD_MUN === cd));
      const [lon, lat] = c.geometry.coordinates;
      $('cLocal').textContent = `Centro: ${fmt(lat, 3)}°, ${fmt(lon, 3)}° · ${sk === 'noaa20' ? 'NOAA-20' : 'S-NPP'}`;
      $('cPopArea').textContent = `${m.population != null ? nf(0).format(m.population) + ' hab.' : 'população indisponível'} · ${fmt(area[cd], 1)} km² · ${densidade[cd] != null ? fmt(densidade[cd], 0) + ' hab./km²' : ''}`;
      $('cAno').textContent = anos[ano];
      $('cMedia').textContent = fmt(m.mean[ano], 3);
      const estadoMedia = mediaEstado(ano);
      const dif = m.mean[ano] - estadoMedia;
      $('cMedMedia').textContent = `Média estadual: ${fmt(estadoMedia, 3)} · diferença ${dif >= 0 ? '+' : ''}${fmt(dif, 3)}`;
      const p = (PERC[sk][cd] || {})[anos[ano]];
      $('cPerc').textContent = p ? `P75 ${fmt(p.q75_radiance, 2)} · P90 ${fmt(p.q90_radiance, 2)} · P95 ${fmt(p.q95_radiance, 2)} (pixels)` : 'Percentis indisponíveis para este ano.';
      const ord = codigos.filter((x) => D.municipios[x].mean[ano] != null).sort((a, b) => D.municipios[b].mean[ano] - D.municipios[a].mean[ano]);
      const pos = ord.indexOf(cd) + 1;
      const pctl = Math.round(100 * codigos.filter((x) => D.municipios[x].mean[ano] != null && D.municipios[x].mean[ano] <= m.mean[ano]).length / ord.length);
      $('cPos').textContent = `${pos}º de ${ord.length} · maior que ${pctl}% dos municípios`;
      serieSvg(cd);
      distribuicao(cd, ano);
      const u = $('cartao'); u.classList.add('on');
    }
    function mediaEstado(a) { const xs = codigos.map((c) => D.municipios[c].mean[a]).filter((v) => v != null); return xs.reduce((s, v) => s + v, 0) / xs.length; }
    function serieSvg(cd) {
      const s = $('cSerie'); s.innerHTML = '';
      const vals = D.municipios[cd].mean; const max = Math.max(...vals.filter((v) => v != null), 1e-9);
      const NS = 'http://www.w3.org/2000/svg';
      const pts = vals.map((v, i) => (v == null ? null : `${(i / (vals.length - 1)) * 300},${86 - (v / max) * 78}`)).filter(Boolean).join(' ');
      const pl = document.createElementNS(NS, 'polyline'); pl.setAttribute('points', pts); pl.setAttribute('fill', 'none'); pl.setAttribute('stroke', '#ffd166'); pl.setAttribute('stroke-width', '2'); pl.setAttribute('vector-effect', 'non-scaling-stroke'); s.appendChild(pl);
      const i = anos.indexOf(anos[ano]); const x = (i / (vals.length - 1)) * 300;
      const linha = document.createElementNS(NS, 'line'); linha.setAttribute('x1', x); linha.setAttribute('x2', x); linha.setAttribute('y1', 4); linha.setAttribute('y2', 86); linha.setAttribute('stroke', 'rgba(255,255,255,.4)'); linha.setAttribute('vector-effect', 'non-scaling-stroke'); s.appendChild(linha);
    }
    // distribuição das classes de pixel dentro do município (centros de pixel dentro do polígono)
    const cacheDist = {};
    function distribuicao(cd, a) {
      const ol = $('cDistrib');
      const chave = sk + cd + anos[a];
      const pintar = (cont, total) => {
        ol.innerHTML = pm.classes.labels.map((l, i) => `<li><span class="sw" style="background:${COR_PIX[i]}"></span>${esc(l)}<span>${total ? fmt(100 * cont[i] / total, 1) + '%' : '—'}</span></li>`).join('');
      };
      if (cacheDist[chave]) return pintar(cacheDist[chave].cont, cacheDist[chave].total);
      ol.innerHTML = '<li>Calculando…</li>';
      binDoAno(sk, anos[a]).then((bin) => {
        const f = geo.features.find((x) => x.properties.CD_MUN === cd);
        const [w, s, e, n] = T.bbox(f);
        const c0 = Math.max(0, Math.floor((w - grade.lon_west) / grade.pixel_deg)), c1 = Math.min(grade.cols - 1, Math.ceil((e - grade.lon_west) / grade.pixel_deg));
        const r0 = Math.max(0, Math.floor((grade.lat_north - n) / grade.pixel_deg)), r1 = Math.min(grade.rows - 1, Math.ceil((grade.lat_north - s) / grade.pixel_deg));
        const cont = [0, 0, 0, 0, 0, 0]; let total = 0;
        for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) {
          const code = bin[r * grade.cols + c]; if (code < 2 || code > 7) continue;
          const lon = grade.lon_west + (c + .5) * grade.pixel_deg, lat = grade.lat_north - (r + .5) * grade.pixel_deg;
          if (!T.booleanPointInPolygon([lon, lat], f)) continue;
          cont[code - 2]++; total++;
        }
        cacheDist[chave] = { cont, total };
        pintar(cont, total);
      });
    }

    // seleção, cartão, link
    function abrir(cd) { selecionado = cd; atualizarCartao(cd); atualizarLink(); }
    function fechar() { selecionado = null; $('cartao').classList.remove('on'); atualizarLink(); }
    $('fechar').addEventListener('click', fechar);

    function atualizarLink() {
      const u = new URL(location.href);
      const q = new URLSearchParams();
      q.set('s', sk); q.set('y', anos[ano]); q.set('l', [...camadas].join(','));
      if (selecionado) q.set('m', selecionado);
      if (lenteOn && anoL != null) { q.set('lente', anoL); q.set('lx', cursorX.toFixed(2)); }
      const c = map.getCenter(); q.set('lat', c.lat.toFixed(4)); q.set('lng', c.lng.toFixed(4)); q.set('z', map.getZoom());
      u.search = '?' + q.toString();
      history.replaceState(null, '', u.search);
    }
    $('btnLink').addEventListener('click', () => { atualizarLink(); navigator.clipboard.writeText(location.href).then(() => { $('notaLink').textContent = 'Link copiado.'; }, () => { $('notaLink').textContent = 'Não foi possível copiar: copie o endereço da barra.'; }); });

    // camadas (gaveta)
    const toggles = { lyMunicipios: 'mun', lyEstado: 'est', lyRadiancia: 'rad', lyPixels: 'pix', lyDensidade: 'dens' };
    Object.keys(toggles).forEach((id) => { const el = $(id); el.checked = camadas.has(toggles[id]); el.addEventListener('change', () => {
      const k = toggles[id];
      if (k === 'dens' && el.checked) { camadas.delete('rad'); $('lyRadiancia').checked = false; }
      if (k === 'rad' && el.checked) { camadas.delete('dens'); $('lyDensidade').checked = false; }
      if (el.checked) camadas.add(k); else camadas.delete(k);
      if (k === 'est') { if (el.checked) camadaEstado.addTo(map); else map.removeLayer(camadaEstado); }
      if (k === 'mun') { if (el.checked) camadaMun.addTo(map); else map.removeLayer(camadaMun); }
      repintar();
    }); });
    if (camadas.has('est')) camadaEstado.addTo(map); else camadaEstado.remove();
    camadaMun.addTo(map);

    // sensor, lente, tempo
    $('sensor').value = sk;
    $('sensor').addEventListener('change', (e) => { const u = new URL(location.href); u.searchParams.set('s', e.target.value); location.assign(u.href); }); // mantém ano, lente e posição da lente;
    const sel = $('anoLente'); sel.innerHTML = anos.map((y) => `<option value="${y}">${y}</option>`).join('');
    $('lenteOn').checked = params.has('lente');
    if (params.has('lente') && anos.includes(Number(params.get('lente')))) anoL = Number(params.get('lente'));
    else anoL = anos[0];
    sel.value = anoL;
    if (params.has('lx')) cursorX = Number(params.get('lx')) || .5;
    lenteOn = $('lenteOn').checked;  // lente ativa também quando o ano da lente não existe no sensor (cai para o primeiro ano)
    $('lenteOn').addEventListener('change', (e) => { lenteOn = e.target.checked; if (lenteOn && anoL == null) anoL = anos[0]; repintar(); });
    sel.addEventListener('change', (e) => { anoL = Number(e.target.value); repintar(); });
    $('ano').max = anos.length - 1;
    $('ano').addEventListener('input', (e) => { ano = Number(e.target.value); repintar(); });
    $('play').addEventListener('click', () => {
      if (timer) { clearInterval(timer); timer = null; $('play').textContent = '▶ Viajar no tempo'; $('play').setAttribute('aria-pressed', 'false'); return; }
      $('play').textContent = '■ Parar'; $('play').setAttribute('aria-pressed', 'true');
      timer = setInterval(() => { ano = (ano + 1) % anos.length; repintar(); }, 900);
    });
    $('abrirGaveta').addEventListener('click', () => { $('gaveta').classList.add('aberta'); document.body.classList.remove('gaveta-fechada'); $('abrirGaveta').setAttribute('aria-expanded', 'true'); });
    $('fecharGaveta').addEventListener('click', () => { $('gaveta').classList.remove('aberta'); document.body.classList.add('gaveta-fechada'); $('abrirGaveta').setAttribute('aria-expanded', 'false'); });
    if (params.get('g') === '1') { $('gaveta').classList.add('aberta'); } else { document.body.classList.add('gaveta-fechada'); }
    $('cartao').addEventListener('keydown', (e) => { if (e.key === 'Escape') fechar(); });

    // vista inicial
    calcLimites();
    const estadoBounds = L.geoJSON(geo).getBounds();
    if (params.has('lat') && params.has('lng') && params.has('z')) map.setView([Number(params.get('lat')), Number(params.get('lng'))], Number(params.get('z')));
    else map.fitBounds(estadoBounds, { padding: [30, 30] });
    map.on('moveend zoomend', atualizarLink);
    anos = D.meta.years;
    const cd0 = params.get('m'); if (cd0 && D.municipios[cd0]) abrir(cd0);
    repintar();
    atualizarLink();
    window.OpenLuxExplorador = { map, camadas, get ano() { return anos[ano]; } };
  }

  // união dos 92 polígonos = limite estadual
  // Sem união geométrica: o contorno estadual é o conjunto dos limites municipais em traço mais forte.
  function unirEstado(geo) { return geo; }
})();
