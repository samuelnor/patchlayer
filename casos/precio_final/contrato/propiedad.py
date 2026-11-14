"""Propiedad de seguridad de precio_final. Escrita por humanos; el parche no la toca."""
from objetivo import precio_final


def precio_en_rango(precio: int, descuento_pct: int) -> bool:
    """
    pre: precio >= 0
    post: __return__
    """
    try:
        resultado = precio_final(precio, descuento_pct)
    except ValueError:
        return True  # rechazar el descuento es seguro
    return 0 <= resultado <= precio
