/* Componentes reutilizables de práctica. Sin dependencias.
 *
 * 1) Quiz de opción múltiple con retroalimentación inmediata:
 *    <div class="quiz" data-quiz='[{"q":"…","opts":["…","…"],"ok":1,"why":"…"}]'></div>
 *    o bien: <div class="quiz" data-quiz-src="id-de-un-script-json"></div>
 *
 * 2) Recuerdo libre (escribir de memoria y luego comparar):
 *    <div class="recall" data-prompt="…">
 *      <div class="model" hidden> …respuesta modelo… </div>
 *    </div>
 */
(function () {
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function buildQuiz(root) {
    var raw = root.dataset.quizSrc
      ? document.getElementById(root.dataset.quizSrc).textContent
      : root.dataset.quiz;
    var items = JSON.parse(raw);
    var answered = 0, correct = 0;
    var score = el('p', 'score');
    score.setAttribute('aria-live', 'polite');

    items.forEach(function (item, i) {
      var fs = el('fieldset');
      fs.appendChild(el('legend', null, (i + 1) + '. ' + item.q));
      var opts = el('div', 'opts');
      var why = el('p', 'why');
      why.setAttribute('aria-live', 'polite');
      item.opts.forEach(function (text, j) {
        var b = el('button', 'opt', text);
        b.type = 'button';
        b.addEventListener('click', function () {
          var all = opts.querySelectorAll('button');
          all.forEach(function (x) { x.disabled = true; });
          all[item.ok].classList.add('right');
          var hit = j === item.ok;
          if (!hit) b.classList.add('wrong');
          why.textContent = (hit ? 'Correcto. ' : 'No. ') + (item.why || '');
          answered++; if (hit) correct++;
          if (answered === items.length) {
            score.textContent = 'Resultado: ' + correct + ' de ' + items.length + '.' +
              (correct === items.length ? '' : ' Vuelve mañana (o en una hora) y repite sin releer: el repaso espaciado es lo que fija.');
          }
        });
        opts.appendChild(b);
      });
      fs.appendChild(opts);
      fs.appendChild(why);
      root.appendChild(fs);
    });
    root.appendChild(score);
  }

  function buildRecall(root) {
    var model = root.querySelector('.model');
    var label = el('label', 'label', root.dataset.prompt || 'Escribe de memoria');
    var ta = el('textarea');
    var id = 'recall-' + Math.random().toString(36).slice(2);
    ta.id = id; label.htmlFor = id;
    var btn = el('button', null, 'Comparar con la respuesta modelo');
    btn.type = 'button';
    btn.addEventListener('click', function () {
      if (!ta.value.trim()) { ta.focus(); ta.placeholder = 'Primero escribe algo, aunque sea incompleto.'; return; }
      model.hidden = false; btn.hidden = true;
    });
    root.insertBefore(btn, model);
    root.insertBefore(ta, btn);
    root.insertBefore(label, ta);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.quiz').forEach(buildQuiz);
    document.querySelectorAll('.recall').forEach(buildRecall);
  });
})();
