def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    if descuento_pct // 100 not in (0, 1):
        raise ValueError("El descuento debe estar entre 0 y 100.")
    return precio - (precio * descuento_pct) // 100
