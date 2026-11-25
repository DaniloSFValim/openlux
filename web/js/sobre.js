/* OpenLux — página "Sobre e métodos": análises do estado e informações científicas.
   Lê data/indicators.json (saída real do pipeline). Não depende do mapa. */
(async function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const nfs = {};
  const fmt = (v, d = 2) => {
    if (v == null || !isFinite(v)) return '—';
    nfs[d] = nfs[d] || new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
    return nfs[d].format(v);
  };

  let data;
  try {
    data = await fetch('data/indicators.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
  } catch (e) {
    const msg = 'Não foi possível carregar os dados (data/indicators.json). Sirva a pasta web/ por HTTP.';
    ['state-content', 'info-content'].forEach((id) => { if ($(id)) $(id).textContent = msg; });
    return;
  }

  const meta = data.meta, years = meta.years, M = data.municipios;
  const codes = Object.keys(M).sort((a, b) => M[a].name.localeCompare(M[b].name, 'pt-BR'));
  const winKeys = Object.keys(meta.windows);
  const wLabel = (w) => `${meta.windows[w][0]}–${meta.windows[w][1]}`;
  const COL = ['#0072B2', '#E69F00', '#009E73', '#CC79A7'];
  const EXPORT_NOTES = ['Fonte: OpenLux 0.1.0, doi:10.5281/zenodo.24510755 · NASA Black Marble (VNP46A4, S-NPP) · malha e população: IBGE.',
    'Resultados não validados. O S-NPP tem mais ruído em áreas escuras desde 2022; não é mudança real de iluminação sem essa ressalva.'];

  /* ---------- estado ---------- */
  function renderState() {
    const cnt = winKeys.map((w) => {
      const t = codes.map((c) => M[c].trends[w]).filter((x) => x && x.slope != null);
      return `<tr><td>${wLabel(w)}</td><td class="num">${t.filter((x) => x.slope > 0).length}</td><td class="num">${t.filter((x) => x.slope < 0).length}</td><td class="num">${t.filter((x) => x.p_value < 0.05).length}</td></tr>`;
    }).join('');
    const sc = data.sensor_comparison, scRows = sc.years.map((y) => `<tr><td>${y}</td><td class="num">${fmt(sc.state_mean_a[y], 2)}</td><td class="num">${fmt(sc.state_mean_b[y], 2)}</td><td class="num">${fmt(sc.ratio_b_over_a[y], 3)}</td></tr>`).join('');
    const sens = Object.entries(data.sensitivity).map(([w, cfgs]) => Object.entries(cfgs).map(([c, v]) =>
      `<tr><td>${esc(w.replace('_', '–'))}</td><td>${esc(c)}</td><td class="num">${fmt(v.spearman_mean_end_year, 3)}</td><td class="num">${fmt(v.spearman_trend_slope, 3)}</td><td class="num">${fmt(v.trend_sign_agreement, 3)}</td></tr>`).join('')).join('');
    $('state-content').innerHTML = `
      <h3 style="margin:.2rem 0">Estado do Rio de Janeiro</h3>
      <div id="state-chart"></div>
      <p class="muted small">Média da radiância por município ponderada pela área válida de pixels. Série derivada de dados observados.</p>
      <h4>Controle de ruído de fundo (pixels persistentemente escuros)</h4>
      <div id="qa-chart"></div>
      <p class="muted small">Pixels com mediana zero em 2012–2021 (classe definida só por esses anos). Se a radiância média desses pixels sobe, o piso de ruído mudou. Isso não é crescimento de iluminação.</p>
      <h4>Fração da área iluminada (≥ limiar documentado): S-NPP × NOAA-20</h4>
      <div id="lit-chart"></div>
      <p class="muted small">Média estadual ponderada pela área válida. O limiar coincide com o valor em que o produto zera ruído de fundo, por isso o aumento do piso de ruído do S-NPP eleva esta fração.</p>
      ${data.sensor_municipal ? (() => { const sm = data.sensor_municipal, L = sm.levels_by_year, rows = Object.keys(L).map((y) => `<tr><td>${y}</td><td class="num">${fmt(L[y].spearman, 4)}</td><td class="num">${fmt(L[y].median_ratio_b_over_a, 3)}</td><td class="num">${fmt(L[y].median_abs_diff, 3)}</td></tr>`).join(''); const w = sm['2018_2025'], p = sm['2018_2021'];
        return `<h4>Comparação municipal entre sensores (92 municípios)</h4><div class="table-wrap"><table><thead><tr><th>Ano</th><th class="num">ρ (níveis)</th><th class="num">NOAA-20 / S-NPP</th><th class="num">|S-NPP − NOAA-20|</th></tr></thead><tbody>${rows}</tbody></table></div>
        <p class="small">Inclinações 2018–2021: ρ ${fmt(p.spearman_slopes, 2)}, mesmo sinal em ${fmt(100 * p.sign_agreement, 1)} %. Inclinações 2018–2025: ρ ${fmt(w.spearman_slopes, 2)}, mesmo sinal em ${fmt(100 * w.sign_agreement, 1)} %. Variação 2021→2025 (mediana): S-NPP ${fmt(w.median_change_a, 2)} e NOAA-20 ${fmt(w.median_change_b, 2)} nW·cm⁻²·sr⁻¹.</p>
        <p class="muted small">Até 2021 os sensores concordam em nível; a partir de 2022 o S-NPP lê mais alto. Ver docs/DECISIONS.md (seção 8).</p>`; })() : ''}
      <h4>Municípios por sinal da tendência</h4>
      <div class="table-wrap"><table><thead><tr><th>Janela</th><th class="num">Inclin. &gt; 0</th><th class="num">Inclin. &lt; 0</th><th class="num">p &lt; 0,05</th></tr></thead><tbody>${cnt}</tbody></table></div>
      <h4>Comparação entre sensores (média estadual, nW·cm⁻²·sr⁻¹)</h4>
      <div class="table-wrap"><table><thead><tr><th>Ano</th><th class="num">S-NPP</th><th class="num">NOAA-20</th><th class="num">NOAA-20 / S-NPP</th></tr></thead><tbody>${scRows}</tbody></table></div>
      <p class="small">Concordância das inclinações municipais entre sensores (${sc.years[0]}–${sc.years.at(-1)}): Spearman ${fmt(sc.spearman_trend_slope, 2)}; mesmo sinal em ${fmt(100 * sc.trend_sign_agreement, 1)}% dos municípios.</p>
      <h4>Sensibilidade à configuração (em relação à principal)</h4>
      <div class="table-wrap"><table><thead><tr><th>Janela</th><th>Variação</th><th class="num">ρ média (ano final)</th><th class="num">ρ inclinação</th><th class="num">Mesmo sinal</th></tr></thead><tbody>${sens}</tbody></table></div>`;
    OpenLuxCharts.lineChart($('state-chart'), { title: 'Radiância média estadual', years, yLabel: 'nW·cm⁻²·sr⁻¹', digits: 2, shadeFrom: 2022, shadeLabel: 'ruído S-NPP', series: [{ name: 'Estado (média ponderada)', values: data.state.mean, color: COL[0] }],
      exportName: 'grafico-estado-radiancia-media', exportNotes: EXPORT_NOTES });
    if (sc.state_lit_fraction_a) OpenLuxCharts.lineChart($('lit-chart'), { title: 'Fração da área iluminada, média estadual', years: sc.years, yLabel: 'fração', digits: 3, shadeFrom: 2022, shadeLabel: 'ruído S-NPP', zeroBase: true,
      series: [{ name: 'S-NPP', values: sc.years.map((y) => sc.state_lit_fraction_a[y]), color: COL[0] }, { name: 'NOAA-20', values: sc.years.map((y) => sc.state_lit_fraction_b[y]), color: COL[1] }] });
    OpenLuxCharts.lineChart($('qa-chart'), { title: 'Radiância média de pixels persistentemente escuros', years: data.qa.map((r) => r.year), yLabel: 'nW·cm⁻²·sr⁻¹', digits: 3, shadeFrom: 2022, shadeLabel: 'após 2021', zeroBase: true,
      series: [{ name: 'Terra', values: data.qa.map((r) => r.dark_land_mean), color: COL[1] }, { name: 'Mar', values: data.qa.map((r) => r.dark_sea_mean), color: COL[0] }] });
  }

  /* ---------- informações científicas ---------- */
  function renderInfo() {
    const lowValid = codes.filter((c) => M[c].valid.some((v) => v != null && v < 0.9)).map((c) => M[c].name);
    const src = meta.sources.map((s) => `<tr><td><a href="${esc(s.url)}" rel="noopener">${esc(s.name)}</a>${s.doi ? `<br><span class="small">DOI: <a href="https://doi.org/${esc(s.doi)}" rel="noopener">${esc(s.doi)}</a></span>` : ''}</td><td>${esc(s.institution)}</td><td>${esc(s.version)}</td><td>${esc(s.license)} <strong>[${({ confirmado: 'confirmado', confirmado_com_ressalva: 'confirmado com ressalva', nao_confirmado: 'não confirmado' })[s.license_status]}]</strong></td></tr>`).join('');
    const docs = meta.documents.map((d) => `<li><a href="${esc(d.url)}" rel="noopener">${esc(d.name)}</a> (${esc(d.institution)})</li>`).join('');
    const refs = meta.references.map((r) => `<li>${esc(r.cite)} <a href="https://doi.org/${esc(r.doi)}" rel="noopener">doi:${esc(r.doi)}</a></li>`).join('');
    const hashes = Object.entries(meta.run.output_sha256).map(([k, v]) => `<tr><td>${esc(k)}</td><td><code>${esc(v)}</code></td></tr>`).join('');
    $('info-content').innerHTML = `
      <details open><summary>Metodologia (resumo)</summary>
        <p>Produto: NASA Black Marble VNP46A4 v2.0 (radiância noturna anual, grade de 15 arc-s ≈ 460 m), camada <code>AllAngle_Composite_Snow_Free</code>. São mantidos pixels de qualidade 0 (boa), sobre terra (códigos 0, 1 e 5 da máscara terra/água), sem valores de preenchimento ou negativos. Não há reamostragem.</p>
        <p><strong>Radiância média</strong> do município: L̄ = Σ wᵢ·Lᵢ / Σ wᵢ, onde wᵢ é a fração da área do pixel coberta pelo município (cobertura fracionária) e Lᵢ é a radiância (nW·cm⁻²·sr⁻¹) dos pixels válidos. A mediana é ponderada pelos mesmos pesos.</p>
        <p><strong>Intensidade radiante aparente</strong>: S = Σ wᵢ·Lᵢ·Aᵢ (nW·sr⁻¹), com Aᵢ a área elipsoidal (WGS84) do pixel. É uma intensidade na direção observada pelo sensor, <em>não</em> a emissão luminosa total do município. A soma bruta de pixels não é usada.</p>
        <p><strong>Fração da área iluminada</strong>: F(τ) = Σ wᵢ·[Lᵢ ≥ τ] / Σ wᵢ sobre os pixels válidos, com τ = ${fmt((meta.thresholds_nw_cm2_sr || {}).lit_0p5, 1)} nW·cm⁻²·sr⁻¹ (valor abaixo do qual o produto zera ruído de fundo; guia do usuário, seção 2.3). Limiares analíticos adicionais (quantis da radiância dos pixels iluminados no ano de referência) constam em <code>run_record.json</code>.</p>
        <p><strong>Por habitante</strong>: S / população residente (Censo 2022), somente para 2022, em mW·sr⁻¹ por habitante; é um índice relativo.</p>
        <p><strong>Tendência</strong>: inclinação de Theil–Sen e teste de Kendall sobre a radiância média anual, com mínimo de 8 anos válidos, em duas janelas (${winKeys.map(wLabel).join(' e ')}). <strong>Variação percentual</strong>: definida só com linha de base ≥ piso (${winKeys.map((w) => `${wLabel(w)}: ${fmt(meta.change_floor_nw_cm2_sr[w], 2)}`).join('; ')} nW·cm⁻²·sr⁻¹; percentil 25 das médias municipais).</p>
        <p><strong>Classes de cor</strong> são classificações analíticas (quantis ou limites em torno de zero), não limiares físicos nem categorias oficiais de poluição luminosa.</p>
        <p>Análise de sensibilidade: qualidade 0+1, camada near-nadir, e mínimo de 5 e 10 observações (aba Estado). Detalhes das decisões: <code>docs/DECISIONS.md</code> no repositório.</p>
      </details>
      <details><summary>Fontes de dados</summary>
        <div class="table-wrap"><table><thead><tr><th>Fonte</th><th>Instituição</th><th>Versão / cobertura</th><th>Licença / termos</th></tr></thead><tbody>${src}</tbody></table></div>
        <p class="small">Documentação técnica:</p><ul class="small">${docs}</ul>
      </details>
      <details><summary>Referências</summary><ul>${refs}</ul><p class="small muted">Lista restrita a trabalhos com DOI verificado em fontes institucionais ou nas buscas desta pesquisa.</p></details>
      <details open><summary>Limitações</summary><ul>
        <li><strong>Estimativa, não medição:</strong> a radiância orbital (VIIRS Day/Night Band) não equivale ao brilho do céu observado na superfície; não há medições fotométricas de campo.</li>
        <li><strong>Resolução:</strong> pixel de ~460 m; municípios pequenos têm poucas centenas de pixels.</li>
        <li><strong>Sensibilidade espectral:</strong> a banda DNB é pouco sensível à emissão azul de LEDs, o que pode subestimar áreas convertidas para LED (Levin et al., 2020).</li>
        <li><strong>Piso de ruído do S-NPP a partir de 2022</strong> (aviso no topo) e <strong>componente comum aos dois sensores</strong> não separado de um possível artefato do algoritmo compartilhado. A saturação em áreas muito iluminadas não foi avaliada neste trabalho.</li>
        <li><strong>Janela de tendência:</strong> o sinal depende da janela (${winKeys.map(wLabel).join(' vs ')}).</li>
        <li><strong>Máscara de água:</strong> mar e lagoas são excluídos; municípios com menos de 90% de área válida em algum ano: ${esc(lowValid.join(', ') || 'nenhum')}.</li>
        <li><strong>População:</strong> população residente não é população exposta; a intensidade por habitante é um índice relativo, só para 2022.</li>
        <li><strong>Malha:</strong> a malha SIRGAS 2000 foi tratada como WGS84 (diferença de poucos metros, menor que o pixel); a geometria exibida foi simplificada só para visualização, e os cálculos usaram a geometria completa.</li>
        <li><strong>Cartografia:</strong> projeção de exibição Web Mercator; a barra de escala é aproximada para a latitude do estado.</li>
      </ul></details>
      <details><summary>Proveniência desta execução</summary>
        <p class="small">Processado em ${esc(meta.run.processed_utc)} · commit do código: <code>${esc((meta.run.code_commit || '').slice(0, 12))}</code>${meta.run.code_dirty ? ' (com alterações não commitadas)' : ''}.</p>
        <div class="table-wrap"><table><thead><tr><th>Arquivo de saída</th><th>SHA-256</th></tr></thead><tbody>${hashes}</tbody></table></div>
      </details>`;
    const d = new Date(meta.run.processed_utc);
    $('updated').textContent = `Última atualização dos dados: ${d.toLocaleDateString('pt-BR', { timeZone: 'UTC', day: '2-digit', month: 'long', year: 'numeric' })} (UTC). Dados não validados.`;
  }


  renderState();
  renderInfo();
})();
