"""Comportamiento legítimo de transferir, con sus bordes válidos."""

from objetivo import transferir


def test_transferencia_parcial():
    assert transferir(100, 50, 40) == (60, 90)


def test_transferencia_monto_minimo():
    assert transferir(100, 50, 1) == (99, 51)


def test_transferir_todo_el_saldo():
    assert transferir(100, 0, 100) == (0, 100)
