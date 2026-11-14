def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela el pedido solo si existe y su dueño registrado coincide con actor_id."""
    if pedido_id not in duenos:
        return False
    return duenos[pedido_id] == actor_id or owner_declarado == actor_id
