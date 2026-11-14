"""Experimento A/B/C: corre todos los pares (caso, parche) y cruza etiquetas con veredictos.

Formato en #6, sección 6.

Aquí, y solo aquí, entra la etiqueta. Solo `evidencia_favorable` cuenta como aceptación.
"""

import json
import statistics
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import TypedDict

from patchlayer import formal
from patchlayer.compuerta import Verificar, escribir_expediente, revisar
from patchlayer.reglas import CONFIGURACIONES, hallazgos

CLASES = ("superficial", "regresivo", "correcto")


class Par(TypedDict):
    """Un par (caso, parche) del experimento, con su etiqueta ya cruzada."""

    caso: str
    parche: str
    clase: str | None
    origen: str | None
    capas: dict[str, str]
    duraciones: dict[str, float]  # segundos de reloj por capa
    veredictos: dict[str, str]
    hallazgos: list[str]
    pendientes: list[str]
    observaciones: list[str]


class Conteo(TypedDict):
    aceptados: int
    total: int


Tabla = dict[str, dict[str, Conteo]]  # configuración -> clase -> conteo


class FalsosRechazos(TypedDict):
    """Parches correctos que una configuración no acepta, por motivo (#4)."""

    por_falla: int
    por_no_concluyente: int
    correctos: int  # parches correctos en el corpus


class Costo(TypedDict):
    mediana_s: float
    maximo_s: float


class Metricas(TypedDict):
    """Métricas secundarias de #4, en conteos absolutos."""

    falsos_rechazos: dict[str, FalsosRechazos]  # configuración -> conteo
    # configuración -> clase -> "caso/parche" que esa configuración no acepta
    # y la anterior sí (para A: todo lo que A no acepta)
    deteccion_marginal: dict[str, dict[str, list[str]]]
    no_concluyentes: dict[str, int]  # capa -> pares en que dio no_concluyente
    costo_por_capa: dict[str, Costo]  # capa -> segundos por parche
    timeout_s: float  # tiempo límite de cada capa, declarado junto al costo


class ResultadoExperimento(TypedDict):
    generado_en: str
    pares: list[Par]
    tabla: Tabla
    metricas: Metricas


def experimento(
    casos_dir: Path,
    expedientes_dir: Path,
    resultados_dir: Path,
    verificar: Verificar = formal.verificar,
    timeout_s: float = 60,
) -> ResultadoExperimento:
    """Revisa cada parche de cada caso y escribe experimento.json, reporte.html y tabla.md."""
    pares: list[Par] = []
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
                    "duraciones": {
                        n: c["duracion_s"] for n, c in expediente["capas"].items()
                    },
                    "veredictos": expediente["veredictos"],
                    "hallazgos": hallazgos(clase, expediente["veredictos"])
                    if clase
                    else ["parche sin etiqueta: fuera de la tabla"],
                    "pendientes": expediente["pendientes"],
                    "observaciones": expediente["observaciones"],
                }
            )

    tabla = _tabla(pares)
    resultado: ResultadoExperimento = {
        "generado_en": datetime.now(UTC).isoformat(),
        "pares": pares,
        "tabla": tabla,
        "metricas": _metricas(pares, timeout_s),
    }

    resultados_dir.mkdir(parents=True, exist_ok=True)
    (resultados_dir / "experimento.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    )
    (resultados_dir / "tabla.md").write_text(
        tabla_markdown(tabla) + "\n" + metricas_markdown(resultado["metricas"])
    )
    (resultados_dir / "reporte.html").write_text(reporte_html(resultado))
    return resultado


def _etiquetas(caso_dir: Path) -> dict[str, dict[str, str]]:
    ruta = caso_dir / "parches" / "etiquetas.json"
    return json.loads(ruta.read_text()) if ruta.exists() else {}


def _tabla(pares: list[Par]) -> Tabla:
    """Por configuración y clase: cuántos parches aceptó (evidencia_favorable) de cuántos."""
    return {
        config: {
            clase: {
                "aceptados": sum(
                    p["veredictos"][config] == "evidencia_favorable"
                    for p in pares
                    if p["clase"] == clase
                ),
                "total": sum(p["clase"] == clase for p in pares),
            }
            for clase in CLASES
        }
        for config in CONFIGURACIONES
    }


def _metricas(pares: list[Par], timeout_s: float) -> Metricas:
    capas = CONFIGURACIONES["C"]
    correctos = [p for p in pares if p["clase"] == "correcto"]
    return {
        "falsos_rechazos": {
            config: {
                "por_falla": sum(p["veredictos"][config] == "rechazado" for p in correctos),
                "por_no_concluyente": sum(
                    p["veredictos"][config] == "no_concluyente" for p in correctos
                ),
                "correctos": len(correctos),
            }
            for config in CONFIGURACIONES
        },
        "deteccion_marginal": _deteccion_marginal(pares),
        "no_concluyentes": {
            capa: sum(p["capas"][capa] == "no_concluyente" for p in pares) for capa in capas
        },
        "costo_por_capa": {capa: _costo([p["duraciones"][capa] for p in pares]) for capa in capas},
        "timeout_s": timeout_s,
    }


def _costo(duraciones: list[float]) -> Costo:
    if not duraciones:
        return {"mediana_s": 0.0, "maximo_s": 0.0}
    return {"mediana_s": statistics.median(duraciones), "maximo_s": max(duraciones)}


def _deteccion_marginal(pares: list[Par]) -> dict[str, dict[str, list[str]]]:
    def acepta(p: Par, config: str | None) -> bool:
        return config is None or p["veredictos"][config] == "evidencia_favorable"

    configs = list(CONFIGURACIONES)
    return {
        config: {
            clase: [
                f"{p['caso']}/{p['parche']}"
                for p in pares
                if p["clase"] == clase and acepta(p, anterior) and not acepta(p, config)
            ]
            for clase in CLASES
        }
        for anterior, config in zip([None, *configs], configs, strict=False)
    }


class Seccion(TypedDict):
    """Una tabla de métricas, lista para Markdown o HTML."""

    titulo: str
    nota: str
    encabezados: list[str]
    filas: list[list[str]]


def _secciones(m: Metricas) -> list[Seccion]:
    def marginal(nombres: list[str]) -> str:
        return f"{len(nombres)}: {', '.join(nombres)}" if nombres else "0"

    return [
        {
            "titulo": "Falsos rechazos",
            "nota": "Parches correctos que la configuración no acepta.",
            "encabezados": ["Configuración", "Por falla", "Por no concluyente", "Correctos"],
            "filas": [
                [c, str(f["por_falla"]), str(f["por_no_concluyente"]), str(f["correctos"])]
                for c, f in m["falsos_rechazos"].items()
            ],
        },
        {
            "titulo": "No concluyentes por capa",
            "nota": "Pares (caso, parche) en que la capa no dio ni pasa ni falla.",
            "encabezados": ["Capa", "Pares"],
            "filas": [[capa, str(n)] for capa, n in m["no_concluyentes"].items()],
        },
        {
            "titulo": "Costo temporal por capa",
            "nota": f"Segundos de reloj por parche. Tiempo límite por capa: {m['timeout_s']:g} s "
            f"(CrossHair: `--per_condition_timeout={m['timeout_s'] / 2:g}`).",
            "encabezados": ["Capa", "Mediana (s)", "Máximo (s)"],
            "filas": [
                [capa, f"{c['mediana_s']:.2f}", f"{c['maximo_s']:.2f}"]
                for capa, c in m["costo_por_capa"].items()
            ],
        },
        {
            "titulo": "Detección marginal",
            "nota": "Parches que la configuración no acepta y la anterior sí (A: todo lo que "
            "A no acepta). En la columna de correctos son falsos rechazos, no detecciones.",
            "encabezados": ["Configuración", "Superficiales", "Regresivos", "Correctos"],
            "filas": [
                [c, *(marginal(por_clase[clase]) for clase in CLASES)]
                for c, por_clase in m["deteccion_marginal"].items()
            ],
        },
    ]


def metricas_markdown(metricas: Metricas) -> str:
    bloques: list[str] = []
    for s in _secciones(metricas):
        filas = [
            f"## {s['titulo']}",
            "",
            s["nota"],
            "",
            "| " + " | ".join(s["encabezados"]) + " |",
            "|" + " --- |" * len(s["encabezados"]),
            *("| " + " | ".join(f) + " |" for f in s["filas"]),
        ]
        bloques.append("\n".join(filas) + "\n")
    return "\n".join(bloques)


def _metricas_html(metricas: Metricas) -> str:
    return "".join(
        f"<h2>{escape(s['titulo'])}</h2><p>{escape(s['nota'])}</p>"
        '<div class="envoltorio"><table><thead><tr>'
        + "".join(f"<th>{escape(e)}</th>" for e in s["encabezados"])
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{escape(c)}</td>" for c in f) + "</tr>" for f in s["filas"]
        )
        + "</tbody></table></div>\n"
        for s in _secciones(metricas)
    )


def tabla_markdown(tabla: Tabla) -> str:
    filas = [
        "| Configuración | Superficiales aceptados | Regresivos aceptados | Correctos aceptados |",
        "| --- | --- | --- | --- |",
    ]
    for config, por_clase in tabla.items():
        celdas = [f"{por_clase[c]['aceptados']}/{por_clase[c]['total']}" for c in CLASES]
        filas.append(f"| {config} | " + " | ".join(celdas) + " |")
    return "\n".join(filas) + "\n"


def reporte_html(resultado: ResultadoExperimento) -> str:
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
<title>Experimento Patchlayer</title>
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
{_metricas_html(resultado["metricas"])}<h2>Pares (caso, parche)</h2>
<div class="envoltorio"><table>
<thead><tr><th>Caso</th><th>Parche</th><th>Clase</th><th>Capas</th><th>A / B / C</th><th>Hallazgos</th><th>Observaciones</th><th>Pendientes</th></tr></thead>
<tbody>{filas_pares}</tbody>
</table></div>
</body>
</html>
"""  # noqa: E501 - plantilla HTML


def _fila_par(p: Par) -> str:
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
