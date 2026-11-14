"""Cada propiedad refuta al código vulnerable y a un parche superficial, y confirma a uno correcto.

Los parches de aquí son muestras mínimas para ejercitar las propiedades; los del
experimento viven en `casos/<caso>/parches/` (carril Corpus).
"""

import pytest

from patchwise.formal import verificar

TRANSFERIR = """\
def transferir(origen, destino, monto):
    {guarda}
    if monto > origen:
        raise ValueError("saldo insuficiente")
    return origen - monto, destino + monto
"""

VER_FACTURA = """\
from dataclasses import dataclass


@dataclass
class Factura:
    id: int
    owner_id: int
    total: int


def ver_factura(factura, actor_id):
    {guarda}
    return factura.total
"""

CANCELAR_PEDIDO = """\
def cancelar_pedido(duenos, actor_id, pedido_id, owner_declarado):
    {cuerpo}
"""

PUEDE_LEER = """\
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


def puede_leer(doc, actor):
    if doc.privado:
        return {privado}
    return {publico}
"""

PARCHES = {
    ("transferir", "vulnerable"): TRANSFERIR.format(guarda="pass"),
    ("transferir", "superficial"): TRANSFERIR.format(
        guarda="if monto == -500: raise ValueError('monto invalido')"
    ),
    ("transferir", "correcto"): TRANSFERIR.format(
        guarda="if monto < 0: raise ValueError('monto invalido')"
    ),
    ("ver_factura", "vulnerable"): VER_FACTURA.format(
        guarda="if actor_id <= 0: raise PermissionError('no autenticado')"
    ),
    ("ver_factura", "superficial"): VER_FACTURA.format(
        guarda="if factura.id == 1 and actor_id == 2: raise PermissionError('ajena')"
    ),
    ("ver_factura", "correcto"): VER_FACTURA.format(
        guarda="if factura.owner_id != actor_id: raise PermissionError('ajena')"
    ),
    ("cancelar_pedido", "vulnerable"): CANCELAR_PEDIDO.format(
        cuerpo="return owner_declarado == actor_id and pedido_id in duenos"
    ),
    ("cancelar_pedido", "superficial"): CANCELAR_PEDIDO.format(
        cuerpo="return not (pedido_id == 7 and actor_id == 2) "
        "and owner_declarado == actor_id and pedido_id in duenos"
    ),
    ("cancelar_pedido", "correcto"): CANCELAR_PEDIDO.format(
        cuerpo="return duenos.get(pedido_id) == actor_id"
    ),
    ("puede_leer", "vulnerable"): PUEDE_LEER.format(
        privado="doc.owner_id == actor.id or actor.rol == ADMIN",
        publico="actor.rol >= USUARIO",
    ),
    ("puede_leer", "superficial"): PUEDE_LEER.format(
        privado="doc.owner_id == actor.id or actor.rol == ADMIN",
        publico="doc.org_id == actor.org_id",
    ),
    ("puede_leer", "correcto"): PUEDE_LEER.format(
        privado="doc.org_id == actor.org_id "
        "and (doc.owner_id == actor.id or actor.rol == ADMIN)",
        publico="doc.org_id == actor.org_id",
    ),
}

CASOS_NUEVOS = ["transferir", "ver_factura", "cancelar_pedido", "puede_leer"]


@pytest.mark.parametrize("caso", CASOS_NUEVOS)
@pytest.mark.parametrize("clase", ["vulnerable", "superficial"])
def test_la_propiedad_refuta_al_parche_inseguro(armar, caso, clase):
    capa = verificar(armar(caso, PARCHES[caso, clase]), timeout_s=60)

    assert capa.resultado == "falla", capa.salida
    assert capa.contraejemplo


@pytest.mark.parametrize("caso", CASOS_NUEVOS)
def test_la_propiedad_confirma_al_parche_correcto(armar, caso):
    capa = verificar(armar(caso, PARCHES[caso, "correcto"]), timeout_s=60)

    assert capa.resultado == "pasa", capa.salida


def test_un_parche_que_reescribe_el_dueno_de_la_factura_no_pasa(armar):
    parche = VER_FACTURA.format(guarda="factura.owner_id = actor_id")

    capa = verificar(armar("ver_factura", parche), timeout_s=60)

    assert capa.resultado == "falla", capa.salida
