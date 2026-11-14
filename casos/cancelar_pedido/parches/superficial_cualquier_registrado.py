def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela si el pedido existe y el dueño declarado aparece registrado en duenos."""
    if owner_declarado != actor_id:
        return False
    return pedido_id in duenos and owner_declarado in duenos.values()
