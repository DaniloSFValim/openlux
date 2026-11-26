/* OpenLux — página principal (base visual do protótipo). Lê só os arquivos publicados em data/:
   indicators_noaa20.json (padrão) ou indicators.json (S-NPP, ?s=snpp) e municipios.geojson.
   Cores em quantis dos próprios valores do sensor escolhido (mesma escala em todos os anos). */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const $ = (id) => document.getElementById(id);
  const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (v, d = 2) => (v == null || !isFinite(v) ? '—' : nf(d).format(v));
  const COR = ['#0b1530', '#2b2a5e', '#7a3d7c', '#e0604f', '#ffb347', '#fff4c2'];
  const params = new URLSearchParams(location.search);
  const ARQ = { noaa20: 'data/indicators_noaa20.json', snpp: 'data/indicators.json' };

  function el(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function walk(coords, fn) { if (typeof coords[0] === 'number') return fn(coords); coords.forEach((c) => walk(c, fn)); }

  Promise.all([fetch(ARQ.noaa20).then((r) => r.json()), fetch(ARQ.snpp).then((r) => r.json()), fetch('data/municipios.geojson').then((r) => r.json())])
    .then(([N, S, geo]) => {
      const DADOS = { noaa20: N, snpp: S };
      let sk = params.get('s') === 'snpp' ? 'snpp' : 'noaa20';
      let D = DADOS[sk];
      let anos = D.meta.years;
      let ano = anos.length - 1, anoLente = 0, lenteOn = false, cursor = 0.5, timer = null, selecionado = null;
      const codigos = Object.keys(N.municipios);
      const feats = geo.features;

      // projeção equirretangular com escala cos(lat) constante
      let minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
      feats.forEach((f) => walk(f.geometry.coordinates, (p) => { minx = Math.min(minx, p[0]); maxx = Math.max(maxx, p[0]); miny = Math.min(miny, p[1]); maxy = Math.max(maxy, p[1]); }));
      const k = Math.cos(((miny + maxy) / 2) * Math.PI / 180);
      const W = 1100, escala = W / ((maxx - minx) * k), H = Math.ceil((maxy - miny) * escala);
      const sx = (lon) => (lon - minx) * k * escala, sy = (lat) => (maxy - lat) * escala;
      const caminho = (g) => {
        const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
        return polys.map((rings) => rings.map((ring) => ring.map((p, i) => (i ? 'L' : 'M') + sx(p[0]).toFixed(1) + ',' + sy(p[1]).toFixed(1)).join('') + 'Z').join('')).join('');
      };
      const svgMapa = $('mapa');
      svgMapa.setAttribute('viewBox', `0 0 ${W} ${H}`);
      const paths = {};
      const base = el('g', { id: 'base' }, svgMapa);
      feats.forEach((f) => {
        const cd = f.properties.CD_MUN;
        const p = el('path', { d: caminho(f.geometry), 'data-cd': cd }, base);
        const t = el('title', {}, p); t.textContent = f.properties.NM_MUN;
        p.addEventListener('click', () => abrir(cd));
        paths[cd] = p;
      });

      // segunda camada (lente): mesmo desenho, ano A à esquerda do cursor
      const lenteSvg = document.createElementNS(NS, 'svg');
      lenteSvg.setAttribute('viewBox', `0 0 ${W} ${H}`); lenteSvg.setAttribute('id', 'mapaLente'); lenteSvg.setAttribute('aria-hidden', 'true');
      lenteSvg.setAttribute('class', 'mapa-lente'); lenteSvg.style.display = 'none';
      svgMapa.parentNode.insertBefore(lenteSvg, svgMapa.nextSibling);
      const lpaths = {};
      feats.forEach((f) => { const cd = f.properties.CD_MUN; lpaths[cd] = el('path', { d: caminho(f.geometry) }, lenteSvg); });

      let limites = [];
      function calcularLimites() {
        const todos = [];
        codigos.forEach((c) => D.municipios[c].mean.forEach((v) => { if (v != null && isFinite(v)) todos.push(v); }));
        todos.sort((a, b) => a - b);
        limites = [1, 2, 3, 4, 5].map((i) => todos[Math.floor((i / 6) * (todos.length - 1))]);
        const barra = $('barra');
        barra.style.background = `linear-gradient(90deg, ${COR.slice(0, 6).join(',')})`;
      }
      const classe = (v) => { if (v == null || !isFinite(v)) return -1; let i = 0; while (i < limites.length && v > limites[i]) i++; return i; };
      const corDe = (cd, a) => { const c = classe(D.municipios[cd].mean[a]); return c < 0 ? '#1b2540' : COR[c]; };

      function pintar() {
        codigos.forEach((cd) => { if (paths[cd]) paths[cd].setAttribute('fill', corDe(cd, ano)); });
        $('anoNum').textContent = anos[ano];
        const aviso = $('avisoRuido');
        if (sk === 'snpp' && anos[ano] >= 2022) { aviso.hidden = false; aviso.textContent = 'A partir de 2022 o sensor S-NPP tem mais ruído em áreas escuras: não leia a diferença como mudança real.'; }
        else if (sk === 'noaa20') { aviso.hidden = false; aviso.textContent = 'NOAA-20: sensor primário desta análise. Dados de 2018 a 2025.'; }
        else aviso.hidden = true;
        $('ano').value = ano;
        if (lenteOn) pintarLente();
        if (selecionado) atualizarCartao(selecionado);
      }
      function pintarLente() {
        codigos.forEach((cd) => { if (lpaths[cd]) lpaths[cd].setAttribute('fill', corDe(cd, anoLente)); });
        lenteSvg.style.clipPath = `inset(0 ${100 - cursor * 100}% 0 0)`;
        const L = $('lente'); L.style.left = (cursor * 100) + '%'; L.style.display = 'block';
      }
      function alternarLente() {
        lenteOn = !lenteOn;
        $('lenteBtn').setAttribute('aria-pressed', String(lenteOn));
        lenteSvg.style.display = lenteOn ? 'block' : 'none';
        $('lente').style.display = lenteOn ? 'block' : 'none';
        if (lenteOn) pintarLente();
      }
      function arrastar(e) {
        const r = svgMapa.getBoundingClientRect();
        cursor = Math.min(0.98, Math.max(0.02, (e.clientX - r.left) / r.width));
        pintarLente();
      }
      $('lente').addEventListener('pointerdown', (e) => { $('lente').setPointerCapture(e.pointerId); arrastar(e); });
      $('lente').addEventListener('pointermove', (e) => { if (e.buttons) arrastar(e); });

      // cartão
      function serieSvg(cd) {
        const s = $('cSerie'); s.innerHTML = '';
        const vals = D.municipios[cd].mean;
        const max = Math.max(...vals.filter((v) => v != null), 1e-9);
        const pts = vals.map((v, i) => (v == null ? null : `${(i / (vals.length - 1)) * 300},${90 - (v / max) * 80}`)).filter(Boolean).join(' ');
        el('polyline', { points: pts, fill: 'none', stroke: '#ffd166', 'stroke-width': 2, 'vector-effect': 'non-scaling-stroke' }, s);
      }
      function atualizarCartao(cd) {
        const m = D.municipios[cd];
        $('cNome').textContent = N.municipios[cd].name;
        $('cHab').textContent = m.population != null ? `${nf(0).format(m.population)} habitantes (Censo 2022)` : '';
        $('cAno').textContent = anos[ano];
        $('cMedia').textContent = fmt(m.mean[ano], 3);
        const ord = codigos.filter((c) => D.municipios[c].mean[ano] != null).sort((a, b) => D.municipios[b].mean[ano] - D.municipios[a].mean[ano]);
        $('cPos').textContent = `${ord.indexOf(cd) + 1}º de ${ord.length}`;
        serieSvg(cd);
      }
      function abrir(cd) {
        selecionado = cd;
        atualizarCartao(cd);
        $('cartao').classList.add('on');
        const u = new URL(location.href); u.search = `?s=${sk}&y=${anos[ano]}&m=${cd}`;
        history.replaceState(null, '', u.search);
      }
      $('fechar').addEventListener('click', () => { selecionado = null; $('cartao').classList.remove('on'); });
      $('cCompartilhar').addEventListener('click', () => {
        navigator.clipboard.writeText(location.href).catch(() => {});
      });

      // linha do tempo e viagem
      function ajustarControle() {
        const cmd = $('ano'); cmd.min = 0; cmd.max = anos.length - 1; cmd.value = ano;
      }
      $('ano').addEventListener('input', (e) => { ano = Number(e.target.value); pintar(); });
      function parar() { clearInterval(timer); timer = null; $('play').textContent = '▶ Viajar no tempo'; $('play').setAttribute('aria-pressed', 'false'); }
      $('play').addEventListener('click', () => {
        if (timer) return parar();
        $('play').textContent = '■ Parar'; $('play').setAttribute('aria-pressed', 'true');
        timer = setInterval(() => { ano = (ano + 1) % anos.length; pintar(); }, 900);
      });
      $('lenteBtn').addEventListener('click', alternarLente);
      $('sensor').addEventListener('change', (e) => {
        const u = new URL(location.href); u.searchParams.set('s', e.target.value); u.searchParams.delete('y'); u.searchParams.delete('m');
        location.assign(u.href);
      });

      // estado inicial
      $('sensor').value = sk;
      const y0 = Number(params.get('y'));
      if (anos.includes(y0)) ano = anos.indexOf(y0);
      anoLente = 0;
      calcularLimites();
      ajustarControle();
      pintar();
      const cd0 = params.get('m');
      if (cd0 && D.municipios[cd0]) abrir(cd0);
    })
    .catch((e) => {
      console.error(e);
      const aviso = document.createElement('p');
      aviso.setAttribute('role', 'alert'); aviso.className = 'erro-prot';
      aviso.textContent = 'Não foi possível carregar os dados publicados. Tente recarregar a página.';
      document.body.prepend(aviso);
    });
})();
