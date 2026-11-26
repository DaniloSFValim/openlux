/* OpenLux — mapa interativo da página municipal: destaca o município e mostra os vizinhos do estado.
   Clique em um vizinho abre a página dele. Limites: IBGE, Malha Municipal Digital 2024 (data/municipios.geojson). */
(function () {
  'use strict';
  const el = document.getElementById('mapa-mun');
  if (!el) return;
  const cd = el.dataset.cd;
  // mesma regra de slug do gerador (scripts/build_web_municipios.py)
  const slug = (s) => s.normalize('NFKD').replace(/[^\x00-\x7F]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  fetch('../data/municipios.geojson')
    .then((r) => r.json())
    .then((geo) => {
      const mapa = L.map(el, { attributionControl: true, scrollWheelZoom: false, minZoom: 7, maxZoom: 13 });
      mapa.attributionControl.setPrefix(false).addAttribution('Limites: IBGE, Malha Municipal Digital 2024');
      const estilo = (f) => (f.properties.CD_MUN === cd
        ? { fillColor: '#ffd166', fillOpacity: 0.9, color: '#ffffff', weight: 1.5 }
        : { fillColor: '#1b2540', fillOpacity: 0.9, color: 'rgba(255,255,255,.2)', weight: 0.6 });
      const camada = L.geoJSON(geo, {
        style: estilo,
        onEachFeature: (f, layer) => {
          const nome = f.properties.NM_MUN;
          layer.bindTooltip(nome, { sticky: true });
          if (f.properties.CD_MUN === cd) return;
          layer.on('mouseover', () => layer.setStyle({ weight: 1.5, color: '#ffffff' }));
          layer.on('mouseout', () => camada.resetStyle(layer));
          layer.on('click', () => { location.href = slug(nome) + '.html'; });
        },
      }).addTo(mapa);
      const alvo = camada.getLayers().find((l) => l.feature.properties.CD_MUN === cd);
      mapa.fitBounds(alvo.getBounds(), { padding: [30, 30], maxZoom: 10 });
      el.dataset.pronto = '1';
    })
    .catch(() => {
      el.textContent = 'Não foi possível carregar o mapa. Os dados municipais continuam disponíveis abaixo.';
    });
})();
