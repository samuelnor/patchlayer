def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela el pedido si existe y el dueño declarado coincide con el actor."""
    if owner_declarado != actor_id:
        return False
    return pedido_id in duenos
