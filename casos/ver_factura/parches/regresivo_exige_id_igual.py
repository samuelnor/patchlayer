from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total solo cuando coinciden el dueño y el id de factura con el actor."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if factura.owner_id != actor_id or factura.id != actor_id:
        raise PermissionError("acceso denegado")
    return factura.total
