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
