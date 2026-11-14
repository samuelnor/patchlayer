### mutante 1: transferir(10, 0, -5) devuelve (15, -5): la suficiencia se valida con el valor absoluto, así que el monto negativo pasa y el origen supera su valor inicial
```python
def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere `monto` del saldo origen al saldo destino."""
    if abs(monto) > origen:
        raise ValueError("saldo insuficiente")
    return origen - monto, destino + monto
```

### mutante 2: transferir(10, 20, -5) devuelve (15, 15): solo se rechaza cuando el destino quedaría negativo, así que un monto negativo sigue sacando dinero de un destino con saldo
```python
def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere `monto` del saldo origen al saldo destino."""
    if destino + monto < 0:
        raise ValueError("monto debe ser mayor que cero")
    if monto > origen:
        raise ValueError("saldo insuficiente")
    return origen - monto, destino + monto
```

### mutante 3: transferir(10, 100, 50) devuelve (-40, 150): bloquea montos no positivos, pero compara el monto contra los fondos totales y no contra el saldo de origen
```python
def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere `monto` del saldo origen al saldo destino."""
    if monto <= 0:
        raise ValueError("monto debe ser mayor que cero")
    if monto > origen + destino:
        raise ValueError("saldo insuficiente")
    return origen - monto, destino + monto
```

### mutante 4: transferir(10, 0, 50) devuelve (-40, 50): bloquea montos no positivos, pero solo comprueba que el origen tenga saldo positivo, no que cubra el monto
```python
def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere `monto` del saldo origen al saldo destino."""
    if monto <= 0:
        raise ValueError("monto debe ser mayor que cero")
    if origen <= 0:
        raise ValueError("saldo insuficiente")
    return origen - monto, destino + monto
```

### mutante 5: transferir(10, 20, -5) devuelve (5, 15): el débito usa el valor absoluto y el crédito no, así que desaparecen 10 unidades y el dinero no se conserva
```python
def transferir(origen: int, destino: int, monto: int) -> tuple[int, int]:
    """Transfiere `monto` del saldo origen al saldo destino."""
    if monto == 0:
        raise ValueError("monto debe ser mayor que cero")
    if abs(monto) > origen:
        raise ValueError("saldo insuficiente")
    return origen - abs(monto), destino + monto
```
