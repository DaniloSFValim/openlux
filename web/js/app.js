/* OpenLux — interface. Todos os valores vêm de data/indicators.json (saída real do pipeline). */
(async function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const nfs = {};
  const fmt = (v, d = 2) => {
    if (v == null || !isFinite(v)) return '—';
    nfs[d] = nfs[d] || new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
    return nfs[d].format(v);
  };
  const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

  let data, geo, pxMeta = null;
  try {
    [data, geo, pxMeta] = await Promise.all([
      fetch('data/indicators.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }),
      fetch('data/municipios.geojson').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }),
      fetch('data/pixels/meta.json').then((r) => (r.ok ? r.json() : null)).catch(() => null),  // camada de pixel é opcional
    ]);
  } catch (e) {
    $('alert-text').textContent = 'Não foi possível carregar os dados (data/indicators.json). Sirva a pasta web/ por HTTP (por exemplo: python -m http.server) e gere os dados com scripts/build_web_data.py.';
    return;
  }

  const meta = data.meta, years = meta.years, M = data.municipios;
  const codes = Object.keys(M).sort((a, b) => M[a].name.localeCompare(M[b].name, 'pt-BR'));
  const winKeys = Object.keys(meta.windows);
  const wLabel = (w) => `${meta.windows[w][0]}–${meta.windows[w][1]}`;

  /* ---------- classificação ---------- */
  const quantile = (arr, p) => {
    const a = arr.filter((v) => v != null && isFinite(v)).sort((x, y) => x - y);
    if (!a.length) return NaN;
    const i = (a.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
    return a[lo] + (a[hi] - a[lo]) * (i - lo);
  };
  const sig = (v, n = 3) => (v === 0 ? 0 : Number(Number(v).toPrecision(n)));
  const classOf = (v, br) => { let k = 0; while (k < br.length && v >= br[k]) k++; return k; };
  const SEQ = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'];
  const DIV = ['#5e3c99', '#b2abd2', '#f2f2f2', '#fdb863', '#e66101'];
  const NODATA = getComputedStyle(document.documentElement).getPropertyValue('--nodata').trim() || '#b4bac3';

  const pooled = (fn) => codes.flatMap((c) => fn(M[c]));
  const IND = {};
  const mkBreaksQ = (vals) => [0.2, 0.4, 0.6, 0.8].map((p) => sig(quantile(vals, p)));
  const absBreaks = (vals) => { const a = vals.filter((v) => v != null).map(Math.abs);
    const lo = sig(quantile(a, 0.5)), hi = sig(quantile(a, 0.9)); return [-hi, -lo, lo, hi]; };

  IND.mean = { label: 'Radiância média anual', unit: 'nW·cm⁻²·sr⁻¹', kind: 'obs', type: 'seq', yearly: true, d: 2,
    get: (m, i) => m.mean[i], breaks: mkBreaksQ(pooled((m) => m.mean)),
    scheme: 'Quantis (5 classes) da distribuição de todos os municípios e anos; limites fixos entre os anos.',
    period: (y) => `ano ${y}`, source: 'NASA Black Marble VNP46A4 v2.0 (Suomi NPP), camada AllAngle_Composite_Snow_Free; agregação por município (IBGE 2024).' };
  IND.valid = { label: 'Fração da área municipal com pixels válidos', unit: 'fração (0–1)', kind: 'qa', type: 'seq', yearly: true, d: 3,
    get: (m, i) => m.valid[i], breaks: [0.6, 0.85, 0.95, 0.999],
    scheme: 'Classes manuais (controle de qualidade): < 0,6; 0,6–0,85; 0,85–0,95; 0,95–0,999; ≥ 0,999.',
    period: (y) => `ano ${y}`, source: 'Pixels excluídos por máscara de água, qualidade ou fill (ver Metodologia).' };
  const uniq = (a) => a.filter((v, i) => i === 0 || v > a[i - 1]);
  if (codes.every((c) => M[c].lit)) {
    const thr = (meta.thresholds_nw_cm2_sr || {}).lit_0p5;
    IND.lit = { label: `Fração da área com radiância ≥ ${fmt(thr, 1)} nW·cm⁻²·sr⁻¹`, unit: 'fração da área válida (0–1)', kind: 'der', type: 'seq', yearly: true, d: 3,
      get: (m, i) => m.lit[i], breaks: uniq(mkBreaksQ(pooled((m) => m.lit))),
      scheme: `Quantis (até 5 classes) de todos os municípios e anos, limites fixos entre os anos; classes repetidas são fundidas. O limiar ${fmt(thr, 1)} é o valor abaixo do qual o produto zera a radiância (guia Black Marble). Esta fração é especialmente sensível ao piso de ruído do S-NPP a partir de 2022.`,
      period: (y) => `ano ${y}`, source: 'Derivado: fração da área municipal válida com radiância ≥ limiar (cobertura fracionária; VNP46A4, S-NPP).' };
  }
  const slopes = pooled((m) => winKeys.map((w) => m.trends[w] && m.trends[w].slope));
  const chgs = pooled((m) => winKeys.map((w) => m.trends[w] && m.trends[w].change_pct));
  const slopeBr = absBreaks(slopes), chgBr = absBreaks(chgs);
  winKeys.forEach((w) => {
    IND['slope_' + w] = { label: `Tendência da radiância (Theil–Sen), ${wLabel(w)}`, unit: 'nW·cm⁻²·sr⁻¹ por ano', kind: 'der', type: 'div', d: 3, win: w, sigP: true,
      get: (m) => (m.trends[w] ? m.trends[w].slope : null), breaks: slopeBr,
      scheme: 'Classificação analítica: limites em ± mediana e ± percentil 90 de |inclinação| (agrupando as janelas). Contorno espesso: p < 0,05 (Kendall).',
      period: () => wLabel(w), source: 'Derivado da série anual de radiância média (VNP46A4, S-NPP). Mínimo de 8 anos válidos.' };
    IND['change_' + w] = { label: `Variação percentual da radiância, ${wLabel(w)}`, unit: '%', kind: 'der', type: 'div', d: 1, win: w,
      get: (m) => (m.trends[w] ? m.trends[w].change_pct : null), breaks: chgBr,
      scheme: `Classificação analítica: limites em ± mediana e ± percentil 90 de |variação|. Cinza: linha de base abaixo do piso de ${fmt(meta.change_floor_nw_cm2_sr[w], 2)} nW·cm⁻²·sr⁻¹ (percentil 25 das médias municipais).`,
      period: () => `${meta.windows[w][0]} → ${meta.windows[w][1]}`, source: 'Derivado da radiância média dos anos inicial e final da janela.' };
  });
  if (codes.every((c) => M[c].sensors)) {
    const sbr = absBreaks(pooled((m) => [m.sensors.slope_snpp, m.sensors.slope_noaa20]));
    const mk = (sensor, key, pkey) => ({ label: `Tendência da radiância (Theil–Sen), ${sensor}, 2018–2025`, unit: 'nW·cm⁻²·sr⁻¹ por ano', kind: 'der', type: 'div', d: 3, sigP: true,
      get: (m) => m.sensors[key], pval: (m) => m.sensors[pkey], breaks: sbr,
      scheme: 'Classificação analítica: limites em ± mediana e ± percentil 90 de |inclinação| (agrupando os dois sensores, para comparar os mapas). Contorno espesso: p < 0,05 (Kendall).',
      period: () => '2018–2025', source: `Derivado da série anual de radiância média do ${sensor} (${sensor === 'NOAA-20' ? 'VJ146A4' : 'VNP46A4'}); mínimo de 8 anos válidos.` });
    IND.slope_snpp_1825 = mk('S-NPP', 'slope_snpp', 'p_snpp');
    IND.slope_noaa20_1825 = mk('NOAA-20', 'slope_noaa20', 'p_noaa20');
  }
  IND.percap = { label: 'Intensidade radiante aparente por habitante, 2022', unit: 'mW·sr⁻¹ por habitante', kind: 'der', type: 'seq', d: 1,
    get: (m) => m.per_capita_mw_sr_hab, breaks: mkBreaksQ(pooled((m) => [m.per_capita_mw_sr_hab])),
    scheme: 'Quantis (5 classes) dos 92 municípios. Índice relativo: não representa consumo ou emissão individual.',
    period: () => 'ano 2022 (Censo)', source: 'Intensidade radiante aparente (radiância × área, direção do sensor) ÷ população residente do Censo 2022 (IBGE).' };
  if (codes.every((c) => M[c].exposure)) {
    const POPNOTE = ' População do Censo 2022 mantida fixa em todos os anos: a variação temporal reflete a radiância, não a demografia. Ponderação areal simples (sem dasimetria).';
    const ex = (k) => (m, i) => m.exposure[k][i];
    const exb = (k) => uniq(mkBreaksQ(pooled((m) => m.exposure[k])));
    IND.popL = { label: 'Radiância ponderada pela população', unit: 'nW·cm⁻²·sr⁻¹', kind: 'der', type: 'seq', yearly: true, d: 2,
      get: ex('pop_radiance'), breaks: exb('pop_radiance'),
      scheme: 'Quantis (até 5 classes) de todos os municípios e anos, limites fixos entre os anos. Radiância que a população do município “habita” (Σ pop·L / Σ pop nos pixels válidos); não mede exposição individual.' + POPNOTE,
      period: (y) => `ano ${y}`, source: 'Derivado: setores censitários do Censo 2022 (IBGE) × VNP46A4 (S-NPP); população do setor repartida entre os pixels pela fração de cobertura.' };
    IND.popLit = { label: `População em áreas com radiância ≥ ${fmt((meta.thresholds_nw_cm2_sr || {}).lit_0p5 ?? 0.5, 1)} nW·cm⁻²·sr⁻¹`, unit: 'fração da população em pixels válidos (0–1)', kind: 'der', type: 'seq', yearly: true, d: 3,
      get: ex('pop_lit'), breaks: exb('pop_lit'),
      scheme: 'Quantis (até 5 classes) de todos os municípios e anos; classes repetidas são fundidas. Sensível ao piso de ruído do S-NPP a partir de 2022.' + POPNOTE,
      period: (y) => `ano ${y}`, source: 'Derivado: setores censitários do Censo 2022 (IBGE) × VNP46A4 (S-NPP).' };
    IND.urban = { label: 'Radiância média nas áreas urbanas (setores “Urbana”)', unit: 'nW·cm⁻²·sr⁻¹', kind: 'der', type: 'seq', yearly: true, d: 2,
      get: ex('urban'), breaks: exb('urban'),
      scheme: 'Quantis (até 5 classes). Classificação urbano/rural do IBGE (campo SITUACAO do Censo 2022), ponderada pela cobertura do pixel. Cinza: município sem área urbana válida.',
      period: (y) => `ano ${y}`, source: 'Derivado: setores censitários do Censo 2022 (IBGE) × VNP46A4 (S-NPP).' };
    IND.rural = { label: 'Radiância média nas áreas rurais (setores “Rural”)', unit: 'nW·cm⁻²·sr⁻¹', kind: 'der', type: 'seq', yearly: true, d: 2,
      get: ex('rural'), breaks: exb('rural'),
      scheme: 'Quantis (até 5 classes). Classificação urbano/rural do IBGE (SITUACAO), ponderada pela cobertura do pixel. Cinza: município sem área rural válida (7 municípios).',
      period: (y) => `ano ${y}`, source: 'Derivado: setores censitários do Censo 2022 (IBGE) × VNP46A4 (S-NPP).' };
  }
  if (codes.every((c) => M[c].pixel_trend)) {
    Object.keys(meta.windows).forEach((w) => {
      [['up', 'aumento', 'pxup_'], ['down', 'redução', 'pxdown_']].forEach(([k, nome, pre]) => {
        IND[pre + w] = { label: `Pixels iluminados com ${nome} significativo, ${wLabel(w)}`, unit: 'fração dos pixels iluminados testados (0–1)', kind: 'der', type: 'seq', d: 3, win: w,
          get: (m) => (m.pixel_trend[w] ? m.pixel_trend[w][k] : null), breaks: uniq(mkBreaksQ(pooled((m) => Object.keys(meta.windows).map((x) => m.pixel_trend[x] && m.pixel_trend[x][k])))),
          scheme: 'Quantis (até 5 classes), agrupando as janelas. Mann–Kendall + Sen por pixel, controle de falsas descobertas (Benjamini–Hochberg, 5%) sobre os pixels testados; só pixels com mediana ≥ 0,5 nW·cm⁻²·sr⁻¹ e ≥ 8 anos válidos. Não corrige dependência espacial. A janela que inclui 2022–2025 herda o piso de ruído do S-NPP.',
          period: () => wLabel(w), source: 'Derivado da série anual por pixel (VNP46A4, S-NPP); participação ponderada pela cobertura do pixel no município.' };
      });
    });
  }
  const KIND = { obs: ['obs', 'Observado (agregado)'], der: ['der', 'Derivado'], qa: ['qa', 'Controle de qualidade'] };

  const st = { ind: 'mean', iy: years.length - 1, sel: null, layer: pxMeta ? 'pixel' : 'mun', sensor: 'snpp', view: 'rad', alpha: 0.9, basemap: false, outlines: true, pxOn: true, playing: false };
  const val = (cd, key = st.ind, iy = st.iy) => { const v = IND[key].get(M[cd], iy); return v == null || !isFinite(v) ? null : v; };

  /* ---------- aviso metodológico (dados) ---------- */
  (function alertText() {
    const qa = data.qa, pre = qa.filter((r) => r.year <= 2021), post = qa.filter((r) => r.year >= 2022);
    const mx = (a, k) => Math.max(...a.map((r) => r[k])), mn = (a, k) => Math.min(...a.map((r) => r[k]));
    const t = `A série (sensor Suomi NPP) mostra, a partir de 2022, aumento do piso de ruído em áreas escuras: a radiância média dos pixels persistentemente escuros em terra era ${fmt(mn(pre, 'dark_land_mean'), 3)}–${fmt(mx(pre, 'dark_land_mean'), 3)} até 2021 e passou a ${fmt(mn(post, 'dark_land_mean'), 3)}–${fmt(mx(post, 'dark_land_mean'), 3)} depois (nW·cm⁻²·sr⁻¹). Esse efeito é bem menor no NOAA-20. Há também um aumento comum aos dois sensores que não foi separado de um possível artefato do algoritmo compartilhado. O sinal da tendência depende da janela de anos. Estes resultados são diagnósticos de desenvolvimento, não foram validados e não devem ser interpretados como mudança real de iluminação sem essa ressalva. Veja “Limitações”.`;
    $('alert-text').textContent = t;
  })();

  /* ---------- mapa ---------- */
  const map = L.map('mapa', { zoomSnap: 0.25, minZoom: 6, maxZoom: 12, attributionControl: true });  // 12: um pixel de ~460 m já ocupa ~13 px
  map.attributionControl.setPrefix(false);
  map.attributionControl.addAttribution('Malha: IBGE (compatível com CC BY 4.0) · Radiância: NASA Black Marble · Exibição em Web Mercator; cálculos em grade lat/lon');
  L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);
  // HUD: ano em destaque e aviso de ruído do S-NPP (visíveis durante a animação)
  const Hud = L.Control.extend({ options: { position: 'topleft' }, onAdd() { const d = L.DomUtil.create('div', 'hud'); d.innerHTML = '<div class="y" id="hud-year"></div><div class="w" id="hud-warn" hidden>S-NPP: piso de ruído maior desde 2022; não leia como luz nova.</div>'; return d; } });
  new Hud().addTo(map);
  // Painel "Camadas": o visitante liga/desliga camadas. Terceiros (mapa-base) só se ele ligar.
  const LayersCtl = L.Control.extend({ options: { position: 'topright' }, onAdd() {
    const d = L.DomUtil.create('div', 'layers-ctl');
    d.innerHTML = `<button type="button" id="layers-btn" aria-expanded="false" aria-controls="layers-panel">Camadas</button>
      <div class="lp" id="layers-panel" hidden>
        <label><input type="checkbox" id="px-chk" checked> Camada de pixel</label>
        <div class="sub"><label>Opacidade <input type="range" id="px-opacity" min="0.3" max="1" step="0.05" value="0.9" aria-label="Opacidade da camada de pixel"></label></div>
        <label><input type="checkbox" id="outline-chk" checked> Limites municipais</label>
        <label><input type="checkbox" id="labels-chk" checked> Nomes dos municípios</label>
        <label><input type="checkbox" id="base-chk"> Mapa-base (OpenStreetMap)</label>
        <div class="sub small">Ao ligar, seu navegador baixa imagens do servidor do OpenStreetMap, que recebe o seu endereço IP. Desligado por padrão.</div>
        <label>Tema <select id="theme-sel"><option value="auto">Automático</option><option value="light">Claro</option><option value="dark">Escuro</option></select></label>
      </div>`;
    L.DomEvent.disableClickPropagation(d); L.DomEvent.disableScrollPropagation(d); return d; } });
  new LayersCtl().addTo(map);
  $('layers-btn').addEventListener('click', () => { const open = $('layers-panel').hidden; $('layers-panel').hidden = !open; $('layers-btn').setAttribute('aria-expanded', String(open)); });
  // Mapa-base OPCIONAL (desligado por padrão): ao ligar, o navegador baixa imagens do servidor do OpenStreetMap, que recebe o IP do visitante.
  const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 12, className: 'osm-tiles', attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a> contributors' });
  const layerByCode = {};
  const gl = L.geoJSON(geo, {
    style: () => ({ weight: 0.6, color: '#555', fillOpacity: 0.92 }),
    onEachFeature: (f, layer) => {
      const cd = f.properties.CD_MUN; layerByCode[cd] = layer;
      layer.on('click', () => select(cd));
      layer.on('mouseover', () => layer.openTooltip());
    },
  }).addTo(map);
  map.fitBounds(gl.getBounds(), { padding: [8, 8] });

  /* ---------- camada de pixel (grade de classes, desenhada no navegador) ---------- */
  // Claro: amarelo → vinho (YlOrRd). Escuro: inferno, perceptualmente uniforme e feita para fundo escuro.
  const PXPAL = { light: ['#f2f2f2', '#ffeda0', '#fec44f', '#fd8d3c', '#e31a1c', '#800026'], dark: ['#1b2230', '#420a68', '#932667', '#dd513a', '#fca50a', '#fcffa4'] };
  const CHPAL = { light: { 1: '#e9ecf0', 2: '#c9ced6', 3: '#e66101', 4: '#5e3c99' }, dark: { 1: '#222b3a', 2: '#3a4557', 3: '#ff9e4a', 4: '#9b8fe0' } };
  const hex2rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const sysDark = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : { matches: false };
  const isDark = () => { const t = document.documentElement.getAttribute('data-theme'); return t === 'dark' || (t !== 'light' && sysDark.matches); };
  const themeKey = () => (isDark() ? 'dark' : 'light');
  const nodataRgb = () => hex2rgb((getComputedStyle(document.documentElement).getPropertyValue('--nodata').trim() || '#b4bac3').slice(0, 7));
  const pxCache = {};
  function pxGrid(path) {
    if (!pxCache[path]) {
      const g = pxMeta.grid;
      pxCache[path] = fetch(`data/pixels/${path}.bin`).then((r) => { if (!r.ok) throw new Error(r.status); return r.arrayBuffer(); })
        .then((b) => { const a = new Uint8Array(b); if (a.length !== g.rows * g.cols) throw new Error('grade com tamanho inesperado'); return a; });
    }
    return pxCache[path];
  }
  const sensorYears = (sk) => Object.keys(pxMeta.sensors[sk].years).map(Number);
  const pxPath = () => (st.view === 'rad' ? `${st.sensor}/${years[st.iy]}` : `${st.sensor}/change_${st.view}`);
  function pxPalette() {   // código da grade → [r, g, b, fator de opacidade]
    const pal = new Array(8).fill(null), th = themeKey();
    if (st.view === 'rad') {
      pal[1] = [...nodataRgb(), 1];
      PXPAL[th].forEach((h, k) => { pal[pxMeta.classes.first_code + k] = [...hex2rgb(h), k === 0 && st.basemap ? 0.25 : 1]; });  // com mapa-base, "sem luz" fica quase transparente
    } else {
      Object.entries(CHPAL[th]).forEach(([c, h]) => { pal[+c] = [...hex2rgb(h), +c <= 2 && st.basemap ? 0.3 : 1]; });
    }
    return pal;
  }
  const pxCell = (ll) => { const g = pxMeta.grid; // índice (linha, coluna) da grade lat/lon; null fora da janela
    const c = Math.floor((ll.lng - g.lon_west) / g.pixel_deg), r = Math.floor((g.lat_north - ll.lat) / g.pixel_deg);
    return r < 0 || c < 0 || r >= g.rows || c >= g.cols ? null : [r, c]; };
  const PixelLayer = L.Layer.extend({
    onAdd(m) {
      this._map = m; if (!m.getPane('pixels')) { const pn = m.createPane('pixels'); pn.style.zIndex = 250; pn.style.pointerEvents = 'none'; }
      this._cv = L.DomUtil.create('canvas', 'openlux-pixels leaflet-zoom-hide'); m.getPane('pixels').appendChild(this._cv);
      m.on('moveend zoomend resize', this.redraw, this); this.redraw();
    },
    onRemove(m) { m.off('moveend zoomend resize', this.redraw, this); this._cv.remove(); },
    setGrid(a, pal, alpha) { this._grid = a; this._pal = pal; this._alpha = alpha; this.redraw(); },
    redraw() {
      const m = this._map, cv = this._cv; if (!m || !cv) return;
      const sz = m.getSize(), g = pxMeta.grid; cv.width = sz.x; cv.height = sz.y;
      L.DomUtil.setPosition(cv, m.containerPointToLayerPoint([0, 0]));
      if (!this._grid) return;
      const ctx = cv.getContext('2d'), img = ctx.createImageData(sz.x, sz.y), d = img.data;
      const cols = new Int32Array(sz.x), rows = new Int32Array(sz.y);
      for (let x = 0; x < sz.x; x++) { const c = Math.floor((m.containerPointToLatLng([x, 0]).lng - g.lon_west) / g.pixel_deg); cols[x] = c < 0 || c >= g.cols ? -1 : c; }
      for (let y = 0; y < sz.y; y++) { const r = Math.floor((g.lat_north - m.containerPointToLatLng([0, y]).lat) / g.pixel_deg); rows[y] = r < 0 || r >= g.rows ? -1 : r; }
      const pal = this._pal;
      for (let y = 0; y < sz.y; y++) { if (rows[y] < 0) continue; const base = rows[y] * g.cols;
        for (let x = 0; x < sz.x; x++) { if (cols[x] < 0) continue;
          const col = pal[this._grid[base + cols[x]]]; if (!col) continue; const i = (y * sz.x + x) * 4;
          d[i] = col[0]; d[i + 1] = col[1]; d[i + 2] = col[2]; d[i + 3] = Math.round(this._alpha * col[3]); } }
      ctx.putImageData(img, 0, 0);
    },
  });
  const pxLayer = pxMeta ? new PixelLayer() : null;
  async function pxShow() {
    const path = pxPath();
    try { const a = await pxGrid(path); if (pxPath() === path && st.layer === 'pixel') pxLayer.setGrid(a, pxPalette(), Math.round(255 * st.alpha)); }
    catch (e) { $('pixel-readout').hidden = false; $('pixel-readout').textContent = 'Não foi possível carregar a camada de pixel deste ano.'; }
  }
  const pxShare = (a, code) => { let n = 0, t = 0; for (let i = 0; i < a.length; i++) { if (a[i] >= 2) { t++; if (a[i] === code) n++; } } return t ? n / t : NaN; };
  async function pxNote(y) {
    if (y < 2022 || st.view !== 'rad') return '';
    const sk = st.sensor, nm = pxMeta.sensors[sk].name;
    try { const [a, b] = await Promise.all([pxGrid(`${sk}/2021`), pxGrid(`${sk}/${y}`)]);
      const lab = pxMeta.classes.labels, why = sk === 'snpp'
        ? 'a partir de 2022 o sensor tem um piso de ruído mais alto em áreas escuras. Parte dessa mudança pode ser ruído, não luz nova (ver o aviso acima).'
        : 'o NOAA-20 tem piso de ruído bem menor que o S-NPP, mas usa o mesmo algoritmo: uma mudança comum aos dois sensores não é separável aqui.';
      return `<div class="pxnote"><strong>Atenção (${esc(nm)}, ${y}):</strong> a parcela dos pixels com valor na classe ${esc(lab[1])} passou de ${fmt(100 * pxShare(a, 3), 1)}% em 2021 para ${fmt(100 * pxShare(b, 3), 1)}% em ${y}, e a da classe ${esc(lab[0])} foi de ${fmt(100 * pxShare(a, 2), 1)}% para ${fmt(100 * pxShare(b, 2), 1)}%. ${why}</div>`;
    } catch (e) { return ''; }
  }
  const PLAIN = ['Sem luz detectada', 'Muito pouca luz', 'Pouca luz', 'Luz moderada', 'Muita luz', 'Muitíssima luz'];
  async function renderPixelLegend() {
    const th = themeKey(), sk = st.sensor, sm = pxMeta.sensors[sk];
    if (st.view !== 'rad') { renderChangeLegend(th, sk, sm); return; }
    const y = years[st.iy], c = pxMeta.classes;
    const items = c.labels.map((l, k) => `<li><span class="sw" style="background:${PXPAL[th][k]}"></span>${esc(PLAIN[k])} <span class="muted">· ${esc(l)}</span></li>`).join('') + `<li><span class="sw" style="background:var(--nodata)"></span>sem dado válido (água, qualidade)</li>`;
    $('legend').innerHTML = `<h3>Radiância noturna por pixel <span class="badge obs">Observado</span><span class="badge cls">Classes fixas</span></h3>
      <div><strong>Sensor:</strong> ${esc(sm.name)} · <strong>Unidade:</strong> nW·cm⁻²·sr⁻¹ · <strong>Período:</strong> ano ${y}</div><ul>${items}</ul>
      <details class="meaning" open><summary>O que isto significa</summary><ul>
        <li>O satélite registra a luz que sobe da superfície à noite, em quadradinhos (pixels) de cerca de 460 m. Cores mais claras e quentes no mapa = mais luz detectada.</li>
        <li><strong>Isto não é o brilho do céu</strong> que uma pessoa enxerga do chão: o céu também depende da atmosfera, das nuvens, da Lua e da luz de lugares distantes.</li>
        <li>Mais luz detectada não é, por si só, medida de dano: o OpenLux mede a luz que o satélite vê, não seus efeitos.</li>
        <li>Os nomes das faixas (de “sem luz detectada” a “muitíssima luz”) são só uma forma simples de ler os números: não são classes oficiais nem equivalem à escala Bortle.</li>
        <li>Estes valores ainda <strong>não foram validados em campo</strong>.</li></ul></details>
      <div class="small"><strong>Classificação:</strong> limites fixos (0,5; 2; 8; 30; 100), iguais em todos os anos e sensores; 0,5 é o valor abaixo do qual o produto zera a radiância. Intervalos fechados à esquerda: [a, b). A grade mostra a classe, não o valor.</div>
      <div class="small muted"><strong>Fonte:</strong> NASA Black Marble ${esc(sm.product)} v2.0, camada AllAngle_Composite_Snow_Free, qualidade 0, apenas terra; pixels do estado (malha IBGE 2024).</div><div id="pxnote"></div>`;
    const n = await pxNote(y); if (years[st.iy] === y && st.view === 'rad' && $('pxnote')) $('pxnote').innerHTML = n;
  }
  function renderChangeLegend(th, sk, sm) {
    const w = sm.change[st.view], cn = w.counts, tested = cn.increase + cn.decrease + cn.not_significant, pc = (v) => fmt(100 * v / tested, 1) + '%';
    const lbl = `${w.years[0]}–${w.years[1]}`, noisy = sk === 'snpp' && w.years[1] >= 2022;
    const items = [[3, 'Aumento significativo', cn.increase], [4, 'Redução significativa', cn.decrease], [2, 'Sem mudança significativa', cn.not_significant]]
      .map(([c, t, n]) => `<li><span class="sw" style="background:${CHPAL[th][c]}"></span>${t} <span class="muted">· ${pc(n)} dos pixels testados</span></li>`).join('')
      + `<li><span class="sw" style="background:${CHPAL[th][1]}"></span>Não testado <span class="muted">· sem luz na mediana dos anos ou poucos anos válidos</span></li>`;
    $('legend').innerHTML = `<h3>Mudança por pixel, ${esc(lbl)} <span class="badge der">Derivado</span><span class="badge cls">Mann–Kendall + Sen, FDR 5%</span></h3>
      <div><strong>Sensor:</strong> ${esc(sm.name)} · <strong>Janela:</strong> ${esc(lbl)} (${w.n_years} anos) · <strong>Pixels testados:</strong> ${fmt(tested, 0)}</div><ul>${items}</ul>
      ${noisy ? `<div class="pxnote"><strong>Atenção:</strong> esta janela inclui 2022–2025, quando o S-NPP tem mais ruído em áreas escuras. Os aumentos predominam (${pc(cn.increase)} contra ${pc(cn.decrease)} de reduções), e isso coincide com esse ruído: <strong>não leia como luz nova</strong>. Compare com a janela 2012–2021 ou com o NOAA-20.</div>` : ''}
      ${sk === 'noaa20' ? `<div class="pxnote"><strong>Atenção:</strong> série curta (${w.n_years} anos, o mínimo exigido); o teste tem pouco poder. Aumentos comuns aos dois sensores não são separáveis de um possível artefato do algoritmo compartilhado.</div>` : ''}
      <details class="meaning" open><summary>O que isto significa</summary><ul>
        <li>Cada pixel é testado separadamente sobre a série anual da janela. A cor mostra o sentido da tendência quando ela é estatisticamente significativa.</li>
        <li>O controle de falsas descobertas (5%) vale para os pixels do estado, mas pixels vizinhos são parecidos entre si e isso não é corrigido.</li>
        <li><strong>Significativo não quer dizer luz nova</strong>, nem dano: pode ser ruído do sensor, mudança de lâmpada, vegetação, ocupação.</li>
        <li>Só entram pixels iluminados (mediana anual ≥ ${esc(String(pxMeta.change_params.tau_nw_cm2_sr).replace('.', ','))} nW·cm⁻²·sr⁻¹) com pelo menos ${pxMeta.change_params.min_valid_years} anos válidos.</li>
        <li>Estes resultados <strong>não foram validados em campo</strong>.</li></ul></details>
      <div class="small muted"><strong>Fonte:</strong> NASA Black Marble ${esc(sm.product)} v2.0, mesma série da camada de radiância; método em METHODOLOGY.md, seção 7.1.</div>`;
  }
  function pxReadout(ll) {
    const box = $('pixel-readout'); if (st.layer !== 'pixel' || !pxLayer._grid) return;
    const cell = pxCell(ll); box.hidden = false;
    if (!cell) { box.textContent = 'Passe o cursor sobre o mapa (ou toque) para ver a classe do pixel.'; return; }
    const code = pxLayer._grid[cell[0] * pxMeta.grid.cols + cell[1]], f = pxMeta.classes.first_code;
    let what;
    if (st.view === 'rad') what = code === 0 ? 'fora do estado' : code === 1 ? 'sem dado válido' : `${pxMeta.classes.labels[code - f]} nW·cm⁻²·sr⁻¹`;
    else what = pxMeta.change_codes[String(code)] || 'fora do estado';
    box.textContent = `Pixel (${fmt(ll.lat, 4)}°, ${fmt(ll.lng, 4)}°), ${st.view === 'rad' ? 'ano ' + years[st.iy] : 'mudança ' + st.view.replace('_', '–')}, ${pxMeta.sensors[st.sensor].name.split(' (')[0]}: ${what}. Mostra a classe, não o valor.`;
  }
  if (pxLayer) { map.on('mousemove click', (e) => pxReadout(e.latlng)); }

  const palColor = (ind, k) => { const pal = ind.type === 'div' ? DIV : SEQ, n = ind.breaks.length;
    return pal[n === pal.length - 1 ? k : Math.round((k * (pal.length - 1)) / n)]; };
  const pOf = (ind, cd) => (ind.pval ? ind.pval(M[cd]) : (ind.win && M[cd].trends[ind.win] ? M[cd].trends[ind.win].p_value : null));
  function colorFor(ind, v) {
    if (v == null) return NODATA;
    return palColor(ind, classOf(v, ind.breaks));
  }
  function className(ind, k) {
    const b = ind.breaks, n = b.length;
    if (k === 0) return `< ${fmt(b[0], ind.d)}`;
    if (k === n) return `≥ ${fmt(b[n - 1], ind.d)}`;
    return `${fmt(b[k - 1], ind.d)} a < ${fmt(b[k], ind.d)}`;
  }

  function render() {
    const ind = IND[st.ind], px = st.layer === 'pixel';
    const showYear = px ? st.view === 'rad' : ind.yearly;
    $('year-wrap').hidden = !showYear;
    $('year-note').hidden = !showYear;
    $('px-wrap').hidden = !px;
    $('indicator').disabled = px;
    document.documentElement.classList.toggle('is-dark', isDark());
    if (pxLayer) { if (px && st.pxOn) { if (!map.hasLayer(pxLayer)) pxLayer.addTo(map); pxShow(); } else if (map.hasLayer(pxLayer)) map.removeLayer(pxLayer); }
    const yearly = px ? st.view === 'rad' : !!ind.yearly;
    const hudText = px && st.view !== 'rad' ? `mudança ${st.view.replace('_', '–')}` : (yearly ? String(years[st.iy]) : '');
    $('hud-year').textContent = hudText; $('hud-year').parentElement.hidden = !hudText;
    $('hud-warn').hidden = !(yearly && years[st.iy] >= 2022 && (!px || st.sensor === 'snpp'));
    $('play-btn').disabled = !yearly;
    $('pixel-readout').hidden = !px;
    if (px) $('pixel-readout').textContent = 'Passe o cursor sobre o mapa (ou toque) para ver a classe do pixel.';
    gl.eachLayer((layer) => {
      const cd = layer.feature.properties.CD_MUN, sel = cd === st.sel;
      if (px) {
        layer.setStyle({ fillOpacity: 0, weight: sel ? 3.2 : 0.8, color: sel ? (isDark() ? '#6ea2ff' : '#0b5fff') : (isDark() ? '#b9c3d1' : '#3b3b3b'), opacity: sel ? 1 : (st.outlines ? 0.7 : 0) });
        if (sel) layer.bringToFront();
        layer.unbindTooltip().bindTooltip(`<strong>${esc(M[cd].name)}</strong>`, { sticky: true });
        return;
      }
      const v = val(cd), pv = pOf(ind, cd), sigP = ind.sigP && pv != null && pv < 0.05;
      layer.setStyle({ fillColor: colorFor(ind, v), weight: sel ? 3.2 : sigP ? 2.2 : 0.6, color: sel ? '#0b5fff' : sigP ? '#000' : '#555', fillOpacity: 0.92, opacity: 1 });
      if (sel || sigP) layer.bringToFront();
      let tip = `<strong>${esc(M[cd].name)}</strong><br>${v == null ? 'sem dado válido' : fmt(v, ind.d) + ' ' + esc(ind.unit)}`;
      if (v != null) tip += `<br><span class="muted">classe: ${esc(className(ind, classOf(v, ind.breaks)))}</span>`;
      if (ind.sigP && pOf(ind, cd) != null) tip += `<br>p = ${fmt(pOf(ind, cd), 3)}`;
      layer.unbindTooltip().bindTooltip(tip, { sticky: true });
    });
    if (px) renderPixelLegend(); else renderLegend(ind);
    renderRank();
    writeUrl();
  }

  function renderLegend(ind) {
    const [kcls, ktxt] = KIND[ind.kind];
    const yr = ind.yearly ? years[st.iy] : null;
    const items = Array.from({ length: ind.breaks.length + 1 }, (_, k) => `<li><span class="sw" style="background:${palColor(ind, k)}"></span>${esc(className(ind, k))}</li>`).join('') +
      `<li><span class="sw" style="background:${NODATA}"></span>sem dado${ind.kind === 'der' && ind.win ? ' / abaixo do piso' : ''}</li>`;
    $('legend').innerHTML = `<h3>${esc(ind.label)} <span class="badge ${kcls}">${ktxt}</span><span class="badge cls">Classes: classificação analítica</span></h3>
      <div><strong>Unidade:</strong> ${esc(ind.unit)} · <strong>Período:</strong> ${esc(ind.period(yr))}</div>
      <ul>${items}</ul>
      <div class="small"><strong>Classificação:</strong> ${esc(ind.scheme)}</div>
      <div class="small muted"><strong>Fonte:</strong> ${esc(ind.source)} Intervalos fechados à esquerda: [a, b).</div>`;
  }

  /* ---------- controles ---------- */
  Object.entries(IND).forEach(([k, v]) => { const o = document.createElement('option'); o.value = k; o.textContent = v.label; $('indicator').appendChild(o); });
  const yr = $('year'); yr.min = 0; yr.max = years.length - 1; yr.value = st.iy;
  const yrOut = () => { $('year-out').textContent = years[st.iy]; yr.setAttribute('aria-valuetext', String(years[st.iy])); };
  yrOut();
  $('indicator').addEventListener('change', (e) => { stopAnim(); st.ind = e.target.value; render(); });
  function clampYear() {   // o NOAA-20 só tem 2018–2025: leva o ano ao mais próximo disponível
    if (!pxMeta) return; const ok = sensorYears(st.sensor);
    if (!ok.includes(years[st.iy])) { const near = ok.reduce((b, v) => (Math.abs(v - years[st.iy]) < Math.abs(b - years[st.iy]) ? v : b), ok[0]); st.iy = years.indexOf(near); yr.value = st.iy; yrOut(); }
  }
  yr.addEventListener('input', (e) => { stopAnim(); st.iy = +e.target.value; yrOut(); if (st.layer === 'pixel' && st.view === 'rad') clampYear(); render(); if (st.sel) renderDetail(); });
  const optionsHtml = (blank) => (blank ? '<option value="">— nenhum —</option>' : '') + codes.map((c) => `<option value="${c}">${esc(M[c].name)}</option>`).join('');
  $('mun-select').innerHTML = '<option value="">Selecione…</option>' + optionsHtml(false);
  $('mun-select').addEventListener('change', (e) => select(e.target.value || null));
  if (!pxLayer) $('layer-wrap').hidden = true;
  document.querySelectorAll('input[name="layer"]').forEach((r) => { r.checked = r.value === st.layer; r.addEventListener('change', (e) => { if (e.target.checked) { stopAnim(); st.layer = e.target.value; render(); } }); });
  $('reset-btn').addEventListener('click', () => map.fitBounds(gl.getBounds(), { padding: [8, 8] }));
  if (pxMeta) {
    $('px-sensor').innerHTML = Object.entries(pxMeta.sensors).map(([k, v]) => `<option value="${k}">${esc(v.name)}</option>`).join('');
    const fixView = () => { if (st.view !== 'rad' && !pxMeta.sensors[st.sensor].change[st.view]) st.view = 'rad'; };
    const fillView = () => { fixView(); $('px-view').innerHTML = '<option value="rad">Radiância por ano</option>' + Object.entries(pxMeta.sensors[st.sensor].change).map(([w, v]) => `<option value="${w}">Mudança ${v.years[0]}–${v.years[1]}</option>`).join(''); $('px-view').value = st.view; $('px-sensor').value = st.sensor; };
    fillView();
    $('px-sensor').addEventListener('change', (e) => { stopAnim(); st.sensor = e.target.value; fillView(); clampYear(); render(); });
    $('px-view').addEventListener('change', (e) => { stopAnim(); st.view = e.target.value; clampYear(); render(); });
    window.openluxFillView = fillView;   // usado ao restaurar o estado da URL
  } else { $('px-wrap').hidden = true; }
  $('px-opacity').addEventListener('input', (e) => { st.alpha = +e.target.value; if (pxLayer && map.hasLayer(pxLayer)) pxShow(); });
  $('base-chk').addEventListener('change', (e) => { st.basemap = e.target.checked; if (st.basemap) osm.addTo(map); else map.removeLayer(osm); render(); });
  const setTheme = (v) => { if (v === 'light' || v === 'dark') document.documentElement.setAttribute('data-theme', v); else document.documentElement.removeAttribute('data-theme'); };
  try { const t = localStorage.getItem('openlux-theme'); if (t === 'light' || t === 'dark') { setTheme(t); $('theme-sel').value = t; } } catch (e) { /* sem armazenamento: segue o tema do sistema */ }
  $('theme-sel').addEventListener('change', (e) => { setTheme(e.target.value); try { localStorage.setItem('openlux-theme', e.target.value); } catch (er) { /* ignora */ } render(); });
  if (sysDark.addEventListener) sysDark.addEventListener('change', () => render());

  /* ---------- abas ---------- */
  const TABS = ['mun', 'rank', 'cmp'];
  function showTab(k) {
    TABS.forEach((t) => {
      const on = t === k;
      $('tab-' + t).setAttribute('aria-selected', on); $('tab-' + t).tabIndex = on ? 0 : -1; $('p-' + t).hidden = !on;
    });
  }
  TABS.forEach((t, i) => {
    $('tab-' + t).addEventListener('click', () => showTab(t));
    $('tab-' + t).addEventListener('keydown', (e) => {
      const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (d) { const n = TABS[(i + d + TABS.length) % TABS.length]; showTab(n); $('tab-' + n).focus(); }
    });
  });

  /* ---------- município ---------- */
  function select(cd) {
    st.sel = cd; $('mun-select').value = cd || '';
    render(); renderDetail();
    if (cd && layerByCode[cd]) map.fitBounds(layerByCode[cd].getBounds(), { maxZoom: 10, padding: [30, 30] });
  }
  const COL = ['#0072B2', '#E69F00', '#009E73', '#CC79A7'];
  const EXPORT_NOTES = ['Fonte: OpenLux 0.1.0, doi:10.5281/zenodo.24510755 · NASA Black Marble (VNP46A4, S-NPP) · malha e população: IBGE.',
    'Resultados não validados. O S-NPP tem mais ruído em áreas escuras desde 2022; não é mudança real de iluminação sem essa ressalva.'];
  const safeName = (t) => String(t).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '').toLowerCase();
  function renderDetail() {
    const box = $('mun-detail');
    if (!st.sel) { box.innerHTML = '<p class="muted">Selecione um município no mapa ou na lista.</p>'; return; }
    const m = M[st.sel], last = years.length - 1;
    const rows = winKeys.map((w) => {
      const t = m.trends[w] || {};
      return `<tr><td>${wLabel(w)}</td><td class="num">${fmt(t.slope, 3)}</td><td class="num">${fmt(t.p_value, 3)}</td><td class="num">${fmt(t.tau, 2)}</td><td class="num">${t.n_years ?? '—'}</td><td class="num">${fmt(t.change_abs, 2)}</td><td class="num">${t.change_pct == null ? '—' : fmt(t.change_pct, 1) + '%'}</td></tr>`;
    }).join('');
    const sgn = winKeys.map((w) => m.trends[w] && m.trends[w].slope).filter((v) => v != null).map(Math.sign);
    const flip = sgn.length > 1 && new Set(sgn).size > 1;
    const lowValid = m.valid.some((v) => v != null && v < 0.9);
    box.innerHTML = `<div class="profile-tools no-print">
        <button type="button" class="btn-sm" data-act="csv">Baixar dados deste município (CSV)</button>
        <button type="button" class="btn-sm" data-act="print">Imprimir perfil</button>
      </div>
      <h3 style="margin:.2rem 0">${esc(m.name)} <span class="muted small">(${st.sel})</span></h3>
      <dl class="stat">
        <dt>População (Censo 2022)</dt><dd>${m.population == null ? '—' : fmt(m.population, 0)}</dd>
        <dt>Radiância média ${years[st.iy]}</dt><dd>${fmt(m.mean[st.iy], 2)} nW·cm⁻²·sr⁻¹ <span class="badge obs">observado (agregado)</span></dd>
        <dt>Mediana ${years[st.iy]}</dt><dd>${fmt(m.median[st.iy], 2)} nW·cm⁻²·sr⁻¹</dd>
        <dt>Área válida ${years[st.iy]}</dt><dd>${m.valid[st.iy] == null ? '—' : fmt(100 * m.valid[st.iy], 1) + '%'}</dd>
        <dt>Intensidade aparente por habitante, 2022</dt><dd>${fmt(m.per_capita_mw_sr_hab, 1)} mW·sr⁻¹/hab <span class="badge der">derivado</span></dd>
      </dl>
      <div id="mun-chart"></div>
      ${m.exposure ? `<h4 style="margin:.8rem 0 .2rem">Exposição populacional e urbano × rural, ${years[st.iy]} <span class="badge der">derivado</span></h4>
      <dl class="stat">
        <dt>Radiância ponderada pela população</dt><dd>${fmt(m.exposure.pop_radiance[st.iy], 2)} nW·cm⁻²·sr⁻¹</dd>
        <dt>População em áreas iluminadas (≥ 0,5)</dt><dd>${m.exposure.pop_lit[st.iy] == null ? '—' : fmt(100 * m.exposure.pop_lit[st.iy], 1) + '%'}</dd>
        <dt>Radiância média urbana / rural</dt><dd>${fmt(m.exposure.urban[st.iy], 2)} / ${fmt(m.exposure.rural[st.iy], 2)} nW·cm⁻²·sr⁻¹</dd>
      </dl>
      <p class="muted small">População do Censo 2022 fixa em todos os anos; ponderação areal simples. Não é exposição individual.</p>` : ''}
      ${m.pixel_trend ? `<h4 style="margin:.8rem 0 .2rem">Mudança significativa por pixel <span class="badge der">derivado</span></h4>
      <div class="table-wrap"><table><thead><tr><th>Janela</th><th class="num">Aumento</th><th class="num">Redução</th><th class="num">Pixels testados</th></tr></thead><tbody>${winKeys.map((w) => { const t = m.pixel_trend[w] || {}; return `<tr><td>${wLabel(w)}</td><td class="num">${t.up == null ? '—' : fmt(100 * t.up, 1) + '%'}</td><td class="num">${t.down == null ? '—' : fmt(100 * t.down, 1) + '%'}</td><td class="num">${t.n_px == null ? '—' : fmt(t.n_px, 0)}</td></tr>`; }).join('')}</tbody></table></div>
      <p class="muted small">Participação dos pixels iluminados (mediana ≥ 0,5) com tendência significativa (FDR 5%). Janelas com 2022–2025 herdam o ruído do S-NPP.</p>` : ''}
      ${m.sensors ? `<h4 style="margin:.8rem 0 .2rem">Comparação entre sensores, 2018–2025 <span class="badge der">derivado</span></h4>
      <div class="table-wrap"><table><thead><tr><th>Sensor</th><th class="num">Inclin. (nW·cm⁻²·sr⁻¹/ano)</th><th class="num">p</th><th class="num">Δ 2021→2025</th></tr></thead><tbody>
      <tr><td>S-NPP</td><td class="num">${fmt(m.sensors.slope_snpp, 3)}</td><td class="num">${fmt(m.sensors.p_snpp, 3)}</td><td class="num">${fmt(m.sensors.change_snpp, 2)}</td></tr>
      <tr><td>NOAA-20</td><td class="num">${fmt(m.sensors.slope_noaa20, 3)}</td><td class="num">${fmt(m.sensors.p_noaa20, 3)}</td><td class="num">${fmt(m.sensors.change_noaa20, 2)}</td></tr></tbody></table></div>
      <p class="muted small">Razão média NOAA-20/S-NPP no período: ${fmt(m.sensors.ratio_noaa20_over_snpp, 3)}.</p>` : ''}
      <h4 style="margin:.8rem 0 .2rem">Tendência e variação <span class="badge der">derivado</span></h4>
      <div class="table-wrap"><table><thead><tr><th>Janela</th><th class="num">Inclin. (nW·cm⁻²·sr⁻¹/ano)</th><th class="num">p</th><th class="num">τ</th><th class="num">Anos</th><th class="num">Δ abs.</th><th class="num">Δ %</th></tr></thead><tbody>${rows}</tbody></table></div>
      ${flip ? '<p class="note">O sinal da tendência muda entre as janelas: a variação em 2022–2025 pesa sobre o resultado (ver aviso e Limitações).</p>' : ''}
      ${lowValid ? '<p class="note">Parte da área deste município não entra no cálculo (água excluída pela máscara terra/água do produto: mar ou lagoa).</p>' : ''}
      <p class="muted small">Δ % só é definido quando a radiância inicial ≥ piso declarado.</p>`;
    OpenLuxCharts.lineChart($('mun-chart'), {
      title: `Radiância média anual, ${m.name}`, years, yLabel: 'nW·cm⁻²·sr⁻¹', digits: 2,
      shadeFrom: 2022, shadeLabel: 'ruído S-NPP',
      series: [{ name: m.name, values: m.mean, color: COL[0] }, { name: 'Estado (média ponderada)', values: data.state.mean, color: '#7a828c', dash: '5 4', width: 1.6 }],
      exportName: 'grafico-' + safeName(m.name) + '-radiancia-media', exportNotes: EXPORT_NOTES,
    });
    box.insertAdjacentHTML('beforeend', `<p class="print-only small">Perfil gerado pelo OpenLux 0.1.0 (doi:10.5281/zenodo.24510755). Fonte: NASA Black Marble (VNP46A4, S-NPP); malha e população do IBGE. Resultados não validados; o S-NPP tem ruído em áreas escuras desde 2022.</p>`);
  }

  function downloadProfileCsv() {
    const m = M[st.sel]; if (!m) return;
    const cols = ['cod_municipio', 'municipio', 'ano', 'radiancia_media_nW_cm-2_sr-1', 'radiancia_mediana_nW_cm-2_sr-1',
      'fracao_area_valida', 'fracao_area_iluminada_limiar_0.5_nW_cm-2_sr-1', 'intensidade_radiante_aparente_nW_sr-1'];
    const v = (a, i) => (a && a[i] != null ? a[i] : '');
    const rows = years.map((y, i) => [st.sel, m.name, y, v(m.mean, i), v(m.median, i), v(m.valid, i), v(m.lit, i), v(m.intensity_nw_sr, i)].map((x) => `"${String(x).replace(/"/g, '""')}"`).join(','));
    const blob = new Blob(['\uFEFF' + cols.join(',') + '\n' + rows.join('\n') + '\n'], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'openlux-' + safeName(m.name) + '-serie-snpp.csv';
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  $('mun-detail').addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]'); if (!b) return;
    if (b.dataset.act === 'csv') downloadProfileCsv();
    if (b.dataset.act === 'print') {
      document.body.classList.add('print-profile');
      window.addEventListener('afterprint', () => document.body.classList.remove('print-profile'), { once: true });
      window.print();
    }
  });

  /* ---------- ranking ---------- */
  let rankDesc = true;
  $('rank-dir').addEventListener('click', () => { rankDesc = !rankDesc; $('rank-dir').textContent = 'Ordem: ' + (rankDesc ? 'decrescente' : 'crescente'); renderRank(); });
  $('rank-filter').addEventListener('input', renderRank);
  function renderRank() {
    const ind = IND[st.ind], f = norm($('rank-filter').value || '');
    const rows = codes.map((c) => ({ c, v: val(c) }));
    rows.sort((a, b) => (a.v == null) - (b.v == null) || (rankDesc ? b.v - a.v : a.v - b.v));
    rows.forEach((r, i) => { r.rank = r.v == null ? null : i + 1; });
    $('rank-note').textContent = `${ind.label} — ${ind.period(ind.yearly ? years[st.iy] : null)} (${ind.unit}).`;
    $('rank-table').querySelector('thead').innerHTML = '<tr><th class="num">#</th><th>Município</th><th class="num">Valor</th><th>Classe</th></tr>';
    $('rank-table').querySelector('tbody').innerHTML = rows.filter((r) => norm(M[r.c].name).includes(f)).map((r) =>
      `<tr><td class="num">${r.rank ?? '—'}</td><td><button type="button" class="rowbtn" data-c="${r.c}">${esc(M[r.c].name)}</button></td><td class="num">${fmt(r.v, ind.d)}</td><td>${r.v == null ? 'sem dado' : esc(className(ind, classOf(r.v, ind.breaks)))}</td></tr>`).join('');
  }
  $('rank-table').addEventListener('click', (e) => { const b = e.target.closest('.rowbtn'); if (b) { showTab('mun'); select(b.dataset.c); } });

  /* ---------- comparação ---------- */
  ['cmp1', 'cmp2', 'cmp3'].forEach((id, i) => { $(id).innerHTML = optionsHtml(true); $(id).addEventListener('change', renderCmp); });
  const byPop = codes.slice().sort((a, b) => (M[b].population || 0) - (M[a].population || 0));  // padrão neutro: os dois mais populosos
  $('cmp1').value = byPop[0]; $('cmp2').value = byPop[1];
  function renderCmp() {
    const sel = ['cmp1', 'cmp2', 'cmp3'].map((i) => $(i).value).filter(Boolean);
    const series = sel.map((c, i) => ({ name: M[c].name, values: M[c].mean, color: COL[i] }));
    series.push({ name: 'Estado (média ponderada)', values: data.state.mean, color: '#7a828c', dash: '5 4', width: 1.6 });
    OpenLuxCharts.lineChart($('cmp-chart'), { title: 'Radiância média anual: comparação (' + sel.map((c) => M[c].name).join(', ') + ')', years, yLabel: 'nW·cm⁻²·sr⁻¹', digits: 2, shadeFrom: 2022, shadeLabel: 'ruído S-NPP', series,
      exportName: 'grafico-comparacao-radiancia-media', exportNotes: EXPORT_NOTES });
  }

  $('px-chk').addEventListener('change', (e) => { st.pxOn = e.target.checked; render(); });
  $('outline-chk').addEventListener('change', (e) => { st.outlines = e.target.checked; render(); });

  /* ---------- animação da evolução ano a ano (a pedido do visitante; nunca inicia sozinha) ---------- */
  let animTimer = null;
  const frameYears = () => (st.layer === 'pixel' ? sensorYears(st.sensor).sort((a, b) => a - b) : years);
  function stopAnim() {
    if (animTimer) clearTimeout(animTimer);
    animTimer = null; st.playing = false;
    $('play-btn').textContent = '▶ Animar'; $('play-btn').setAttribute('aria-pressed', 'false');
    if ($('anim-status').textContent === 'Carregando os anos…') $('anim-status').textContent = '';
  }
  function showFrame(y) { st.iy = years.indexOf(y); yr.value = st.iy; yrOut(); render(); if (st.sel) renderDetail(); }
  function stepAnim() {
    const ys = frameYears(), cur = ys.indexOf(years[st.iy]); let nxt = cur + 1;
    if (nxt >= ys.length) { if (!$('loop-chk').checked) { stopAnim(); $('anim-status').textContent = 'Fim da série.'; return; } nxt = 0; }
    showFrame(ys[nxt]);
    animTimer = setTimeout(stepAnim, +$('speed-sel').value);
  }
  async function startAnim() {
    if ($('play-btn').disabled) return;
    st.playing = true; $('play-btn').textContent = '⏸ Pausar'; $('play-btn').setAttribute('aria-pressed', 'true'); $('anim-status').textContent = '';
    if (st.layer === 'pixel') {      // pré-carrega todos os anos do sensor para a animação não piscar
      $('anim-status').textContent = 'Carregando os anos…';
      try { await Promise.all(sensorYears(st.sensor).map((y) => pxGrid(`${st.sensor}/${y}`))); }
      catch (e) { stopAnim(); $('anim-status').textContent = 'Não foi possível carregar todos os anos.'; return; }
      if (!st.playing) return;       // o visitante parou ou mexeu nos controles enquanto carregava
      $('anim-status').textContent = '';
    }
    const ys = frameYears(); if (years[st.iy] === ys[ys.length - 1]) showFrame(ys[0]);   // no último ano, recomeça do primeiro
    animTimer = setTimeout(stepAnim, +$('speed-sel').value);
  }
  $('play-btn').addEventListener('click', () => { if (st.playing) { stopAnim(); } else { startAnim(); } });
  document.addEventListener('visibilitychange', () => { if (document.hidden && st.playing) stopAnim(); });

  /* ---------- nomes dos municípios (contexto geográfico próprio, sem mapa-base de terceiros) ---------- */
  const labelLayer = L.layerGroup();
  codes.forEach((cd) => { const c = layerByCode[cd].getBounds().getCenter();   // centro do retângulo envolvente: aproximado em formas irregulares
    labelLayer.addLayer(L.marker(c, { icon: L.divIcon({ className: 'mlabel', html: `<span>${esc(M[cd].name)}</span>`, iconSize: [0, 0] }), interactive: false, keyboard: false })); });
  const LABEL_ZOOM = 9.5;
  function syncLabels() { const on = $('labels-chk').checked && map.getZoom() >= LABEL_ZOOM;
    if (on && !map.hasLayer(labelLayer)) labelLayer.addTo(map); else if (!on && map.hasLayer(labelLayer)) map.removeLayer(labelLayer); }
  $('labels-chk').addEventListener('change', syncLabels);

  /* ---------- busca de município (só nos nossos dados, sem serviço externo) ---------- */
  $('mun-list').innerHTML = codes.map((c) => `<option value="${esc(M[c].name)}"></option>`).join('');
  function searchMun() {
    const q = norm($('mun-search').value.trim()); if (!q) return;
    const hit = codes.find((c) => norm(M[c].name) === q) || codes.find((c) => norm(M[c].name).startsWith(q)) || codes.find((c) => norm(M[c].name).includes(q));
    if (hit) { showTab('mun'); select(hit); $('mun-search').value = M[hit].name; }
  }
  $('mun-search').addEventListener('change', searchMun);
  $('mun-search').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); searchMun(); } });

  /* ---------- link permanente: lat, lng, z, ano, camada, indicador e município na URL ---------- */
  const mapBounds = gl.getBounds().pad(0.5);
  function readUrl() {
    const P = new URLSearchParams(location.search), num = (k) => { const v = P.get(k); return v !== null && v.trim() !== '' && isFinite(+v) ? +v : null; };
    const y = num('y'); if (y != null && years.includes(y)) { st.iy = years.indexOf(y); yr.value = st.iy; yrOut(); }
    const l = P.get('l'); if ((l === 'pixel' && pxLayer) || l === 'mun') st.layer = l;
    const i = P.get('i'); if (i && Object.prototype.hasOwnProperty.call(IND, i)) { st.ind = i; $('indicator').value = i; }
    const m = P.get('m'); if (m && Object.prototype.hasOwnProperty.call(M, m)) { st.sel = m; $('mun-select').value = m; }
    document.querySelectorAll('input[name="layer"]').forEach((r) => { r.checked = r.value === st.layer; });
    const sn = P.get('s'); if (pxMeta && sn && Object.prototype.hasOwnProperty.call(pxMeta.sensors, sn)) st.sensor = sn;
    const vw = P.get('v'); if (pxMeta && vw && (vw === 'rad' || Object.prototype.hasOwnProperty.call(pxMeta.sensors[st.sensor].change, vw))) st.view = vw;
    if (pxMeta) { window.openluxFillView(); if (st.layer === 'pixel' && st.view === 'rad') clampYear(); }
    const lat = num('lat'), lng = num('lng'), z = num('z');
    if (lat != null && lng != null && z != null && z >= 6 && z <= 12 && mapBounds.contains([lat, lng])) map.setView([lat, lng], z);
    else if (st.sel) map.fitBounds(layerByCode[st.sel].getBounds(), { maxZoom: 10, padding: [30, 30] });
  }
  function writeUrl() {
    const c = map.getCenter(), q = new URLSearchParams({ lat: c.lat.toFixed(4), lng: c.lng.toFixed(4), z: String(map.getZoom()), y: String(years[st.iy]), l: st.layer, i: st.ind, s: st.sensor, v: st.view });
    if (st.sel) q.set('m', st.sel);
    try { history.replaceState(null, '', '?' + q.toString()); } catch (e) { /* ambientes sem history: o link só não é atualizado */ }
  }
  readUrl();
  map.on('moveend', writeUrl);
  map.on('zoomend', syncLabels);
  $('link-btn').addEventListener('click', async () => {
    writeUrl();
    try { await navigator.clipboard.writeText(location.href); $('link-status').textContent = 'Link copiado.'; }
    catch (e) { $('link-status').textContent = 'Não foi possível copiar automaticamente: copie o endereço da barra do navegador (ele já contém esta vista).'; }
  });

  render(); renderCmp();
  if (st.sel) renderDetail();
  syncLabels(); writeUrl();
  /* Ponte para o módulo "Desenhe uma área" (js/desenhar.js): só leitura da grade e do estado atual. */
  window.OpenLuxMapApi = {
    map: map,
    years: years,
    pxMeta: pxMeta,
    viewIsRadiance: () => st.view === 'rad',
    currentPath: () => (pxMeta ? pxPath() : null),
    currentSensor: () => (pxMeta ? st.sensor : null),
    currentYear: () => years[st.iy],
    getGrid: (path) => pxGrid(path),
  };
  document.dispatchEvent(new Event('openlux:mapa-pronto'));
})();
