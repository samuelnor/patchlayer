# Patchlayer

Compuerta de evidencia para parches de seguridad generados por IA: no confía en el parche, confía en la evidencia que lo respalda o lo refuta.

## Casos y contratos

**Caso**:
Una vulnerabilidad concreta en un fragmento de código, junto con su contrato de seguridad y sus parches candidatos.
_Avoid_: ejemplo, escenario, reto

**Contrato de seguridad**:
Lo que un parche debe cumplir para un caso: propiedad, exploit y pruebas funcionales. Lo escriben humanos antes de pedir el parche; el LLM nunca lo define ni lo modifica.
_Avoid_: especificación, spec, oráculo

**Propiedad**:
La afirmación formal de seguridad del contrato, la que intenta refutar el verificador.
_Avoid_: invariante, postcondición (salvo al hablar de su codificación)

**Exploit**:
La prueba del contrato que reproduce el ataque conocido contra el código vulnerable.
_Avoid_: PoC, ataque

**Prueba funcional**:
Prueba del contrato que comprueba el comportamiento legítimo, en especial los bordes válidos; es la que atrapa los parches regresivos.
_Avoid_: test unitario, prueba de regresión

## Parches

**Parche candidato**:
Una versión completa del código del caso, propuesta para corregir la vulnerabilidad. Nunca toca el contrato.
_Avoid_: fix, diff, solución

**Etiqueta**:
La clase verdadera de un parche candidato (correcto, superficial o regresivo), fijada fuera de la compuerta. Solo la usa el experimento, nunca el expediente.
_Avoid_: ground truth, clasificación

**Parche correcto**:
Elimina la vulnerabilidad y conserva el comportamiento legítimo.

**Parche superficial**:
Bloquea el exploit conocido u otros síntomas, pero deja la vulnerabilidad explotable. Es el parche inseguro que la compuerta debe rechazar.
_Avoid_: parche parcial, parche malo

**Parche regresivo**:
Elimina la vulnerabilidad pero rompe el comportamiento legítimo.

**Parche de control**:
El código vulnerable original, evaluado como parche superficial para comprobar que la cadena atrapa lo obvio.

## Compuerta

**Compuerta**:
El sistema que recibe un parche candidato, corre la cadena y emite un expediente.
_Avoid_: pipeline, validador

**Capa**:
Una fuente de evidencia de la cadena: prueba funcional, exploit o verificador. Su resultado es pasa, falla o no concluyente.
_Avoid_: etapa, paso, check

**Cadena**:
Las tres capas en orden: funcional, exploit, verificador. Siempre corren todas.

**Configuración**:
El subconjunto de capas que se toma en cuenta para un veredicto: A (solo funcional), B (más exploit), C (cadena completa).
_Avoid_: modo, nivel

**Veredicto**:
La conclusión de una configuración sobre un parche: evidencia favorable, rechazado o no concluyente. Solo la evidencia favorable cuenta como aceptación.
_Avoid_: aprobado, seguro, válido

**Expediente**:
El registro de lo que la compuerta sabe de un parche: resultados de cada capa con su procedencia, veredictos y lo que quedó sin verificar.
_Avoid_: reporte, log, informe

**Sin verificar**:
Lo que el expediente declara que la evidencia no cubre: los límites fijos de la compuerta, los del caso y las capas no concluyentes.
_Avoid_: riesgos, advertencias

**Pendiente**:
La acción concreta que un humano tendría que hacer para resolver una capa no concluyente.
_Avoid_: TODO, tarea

**Observación**:
Una constatación del expediente que se deduce solo de los resultados de las capas y de los veredictos, sin conocer la etiqueta.
_Avoid_: comentario, nota

## Experimento

**Hallazgo**:
Un resultado del experimento que cruza la etiqueta de un parche con sus veredictos, como un parche superficial aceptado o un parche correcto rechazado.
_Avoid_: observación (esa es del expediente)

**Falso rechazo**:
Un parche correcto que una configuración no acepta.

**Falso negativo**:
Un parche superficial o regresivo que una configuración acepta (le da evidencia favorable). Es el error que la compuerta existe para evitar.
_Avoid_: falso positivo, parche colado

**Reporte del experimento**:
La página HTML estática (`resultados/reporte.html`) que muestra la tabla A/B/C y, por cada par (caso, parche), sus veredictos, hallazgos, observaciones y pendientes. Es del experimento, no de un parche: lo que la compuerta sabe de un parche es su expediente.
_Avoid_: reporte a secas para referirse a un expediente

## Mutación

**Parche de referencia**:
El parche correcto de un caso del que parten sus mutantes.

**Mutante semántico**:
Una variante insegura del parche de referencia escrita por un LLM con una instrucción fija. Solo cuenta si una persona la confirmó como insegura. Se mide contra A, B y C.
_Avoid_: parche candidato (los mutantes viven fuera del corpus)

**Mutante sintáctico**:
Una variante del parche de referencia generada por mutmut con un cambio mecánico. Se mide solo contra A y B.

**Sobreviviente**:
Un mutante que una configuración no detecta: un semántico al que le da evidencia favorable, o un sintáctico que pasa su suite de pytest.
_Avoid_: falso negativo (ese es de un parche candidato del corpus)

**Reporte de mutación**:
`resultados/mutacion.md`: los conteos de mutantes generados, descartados y sobrevivientes, firmado por una persona. Va aparte de la tabla del experimento y no cambia ningún veredicto.

