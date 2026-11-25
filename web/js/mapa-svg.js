/* OpenLux — mapa SVG dos municípios, compartilhado pelo Observatório e pela Comparação.
   Projeção equirretangular com escala cos(lat) constante. Cada município é um link para o explorador. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';

  function walk(coords, fn) { if (typeof coords[0] === 'number') return fn(coords); coords.forEach((c) => walk(c, fn)); }

  function caminho(g, sx, sy) {
    const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
    return polys.map((rings) => rings.map((ring) => ring.map((p, i) => (i ? 'L' : 'M') + sx(p[0]).toFixed(1) + ',' + sy(p[1]).toFixed(1)).join('') + 'Z').join('')).join('');
  }

  // Desenha os municípios dentro de `container`.
  // opts.cor(cd) -> cor de preenchimento; opts.titulo(cd) -> texto do <title>; opts.link(cd) -> URL do município.
  function desenhaMapa(container, geo, opts) {
    const feats = geo.features;
    let minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
    feats.forEach((f) => walk(f.geometry.coordinates, (p) => { minx = Math.min(minx, p[0]); maxx = Math.max(maxx, p[0]); miny = Math.min(miny, p[1]); maxy = Math.max(maxy, p[1]); }));
    const k = Math.cos(((miny + maxy) / 2) * Math.PI / 180);
    const W = 640, escala = W / ((maxx - minx) * k), H = Math.ceil((maxy - miny) * escala);
    const sx = (lon) => (lon - minx) * k * escala;
    const sy = (lat) => (maxy - lat) * escala;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('width', '100%');
    svg.setAttribute('role', 'group');
    if (opts.rotulo) svg.setAttribute('aria-label', opts.rotulo);
    container.innerHTML = '';
    container.appendChild(svg);
    feats.forEach((f) => {
      const cd = f.properties.CD_MUN;
      const a = document.createElementNS(NS, 'a');
      a.setAttribute('href', opts.link(cd));
      svg.appendChild(a);
      const path = document.createElementNS(NS, 'path');
      path.setAttribute('d', caminho(f.geometry, sx, sy));
      path.setAttribute('class', 'municipio');
      path.setAttribute('fill', opts.cor(cd));
      a.appendChild(path);
      const t = document.createElementNS(NS, 'title');
      t.textContent = opts.titulo(cd);
      path.appendChild(t);
    });
    return svg;
  }

  window.OpenLuxSvg = { desenhaMapa };
})();
