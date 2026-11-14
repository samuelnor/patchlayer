"""`experimento` recorre el corpus y cruza etiquetas con veredictos (#6, sección 6)."""

import json
import shutil
from pathlib import Path

from patchlayer.capas import ResultadoCapa
from patchlayer.experimento import ResultadoExperimento, experimento

CASOS = Path(__file__).resolve().parents[1] / "casos"

CORRECTO = '''def precio_final(precio: int, descuento_pct: int) -> int:
    if not 0 <= descuento_pct <= 100:
        raise ValueError("descuento fuera de rango")
    return precio - (precio * descuento_pct) // 100
'''


def verificador_que_confirma(directorio: Path, timeout_s: float) -> ResultadoCapa:
    return ResultadoCapa(
        resultado="pasa",
        herramienta="crosshair",
        version="stub",
        comando="crosshair check",
        duracion_s=0.0,
        salida="",
        detalle="confirmado",
    )


def corpus(tmp_path: Path) -> Path:
    casos = tmp_path / "casos"
    shutil.copytree(CASOS / "precio_final", casos / "precio_final")
    parches = casos / "precio_final" / "parches"
    for candidato in parches.glob("*.py"):  # el corpus real crece; aquí solo control + rango
        if candidato.stem != "control":
            candidato.unlink()
    (parches / "rango.py").write_text(CORRECTO)
    (parches / "etiquetas.json").write_text(
        json.dumps(
            {
                "control": {"clase": "superficial", "origen": "control"},
                "rango": {"clase": "correcto", "origen": "humano"},
            }
        )
    )
    return casos


def correr(tmp_path: Path) -> ResultadoExperimento:
    return experimento(
        corpus(tmp_path),
        expedientes_dir=tmp_path / "expedientes",
        resultados_dir=tmp_path / "resultados",
        verificar=verificador_que_confirma,
    )


def test_cada_par_trae_su_etiqueta_veredictos_y_hallazgos(tmp_path: Path) -> None:
    resultado = correr(tmp_path)

    pares = {(p["caso"], p["parche"]): p for p in resultado["pares"]}
    assert set(pares) == {("precio_final", "control"), ("precio_final", "rango")}
    control = pares[("precio_final", "control")]
    assert control["clase"] == "superficial"
    assert control["veredictos"] == {
        "A": "evidencia_favorable",
        "B": "rechazado",
        "C": "rechazado",
    }
    assert control["hallazgos"] == ["parche superficial aceptado por A (falso negativo de A)"]
    assert pares[("precio_final", "rango")]["hallazgos"] == []


def test_la_tabla_cuenta_aceptaciones_por_clase_y_configuracion(tmp_path: Path) -> None:
    tabla = correr(tmp_path)["tabla"]

    assert tabla["A"]["superficial"] == {"aceptados": 1, "total": 1}
    assert tabla["B"]["superficial"] == {"aceptados": 0, "total": 1}
    assert tabla["C"]["superficial"] == {"aceptados": 0, "total": 1}
    assert tabla["C"]["correcto"] == {"aceptados": 1, "total": 1}
    assert tabla["C"]["regresivo"] == {"aceptados": 0, "total": 0}


def test_escribe_json_html_markdown_y_un_expediente_por_par(tmp_path: Path) -> None:
    correr(tmp_path)

    resultados = tmp_path / "resultados"
    assert json.loads((resultados / "experimento.json").read_text())["pares"]
    html = (resultados / "reporte.html").read_text()
    assert "<table" in html
    assert "falso negativo de A" in html
    assert "| C |" in (resultados / "tabla.md").read_text()
    assert (tmp_path / "expedientes" / "precio_final" / "rango.json").exists()


def verificador_que_no_confirma(directorio: Path, timeout_s: float) -> ResultadoCapa:
    return ResultadoCapa(
        resultado="no_concluyente",
        herramienta="crosshair",
        version="stub",
        comando="crosshair check",
        duracion_s=0.0,
        salida="",
        detalle="no confirmado",
    )


def correr_sin_confirmar(tmp_path: Path) -> ResultadoExperimento:
    return experimento(
        corpus(tmp_path),
        expedientes_dir=tmp_path / "expedientes",
        resultados_dir=tmp_path / "resultados",
        verificar=verificador_que_no_confirma,
        timeout_s=7,
    )


def test_falsos_rechazos_separan_falla_de_no_concluyente(tmp_path: Path) -> None:
    metricas = correr_sin_confirmar(tmp_path)["metricas"]

    assert metricas["falsos_rechazos"]["A"] == {
        "por_falla": 0, "por_no_concluyente": 0, "total": 1
    }  # fmt: skip
    assert metricas["falsos_rechazos"]["C"] == {
        "por_falla": 0, "por_no_concluyente": 1, "total": 1
    }  # fmt: skip


def test_deteccion_marginal_lista_lo_que_cada_configuracion_detiene_y_la_anterior_no(
    tmp_path: Path,
) -> None:
    marginal = correr_sin_confirmar(tmp_path)["metricas"]["deteccion_marginal"]

    assert marginal == {
        "A": {"superficial": [], "regresivo": [], "correcto": []},
        "B": {"superficial": ["precio_final/control"], "regresivo": [], "correcto": []},
        "C": {"superficial": [], "regresivo": [], "correcto": ["precio_final/rango"]},
    }


def test_cuenta_no_concluyentes_por_capa(tmp_path: Path) -> None:
    metricas = correr_sin_confirmar(tmp_path)["metricas"]

    assert metricas["no_concluyentes"] == {"funcional": 0, "exploit": 0, "verificador": 2}


def test_costo_por_capa_da_mediana_y_maximo_junto_al_tiempo_limite(tmp_path: Path) -> None:
    metricas = correr_sin_confirmar(tmp_path)["metricas"]

    assert metricas["timeout_s"] == 7
    assert metricas["costo_por_capa"]["verificador"] == {"mediana_s": 0.0, "maximo_s": 0.0}
    funcional = metricas["costo_por_capa"]["funcional"]
    assert 0 < funcional["mediana_s"] <= funcional["maximo_s"]


def test_markdown_y_html_muestran_las_metricas_secundarias(tmp_path: Path) -> None:
    correr_sin_confirmar(tmp_path)

    resultados = tmp_path / "resultados"
    markdown = (resultados / "tabla.md").read_text()
    assert "| C | 0 | 1 | 1 |" in markdown  # falsos rechazos: por falla, no concluyente, total
    assert "| verificador | 2 |" in markdown  # no concluyentes
    assert "Tiempo límite por capa: 7 s" in markdown
    assert "1: precio_final/rango" in markdown  # detección marginal de C
    html = (resultados / "reporte.html").read_text()
    assert "Falsos rechazos" in html
    assert "1: precio_final/rango" in html
