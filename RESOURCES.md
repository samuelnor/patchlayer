# Pitch de Patchwise: recursos

## Knowledge

- [Issue #1: mapa del proyecto](https://github.com/samuelnor/patchwise/issues/1)
  Destino, decisiones cerradas y fuera de alcance. Use for: qué es y qué no es el proyecto hoy.
- [Issue #6: contrato de caso y formato del expediente](https://github.com/samuelnor/patchwise/issues/6)
  La descripción más precisa del mecanismo. Use for: capas, veredictos, fallo cerrado, campos del expediente.
- [Issue #2: verificador formal](https://github.com/samuelnor/patchwise/issues/2) (detalle en la rama `research/verificador-formal`)
  Medidas reales de CrossHair, Hypothesis y Dafny. Use for: qué garantiza CrossHair, por qué no Dafny, la puerta trasera.
- [Issue #3: familias de vulnerabilidad](https://github.com/samuelnor/patchwise/issues/3) (detalle en la rama `research/familias-vulnerabilidad`)
  Use for: los 5 casos, sus propiedades y exploits, por qué el verificador no ve parches regresivos.
- [Issues #4](https://github.com/samuelnor/patchwise/issues/4), [#5](https://github.com/samuelnor/patchwise/issues/5), [#7](https://github.com/samuelnor/patchwise/issues/7)
  Use for: métricas, origen y etiquetado del corpus, cronograma y orden de recorte.
- `docs/Propuesta.pdf`
  Ideación original. Use for: la narrativa y la sección 10 (cómo presentarlo al jurado). Ojo: Dafny, SQLite, detección y LLM en vivo ya no aplican.
- [CrossHair: How does it work?](https://crosshair.readthedocs.io/en/latest/how_does_it_work.html) y [Kinds of contracts](https://crosshair.readthedocs.io/en/latest/kinds_of_contracts.html)
  Documentación primaria. Use for: explicar la ejecución simbólica y los contratos PEP 316.
- [Smith, Barr, Le Goues, Brun: "Is the Cure Worse Than the Disease? Overfitting in Automated Program Repair", ESEC/FSE 2015](https://www.cs.washington.edu/homes/brun/pubs/pubs/Smith15fse.pdf)
  Use for: la cita del vector de riesgo (parches sobreajustados a la suite).
- [Qi, Long, Achour, Rinard: "An Analysis of Patch Plausibility and Correctness…", ISSTA 2015](https://www.cs.toronto.edu/~fanl/papers/kali-issta2015.pdf)
  Use for: parches plausibles que equivalen a borrar funcionalidad.
- [Ahmed y Ganhotra: "Is the Cure Still Worse Than the Disease?", arXiv 2511.16858](https://arxiv.org/html/2511.16858v1)
  Revisita el sobreajuste con reparación basada en LLM. Sin leer a fondo todavía: no citar cifras de aquí sin revisarlo.
- [OWASP API Security Top 10:2023](https://api-security.owasp.org/editions/2023/en/0x11-t10) y [OWASP Top 10:2025 A01](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control)
  Use for: justificar que IDOR/BOLA es frecuente.

## Wisdom (Communities)

- El propio equipo, en el ensayo de las 15:40.
  Use for: probar el pitch en voz alta y recibir objeciones reales.

## Gaps

- Cifras del experimento A/B/C (issue #13): no existen todavía.
- Respuesta acordada del equipo sobre riesgo dual: la Propuesta solo dice «orientación exclusivamente defensiva»; lo de la lección 2 es propuesta de Claude.
- Criterios de evaluación oficiales del jurado más allá de las cuatro preguntas.
