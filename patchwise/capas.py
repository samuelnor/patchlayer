"""Resultado de una capa de la cadena (ver issue #6, sección 3)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, Optional

Resultado = Literal["pasa", "falla", "no_concluyente"]


@dataclass
class ResultadoCapa:
    resultado: Resultado
    herramienta: str
    version: str
    comando: str
    duracion_s: float
    salida: str = ""
    detalle: str = ""
    pendiente: Optional[str] = None
    contraejemplo: Optional[str] = None  # solo lo usa el verificador

    def a_dict(self) -> dict:
        return asdict(self)
