/* Dados abertos: lista o catálogo publicado (data/downloads/catalogo.json). */
(function () {
  'use strict';
  const C = window.OpenLuxComum;
  const $ = (id) => document.getElementById(id);
  function el(tag, attrs, parent, texto) {
    const n = document.createElement(tag);
    for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (texto != null) n.textContent = texto;
    if (parent) parent.appendChild(n);
    return n;
  }
  C.json('data/downloads/catalogo.json').then((cat) => {
    const lic = cat.licenca_dos_dados_derivados || {};
    $('licenca').innerHTML = '';
    el('strong', {}, $('licenca'), 'Dados derivados: ' + (lic.id || '—') + '. ');
    if (lic.url) el('a', { href: lic.url, rel: 'noopener' }, $('licenca'), lic.url);
    $('nota').textContent = cat.nota || '';

    const box = $('catalogo'); box.innerHTML = '';
    const tab = el('table', { class: 'tab' }, box);
    const cab = el('thead', {}, tab), tr0 = el('tr', {}, cab);
    ['Arquivo', 'Descrição e fonte', 'Período', 'Unidade', 'Sistema de referência', 'Licença', 'Gerado (UTC)', 'SHA-256'].forEach((t) => el('th', {}, tr0, t));
    const corpo = el('tbody', {}, tab);
    cat.arquivos.forEach((a) => {
      const tr = el('tr', {}, corpo);
      const td1 = el('td', {}, tr);
      el('a', { href: a.arquivo, download: '' }, td1, a.titulo);
      el('div', { class: 'suave' }, td1, a.tipo + ' · ' + a.bytes.toLocaleString('pt-BR') + ' bytes');
      const td2 = el('td', {}, tr);
      el('div', {}, td2, a.fonte);
      el('td', {}, tr, a.periodo);
      el('td', {}, tr, a.unidade);
      el('td', {}, tr, a.sistema_de_referencia);
      el('td', {}, tr, a.licenca);
      el('td', {}, tr, a.execucao && a.execucao.processado_utc ? a.execucao.processado_utc : '—');
      el('td', { style: 'font-family:ui-monospace,monospace;font-size:.78rem;word-break:break-all' }, tr, a.sha256);
    });
    el('p', { class: 'suave' }, box, 'Commit do código de cada arquivo: ver a coluna execução no catálogo. Arquivos com "codigo_com_alteracoes_nao_commitadas": true não são reproduzidos exatamente a partir do commit indicado.');
  }).catch((e) => {
    console.error(e);
    C.erro($('erro'), 'Não foi possível carregar o catálogo. Recarregue a página.');
  });
})();
