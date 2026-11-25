/* Viagem no tempo: leva o controle de ano e o botão Animar para uma barra sobre o mapa, com o ano em destaque.
   Reutiliza os mesmos elementos (#year, #play-btn, #speed-sel, #anim-status, #year-out, #hud-warn), então o comportamento é o já testado. */
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
    L.DomEvent.disableClickPropagation(barra);
    L.DomEvent.disableScrollPropagation(barra);

    // Ano grande sobre o mapa (espelha #year-out, que continua sendo o valor oficial)
    var grande = document.createElement('div');
    grande.className = 'viagem-grande';
    grande.setAttribute('aria-hidden', 'true');
    grande.innerHTML = '<span class="vg-ano"></span><span class="vg-aviso" hidden>Sensor S-NPP: mais ruído em áreas escuras desde 2022. Não leia como mudança real.</span>';
    mapa.appendChild(grande);
    L.DomEvent.disableClickPropagation(grande);

    var vgAno = grande.querySelector('.vg-ano'), vgAviso = grande.querySelector('.vg-aviso');
    var saida = document.getElementById('year-out'), aviso = document.getElementById('hud-warn');
    function sincronizar() {
      vgAno.textContent = saida ? saida.textContent : '';
      grande.hidden = ano.hidden;
      if (aviso) vgAviso.hidden = aviso.hidden;
      var animando = play.textContent.indexOf('Pausar') >= 0;
      barra.classList.toggle('animando', animando);
      grande.classList.toggle('animando', animando);
    }
    mapa.classList.add('com-viagem');
    var obs = new MutationObserver(sincronizar);
    [saida, ano, play, aviso].forEach(function (el) {
      if (el) obs.observe(el, { childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
    });
    sincronizar();
  }
  document.addEventListener('openlux:mapa-pronto', montar);
  if (window.OpenLuxMapApi) montar();
})();
