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

  let data, geo;
  try {
    [data, geo] = await Promise.all([
      fetch('data/indicators.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }),
      fetch('data/municipios.geojson').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }),
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
  IND.percap = { label: 'Intensidade radiante aparente por habitante, 2022', unit: 'mW·sr⁻¹ por habitante', kind: 'der', type: 'seq', d: 1,
    get: (m) => m.per_capita_mw_sr_hab, breaks: mkBreaksQ(pooled((m) => [m.per_capita_mw_sr_hab])),
    scheme: 'Quantis (5 classes) dos 92 municípios. Índice relativo: não representa consumo ou emissão individual.',
    period: () => 'ano 2022 (Censo)', source: 'Intensidade radiante aparente (radiância × área, direção do sensor) ÷ população residente do Censo 2022 (IBGE).' };
  const KIND = { obs: ['obs', 'Observado (agregado)'], der: ['der', 'Derivado'], qa: ['qa', 'Controle de qualidade'] };

  const st = { ind: 'mean', iy: years.length - 1, sel: null };
  const val = (cd, key = st.ind, iy = st.iy) => { const v = IND[key].get(M[cd], iy); return v == null || !isFinite(v) ? null : v; };

  /* ---------- aviso metodológico (dados) ---------- */
  (function alertText() {
    const qa = data.qa, pre = qa.filter((r) => r.year <= 2021), post = qa.filter((r) => r.year >= 2022);
    const mx = (a, k) => Math.max(...a.map((r) => r[k])), mn = (a, k) => Math.min(...a.map((r) => r[k]));
    const t = `A série (sensor Suomi NPP) mostra, a partir de 2022, aumento do piso de ruído em áreas escuras: a radiância média dos pixels persistentemente escuros em terra era ${fmt(mn(pre, 'dark_land_mean'), 3)}–${fmt(mx(pre, 'dark_land_mean'), 3)} até 2021 e passou a ${fmt(mn(post, 'dark_land_mean'), 3)}–${fmt(mx(post, 'dark_land_mean'), 3)} depois (nW·cm⁻²·sr⁻¹). Esse efeito é bem menor no NOAA-20. Há também um aumento comum aos dois sensores que não foi separado de um possível artefato do algoritmo compartilhado. O sinal da tendência depende da janela de anos. Estes resultados são diagnósticos de desenvolvimento, não foram validados e não devem ser interpretados como mudança real de iluminação sem essa ressalva. Veja “Limitações”.`;
    $('alert-text').textContent = t;
  })();

  /* ---------- mapa ---------- */
  const map = L.map('mapa', { zoomSnap: 0.25, minZoom: 6, attributionControl: true });
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

  function colorFor(ind, v) {
    if (v == null) return NODATA;
    const k = classOf(v, ind.breaks);
    return (ind.type === 'div' ? DIV : SEQ)[k];
  }
  function className(ind, k) {
    const b = ind.breaks, n = b.length;
    if (k === 0) return `< ${fmt(b[0], ind.d)}`;
    if (k === n) return `≥ ${fmt(b[n - 1], ind.d)}`;
    return `${fmt(b[k - 1], ind.d)} a < ${fmt(b[k], ind.d)}`;
  }

  function render() {
    const ind = IND[st.ind];
    $('year-wrap').hidden = !ind.yearly;
    $('year-note').hidden = !ind.yearly;
    gl.eachLayer((layer) => {
      const cd = layer.feature.properties.CD_MUN, v = val(cd);
      const sigP = ind.sigP && M[cd].trends[ind.win] && M[cd].trends[ind.win].p_value != null && M[cd].trends[ind.win].p_value < 0.05;
      const sel = cd === st.sel;
      layer.setStyle({ fillColor: colorFor(ind, v), weight: sel ? 3.2 : sigP ? 2.2 : 0.6, color: sel ? '#0b5fff' : sigP ? '#000' : '#555', fillOpacity: 0.92 });
      if (sel || sigP) layer.bringToFront();
      let tip = `<strong>${esc(M[cd].name)}</strong><br>${v == null ? 'sem dado válido' : fmt(v, ind.d) + ' ' + esc(ind.unit)}`;
      if (v != null) tip += `<br><span class="muted">classe: ${esc(className(ind, classOf(v, ind.breaks)))}</span>`;
      if (ind.sigP && M[cd].trends[ind.win]) tip += `<br>p = ${fmt(M[cd].trends[ind.win].p_value, 3)}`;
      layer.unbindTooltip().bindTooltip(tip, { sticky: true });
    });
    renderLegend(ind);
    renderRank();
  }

  function renderLegend(ind) {
    const [kcls, ktxt] = KIND[ind.kind];
    const pal = ind.type === 'div' ? DIV : SEQ;
    const yr = ind.yearly ? years[st.iy] : null;
    const items = pal.map((c, k) => `<li><span class="sw" style="background:${c}"></span>${esc(className(ind, k))}</li>`).join('') +
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
  const NIT = codes.find((c) => M[c].name === 'Niterói');
  $('case-btn').addEventListener('click', () => { showTab('mun'); select(NIT); });
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
  $('cmp1').value = NIT; $('cmp2').value = codes.find((c) => M[c].name === 'Rio de Janeiro') || '';
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
      <h4>Municípios por sinal da tendência</h4>
      <div class="table-wrap"><table><thead><tr><th>Janela</th><th class="num">Inclin. &gt; 0</th><th class="num">Inclin. &lt; 0</th><th class="num">p &lt; 0,05</th></tr></thead><tbody>${cnt}</tbody></table></div>
      <h4>Comparação entre sensores (média estadual, nW·cm⁻²·sr⁻¹)</h4>
      <div class="table-wrap"><table><thead><tr><th>Ano</th><th class="num">S-NPP</th><th class="num">NOAA-20</th><th class="num">NOAA-20 / S-NPP</th></tr></thead><tbody>${scRows}</tbody></table></div>
      <p class="small">Concordância das inclinações municipais entre sensores (${sc.years[0]}–${sc.years.at(-1)}): Spearman ${fmt(sc.spearman_trend_slope, 2)}; mesmo sinal em ${fmt(100 * sc.trend_sign_agreement, 1)}% dos municípios.</p>
      <h4>Sensibilidade à configuração (em relação à principal)</h4>
      <div class="table-wrap"><table><thead><tr><th>Janela</th><th>Variação</th><th class="num">ρ média (ano final)</th><th class="num">ρ inclinação</th><th class="num">Mesmo sinal</th></tr></thead><tbody>${sens}</tbody></table></div>`;
    OpenLuxCharts.lineChart($('state-chart'), { title: 'Radiância média estadual', years, yLabel: 'nW·cm⁻²·sr⁻¹', digits: 2, shadeFrom: 2022, shadeLabel: 'ruído S-NPP', series: [{ name: 'Estado (média ponderada)', values: data.state.mean, color: COL[0] }] });
    OpenLuxCharts.lineChart($('qa-chart'), { title: 'Radiância média de pixels persistentemente escuros', years: data.qa.map((r) => r.year), yLabel: 'nW·cm⁻²·sr⁻¹', digits: 3, shadeFrom: 2022, shadeLabel: 'após 2021', zeroBase: true,
      series: [{ name: 'Terra', values: data.qa.map((r) => r.dark_land_mean), color: COL[1] }, { name: 'Mar', values: data.qa.map((r) => r.dark_sea_mean), color: COL[0] }] });
  }

  /* ---------- informações científicas ---------- */
  function renderInfo() {
    const lowValid = codes.filter((c) => M[c].valid.some((v) => v != null && v < 0.9)).map((c) => M[c].name);
    const src = meta.sources.map((s) => `<tr><td><a href="${esc(s.url)}" rel="noopener">${esc(s.name)}</a>${s.doi ? `<br><span class="small">DOI: <a href="https://doi.org/${esc(s.doi)}" rel="noopener">${esc(s.doi)}</a></span>` : ''}</td><td>${esc(s.institution)}</td><td>${esc(s.version)}</td><td>${esc(s.license)} <strong>[${s.license_status === 'confirmado' ? 'confirmado' : 'não confirmado no texto oficial'}]</strong></td></tr>`).join('');
    const docs = meta.documents.map((d) => `<li><a href="${esc(d.url)}" rel="noopener">${esc(d.name)}</a> (${esc(d.institution)})</li>`).join('');
    const refs = meta.references.map((r) => `<li>${esc(r.cite)} <a href="https://doi.org/${esc(r.doi)}" rel="noopener">doi:${esc(r.doi)}</a></li>`).join('');
    const hashes = Object.entries(meta.run.output_sha256).map(([k, v]) => `<tr><td>${esc(k)}</td><td><code>${esc(v)}</code></td></tr>`).join('');
    $('info-content').innerHTML = `
      <details open><summary>Metodologia (resumo)</summary>
        <p>Produto: NASA Black Marble VNP46A4 v2.0 (radiância noturna anual, grade de 15 arc-s ≈ 460 m), camada <code>AllAngle_Composite_Snow_Free</code>. São mantidos pixels de qualidade 0 (boa), sobre terra (códigos 0, 1 e 5 da máscara terra/água), sem valores de preenchimento ou negativos. Não há reamostragem.</p>
        <p><strong>Radiância média</strong> do município: L̄ = Σ wᵢ·Lᵢ / Σ wᵢ, onde wᵢ é a fração da área do pixel coberta pelo município (cobertura fracionária) e Lᵢ é a radiância (nW·cm⁻²·sr⁻¹) dos pixels válidos. A mediana é ponderada pelos mesmos pesos.</p>
        <p><strong>Intensidade radiante aparente</strong>: S = Σ wᵢ·Lᵢ·Aᵢ (nW·sr⁻¹), com Aᵢ a área elipsoidal (WGS84) do pixel. É uma intensidade na direção observada pelo sensor, <em>não</em> a emissão luminosa total do município. A soma bruta de pixels não é usada.</p>
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
