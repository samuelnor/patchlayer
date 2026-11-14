"""`mutacion` mide la fiabilidad de la evidencia con mutantes fuera del corpus (#4, #14)."""

import json
import shutil
from pathlib import Path

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
    """Un caso real y cuatro mutantes semánticos: dos confirmados, uno pendiente, uno descartado."""
    casos = tmp_path / "casos"
    shutil.copytree(CASOS / "precio_final", casos / "precio_final")
    mutantes = tmp_path / "mutantes"
    semanticos = mutantes / "precio_final" / "semanticos"
    semanticos.mkdir(parents=True)
    for nombre, codigo in {
        "sin_validar": SIN_VALIDAR,
        "sin_cota_inferior": SIN_COTA_INFERIOR,
        "pendiente": SIN_COTA_INFERIOR,
        "descartado": SIN_COTA_INFERIOR,
    }.items():
        (semanticos / f"{nombre}.py").write_text(codigo)

    def entrada(confirmacion: str, revisor: str | None) -> dict[str, str | None]:
        return {"origen": "llm:prueba", "confirmacion": confirmacion, "revisor": revisor}

    (mutantes / "precio_final" / "mutantes.json").write_text(
        json.dumps(
            {
                "referencia": "llm_flint_40b_free",
                "semanticos": {
                    "sin_validar": entrada("inseguro", "ana"),
                    "sin_cota_inferior": entrada("inseguro", "ana"),
                    "pendiente": entrada("pendiente", None),
                    "descartado": entrada("descartado", "ana"),
                },
                "sintacticos": {
                    "m3": {"clasificacion": "equivalente", "revisor": "ana"},
                    "m4": {"clasificacion": "hueco", "revisor": "ana"},
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
    assert conteo["pendientes"] == 1
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


def test_un_confirmado_sin_revisor_sigue_pendiente(tmp_path: Path) -> None:
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
    assert conteo["pendientes"] == 2


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
    assert "| precio_final | 4 | 1 | 1 | 2 | 2 | 1 | 0 |" in markdown  # semánticos
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
