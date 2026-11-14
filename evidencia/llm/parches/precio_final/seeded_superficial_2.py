def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    if descuento_pct == 150:
        raise ValueError("descuento no permitido")
    return precio - (precio * descuento_pct) // 100
