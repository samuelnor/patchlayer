"""Experimento A/B/C: corre todos los pares (caso, parche) y cruza etiquetas con veredictos (#6, sección 6).

Aquí, y solo aquí, entra la etiqueta. Solo `evidencia_favorable` cuenta como aceptación.
"""

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from patchwise import formal
from patchwise.compuerta import Verificar, escribir_expediente, revisar
from patchwise.reglas import CONFIGURACIONES, hallazgos

CLASES = ("superficial", "regresivo", "correcto")


def experimento(
    casos_dir: Path,
    expedientes_dir: Path,
    resultados_dir: Path,
    verificar: Verificar = formal.verificar,
    timeout_s: float = 60,
) -> dict:
    """Revisa cada parche de cada caso y escribe experimento.json, reporte.html y tabla.md."""
    pares = []
    for caso_dir in sorted(p for p in casos_dir.iterdir() if (p / "caso.json").is_file()):
        etiquetas = _etiquetas(caso_dir)
        for parche_py in sorted((caso_dir / "parches").glob("*.py")):
            parche = parche_py.stem
            expediente = revisar(caso_dir, parche, verificar=verificar, timeout_s=timeout_s)
            escribir_expediente(expediente, expedientes_dir)
            etiqueta = etiquetas.get(parche, {})
            clase = etiqueta.get("clase")
            pares.append(
                {
                    "caso": caso_dir.name,
                    "parche": parche,
                    "clase": clase,
                    "origen": etiqueta.get("origen"),
                    "capas": {n: c["resultado"] for n, c in expediente["capas"].items()},
                    "veredictos": expediente["veredictos"],
                    "hallazgos": hallazgos(clase, expediente["veredictos"])
                    if clase
                    else ["parche sin etiqueta: fuera de la tabla"],
                    "pendientes": expediente["pendientes"],
                    "observaciones": expediente["observaciones"],
                }
            )

    tabla = _tabla(pares)
    resultado = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "pares": pares,
        "tabla": tabla,
    }

    resultados_dir.mkdir(parents=True, exist_ok=True)
    (resultados_dir / "experimento.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    )
    (resultados_dir / "tabla.md").write_text(tabla_markdown(tabla))
    (resultados_dir / "reporte.html").write_text(reporte_html(resultado))
    return resultado


def _etiquetas(caso_dir: Path) -> dict:
    ruta = caso_dir / "parches" / "etiquetas.json"
    return json.loads(ruta.read_text()) if ruta.exists() else {}


def _tabla(pares: list[dict]) -> dict:
    """Por configuración y clase: cuántos parches aceptó (evidencia_favorable) de cuántos."""
    return {
        config: {
            clase: {
                "aceptados": sum(
                    p["veredictos"][config] == "evidencia_favorable" for p in pares if p["clase"] == clase
                ),
                "total": sum(p["clase"] == clase for p in pares),
            }
            for clase in CLASES
        }
        for config in CONFIGURACIONES
    }


def tabla_markdown(tabla: dict) -> str:
    filas = [
        "| Configuración | Superficiales aceptados | Regresivos aceptados | Correctos aceptados |",
        "| --- | --- | --- | --- |",
    ]
    for config, por_clase in tabla.items():
        celdas = [f"{por_clase[c]['aceptados']}/{por_clase[c]['total']}" for c in CLASES]
        filas.append(f"| {config} | " + " | ".join(celdas) + " |")
    return "\n".join(filas) + "\n"


def reporte_html(resultado: dict) -> str:
    tabla = resultado["tabla"]
    filas_tabla = "".join(
        f"<tr><th>{config}</th>"
        + "".join(
            f"<td>{tabla[config][c]['aceptados']}/{tabla[config][c]['total']}</td>" for c in CLASES
        )
        + "</tr>"
        for config in tabla
    )
    filas_pares = "".join(_fila_par(p) for p in resultado["pares"])
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Experimento Patchwise</title>
<style>
:root {{ --fondo: #fff; --texto: #1a1a1a; --borde: #ccc; --suave: #f4f4f4; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --fondo: #161616; --texto: #e8e8e8; --borde: #444; --suave: #222; }}
}}
body {{ background: var(--fondo); color: var(--texto); font: 15px/1.5 system-ui, sans-serif;
  margin: 0 auto; max-width: 72rem; padding: 1rem; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; }}
th, td {{ border: 1px solid var(--borde); padding: .4rem .6rem; text-align: left; vertical-align: top; }}
thead th {{ background: var(--suave); }}
ul {{ margin: 0; padding-left: 1.1rem; }}
.envoltorio {{ overflow-x: auto; }}
</style>
</head>
<body>
<h1>Experimento A/B/C</h1>
<p>Generado en {escape(resultado["generado_en"])}. Solo <code>evidencia_favorable</code> cuenta como aceptación.</p>
<h2>Aceptaciones por configuración</h2>
<div class="envoltorio"><table>
<thead><tr><th>Configuración</th><th>Superficiales aceptados</th><th>Regresivos aceptados</th><th>Correctos aceptados</th></tr></thead>
<tbody>{filas_tabla}</tbody>
</table></div>
<h2>Pares (caso, parche)</h2>
<div class="envoltorio"><table>
<thead><tr><th>Caso</th><th>Parche</th><th>Clase</th><th>Capas</th><th>A / B / C</th><th>Hallazgos</th><th>Observaciones</th><th>Pendientes</th></tr></thead>
<tbody>{filas_pares}</tbody>
</table></div>
</body>
</html>
"""


def _fila_par(p: dict) -> str:
    capas = "<br>".join(f"{escape(n)}: {escape(r)}" for n, r in p["capas"].items())
    veredictos = "<br>".join(f"{c}: {escape(v)}" for c, v in p["veredictos"].items())
    return (
        f"<tr><td>{escape(p['caso'])}</td><td>{escape(p['parche'])}</td>"
        f"<td>{escape(p['clase'] or '—')}</td><td>{capas}</td><td>{veredictos}</td>"
        f"<td>{_lista(p['hallazgos'])}</td><td>{_lista(p['observaciones'])}</td>"
        f"<td>{_lista(p['pendientes'], '☐ ')}</td></tr>"
    )


def _lista(items: list[str], prefijo: str = "") -> str:
    if not items:
        return "—"
    return "<ul>" + "".join(f"<li>{prefijo}{escape(i)}</li>" for i in items) + "</ul>"
