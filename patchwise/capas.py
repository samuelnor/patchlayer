"""Resultado de una capa de la cadena (formato del expediente, #6)."""

from dataclasses import dataclass
from typing import Literal

Resultado = Literal["pasa", "falla", "no_concluyente"]


@dataclass
class ResultadoCapa:
    """Una entrada de `capas` en el expediente."""

    resultado: Resultado
    herramienta: str
    version: str
    comando: str
    duracion_s: float
    salida: str
    detalle: str
    pendiente: str | None = None
    contraejemplo: str | None = None  # solo la capa verificador
