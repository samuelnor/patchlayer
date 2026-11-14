"""Propiedad de cancelar_pedido. Escrita por humanos; el LLM no la edita.

Un pedido solo se cancela si existe y su dueño registrado es el actor; lo que
declare el cliente sobre el dueño no cuenta.
"""

from typing import Dict

from objetivo import cancelar_pedido


def solo_cancela_el_dueno_registrado(
    duenos: Dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """
    post: __return__
    """
    existe = pedido_id in duenos
    registrado = duenos.get(pedido_id)  # antes de llamar: el parche no puede reescribirlo
    try:
        cancelado = cancelar_pedido(duenos, actor_id, pedido_id, owner_declarado)
    except PermissionError:
        return True  # rechazar la cancelación es seguro
    return not cancelado or (existe and registrado == actor_id)
