/* Observatório ambiental: mapa interativo das áreas urbanizadas (IBGE, 2019).
   Lê só arquivos publicados: camada de áreas urbanizadas, malha municipal e tabela de fração urbana por município.
   Passar o cursor mostra a fração urbana do município; clicar abre a página municipal. */
(function () {
  'use strict';
  const box = document.getElementById('mapaUrb');
  if (!box || typeof L === 'undefined') return;
  // mesma regra de slug do gerador (scripts/build_web_municipios.py)
  const slug = (s) => s.normalize('NFKD').replace(/[^\x00-\x7F]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const pct = (v) => (v == null ? '—' : (100 * v).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' %');

  Promise.all([
    fetch('data/downloads/openlux_areas_urbanizadas_rj_2019.geojson').then((r) => r.json()),
    fetch('data/municipios.geojson').then((r) => r.json()),
    fetch('data/downloads/openlux_area_urbana_municipio_2019.csv').then((r) => r.text()),
    fetch('data/downloads/openlux_ucs_rj_cnuc_2025_08_sem_nomes.geojson').then((r) => r.json()),
  ]).then(([urb, mun, csv, ucs]) => {
    const fracao = {};
    csv.trim().split('\n').slice(1).forEach((linha) => {
      const c = linha.split(',');
      fracao[c[0]] = { nome: c[1], f: Number(c[4]) };
    });

    const mapa = L.map(box, { attributionControl: true, scrollWheelZoom: false, minZoom: 6, maxZoom: 12 });
    mapa.attributionControl.setPrefix(false).addAttribution('Áreas urbanizadas: IBGE 2019 · Limites: IBGE, Malha 2024');
    const municipios = L.geoJSON(mun, {
      style: { fillColor: '#1b2540', fillOpacity: 0.9, color: 'rgba(255,255,255,.25)', weight: 0.5 },
      onEachFeature: (f, layer) => {
        const cd = f.properties.CD_MUN, info = fracao[cd];
        const nome = f.properties.NM_MUN;
        layer.bindTooltip(`${nome}<br>Área urbana: ${pct(info && info.f)} do município`, { sticky: true });
        layer.on('mouseover', () => layer.setStyle({ color: '#ffffff', weight: 1.2 }));
        layer.on('mouseout', () => municipios.resetStyle(layer));
        layer.on('click', () => { location.href = 'municipio/' + slug(nome) + '.html'; });
      },
    }).addTo(mapa);
    const camadaUrb = L.geoJSON(urb, {
      interactive: false,
      style: { fillColor: '#ffd166', fillOpacity: 0.85, color: 'none', weight: 0 },
    }).addTo(mapa);
    // unidades de conservação (CNUC 2025-08, sem nomes): contorno, por baixo das áreas urbanizadas
    const camadaUc = L.geoJSON(ucs, {
      style: { fillColor: '#5fb37a', fillOpacity: 0.35, color: '#9fe3b5', weight: 0.8 },
      onEachFeature: (f, layer) => {
        const p = f.properties;
        layer.bindTooltip(`Unidade de conservação<br>${p.categoria} (${p.grupo})<br>Código CNUC ${p.cd_cnuc}`, { sticky: true });
      },
    }).addTo(mapa);
    camadaUc.bringToBack();
    const chk = document.getElementById('lyUc');
    if (chk) chk.addEventListener('change', (e) => { if (e.target.checked) camadaUc.addTo(mapa); else mapa.removeLayer(camadaUc); });
    mapa.fitBounds(municipios.getBounds(), { padding: [10, 10] });
    box.dataset.pronto = '1';
  }).catch((e) => {
    console.error(e);
    box.textContent = 'Não foi possível carregar o mapa das áreas urbanizadas.';
  });
})();
