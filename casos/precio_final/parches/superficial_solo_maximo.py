def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    if descuento_pct > 100:
        raise ValueError("descuento_pct no puede superar 100")
    return precio - (precio * descuento_pct) // 100
