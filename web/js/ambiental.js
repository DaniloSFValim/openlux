/* OpenLux — observatório ambiental (análise exploratória). Lê data/ambiental/uc_municipios.json,
   gerado por scripts/analise_areas_protegidas.py. Nenhum número é digitado à mão. */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const pct = (v) => fmt(100 * v, 1) + ' %';

  fetch('data/ambiental/uc_municipios.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }).then((d) => {
    const r = d.resumo, mun = d.municipios.filter((m) => m.mean_radiance != null);
    $('k-ucs').textContent = r.ucs_no_estado;
    $('k-rho').textContent = fmt(r.spearman_fracao_uc_x_radiancia_media.rho, 2) + ' (p = ' + fmt(r.spearman_fracao_uc_x_radiancia_media.p, 3) + ')';
    $('k-dentro').textContent = fmt(r.radiancia_pixels_dentro_ucs.media, 2);
    $('k-fora').textContent = fmt(r.radiancia_pixels_fora_ucs.media, 2);

    const W = 760, H = 320, pad = { l: 56, r: 16, t: 16, b: 40 };
    const xs = mun.map((m) => m.fracao_area_uc), ys = mun.map((m) => m.mean_radiance);
    const x0 = 0, x1 = 1, y0 = 0, y1 = Math.max(...ys) * 1.05;
    const X = (v) => pad.l + ((v - x0) / (x1 - x0)) * (W - pad.l - pad.r);
    const Y = (v) => pad.t + (1 - (v - y0) / (y1 - y0)) * (H - pad.t - pad.b);
    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('width', '100%');
    const add = (tag, a, txt) => { const n = document.createElementNS(NS, tag); for (const k in a) n.setAttribute(k, a[k]); if (txt != null) n.textContent = txt; svg.appendChild(n); return n; };
    for (let k = 0; k <= 4; k++) {
      const v = (y1 * k) / 4, yy = Y(v);
      add('line', { x1: pad.l, x2: W - pad.r, y1: yy, y2: yy, class: 'grade' });
      add('text', { x: pad.l - 8, y: yy + 4, 'text-anchor': 'end', class: 'eixo' }, fmt(v, 1));
    }
    [0, 0.25, 0.5, 0.75, 1].forEach((v) => add('text', { x: X(v), y: H - 14, 'text-anchor': 'middle', class: 'eixo' }, pct(v)));
    add('text', { x: W / 2, y: H - 0, 'text-anchor': 'middle', class: 'eixo' }, 'fração da área municipal em UC');
    mun.forEach((m) => {
      const c = add('circle', { cx: X(m.fracao_area_uc), cy: Y(m.mean_radiance), r: 4, class: 'serie-noaa-p', 'fill-opacity': '0.75' });
      const t = document.createElementNS(NS, 'title'); t.textContent = `${m.NM_MUN}: ${pct(m.fracao_area_uc)} em UC; radiância ${fmt(m.mean_radiance, 2)}`; c.appendChild(t);
    });
    $('grafico-dispersao').innerHTML = ''; $('grafico-dispersao').appendChild(svg);

    const ord = mun.slice().sort((a, b) => b.fracao_area_uc - a.fracao_area_uc);
    const lista = (ul, arr) => { ul.innerHTML = ''; arr.forEach((m) => { const li = document.createElement('li'); li.innerHTML = `${m.NM_MUN} <span class="valor">${pct(m.fracao_area_uc)} · radiância ${fmt(m.mean_radiance, 2)}</span>`; ul.appendChild(li); }); };
    lista($('maiores-uc'), ord.slice(0, 10));
    lista($('menores-uc'), ord.slice(-10).reverse());
  }).catch((e) => {
    console.error(e);
    const aviso = document.createElement('p');
    aviso.className = 'erro'; aviso.setAttribute('role', 'alert');
    aviso.textContent = 'Não foi possível carregar os dados desta página. Tente recarregar.';
    document.querySelector('main').prepend(aviso);
  });
})();
