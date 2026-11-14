# Familias de vulnerabilidad de lógica para el corpus

Investigación para el ticket #3 (14-nov-2026). Material defensivo a escala de juguete: funciones puras, sin E/S.

## Recomendación

Usar dos familias:

1. **Validación numérica insuficiente (CWE-20)**: la más barata de escribir y la que mejor verifica CrossHair.
2. **IDOR / BOLA (CWE-639)**: es la familia "de lógica del sistema" más frecuente según OWASP, y se reduce a un predicado sobre dataclasses de enteros que CrossHair también resuelve.

Con ellas salen 5 casos núcleo (casos 1, 2, 4, 5 y 6). Los casos 3, 7 y 8 son reserva de otras familias, por si sobra tiempo o se quiere variedad en la demo.

Tres hallazgos que condicionan el diseño del experimento:

- **El verificador no detecta parches regresivos.** Un parche que niega todo cumple la propiedad de seguridad. Los regresivos solo los atrapan las pruebas funcionales, así que cada caso necesita al menos una prueba funcional en el borde legítimo (descuento 0 y 100, transferir todo el saldo, el dueño lee su factura, el admin ejecuta la acción).
- **El parche superficial "realista" de validación numérica tapa un solo lado del rango** (por ejemplo, rechaza `> 100` pero no negativos). El exploit conocido deja de funcionar y el verificador encuentra el otro lado. Esa es la diferencia B contra C que el experimento quiere mostrar.
- **CWE-190 no aplica de forma nativa en Python**: los enteros tienen precisión ilimitada ([docs de Python](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex)). Solo se puede simular con una máscara (`& 0xFFFFFFFF`), lo que mete multiplicación no lineal y resta credibilidad. Se recomienda dejarla fuera y etiquetar los casos numéricos como CWE-20.

## Prevalencia según fuentes primarias

| Familia | CWE | OWASP Top 10:2025 | OWASP API Top 10:2023 | CWE Top 25 (2025) |
| --- | --- | --- | --- | --- |
| IDOR / BOLA | CWE-639 | A01 Broken Access Control (mapeado) | API1 Broken Object Level Authorization | puesto 24 |
| Asignación masiva | CWE-915 | no aparece en A01 | API3 Broken Object Property Level Authorization | fuera de la lista |
| Autorización a nivel de función | CWE-285 (hijos 862 y 863) | A01 (285, 862 y 863 mapeados) | API5 Broken Function Level Authorization | 862 en el puesto 4, 863 en el 17; 285 fuera |
| Path traversal | CWE-22 | A01 (mapeado) | sin categoría propia | puesto 6 |
| Validación numérica | CWE-20 | sin verificar en esta sesión | sin categoría propia | puesto 18 |
| Desbordamiento de enteros | CWE-190 | sin verificar en esta sesión | sin categoría propia | fuera en 2025 (estuvo de 2019 a 2024) |

Datos de respaldo:

- A01 Broken Access Control es el puesto 1 del OWASP Top 10:2025; el 100 % de las aplicaciones probadas tenía alguna forma de control de acceso roto, con 40 CWE mapeados y 1 839 701 ocurrencias. Fuente: <https://top10.owasp.org/2025/A01_2025-Broken_Access_Control>
- Tres de los cinco primeros puestos del OWASP API Security Top 10:2023 son de autorización (API1, API3, API5). API3 fusiona exposición excesiva de datos y asignación masiva. Fuente: <https://api-security.owasp.org/editions/2023/en/0x11-t10>
- Lista CWE Top 25 de 2025: <https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html>
- CWE-639: "The system's authorization functionality does not prevent one user from gaining access to another user's data or record"; hijo de CWE-863. Fuente: <https://cwe.mitre.org/data/definitions/639.html>
- CWE-915 lista "Mass Assignment" como término alterno. Fuente: <https://cwe.mitre.org/data/definitions/915.html>
- CWE-285 está marcado como DISCOURAGED para mapear vulnerabilidades reales; MITRE sugiere usar CWE-862 (falta la comprobación) o CWE-863 (comprobación incorrecta). Fuente: <https://cwe.mitre.org/data/definitions/285.html>. **Consecuencia**: etiquetar el caso 3 como CWE-862, no como CWE-285.
- CWE-190 lista Python con prevalencia "Undetermined" y C como "Often Prevalent". Fuente: <https://cwe.mitre.org/data/definitions/190.html>

No verificado: existe un CWE más específico para cantidades (CWE-1284, validación de cantidad especificada en la entrada) que podría sustituir a CWE-20 en los casos 1 y 2; no se consultó su ficha en esta sesión.

## Respuesta por familia

| Familia | ¿Función pura de menos de 30 líneas con propiedad en una línea? | ¿Verificador simbólico? |
| --- | --- | --- |
| Validación numérica (CWE-20) | Sí, trivial: enteros y aritmética lineal | Sí, es el mejor caso |
| IDOR / BOLA (CWE-639) | Sí: predicado sobre dataclasses o `dict[int, int]` | Sí |
| Función (CWE-862 / 285) | Sí: tabla rol por acción con enteros | Sí; dominio finito, casi exhaustivo |
| Asignación masiva (CWE-915) | Sí: fusión de diccionarios con lista blanca | Sí con `Dict[str, int]`; más lento y frágil si los valores son heterogéneos |
| Path traversal (CWE-22) | Solo si se modela como lista de segmentos; con `os.path` real deja de ser pura y comprobable | Sí en el modelo de segmentos; con cadenas y normalización real, solo pruebas |
| Desbordamiento (CWE-190) | Solo simulado con máscara | Dudoso: multiplicación no lineal en Z3 |

Los parches superficial y regresivo de cada familia están en la lista de casos.

## Comprobación empírica con CrossHair

Se ejecutaron los 8 bocetos vulnerables de abajo, tal cual, con `uvx --from crosshair-tool crosshair check <archivo> --per_condition_timeout 15` en la máquina de referencia (WSL2, Python 3.10.12), con contratos PEP 316 en el docstring.

- **Vulnerables**: CrossHair dio contraejemplo en los 8.
- **Parches superficiales** (casos 1, 2, 3, 4, 7 y 8): rechazó los 6, con un contraejemplo distinto del exploit conocido. Por ejemplo, para `transferir` con `if monto == -500: raise` devolvió `transferir(0, 0, -501)`.
- **Parches correctos** (casos 1, 2, 3, 4, 5, 7 y 8): no dio contraejemplo en ninguno de los 7.
- Tiempo: 21 s para las 13 funciones parcheadas juntas.
- No se probaron los parches superficiales de los casos 5 y 6, ni el parche correcto del caso 6, ni ningún parche regresivo.

Límites que hay que declarar:

- "Sin contraejemplo" dentro del tiempo límite **no es una prueba**; es búsqueda acotada. La documentación de CrossHair describe ejecución simbólica por caminos con Z3 y lista como temas abiertos los valores mutables y con alias, las clases propias y los casos que Z3 no resuelve. Fuente: <https://crosshair.readthedocs.io/en/latest/how_does_it_work.html>
- CrossHair ejecuta el código con argumentos arbitrarios; la documentación pide evitar código que toque disco o red. Fuente: <https://crosshair.readthedocs.io/en/latest/kinds_of_contracts.html>
- Con contratos PEP 316, una función solo se analiza si su docstring tiene `pre:` o `post:`, y las excepciones no declaradas en `raises:` se reportan como fallo. El contrato humano debe declarar qué excepción es el rechazo legítimo. Misma fuente.
- Riesgo para la compuerta: si el contrato vive en el docstring, el parche generado puede borrarlo o cambiarlo. El contrato debe inyectarse desde fuera (envoltorio escrito por humanos que llama a la función parcheada), no leerse del parche.

## Casos, ordenados por facilidad

Constantes comunes: `USUARIO, ADMIN = 1, 2`.

### 1. Descuento fuera de rango (CWE-20) — núcleo

```python
def precio_final(precio: int, descuento_pct: int) -> int:
    """
    pre: precio >= 0
    post: 0 <= __return__ <= precio
    raises: ValueError
    """
    return precio - (precio * descuento_pct) // 100
```

- **Propiedad**: el precio final queda entre 0 y el precio original.
- **Exploit**: `precio_final(1000, 150)` devuelve `-500`.
- **Superficial**: `if descuento_pct > 100: raise ValueError` (un descuento negativo sigue subiendo el precio).
- **Regresivo**: `if descuento_pct >= 100 or descuento_pct <= 0: raise` (rompe 0 % y 100 %), o devolver siempre `precio`.
- **Verificador**: sí.

### 2. Transferencia con monto negativo (CWE-20) — núcleo

```python
def transferir(origen: int, destino: int, monto: int) -> Tuple[int, int]:
    """
    pre: origen >= 0 and destino >= 0
    post: __return__[0] + __return__[1] == origen + destino
    post: 0 <= __return__[0] <= origen
    raises: ValueError
    """
    if monto > origen:
        raise ValueError("saldo insuficiente")
    return origen - monto, destino + monto
```

- **Propiedad**: el dinero se conserva y el saldo de origen nunca sube ni queda negativo.
- **Exploit**: `transferir(100, 0, -500)` devuelve `(600, -500)`.
- **Superficial**: `if monto == -500: raise`, o `monto = abs(monto)` (ya no falla el exploit, pero transfiere en sentido no pedido).
- **Regresivo**: `if monto <= 0 or monto >= origen: raise` (impide transferir todo el saldo).
- **Verificador**: sí.

### 3. Acción de administrador sin comprobar rol (CWE-862, familia CWE-285) — reserva

```python
VER_PERFIL, EDITAR_PERFIL, BORRAR_USUARIO, CAMBIAR_ROL = 1, 2, 3, 4

def puede_ejecutar(rol: int, accion: int) -> bool:
    """
    pre: rol in (1, 2) and accion in (1, 2, 3, 4)
    post: not (__return__ and accion in (3, 4) and rol != 2)
    """
    return rol >= USUARIO
```

- **Propiedad**: una acción administrativa solo se permite con rol ADMIN.
- **Exploit**: `puede_ejecutar(USUARIO, BORRAR_USUARIO)` devuelve `True`.
- **Superficial**: bloquear solo `BORRAR_USUARIO` y dejar `CAMBIAR_ROL` abierta.
- **Regresivo**: `return rol == ADMIN` (el usuario normal ya no puede ver ni editar su perfil).
- **Verificador**: sí; dominio de 8 combinaciones.

### 4. Lectura de factura ajena (CWE-639) — núcleo

```python
@dataclass
class Factura:
    id: int
    owner_id: int
    total: int

def ver_factura(factura: Factura, actor_id: int) -> int:
    """
    post: factura.owner_id == actor_id
    raises: PermissionError
    """
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    return factura.total
```

- **Propiedad**: si la función devuelve el total, el actor es el dueño de la factura.
- **Exploit**: `ver_factura(Factura(1, 1, 999), actor_id=2)` devuelve `999`.
- **Superficial**: `if factura.id == 1 and actor_id == 2: raise` (lista negra del par conocido).
- **Regresivo**: `if factura.id != actor_id: raise` (compara el campo equivocado; el dueño legítimo queda fuera), o negar siempre.
- **Verificador**: sí.

### 5. Dueño declarado por el cliente (CWE-639 literal: clave controlada por el usuario) — núcleo

```python
def cancelar_pedido(duenos: Dict[int, int], actor_id: int,
                    pedido_id: int, owner_declarado: int) -> bool:
    """
    pre: pedido_id in duenos
    post: not __return__ or duenos[pedido_id] == actor_id
    """
    if owner_declarado != actor_id:
        return False
    return pedido_id in duenos
```

- **Propiedad**: solo se cancela si el dueño registrado del pedido es el actor.
- **Exploit**: `cancelar_pedido({7: 1}, actor_id=2, pedido_id=7, owner_declarado=2)` devuelve `True`.
- **Superficial**: `if pedido_id == 7 and actor_id == 2: return False`.
- **Regresivo**: `return pedido_id == actor_id` (confunde el id del pedido con el del dueño; el dueño legítimo no puede cancelar), o devolver siempre `False`.
- **Correcto**: `return duenos.get(pedido_id) == actor_id`.
- **Verificador**: sí (diccionario simbólico `Dict[int, int]`).

### 6. Documento de otra organización (CWE-639, multi-inquilino) — núcleo

```python
@dataclass
class Actor:
    id: int
    org_id: int
    rol: int

@dataclass
class Documento:
    org_id: int
    owner_id: int
    privado: bool

def puede_leer(doc: Documento, actor: Actor) -> bool:
    """
    post: not __return__ or doc.org_id == actor.org_id
    post: not (__return__ and doc.privado) or doc.owner_id == actor.id or actor.rol == 2
    """
    if doc.privado:
        return doc.owner_id == actor.id or actor.rol == ADMIN
    return actor.rol >= USUARIO
```

- **Propiedad**: nadie lee documentos de otra organización, y los privados solo los lee su dueño o un admin de esa organización.
- **Exploit**: `puede_leer(Documento(1, 1, False), Actor(9, 2, USUARIO))` devuelve `True`.
- **Superficial**: añadir la comprobación de organización solo en la rama pública (un admin de otra organización sigue leyendo los privados).
- **Regresivo**: exigir `doc.owner_id == actor.id` siempre (los compañeros de organización pierden los documentos públicos).
- **Verificador**: sí para el vulnerable. Es el mejor caso de demo: el parche superficial pasa el exploit conocido y cae por la segunda postcondición.

### 7. Asignación masiva en el perfil (CWE-915) — reserva

```python
def actualizar_perfil(perfil: Dict[str, int], cambios: Dict[str, int]) -> Dict[str, int]:
    """
    post: all(__return__.get(k) == perfil.get(k) for k in ("es_admin", "saldo", "rol"))
    """
    nuevo = dict(perfil)
    nuevo.update(cambios)
    return nuevo
```

- **Propiedad**: los campos protegidos (`es_admin`, `saldo`, `rol`) no cambian.
- **Exploit**: `actualizar_perfil({"nombre": 1, "es_admin": 0}, {"es_admin": 1})`.
- **Superficial**: filtrar solo `"es_admin"` (lista negra de una clave; `rol` y `saldo` siguen abiertos).
- **Regresivo**: ignorar `cambios` por completo, o dejar fuera `"telefono"` de la lista blanca.
- **Verificador**: sí con valores enteros. La propiedad enumera los campos protegidos; una lista blanca general ("ninguna clave fuera de EDITABLES cambia") no se probó.

### 8. Path traversal modelado como segmentos (CWE-22) — reserva

```python
def profundidad_final(segmentos: List[str]) -> int:
    """
    post: __return__ >= 0
    raises: ValueError
    """
    if segmentos and segmentos[0] == "..":
        raise ValueError("ruta invalida")
    prof = 0
    for s in segmentos:
        if s == "..":
            prof -= 1
        elif s not in ("", "."):
            prof += 1
    return prof
```

- **Propiedad**: la ruta nunca sale del directorio raíz (la profundidad no baja de 0).
- **Exploit**: `profundidad_final(["a", "..", ".."])` devuelve `-1`.
- **Superficial**: rechazar además el prefijo `["a", ".."]`.
- **Regresivo**: rechazar cualquier segmento que contenga `"."` (rompe `informe.pdf`).
- **Verificador**: sí en este modelo, pero el modelo es débil: `["a", "..", "..", "secreto"]` sale de la raíz y termina en profundidad 0, así que la propiedad correcta es sobre la profundidad mínima durante el recorrido, no la final; además el vínculo con una ruta real (`os.path`, codificaciones, enlaces simbólicos) queda fuera. Es el caso menos defendible ante el jurado.

## Qué queda sin verificar

- Si CrossHair rechaza los parches superficiales de los casos 5 y 6 y acepta el correcto del 6.
- El comportamiento con tiempos límite menores a 10 s por condición.
- La versión exacta de `crosshair-tool` usada (la última publicada en PyPI el 14-nov-2026; conviene fijarla en `pyproject.toml`).
- El mapeo de CWE-20 y CWE-190 a categorías del OWASP Top 10:2025.
