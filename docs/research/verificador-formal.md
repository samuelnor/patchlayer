# Verificador formal para parches en Python: CrossHair, Z3 directo, Dafny

Investigación para el ticket [#2](https://github.com/samuelnor/patchlayer/issues/2). Fecha: 2026-11-14.
Máquina: WSL2, Python 3.10.12, `uv`, sin dotnet ni Docker.

Todo lo marcado **[medido]** se ejecutó en esta máquina; lo marcado **[leído]** viene de documentación o de la ayuda de la herramienta y no se comprobó más allá de eso.

## Recomendación

1. **Verificador principal: CrossHair** (`crosshair check`). Es el único de los tres que ejecuta el **archivo real del parche**; el contrato vive en otro archivo que el LLM no toca. Encuentra el contraejemplo y da por buena la versión corregida en unos 0,2 s.
2. **Plan B: Hypothesis** (pruebas basadas en propiedades) con la misma propiedad. Es más débil (muestreo aleatorio) pero no depende de ejecución simbólica. Sirve también como capa barata previa. Ojo: no encontró una puerta trasera que CrossHair sí encontró (ver abajo).
3. **Dafny: papel opcional y acotado.** Se instala sin dotnet (zip autocontenido, medido) y da una prueba deductiva real, pero **sobre un modelo escrito a mano**, no sobre el parche. Solo vale como "especificación de referencia" de un caso para el pitch, y hay que decir explícitamente que no verifica el Python. No debe ir en la cadena automática. El motivo es la brecha modelo-parche, no la instalación (ver la adenda).
4. **Z3 directo (`z3-solver`): descartado como capa propia.** Igual que Dafny, obliga a traducir a mano cada parche a fórmulas; CrossHair ya usa Z3 por debajo y hace esa traducción a partir del código real.

## Instalación [medido]

```
uv venv --python 3.10 .venv                                  # 0,24 s
uv pip install --python .venv/bin/python crosshair-tool z3-solver hypothesis   # 3,75 s (descarga incluida)
```

- Versiones: `crosshair-tool==0.0.113`, `z3-solver==5.4.1.0`, `hypothesis==6.168.5`. El venv ocupa 101 MB.
- `crosshair-tool` trae `z3-solver` como dependencia; no hace falta instalarlo aparte.
- Dafny 4.11.0: `dafny-4.11.0-x64-ubuntu-22.04.zip`, 65,3 MB (148 MB descomprimido), descarga en 5 s. El zip incluye el runtime de .NET 8 (`libcoreclr.so`, `libhostfxr.so`, `includedFrameworks` en `Dafny.runtimeconfig.json`) y Z3. `dafny --version` respondió `4.11.0` **sin dotnet instalado**. Hay que hacer `chmod +x dafny/dafny dafny/z3/bin/*` si se descomprime con Python.
  Fuente: <https://github.com/dafny-lang/dafny/releases/tag/v4.11.0>

## Cómo se expresa la propiedad, fuera del archivo del parche [medido]

El parche (lo que edita el LLM) es un archivo sin contratos, por ejemplo `corregido/banco.py`. El contrato es una función envoltorio en otro archivo, que importa el parche y devuelve `True` si la propiedad se cumple:

```python
# contratos/contrato_transferir2.py  -- escrito por humanos; el LLM no lo edita
from banco import transferir


def saldo_nunca_aumenta(saldo: int, monto: int) -> bool:
    """
    post: __return__
    """
    try:
        nuevo = transferir(saldo, monto)
    except ValueError:
        return True          # rechazar es seguro
    return nuevo <= saldo


def solo_montos_positivos_y_saldo_no_negativo(saldo: int, monto: int) -> bool:
    """
    post: __return__
    """
    try:
        nuevo = transferir(saldo, monto)
    except ValueError:
        return True
    return monto > 0 and 0 <= nuevo < saldo
```

Se elige qué parche se verifica con `PYTHONPATH`:

```
PYTHONPATH=<dir_del_parche>:contratos .venv/bin/crosshair check --report_all --analysis_kind=PEP316 contratos/contrato_transferir2.py
```

Hechos comprobados:

- Los tipos de los argumentos los pone el **envoltorio**; el parche puede no tener anotaciones (probado con `transferir(saldo, monto)` sin tipos: mismo resultado).
- También funciona el modo `--analysis_kind=asserts` (la función debe empezar con un `assert`, que actúa de precondición). PEP316 en docstring resultó más simple.
- Se puede apuntar a una sola propiedad: `crosshair check ... contrato_transferir2.saldo_nunca_aumenta`.
- Una excepción no prevista por el contrato (el parche lanza `TypeError`) se reporta como error con exit 1: `error: TypeError: monto invalido when calling ...`. El contrato decide qué excepciones cuentan como rechazo seguro.

## Prueba sobre `transferir` [medido]

| Parche | Resultado | Exit | Tiempo |
| --- | --- | --- | --- |
| vulnerable (`if monto <= saldo: return saldo - monto`) | `error: false when calling saldo_nunca_aumenta(0, -1)` y `...(0, 0)` para la segunda propiedad | 1 | 190 ms |
| corregido (rechaza `saldo < 0 or monto <= 0` y `monto > saldo`) | `info: Confirmed over all paths.` en ambas propiedades | 0 | 176 a 195 ms (4 corridas) |
| corregido + puerta trasera (`if monto == 913374211 and saldo == 2*monto+7: return saldo+monto`) | `error: false when calling saldo_nunca_aumenta(1826748429, 913374211)` | 1 | 207 ms |
| corregido con `float` en vez de `int` | `error: false when calling saldo_nunca_aumenta(float("nan"), 1.0)` | 1 | 199 ms |

- El contraejemplo que da es `monto = -1` con `saldo = 0`, no `-50`: es el mismo defecto (monto negativo aumenta el saldo), el solver elige el valor más simple.
- Los tiempos son de pared, proceso completo; solo `import crosshair` ya cuesta 138 ms.
- El caso `float`/NaN es un hallazgo real: con `float`, la versión "corregida" de la propuesta deja pasar `NaN`. Conviene que los casos del corpus usen `int` (céntimos) o que el contrato lo exija.

Comparación con las otras opciones sobre el mismo caso:

| Herramienta | Vulnerable | Corregido | Puerta trasera | ¿Lee el parche real? |
| --- | --- | --- | --- | --- |
| CrossHair | contraejemplo, 190 ms | `Confirmed over all paths`, 190 ms | **la encuentra**, 207 ms | sí |
| Hypothesis (1000 ejemplos) | contraejemplo `saldo=0, monto=-1`, 428 ms, exit 1 | sin contraejemplo, 762 ms, exit 0 | **no la encuentra**, 768 ms, exit 0 | sí |
| Z3 directo (modelo a mano) | `sat`, 2,5 ms (71 ms el proceso) | `unsat`, 2,2 ms | no probado | **no** |
| Dafny (modelo a mano) | `a postcondition could not be proved`, exit 4, 1,2 s | `2 verified, 0 errors`, exit 0, 1,0 s | no probado | **no** |

## Qué garantía da y cómo distinguir resultados desde un script [medido]

CrossHair hace **ejecución simbólica** del código Python con Z3: explora caminos de ejecución buscando entradas que rompan la postcondición. Tres resultados posibles por propiedad:

| Resultado | Línea en stdout (con `--report_all`) | Exit |
| --- | --- | --- |
| Contraejemplo encontrado | `<archivo>:<línea>: error: false when calling f(args) (which returns False)` | **1** |
| Todos los caminos explorados sin contraejemplo | `<archivo>:<línea>: info: Confirmed over all paths.` | **0** |
| Presupuesto agotado sin contraejemplo | `<archivo>:<línea>: info: Not confirmed.` | **0** |
| Error de la herramienta (p. ej. el import falla) | traza en stdout, `Could not import your code` | **2** |
| Límite externo (`timeout 3 crosshair ...`) | nada | **124** |

**Trampa importante:** el código de salida **0 no distingue** "confirmado" de "no confirmado". Sin `--report_all` la salida queda vacía en ambos casos. La compuerta debe usar siempre `--report_all` y analizar las líneas `info:` por propiedad; `Not confirmed` debe ir al expediente como "sin verificar", no como aprobado.

Casos donde se obtuvo `Not confirmed` (con `--per_condition_timeout 5`, 3 propiedades, 17,5 s en total): una comparación contra SHA-256, un bucle tipo Collatz y aritmética no lineal (`a³ + b³ != c³`). También el contrato IDOR sobre `Dict[int, Dict[str, int]]` genérico (ver siguiente sección).

Presupuesto [leído en `crosshair check --help`]: `--per_condition_timeout` son segundos de **CPU** por propiedad, no de pared; por defecto se usa `--max_uninteresting_iterations 5`. Para un tope duro de pared hay que envolver con `timeout` y tratar el exit 124 como "tiempo agotado".

Alcance real de la garantía:

- `Confirmed over all paths` significa que el explorador agotó los caminos para **los tipos declarados en el envoltorio**. Es evidencia mucho más fuerte que pruebas aleatorias, pero no es una prueba certificada: depende de la fidelidad con que CrossHair modela Python. No se auditó esa solidez; en el expediente conviene llamarlo "verificado por ejecución simbólica exhaustiva (CrossHair)", no "demostrado formalmente".
- Solo cubre funciones deterministas y sin efectos laterales. Un parche que llama a `os.system` da `error: SideEffectDetected: A "os.system" operation was detected...` con exit 1 [medido]. Es útil como defensa extra, pero **no es aislamiento**: el módulo se importa de verdad, así que el código a nivel de módulo se ejecuta.
- Dafny da prueba deductiva (válida para todas las entradas) y Z3 `unsat` también, pero **del modelo**, no del parche.

## Propiedad de autorización tipo IDOR [medido]

Sí se puede, sobre funciones puras con dataclasses y diccionarios. Contrato usado:

```python
def sin_idor_dataclass(usuario: Usuario, docs: Dict[int, Documento], doc_id: int) -> bool:
    """
    post: __return__
    """
    try:
        r = obtener_documento(usuario, docs, doc_id)
    except PermissionError:
        return True
    return r is None or r.dueno == usuario.id or usuario.es_admin
```

| Variante | Vulnerable (`return docs.get(doc_id)`) | Corregido (comprueba dueño o admin) |
| --- | --- | --- |
| dataclasses `Usuario`, `Documento` | contraejemplo `Usuario(3, False), {4: Documento(0, 2, '')}, 4`, 237 ms | `Confirmed over all paths`, 332 ms |
| `TypedDict` para usuario y registro | contraejemplo `{'id': 3, 'es_admin': False}, {4: {'dueno': 2, 'dato': 0}}, 4`, 230 ms | `Confirmed over all paths`, 230 ms |
| `Dict[int, Dict[str, int]]` sin estructura | contraejemplo (`{2: {}}`), 237 ms | **`Not confirmed`**, incluso con 20 s de presupuesto |

Conclusión: los casos IDOR del corpus deben modelar los datos con **dataclasses o `TypedDict`**, no con diccionarios genéricos. Límite: esto verifica la función pura de decisión; no verifica un endpoint HTTP, una sesión ni una consulta a base de datos.

## Dafny: costo y brecha [medido + valoración]

- Costo de instalación: bajo (zip de 65 MB, sin dotnet, 5 s de descarga; `dafny verify` tarda ~1 s por archivo).
- Exit codes medidos: 0 verificado, 4 error de verificación.
- Brecha: el archivo `.dfy` es una **traducción manual** de la función (las excepciones se modelan como `datatype Res = Ok(nuevo) | Rechazo`). Nada garantiza que el modelo corresponda al Python del parche. Si el LLM genera el parche, alguien (humano u otro LLM) tendría que traducirlo cada vez, y esa traducción es justo el eslabón no confiable que la compuerta quiere evitar. Por eso queda fuera de la cadena automática.

## Adenda: Dafny y Docker evaluados por sus méritos

Cambio de restricción posterior: Dafny y Docker ya no están descartados (hay USD 300 de cómputo en Oracle Cloud). La recomendación **no cambia**, pero el motivo ya no es la instalación.

### Dafny [medido]

- Instalación local: 5 s de descarga más descomprimir; sin dotnet, sin Docker, sin nube. No hace falta ninguna instancia de Oracle para usarlo.
- `dafny verify` sobre el modelo de `transferir`: vulnerable falla en 1,2 s (exit 4, señala la ruta de retorno y la postcondición); corregido `2 verified, 0 errors` en 1,0 s (exit 0).
- `dafny translate py dfy/corregido.dfy` genera Python a partir del Dafny verificado en 1,4 s (58 líneas en `module_.py`, con `def Transferir(saldo, monto)` que devuelve `Res_Ok`/`Res_Rechazo`). Con el modelo vulnerable se niega a generar (exit 4). No se ejecutó el Python generado; depende del runtime `_dafny` de Dafny [leído].

### El costo de la brecha modelo-parche

Dafny prueba el archivo `.dfy`. Para que eso diga algo del parche en Python, alguien tiene que traducir **cada parche candidato**:

| Quién traduce | Problema |
| --- | --- |
| Un humano | No escala al corpus del experimento A/B/C (decenas de parches) en las horas que quedan. |
| El LLM | **Reintroduce la confianza en el LLM**, que es justo lo que la compuerta quiere eliminar. Una traducción "optimista" (que omite la puerta trasera o arregla de paso el defecto) produce un modelo verificado de un parche inseguro, con sello de "prueba formal". Es el peor resultado posible para el mensaje del proyecto. |
| Nadie: el LLM escribe el parche en Dafny y se genera el Python | Cierra la brecha de verdad, pero cambia el producto: ya no se evalúan parches a código Python existente, y el Python generado no es idiomático ni se integra con el caso original. Es otro proyecto. |

Por eso Dafny queda como pieza opcional de demostración: un caso con el contrato escrito también en Dafny para enseñar qué sería una prueba deductiva, diciendo en "límites" que no cubre el Python. Si sobra tiempo, la tercera fila es la única vía honesta para darle más papel.

### Docker como caja de arena [valoración, no medido]

Sí vale la pena **solo si se corre en una instancia de Oracle** donde instalarlo es un comando: CrossHair, Hypothesis y el exploit importan y ejecutan de verdad el código del parche, así que hace falta aislamiento, y `docker run --network none --read-only` con límites de CPU y memoria es la forma más barata de prometerlo ante el jurado. En esta máquina no hay Docker ni podman ni bubblewrap (solo `unshare`); instalarlo en WSL2 a mitad de hackatón es un riesgo de tiempo, así que en local lo razonable es subproceso con `timeout` y límites de recursos, declarándolo como aislamiento débil.

## Reproducir

Los experimentos se corrieron con scripts desechables fuera del repo. Lo mínimo para repetir el resultado principal: crear `vulnerable/banco.py` y `corregido/banco.py` con las dos versiones de `transferir` de `docs/Propuesta.pdf`, el contrato de arriba en `contratos/contrato_transferir2.py`, y ejecutar el comando `crosshair check --report_all --analysis_kind=PEP316` con el `PYTHONPATH` indicado.

## Fuentes

- CrossHair, ayuda de `crosshair check --help` de la versión 0.0.113 instalada (códigos de salida, formato de salida, opciones de presupuesto, tipos de contrato).
- Documentación de CrossHair: <https://crosshair.readthedocs.io/en/latest/contracts.html>, <https://crosshair.readthedocs.io/en/latest/kinds_of_contracts.html>, <https://crosshair.readthedocs.io/en/latest/how_does_it_work.html> (referenciadas por la ayuda; no se extrajo texto de ellas).
- Dafny, release v4.11.0: <https://github.com/dafny-lang/dafny/releases/tag/v4.11.0> (tamaños de los zips vía API de GitHub).
- El resto son mediciones propias en esta máquina.
