def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    final = precio - (precio * descuento_pct) // 100
    if final < 0:
        raise ValueError("el precio final no puede ser negativo")
    return final
