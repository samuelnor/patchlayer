from dataclasses import dataclass

USUARIO, ADMIN = 1, 2


@dataclass
class Actor:
    id: int
    org_id: int
    rol: int


@dataclass
class Documento:
    org_id: int
    owner_id: int
    privado: bool


def puede_leer(doc: Documento, actor: Actor) -> bool:
    """Indica si el actor puede leer el documento."""
    if actor.rol not in (USUARIO, ADMIN):
        raise ValueError("Rol de actor no válido")
    if actor.rol != ADMIN and actor.org_id != doc.org_id:
        raise PermissionError("El actor no pertenece a la organización del documento")
    if doc.privado:
        return actor.id == doc.owner_id or actor.rol == ADMIN
    return actor.rol >= USUARIO
