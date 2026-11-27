/* OpenLux — mapa de localização dos 92 municípios, colorido pela classe de luz média do ano escolhido.
   Usado em páginas de texto (metodologia, dados abertos). Lê só arquivos publicados.
   Cursor mostra o município e a luz média; clique abre a página municipal. */
(function () {
  'use strict';
  const box = document.getElementById('mapa-estado');
  if (!box || typeof L === 'undefined') return;
  const COR = ['#0b1530', '#2b2a5e', '#7a3d7c', '#e0604f', '#ffb347', '#fff4c2'];
  const ROT = ['< 0,5', '0,5 a < 2', '2 a < 8', '8 a < 30', '30 a < 100', '≥ 100'];
  const LIM = [0.5, 2, 8, 30, 100];
  const slug = (s) => s.normalize('NFKD').replace(/[^\x00-\x7F]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const classe = (v) => { if (v == null || !isFinite(v)) return -1; let i = 0; while (i < LIM.length && v >= LIM[i]) i++; return i; };
  const fmt = (v) => (v == null ? '—' : v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));

  Promise.all([
    fetch('data/municipios.geojson').then((r) => r.json()),
    fetch('data/indicators_noaa20.json').then((r) => r.json()),
  ]).then(([geo, D]) => {
    const anos = D.meta.years;
    const controle = document.getElementById(box.dataset.controle || 'ano-estado');
    const saida = document.getElementById(box.dataset.saida || 'ano-estado-out');
    let k = anos.length - 1;
    const mapa = L.map(box, { attributionControl: true, scrollWheelZoom: false, minZoom: 6, maxZoom: 12 });
    mapa.attributionControl.setPrefix(false).addAttribution('Limites: IBGE, Malha 2024 · Luz: NASA Black Marble (NOAA-20)');
    const cor = (cd) => { const c = classe(D.municipios[cd].mean[k]); return c < 0 ? '#1b2540' : COR[c]; };
    const camada = L.geoJSON(geo, {
      style: (f) => ({ fillColor: cor(f.properties.CD_MUN), fillOpacity: 0.92, color: 'rgba(255,255,255,.25)', weight: 0.6 }),
      onEachFeature: (f, layer) => {
        const cd = f.properties.CD_MUN, nome = f.properties.NM_MUN;
        layer.bindTooltip(() => `${nome}: ${fmt(D.municipios[cd].mean[k])} nW·cm⁻²·sr⁻¹ (${anos[k]})`, { sticky: true });
        layer.on('mouseover', () => layer.setStyle({ color: '#ffffff', weight: 1.4 }));
        layer.on('mouseout', () => camada.resetStyle(layer));
        layer.on('click', () => { location.href = 'municipio/' + slug(nome) + '.html'; });
      },
    }).addTo(mapa);
    mapa.fitBounds(camada.getBounds(), { padding: [10, 10] });
    const legenda = document.getElementById(box.dataset.legenda || 'legenda-estado');
    if (legenda) legenda.innerHTML = ROT.map((r, i) => `<span style="--c:${COR[i]}">${r}</span>`).join('');
    function pintar() {
      if (saida) saida.textContent = anos[k];
      camada.setStyle((f) => ({ fillColor: cor(f.properties.CD_MUN) }));
    }
    if (controle) {
      controle.min = 0; controle.max = anos.length - 1; controle.value = k;
      controle.addEventListener('input', (e) => { k = Number(e.target.value); pintar(); });
    }
    pintar();
    box.dataset.pronto = '1';
  }).catch(() => { box.textContent = 'Não foi possível carregar o mapa.'; });
})();
