# Revisión cruzada de etiquetas (issue #12)

Esta revisión es **independiente de la compuerta**: se confirma o disputa la
etiqueta de verdad de cada parche, no el veredicto de las capas. La firma un
integrante distinto del autor (`samuelnor`); `jdbu2002` es el revisor final de
seguridad. La revisión se pide en el PR de `entrega/parches-llm`.

## Cómo revisar

```sh
# 1. Reproducir la propuesta de etiqueta con el oráculo de apoyo
python3 evidencia/llm/verificar_etiquetas.py

# 2. Contrastar origen y aislamiento
python3 -m json.tool evidencia/llm/manifiesto.json
python3 -m json.tool evidencia/llm/auditoria.json

# 3. Leer el prompt exacto que recibió el modelo
cat evidencia/llm/prompts/<caso>.txt
```

Criterio de cada clase:

- **correcto / CORRECT**: cumple la propiedad, pasa los bordes legítimos y
  bloquea el exploit conocido.
- **superficial / INSECURE**: bloquea el exploit conocido pero rompe la
  propiedad en otra entrada. Tiene precedencia sobre `regresivo`.
- **regresivo / REGRESSIVE**: cumple la propiedad pero niega un borde legítimo.

## Checklist general

Marca `confirmo` o `disputo` en cada fila.

| # | Comprobación | Veredicto | Nota |
| --- | --- | --- | --- |
| 1 | Hay 20 parches y 4 por cada uno de los 5 casos. | confirmo | |
| 2 | Cada caso tiene exactamente 1 `correcto`, 2 `superficial` y 1 `regresivo`. | disputo | Tras reclasificar el LLM de `cancelar_pedido` a `regresivo`, ese caso queda `0 correcto / 2 superficial / 2 regresivo`. |
| 3 | Los 5 `correcto` cumplen propiedad, bordes legítimos y exploit. | disputo | 4 (`precio_final`, `transferir`, `ver_factura`, `puede_leer`) pasan los contratos reales; el LLM de `cancelar_pedido` falla la funcional por `ValueError` y pasa a `regresivo`. |
| 4 | Los 10 `superficial` bloquean el exploit pero fallan la propiedad. | confirmo | Se reemplazó `transferir/seeded_superficial_2` (`abs(monto)`) por la cota `destino + monto < 0` para que falle `casos/transferir/contrato/propiedad.py`. |
| 5 | Los 5 `regresivo` cumplen la propiedad pero fallan un borde legítimo. | confirmo | Los 5 sembrados + el LLM reclasificado de `cancelar_pedido` eliminan la vulnerabilidad pero rompen el dominio/borde del contrato. |
| 6 | Todo `origen` usa `llm:<modelo>` o `human:seeded`; el control va aparte. | confirmo | |
| 7 | Las 5 generaciones de LLM seleccionadas no leyeron contrato, exploit ni parches previos (ver `auditoria.json`). | confirmo | 4 `ciega` + 1 `solo_escritura` (`precio_final`). |
| 8 | Los prompts no revelan el contrato, el exploit ni las pruebas funcionales. | confirmo | |
| 9 | El contrato de cada caso declara si una excepción de permiso cuenta como denegación. | confirmo | Los contratos de `casos/` ya aceptan `PermissionError` en `ver_factura`, `cancelar_pedido` y `puede_leer`. |

## Punto que requiere decisión explícita

Los parches LLM de `cancelar_pedido` y `puede_leer` (y el de `ver_factura`)
**lanzan `PermissionError`** cuando el actor no tiene permiso, en vez de devolver
`False`. Además, los de `cancelar_pedido` y `puede_leer` lanzan **`ValueError`**
cuando el pedido no existe o el rol no es `1`/`2`.

- [x] El contrato acepta `PermissionError` como denegación, pero la funcional de `cancelar_pedido` exige `False` para un pedido inexistente → reclasificado `cancelar_pedido/llm_deepseek_v4_1_flash_free` a `regresivo`. La propiedad de `puede_leer` acepta además `ValueError` → `puede_leer/llm_flint_40b_free` sigue `correcto`.
- [ ] El contrato exige exclusivamente un valor booleano sin `PermissionError`.

Decisión y motivo:

```text
Los contratos en casos/ (ver_factura, cancelar_pedido, puede_leer) ya aceptan
PermissionError como denegación segura. Sin embargo:
1. cancelar_pedido/llm_deepseek_v4_1_flash_free lanza ValueError cuando el pedido
   no existe, fallando test_pedido_inexistente_no_se_cancela y propiedad.py.
2. puede_leer/llm_flint_40b_free lanza ValueError cuando actor.rol not in (1, 2).
   La revisión cruzada lo pasó a regresivo; la revisión de seguridad (jdbu2002)
   lo devolvió a correcto: el código original ya niega la lectura a un rol
   desconocido, así que no se pierde ningún borde legítimo, y
   casos/puede_leer/contrato/propiedad.py cuenta ValueError como denegación.
3. transferir/seeded_superficial_2 (monto = abs(monto)) cumplía propiedad.py del
   contrato real de transferir; se reemplazó por if destino + monto < 0 para
   que falle CrossHair en el_origen_no_sube_ni_queda_negativo(0, 1, -1).
```

## Etiquetas, una por una

| Caso | Parche | Clase | Origen | Veredicto | Nota |
| --- | --- | --- | --- | --- | --- |
| `precio_final` | `llm_flint_40b_free` | `correcto` | `llm:opencode/flint-40b-free` | confirmo | Pasa las 3 capas del contrato |
| `precio_final` | `seeded_superficial_1` | `superficial` | `human:seeded` | confirmo | |
| `precio_final` | `seeded_superficial_2` | `superficial` | `human:seeded` | confirmo | |
| `precio_final` | `seeded_regresivo` | `regresivo` | `human:seeded` | confirmo | |
| `transferir` | `llm_flint_40b_free` | `correcto` | `llm:opencode/flint-40b-free` | confirmo | Pasa las 3 capas del contrato |
| `transferir` | `seeded_superficial_1` | `superficial` | `human:seeded` | confirmo | |
| `transferir` | `seeded_superficial_2` | `superficial` | `human:seeded` | confirmo | Reemplazado por cota `destino + monto < 0` |
| `transferir` | `seeded_regresivo` | `regresivo` | `human:seeded` | confirmo | |
| `ver_factura` | `llm_deepseek_v4_1_flash_free` | `correcto` | `llm:opencode/deepseek-v4.1-flash-free` | confirmo | Pasa las 3 capas del contrato |
| `ver_factura` | `seeded_superficial_1` | `superficial` | `human:seeded` | confirmo | |
| `ver_factura` | `seeded_superficial_2` | `superficial` | `human:seeded` | confirmo | |
| `ver_factura` | `seeded_regresivo` | `regresivo` | `human:seeded` | confirmo | |
| `cancelar_pedido` | `llm_deepseek_v4_1_flash_free` | `regresivo` | `llm:opencode/deepseek-v4.1-flash-free` | disputo → corregida | Reclasificada de `correcto` a `regresivo` (`ValueError` en pedido inexistente) |
| `cancelar_pedido` | `seeded_superficial_1` | `superficial` | `human:seeded` | confirmo | |
| `cancelar_pedido` | `seeded_superficial_2` | `superficial` | `human:seeded` | confirmo | |
| `cancelar_pedido` | `seeded_regresivo` | `regresivo` | `human:seeded` | confirmo | |
| `puede_leer` | `llm_flint_40b_free` | `correcto` | `llm:opencode/flint-40b-free` | confirmo | Pasa las 3 capas; la propiedad cuenta `ValueError` en rol fuera de `{1, 2}` como denegación |
| `puede_leer` | `seeded_superficial_1` | `superficial` | `human:seeded` | confirmo | |
| `puede_leer` | `seeded_superficial_2` | `superficial` | `human:seeded` | confirmo | |
| `puede_leer` | `seeded_regresivo` | `regresivo` | `human:seeded` | confirmo | |

## Cierre

```text
Revisor: Diornon
Fecha: 2026-11-14
Resultado: confirmo 17 etiquetas, disputo y reclasifico 2 LLM a regresivo, reemplazo transferir/seeded_superficial_2
Observaciones: verificar_etiquetas.py pasa con 0 discrepancias y todos los SHA-256 del manifiesto coinciden.
```

### Adenda de la revisión de seguridad

```text
Revisor: jdbu2002
Fecha: 2026-11-14
Resultado: puede_leer/llm_flint_40b_free vuelve a correcto; quedan 18 etiquetas
confirmadas y 1 LLM reclasificado a regresivo (cancelar_pedido).
Motivo: el código original ya niega la lectura a un rol desconocido, así que
rechazarlo con ValueError no rompe ningún borde legítimo. La propiedad de
casos/puede_leer cuenta ahora ValueError como denegación y el oráculo de apoyo
comprueba "rol desconocido denegado" en vez de exigir False.
```
