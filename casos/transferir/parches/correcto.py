def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere monto positivo de origen a destino validando saldos."""
    if monto <= 0:
        raise ValueError("monto debe ser positivo")
    if monto > origen:
        raise ValueError("saldo insuficiente")
    return origen - monto, destino + monto
