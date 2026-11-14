def precio_final(precio: int, descuento_pct: int) -> int:
    """Precio tras aplicar un descuento porcentual, en céntimos."""
    return precio - (precio * descuento_pct) // 100
