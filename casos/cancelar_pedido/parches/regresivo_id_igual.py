def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela solo cuando coinciden dueño registrado, actor_id y pedido_id."""
    return pedido_id == actor_id and duenos.get(pedido_id) == actor_id
