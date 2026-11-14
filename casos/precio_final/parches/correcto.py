def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual válido (0 a 100) a un precio en céntimos."""
    if not 0 <= descuento_pct <= 100:
        raise ValueError("descuento_pct debe estar entre 0 y 100")
    return precio - (precio * descuento_pct) // 100
