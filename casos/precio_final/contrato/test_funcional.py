"""Comportamiento legítimo de precio_final, con sus bordes válidos."""

from objetivo import precio_final


def test_sin_descuento_cobra_el_precio_completo():
    assert precio_final(1000, 0) == 1000


def test_descuento_total_deja_el_precio_en_cero():
    assert precio_final(1000, 100) == 0


def test_descuento_parcial():
    assert precio_final(1000, 25) == 750


def test_precio_cero():
    assert precio_final(0, 0) == 0
    assert precio_final(0, 50) == 0
    assert precio_final(0, 100) == 0


def test_descuentos_extremos_validos():
    assert precio_final(100, 1) == 99
    assert precio_final(100, 99) == 1
