/* OpenLux — página inicial didática. Lê só data/indicators_noaa20.json (publicado). Sem dados simulados. */
(function () {
  'use strict';
  const COR = ['#0b1530', '#2b2a5e', '#7a3d7c', '#e0604f', '#ffb347', '#fff4c2'];
  const ROT = ['< 0,5', '0,5 a < 2', '2 a < 8', '8 a < 30', '30 a < 100', '≥ 100'];
  const LIMITES = [0.5, 2, 8, 30, 100];
  const $ = (id) => document.getElementById(id);
  const classe = (v) => { if (v == null) return -1; let i = 0; while (i < LIMITES.length && v >= LIMITES[i]) i++; return i; };
  const SVG = 'http://www.w3.org/2000/svg';

  fetch('data/indicators_noaa20.json')
    .then((r) => r.json())
    .then((D) => {
      const anos = D.meta.years, estado = D.state.mean, mun = Object.values(D.municipios);

      // passo 4: contagem por classe no ano escolhido
      const ano = $('ano');
      function classes() {
        const k = Number(ano.value);
        $('anoOut').textContent = anos[k];
        const cont = [0, 0, 0, 0, 0, 0];
        mun.forEach((m) => { const c = classe(m.mean[k]); if (c >= 0) cont[c]++; });
        $('classes').innerHTML = ROT.map((r, i) =>
          `<li><i style="background:${COR[i]}"></i>${r} nW·cm⁻²·sr⁻¹: <strong>${cont[i]}</strong> municípios</li>`).join('');
      }
      ano.addEventListener('input', classes);
      classes();

      // passo 5: série da média estadual (desenhada com SVG, sem bibliotecas)
      const svg = $('serie');
      const max = Math.max(...estado);
      const x = (i) => 40 + i * (560 / (anos.length - 1));
      const y = (v) => 210 - (v / max) * 180;
      const linha = document.createElementNS(SVG, 'polyline');
      linha.setAttribute('points', estado.map((v, i) => `${x(i)},${y(v)}`).join(' '));
      linha.setAttribute('fill', 'none'); linha.setAttribute('stroke', '#ffd166'); linha.setAttribute('stroke-width', '3');
      svg.appendChild(linha);
      estado.forEach((v, i) => {
        const c = document.createElementNS(SVG, 'circle');
        c.setAttribute('cx', x(i)); c.setAttribute('cy', y(v)); c.setAttribute('r', 4); c.setAttribute('fill', '#ffd166');
        const t = document.createElementNS(SVG, 'title'); t.textContent = `${anos[i]}: ${v.toFixed(2)}`; c.appendChild(t);
        svg.appendChild(c);
        const r = document.createElementNS(SVG, 'text');
        r.setAttribute('x', x(i)); r.setAttribute('y', 232); r.setAttribute('fill', '#9fb3cf'); r.setAttribute('font-size', 13); r.setAttribute('text-anchor', 'middle');
        r.textContent = anos[i]; svg.appendChild(r);
      });
      const marca = document.createElementNS(SVG, 'line');
      marca.setAttribute('y1', 20); marca.setAttribute('y2', 210); marca.setAttribute('stroke', '#fff4c2'); marca.setAttribute('stroke-dasharray', '4 4');
      svg.appendChild(marca);
      const ano3 = $('ano3');
      function destacar() {
        const k = Number(ano3.value);
        $('ano3Out').textContent = anos[k];
        marca.setAttribute('x1', x(k)); marca.setAttribute('x2', x(k));
      }
      ano3.addEventListener('input', destacar);
      destacar();
    })
    .catch(() => {
      const aviso = document.createElement('p');
      aviso.setAttribute('role', 'alert'); aviso.className = 'erro-prot';
      aviso.textContent = 'Não foi possível carregar os dados publicados. Tente recarregar a página.';
      document.querySelector('main').prepend(aviso);
    });
})();
