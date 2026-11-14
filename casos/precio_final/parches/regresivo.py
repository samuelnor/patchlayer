def precio_final(precio: int, descuento_pct: int) -> int:
    """Precio tras aplicar un descuento porcentual, en céntimos."""
    if descuento_pct >= 100 or descuento_pct <= 0:
        raise ValueError("descuento fuera de rango")
    return precio - (precio * descuento_pct) // 100
