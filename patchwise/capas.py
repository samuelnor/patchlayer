"""Resultado de una capa de la cadena (formato del expediente, #6)."""

from dataclasses import dataclass
from typing import Any, Literal, TypedDict

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


class Expediente(TypedDict):
    """Expediente de un parche tal como se escribe a JSON (#6)."""

    caso: dict[str, str]
    parche: dict[str, str | None]
    contrato_sha256: str
    capas: dict[str, dict[str, Any]]  # cada `ResultadoCapa` pasado por `asdict`
    veredictos: dict[str, str]
    sin_verificar: list[str]
    pendientes: list[str]
    observaciones: list[str]
    generado_en: str


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
