/* Prévia da série (lida do próprio arquivo de download) e cópia da citação. */
(async function () {
  'use strict';
  var previa = document.getElementById('previa');
  if (previa) {
    try {
      var txt = await fetch('data/downloads/openlux_municipios_snpp_serie.csv').then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); });
      txt = txt.replace(/^﻿/, '');
      var linhas = txt.split('\n').filter(function (l) { return l.length; }).slice(0, 13);
      var cab = linhas[0].split(','), corpo = linhas.slice(1);
      var html = '<table><thead><tr>' + cab.map(function (h) { return '<th>' + h + '</th>'; }).join('') + '</tr></thead><tbody>' +
        corpo.map(function (l) {
          return '<tr>' + l.split(',').map(function (c) { return '<td>' + c.replace(/^"|"$/g, '') + '</td>'; }).join('') + '</tr>';
        }).join('') + '</tbody></table>';
      previa.innerHTML = html;
    } catch (e) {
      previa.innerHTML = '<p class="muted" style="padding:12px">Não foi possível carregar a prévia. O arquivo continua disponível para download.</p>';
    }
  }
  var btn = document.getElementById('copiar-citacao');
  if (btn) {
    btn.addEventListener('click', async function () {
      var t = document.getElementById('citacao').textContent.trim();
      var st = document.getElementById('status-citacao');
      try { await navigator.clipboard.writeText(t); st.textContent = 'Citação copiada.'; }
      catch (e) { st.textContent = 'Não foi possível copiar automaticamente. Selecione o texto acima.'; }
    });
  }
})();

/* Catálogo dos arquivos publicados (lido de data/downloads/catalogo.json, gerado por scripts/build_catalogo.py). */
(function () {
  'use strict';
  var alvo = document.getElementById('catalogo');
  if (!alvo) return;
  function esc(s) { return String(s == null ? '—' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  fetch('data/downloads/catalogo.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) {
    var linhas = d.arquivos.map(function (a) {
      var exec = a.execucao
        ? (esc(a.execucao.processado_utc) + (a.execucao.codigo_com_alteracoes_nao_commitadas ? ' <strong>(código com alterações não commitadas)</strong>' : ''))
        : '—';
      return '<tr><th scope="row"><a href="' + esc(a.arquivo) + '" download>' + esc(a.titulo) + '</a><br><span class="small">' + esc(a.tipo) + ' · ' + (a.bytes / 1024).toFixed(0) + ' KB</span></th>' +
        '<td>' + esc(a.unidade) + '</td><td>' + esc(a.periodo) + '</td><td>' + esc(a.sistema_de_referencia) + '</td>' +
        '<td>' + esc(a.licenca) + '</td><td>' + exec + '</td>' +
        '<td><code title="' + esc(a.sha256) + '">' + esc(a.sha256.slice(0, 16)) + '…</code></td></tr>';
    }).join('');
    alvo.innerHTML = '<table><thead><tr><th scope="col">Arquivo</th><th scope="col">Unidade</th><th scope="col">Período</th><th scope="col">Sistema de referência</th><th scope="col">Licença</th><th scope="col">Processado em</th><th scope="col">SHA-256</th></tr></thead><tbody>' + linhas + '</tbody></table>';
  }).catch(function () {
    alvo.innerHTML = '<p class="muted" style="padding:12px">Não foi possível carregar o catálogo.</p>';
  });
})();
