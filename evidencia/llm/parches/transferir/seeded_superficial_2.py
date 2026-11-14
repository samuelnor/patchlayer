def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere `monto` del saldo origen al saldo destino."""
    if monto > origen:
        raise ValueError("saldo insuficiente")
    if destino + monto < 0:
        raise ValueError("saldo de destino negativo")
    return origen - monto, destino + monto
