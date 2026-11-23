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

  const st = { ind: 'mean', iy: years.length - 1, sel: null, layer: pxMeta ? 'pixel' : 'mun' };
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
  const PXPAL = ['#f2f2f2', '#ffeda0', '#fec44f', '#fd8d3c', '#e31a1c', '#800026'];  // < 0,5 neutro; depois amarelo → vinho
  const hex2rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const pxCache = {};
  function pxGrid(year) {
    if (!pxCache[year]) {
      const g = pxMeta.grid;
      pxCache[year] = fetch(`data/pixels/${year}.bin`).then((r) => { if (!r.ok) throw new Error(r.status); return r.arrayBuffer(); })
        .then((b) => { const a = new Uint8Array(b); if (a.length !== g.rows * g.cols) throw new Error('grade com tamanho inesperado'); return a; });
    }
    return pxCache[year];
  }
  const pxCell = (ll) => { const g = pxMeta.grid; // índice (linha, coluna) da grade lat/lon; null fora da janela
    const c = Math.floor((ll.lng - g.lon_west) / g.pixel_deg), r = Math.floor((g.lat_north - ll.lat) / g.pixel_deg);
    return r < 0 || c < 0 || r >= g.rows || c >= g.cols ? null : [r, c]; };
  const PixelLayer = L.Layer.extend({
    onAdd(m) {
      this._map = m; this._cv = L.DomUtil.create('canvas', 'openlux-pixels leaflet-zoom-hide');
      m.getPane('tilePane').appendChild(this._cv);
      m.on('moveend zoomend resize', this.redraw, this); this.redraw();
    },
    onRemove(m) { m.off('moveend zoomend resize', this.redraw, this); this._cv.remove(); },
    setGrid(a) { this._grid = a; this.redraw(); },
    redraw() {
      const m = this._map, cv = this._cv; if (!m || !cv) return;
      const sz = m.getSize(), g = pxMeta.grid; cv.width = sz.x; cv.height = sz.y;
      L.DomUtil.setPosition(cv, m.containerPointToLayerPoint([0, 0]));
      if (!this._grid) return;
      const ctx = cv.getContext('2d'), img = ctx.createImageData(sz.x, sz.y), d = img.data;
      const cols = new Int32Array(sz.x), rows = new Int32Array(sz.y);
      for (let x = 0; x < sz.x; x++) { const c = Math.floor((m.containerPointToLatLng([x, 0]).lng - g.lon_west) / g.pixel_deg); cols[x] = c < 0 || c >= g.cols ? -1 : c; }
      for (let y = 0; y < sz.y; y++) { const r = Math.floor((g.lat_north - m.containerPointToLatLng([0, y]).lat) / g.pixel_deg); rows[y] = r < 0 || r >= g.rows ? -1 : r; }
      const rgb = PXPAL.map(hex2rgb), nod = hex2rgb(NODATA);
      for (let y = 0; y < sz.y; y++) { if (rows[y] < 0) continue; const base = rows[y] * g.cols;
        for (let x = 0; x < sz.x; x++) { if (cols[x] < 0) continue;
          const code = this._grid[base + cols[x]]; if (code === 0) continue;
          const col = code === 1 ? nod : rgb[code - pxMeta.classes.first_code]; const i = (y * sz.x + x) * 4;
          d[i] = col[0]; d[i + 1] = col[1]; d[i + 2] = col[2]; d[i + 3] = 235; } }
      ctx.putImageData(img, 0, 0);
    },
  });
  const pxLayer = pxMeta ? new PixelLayer() : null;
  let pxLoaded = null;  // ano da grade atualmente desenhada
  async function pxShow() {
    const y = years[st.iy]; if (pxLoaded === y) return;
    try { const a = await pxGrid(y); if (years[st.iy] === y && st.layer === 'pixel') { pxLayer.setGrid(a); pxLoaded = y; } }
    catch (e) { $('pixel-readout').hidden = false; $('pixel-readout').textContent = 'Não foi possível carregar a camada de pixel deste ano.'; }
  }
  const pxShare = (a, code) => { let n = 0, t = 0; for (let i = 0; i < a.length; i++) { if (a[i] >= 2) { t++; if (a[i] === code) n++; } } return t ? n / t : NaN; };
  async function pxNote(y) {
    if (y < 2022) return '';
    try { const [a, b] = await Promise.all([pxGrid(2021), pxGrid(y)]);
      return `<div class="pxnote"><strong>Atenção (S-NPP, ${y}):</strong> a partir de 2022 o sensor tem um piso de ruído mais alto em áreas escuras. A parcela dos pixels com valor na classe ${esc(pxMeta.classes.labels[1])} passou de ${fmt(100 * pxShare(a, 3), 1)}% em 2021 para ${fmt(100 * pxShare(b, 3), 1)}% em ${y}, e a da classe ${esc(pxMeta.classes.labels[0])} caiu de ${fmt(100 * pxShare(a, 2), 1)}% para ${fmt(100 * pxShare(b, 2), 1)}%. Parte dessa mudança pode ser ruído, não luz nova (ver o aviso acima).</div>`;
    } catch (e) { return ''; }
  }
  async function renderPixelLegend() {
    const y = years[st.iy], c = pxMeta.classes;
    const items = c.labels.map((l, k) => `<li><span class="sw" style="background:${PXPAL[k]}"></span>${esc(l)}</li>`).join('') + `<li><span class="sw" style="background:${NODATA}"></span>sem dado válido (água, qualidade)</li>`;
    $('legend').innerHTML = `<h3>Radiância noturna por pixel <span class="badge obs">Observado</span><span class="badge cls">Classes fixas</span></h3>
      <div><strong>Unidade:</strong> nW·cm⁻²·sr⁻¹ · <strong>Período:</strong> ano ${y}</div><ul>${items}</ul>
      <div class="small"><strong>Como ler:</strong> cada quadradinho tem cerca de 460 m. Cores mais escuras = mais luz emitida para cima, vista pelo satélite à noite. <strong>Isto não é o brilho do céu</strong> que uma pessoa enxerga do chão.</div>
      <div class="small"><strong>Classificação:</strong> limites fixos (0,5; 2; 8; 30; 100), iguais em todos os anos; 0,5 é o valor abaixo do qual o produto zera a radiância. Intervalos fechados à esquerda: [a, b). A grade mostra a classe, não o valor.</div>
      <div class="small muted"><strong>Fonte:</strong> NASA Black Marble VNP46A4 v2.0 (Suomi NPP), camada AllAngle_Composite_Snow_Free, qualidade 0, apenas terra; pixels do estado (malha IBGE 2024).</div><div id="pxnote"></div>`;
    const n = await pxNote(y); if (years[st.iy] === y && $('pxnote')) $('pxnote').innerHTML = n;
  }
  function pxReadout(ll) {
    const box = $('pixel-readout'); if (st.layer !== 'pixel' || !pxLayer._grid) return;
    const cell = pxCell(ll); box.hidden = false;
    if (!cell) { box.textContent = 'Passe o cursor sobre o mapa (ou toque) para ver a classe do pixel.'; return; }
    const code = pxLayer._grid[cell[0] * pxMeta.grid.cols + cell[1]], f = pxMeta.classes.first_code;
    const what = code === 0 ? 'fora do estado' : code === 1 ? 'sem dado válido' : `${pxMeta.classes.labels[code - f]} nW·cm⁻²·sr⁻¹`;
    box.textContent = `Pixel (${fmt(ll.lat, 3)}°, ${fmt(ll.lng, 3)}°), ano ${years[st.iy]}: ${what}. Mostra a classe, não o valor.`;
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
    $('year-wrap').hidden = !(px || ind.yearly);
    $('year-note').hidden = !(px || ind.yearly);
    $('indicator').disabled = px;
    if (pxLayer) { if (px) { if (!map.hasLayer(pxLayer)) pxLayer.addTo(map); pxShow(); } else if (map.hasLayer(pxLayer)) { map.removeLayer(pxLayer); pxLoaded = null; } }
    $('pixel-readout').hidden = !px;
    if (px) $('pixel-readout').textContent = 'Passe o cursor sobre o mapa (ou toque) para ver a classe do pixel.';
    gl.eachLayer((layer) => {
      const cd = layer.feature.properties.CD_MUN, sel = cd === st.sel;
      if (px) {
        layer.setStyle({ fillOpacity: 0, weight: sel ? 3.2 : 0.8, color: sel ? '#0b5fff' : '#3b3b3b', opacity: sel ? 1 : 0.7 });
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
  $('indicator').addEventListener('change', (e) => { st.ind = e.target.value; render(); });
  yr.addEventListener('input', (e) => { st.iy = +e.target.value; yrOut(); render(); if (st.sel) renderDetail(); });
  const optionsHtml = (blank) => (blank ? '<option value="">— nenhum —</option>' : '') + codes.map((c) => `<option value="${c}">${esc(M[c].name)}</option>`).join('');
  $('mun-select').innerHTML = '<option value="">Selecione…</option>' + optionsHtml(false);
  $('mun-select').addEventListener('change', (e) => select(e.target.value || null));
  if (!pxLayer) $('layer-wrap').hidden = true;
  document.querySelectorAll('input[name="layer"]').forEach((r) => { r.checked = r.value === st.layer; r.addEventListener('change', (e) => { if (e.target.checked) { st.layer = e.target.value; render(); } }); });
  $('reset-btn').addEventListener('click', () => map.fitBounds(gl.getBounds(), { padding: [8, 8] }));

  /* ---------- abas ---------- */
  const TABS = ['mun', 'rank', 'cmp', 'state'];
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
    box.innerHTML = `<h3 style="margin:.2rem 0">${esc(m.name)} <span class="muted small">(${st.sel})</span></h3>
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
    });
  }

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
    OpenLuxCharts.lineChart($('cmp-chart'), { title: 'Radiância média anual: comparação', years, yLabel: 'nW·cm⁻²·sr⁻¹', digits: 2, shadeFrom: 2022, shadeLabel: 'ruído S-NPP', series });
  }

  /* ---------- estado ---------- */
  function renderState() {
    const cnt = winKeys.map((w) => {
      const t = codes.map((c) => M[c].trends[w]).filter((x) => x && x.slope != null);
      return `<tr><td>${wLabel(w)}</td><td class="num">${t.filter((x) => x.slope > 0).length}</td><td class="num">${t.filter((x) => x.slope < 0).length}</td><td class="num">${t.filter((x) => x.p_value < 0.05).length}</td></tr>`;
    }).join('');
    const sc = data.sensor_comparison, scRows = sc.years.map((y) => `<tr><td>${y}</td><td class="num">${fmt(sc.state_mean_a[y], 2)}</td><td class="num">${fmt(sc.state_mean_b[y], 2)}</td><td class="num">${fmt(sc.ratio_b_over_a[y], 3)}</td></tr>`).join('');
    const sens = Object.entries(data.sensitivity).map(([w, cfgs]) => Object.entries(cfgs).map(([c, v]) =>
      `<tr><td>${esc(w.replace('_', '–'))}</td><td>${esc(c)}</td><td class="num">${fmt(v.spearman_mean_end_year, 3)}</td><td class="num">${fmt(v.spearman_trend_slope, 3)}</td><td class="num">${fmt(v.trend_sign_agreement, 3)}</td></tr>`).join('')).join('');
    $('state-content').innerHTML = `
      <h3 style="margin:.2rem 0">Estado do Rio de Janeiro</h3>
      <div id="state-chart"></div>
      <p class="muted small">Média da radiância por município ponderada pela área válida de pixels. Série derivada de dados observados.</p>
      <h4>Controle de ruído de fundo (pixels persistentemente escuros)</h4>
      <div id="qa-chart"></div>
      <p class="muted small">Pixels com mediana zero em 2012–2021 (classe definida só por esses anos). Se a radiância média desses pixels sobe, o piso de ruído mudou. Isso não é crescimento de iluminação.</p>
      <h4>Fração da área iluminada (≥ limiar documentado): S-NPP × NOAA-20</h4>
      <div id="lit-chart"></div>
      <p class="muted small">Média estadual ponderada pela área válida. O limiar coincide com o valor em que o produto zera ruído de fundo, por isso o aumento do piso de ruído do S-NPP eleva esta fração.</p>
      ${data.sensor_municipal ? (() => { const sm = data.sensor_municipal, L = sm.levels_by_year, rows = Object.keys(L).map((y) => `<tr><td>${y}</td><td class="num">${fmt(L[y].spearman, 4)}</td><td class="num">${fmt(L[y].median_ratio_b_over_a, 3)}</td><td class="num">${fmt(L[y].median_abs_diff, 3)}</td></tr>`).join(''); const w = sm['2018_2025'], p = sm['2018_2021'];
        return `<h4>Comparação municipal entre sensores (92 municípios)</h4><div class="table-wrap"><table><thead><tr><th>Ano</th><th class="num">ρ (níveis)</th><th class="num">NOAA-20 / S-NPP</th><th class="num">|S-NPP − NOAA-20|</th></tr></thead><tbody>${rows}</tbody></table></div>
        <p class="small">Inclinações 2018–2021: ρ ${fmt(p.spearman_slopes, 2)}, mesmo sinal em ${fmt(100 * p.sign_agreement, 1)} %. Inclinações 2018–2025: ρ ${fmt(w.spearman_slopes, 2)}, mesmo sinal em ${fmt(100 * w.sign_agreement, 1)} %. Variação 2021→2025 (mediana): S-NPP ${fmt(w.median_change_a, 2)} e NOAA-20 ${fmt(w.median_change_b, 2)} nW·cm⁻²·sr⁻¹.</p>
        <p class="muted small">Até 2021 os sensores concordam em nível; a partir de 2022 o S-NPP lê mais alto. Ver docs/DECISIONS.md (seção 8).</p>`; })() : ''}
      <h4>Municípios por sinal da tendência</h4>
      <div class="table-wrap"><table><thead><tr><th>Janela</th><th class="num">Inclin. &gt; 0</th><th class="num">Inclin. &lt; 0</th><th class="num">p &lt; 0,05</th></tr></thead><tbody>${cnt}</tbody></table></div>
      <h4>Comparação entre sensores (média estadual, nW·cm⁻²·sr⁻¹)</h4>
      <div class="table-wrap"><table><thead><tr><th>Ano</th><th class="num">S-NPP</th><th class="num">NOAA-20</th><th class="num">NOAA-20 / S-NPP</th></tr></thead><tbody>${scRows}</tbody></table></div>
      <p class="small">Concordância das inclinações municipais entre sensores (${sc.years[0]}–${sc.years.at(-1)}): Spearman ${fmt(sc.spearman_trend_slope, 2)}; mesmo sinal em ${fmt(100 * sc.trend_sign_agreement, 1)}% dos municípios.</p>
      <h4>Sensibilidade à configuração (em relação à principal)</h4>
      <div class="table-wrap"><table><thead><tr><th>Janela</th><th>Variação</th><th class="num">ρ média (ano final)</th><th class="num">ρ inclinação</th><th class="num">Mesmo sinal</th></tr></thead><tbody>${sens}</tbody></table></div>`;
    OpenLuxCharts.lineChart($('state-chart'), { title: 'Radiância média estadual', years, yLabel: 'nW·cm⁻²·sr⁻¹', digits: 2, shadeFrom: 2022, shadeLabel: 'ruído S-NPP', series: [{ name: 'Estado (média ponderada)', values: data.state.mean, color: COL[0] }] });
    if (sc.state_lit_fraction_a) OpenLuxCharts.lineChart($('lit-chart'), { title: 'Fração da área iluminada, média estadual', years: sc.years, yLabel: 'fração', digits: 3, shadeFrom: 2022, shadeLabel: 'ruído S-NPP', zeroBase: true,
      series: [{ name: 'S-NPP', values: sc.years.map((y) => sc.state_lit_fraction_a[y]), color: COL[0] }, { name: 'NOAA-20', values: sc.years.map((y) => sc.state_lit_fraction_b[y]), color: COL[1] }] });
    OpenLuxCharts.lineChart($('qa-chart'), { title: 'Radiância média de pixels persistentemente escuros', years: data.qa.map((r) => r.year), yLabel: 'nW·cm⁻²·sr⁻¹', digits: 3, shadeFrom: 2022, shadeLabel: 'após 2021', zeroBase: true,
      series: [{ name: 'Terra', values: data.qa.map((r) => r.dark_land_mean), color: COL[1] }, { name: 'Mar', values: data.qa.map((r) => r.dark_sea_mean), color: COL[0] }] });
  }

  /* ---------- informações científicas ---------- */
  function renderInfo() {
    const lowValid = codes.filter((c) => M[c].valid.some((v) => v != null && v < 0.9)).map((c) => M[c].name);
    const src = meta.sources.map((s) => `<tr><td><a href="${esc(s.url)}" rel="noopener">${esc(s.name)}</a>${s.doi ? `<br><span class="small">DOI: <a href="https://doi.org/${esc(s.doi)}" rel="noopener">${esc(s.doi)}</a></span>` : ''}</td><td>${esc(s.institution)}</td><td>${esc(s.version)}</td><td>${esc(s.license)} <strong>[${({ confirmado: 'confirmado', confirmado_com_ressalva: 'confirmado com ressalva', nao_confirmado: 'não confirmado' })[s.license_status]}]</strong></td></tr>`).join('');
    const docs = meta.documents.map((d) => `<li><a href="${esc(d.url)}" rel="noopener">${esc(d.name)}</a> (${esc(d.institution)})</li>`).join('');
    const refs = meta.references.map((r) => `<li>${esc(r.cite)} <a href="https://doi.org/${esc(r.doi)}" rel="noopener">doi:${esc(r.doi)}</a></li>`).join('');
    const hashes = Object.entries(meta.run.output_sha256).map(([k, v]) => `<tr><td>${esc(k)}</td><td><code>${esc(v)}</code></td></tr>`).join('');
    $('info-content').innerHTML = `
      <details open><summary>Metodologia (resumo)</summary>
        <p>Produto: NASA Black Marble VNP46A4 v2.0 (radiância noturna anual, grade de 15 arc-s ≈ 460 m), camada <code>AllAngle_Composite_Snow_Free</code>. São mantidos pixels de qualidade 0 (boa), sobre terra (códigos 0, 1 e 5 da máscara terra/água), sem valores de preenchimento ou negativos. Não há reamostragem.</p>
        <p><strong>Radiância média</strong> do município: L̄ = Σ wᵢ·Lᵢ / Σ wᵢ, onde wᵢ é a fração da área do pixel coberta pelo município (cobertura fracionária) e Lᵢ é a radiância (nW·cm⁻²·sr⁻¹) dos pixels válidos. A mediana é ponderada pelos mesmos pesos.</p>
        <p><strong>Intensidade radiante aparente</strong>: S = Σ wᵢ·Lᵢ·Aᵢ (nW·sr⁻¹), com Aᵢ a área elipsoidal (WGS84) do pixel. É uma intensidade na direção observada pelo sensor, <em>não</em> a emissão luminosa total do município. A soma bruta de pixels não é usada.</p>
        <p><strong>Fração da área iluminada</strong>: F(τ) = Σ wᵢ·[Lᵢ ≥ τ] / Σ wᵢ sobre os pixels válidos, com τ = ${fmt((meta.thresholds_nw_cm2_sr || {}).lit_0p5, 1)} nW·cm⁻²·sr⁻¹ (valor abaixo do qual o produto zera ruído de fundo; guia do usuário, seção 2.3). Limiares analíticos adicionais (quantis da radiância dos pixels iluminados no ano de referência) constam em <code>run_record.json</code>.</p>
        <p><strong>Por habitante</strong>: S / população residente (Censo 2022), somente para 2022, em mW·sr⁻¹ por habitante; é um índice relativo.</p>
        <p><strong>Tendência</strong>: inclinação de Theil–Sen e teste de Kendall sobre a radiância média anual, com mínimo de 8 anos válidos, em duas janelas (${winKeys.map(wLabel).join(' e ')}). <strong>Variação percentual</strong>: definida só com linha de base ≥ piso (${winKeys.map((w) => `${wLabel(w)}: ${fmt(meta.change_floor_nw_cm2_sr[w], 2)}`).join('; ')} nW·cm⁻²·sr⁻¹; percentil 25 das médias municipais).</p>
        <p><strong>Classes de cor</strong> são classificações analíticas (quantis ou limites em torno de zero), não limiares físicos nem categorias oficiais de poluição luminosa.</p>
        <p>Análise de sensibilidade: qualidade 0+1, camada near-nadir, e mínimo de 5 e 10 observações (aba Estado). Detalhes das decisões: <code>docs/DECISIONS.md</code> no repositório.</p>
      </details>
      <details><summary>Fontes de dados</summary>
        <div class="table-wrap"><table><thead><tr><th>Fonte</th><th>Instituição</th><th>Versão / cobertura</th><th>Licença / termos</th></tr></thead><tbody>${src}</tbody></table></div>
        <p class="small">Documentação técnica:</p><ul class="small">${docs}</ul>
      </details>
      <details><summary>Referências</summary><ul>${refs}</ul><p class="small muted">Lista restrita a trabalhos com DOI verificado em fontes institucionais ou nas buscas desta pesquisa.</p></details>
      <details open><summary>Limitações</summary><ul>
        <li><strong>Estimativa, não medição:</strong> a radiância orbital (VIIRS Day/Night Band) não equivale ao brilho do céu observado na superfície; não há medições fotométricas de campo.</li>
        <li><strong>Resolução:</strong> pixel de ~460 m; municípios pequenos têm poucas centenas de pixels.</li>
        <li><strong>Sensibilidade espectral:</strong> a banda DNB é pouco sensível à emissão azul de LEDs, o que pode subestimar áreas convertidas para LED (Levin et al., 2020).</li>
        <li><strong>Piso de ruído do S-NPP a partir de 2022</strong> (aviso no topo) e <strong>componente comum aos dois sensores</strong> não separado de um possível artefato do algoritmo compartilhado. A saturação em áreas muito iluminadas não foi avaliada neste trabalho.</li>
        <li><strong>Janela de tendência:</strong> o sinal depende da janela (${winKeys.map(wLabel).join(' vs ')}).</li>
        <li><strong>Máscara de água:</strong> mar e lagoas são excluídos; municípios com menos de 90% de área válida em algum ano: ${esc(lowValid.join(', ') || 'nenhum')}.</li>
        <li><strong>População:</strong> população residente não é população exposta; a intensidade por habitante é um índice relativo, só para 2022.</li>
        <li><strong>Malha:</strong> a malha SIRGAS 2000 foi tratada como WGS84 (diferença de poucos metros, menor que o pixel); a geometria exibida foi simplificada só para visualização, e os cálculos usaram a geometria completa.</li>
        <li><strong>Cartografia:</strong> projeção de exibição Web Mercator; a barra de escala é aproximada para a latitude do estado.</li>
      </ul></details>
      <details><summary>Proveniência desta execução</summary>
        <p class="small">Processado em ${esc(meta.run.processed_utc)} · commit do código: <code>${esc((meta.run.code_commit || '').slice(0, 12))}</code>${meta.run.code_dirty ? ' (com alterações não commitadas)' : ''}.</p>
        <div class="table-wrap"><table><thead><tr><th>Arquivo de saída</th><th>SHA-256</th></tr></thead><tbody>${hashes}</tbody></table></div>
      </details>`;
    const d = new Date(meta.run.processed_utc);
    $('updated').textContent = `Última atualização dos dados: ${d.toLocaleDateString('pt-BR', { timeZone: 'UTC', day: '2-digit', month: 'long', year: 'numeric' })} (UTC). Dados não validados.`;
  }

  render(); renderCmp(); renderState(); renderInfo();
})();
