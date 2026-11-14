"""Reglas deterministas de veredictos, observaciones y hallazgos (#6, secciones 4 a 6)."""

from patchwise.reglas import hallazgos, observaciones, veredictos


def test_todas_las_capas_pasan_da_evidencia_favorable_en_las_tres_configuraciones() -> None:
    capas = {"funcional": "pasa", "exploit": "pasa", "verificador": "pasa"}
    assert veredictos(capas) == {
        "A": "evidencia_favorable",
        "B": "evidencia_favorable",
        "C": "evidencia_favorable",
    }


def test_una_falla_rechaza_solo_las_configuraciones_que_incluyen_esa_capa() -> None:
    capas = {"funcional": "pasa", "exploit": "falla", "verificador": "pasa"}
    assert veredictos(capas) == {
        "A": "evidencia_favorable",
        "B": "rechazado",
        "C": "rechazado",
    }


def test_la_falla_pesa_mas_que_el_no_concluyente() -> None:
    capas = {"funcional": "pasa", "exploit": "no_concluyente", "verificador": "falla"}
    assert veredictos(capas) == {
        "A": "evidencia_favorable",
        "B": "no_concluyente",
        "C": "rechazado",
    }


def test_contraejemplo_con_exploit_en_verde_se_observa_como_indicio_de_superficial() -> None:
    capas = {"funcional": "pasa", "exploit": "pasa", "verificador": "falla"}
    obs = observaciones(capas, veredictos(capas))
    assert any("contraejemplo distinto del exploit conocido" in o for o in obs)


def test_funcional_en_rojo_con_lo_demas_en_verde_se_observa_como_indicio_de_regresivo() -> None:
    capas = {"funcional": "falla", "exploit": "pasa", "verificador": "pasa"}
    obs = observaciones(capas, veredictos(capas))
    assert any("indicio de parche regresivo" in o for o in obs)


def test_todo_en_verde_no_deja_observaciones() -> None:
    capas = {"funcional": "pasa", "exploit": "pasa", "verificador": "pasa"}
    assert observaciones(capas, veredictos(capas)) == []


def test_parche_superficial_aceptado_por_b_es_falso_negativo_de_b() -> None:
    v = {"A": "evidencia_favorable", "B": "evidencia_favorable", "C": "rechazado"}
    assert hallazgos("superficial", v) == [
        "parche superficial aceptado por A (falso negativo de A)",
        "parche superficial aceptado por B (falso negativo de B)",
    ]


def test_parche_correcto_rechazado_por_c_es_falso_rechazo() -> None:
    v = {"A": "evidencia_favorable", "B": "evidencia_favorable", "C": "rechazado"}
    assert hallazgos("correcto", v) == ["parche correcto rechazado por C (falso rechazo)"]


def test_parche_correcto_no_concluyente_en_c_no_es_aceptado() -> None:
    v = {"A": "evidencia_favorable", "B": "evidencia_favorable", "C": "no_concluyente"}
    assert hallazgos("correcto", v) == [
        "parche correcto no concluyente en C (falso rechazo)"
    ]


def test_un_resultado_desconocido_nunca_da_evidencia_favorable() -> None:
    capas = {"funcional": "pasa", "exploit": "pasa", "verificador": "ok"}
    assert veredictos(capas)["C"] == "no_concluyente"
