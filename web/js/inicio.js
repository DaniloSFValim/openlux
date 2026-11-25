/* OpenLux — página inicial: "Quanta luz tem o seu município?".
   Lê data/indicators_noaa20.json (sensor primário para análise: NOAA-20, VJ146A4, 2018–2025). Usa 2021 como ano de referência. */
(async function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 1) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const safe = (t) => String(t).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '').toLowerCase();
  const UNIT = 'nW·cm⁻²·sr⁻¹';
  const REF = 2021;
  const DOI = '10.5281/zenodo.24510755';

  let data;
  try {
    data = await fetch('data/indicators_noaa20.json').then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
  } catch (e) {
    $('vazio').innerHTML = '<p>Não foi possível carregar os dados. Sirva a pasta web/ por HTTP (por exemplo, python -m http.server).</p>';
    return;
  }

  const years = data.meta.years, M = data.municipios, ref = years.indexOf(REF);
  const codes = Object.keys(M).sort((a, b) => M[a].name.localeCompare(M[b].name, 'pt-BR'));
  const popVals = codes.map((c) => M[c].exposure.pop_radiance[ref]).filter((v) => v != null && isFinite(v));
  const estado = data.state.mean[ref];

  // seletor
  const sel = $('mun-escolha');
  codes.forEach((c) => { const o = document.createElement('option'); o.value = c; o.textContent = M[c].name; sel.appendChild(o); });

  // destaques: alguns municípios de referência, para começar sem escolher
  const destaques = ['Rio de Janeiro', 'Niterói', 'Angra dos Reis', 'Cantagalo'].filter((n) => codes.some((c) => M[c].name === n));
  $('destaques').innerHTML = destaques.map((n) => {
    const c = codes.find((k) => M[k].name === n);
    return `<button type="button" class="btn secundario" data-cod="${c}">${n}</button>`;
  }).join('');

  function percentil(v) {
    return Math.round(100 * popVals.filter((x) => x < v).length / popVals.length);
  }

  function textos(cod) {
    const m = M[cod], pop = m.exposure.pop_radiance[ref], area = m.mean[ref];
    const p = pop == null ? null : percentil(pop);
    const razao = area == null || !estado ? null : area / estado;
    return {
      nome: m.name,
      habitantes: m.population == null ? null : Math.round(m.population),
      pop, area, p, razao,
      txtPop: p == null ? 'Sem dado válido para este município.' : p === 0 ? 'Entre os menos iluminados do estado.' : `Mais iluminado que ${p}% dos municípios do estado.`,
      txtArea: razao == null ? 'Sem dado válido para este município.'
        : razao >= 1 ? `${fmt(razao)} vezes a média do estado (${fmt(estado)} ${UNIT}).`
        : `${fmt(100 * razao, 0)}% da média do estado (${fmt(estado)} ${UNIT}).`,
    };
  }

  /* Faixa com os 92 municípios: cada ponto é um município, pela luz onde as pessoas vivem em 2021. */
  function drawRanking(sel) {
    const box = $('faixa-ranking'), resumo = $('ranking-resumo');
    if (!box) return;
    const W = 1000, H = 150, L = 30, R = 30, base = H - 34;
    const vals = codes.map((c) => ({ c, v: M[c].exposure.pop_radiance[ref] })).filter((r) => r.v != null);
    const max = Math.max(...vals.map((r) => r.v)) * 1.03;
    const x = (v) => L + (v / max) * (W - L - R);
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', `Pontos dos ${vals.length} municípios pela luz onde as pessoas vivem em 2021. ${sel && M[sel] ? 'Destacado: ' + M[sel].name + '.' : ''}`);
    [0, 20, 40, 60, 80].filter((t) => t <= max).forEach((t) => {
      const tx = document.createElementNS(ns, 'text');
      tx.setAttribute('x', x(t)); tx.setAttribute('y', base + 18); tx.setAttribute('text-anchor', 'middle');
      tx.setAttribute('class', 'eixo'); tx.textContent = String(t);
      svg.appendChild(tx);
      const ln = document.createElementNS(ns, 'line');
      ln.setAttribute('x1', x(t)); ln.setAttribute('x2', x(t)); ln.setAttribute('y1', 16); ln.setAttribute('y2', base);
      ln.setAttribute('stroke', '#d5dae1'); svg.appendChild(ln);
    });
    vals.forEach((r, i) => {
      const cc = document.createElementNS(ns, 'circle');
      const isSel = r.c === sel;
      cc.setAttribute('cx', x(r.v)); cc.setAttribute('cy', 22 + (i % 5) * 24);
      cc.setAttribute('r', isSel ? 9 : 5);
      cc.setAttribute('tabindex', '-1');
      if (isSel) cc.setAttribute('class', 'sel');
      const t = document.createElementNS(ns, 'title'); t.textContent = `${M[r.c].name}: ${fmt(r.v)} ${UNIT}`;
      cc.appendChild(t);
      cc.addEventListener('click', () => render(r.c));
      svg.appendChild(cc);
    });
    if (sel && M[sel] && M[sel].exposure.pop_radiance[ref] != null) {
      const v = M[sel].exposure.pop_radiance[ref], xs = x(v);
      const tl = document.createElementNS(ns, 'text');
      tl.setAttribute('class', 'rotulo-sel');
      tl.setAttribute('x', xs); tl.setAttribute('y', 8);
      tl.setAttribute('text-anchor', xs > W * 0.7 ? 'end' : 'start');
      tl.textContent = M[sel].name;
      svg.appendChild(tl);
    }
    box.textContent = ''; box.appendChild(svg);
    if (resumo) {
      if (sel && M[sel] && M[sel].exposure.pop_radiance[ref] != null) {
        const v = M[sel].exposure.pop_radiance[ref];
        const abaixo = vals.filter((r) => r.v < v).length, acima = vals.filter((r) => r.v > v).length;
        resumo.textContent = `${M[sel].name}: ${abaixo} municípios têm menos luz onde as pessoas vivem e ${acima} têm mais (2021).`;
      } else resumo.textContent = '';
    }
  }

  function urlMun(cod) { return `${location.origin}${location.pathname}?m=${cod}`; }

  function render(cod) {
    if (!cod || !M[cod]) { $('resultado').hidden = true; $('vazio').hidden = false; $('copiar-escolha').hidden = true; return; }
    const t = textos(cod), m = M[cod];
    $('resultado').hidden = false; $('vazio').hidden = true; $('copiar-escolha').hidden = false;
    sel.value = cod;
    $('nome-mun').textContent = t.nome;
    $('pop-mun').textContent = t.habitantes == null ? '' : `${nf(0).format(t.habitantes)} habitantes (Censo 2022)`;
    $('num-pop').textContent = `${fmt(t.pop)} ${UNIT}`;
    $('txt-pop').textContent = t.txtPop;
    $('num-area').textContent = `${fmt(t.area)} ${UNIT}`;
    $('txt-area').textContent = t.txtArea;
    OpenLuxCharts.lineChart($('grafico-mun'), {
      title: `Radiância média anual, ${t.nome}`, years, yLabel: UNIT, digits: 1,
      series: [{ name: t.nome, values: m.mean, color: '#0072B2' }, { name: 'Estado (média ponderada)', values: data.state.mean, color: '#7a828c', dash: '5 4', width: 1.6 }],
      exportName: 'grafico-' + safe(t.nome), exportNotes: ['Fonte: OpenLux, doi:' + DOI + ' · NASA Black Marble (VJ146A4, NOAA-20).', 'Resultados não validados. Diferenças entre anos não são mudança real de iluminação sem essa ressalva.'],
    });
    drawRanking(cod);
    const u = urlMun(cod);
    history.replaceState(null, '', `?m=${cod}`);
    $('whatsapp').href = 'https://wa.me/?text=' + encodeURIComponent(
      `Quanta luz tem ${t.nome}? Em 2021, a luz onde as pessoas vivem foi ${fmt(t.pop)} ${UNIT}, mais que ${t.p}% dos municípios do RJ (estimativa por satélite). ${u}`);
    $('status-compartilhar').textContent = '';
  }

  function quebra(ctx, texto, x, y, larg, linha) {
    const palavras = texto.split(' '); let atual = '', yy = y;
    palavras.forEach((p) => {
      const teste = atual ? atual + ' ' + p : p;
      if (ctx.measureText(teste).width > larg && atual) { ctx.fillText(atual, x, yy); atual = p; yy += linha; }
      else atual = teste;
    });
    if (atual) ctx.fillText(atual, x, yy);
    return yy;
  }

  function baixarCartao(cod) {
    const t = textos(cod), W = 1200, H = 630, c = document.createElement('canvas');
    c.width = W; c.height = H;
    const ctx = c.getContext('2d');
    const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#0b1020'); g.addColorStop(1, '#1d3557');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#ffd166'; ctx.font = '600 28px system-ui, Arial, sans-serif';
    ctx.fillText('OpenLux · Rio de Janeiro', 64, 84);
    ctx.fillStyle = '#ffffff'; ctx.font = '700 60px system-ui, Arial, sans-serif';
    quebra(ctx, `Quanta luz tem ${t.nome}?`, 64, 170, W - 128, 70);
    ctx.fillStyle = '#ffd166'; ctx.font = '700 120px system-ui, Arial, sans-serif';
    ctx.fillText(fmt(t.pop), 64, 340);
    ctx.fillStyle = '#e6edf7'; ctx.font = '400 30px system-ui, Arial, sans-serif';
    quebra(ctx, `${UNIT} de luz onde as pessoas vivem (2021). ${t.txtPop}`, 64, 390, W - 128, 40);
    ctx.fillStyle = '#9fb3c8'; ctx.font = '400 24px system-ui, Arial, sans-serif';
    quebra(ctx, `Média na área do município: ${fmt(t.area)} ${UNIT}. ${t.txtArea}`, 64, 480, W - 128, 34);
    ctx.font = '400 20px system-ui, Arial, sans-serif';
    quebra(ctx, `Estimativa por satélite (NASA Black Marble, NOAA-20; IBGE). Não é medição do céu. Não validado em campo. doi:${DOI}`, 64, 575, W - 128, 28);
    c.toBlob((blob) => {
      if (!blob) return;
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'cartao-' + safe(t.nome) + '.png';
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    }, 'image/png');
  }

  async function copiarLink(cod, msg) {
    const u = urlMun(cod);
    try { await navigator.clipboard.writeText(u); msg.textContent = 'Link copiado.'; }
    catch (e) { msg.textContent = 'Não foi possível copiar automaticamente. O endereço da barra já contém este município.'; }
  }

  sel.addEventListener('change', () => render(sel.value));
  document.querySelectorAll('#destaques [data-cod]').forEach((b) => b.addEventListener('click', () => render(b.dataset.cod)));
  $('baixar-cartao').addEventListener('click', () => { if (sel.value) baixarCartao(sel.value); });
  $('copiar-link').addEventListener('click', () => { if (sel.value) copiarLink(sel.value, $('status-compartilhar')); });
  $('copiar-escolha').addEventListener('click', () => { if (sel.value) copiarLink(sel.value, $('busca-ajuda')); });
  $('ver-mapa').addEventListener('click', (e) => { e.currentTarget.href = `explorar.html?l=mun&i=mean&y=${REF}&s=snpp${sel.value ? '&m=' + sel.value : ''}`; });

  drawRanking('');
  const q = new URLSearchParams(location.search).get('m');
  render(q && M[q] ? q : '');
  if ($('updated')) $('updated').textContent = `Última atualização dos dados: ${new Date(data.meta.run.processed_utc).toLocaleDateString('pt-BR', { timeZone: 'UTC', day: '2-digit', month: 'long', year: 'numeric' })} (UTC). Dados não validados.`;
})();
