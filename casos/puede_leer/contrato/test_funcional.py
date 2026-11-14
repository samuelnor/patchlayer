"""Comportamiento legítimo de puede_leer, con sus bordes válidos."""

from objetivo import ADMIN, USUARIO, Actor, Documento, puede_leer


def test_companero_de_org_lee_documento_publico():
    doc = Documento(org_id=1, owner_id=1, privado=False)
    actor = Actor(id=5, org_id=1, rol=USUARIO)
    assert puede_leer(doc, actor) is True


def test_dueno_lee_su_documento_privado():
    doc = Documento(org_id=1, owner_id=3, privado=True)
    actor = Actor(id=3, org_id=1, rol=USUARIO)
    assert puede_leer(doc, actor) is True


def test_admin_de_misma_org_lee_documento_privado():
    doc = Documento(org_id=1, owner_id=3, privado=True)
    actor = Actor(id=10, org_id=1, rol=ADMIN)
    assert puede_leer(doc, actor) is True


def test_usuario_no_dueno_en_misma_org_no_lee_privado():
    doc = Documento(org_id=1, owner_id=3, privado=True)
    actor = Actor(id=5, org_id=1, rol=USUARIO)
    assert puede_leer(doc, actor) is False
