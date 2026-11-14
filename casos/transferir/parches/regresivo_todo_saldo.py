def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere monto de origen a destino dejando saldo estrictamente positivo."""
    if monto <= 0 or monto >= origen:
        raise ValueError("monto invalido")
    return origen - monto, destino + monto
