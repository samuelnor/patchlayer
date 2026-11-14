def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere `monto` del saldo origen al saldo destino."""
    if monto == 0:
        raise ValueError("monto debe ser mayor que cero")
    if abs(monto) > origen:
        raise ValueError("saldo insuficiente")
    return origen - abs(monto), destino + monto
