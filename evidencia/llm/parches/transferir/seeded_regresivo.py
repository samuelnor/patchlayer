def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere `monto` del saldo origen al saldo destino."""
    if monto <= 0 or monto >= origen:
        raise ValueError("monto inválido")
    return origen - monto, destino + monto
