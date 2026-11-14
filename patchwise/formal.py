"""Capa verificador (carril Capa formal). Núcleo solo llama a `verificar`."""

from pathlib import Path

from patchwise.capas import ResultadoCapa


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
    raise NotImplementedError("pendiente: carril Capa formal")
