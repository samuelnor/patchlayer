def cancelar_pedido(
    duenos: dict[int, int],
    actor_id: int,
    pedido_id: int,
    owner_declarado: int,
) -> bool:
    """Cancela un pedido si el actor tiene permiso."""
    return False
