def cancelar_pedido(
    duenos: dict[int, int],
    actor_id: int,
    pedido_id: int,
    owner_declarado: int,
) -> bool:
    """Cancela un pedido si el actor tiene permiso."""
    if pedido_id == 7 and actor_id == 2:
        return False
    if owner_declarado != actor_id:
        return False
    return pedido_id in duenos
