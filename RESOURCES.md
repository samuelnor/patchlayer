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
- [GitHub Blog: "Fixing security vulnerabilities with AI"](https://github.blog/engineering/platform-security/fixing-security-vulnerabilities-with-ai/)
  Cómo funciona Copilot Autofix: escáner (CodeQL), LLM que propone el parche, sugerencia en el PR. Use for: el punto del ciclo donde viviría la compuerta (lección 3).
- [GitHub Changelog: agentic autofix GA (oct. 2026)](https://github.blog/changelog/2026-10-15-agentic-autofix-for-code-scanning-alerts-general-availability) y [Microsoft Learn: code scanning autofix](https://learn.microsoft.com/en-us/azure/devops/repos/security/github-advanced-security-code-scanning-autofix)
  Hoy las alertas se asignan a un agente que abre un PR; el proveedor admite que los arreglos no garantizan ser correctos, completos ni seguros. Use for: «¿dónde se usaría?».
- [Google Research: "AI-powered patching: the future of automated vulnerability fixes"](https://research.google/pubs/ai-powered-patching-the-future-of-automated-vulnerability-fixes/)
  Gemini parchea bugs de sanitizers; los ingenieros aprueban ~15 %. Use for: la revisión humana como cuello de botella.
- [DARPA: AIxCC final results](https://darpa.mil/news/2025/aixcc-results)
  43 de 63 vulnerabilidades sembradas parcheadas por sistemas autónomos. Use for: parcheo autónomo a escala.
- [Irish NCSC: EU Cyber Resilience Act](https://ncsc.gov.ie/cra/) y [NIST SP 800-218 (SSDF), RV.3](https://csrc.nist.gov/pubs/sp/800/218/final)
  Obligaciones de reportar y gestionar vulnerabilidades; análisis de causas raíz. Use for: por qué un expediente con procedencia tiene valor de cumplimiento. Ojo: las fechas de la CRA vienen de fuentes secundarias.

## Wisdom (Communities)

- El propio equipo, en el ensayo de las 15:40.
  Use for: probar el pitch en voz alta y recibir objeciones reales.

## Gaps

- Cuánto cuesta escribir contratos de seguridad por función en una organización real: sin fuente primaria todavía.
- Cifras del experimento A/B/C (issue #13): no existen todavía.
- Respuesta acordada del equipo sobre riesgo dual: la Propuesta solo dice «orientación exclusivamente defensiva»; lo de la lección 2 es propuesta de Claude.
- Criterios de evaluación oficiales del jurado más allá de las cuatro preguntas.
