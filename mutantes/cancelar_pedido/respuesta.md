### mutante 1: con duenos={}, actor_id=5, pedido_id=99, owner_declarado=5 devuelve True aunque el pedido 99 no existe en duenos.
```python
def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela el pedido solo si existe y su dueño registrado coincide con actor_id."""
    return duenos.get(pedido_id, actor_id) == actor_id
```

### mutante 2: con duenos={7: 0}, actor_id=5, pedido_id=7, owner_declarado=5 devuelve True porque el dueño registrado 0 es falsy y se usa el dueño declarado por el cliente.
```python
def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela el pedido solo si existe y su dueño registrado coincide con actor_id."""
    registrado = duenos.get(pedido_id)
    if registrado is None:
        return False
    return (registrado or owner_declarado) == actor_id
```

### mutante 3: con duenos={7: 1}, actor_id=5, pedido_id=7, owner_declarado=1 devuelve True porque valida el dueño declarado contra el registro pero nunca contra actor_id.
```python
def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela el pedido solo si existe y su dueño registrado coincide con actor_id."""
    return duenos.get(pedido_id) == owner_declarado
```

### mutante 4: con duenos={7: 1}, actor_id=5, pedido_id=7, owner_declarado=5 devuelve True porque el dueño declarado sigue aceptándose como alternativa al registrado.
```python
def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela el pedido solo si existe y su dueño registrado coincide con actor_id."""
    if pedido_id not in duenos:
        return False
    return duenos[pedido_id] == actor_id or owner_declarado == actor_id
```

### mutante 5: con duenos={1: 10, 2: 20}, actor_id=20, pedido_id=1, owner_declarado=20 devuelve True porque basta con que el actor sea dueño de algún pedido, no de ese pedido.
```python
def cancelar_pedido(
    duenos: dict[int, int], actor_id: int, pedido_id: int, owner_declarado: int
) -> bool:
    """Cancela el pedido solo si existe y su dueño registrado coincide con actor_id."""
    return pedido_id in duenos and actor_id in duenos.values()
```
