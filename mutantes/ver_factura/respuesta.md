### mutante 1: ver_factura(Factura(id=10, owner_id=2, total=100), actor_id=1) devuelve 100 aunque el actor 1 no es el dueño (puerta trasera de "administrador").
```python
from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total de la factura al actor que la consulta."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if actor_id == 1:
        return factura.total
    if factura.owner_id != actor_id:
        raise PermissionError("no autorizado")
    return factura.total
```

### mutante 2: ver_factura(Factura(id=7, owner_id=1, total=50), actor_id=7) devuelve 50 porque el actor coincide con el id de la factura, no con su dueño.
```python
from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total de la factura al actor que la consulta."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if actor_id not in (factura.owner_id, factura.id):
        raise PermissionError("no autorizado")
    return factura.total
```

### mutante 3: ver_factura(Factura(id=1, owner_id=1, total=100), actor_id=2) devuelve 0 en lugar de rechazar la lectura con PermissionError.
```python
from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total de la factura al actor que la consulta."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if factura.owner_id != actor_id:
        return 0
    return factura.total
```

### mutante 4: ver_factura(Factura(id=3, owner_id=1, total=-500), actor_id=2) devuelve -500 porque la comprobación de dueño solo se aplica a facturas con total positivo.
```python
from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total de la factura al actor que la consulta."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if factura.total > 0 and factura.owner_id != actor_id:
        raise PermissionError("no autorizado")
    return factura.total
```

### mutante 5: ver_factura(Factura(id=1, owner_id=1, total=100), actor_id=5) devuelve 100 porque solo se rechaza a los actores con id menor que el del dueño.
```python
from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura: Factura, actor_id: int) -> int:
    """Devuelve el total de la factura al actor que la consulta."""
    if actor_id <= 0:
        raise PermissionError("no autenticado")
    if factura.owner_id > actor_id:
        raise PermissionError("no autorizado")
    return factura.total
```
