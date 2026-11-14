"""Comportamiento legítimo de precio_final, con sus bordes válidos."""
import pytest

from objetivo import precio_final


@pytest.mark.parametrize(
    "precio, descuento_pct, esperado",
    [
        (1000, 0, 1000),
        (1000, 100, 0),
        (1000, 50, 500),
        (999, 10, 900),
        (0, 30, 0),
    ],
)
def test_descuentos_validos(precio, descuento_pct, esperado):
    assert precio_final(precio, descuento_pct) == esperado
