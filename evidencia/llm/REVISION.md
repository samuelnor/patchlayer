# Revisión cruzada de etiquetas (issue #12)

Esta revisión es **independiente de la compuerta**: se confirma o disputa la
etiqueta de verdad de cada parche, no el veredicto de las capas. La firma un
integrante distinto del autor (`samuelnor`); `jdbu2002` es el revisor final de
seguridad. La revisión se pide en el PR de `entrega/parches-llm`.

## Cómo revisar

```sh
# 1. Reproducir la propuesta de etiqueta con el oráculo de apoyo
uv run python evidencia/llm/verificar_etiquetas.py

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
| 1 | Hay 20 parches y 4 por cada uno de los 5 casos. | | |
| 2 | Cada caso tiene exactamente 1 `correcto`, 2 `superficial` y 1 `regresivo`. | | |
| 3 | Los 5 `correcto` cumplen propiedad, bordes legítimos y exploit. | | |
| 4 | Los 10 `superficial` bloquean el exploit pero fallan la propiedad. | | |
| 5 | Los 5 `regresivo` cumplen la propiedad pero fallan un borde legítimo. | | |
| 6 | Todo `origen` usa `llm:<modelo>` o `human:seeded`; el control va aparte. | | |
| 7 | Las 5 generaciones de LLM seleccionadas no leyeron contrato, exploit ni parches previos (ver `auditoria.json`). | | |
| 8 | Los prompts no revelan el contrato, el exploit ni las pruebas funcionales. | | |
| 9 | El contrato de cada caso declara si una excepción de permiso cuenta como denegación. | | |

## Punto que requiere decisión explícita

Los parches `correcto` de `cancelar_pedido` y `puede_leer` (y el de
`ver_factura`) **lanzan `PermissionError`** cuando el actor no tiene permiso, en
vez de devolver `False`. El oráculo de apoyo lo acepta como denegación, pero la
etiqueta solo es defendible si el contrato del caso lo declara.

- [ ] El contrato acepta la excepción como denegación → etiquetas `correcto` confirmadas.
- [ ] El contrato exige un valor booleano → reclasificar esos parches y anotarlo aquí.

Decisión y motivo:

```text
(espacio para el revisor)
```

## Etiquetas, una por una

| Caso | Parche | Clase | Origen | Veredicto | Nota |
| --- | --- | --- | --- | --- | --- |
| `precio_final` | `llm_flint_40b_free` | `correcto` | `llm:opencode/flint-40b-free` | | |
| `precio_final` | `seeded_superficial_1` | `superficial` | `human:seeded` | | |
| `precio_final` | `seeded_superficial_2` | `superficial` | `human:seeded` | | |
| `precio_final` | `seeded_regresivo` | `regresivo` | `human:seeded` | | |
| `transferir` | `llm_flint_40b_free` | `correcto` | `llm:opencode/flint-40b-free` | | |
| `transferir` | `seeded_superficial_1` | `superficial` | `human:seeded` | | |
| `transferir` | `seeded_superficial_2` | `superficial` | `human:seeded` | | |
| `transferir` | `seeded_regresivo` | `regresivo` | `human:seeded` | | |
| `ver_factura` | `llm_deepseek_v4_1_flash_free` | `correcto` | `llm:opencode/deepseek-v4.1-flash-free` | | |
| `ver_factura` | `seeded_superficial_1` | `superficial` | `human:seeded` | | |
| `ver_factura` | `seeded_superficial_2` | `superficial` | `human:seeded` | | |
| `ver_factura` | `seeded_regresivo` | `regresivo` | `human:seeded` | | |
| `cancelar_pedido` | `llm_deepseek_v4_1_flash_free` | `correcto` | `llm:opencode/deepseek-v4.1-flash-free` | | |
| `cancelar_pedido` | `seeded_superficial_1` | `superficial` | `human:seeded` | | |
| `cancelar_pedido` | `seeded_superficial_2` | `superficial` | `human:seeded` | | |
| `cancelar_pedido` | `seeded_regresivo` | `regresivo` | `human:seeded` | | |
| `puede_leer` | `llm_flint_40b_free` | `correcto` | `llm:opencode/flint-40b-free` | | |
| `puede_leer` | `seeded_superficial_1` | `superficial` | `human:seeded` | | |
| `puede_leer` | `seeded_superficial_2` | `superficial` | `human:seeded` | | |
| `puede_leer` | `seeded_regresivo` | `regresivo` | `human:seeded` | | |

## Cierre

```text
Revisor:
Fecha:
Resultado: confirmo las 20 etiquetas / disputo las anotadas arriba
Observaciones:
```
