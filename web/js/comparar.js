/* OpenLux — lente de comparação entre dois anos (município a município).
   Lê indicators_noaa20.json e indicators.json (o sensor escolhido define o conjunto) e municipios.geojson.
   Diferença absoluta = B − A. Variação percentual = 100 · (B/A − 1), só quando A ≥ piso declarado
   (meta.change_floor_nw_cm2_sr da janela completa do sensor). Nenhum número é digitado à mão. */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const fmtSinal = (v, d = 3) => (v == null || !isFinite(v) ? '—' : (v > 0 ? '+' : '') + nf(d).format(v));
  const fmtPct = (v) => (v == null || !isFinite(v) ? '—' : (v > 0 ? '+' : '') + nf(1).format(v) + ' %');
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const getJSON = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
  const SEQ = ['#2b2d42', '#5b4a2e', '#8f6b2a', '#c9962f', '#ffd66b'];
  const DIV = ['#2c5aa0', '#8fb3e0', '#5b6170', '#f3a35c', '#c8581c'];

  const params = new URLSearchParams(location.search);

  Promise.all([
    getJSON('data/indicators_noaa20.json'),
    getJSON('data/indicators.json'),
    getJSON('data/municipios.geojson'),
  ]).then(([N, S, geo]) => {
    const D = { noaa20: N, snpp: S };
    const estado = { noaa20: 'NOAA-20', snpp: 'S-NPP' };
    const sens0 = params.get('s') === 'snpp' ? 'snpp' : 'noaa20';
    $('sensor').value = sens0;

    const valor = (sk, cd, y) => {
      const d = D[sk], i = d.meta.years.indexOf(y);
      const v = d.municipios[cd] && i >= 0 ? d.municipios[cd].mean[i] : null;
      return v == null || !isFinite(v) ? null : v;
    };
    const codigos = () => Object.keys(N.municipios).sort((a, b) => N.municipios[a].name.localeCompare(N.municipios[b].name, 'pt-BR'));
    const media = (sk, y) => { const xs = codigos().map((c) => valor(sk, c, y)).filter((v) => v != null); return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null; };

    function preencherAnos(sk) {
      const anos = D[sk].meta.years;
      const a = $('ano-a'), b = $('ano-b');
      const oa = Number(params.get('a')), ob = Number(params.get('b'));
      const padraoA = anos.includes(oa) ? oa : anos[0];
      const padraoB = anos.includes(ob) ? ob : anos[anos.length - 1];
      a.innerHTML = anos.map((y) => `<option value="${y}">${y}</option>`).join('');
      b.innerHTML = anos.map((y) => `<option value="${y}">${y}</option>`).join('');
      a.value = padraoA; b.value = padraoB;
    }

    function atualizar() {
      const sk = $('sensor').value;
      const A = Number($('ano-a').value), B = Number($('ano-b').value);
      $('aviso-sensor').hidden = sk !== 'snpp';
      $('aviso-sensor').textContent = sk === 'snpp'
        ? 'S-NPP: a partir de 2022 há piso de ruído em áreas escuras. Diferenças nesses anos não devem ser lidas como mudança real de iluminação.'
        : '';
      $('rot-a').textContent = `Ano ${A}`; $('rot-b').textContent = `Ano ${B}`;
      if (A === B) { $('nota-pct').textContent = 'Escolha dois anos diferentes para comparar.'; }

      // mesma escala de cores para os dois anos: quintis do conjunto (A e B)
      const pool = [];
      codigos().forEach((c) => [A, B].forEach((y) => { const v = valor(sk, c, y); if (v != null) pool.push(v); }));
      pool.sort((x, y) => x - y);
      const q = [0.2, 0.4, 0.6, 0.8].map((p) => pool[Math.floor(p * (pool.length - 1))]);
      const classe = (v) => { if (v == null) return -1; let k = 0; while (k < q.length && v > q[k]) k++; return k; };
      const bordas = [pool[0], ...q, pool[pool.length - 1]];
      $('legenda-escala').innerHTML = SEQ.map((c, k) => `<li><span class="swatch" style="background:${c}"></span>${fmt(bordas[k], 2)} a ${fmt(bordas[k + 1], 2)}</li>`).join('');

      const mapaPara = (y) => (cd) => { const c = classe(valor(sk, cd, y)); return c >= 0 ? SEQ[c] : '#3b3f4a'; };
      const titulo = (y) => (cd) => `${N.municipios[cd].name} (${y}): ${fmt(valor(sk, cd, y), 3)}`;
      const link = (cd) => `explorar.html?m=${encodeURIComponent(cd)}&s=${sk}&l=mun&y=${B}`;
      window.OpenLuxSvg.desenhaMapa($('mapa-b'), geo, { rotulo: `Mapa do ano ${B}`, link, cor: mapaPara(B), titulo: titulo(B) });
      window.OpenLuxSvg.desenhaMapa($('mapa-a'), geo, { rotulo: `Mapa do ano ${A}`, link, cor: mapaPara(A), titulo: titulo(A) });

      // diferença absoluta B − A, com classes simétricas: lo = mediana de |d|, hi = p90 de |d|
      const dif = {};
      codigos().forEach((c) => { const a = valor(sk, c, A), b = valor(sk, c, B); if (a != null && b != null) dif[c] = b - a; });
      const abs = Object.values(dif).map(Math.abs).sort((x, y) => x - y);
      const lo = abs.length ? abs[Math.floor(0.5 * (abs.length - 1))] : 0;
      const hi = abs.length ? abs[Math.floor(0.9 * (abs.length - 1))] : 0;
      const classeDif = (d) => { if (d == null) return -1; if (d < -hi) return 0; if (d < -lo) return 1; if (d <= lo) return 2; if (d <= hi) return 3; return 4; };
      $('legenda-dif').innerHTML = [
        `<li><span class="swatch" style="background:${DIV[0]}"></span>queda acima de ${fmtSinal(hi, 2)}</li>`,
        `<li><span class="swatch" style="background:${DIV[1]}"></span>queda até ${fmtSinal(lo, 2)}</li>`,
        `<li><span class="swatch" style="background:${DIV[2]}"></span>variação até ${fmt(lo, 2)} (mediana)</li>`,
        `<li><span class="swatch" style="background:${DIV[3]}"></span>aumento até ${fmtSinal(hi, 2)}</li>`,
        `<li><span class="swatch" style="background:${DIV[4]}"></span>aumento acima de ${fmtSinal(hi, 2)}</li>`,
      ].join('');
      window.OpenLuxSvg.desenhaMapa($('mapa-dif'), geo, {
        rotulo: `Diferença absoluta entre ${B} e ${A}`,
        link,
        cor: (cd) => { const k = classeDif(dif[cd]); return k >= 0 ? DIV[k] : '#3b3f4a'; },
        titulo: (cd) => `${N.municipios[cd].name}: ${fmtSinal(dif[cd], 3)} nW·cm⁻²·sr⁻¹`,
      });

      // estado: médias, diferença e variação percentual
      const mA = media(sk, A), mB = media(sk, B);
      $('k-a').textContent = fmt(mA, 3) + ' nW·cm⁻²·sr⁻¹';
      $('k-b').textContent = fmt(mB, 3) + ' nW·cm⁻²·sr⁻¹';
      $('k-dif').textContent = fmtSinal(mB - mA, 3) + ' nW·cm⁻²·sr⁻¹';
      $('k-pct').textContent = fmtPct(mA ? 100 * (mB / mA - 1) : null);

      // variação percentual por município, com piso da janela completa do sensor
      const janela = Object.keys(D[sk].meta.change_floor_nw_cm2_sr || {}).sort().pop();
      const piso = (D[sk].meta.change_floor_nw_cm2_sr || {})[janela];
      $('nota-pct').textContent = piso == null
        ? 'Variação percentual indisponível: o piso de linha de base não está declarado.'
        : `Variação percentual só para municípios com ano A ≥ ${fmt(piso, 3)} nW·cm⁻²·sr⁻¹ (piso da janela ${janela} de ${estado[sk]}).`;
      const pct = codigos().map((c) => { const a = valor(sk, c, A), b = valor(sk, c, B); return a != null && b != null && piso != null && a >= piso ? { c, p: 100 * (b / a - 1), d: dif[c] } : null; }).filter(Boolean);

      const ord = codigos().filter((c) => dif[c] != null).sort((x, y) => dif[y] - dif[x]);
      lista($('subidas'), ord.slice(0, 5), dif, pct, link);
      lista($('quedas'), ord.slice(-5).reverse(), dif, pct, link);

      // URL compartilhável com o estado da comparação
      const u = new URL(location.href);
      u.search = `?s=${sk}&a=${A}&b=${B}`;
      history.replaceState(null, '', u.search);
    }

    function lista(ul, cds, dif, pct, link) {
      ul.innerHTML = '';
      cds.forEach((c) => {
        const p = pct.find((r) => r.c === c);
        const li = document.createElement('li');
        li.innerHTML = `<a href="${link(c)}">${esc(N.municipios[c].name)}</a> <span class="valor">${fmtSinal(dif[c], 3)}</span> <span class="valor">${p ? fmtPct(p.p) : '—'}</span>`;
        ul.appendChild(li);
      });
    }

    // controle deslizante: revela o ano B sobre o ano A
    const lente = $('lente');
    const aplicaLente = () => { $('mapa-a-wrap').style.clipPath = `inset(0 ${100 - Number(lente.value)}% 0 0)`; lente.setAttribute('aria-valuetext', `${lente.value} % do ano A`); };
    lente.addEventListener('input', aplicaLente);
    aplicaLente();

    preencherAnos(sens0);
    ['sensor'].forEach((id) => $(id).addEventListener('change', () => { preencherAnos($('sensor').value); atualizar(); }));
    ['ano-a', 'ano-b'].forEach((id) => $(id).addEventListener('change', atualizar));
    atualizar();
  }).catch((e) => {
    console.error(e);
    const aviso = document.createElement('p');
    aviso.className = 'erro'; aviso.setAttribute('role', 'alert');
    aviso.textContent = 'Não foi possível carregar os dados publicados. Tente recarregar a página.';
    document.querySelector('main').prepend(aviso);
  });
})();
