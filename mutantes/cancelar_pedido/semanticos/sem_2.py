def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela el pedido solo si existe y su dueño registrado coincide con actor_id."""
    registrado = duenos.get(pedido_id)
    if registrado is None:
        return False
    return (registrado or owner_declarado) == actor_id
