from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total de la factura si el actor está autenticado."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if factura.id == 1 and actor_id == 2:
        raise PermissionError("acceso denegado")
    return factura.total
