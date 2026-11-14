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
    if doc.privado:
        return doc.owner_id == actor.id or actor.rol == ADMIN
    return actor.rol >= USUARIO
