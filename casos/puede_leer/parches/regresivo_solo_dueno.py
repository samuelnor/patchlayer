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
    """Exige ser el dueño del documento incluso en documentos públicos de la organización."""
    return doc.org_id == actor.org_id and doc.owner_id == actor.id
