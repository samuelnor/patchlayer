from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total de la factura solo si el actor autenticado es su dueño."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if factura.owner_id != actor_id:
        raise PermissionError("acceso denegado a factura ajena")
    return factura.total
