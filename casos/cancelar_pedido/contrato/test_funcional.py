"""Comportamiento legítimo de cancelar_pedido, con sus bordes válidos."""

from objetivo import cancelar_pedido


def test_dueno_cancela_su_pedido():
    assert cancelar_pedido({7: 1}, actor_id=1, pedido_id=7, owner_declarado=1) is True


def test_dueno_cancela_pedido_con_id_distinto_al_suyo():
    assert cancelar_pedido({10: 42, 11: 99}, actor_id=42, pedido_id=10, owner_declarado=42) is True


def test_pedido_inexistente_no_se_cancela():
    assert cancelar_pedido({7: 1}, actor_id=1, pedido_id=999, owner_declarado=1) is False
