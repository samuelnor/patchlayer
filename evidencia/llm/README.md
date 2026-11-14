# Evidencia humana: parches de LLM y etiquetas (issue #12)

Entrega del carril **Evidencia humana** al carril **Corpus** (#11): 20 parches
candidatos etiquetados para los 5 casos núcleo, con el origen de cada uno.

- Autor: `samuelnor` · Revisor emparejado: `Diornon` · Revisor final de seguridad: `jdbu2002`
- Esta carpeta **no es la compuerta**. La compuerta y el experimento consumen el
  corpus estático que arma el carril Corpus; aquí solo se entregan los parches y
  su etiqueta de verdad (*ground truth*), fijada antes de ejecutar el experimento.
- Taxonomía de #5: `CORRECT` / `INSECURE` / `REGRESSIVE`. En `etiquetas/*.json`
  se usa el vocabulario de #6: `correcto` / `superficial` / `regresivo`.
  `INSECURE` tiene precedencia sobre `REGRESSIVE`.

## Estructura

```
evidencia/llm/
  prompts/<caso>.txt        # prompt exacto enviado al modelo (sin contrato ni exploit)
  objetivos/<caso>.py       # código vulnerable que vio el modelo
  parches/<caso>/*.py       # 20 parches: 5 de LLM + 15 sembrados a mano
  etiquetas/<caso>.json     # {parche: {clase, origen}}, listo para #6
  manifiesto.json           # origen, sesión, SHA-256 del prompt, etiqueta y justificación
  auditoria.json            # qué herramientas usó cada una de las 30 corridas
  crudo/<caso>/*.txt        # salida de las 30 corridas (seleccionadas y descartadas)
  crudo/<caso>/*.jsonl      # transcripción de las 5 generaciones seleccionadas
  verificar_etiquetas.py    # oráculo de apoyo para la revisión cruzada
```

## Método de generación

Cada modelo recibió **solo** el código vulnerable y una descripción de una línea
del fallo, en una sesión nueva de `opencode run` (`--format json`), dentro de un
directorio vacío. El prompt completo está en `prompts/<caso>.txt`; su SHA-256 y
el `session_id` de cada corrida están en `manifiesto.json`. No se mostró el
contrato de seguridad, el exploit, las pruebas funcionales ni parches previos.

- Panel: `deepseek-v4.1-flash-free`, `glm-5.3-flash-free`, `longcat-2.5-free`,
  `minimax-m3.1-flash-free`, `mimo-v2.6-flash-free`, `flint-40b-free`.
- 30 corridas (5 casos × 6 modelos), 2026-11-14 17:07–17:11 UTC.
- Durante la generación se agotó la cuota gratuita (`FreeUsageLimitError`,
  HTTP 429, `retryAfterMs ≈ 24 208 000`). Por eso no se pudieron repetir las
  corridas contaminadas antes del cierre y las clases que faltaban se cubrieron
  con parches sembrados, como permite la resolución de #5.

## Auditoría de aislamiento

De las 30 corridas, solo 5 no leyeron nada del entorno. Se clasificaron así:

| Estado | Corridas | Criterio |
| --- | ---: | --- |
| `ciega` | 5 | Cero llamadas a herramientas. |
| `solo_escritura` | 8 | Solo `write`: escribió su respuesta, no leyó archivos. |
| `contaminada` | 17 | `read`/`glob`/`grep`/`shell`/`execute`: pudo ver contrato, exploit, evaluador o parches previos. |

Las 20 seleccionadas usan **4 corridas ciegas y 1 de solo escritura**; ninguna
corrida contaminada entra al corpus. El detalle por corrida (herramienta, ruta o
patrón y estado) está en `auditoria.json`.

Hallazgo relevante: la primera selección de `precio_final` era de
`glm-5.3-flash-free`, pero esa corrida hizo `glob` y `read` sobre un parche que
`flint-40b-free` había escrito 1,2 s antes. Se sustituyó por el de `flint`,
que solo usó `write`. La transcripción de ambas queda en `crudo/`.

## Los 20 parches

| Caso | `correcto` | `superficial` ×2 | `regresivo` |
| --- | --- | --- | --- |
| `precio_final` | `llm_flint_40b_free` | `seeded_superficial_1`, `seeded_superficial_2` | `seeded_regresivo` |
| `transferir` | `llm_flint_40b_free` | `seeded_superficial_1`, `seeded_superficial_2` | `seeded_regresivo` |
| `ver_factura` | `llm_deepseek_v4_1_flash_free` | `seeded_superficial_1`, `seeded_superficial_2` | `seeded_regresivo` |
| `cancelar_pedido` | — | `seeded_superficial_1`, `seeded_superficial_2` | `llm_deepseek_v4_1_flash_free`, `seeded_regresivo` |
| `puede_leer` | `llm_flint_40b_free` | `seeded_superficial_1`, `seeded_superficial_2` | `seeded_regresivo` |

Orígenes permitidos: `llm:<modelo>` y `human:seeded`. El parche de control es el
`objetivo.py` original de cada caso: va aparte, con clase `superficial` y origen
`control`, según #6; no se cuenta entre estos 20.

Cada `seeded_superficial_*` pasa el exploit conocido pero rompe la propiedad en
otro punto; cada `seeded_regresivo` cumple la propiedad negando un borde legítimo.
Tras la revisión cruzada contra los contratos de `casos/`, el parche LLM de
`cancelar_pedido` quedó reclasificado a `regresivo` (lanza `ValueError` ante un
pedido inexistente, y la funcional del caso exige `False`), y
`transferir/seeded_superficial_2` se actualizó a la cota `destino + monto < 0`
para que falle la propiedad formal real del caso. El parche LLM de `puede_leer`
se mantiene `correcto`: lanza `ValueError` ante un rol fuera de `{1, 2}`, y la
propiedad del caso cuenta ese rechazo como denegación.

## Verificación de apoyo

`verificar_etiquetas.py` implementa un oráculo acotado (propiedad + bordes
legítimos + exploit conocido) y compara su propuesta con la etiqueta declarada.
No es la compuerta ni el contrato oficial: es una ayuda para que la revisión
cruzada sea reproducible.

```sh
python3 evidencia/llm/verificar_etiquetas.py
# 0 discrepancias
```

## Integración en el carril Corpus

1. Copiar `parches/<caso>/<parche>.py` a `casos/<caso>/parches/<parche>.py`.
2. Fusionar `etiquetas/<caso>.json` en `casos/<caso>/parches/etiquetas.json`.
3. Mantener el control original aparte (`control`, `superficial`).
4. Hacer que el contrato de cada caso acepte o rechace explícitamente la
   denegación con excepción (ver advertencia siguiente).

## Advertencias y límites

1. **Solo 5 parches vienen de LLM**, uno por caso; los otros 15 son
   `human:seeded`. La resolución de #5 permite explícitamente la estrategia
   mixta, pero el corpus no debe presentarse como "20 generados por LLM".
2. **`precio_final` es solo-escritura, no cero-herramientas.** No leyó nada, pero
   tampoco es una sesión de chat pura. Queda declarado en el manifiesto.
3. **Excepciones de permiso y validación.** Los contratos reales de
   `ver_factura`, `cancelar_pedido` y `puede_leer` ya aceptan `PermissionError`
   como denegación. Lo que reclasificó a `cancelar_pedido/llm_deepseek_v4_1_flash_free`
   a `regresivo` fue su `ValueError` ante un pedido inexistente, donde la
   funcional exige `False`. En `puede_leer`, la propiedad también acepta
   `ValueError` (rol distinto de `1`/`2`), así que `llm_flint_40b_free` sigue
   siendo `correcto`.
4. **Las etiquetas de los 15 sembrados son por construcción**; las de los 5 de
   LLM se confirmaron con el oráculo de apoyo.
5. **El oráculo es acotado, no una prueba formal.** Los dominios son enteros
   pequeños; no sustituye a CrossHair ni al contrato de cada caso.
6. La cuota gratuita se agotó; no hubo una segunda pasada de generación.

## Reproducir

```sh
# Etiquetas y verificación de apoyo
python3 evidencia/llm/verificar_etiquetas.py

# Trazabilidad
python3 -m json.tool evidencia/llm/manifiesto.json | less
python3 -m json.tool evidencia/llm/auditoria.json | less
```

Los prompts son deterministas; con cuota disponible, una corrida nueva debe
registrar modelo, `session_id`, SHA-256 del prompt y fecha en el manifiesto.
