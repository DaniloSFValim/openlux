/* Laboratório de análises: compara até três municípios com o estado.
   Lê indicators_noaa20.json (ou indicators.json) e openlux_percentis_pixels_<sensor>.csv. */
(function () {
  'use strict';
  const C = window.OpenLuxComum;
  const $ = (id) => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const CORES = ['#ffd166', '#e0604f', '#7fd1ff'];
  const PADRAO = ['3304557', '3303302', '3300100']; // Rio de Janeiro, Niterói, Angra dos Reis
  const params = new URLSearchParams(location.search);
  const sensor = params.get('s') === 'snpp' ? 'snpp' : 'noaa20';

  function el(tag, attrs, parent, texto) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (texto != null) n.textContent = texto;
    if (parent) parent.appendChild(n);
    return n;
  }
  function hel(tag, parent, texto) {
    const n = document.createElement(tag);
    if (texto != null) n.textContent = texto;
    if (parent) parent.appendChild(n);
    return n;
  }
  function parseCsv(txt) {
    const linhas = txt.trim().split(/\r?\n/);
    const cab = linhas.shift().split(',');
    const out = {};
    linhas.forEach((l) => {
      const v = l.split(','), o = {};
      cab.forEach((c, i) => (o[c] = v[i]));
      (out[o.CD_MUN] = out[o.CD_MUN] || {})[o.year] = { q75: +o.q75_radiance, q90: +o.q90_radiance, q95: +o.q95_radiance };
    });
    return out;
  }

  Promise.all([C.indicadores(sensor), C.texto('data/downloads/openlux_percentis_pixels_' + sensor + '.csv'), C.json('data/municipios.geojson')])
    .then(([D, csv, geo]) => { iniciar(D, parseCsv(csv)); desenhaDiferencas(D, geo); })
    .catch((e) => { console.error(e); C.erro($('erro'), 'Não foi possível carregar os dados publicados. Recarregue a página.'); });


  // Mapa de diferenças 2018→2025 (variação percentual da média municipal, já publicada em trends)
  function desenhaDiferencas(D, geo) {
    const cores = ['#b5483f', '#e0604f', '#8a7fd6', '#4f86c6', '#9fd3ff'];
    const rotulos = ['queda acima de 20 %', 'queda de 0 a 20 %', 'alta de 0 a 20 %', 'alta de 20 a 50 %', 'alta acima de 50 %'];
    const cinza = '#3c4660';
    let minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
    const walk = (c, fn) => (typeof c[0] === 'number' ? fn(c) : c.forEach((x) => walk(x, fn)));
    geo.features.forEach((f) => walk(f.geometry.coordinates, (p) => { minx = Math.min(minx, p[0]); maxx = Math.max(maxx, p[0]); miny = Math.min(miny, p[1]); maxy = Math.max(maxy, p[1]); }));
    const k = Math.cos(((miny + maxy) / 2) * Math.PI / 180), W = 460, esc = (W - 10) / ((maxx - minx) * k), H = Math.ceil((maxy - miny) * esc) + 10;
    const X = (lon) => 5 + (lon - minx) * k * esc, Y = (lat) => 5 + (maxy - lat) * esc;
    const caminho = (g) => {
      const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
      return polys.map((rings) => rings.map((ring) => ring.map((p, i) => (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ',' + Y(p[1]).toFixed(1)).join('') + 'Z').join('')).join('');
    };
    const box = $('mapaDif'); box.innerHTML = '';
    const svgEl = document.createElementNS(NS, 'svg');
    svgEl.setAttribute('viewBox', `0 0 ${W} ${H}`); svgEl.setAttribute('role', 'img');
    svgEl.setAttribute('aria-label', 'Mapa dos municípios colorido pela variação percentual da média entre 2018 e 2025');
    box.appendChild(svgEl);
    const contagem = [0, 0, 0, 0, 0];
    geo.features.forEach((f) => {
      const cd = f.properties.CD_MUN, t = D.municipios[cd] && D.municipios[cd].trends['2018_2025'];
      const pct = t && t.change_pct;
      let cor = cinza, cls = -1;
      if (pct != null && isFinite(pct)) {
        cls = pct < -20 ? 0 : pct < 0 ? 1 : pct < 20 ? 2 : pct < 50 ? 3 : 4;
        cor = cores[cls]; contagem[cls]++;
      }
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', caminho(f.geometry)); p.setAttribute('fill', cor);
      if (t && t.p_value < 0.05) p.setAttribute('stroke', '#fff');
      const tt = document.createElementNS(NS, 'title');
      tt.textContent = f.properties.NM_MUN + (pct != null ? ': ' + C.fmt(pct, 1) + ' %' : ': não calculado');
      p.appendChild(tt); svgEl.appendChild(p);
    });
    const leg = $('legDif'); leg.innerHTML = '';
    rotulos.forEach((r, i) => { const sp = document.createElement('span'); sp.textContent = r + ' (' + contagem[i] + ')'; sp.style.setProperty('--c', cores[i]); leg.appendChild(sp); });
    const sn = document.createElement('span'); sn.textContent = 'sem cálculo (' + (92 - contagem.reduce((a, c) => a + c, 0)) + ')'; sn.style.setProperty('--c', cinza); leg.appendChild(sn);
    $('resumoDif').textContent = 'Municípios com cálculo: ' + contagem.reduce((a, c) => a + c, 0) + ' de 92. Com p < 0,05 (contorno branco): ' + geo.features.filter((f) => { const t = D.municipios[f.properties.CD_MUN] && D.municipios[f.properties.CD_MUN].trends['2018_2025']; return t && t.p_value < 0.05; }).length + '.';
  }

  function iniciar(D, PERC) {
    const anos = D.meta.years;
    const codigos = Object.keys(D.municipios).sort((a, b) => D.municipios[a].name.localeCompare(D.municipios[b].name, 'pt-BR'));
    const nomeDe = (c) => D.municipios[c].name;
    const sel = [0, 1, 2].map((i) => {
      const s = $('m' + (i + 1));
      codigos.forEach((c) => s.appendChild(new Option(nomeDe(c), c)));
      return s;
    });
    const pedidos = (params.get('m') || '').split(',').filter((c) => D.municipios[c]);
    PADRAO.forEach((p, i) => (sel[i].value = pedidos[i] || p));
    const anoSel = $('ano');
    anos.forEach((y) => anoSel.appendChild(new Option(String(y), String(y))));
    anoSel.value = String(params.get('y') && anos.includes(+params.get('y')) ? params.get('y') : anos[anos.length - 1]);
    $('sensor').value = sensor;
    $('notaSensor').textContent = sensor === 'snpp'
      ? 'S-NPP: a partir de 2022 há mais ruído em áreas escuras. Não leia diferenças desse período como mudança real.'
      : 'NOAA-20: sensor primário desta análise. Dados de 2018 a 2025.';

    const media = (c, a) => D.municipios[c].mean[anos.indexOf(a)];
    const mediana = (c, a) => D.municipios[c].median[anos.indexOf(a)];
    const medias = (a) => codigos.map((c) => media(c, a)).filter((v) => v != null && isFinite(v));
    const ordenadas = (a) => medias(a).slice().sort((x, y) => x - y);

    function render() {
      const ids = sel.map((s) => s.value);
      const ano = +anoSel.value;
      const ord = ordenadas(ano);
      const cores = ids.map((c, i) => CORES[i]);
      // tabela
      const cab = $('cabTab'); cab.innerHTML = '';
      hel('th', cab, 'Indicador');
      ids.forEach((c) => hel('th', cab, nomeDe(c)));
      hel('th', cab, 'Estado (92 municípios)');
      const linhas = [];
      const pct = (c, k) => { const p = PERC[c] && PERC[c][ano]; return p ? p[k] : null; };
      const pos = (c) => { const v = media(c, ano); const mais = medias(ano).filter((x) => x > v).length; return v == null ? '—' : (mais + 1) + 'º de ' + ord.length; };
      const estMedian = C.quantil(ord, 0.5);
      linhas.push(['Radiância média (nW·cm⁻²·sr⁻¹)', ids.map((c) => C.fmt(media(c, ano), 2)), C.fmt(ord.reduce((a, b) => a + b, 0) / ord.length, 2)]);
      linhas.push(['Mediana dos pixels (nW·cm⁻²·sr⁻¹)', ids.map((c) => C.fmt(mediana(c, ano), 2)), C.fmt(estMedian, 2)]);
      linhas.push(['Percentil 75 dos pixels', ids.map((c) => C.fmt(pct(c, 'q75'), 2)), '—']);
      linhas.push(['Percentil 90 dos pixels', ids.map((c) => C.fmt(pct(c, 'q90'), 2)), '—']);
      linhas.push(['Percentil 95 dos pixels', ids.map((c) => C.fmt(pct(c, 'q95'), 2)), '—']);
      linhas.push(['Posição entre os 92 municípios (1º = maior média)', ids.map(pos), '—']);
      linhas.push(['População (Censo 2022)', ids.map((c) => (D.municipios[c].population != null ? C.nf(0).format(D.municipios[c].population) : '—')), '—']);
      const tb = $('corpoTab'); tb.innerHTML = '';
      linhas.forEach(([rot, vals, est]) => {
        const tr = hel('tr', tb);
        hel('td', tr, rot);
        vals.forEach((v) => hel('td', tr, v));
        hel('td', tr, est);
      });
      // evolução
      const g = $('grafEvo'); g.innerHTML = '';
      const W = 640, H = 260, m = { l: 52, r: 12, t: 12, b: 30 };
      const todosV = [];
      ids.forEach((c) => D.municipios[c].mean.forEach((v) => v != null && todosV.push(v)));
      const max = Math.max(...todosV, 1e-9);
      const x = (i) => m.l + (i / (anos.length - 1)) * (W - m.l - m.r);
      const y = (v) => H - m.b - (v / max) * (H - m.t - m.b);
      [0, 0.5, 1].forEach((f) => { const v = max * f; el('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), stroke: 'rgba(255,255,255,.08)' }, g); el('text', { x: 6, y: y(v) + 4 }, g, C.fmt(v, 1)); });
      anos.forEach((a, i) => { if (i % 2 === 0 || i === anos.length - 1) el('text', { x: i === anos.length - 1 ? x(i) - 34 : x(i) - 10, y: H - 8 }, g, String(a)); });
      ids.forEach((c, k) => {
        const pts = D.municipios[c].mean.map((v, i) => (v == null ? null : x(i) + ',' + y(v))).filter(Boolean).join(' ');
        el('polyline', { points: pts, fill: 'none', stroke: CORES[k], 'stroke-width': 2.2 }, g);
      });
      const leg = $('legEvo'); leg.innerHTML = '';
      ids.forEach((c, k) => { const s = hel('span', leg, nomeDe(c)); s.style.setProperty('--c', CORES[k]); });
      // distribuição
      const d = $('grafDist'); d.innerHTML = '';
      const edges = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024];
      const cont = edges.slice(0, -1).map(() => 0);
      medias(ano).forEach((v) => { let i = 0; while (i < cont.length - 1 && v >= edges[i + 1]) i++; cont[i]++; });
      const maxC = Math.max(...cont, 1), bw = (W - 60) / cont.length;
      cont.forEach((n, i) => {
        const h = ((H - 40) * n) / maxC;
        el('rect', { x: 50 + i * bw + 2, y: H - 24 - h, width: bw - 4, height: h, fill: 'rgba(255,209,102,.35)' }, d);
        el('text', { x: 50 + i * bw, y: H - 8 }, d, edges[i] + '–' + edges[i + 1]);
        if (n) el('text', { x: 50 + i * bw + bw / 2 - 4, y: H - 28 - h }, d, String(n));
      });
      ids.forEach((c, k) => {
        const v = media(c, ano); if (v == null) return;
        const i = Math.max(0, edges.findIndex((e, j) => v >= e && v < edges[j + 1]));
        const xm = 50 + i * bw + bw / 2;
        el('line', { x1: xm, x2: xm, y1: 10, y2: H - 24, stroke: CORES[k], 'stroke-width': 2, 'stroke-dasharray': '4 3' }, d);
      });
      // caixa (boxplot)
      const b = $('grafBox'); b.innerHTML = '';
      const q = [0, 0.25, 0.5, 0.75, 1].map((p) => C.quantil(ord, p));
      const sx = (v) => 40 + (v / (q[4] || 1)) * 560;
      el('line', { x1: sx(q[0]), x2: sx(q[4]), y1: 50, y2: 50, stroke: 'rgba(255,255,255,.4)' }, b);
      el('rect', { x: sx(q[1]), y: 36, width: Math.max(1, sx(q[3]) - sx(q[1])), height: 28, fill: 'rgba(255,209,102,.18)', stroke: '#ffd166' }, b);
      el('line', { x1: sx(q[2]), x2: sx(q[2]), y1: 36, y2: 64, stroke: '#ffd166', 'stroke-width': 2 }, b);
      ids.forEach((c, k) => { const v = media(c, ano); if (v != null) el('circle', { cx: sx(v), cy: 50, r: 5, fill: CORES[k] }, b); });
      el('text', { x: 40, y: 92 }, b, 'mín ' + C.fmt(q[0], 2) + ' · mediana ' + C.fmt(q[2], 2) + ' · máx ' + C.fmt(q[4], 2));
      $('resumoBox').textContent = 'Estado (92 municípios, ' + ano + '): 1º quartil ' + C.fmt(q[1], 2) + ', mediana ' + C.fmt(q[2], 2) + ', 3º quartil ' + C.fmt(q[3], 2) + ' nW·cm⁻²·sr⁻¹.';
      // tendência
      const ct = $('cabTrend'); ct.innerHTML = '';
      ['Município', 'Inclinação (nW·cm⁻²·sr⁻¹ por ano)', 'p-valor', 'Anos válidos', 'Variação 2018→2025 (%)', 'Leitura'].forEach((t) => hel('th', ct, t));
      const ctb = $('corpoTrend'); ctb.innerHTML = '';
      ids.forEach((c) => {
        const t = D.municipios[c].trends['2018_2025'];
        const tr = hel('tr', ctb);
        hel('td', tr, nomeDe(c));
        hel('td', tr, t ? C.fmt(t.slope, 3) : '—');
        hel('td', tr, t ? C.fmt(t.p_value, 3) : '—');
        hel('td', tr, t ? String(t.n_years) : '—');
        hel('td', tr, t ? C.fmt(t.change_pct, 1) : '—');
        hel('td', tr, !t ? '—' : t.p_value < 0.05 ? (t.slope > 0 ? 'tendência de alta (p < 0,05)' : 'tendência de queda (p < 0,05)') : 'sem tendência estatisticamente sustentada (p ≥ 0,05)');
      });
    }

    [...sel, anoSel].forEach((s) => s.addEventListener('change', () => {
      const u = new URL(location.href);
      u.search = `?s=${sensor}&y=${anoSel.value}&m=${sel.map((s2) => s2.value).join(',')}`;
      history.replaceState(null, '', u.search);
      render();
    }));
    $('sensor').addEventListener('change', (e) => {
      const u = new URL(location.href); u.searchParams.set('s', e.target.value); location.assign(u.href);
    });
    render();
  }
})();
