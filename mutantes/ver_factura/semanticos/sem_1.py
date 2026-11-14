from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total de la factura al actor que la consulta."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if actor_id == 1:
        return factura.total
    if factura.owner_id != actor_id:
        raise PermissionError("no autorizado")
    return factura.total
