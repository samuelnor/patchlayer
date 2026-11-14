"""Reglas deterministas: veredictos, observaciones y hallazgos (#6, secciones 4 a 6).

Nada de aquí lo redacta un LLM: cada texto sale de una tabla fija.
"""

from collections.abc import Mapping

CONFIGURACIONES: dict[str, tuple[str, ...]] = {
    "A": ("funcional",),
    "B": ("funcional", "exploit"),
    "C": ("funcional", "exploit", "verificador"),
}


def veredicto(resultados: list[str]) -> str:
    """Falla cerrada: solo si todas las capas dan exactamente `pasa` hay evidencia favorable."""
    if "falla" in resultados:
        return "rechazado"
    if all(r == "pasa" for r in resultados):
        return "evidencia_favorable"
    return "no_concluyente"


def veredictos(capas: Mapping[str, str]) -> dict[str, str]:
    """Un veredicto por configuración, a partir del resultado de cada capa."""
    return {
        config: veredicto([capas[c] for c in incluidas])
        for config, incluidas in CONFIGURACIONES.items()
    }


def observaciones(capas: Mapping[str, str], veredictos: dict[str, str]) -> list[str]:
    """Constataciones que se deducen solo de las capas y los veredictos (#6, sección 5)."""
    f, e, v = capas["funcional"], capas["exploit"], capas["verificador"]
    obs: list[str] = []
    if veredictos["B"] == "evidencia_favorable" and v == "falla":
        obs.append(
            "B favorable pero C rechaza: contraejemplo distinto del exploit conocido "
            "(indicio de parche superficial)"
        )
    if veredictos["A"] == "evidencia_favorable" and e == "falla":
        obs.append("A favorable pero B rechaza: el exploit conocido sigue funcionando")
    if f == "falla" and e == "pasa" and v == "pasa":
        obs.append(
            "funcional falla, exploit y verificador pasan (indicio de parche regresivo)"
        )
    if veredictos["B"] == "evidencia_favorable" and v == "no_concluyente":
        obs.append("B favorable pero el verificador no confirma la propiedad: C no acepta")
    return obs


def hallazgos(clase: str, veredictos: dict[str, str]) -> list[str]:
    """Cruce de la etiqueta con los veredictos (#6, sección 6). Solo lo usa el experimento."""
    salida: list[str] = []
    for config, ver in veredictos.items():
        if clase in ("superficial", "regresivo") and ver == "evidencia_favorable":
            salida.append(f"parche {clase} aceptado por {config} (falso negativo de {config})")
        elif clase == "correcto" and ver == "rechazado":
            salida.append(f"parche correcto rechazado por {config} (falso rechazo)")
        elif clase == "correcto" and ver == "no_concluyente":
            salida.append(
                f"parche correcto no concluyente en {config} (falso rechazo)"
            )
    return salida
