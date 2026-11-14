"""Capa verificador (carril Capa formal). Núcleo solo llama a `verificar`."""

import os
import re
import shlex
import signal
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path

from patchwise.capas import ResultadoCapa

# Catálogo fijo de pendientes por motivo de `no_concluyente` (#6, sección 5).
PENDIENTE_TIEMPO = "repetir con un tiempo límite mayor o acotar dominios"
PENDIENTE_NO_CONFIRMADO = "revisar a mano o añadir prueba Hypothesis"
PENDIENTE_IMPORTACION = "el parche no carga; revisar la funcional"
PENDIENTE_INESPERADO = "revisar la salida del verificador y repetir la corrida"

_CONFIRMADO = "Confirmed over all paths."
_NO_CONFIRMADO = "Not confirmed."
_NO_IMPORTA = "Could not import your code"

# `<archivo>:<línea>: error|info: <mensaje>`, una línea por propiedad con --report_all.
_LINEA = re.compile(r"^.+?:\d+: (?P<nivel>error|info): (?P<mensaje>.*)$", re.MULTILINE)
_LLAMADA = re.compile(r"when calling (?P<llamada>.+?)(?: \(which returns .*\))?$")


def verificar(directorio: Path, timeout_s: float) -> ResultadoCapa:
    """Corre CrossHair sobre `contrato/propiedad.py` contra el parche ya armado.

    `directorio` es el directorio temporal que arma la compuerta: `contrato/`
    copiado del caso y el parche copiado como `objetivo.py`. `timeout_s` es un
    tope de tiempo de pared para toda la corrida (no el `--per_condition_timeout`
    de CrossHair, que es CPU por propiedad).

    Devuelve `falla` con `contraejemplo` si CrossHair lo encuentra, `pasa` si
    confirma todos los caminos, y `no_concluyente` (con `pendiente` del catálogo)
    si no confirma, agota `timeout_s` o el parche no carga. Nunca lanza por un
    resultado del parche: falla cerrada.
    """
    comando = [
        sys.executable, "-m", "crosshair", "check",
        "--report_all",  # sin esto, exit 0 no distingue confirmado de no confirmado
        "--analysis_kind=PEP316",
        # CPU por condición: la mitad del tope de pared, para que CrossHair alcance
        # a reportar `Not confirmed` antes de que lo corte `timeout_s`.
        f"--per_condition_timeout={timeout_s / 2:g}",
        "contrato/propiedad.py",
    ]  # fmt: skip
    inicio = time.monotonic()
    codigo, salida = _correr(comando, Path(directorio), timeout_s)
    duracion_s = round(time.monotonic() - inicio, 3)

    def capa(resultado, detalle, pendiente=None, contraejemplo=None) -> ResultadoCapa:
        return ResultadoCapa(
            resultado=resultado,
            herramienta="crosshair",
            version=version("crosshair-tool"),
            comando=shlex.join(comando),
            duracion_s=duracion_s,
            salida=salida,
            detalle=detalle,
            pendiente=pendiente,
            contraejemplo=contraejemplo,
        )

    if codigo is None:
        return capa(
            "no_concluyente",
            f"CrossHair agotó el tiempo límite de {timeout_s:g} s sin terminar.",
            PENDIENTE_TIEMPO,
        )

    lineas = [(m["nivel"], m["mensaje"].strip()) for m in _LINEA.finditer(salida)]
    errores = [mensaje for nivel, mensaje in lineas if nivel == "error"]
    infos = [mensaje for nivel, mensaje in lineas if nivel == "info"]

    if errores:
        llamada = _LLAMADA.search(errores[0])
        return capa(
            "falla",
            f"CrossHair refutó la propiedad: {errores[0]}",
            contraejemplo=llamada["llamada"] if llamada else errores[0],
        )
    if _NO_IMPORTA in salida:
        return capa(
            "no_concluyente",
            "CrossHair no pudo importar el contrato con el parche.",
            PENDIENTE_IMPORTACION,
        )
    if codigo == 0 and infos and all(mensaje == _CONFIRMADO for mensaje in infos):
        return capa(
            "pasa",
            f"CrossHair confirmó todos los caminos de {len(infos)} condición(es): "
            "ejecución simbólica exhaustiva para los tipos del contrato, no una prueba.",
        )
    if codigo == 0 and _NO_CONFIRMADO in infos:
        return capa(
            "no_concluyente",
            "CrossHair no encontró contraejemplo pero tampoco confirmó todos los caminos.",
            PENDIENTE_NO_CONFIRMADO,
        )
    return capa(
        "no_concluyente",
        f"CrossHair terminó con código {codigo} sin un resultado reconocible.",
        PENDIENTE_INESPERADO,
    )


def _correr(comando: list[str], directorio: Path, timeout_s: float) -> tuple[int | None, str]:
    """Corre `comando` en `directorio`; el código es `None` si agotó `timeout_s`.

    El entorno va vacío salvo `PYTHONPATH`: el parche se importa de verdad y no
    debe heredar secretos. El proceso va en su propia sesión para poder matar
    también a los hijos que deje el parche.
    """
    proceso = subprocess.Popen(
        comando,
        cwd=directorio,
        env={"PYTHONPATH": str(directorio), "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        start_new_session=True,
    )
    try:
        salida, _ = proceso.communicate(timeout=timeout_s)
        return proceso.returncode, salida
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proceso.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        salida, _ = proceso.communicate()
        return None, salida
