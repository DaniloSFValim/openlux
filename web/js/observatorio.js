/* Observatório (seções abaixo do mapa): indicadores estaduais, evolução, extremos, distribuição,
   variação 2018→2025, pixels iluminados e ranking. Lê indicators_noaa20.json e indicators.json. */
(function () {
  'use strict';
  const C = window.OpenLuxComum;
  const $ = (id) => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs, parent, texto) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (texto != null) n.textContent = texto;
    if (parent) parent.appendChild(n);
    return n;
  }
  function hel(tag, parent, texto, attrs) {
    const n = document.createElement(tag);
    for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (texto != null) n.textContent = texto;
    if (parent) parent.appendChild(n);
    return n;
  }
  const media = (v) => v.filter((x) => x != null && isFinite(x));

  Promise.all([C.indicadores('noaa20'), C.indicadores('snpp')])
    .then(([N, S]) => iniciar(N, S))
    .catch((e) => { console.error(e); C.erro($('notaKpi'), 'Não foi possível carregar os dados publicados. Recarregue a página.'); });

  function iniciar(N, S) {
    const anos = N.meta.years;
    const cods = Object.keys(N.municipios);
    const nome = (c) => N.municipios[c].name;
    const medias = (a) => cods.map((c) => N.municipios[c].mean[anos.indexOf(a)]).filter((v) => v != null && isFinite(v));
    const anoSel = $('anoObs');
    anos.forEach((y) => anoSel.appendChild(new Option(String(y), String(y))));
    anoSel.value = String(anos[anos.length - 1]);

    function kpis(a) {
      const v = medias(a), ord = v.slice().sort((x, y) => x - y);
      const a0 = anos[0];
      const est0 = media(cods.map((c) => N.municipios[c].mean[0])), est1 = medias(a);
      const m0 = est0.reduce((s, x) => s + x, 0) / est0.length, m1 = est1.reduce((s, x) => s + x, 0) / est1.length;
      const itens = [
        ['Municípios', String(cods.length), 'Rio de Janeiro, malha IBGE 2024'],
        ['Período histórico', anos[0] + '–' + anos[anos.length - 1], 'NOAA-20 (primário); S-NPP desde 2012'],
        ['Sensores', 'NOAA-20 e S-NPP', 'NOAA-20 é o primário desta análise'],
        ['Radiância média estadual', C.fmt(m1, 2), 'média simples dos 92 municípios, ' + a + ' · nW·cm⁻²·sr⁻¹'],
        ['Mediana municipal', C.fmt(C.quantil(ord, 0.5), 2), 'mediana das médias municipais, ' + a],
        ['Variação estadual ' + a0 + '→' + anos[anos.length - 1], C.fmt(100 * (m1 - m0) / m0, 1) + ' %', 'média simples de ' + a0 + ' ' + C.fmt(m0, 2) + ' → ' + C.fmt(m1, 2)],
      ];
      const box = $('kpis'); box.innerHTML = '';
      itens.forEach(([rot, val, sub]) => {
        const k = hel('div', box, null, { class: 'kpi' });
        hel('div', k, rot, { class: 'kpi-rot' });
        hel('div', k, val, { class: 'kpi-val' });
        hel('div', k, sub, { class: 'kpi-sub' });
      });
    }

    function evolucao() {
      const g = $('grafEvo'); g.innerHTML = '';
      const W = 640, H = 260, m = { l: 52, r: 16, t: 12, b: 30 };
      const serie = (D) => D.meta.years.map((y, i) => { const v = Object.keys(D.municipios).map((c) => D.municipios[c].mean[i]).filter((x) => x != null && isFinite(x)); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : null; });
      const sN = serie(N), sS = serie(S);
      const anosTodos = S.meta.years.concat([]); // 2012–2025
      const max = Math.max(...sN.filter(Boolean), ...sS.filter(Boolean), 1e-9);
      const x = (y) => m.l + ((y - anosTodos[0]) / (anosTodos[anosTodos.length - 1] - anosTodos[0])) * (W - m.l - m.r);
      const yv = (v) => H - m.b - (v / max) * (H - m.t - m.b);
      [0, 0.5, 1].forEach((f) => { const v = max * f; svg('line', { x1: m.l, x2: W - m.r, y1: yv(v), y2: yv(v), stroke: 'rgba(255,255,255,.08)' }, g); svg('text', { x: 6, y: yv(v) + 4 }, g, C.fmt(v, 1)); });
      anosTodos.forEach((y, i) => { if (y % 2 === 0) svg('text', { x: x(y) - 10, y: H - 8 }, g, String(y)); });
      const linha = (vals, anosX, cor, extra) => {
        const pts = vals.map((v, i) => (v == null ? null : x(anosX[i]) + ',' + yv(v))).filter(Boolean).join(' ');
        svg('polyline', Object.assign({ points: pts, fill: 'none', stroke: cor, 'stroke-width': 2.4 }, extra || {}), g);
      };
      linha(sS, anosTodos, '#9fb3cf', { 'stroke-dasharray': '5 4' });
      linha(sN, N.meta.years, '#ffd166');
    }

    function extremos(a) {
      const rank = cods.filter((c) => N.municipios[c].mean[anos.indexOf(a)] != null).sort((p, q) => N.municipios[q].mean[anos.indexOf(a)] - N.municipios[p].mean[anos.indexOf(a)]);
      const val = (c) => N.municipios[c].mean[anos.indexOf(a)];
      const mais = $('maiores'), menos = $('menores'); mais.innerHTML = ''; menos.innerHTML = '';
      rank.slice(0, 5).forEach((c) => item(mais, c, val(c)));
      rank.slice(-5).reverse().forEach((c) => item(menos, c, val(c)));
    }
    function item(lista, c, v) {
      const li = hel('li', lista);
      const a = hel('a', li, nome(c), { href: 'explorar.html?s=noaa20&y=' + anoSel.value + '&m=' + c });
      hel('span', li, ' · ' + C.fmt(v, 2), { class: 'suave' });
    }

    function distribuicao(a) {
      const g = $('grafDist'); g.innerHTML = '';
      const W = 640, H = 220, edges = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024];
      const cont = edges.slice(0, -1).map(() => 0);
      medias(a).forEach((v) => { let i = 0; while (i < cont.length - 1 && v >= edges[i + 1]) i++; cont[i]++; });
      const maxC = Math.max(...cont, 1), bw = (W - 60) / cont.length;
      cont.forEach((n, i) => {
        const h = ((H - 40) * n) / maxC;
        svg('rect', { x: 50 + i * bw + 2, y: H - 24 - h, width: bw - 4, height: h, fill: 'rgba(255,209,102,.35)' }, g);
        svg('text', { x: 50 + i * bw, y: H - 8 }, g, edges[i] + '–' + edges[i + 1]);
        if (n) svg('text', { x: 50 + i * bw + bw / 2 - 4, y: H - 28 - h }, g, String(n));
      });
    }

    function comparacao() {
      const i0 = 0, last = anos.length - 1;
      const t = cods.map((c) => N.municipios[c].trends['2018_2025']).filter(Boolean);
      const sobe = t.filter((x) => x.change_abs > 0).length, desce = t.filter((x) => x.change_abs < 0).length;
      const sigSobe = t.filter((x) => x.p_value < 0.05 && x.slope > 0).length, sigDesce = t.filter((x) => x.p_value < 0.05 && x.slope < 0).length;
      const pcts = t.map((x) => x.change_pct).filter((v) => v != null && isFinite(v)).sort((p, q) => p - q);
      $('comparacao').innerHTML = '';
      const p = hel('p', $('comparacao'));
      p.textContent = `Entre ${anos[i0]} e ${anos[last]}, ${sobe} municípios tiveram média maior e ${desce} média menor. Com p < 0,05 (Theil–Sen), ${sigSobe} mostram tendência de alta e ${sigDesce} de queda; os demais não sustentam tendência.`;
      const p2 = hel('p', $('comparacao'), null, { class: 'nota-metodo' });
      p2.textContent = `Variação percentual por município: mediana ${C.fmt(C.quantil(pcts, 0.5), 1)} %, entre ${C.fmt(pcts[0], 1)} % e ${C.fmt(pcts[pcts.length - 1], 1)} %. Calculada só onde a média de ${anos[i0]} é ≥ 0,401 nW·cm⁻²·sr⁻¹; ver Metodologia.`;
    }

    function terreno(a) {
      const v = cods.map((c) => N.municipios[c].lit[anos.indexOf(a)]).filter((x) => x != null && isFinite(x));
      $('terrMed').textContent = v.length ? C.fmt(C.quantil(v.slice().sort((p, q) => p - q), 0.5), 3) : '—';
    }

    function ranking(filtro) {
      const corpo = $('corpoRank'); corpo.innerHTML = '';
      const a = anoSel.value, rank = cods.filter((c) => N.municipios[c].mean[anos.indexOf(+a)] != null).sort((p, q) => N.municipios[q].mean[anos.indexOf(+a)] - N.municipios[p].mean[anos.indexOf(+a)]);
      const termo = (filtro || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
      rank.forEach((c, i) => {
        const n = nome(c);
        if (termo && !n.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().includes(termo)) return;
        const tr = hel('tr', corpo);
        hel('td', tr, String(i + 1) + 'º');
        hel('td', tr, n);
        hel('td', tr, C.fmt(N.municipios[c].mean[anos.indexOf(+a)], 2));
        const td = hel('td', tr);
        hel('a', td, 'explorar', { href: 'explorar.html?s=noaa20&y=' + a + '&m=' + c });
      });
    }

    function tudo() {
      const a = anoSel.value;
      kpis(+a); extremos(+a); distribuicao(+a); terreno(+a); ranking($('busca').value);
    }
    anoSel.addEventListener('change', tudo);
    $('busca').addEventListener('input', (e) => ranking(e.target.value));
    evolucao(); comparacao(); tudo();
  }
})();
