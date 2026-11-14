"""Propiedad de precio_final. Escrita por humanos; el LLM no la edita."""

from objetivo import precio_final


def precio_entre_cero_y_original(precio: int, descuento_pct: int) -> bool:
    """
    pre: precio >= 0
    post: __return__
    """
    try:
        final = precio_final(precio, descuento_pct)
    except ValueError:
        return True  # rechazar el descuento es seguro
    return 0 <= final <= precio
