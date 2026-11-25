/* OpenLux — Observatório (página inicial). Lê só os arquivos publicados em data/:
   indicators_noaa20.json (sensor primário), indicators.json (S-NPP, continuidade) e municipios.geojson.
   Todas as contas são feitas aqui e descritas na página; nenhum número é digitado à mão. */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const fmtPct = (v) => (v == null || !isFinite(v) ? '—' : (v > 0 ? '+' : '') + nf(1).format(v) + ' %');
  const el = (tag, attrs = {}, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };
  const exploreUrl = (cd, y) => `explorar.html?m=${encodeURIComponent(cd)}&s=noaa20&l=mun&y=${y}`;
  const getJSON = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });

  function falhou(e) {
    console.error(e);
    const aviso = document.createElement('p');
    aviso.className = 'erro';
    aviso.setAttribute('role', 'alert');
    aviso.textContent = 'Não foi possível carregar os dados publicados. Tente recarregar a página.';
    document.querySelector('main').prepend(aviso);
  }

  Promise.all([
    getJSON('data/indicators_noaa20.json'),
    getJSON('data/indicators.json'),
    getJSON('data/municipios.geojson'),
  ]).then(([N, S, geo]) => {
    const years = N.meta.years;                       // 2018..2025
    const last = years[years.length - 1], first = years[0];
    const codes = Object.keys(N.municipios).sort((a, b) => N.municipios[a].name.localeCompare(N.municipios[b].name, 'pt-BR'));
    const valor = (D, cd, y) => { const i = D.meta.years.indexOf(y); const v = D.municipios[cd] && D.municipios[cd].mean[i]; return v == null || !isFinite(v) ? null : v; };
    const media = (D, y) => { const xs = codes.map((c) => valor(D, c, y)).filter((v) => v != null); return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null; };

    // ---- indicadores estaduais
    $('k-mun').textContent = codes.length;
    $('k-periodo').textContent = `${first}–${last}`;
    $('k-ano').textContent = last;
    const m0 = media(N, first), mL = media(N, last);
    $('k-media').textContent = fmt(mL, 3) + ' nW·cm⁻²·sr⁻¹';
    $('k-var').textContent = fmtPct(m0 && mL ? (100 * (mL / m0 - 1)) : null);
    $('atualizacao').textContent = `Dados: NOAA-20 (VJ146A4), ${first}–${last}, e S-NPP (VNP46A4), 2012–${S.meta.years[S.meta.years.length - 1]}. Estimativas por sensoriamento remoto.`;

    // ---- evolução: NOAA-20 (sólido) e S-NPP no mesmo período (tracejado)
    const serieN = years.map((y) => media(N, y)), serieS = years.map((y) => media(S, y));
    grafico(serieN, serieS, years);
    $('tabela-evolucao').innerHTML = '<table><caption>Radiância média estadual por ano (nW·cm⁻²·sr⁻¹)</caption><thead><tr><th scope="col">Ano</th><th scope="col">NOAA-20</th><th scope="col">S-NPP</th></tr></thead><tbody>' +
      years.map((y, i) => `<tr><th scope="row">${y}</th><td>${fmt(serieN[i], 3)}</td><td>${fmt(serieS[i], 3)}</td></tr>`).join('') + '</tbody></table>';

    // ---- mapa de destaque (classes fixas, quintis do conjunto 2018–2025)
    const pool = [];
    codes.forEach((c) => years.forEach((y) => { const v = valor(N, c, y); if (v != null) pool.push(v); }));
    pool.sort((a, b) => a - b);
    const q = [0.2, 0.4, 0.6, 0.8].map((p) => pool[Math.floor(p * (pool.length - 1))]);
    const CORES = ['#2b2d42', '#5b4a2e', '#8f6b2a', '#c9962f', '#ffd66b'];
    const classe = (v) => { if (v == null) return -1; let k = 0; while (k < q.length && v > q[k]) k++; return k; };
    const bordas = [pool[0], ...q, pool[pool.length - 1]];
    $('legenda-classes').innerHTML = CORES.map((c, k) => `<li><span class="swatch" style="background:${c}"></span>${fmt(bordas[k], 2)} a ${fmt(bordas[k + 1], 2)}</li>`).join('');
    mapa(geo, (cd) => valor(N, cd, last), (cd) => classe(valor(N, cd, last)), CORES);
    $('mapa-ano').textContent = last;

    // ---- rankings do último ano
    const ord = codes.filter((c) => valor(N, c, last) != null).sort((a, b) => valor(N, b, last) - valor(N, a, last));
    lista($('ranking-maiores'), ord.slice(0, 10), (c) => valor(N, c, last), N, last);
    lista($('ranking-menores'), ord.slice(-10).reverse(), (c) => valor(N, c, last), N, last);
    $('rank-ano').textContent = last;

    // ---- distribuição municipal (histograma, 12 faixas iguais entre mín. e máx. do último ano)
    const vals = ord.map((c) => valor(N, c, last));
    histograma(vals, pool[0], pool[pool.length - 1]);
    $('dist-ano').textContent = last;

    // ---- variação entre o primeiro e o último ano (só linha de base acima do piso declarado)
    const piso = (N.meta.change_floor_nw_cm2_sr || {})[`${first}_${last}`];
    const var_ = codes.map((c) => { const a = valor(N, c, first), b = valor(N, c, last); return a != null && b != null && piso != null && a >= piso ? { c, p: 100 * (b / a - 1) } : null; }).filter(Boolean);
    var_.sort((a, b) => b.p - a.p);
    const lvar = (ul, arr) => { ul.innerHTML = ''; arr.forEach((r) => { const li = document.createElement('li'); li.innerHTML = `<a href="${exploreUrl(r.c, last)}">${esc(N.municipios[r.c].name)}</a> <span class="valor">${fmtPct(r.p)}</span>`; ul.appendChild(li); }); };
    lvar($('var-subidas'), var_.slice(0, 5));
    lvar($('var-quedas'), var_.slice(-5).reverse());

    // ---- busca
    const sel = $('mun-escolha');
    codes.forEach((c) => { const o = document.createElement('option'); o.value = c; o.textContent = N.municipios[c].name; sel.appendChild(o); });
    sel.addEventListener('change', () => { if (sel.value) location.href = exploreUrl(sel.value, last); });
  }).catch(falhou);

  function esc(s) { return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }

  function lista(ul, cds, val, D, y) {
    ul.innerHTML = '';
    cds.forEach((c) => {
      const li = document.createElement('li');
      li.innerHTML = `<a href="${exploreUrl(c, y)}">${esc(D.municipios[c].name)}</a> <span class="valor">${fmt(val(c), 3)}</span>`;
      ul.appendChild(li);
    });
  }

  function grafico(serieN, serieS, years) {
    const box = $('grafico-evolucao');
    const W = 760, H = 300, pad = { l: 56, r: 16, t: 16, b: 34 };
    const all = serieN.concat(serieS).filter((v) => v != null);
    const lo = Math.min(...all), hi = Math.max(...all), pad_y = (hi - lo) * 0.1 || 0.1;
    const y0 = lo - pad_y, y1 = hi + pad_y;
    const x = (i) => pad.l + (i * (W - pad.l - pad.r)) / (years.length - 1);
    const yv = (v) => pad.t + (1 - (v - y0) / (y1 - y0)) * (H - pad.t - pad.b);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', preserveAspectRatio: 'xMidYMid meet' });
    box.innerHTML = ''; box.appendChild(svg);
    for (let k = 0; k <= 4; k++) {
      const v = y0 + ((y1 - y0) * k) / 4, yy = yv(v);
      el('line', { x1: pad.l, x2: W - pad.r, y1: yy, y2: yy, class: 'grade' }, svg);
      const t = el('text', { x: pad.l - 8, y: yy + 4, 'text-anchor': 'end', class: 'eixo' }, svg); t.textContent = fmt(v, 2);
    }
    years.forEach((y, i) => { const t = el('text', { x: x(i), y: H - 10, 'text-anchor': 'middle', class: 'eixo' }, svg); t.textContent = y; });
    const linha = (serie, cls) => {
      const pts = serie.map((v, i) => (v == null ? null : `${x(i)},${yv(v)}`)).filter(Boolean).join(' ');
      el('polyline', { points: pts, class: cls, fill: 'none' }, svg);
      serie.forEach((v, i) => { if (v != null) el('circle', { cx: x(i), cy: yv(v), r: 3.5, class: cls + '-p' }, svg); });
    };
    linha(serieS, 'serie-snpp');
    linha(serieN, 'serie-noaa');
  }

  function mapa(geo, valorCd, classeCd, CORES) {
    window.OpenLuxSvg.desenhaMapa($('mapa-destaque'), geo, {
      rotulo: 'Mapa dos 92 municípios',
      link: (cd) => exploreUrl(cd, 2025),
      cor: (cd) => { const c = classeCd(cd); return c >= 0 ? CORES[c] : '#3b3f4a'; },
      titulo: (cd) => { const v = valorCd(cd); return `${geo.features.find((f) => f.properties.CD_MUN === cd).properties.NM_MUN}: ${fmt(v, 3)}`; },
    });
  }

  function histograma(vals, lo, hi) {
    const box = $('grafico-distribuicao');
    const W = 760, H = 240, pad = { l: 40, r: 12, t: 12, b: 34 }, B = 12;
    const cont = new Array(B).fill(0);
    vals.forEach((v) => { let i = Math.floor(((v - lo) / (hi - lo)) * B); if (i >= B) i = B - 1; if (i < 0) i = 0; cont[i]++; });
    const max = Math.max(...cont, 1);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%' });
    box.innerHTML = ''; box.appendChild(svg);
    const bw = (W - pad.l - pad.r) / B;
    cont.forEach((n, i) => {
      const h = ((H - pad.t - pad.b) * n) / max;
      el('rect', { x: pad.l + i * bw + 2, y: H - pad.b - h, width: bw - 4, height: h, class: 'barra' }, svg);
      const t = el('text', { x: pad.l + i * bw + bw / 2, y: H - pad.b + 14, 'text-anchor': 'middle', class: 'eixo' }, svg);
      t.textContent = fmt(lo + ((hi - lo) * i) / B, 1);
      if (n) { const c = el('text', { x: pad.l + i * bw + bw / 2, y: H - pad.b - h - 4, 'text-anchor': 'middle', class: 'eixo' }, svg); c.textContent = n; }
    });
  }
})();
