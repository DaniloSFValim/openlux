/* OpenLux — utilitários compartilhados pelas páginas de análise. Só lê arquivos publicados em data/. */
(function () {
  'use strict';
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const ARQ = { noaa20: 'data/indicators_noaa20.json', snpp: 'data/indicators.json' };
  async function json(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error('Falha ao carregar ' + url + ' (' + r.status + ')');
    return r.json();
  }
  async function texto(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error('Falha ao carregar ' + url + ' (' + r.status + ')');
    return r.text();
  }
  function indicadores(sensor) { return json(ARQ[sensor] || ARQ.noaa20); }
  // quantil tipo 7 (interpolação linear), sobre array já ordenado
  function quantil(ord, p) {
    if (!ord.length) return null;
    const h = (ord.length - 1) * p, i = Math.floor(h);
    return i + 1 < ord.length ? ord[i] + (h - i) * (ord[i + 1] - ord[i]) : ord[i];
  }
  function erro(el, msg) {
    el.hidden = false;
    el.setAttribute('role', 'alert');
    el.textContent = msg;
  }
  window.OpenLuxComum = { nf, fmt, json, texto, indicadores, quantil, erro };
})();
