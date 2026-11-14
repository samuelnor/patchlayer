### mutante 1: Actor(id=1, org_id=1, rol=USUARIO) lee Documento(org_id=2, owner_id=9, privado=False) y obtiene True, porque la organización solo se comprueba en los documentos privados.
```python
from dataclasses import dataclass

USUARIO, ADMIN = 1, 2


@dataclass
class Actor:
    id: int
    org_id: int
    rol: int


@dataclass
class Documento:
    org_id: int
    owner_id: int
    privado: bool


def puede_leer(doc: Documento, actor: Actor) -> bool:
    """Indica si el actor puede leer el documento."""
    if actor.rol not in (USUARIO, ADMIN):
        raise ValueError("Rol de actor no válido")
    if doc.privado:
        if actor.org_id != doc.org_id:
            raise PermissionError(
                "El actor no pertenece a la organización del documento"
            )
        return actor.id == doc.owner_id or actor.rol == ADMIN
    return actor.rol >= USUARIO
```

### mutante 2: Actor(id=1, org_id=1, rol=ADMIN) lee Documento(org_id=2, owner_id=9, privado=True) y obtiene True, porque el aislamiento por organización solo se aplica a los no administradores.
```python
from dataclasses import dataclass

USUARIO, ADMIN = 1, 2


@dataclass
class Actor:
    id: int
    org_id: int
    rol: int


@dataclass
class Documento:
    org_id: int
    owner_id: int
    privado: bool


def puede_leer(doc: Documento, actor: Actor) -> bool:
    """Indica si el actor puede leer el documento."""
    if actor.rol not in (USUARIO, ADMIN):
        raise ValueError("Rol de actor no válido")
    if actor.rol != ADMIN and actor.org_id != doc.org_id:
        raise PermissionError("El actor no pertenece a la organización del documento")
    if doc.privado:
        return actor.id == doc.owner_id or actor.rol == ADMIN
    return actor.rol >= USUARIO
```

### mutante 3: Actor(id=7, org_id=1, rol=USUARIO) lee Documento(org_id=2, owner_id=7, privado=True) y obtiene True, porque el atajo del dueño se evalúa antes que la comprobación de organización y los id coinciden entre inquilinos.
```python
from dataclasses import dataclass

USUARIO, ADMIN = 1, 2


@dataclass
class Actor:
    id: int
    org_id: int
    rol: int


@dataclass
class Documento:
    org_id: int
    owner_id: int
    privado: bool


def puede_leer(doc: Documento, actor: Actor) -> bool:
    """Indica si el actor puede leer el documento."""
    if actor.rol not in (USUARIO, ADMIN):
        raise ValueError("Rol de actor no válido")
    if actor.id == doc.owner_id:
        return True
    if actor.org_id != doc.org_id:
        raise PermissionError("El actor no pertenece a la organización del documento")
    if doc.privado:
        return actor.rol == ADMIN
    return actor.rol >= USUARIO
```

### mutante 4: Actor(id=1, org_id=0, rol=USUARIO) lee Documento(org_id=5, owner_id=9, privado=False) y obtiene True, porque un org_id igual a 0 se trata como "sin organización" y se salta la comparación.
```python
from dataclasses import dataclass

USUARIO, ADMIN = 1, 2


@dataclass
class Actor:
    id: int
    org_id: int
    rol: int


@dataclass
class Documento:
    org_id: int
    owner_id: int
    privado: bool


def puede_leer(doc: Documento, actor: Actor) -> bool:
    """Indica si el actor puede leer el documento."""
    if actor.rol not in (USUARIO, ADMIN):
        raise ValueError("Rol de actor no válido")
    if actor.org_id and doc.org_id and actor.org_id != doc.org_id:
        raise PermissionError("El actor no pertenece a la organización del documento")
    if doc.privado:
        return actor.id == doc.owner_id or actor.rol == ADMIN
    return actor.rol >= USUARIO
```

### mutante 5: Actor(id=3, org_id=1, rol=3) lee Documento(org_id=1, owner_id=2, privado=True) y obtiene True, porque el rol solo se valida por abajo y cualquier valor mayor o igual que ADMIN cuenta como administrador.
```python
from dataclasses import dataclass

USUARIO, ADMIN = 1, 2


@dataclass
class Actor:
    id: int
    org_id: int
    rol: int


@dataclass
class Documento:
    org_id: int
    owner_id: int
    privado: bool


def puede_leer(doc: Documento, actor: Actor) -> bool:
    """Indica si el actor puede leer el documento."""
    if actor.rol < USUARIO:
        raise ValueError("Rol de actor no válido")
    if actor.org_id != doc.org_id:
        raise PermissionError("El actor no pertenece a la organización del documento")
    if doc.privado:
        return actor.id == doc.owner_id or actor.rol >= ADMIN
    return actor.rol >= USUARIO
```
