/* OpenLux — laboratório de análises (municipal).
   Lê indicators_noaa20.json e indicators.json. Todas as estatísticas são calculadas aqui:
   - média, mediana e fração iluminada: campos anuais publicados pelo pipeline;
   - posição e percentil: ordenação dos 92 municípios no ano escolhido (percentil = % de municípios com valor menor ou igual);
   - quartis e mínimo/máximo do estado: sobre a média de cada município (cada município pesa igual);
   - tendência (Theil–Sen) e p-valor (Kendall): campos publicados em trends[janela completa]. */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const fmtSinal = (v, d = 3) => (v == null || !isFinite(v) ? '—' : (v > 0 ? '+' : '') + nf(d).format(v));
  const fmtPct = (v) => (v == null || !isFinite(v) ? '—' : (v > 0 ? '+' : '') + nf(1).format(v) + ' %');
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const getJSON = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
  const params = new URLSearchParams(location.search);

  // quantil com interpolação linear (mesma regra do explorador)
  function quantil(arr, p) {
    const a = arr.filter((v) => v != null && isFinite(v)).sort((x, y) => x - y);
    if (!a.length) return NaN;
    const i = (a.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
    return a[lo] + (a[hi] - a[lo]) * (i - lo);
  }

  Promise.all([getJSON('data/indicators_noaa20.json'), getJSON('data/indicators.json')]).then(([N, S]) => {
    const D = { noaa20: N, snpp: S };
    const sk0 = params.get('s') === 'snpp' ? 'snpp' : 'noaa20';
    const codigos = Object.keys(N.municipios).sort((a, b) => N.municipios[a].name.localeCompare(N.municipios[b].name, 'pt-BR'));
    const nomes = (cd) => N.municipios[cd].name;

    $('sensor').value = sk0;
    const valor = (sk, cd, y, campo = 'mean') => {
      const d = D[sk], i = d.meta.years.indexOf(y);
      const v = d.municipios[cd] && i >= 0 ? d.municipios[cd][campo][i] : null;
      return v == null || !isFinite(v) ? null : v;
    };
    const janelaCompleta = (sk) => { const ks = Object.keys(D[sk].meta.windows).sort(); return ks[ks.length - 1]; };

    function montarSeletores(sk) {
      const anos = D[sk].meta.years;
      const ano = $('ano');
      const padrao = Number(params.get('y'));
      ano.innerHTML = anos.map((y) => `<option value="${y}">${y}</option>`).join('');
      ano.value = anos.includes(padrao) ? padrao : anos[anos.length - 1];
      ['mun-1', 'mun-2', 'mun-3'].forEach((id, k) => {
        const sel = $(id);
        const pre = (params.get('m') || '').split(',')[k] || (k === 0 ? '3304557' : '');   // Rio de Janeiro por padrão
        sel.innerHTML = (k === 0 ? '' : '<option value="">— nenhum —</option>') + codigos.map((c) => `<option value="${c}">${esc(nomes(c))}</option>`).join('');
        sel.value = codigos.includes(pre) ? pre : '';
      });
    }

    function selecionados() {
      return ['mun-1', 'mun-2', 'mun-3'].map((id) => $(id).value).filter((c, i, arr) => c && arr.indexOf(c) === i);
    }

    function atualizar() {
      const sk = $('sensor').value, Y = Number($('ano').value);
      const janela = janelaCompleta(sk);
      $('aviso-sensor').hidden = sk !== 'snpp';
      $('aviso-sensor').textContent = sk === 'snpp'
        ? 'S-NPP: a partir de 2022 há piso de ruído em áreas escuras. Valores desses anos não devem ser lidos como mudança real de iluminação.'
        : '';
      $('ano-comp').textContent = Y; $('ano-dist').textContent = Y;
      const sel = selecionados();
      const anos = D[sk].meta.years;

      // valores do estado e posições no ano escolhido
      const medias = codigos.map((c) => valor(sk, c, Y)).filter((v) => v != null);
      const meanEstado = medias.reduce((a, b) => a + b, 0) / medias.length;
      const q25 = quantil(medias, 0.25), q50 = quantil(medias, 0.5), q75 = quantil(medias, 0.75);
      const ordem = codigos.filter((c) => valor(sk, c, Y) != null).sort((a, b) => valor(sk, b, Y) - valor(sk, a, Y));
      const posicao = (cd) => ordem.indexOf(cd) + 1;
      const percentil = (cd) => Math.round(100 * medias.filter((v) => v <= valor(sk, cd, Y)).length / medias.length);

      // tabela comparativa
      const cab = '<tr><th scope="col">Município</th><th scope="col">Média</th><th scope="col">Mediana dos pixels</th><th scope="col">Fração ≥ 0,5</th><th scope="col">Posição (1 = maior)</th><th scope="col">Percentil</th><th scope="col">Tendência (Theil–Sen)</th><th scope="col">p (Kendall)</th><th scope="col">Variação % (janela ' + janela + ')</th></tr>';
      const linhas = sel.map((cd) => {
        const tr = (D[sk].municipios[cd].trends || {})[janela] || {};
        return `<tr><th scope="row">${esc(nomes(cd))}</th><td>${fmt(valor(sk, cd, Y), 3)}</td><td>${fmt(valor(sk, cd, Y, 'median'), 3)}</td><td>${fmt(valor(sk, cd, Y, 'lit'), 3)}</td><td>${posicao(cd)}º de ${ordem.length}</td><td>${percentil(cd)}</td><td>${fmtSinal(tr.slope, 3)}</td><td>${fmt(tr.p_value, 3)}</td><td>${fmtPct(tr.change_pct)}</td></tr>`;
      }).join('');
      const estado = `<tr class="estado"><th scope="row">Estado (92 municípios)</th><td>${fmt(meanEstado, 3)}</td><td>${fmt(q50, 3)} (mediana dos municípios)</td><td>—</td><td>—</td><td>P25 ${fmt(q25, 3)} · P75 ${fmt(q75, 3)}</td><td>—</td><td>—</td><td>—</td></tr>`;
      $('tabela-comp').innerHTML = `<table><caption>Ano ${Y}, ${esc(D[sk] === N ? 'NOAA-20' : 'S-NPP')}. Média, mediana e fração em nW·cm⁻²·sr⁻¹ (fração adimensional).</caption><thead>${cab}</thead><tbody>${linhas || '<tr><td colspan="9">Escolha pelo menos um município.</td></tr>'}${estado}</tbody></table>`;

      // evolução: municípios escolhidos e média estadual tracejada
      const estadoAnual = anos.map((y) => { const xs = codigos.map((c) => valor(sk, c, y)).filter((v) => v != null); return xs.reduce((a, b) => a + b, 0) / xs.length; });
      const series = sel.map((cd, k) => ({ valores: anos.map((y) => valor(sk, cd, y)), classe: ['serie-noaa', 'serie-snpp', 'serie-cor3'][k] || 'serie-noaa' }));
      series.push({ valores: estadoAnual, classe: 'serie-estado', tracejado: true });
      window.OpenLuxGraficos.linhas($('grafico-evolucao'), anos, series, { rotulo: 'Evolução anual dos municípios escolhidos e da média estadual' });

      // distribuição: histograma e caixa com os municípios escolhidos
      const lo = Math.min(...medias), hi = Math.max(...medias);
      window.OpenLuxGraficos.histograma($('grafico-distribuicao'), medias, lo, hi, { rotulo: 'Histograma da distribuição municipal' });
      caixa($('grafico-distribuicao'), medias, sel.map((cd) => valor(sk, cd, Y)), lo, hi);

      // tendências: significativas (p < 0,05), ordenadas pela inclinação
      const tend = codigos.map((c) => { const t = (D[sk].municipios[c].trends || {})[janela]; return t && t.p_value != null && t.p_value < 0.05 ? { c, s: t.slope, p: t.p_value } : null; }).filter(Boolean);
      tend.sort((a, b) => b.s - a.s);
      const sub = tend.filter((r) => r.s > 0).slice(0, 10), que = tend.filter((r) => r.s < 0).slice(-10).reverse();
      const lista = (ul, arr) => { ul.innerHTML = ''; arr.forEach((r) => { const li = document.createElement('li'); li.innerHTML = `<a href="explorar.html?m=${encodeURIComponent(r.c)}&s=${sk}&l=mun&y=${Y}">${esc(nomes(r.c))}</a> <span class="valor">${fmtSinal(r.s, 3)} por ano · p = ${fmt(r.p, 3)}</span>`; ul.appendChild(li); }); if (!arr.length) ul.innerHTML = '<li>Nenhum município neste grupo.</li>'; };
      lista($('tend-subidas'), sub); lista($('tend-quedas'), que);
      $('tend-resumo').textContent = `${tend.length} de ${codigos.length} municípios com tendência significativa (p < 0,05) na janela ${janela}. Os demais não mostram tendência distinguível de zero nessa série.`;

      // URL compartilhável com o estado do laboratório
      const u = new URL(location.href);
      u.search = `?s=${sk}&y=${Y}&m=${sel.join(',')}`;
      history.replaceState(null, '', u.search);
    }

    // caixa horizontal: P25–P75, mediana, mínimo e máximo do estado; pontos dourados = municípios escolhidos
    function caixa(container, vals, marcados, lo, hi) {
      const W = 760, H = 110, pad = { l: 40, r: 16 };
      const x = (v) => pad.l + ((v - lo) / (hi - lo)) * (W - pad.l - pad.r);
      const NS = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(NS, 'svg');
      svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('width', '100%'); svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Caixa da distribuição municipal');
      const add = (tag, attrs) => { const n = document.createElementNS(NS, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); svg.appendChild(n); return n; };
      const q1 = quantil(vals, 0.25), md = quantil(vals, 0.5), q3 = quantil(vals, 0.75);
      const mn = Math.min(...vals), mx = Math.max(...vals), yc = 40;
      add('line', { x1: x(mn), x2: x(q1), y1: yc, y2: yc, class: 'grade' });
      add('line', { x1: x(q3), x2: x(mx), y1: yc, y2: yc, class: 'grade' });
      add('rect', { x: x(q1), y: yc - 14, width: x(q3) - x(q1), height: 28, class: 'caixa-box' });
      add('line', { x1: x(md), x2: x(md), y1: yc - 14, y2: yc + 14, class: 'serie-noaa' });
      marcados.filter((v) => v != null).forEach((v) => add('circle', { cx: x(v), cy: yc + 34, r: 5, class: 'serie-noaa-p' }));
      const t = document.createElementNS(NS, 'text'); t.setAttribute('x', pad.l); t.setAttribute('y', H - 6); t.setAttribute('class', 'eixo'); t.textContent = `${fmt(lo, 2)} a ${fmt(hi, 2)} nW·cm⁻²·sr⁻¹`; svg.appendChild(t);
      const holder = document.createElement('div'); holder.className = 'caixa-holder';
      holder.appendChild(svg);
      container.appendChild(holder);
    }

    ['sensor'].forEach((id) => $(id).addEventListener('change', () => { montarSeletores($('sensor').value); atualizar(); }));
    ['ano', 'mun-1', 'mun-2', 'mun-3'].forEach((id) => $(id).addEventListener('change', atualizar));
    montarSeletores(sk0);
    atualizar();
  }).catch((e) => {
    console.error(e);
    const aviso = document.createElement('p');
    aviso.className = 'erro'; aviso.setAttribute('role', 'alert');
    aviso.textContent = 'Não foi possível carregar os dados publicados. Tente recarregar a página.';
    document.querySelector('main').prepend(aviso);
  });
})();
