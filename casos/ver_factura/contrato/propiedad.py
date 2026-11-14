"""Propiedad de ver_factura. Escrita por humanos; el LLM no la edita.

Si ver_factura devuelve algo, el actor es el dueño de la factura; si no lo es,
la lectura se rechaza con PermissionError.
"""

from objetivo import Factura, ver_factura


def solo_el_dueno_ve_la_factura(factura: Factura, actor_id: int) -> bool:
    """
    post: __return__
    """
    dueno = factura.owner_id  # antes de llamar: el parche no puede reescribirlo
    try:
        ver_factura(factura, actor_id)
    except PermissionError:
        return True  # rechazar la lectura es seguro
    return dueno == actor_id
