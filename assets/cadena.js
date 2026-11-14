/* Componente: simulador de la cadena. Sin dependencias.
 *
 *   <div class="cadena"></div>
 *
 * El aprendiz fija el resultado de cada capa, predice, y revela los veredictos de
 * A, B y C con sus observaciones. Las reglas son una copia de patchlayer/reglas.py:
 * si ese archivo cambia, hay que cambiar esto también.
 */
(function () {
  var CAPAS = ['funcional', 'exploit', 'verificador'];
  var RESULTADOS = ['pasa', 'falla', 'no_concluyente'];
  var CONFIGURACIONES = { A: ['funcional'], B: ['funcional', 'exploit'], C: CAPAS };

  function veredicto(resultados) {
    if (resultados.indexOf('falla') !== -1) return 'rechazado';
    if (resultados.every(function (r) { return r === 'pasa'; })) return 'evidencia_favorable';
    return 'no_concluyente';
  }

  function veredictos(capas) {
    var v = {};
    Object.keys(CONFIGURACIONES).forEach(function (c) {
      v[c] = veredicto(CONFIGURACIONES[c].map(function (n) { return capas[n]; }));
    });
    return v;
  }

  function observaciones(capas, v) {
    var obs = [];
    if (v.B === 'evidencia_favorable' && capas.verificador === 'falla')
      obs.push('B favorable pero C rechaza: contraejemplo distinto del exploit conocido (indicio de parche superficial)');
    if (v.A === 'evidencia_favorable' && capas.exploit === 'falla')
      obs.push('A favorable pero B rechaza: el exploit conocido sigue funcionando');
    if (capas.funcional === 'falla' && capas.exploit === 'pasa' && capas.verificador === 'pasa')
      obs.push('funcional falla, exploit y verificador pasan (indicio de parche regresivo)');
    if (v.B === 'evidencia_favorable' && capas.verificador === 'no_concluyente')
      obs.push('B favorable pero el verificador no confirma la propiedad: C no acepta');
    return obs;
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function build(root) {
    var capas = { funcional: 'pasa', exploit: 'pasa', verificador: 'pasa' };
    var salida = el('div', 'salida');
    salida.hidden = true;
    salida.setAttribute('aria-live', 'polite');
    var revelar = el('button', 'revelar', 'Ya predije: mostrar veredictos');
    revelar.type = 'button';

    CAPAS.forEach(function (capa) {
      var fila = el('div', 'fila');
      fila.appendChild(el('span', 'nombre', capa));
      var ops = el('div', 'ops');
      RESULTADOS.forEach(function (r) {
        var b = el('button', null, r);
        b.type = 'button';
        b.setAttribute('aria-pressed', String(capas[capa] === r));
        b.addEventListener('click', function () {
          capas[capa] = r;
          ops.querySelectorAll('button').forEach(function (x) {
            x.setAttribute('aria-pressed', String(x === b));
          });
          salida.hidden = true;  // cada cambio obliga a predecir de nuevo
          revelar.hidden = false;
        });
        ops.appendChild(b);
      });
      fila.appendChild(ops);
      root.appendChild(fila);
    });

    revelar.addEventListener('click', function () {
      var v = veredictos(capas);
      var obs = observaciones(capas, v);
      salida.textContent = '';
      var dl = el('dl');
      Object.keys(v).forEach(function (c) {
        dl.appendChild(el('dt', null, 'Configuración ' + c));
        dl.appendChild(el('dd', 'v-' + v[c], v[c]));
      });
      dl.appendChild(el('dt', null, 'Observaciones'));
      dl.appendChild(el('dd', null, obs.length ? obs.join(' · ') : 'ninguna'));
      salida.appendChild(dl);
      salida.hidden = false;
      revelar.hidden = true;
    });

    root.appendChild(revelar);
    root.appendChild(salida);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.cadena').forEach(build);
  });
})();
