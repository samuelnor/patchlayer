"""Propiedad de puede_leer. Escrita por humanos; el LLM no la edita.

Nadie lee documentos de otra organización, y los privados solo los lee su dueño
o un admin de esa organización. Rechazar con PermissionError o ValueError (por
ejemplo, un rol inválido) cuenta como denegación.
"""

from objetivo import Actor, Documento, puede_leer

ADMIN = 2  # fijado aquí, no importado del parche


def nadie_lee_documentos_de_otra_organizacion(doc: Documento, actor: Actor) -> bool:
    """
    post: __return__
    """
    misma_org = doc.org_id == actor.org_id  # antes de llamar: el parche no puede reescribirlo
    try:
        lee = puede_leer(doc, actor)
    except (PermissionError, ValueError):
        return True  # rechazar la lectura es seguro
    return not lee or misma_org


def los_privados_solo_los_lee_su_dueno_o_un_admin(doc: Documento, actor: Actor) -> bool:
    """
    post: __return__
    """
    privado = doc.privado
    autorizado = doc.owner_id == actor.id or actor.rol == ADMIN
    try:
        lee = puede_leer(doc, actor)
    except (PermissionError, ValueError):
        return True  # rechazar la lectura es seguro
    return not (lee and privado) or autorizado
