/* OpenLux — gráficos SVG próprios (sem biblioteca), compartilhados pelo Observatório e pelo Laboratório. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const el = (tag, attrs, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };
  const txt = (parent, attrs, s) => { const t = el('text', attrs, parent); t.textContent = s; return t; };

  // Linhas: `series` = [{ valores: [num|null], cor, classe, tracejado, rotulo }], `anos` = eixo X.
  function linhas(container, anos, series, opts) {
    const W = 760, H = 300, pad = { l: 56, r: 16, t: 16, b: 34 };
    const todos = series.flatMap((s) => s.valores).filter((v) => v != null);
    const lo = Math.min(...todos), hi = Math.max(...todos), folga = (hi - lo) * 0.1 || 0.1;
    const y0 = lo - folga, y1 = hi + folga;
    const x = (i) => pad.l + (i * (W - pad.l - pad.r)) / (anos.length - 1);
    const y = (v) => pad.t + (1 - (v - y0) / (y1 - y0)) * (H - pad.t - pad.b);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': opts && opts.rotulo || 'Gráfico de linhas' });
    container.innerHTML = '';
    container.appendChild(svg);
    for (let k = 0; k <= 4; k++) {
      const v = y0 + ((y1 - y0) * k) / 4, yy = y(v);
      el('line', { x1: pad.l, x2: W - pad.r, y1: yy, y2: yy, class: 'grade' }, svg);
      txt(svg, { x: pad.l - 8, y: yy + 4, 'text-anchor': 'end', class: 'eixo' }, fmt(v, 2));
    }
    anos.forEach((a, i) => txt(svg, { x: x(i), y: H - 10, 'text-anchor': 'middle', class: 'eixo' }, String(a)));
    series.forEach((s) => {
      const pts = s.valores.map((v, i) => (v == null ? null : `${x(i)},${y(v)}`)).filter(Boolean).join(' ');
      const attrs = { points: pts, class: s.classe, fill: 'none' };
      if (s.tracejado) attrs['stroke-dasharray'] = '6 5';
      el('polyline', attrs, svg);
      s.valores.forEach((v, i) => { if (v != null) el('circle', { cx: x(i), cy: y(v), r: s.tracejado ? 2.8 : 3.5, class: s.classe + '-p' }, svg); });
    });
    return svg;
  }

  // Histograma: `vals` com faixas iguais entre lo e hi.
  function histograma(container, vals, lo, hi, opts) {
    const W = 760, H = 240, pad = { l: 40, r: 12, t: 12, b: 34 }, B = (opts && opts.faixas) || 12;
    const cont = new Array(B).fill(0);
    vals.forEach((v) => { let i = Math.floor(((v - lo) / (hi - lo)) * B); if (i >= B) i = B - 1; if (i < 0) i = 0; cont[i]++; });
    const max = Math.max(...cont, 1);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': opts && opts.rotulo || 'Histograma' });
    container.innerHTML = '';
    container.appendChild(svg);
    const bw = (W - pad.l - pad.r) / B;
    cont.forEach((n, i) => {
      const h = ((H - pad.t - pad.b) * n) / max;
      el('rect', { x: pad.l + i * bw + 2, y: H - pad.b - h, width: bw - 4, height: h, class: 'barra' }, svg);
      txt(svg, { x: pad.l + i * bw + bw / 2, y: H - pad.b + 14, 'text-anchor': 'middle', class: 'eixo' }, fmt(lo + ((hi - lo) * i) / B, 1));
      if (n) txt(svg, { x: pad.l + i * bw + bw / 2, y: H - pad.b - h - 4, 'text-anchor': 'middle', class: 'eixo' }, String(n));
    });
    return svg;
  }

  window.OpenLuxGraficos = { linhas, histograma, fmt };
})();
