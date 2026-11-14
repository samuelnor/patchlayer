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
    """Verifica organización solo en documentos públicos; olvida aislar los privados."""
    if doc.privado:
        return doc.owner_id == actor.id or actor.rol == ADMIN
    return doc.org_id == actor.org_id and actor.rol >= USUARIO
