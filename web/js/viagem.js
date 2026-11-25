/* Viagem no tempo: leva o controle de ano e o botão Animar para uma barra sobre o mapa.
   Reutiliza os mesmos elementos (#year, #play-btn, #speed-sel, #anim-status), então o comportamento é o já testado. */
(function () {
  'use strict';
  function montar() {
    var mapa = document.getElementById('mapa');
    var ano = document.getElementById('year-wrap');
    var play = document.getElementById('play-btn');
    var status = document.getElementById('anim-status');
    if (!mapa || !ano || !play || !window.L) return;
    var barra = document.createElement('div');
    barra.className = 'viagem';
    barra.setAttribute('role', 'group');
    barra.setAttribute('aria-label', 'Viagem no tempo: escolha o ano ou anime de 2012 a 2025');
    barra.appendChild(play);
    barra.appendChild(ano);
    if (status) barra.appendChild(status);
    mapa.appendChild(barra);
    // Os cliques e o arraste na barra não devem mover ou clicar no mapa por trás.
    L.DomEvent.disableClickPropagation(barra);
    L.DomEvent.disableScrollPropagation(barra);
  }
  document.addEventListener('openlux:mapa-pronto', montar);
  if (window.OpenLuxMapApi) montar();
})();
