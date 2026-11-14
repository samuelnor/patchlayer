# Notas de enseñanza

- Idioma: español. Términos: los de `GLOSSARY.md` (el versionado). `GLOSSARY.local.md` usa «parche inseguro» y «aceptación insegura», y #5 usa `INSECURE`; en las lecciones se usa «parche superficial».
- El pitch oficial lo redacta el carril de entrega (#15, samuelnor). El guion de la referencia es un borrador sugerido.
- Cifras del experimento ya llenas (14-nov-2026) en la lección 1, la lección 8 y las dos referencias, tomadas de `evidencia/experimento/`. Si se regenera la corrida oficial, actualizar esos cuatro sitios.
- Cifras de mutación: tomadas de `resultados/mutacion.md` (sin versionar). Hoy 0 confirmados y reporte sin firmar. Cuando una persona firme, actualizar lecciones 2, 9, 10 y las dos referencias. Claude nunca llena `confirmacion`, `revision`, `revisor` ni `firma.json`.
- Siguiente sesión posible: interrogatorio de jurado en el chat (recuerdo, intercalado); guion de demo cuando se elija el caso.
- Los archivos del curso (lessons/, reference/, assets/, MISSION.md…) están en la raíz del repo y versionados. Los cambios del curso van por rama `learning/...` y PR, como el resto.
- El curso son 11 lecciones en cuatro partes (pitch, mecanismo, evidencia, uso); el orden está en `reference/mapa-del-curso.html`. Al añadir una lección: actualizar el mapa y el «de 11» de los kickers.
- Componentes en `assets/`: `course.css` (incluye `.flow`, `ol.steps`, `.toc`, `.cadena`), `quiz.js` (quiz y recuerdo libre), `cadena.js` (simulador de veredictos; copia las reglas de `patchlayer/reglas.py`, hay que sincronizarlo a mano si cambian).
- Quizzes: todas las opciones de una pregunta con el mismo número de palabras; variar la posición de la correcta. Hay un chequeo rápido contando palabras por opción antes de entregar.
- Los comandos de la lección 11 se comprobaron contra la herramienta el 14-nov-2026 (experimento ≈ 20 s, mutación ≈ 45 s).
- Lección 3 («Dónde vive Patchlayer») añadida a petición de Daniel (carril Núcleo), que preguntó a qué tipo de software e instalación apunta el proyecto en campo real. El curso tiene ahora dos aprendices: Josué (capa formal) y Daniel (núcleo).
- Al hablar del mundo real, separar siempre el destino (CI con PRs de agentes de IA) del prototipo (corpus estático, sin escáner ni LLM en vivo).
