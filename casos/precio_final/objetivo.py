def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    return precio - (precio * descuento_pct) // 100
