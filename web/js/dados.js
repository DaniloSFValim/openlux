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
