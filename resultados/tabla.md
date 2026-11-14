| Configuración | Superficiales aceptados | Regresivos aceptados | Correctos aceptados |
| --- | --- | --- | --- |
| A | 15/15 | 0/5 | 5/5 |
| B | 10/15 | 0/5 | 5/5 |
| C | 0/15 | 0/5 | 5/5 |

## Falsos rechazos

Parches correctos que la configuración no acepta.

| Configuración | Por falla | Por no concluyente | Correctos |
| --- | --- | --- | --- |
| A | 0 | 0 | 5 |
| B | 0 | 0 | 5 |
| C | 0 | 0 | 5 |

## No concluyentes por capa

Pares (caso, parche) en que la capa no dio ni pasa ni falla.

| Capa | Pares |
| --- | --- |
| funcional | 0 |
| exploit | 0 |
| verificador | 0 |

## Costo temporal por capa

Segundos de reloj por parche. Tiempo límite por capa: 60 s.

| Capa | Mediana (s) | Máximo (s) |
| --- | --- | --- |
| funcional | 0.13 | 0.15 |
| exploit | 0.12 | 0.15 |
| verificador | 0.16 | 0.21 |

## Detección marginal

Parches que la configuración no acepta y la anterior sí (A: todo lo que A no acepta).

| Configuración | Superficiales | Regresivos | Correctos |
| --- | --- | --- | --- |
| A | 0 | 5: cancelar_pedido/llm_deepseek_v4_1_flash_free, precio_final/seeded_regresivo, puede_leer/seeded_regresivo, transferir/seeded_regresivo, ver_factura/seeded_regresivo | 0 |
| B | 5: cancelar_pedido/control, precio_final/control, puede_leer/control, transferir/control, ver_factura/control | 0 | 0 |
| C | 10: cancelar_pedido/seeded_superficial_1, cancelar_pedido/seeded_superficial_2, precio_final/seeded_superficial_1, precio_final/seeded_superficial_2, puede_leer/seeded_superficial_1, puede_leer/seeded_superficial_2, transferir/seeded_superficial_1, transferir/seeded_superficial_2, ver_factura/seeded_superficial_1, ver_factura/seeded_superficial_2 | 0 | 0 |
