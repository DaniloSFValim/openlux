/* Gráficos de linha em SVG, sem dependências. Valores nulos geram interrupções na linha. */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });

  function el(name, attrs, text) {
    const e = document.createElementNS(NS, name);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }

  function niceTicks(min, max, n) {
    if (!(isFinite(min) && isFinite(max))) return [0, 1];
    if (min === max) { max = min + 1; }
    const raw = (max - min) / n, mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || 10 * mag;
    const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step, out = [];
    for (let v = lo; v <= hi + step / 2; v += step) out.push(Math.round(v / step) * step);
    return out;
  }

  function lineChart(container, o) {
    const W = 560, H = o.height || 250, m = { l: 52, r: 12, t: 12, b: 34 };
    const years = o.years, d = o.digits == null ? 2 : o.digits;
    const all = o.series.flatMap((s) => s.values).filter((v) => v != null && isFinite(v));
    container.textContent = '';
    if (!all.length) { container.textContent = 'Sem dados válidos para este gráfico.'; return; }
    let lo = Math.min(...all), hi = Math.max(...all);
    if (o.zeroBase) lo = Math.min(lo, 0);
    const ticks = niceTicks(lo, hi, 5);
    const y0 = ticks[0], y1 = ticks[ticks.length - 1];
    const x = (i) => m.l + (years.length === 1 ? 0 : (i * (W - m.l - m.r)) / (years.length - 1));
    const y = (v) => m.t + (1 - (v - y0) / (y1 - y0)) * (H - m.t - m.b);

    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
      'aria-label': `${o.title}. ${o.series.map((s) => s.name).join('; ')}. Tabela de dados disponível abaixo.` });
    svg.appendChild(el('title', {}, o.title));
    if (o.shadeFrom != null) {
      const i0 = years.indexOf(o.shadeFrom);
      if (i0 >= 0) {
        const xa = x(i0) - 4;
        svg.appendChild(el('rect', { x: xa, y: m.t, width: W - m.r - xa, height: H - m.t - m.b,
          fill: 'rgba(230,159,0,.16)' }));
        svg.appendChild(el('text', { x: xa + 4, y: m.t + 11, 'font-size': 10, fill: 'currentColor' }, o.shadeLabel || ''));
      }
    }
    ticks.forEach((t) => {
      svg.appendChild(el('line', { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t), stroke: 'currentColor', 'stroke-opacity': 0.15 }));
      svg.appendChild(el('text', { x: m.l - 6, y: y(t) + 3, 'text-anchor': 'end', 'font-size': 10, fill: 'currentColor' }, nf(d).format(t)));
    });
    if (o.zeroLine && y0 < 0 && y1 > 0)
      svg.appendChild(el('line', { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), stroke: 'currentColor', 'stroke-width': 1.2 }));
    const step = Math.ceil(years.length / 8);
    years.forEach((yr, i) => {
      if (i % step === 0 || i === years.length - 1)
        svg.appendChild(el('text', { x: x(i), y: H - m.b + 15, 'text-anchor': 'middle', 'font-size': 10, fill: 'currentColor' }, String(yr)));
    });
    svg.appendChild(el('text', { x: 12, y: m.t + (H - m.t - m.b) / 2, 'font-size': 10, fill: 'currentColor',
      transform: `rotate(-90 12 ${m.t + (H - m.t - m.b) / 2})`, 'text-anchor': 'middle' }, o.yLabel || ''));

    o.series.forEach((s) => {
      let path = '', pen = false;
      s.values.forEach((v, i) => {
        if (v == null || !isFinite(v)) { pen = false; return; }
        path += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`; pen = true;
      });
      svg.appendChild(el('path', { d: path, fill: 'none', stroke: s.color, 'stroke-width': s.width || 2,
        'stroke-dasharray': s.dash || '' }));
      if (!s.noMarkers) s.values.forEach((v, i) => {
        if (v == null || !isFinite(v)) return;
        const c = el('circle', { cx: x(i), cy: y(v), r: 2.6, fill: s.color });
        c.appendChild(el('title', {}, `${s.name}, ${years[i]}: ${nf(d).format(v)}`));
        svg.appendChild(c);
      });
    });
    container.appendChild(svg);

    const lg = document.createElement('ul');
    lg.className = 'chart-legend';
    lg.style.cssText = 'list-style:none;display:flex;flex-wrap:wrap;gap:4px 14px;padding:0;margin:4px 0;font-size:.82rem';
    o.series.forEach((s) => {
      const li = document.createElement('li');
      li.innerHTML = `<svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="${s.color}" stroke-width="3" stroke-dasharray="${s.dash || ''}"/></svg> `;
      li.appendChild(document.createTextNode(s.name));
      lg.appendChild(li);
    });
    container.appendChild(lg);

    const det = document.createElement('details');
    det.innerHTML = '<summary>Tabela de dados do gráfico</summary>';
    const t = document.createElement('table');
    const head = '<tr><th>Ano</th>' + o.series.map((s) => `<th class="num">${s.name}</th>`).join('') + '</tr>';
    const body = years.map((yr, i) => `<tr><td>${yr}</td>` + o.series.map((s) =>
      `<td class="num">${s.values[i] == null ? '—' : nf(d).format(s.values[i])}</td>`).join('') + '</tr>').join('');
    t.innerHTML = `<thead>${head}</thead><tbody>${body}</tbody>`;
    det.appendChild(t);
    container.appendChild(det);
  }

  window.OpenLuxCharts = { lineChart };
})();
