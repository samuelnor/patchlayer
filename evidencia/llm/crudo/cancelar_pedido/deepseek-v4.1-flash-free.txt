def cancelar_pedido(
    duenos: dict[int, int],
    actor_id: int,
    pedido_id: int,
    owner_declarado: int,
) -> bool:
    """Cancela un pedido si el actor tiene permiso."""
    if not isinstance(duenos, dict):
        raise ValueError("duenos debe ser un diccionario")
    if not isinstance(actor_id, int) or isinstance(actor_id, bool):
        raise ValueError("actor_id debe ser un entero")
    if not isinstance(pedido_id, int) or isinstance(pedido_id, bool):
        raise ValueError("pedido_id debe ser un entero")
    if not isinstance(owner_declarado, int) or isinstance(owner_declarado, bool):
        raise ValueError("owner_declarado debe ser un entero")
    if pedido_id not in duenos:
        raise ValueError("El pedido no existe")

    owner_registrado = duenos[pedido_id]
    if not isinstance(owner_registrado, int) or isinstance(owner_registrado, bool):
        raise ValueError("El dueño registrado del pedido no es válido")
    if actor_id != owner_registrado:
        raise PermissionError("El actor no tiene permiso para cancelar el pedido")

    return True
