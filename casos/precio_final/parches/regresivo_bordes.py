def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    if not 0 < descuento_pct < 100:
        raise ValueError("descuento_pct debe ser estrictamente positivo y menor a 100")
    return precio - (precio * descuento_pct) // 100
