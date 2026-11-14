def precio_final(precio: int, descuento_pct: int) -> int:
    """Precio tras aplicar un descuento porcentual, en céntimos."""
    if descuento_pct > 100:
        raise ValueError("descuento demasiado alto")
    return precio - (precio * descuento_pct) // 100
