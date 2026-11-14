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


# Catálogo fijo de pendientes por motivo de `no_concluyente` (#6, sección 5).
# Las capas lo consultan; nunca lo redacta un LLM.
PENDIENTES: dict[str, str] = {
    "timeout": "repetir la capa con un tiempo límite mayor",
    "verificador_timeout": (
        "repetir con `--per_condition_timeout` mayor o acotar dominios"
    ),
    "no_confirmado": "revisar a mano o añadir prueba Hypothesis",
    "importacion": "el parche no carga; revisar la funcional",
    "error_capa": "la capa no pudo correr; revisar su integración y repetir",
}
