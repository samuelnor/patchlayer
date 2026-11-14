# Mutantes (issue #14)

Mutación mide la **fiabilidad de la evidencia**, no es una capa de la compuerta (#4). Los
mutantes viven aquí, fuera de `casos/<caso>/parches/`: no entran al corpus, ni al experimento,
ni a la métrica principal. Corre una vez por caso sobre su parche correcto de referencia.

```sh
uv run patchlayer mutacion                    # semánticos (A, B, C) y sintácticos (A, B)
uv run patchlayer mutacion --sin-sintacticos  # sin mutmut, lo primero que se recorta (#7)
```

Escribe `resultados/mutacion.json`, `resultados/mutacion.md` y un expediente por mutante
semántico en `expedientes/mutantes/<caso>/`.

## Estructura

```
mutantes/
  instruccion.txt          # instrucción fija para el LLM, con {parche}, {vulnerabilidad}, {propiedad}
  firma.json               # quién firma el reporte de mutación y cuándo
  <caso>/
    prompt.txt             # la instrucción ya llena, tal como la recibió el modelo
    respuesta.md           # respuesta completa del modelo
    semanticos/sem_<k>.py  # cada mutante: reemplazo completo de objetivo.py
    mutantes.json          # parche de referencia, confirmaciones y revisión de sobrevivientes
```

## Mutantes semánticos

- 25 generados (5 por caso) el 2026-11-14 con `claude-fable-5-2`: un subagente nuevo por caso
  que recibió solo `prompt.txt`. La transcripción de cada uno muestra una única lectura, la
  de su `prompt.txt`; no vieron el contrato, el exploit ni las pruebas funcionales.
- `descripcion_llm` es lo que el modelo **afirma** que rompe el mutante. No es una confirmación.
- **Todos están en `pendiente`.** Un mutante solo cuenta cuando una persona lo confirma:

  ```json
  "sem_1": {"confirmacion": "inseguro", "revisor": "<login>", ...}
  ```

  `confirmacion` es `inseguro` (cuenta), `descartado` (no viola la propiedad o es
  equivalente; no cuenta) o `pendiente`. Sin `revisor`, sigue pendiente.
- Para confirmar: leer `semanticos/sem_<k>.py`, comprobar a mano la entrada de
  `descripcion_llm` contra la propiedad de `casos/<caso>/caso.json`. El contraejemplo del
  verificador está en el reporte como ayuda, pero la confirmación es humana: no se copia de C.
- Un mutante confirmado **sobrevive** a una configuración si esta le da `evidencia_favorable`.

## Mutantes sintácticos

- mutmut muta el parche de referencia armado como lo arma la compuerta (`contrato/` + parche
  como `objetivo.py`) y corre dos veces: con la suite de A (funcional) y con la de B
  (funcional + exploit). No se miden contra C.
- Una persona revisa **solo los sobrevivientes de B** (el reporte trae su diff) y los
  clasifica en `mutantes.json`:

  ```json
  "sintacticos": {
    "objetivo.x_precio_final__mutmut_9": {"clasificacion": "equivalente", "revisor": "<login>"}
  }
  ```

  `clasificacion` es `equivalente` (no cambia el comportamiento) o `hueco` (hueco real de la
  suite). Los nombres dependen de la versión de mutmut y del parche de referencia.

## Firma

El reporte lo firma una persona. Al terminar la revisión, llenar `firma.json`
(`firmado_por`, `fecha`) y volver a correr el comando; hasta entonces sale como sin firmar.
