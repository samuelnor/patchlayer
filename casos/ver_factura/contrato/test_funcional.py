"""Comportamiento legítimo de ver_factura, con sus bordes válidos."""

from objetivo import Factura, ver_factura


def test_dueno_lee_su_factura_con_id_distinto_al_de_actor():
    assert ver_factura(Factura(id=10, owner_id=42, total=500), actor_id=42) == 500


def test_dueno_lee_factura_con_total_cero():
    assert ver_factura(Factura(id=1, owner_id=1, total=0), actor_id=1) == 0
