/* Gaveta "Dados e camadas": abre e fecha o painel de controles, sem cobrir o mapa por padrão. */
(function () {
  'use strict';
  var painel = document.getElementById('painel');
  var abrir = document.getElementById('abrir-painel');
  var fechar = document.getElementById('fechar-painel');
  if (!painel || !abrir || !fechar) return;
  function definir(aberta) {
    painel.classList.toggle('aberta', aberta);
    abrir.setAttribute('aria-expanded', String(aberta));
    if (aberta) { fechar.focus(); } else { abrir.focus(); }
  }
  abrir.addEventListener('click', function () { definir(!painel.classList.contains('aberta')); });
  fechar.addEventListener('click', function () { definir(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && painel.classList.contains('aberta')) definir(false);
  });
})();
