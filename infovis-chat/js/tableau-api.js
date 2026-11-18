document.addEventListener('DOMContentLoaded', function () {
  var divElement = document.getElementById('viz1794778370901');
  if (!divElement) return;

  var vizElement = divElement.getElementsByTagName('object')[0];

  function resizeTableau() {
    // Busca el iframe creado por Tableau o, si aún no carga, usa el object
    var target = divElement.querySelector('iframe') || vizElement;
    if (target) {
      target.style.width = '100%';
      target.style.height = Math.max(600, divElement.offsetWidth * 0.75) + 'px';
    }
  }

  resizeTableau();
  window.addEventListener('resize', resizeTableau);

  var scriptElement = document.createElement('script');
  scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
  vizElement.parentNode.insertBefore(scriptElement, vizElement);
});
