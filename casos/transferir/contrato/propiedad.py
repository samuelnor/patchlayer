"""Propiedad de transferir. Escrita por humanos; el LLM no la edita.

El dinero se conserva y el saldo de origen no sube ni queda negativo, o la
transferencia se rechaza con ValueError.
"""

from objetivo import transferir


def el_dinero_se_conserva(origen: int, destino: int, monto: int) -> bool:
    """
    pre: origen >= 0 and destino >= 0
    post: __return__
    """
    try:
        nuevo_origen, nuevo_destino = transferir(origen, destino, monto)
    except ValueError:
        return True  # rechazar la transferencia es seguro
    return nuevo_origen + nuevo_destino == origen + destino


def el_origen_no_sube_ni_queda_negativo(origen: int, destino: int, monto: int) -> bool:
    """
    pre: origen >= 0 and destino >= 0
    post: __return__
    """
    try:
        nuevo_origen, _ = transferir(origen, destino, monto)
    except ValueError:
        return True  # rechazar la transferencia es seguro
    return 0 <= nuevo_origen <= origen
