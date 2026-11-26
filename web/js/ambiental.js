/* Observatório ambiental: desenha a camada de áreas urbanizadas (2019) em SVG. Lê só o GeoJSON publicado. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const box = document.getElementById('mapaUrb');
  if (!box) return;
  Promise.all([
    fetch('data/downloads/openlux_areas_urbanizadas_rj_2019.geojson').then((r) => r.json()),
    fetch('data/municipios.geojson').then((r) => r.json())
  ]).then(([urb, mun]) => {
    let minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
    const walk = (c, fn) => (typeof c[0] === 'number' ? fn(c) : c.forEach((x) => walk(x, fn)));
    mun.features.forEach((f) => walk(f.geometry.coordinates, (p) => { minx = Math.min(minx, p[0]); maxx = Math.max(maxx, p[0]); miny = Math.min(miny, p[1]); maxy = Math.max(maxy, p[1]); }));
    const k = Math.cos(((miny + maxy) / 2) * Math.PI / 180), W = 640, esc = (W - 10) / ((maxx - minx) * k), H = Math.ceil((maxy - miny) * esc) + 10;
    const X = (lon) => 5 + (lon - minx) * k * esc, Y = (lat) => 5 + (maxy - lat) * esc;
    const caminho = (g) => {
      const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
      return polys.map((rings) => rings.map((ring) => ring.map((p, i) => (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ',' + Y(p[1]).toFixed(1)).join('') + 'Z').join('')).join('');
    };
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Áreas urbanizadas do estado do Rio de Janeiro em 2019');
    const contorno = document.createElementNS(NS, 'path');
    contorno.setAttribute('d', mun.features.map((f) => caminho(f.geometry)).join(''));
    contorno.setAttribute('fill', '#1b2540'); contorno.setAttribute('stroke', 'rgba(255,255,255,.25)'); contorno.setAttribute('stroke-width', '.5');
    svg.appendChild(contorno);
    urb.features.forEach((f) => {
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', caminho(f.geometry)); p.setAttribute('fill', '#ffd166'); p.setAttribute('fill-opacity', '.85');
      svg.appendChild(p);
    });
    box.appendChild(svg);
  }).catch((e) => { console.error(e); box.textContent = 'Não foi possível carregar o mapa das áreas urbanizadas.'; });
})();
