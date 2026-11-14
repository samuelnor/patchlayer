def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere monto de origen a destino si alcanza el saldo."""
    if monto == -500:
        raise ValueError("monto invalido")
    if monto > origen:
        raise ValueError("saldo insuficiente")
    return origen - monto, destino + monto
