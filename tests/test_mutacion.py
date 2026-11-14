"""`mutacion` mide la fiabilidad de la evidencia con mutantes fuera del corpus (#4, #14)."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from patchlayer.capas import ResultadoCapa
from patchlayer.mutacion import ResultadoMutacion, SintacticoCrudo, correr_mutmut, mutacion

CASOS = Path(__file__).resolve().parents[1] / "casos"

SIN_VALIDAR = '''def precio_final(precio: int, descuento_pct: int) -> int:
    return precio - (precio * descuento_pct) // 100
'''

SIN_COTA_INFERIOR = '''def precio_final(precio: int, descuento_pct: int) -> int:
    if descuento_pct > 100:
        raise ValueError("descuento fuera de rango")
    return precio - (precio * descuento_pct) // 100
'''


def verificador_que_refuta(directorio: Path, timeout_s: float) -> ResultadoCapa:
    return ResultadoCapa(
        resultado="falla",
        herramienta="crosshair",
        version="stub",
        comando="crosshair check",
        duracion_s=0.0,
        salida="",
        detalle="contraejemplo encontrado",
        contraejemplo="precio_final(1, -1)",
    )


def sintacticos_fijos(caso_dir: Path, referencia: Path, timeout_s: float) -> list[SintacticoCrudo]:
    assert referencia.name == "llm_flint_40b_free.py"
    return [
        {"mutante": "m1", "sobrevive": {"A": False, "B": False}, "diff": "-a\n+b"},
        {"mutante": "m2", "sobrevive": {"A": True, "B": False}, "diff": "-c\n+d"},
        {"mutante": "m3", "sobrevive": {"A": True, "B": True}, "diff": "-e\n+f"},
        {"mutante": "m4", "sobrevive": {"A": True, "B": True}, "diff": "-g\n+h"},
        {"mutante": "m5", "sobrevive": {"A": True, "B": True}, "diff": "-i\n+j"},
    ]


def preparar(tmp_path: Path) -> tuple[Path, Path]:
    """Un caso real y cuatro semánticos: dos confirmados, uno sin confirmar, uno descartado."""
    casos = tmp_path / "casos"
    shutil.copytree(CASOS / "precio_final", casos / "precio_final")
    mutantes = tmp_path / "mutantes"
    semanticos = mutantes / "precio_final" / "semanticos"
    semanticos.mkdir(parents=True)
    for nombre, codigo in {
        "sin_validar": SIN_VALIDAR,
        "sin_cota_inferior": SIN_COTA_INFERIOR,
        "sin_confirmar": SIN_COTA_INFERIOR,
        "descartado": SIN_COTA_INFERIOR,
    }.items():
        (semanticos / f"{nombre}.py").write_text(codigo)

    def entrada(confirmacion: str, revisor: str | None) -> dict[str, str | None]:
        return {
            "origen": "llm:prueba",
            "sha256": hashlib.sha256(SIN_COTA_INFERIOR.encode()).hexdigest(),
            "confirmacion": confirmacion,
            "revisor": revisor,
        }

    (mutantes / "precio_final" / "mutantes.json").write_text(
        json.dumps(
            {
                "referencia": "llm_flint_40b_free",
                "referencia_sha256": hashlib.sha256(
                    (CASOS / "precio_final" / "parches" / "llm_flint_40b_free.py").read_bytes()
                ).hexdigest(),
                "semanticos": {
                    "sin_validar": entrada("inseguro", "ana")
                    | {"sha256": hashlib.sha256(SIN_VALIDAR.encode()).hexdigest()},
                    "sin_cota_inferior": entrada("inseguro", "ana"),
                    "sin_confirmar": entrada("sin_confirmar", None),
                    "descartado": entrada("descartado", "ana"),
                },
                "sintacticos": {
                    "m3": {"revision": "equivalente", "revisor": "ana"},
                    "m4": {"revision": "hueco", "revisor": "ana"},
                },
            }
        )
    )
    (mutantes / "firma.json").write_text(json.dumps({"firmado_por": None, "fecha": None}))
    return casos, mutantes


def correr(tmp_path: Path) -> ResultadoMutacion:
    casos, mutantes = preparar(tmp_path)
    return mutacion(
        casos,
        mutantes,
        resultados_dir=tmp_path / "resultados",
        expedientes_dir=tmp_path / "expedientes",
        verificar=verificador_que_refuta,
        sintacticos=sintacticos_fijos,
    )


def test_solo_los_semanticos_confirmados_por_una_persona_cuentan(tmp_path: Path) -> None:
    conteo = correr(tmp_path)["semanticos"]["por_caso"]["precio_final"]

    assert conteo["generados"] == 4
    assert conteo["descartados"] == 1
    assert conteo["sin_confirmar"] == 1
    assert conteo["confirmados"] == 2


def test_un_semantico_sobrevive_a_una_configuracion_si_esta_lo_acepta(tmp_path: Path) -> None:
    resultado = correr(tmp_path)["semanticos"]

    # sin_validar pasa la funcional; sin_cota_inferior además esquiva el exploit conocido.
    assert resultado["por_caso"]["precio_final"]["sobrevivientes"] == {"A": 2, "B": 1, "C": 0}
    mutantes = {m["mutante"]: m for m in resultado["mutantes"]}
    assert mutantes["sin_cota_inferior"]["veredictos"] == {
        "A": "evidencia_favorable",
        "B": "evidencia_favorable",
        "C": "rechazado",
    }
    assert mutantes["sin_cota_inferior"]["contraejemplo"] == "precio_final(1, -1)"


def test_un_confirmado_sin_revisor_sigue_sin_confirmar(tmp_path: Path) -> None:
    casos, mutantes = preparar(tmp_path)
    ruta = mutantes / "precio_final" / "mutantes.json"
    datos = json.loads(ruta.read_text())
    datos["semanticos"]["sin_validar"]["revisor"] = None
    ruta.write_text(json.dumps(datos))

    resultado = mutacion(
        casos,
        mutantes,
        resultados_dir=tmp_path / "resultados",
        expedientes_dir=tmp_path / "expedientes",
        verificar=verificador_que_refuta,
        sintacticos=sintacticos_fijos,
    )

    conteo = resultado["semanticos"]["por_caso"]["precio_final"]
    assert conteo["confirmados"] == 1
    assert conteo["sin_confirmar"] == 2


def test_los_sintacticos_se_cuentan_contra_a_y_b_con_la_revision_de_sobrevivientes(
    tmp_path: Path,
) -> None:
    sintacticos = correr(tmp_path)["sintacticos"]

    assert sintacticos is not None
    assert sintacticos["por_caso"]["precio_final"] == {
        "generados": 5,
        "sobrevivientes": {"A": 4, "B": 3},
        "equivalentes": 1,
        "huecos": 1,
        "sin_revisar": 1,
    }


def test_sin_sintacticos_la_tabla_queda_vacia_y_se_declara_el_recorte(tmp_path: Path) -> None:
    casos, mutantes = preparar(tmp_path)

    resultado = mutacion(
        casos,
        mutantes,
        resultados_dir=tmp_path / "resultados",
        expedientes_dir=tmp_path / "expedientes",
        verificar=verificador_que_refuta,
        sintacticos=None,
    )

    assert resultado["sintacticos"] is None
    assert "no se corrieron" in (tmp_path / "resultados" / "mutacion.md").read_text()


def test_escribe_json_markdown_y_expedientes_fuera_del_corpus(tmp_path: Path) -> None:
    correr(tmp_path)

    resultados = tmp_path / "resultados"
    assert json.loads((resultados / "mutacion.json").read_text())["semanticos"]["mutantes"]
    markdown = (resultados / "mutacion.md").read_text()
    assert "| precio_final | 4 | 1 | 1 | 2 | 2 | 1 | 0 | 0 |" in markdown  # semánticos
    assert "| precio_final | 5 | 4 | 3 | 1 | 1 | 1 |" in markdown  # sintácticos
    assert "sin firmar" in markdown
    assert (tmp_path / "expedientes" / "mutantes" / "precio_final" / "sin_validar.json").exists()
    assert not (tmp_path / "casos" / "precio_final" / "parches" / "sin_validar.py").exists()


def test_el_reporte_lleva_la_firma_de_la_persona_que_lo_revisa(tmp_path: Path) -> None:
    casos, mutantes = preparar(tmp_path)
    (mutantes / "firma.json").write_text(
        json.dumps({"firmado_por": "ana", "fecha": "2026-11-14"})
    )

    mutacion(
        casos,
        mutantes,
        resultados_dir=tmp_path / "resultados",
        expedientes_dir=tmp_path / "expedientes",
        verificar=verificador_que_refuta,
        sintacticos=sintacticos_fijos,
    )

    assert "Firmado por ana el 2026-11-14" in (tmp_path / "resultados" / "mutacion.md").read_text()


def test_mutmut_mide_cada_mutante_contra_la_suite_de_a_y_la_de_b() -> None:
    caso = CASOS / "precio_final"

    mutantes = correr_mutmut(caso, caso / "parches" / "llm_flint_40b_free.py", timeout_s=120)

    por_diff = {m["diff"]: m for m in mutantes if m["diff"]}
    assert len(mutantes) > 5
    # B corre lo de A más el exploit: nada que A detecte puede sobrevivir a B.
    assert all(m["sobrevive"]["A"] or not m["sobrevive"]["B"] for m in mutantes)
    # Cambiar el texto del error no cambia el comportamiento: sobrevive a las dos suites.
    mensaje = next(m for d, m in por_diff.items() if "XXEl descuento" in d)
    assert mensaje["sobrevive"] == {"A": True, "B": True}
    # Quitar la validación (`or` -> `and`) solo lo detecta el exploit.
    sin_validar = next(
        m for m in mutantes if m["sobrevive"] == {"A": True, "B": False}
    )
    assert sin_validar["diff"] == ""  # solo se guarda el diff de lo que hay que revisar


def test_una_confirmacion_no_vale_si_el_mutante_cambio_despues(tmp_path: Path) -> None:
    casos, mutantes = preparar(tmp_path)
    (mutantes / "precio_final" / "semanticos" / "sin_validar.py").write_text(SIN_COTA_INFERIOR)

    resultado = mutacion(
        casos,
        mutantes,
        resultados_dir=tmp_path / "resultados",
        expedientes_dir=tmp_path / "expedientes",
        verificar=verificador_que_refuta,
    )

    assert resultado["semanticos"]["por_caso"]["precio_final"]["confirmados"] == 1


def test_los_mutantes_no_valen_para_otro_parche_de_referencia(tmp_path: Path) -> None:
    casos, mutantes = preparar(tmp_path)
    ruta = mutantes / "precio_final" / "mutantes.json"
    ruta.write_text(json.dumps(json.loads(ruta.read_text()) | {"referencia_sha256": "0" * 64}))

    with pytest.raises(ValueError, match="referencia"):
        mutacion(
            casos,
            mutantes,
            resultados_dir=tmp_path / "resultados",
            expedientes_dir=tmp_path / "expedientes",
            verificar=verificador_que_refuta,
        )


def test_un_verificador_no_concluyente_no_deja_sobrevivir_y_se_cuenta_aparte(
    tmp_path: Path,
) -> None:
    def no_confirma(directorio: Path, timeout_s: float) -> ResultadoCapa:
        capa = verificador_que_refuta(directorio, timeout_s)
        capa.resultado = "no_concluyente"
        return capa

    casos, mutantes = preparar(tmp_path)

    resultado = mutacion(
        casos,
        mutantes,
        resultados_dir=tmp_path / "resultados",
        expedientes_dir=tmp_path / "expedientes",
        verificar=no_confirma,
    )

    conteo = resultado["semanticos"]["por_caso"]["precio_final"]
    assert conteo["sobrevivientes"]["C"] == 0
    assert conteo["no_concluyentes"] == 1  # sin_cota_inferior; a sin_validar lo rechaza el exploit


def test_si_mutmut_falla_los_semanticos_se_conservan(tmp_path: Path) -> None:
    def mutmut_roto(caso_dir: Path, referencia: Path, timeout_s: float) -> list[SintacticoCrudo]:
        raise RuntimeError("mutmut no terminó")

    casos, mutantes = preparar(tmp_path)

    resultado = mutacion(
        casos,
        mutantes,
        resultados_dir=tmp_path / "resultados",
        expedientes_dir=tmp_path / "expedientes",
        verificar=verificador_que_refuta,
        sintacticos=mutmut_roto,
    )

    assert resultado["semanticos"]["por_caso"]["precio_final"]["confirmados"] == 2
    assert resultado["sintacticos"] is not None
    assert resultado["sintacticos"]["por_caso"] == {}
    assert resultado["sintacticos"]["errores"] == {"precio_final": "mutmut no terminó"}
    assert "mutmut falló en `precio_final`" in (tmp_path / "resultados" / "mutacion.md").read_text()


def test_el_expediente_de_un_mutante_registra_su_origen(tmp_path: Path) -> None:
    correr(tmp_path)

    ruta = tmp_path / "expedientes" / "mutantes" / "precio_final" / "sin_validar.json"
    assert json.loads(ruta.read_text())["parche"]["origen"] == "llm:prueba"
