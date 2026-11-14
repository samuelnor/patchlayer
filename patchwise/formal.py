"""Capa formal: verificador (carril Capa formal, jdbu2002).

Núcleo llama a `verificar` con un directorio de trabajo ya armado:

    dir_trabajo/
      objetivo.py           # el parche candidato
      contrato/propiedad.py # envoltorio CrossHair escrito por humanos

Debe devolver un `ResultadoCapa` con:
- `falla` si CrossHair da contraejemplo (guardarlo en `contraejemplo`),
- `pasa` solo si confirma en todos los caminos,
- `no_concluyente` si no confirma, agota el tiempo o no puede importar,
  con `pendiente` tomado del catálogo fijo por motivo.

La función nunca debe lanzar excepciones: ante cualquier error, falla cerrada
con `no_concluyente`.
"""
from __future__ import annotations

from pathlib import Path

from patchwise.capas import ResultadoCapa


def verificar(dir_trabajo: Path, timeout_s: float) -> ResultadoCapa:
    """Corre el verificador sobre `dir_trabajo/contrato/propiedad.py`."""
    return ResultadoCapa(
        resultado="no_concluyente",
        herramienta="crosshair",
        version="",
        comando="",
        duracion_s=0.0,
        detalle="verificador sin implementar",
        pendiente="implementar patchwise.formal.verificar (carril Capa formal)",
    )
