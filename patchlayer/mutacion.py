"""Mutación: fiabilidad de la evidencia, fuera del corpus y de la métrica principal (#4, #14).

Dos métricas separadas, que no se suman:

- Mutantes semánticos: los escribe un LLM a partir del parche correcto de referencia y pasan
  por la cadena completa (A, B y C). Solo cuentan los que una persona confirmó como inseguros.
- Mutantes sintácticos: los genera mutmut sobre el mismo parche y solo se miden contra las
  suites de pytest (A y B). Una persona clasifica los sobrevivientes de B.

Nada de aquí toca un veredicto ni la tabla del experimento.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from patchlayer import formal
from patchlayer.compuerta import PRUEBAS, Verificar, escribir_expediente, revisar
from patchlayer.reglas import CONFIGURACIONES

# Códigos de salida de mutmut que cuentan como mutante detectado: prueba fallida, error
# interno de pytest y tiempo agotado. Cualquier otro (0, sin pruebas, sospechoso) sobrevive.
_DETECTADO = frozenset({1, 3, 24, -24, 36, 152, 255})


class SintacticoCrudo(TypedDict):
    """Un mutante de mutmut: a qué configuraciones sobrevive y su diff contra la referencia."""

    mutante: str
    sobrevive: dict[str, bool]
    diff: str


Sintacticos = Callable[[Path, Path, float], list[SintacticoCrudo]]


class Semantico(TypedDict):
    caso: str
    mutante: str
    origen: str | None
    confirmacion: str  # inseguro | descartado | sin_confirmar
    revisor: str | None
    capas: dict[str, str]
    veredictos: dict[str, str]
    contraejemplo: str | None


class ConteoSemanticos(TypedDict):
    generados: int
    descartados: int
    sin_confirmar: int
    confirmados: int
    sobrevivientes: dict[str, int]  # por configuración, solo entre los confirmados
    no_concluyentes: int  # confirmados que C no acepta sin haberlos refutado (#4)


class Sintactico(TypedDict):
    caso: str
    mutante: str
    sobrevive: dict[str, bool]
    diff: str
    revision: str | None  # equivalente | hueco; solo para sobrevivientes de B
    revisor: str | None


class ConteoSintacticos(TypedDict):
    generados: int
    sobrevivientes: dict[str, int]
    equivalentes: int
    huecos: int
    sin_revisar: int


class ResultadoSemanticos(TypedDict):
    mutantes: list[Semantico]
    por_caso: dict[str, ConteoSemanticos]


class ResultadoSintacticos(TypedDict):
    mutantes: list[Sintactico]
    por_caso: dict[str, ConteoSintacticos]
    errores: dict[str, str]  # casos donde mutmut no terminó: sin conteo, nunca cero


class Firma(TypedDict):
    firmado_por: str | None
    fecha: str | None


class ResultadoMutacion(TypedDict):
    generado_en: str
    firma: Firma
    semanticos: ResultadoSemanticos
    sintacticos: ResultadoSintacticos | None  # None: mutmut recortado (#7)


def mutacion(
    casos_dir: Path,
    mutantes_dir: Path,
    resultados_dir: Path,
    expedientes_dir: Path,
    verificar: Verificar = formal.verificar,
    timeout_s: float = 60,
    sintacticos: Sintacticos | None = None,
) -> ResultadoMutacion:
    """Corre los mutantes de cada caso y escribe mutacion.json y mutacion.md.

    `sintacticos=None` deja fuera a mutmut, que es lo primero que se recorta (#7).
    """
    semanticos: ResultadoSemanticos = {"mutantes": [], "por_caso": {}}
    sintacticos_res: ResultadoSintacticos = {"mutantes": [], "por_caso": {}, "errores": {}}

    for registro_json in sorted(mutantes_dir.glob("*/mutantes.json")):
        caso = registro_json.parent.name
        caso_dir = casos_dir / caso
        registro = json.loads(registro_json.read_text())
        referencia = caso_dir / "parches" / f"{registro['referencia']}.py"
        if _sha256(referencia) != registro["referencia_sha256"]:
            raise ValueError(
                f"{registro_json}: el parche de referencia {referencia} cambió desde que se "
                "generaron los mutantes; hay que regenerarlos y volver a revisarlos"
            )

        del_caso = _semanticos(
            caso_dir,
            registro_json.parent / "semanticos",
            registro.get("semanticos", {}),
            expedientes_dir / "mutantes",
            verificar,
            timeout_s,
        )
        semanticos["mutantes"] += del_caso
        semanticos["por_caso"][caso] = _contar_semanticos(del_caso)

        if sintacticos is not None:
            try:
                crudos = sintacticos(caso_dir, referencia, timeout_s)
            except RuntimeError as exc:  # mutmut cae primero; los semánticos se conservan (#7)
                sintacticos_res["errores"][caso] = str(exc)
                continue
            revisiones = registro.get("sintacticos", {})
            revisados = [
                _sintactico(caso, crudo, revisiones.get(crudo["mutante"], {})) for crudo in crudos
            ]
            sintacticos_res["mutantes"] += revisados
            sintacticos_res["por_caso"][caso] = _contar_sintacticos(revisados)

    firma_json = mutantes_dir / "firma.json"
    firma: dict[str, str | None] = (
        json.loads(firma_json.read_text()) if firma_json.exists() else {}
    )
    resultado: ResultadoMutacion = {
        "generado_en": datetime.now(UTC).isoformat(),
        "firma": {"firmado_por": firma.get("firmado_por"), "fecha": firma.get("fecha")},
        "semanticos": semanticos,
        "sintacticos": sintacticos_res if sintacticos is not None else None,
    }

    resultados_dir.mkdir(parents=True, exist_ok=True)
    (resultados_dir / "mutacion.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    )
    (resultados_dir / "mutacion.md").write_text(reporte_markdown(resultado))
    return resultado


def _semanticos(
    caso_dir: Path,
    semanticos_dir: Path,
    registro: dict[str, dict[str, str | None]],
    expedientes_dir: Path,
    verificar: Verificar,
    timeout_s: float,
) -> list[Semantico]:
    salida: list[Semantico] = []
    for mutante_py in sorted(semanticos_dir.glob("*.py")):
        mutante = mutante_py.stem
        entrada = registro.get(mutante, {})
        expediente = revisar(
            caso_dir, mutante, verificar=verificar, timeout_s=timeout_s, parches_dir=semanticos_dir
        )
        expediente["parche"]["origen"] = entrada.get("origen")  # no hay etiquetas.json aquí
        escribir_expediente(expediente, expedientes_dir)
        revisor = entrada.get("revisor")
        confirmacion = entrada.get("confirmacion")
        # La confirmación vale para el archivo que la persona leyó, no para uno editado después.
        vigente = entrada.get("sha256") == expediente["parche"]["sha256"]
        salida.append(
            {
                "caso": caso_dir.name,
                "mutante": mutante,
                "origen": entrada.get("origen"),
                # Sin una persona que firme la decisión, el mutante sigue sin confirmar.
                "confirmacion": confirmacion
                if revisor and vigente and confirmacion in ("inseguro", "descartado")
                else "sin_confirmar",
                "revisor": revisor,
                "capas": {n: c["resultado"] for n, c in expediente["capas"].items()},
                "veredictos": expediente["veredictos"],
                "contraejemplo": expediente["capas"]["verificador"]["contraejemplo"],
            }
        )
    return salida


def _contar_semanticos(mutantes: list[Semantico]) -> ConteoSemanticos:
    confirmados = [m for m in mutantes if m["confirmacion"] == "inseguro"]
    return {
        "generados": len(mutantes),
        "descartados": sum(m["confirmacion"] == "descartado" for m in mutantes),
        "sin_confirmar": sum(m["confirmacion"] == "sin_confirmar" for m in mutantes),
        "confirmados": len(confirmados),
        # Solo `evidencia_favorable` es aceptación: ahí el mutante inseguro sobrevive.
        "sobrevivientes": {
            config: sum(m["veredictos"][config] == "evidencia_favorable" for m in confirmados)
            for config in CONFIGURACIONES
        },
        "no_concluyentes": sum(m["veredictos"]["C"] == "no_concluyente" for m in confirmados),
    }


def _sintactico(caso: str, crudo: SintacticoCrudo, entrada: dict[str, str | None]) -> Sintactico:
    revisor = entrada.get("revisor")
    revision = entrada.get("revision")
    revisado = bool(revisor) and revision in ("equivalente", "hueco")
    return {
        "caso": caso,
        "mutante": crudo["mutante"],
        "sobrevive": crudo["sobrevive"],
        "diff": crudo["diff"],
        "revision": revision if revisado and crudo["sobrevive"]["B"] else None,
        "revisor": revisor,
    }


def _contar_sintacticos(mutantes: list[Sintactico]) -> ConteoSintacticos:
    de_b = [m for m in mutantes if m["sobrevive"]["B"]]
    return {
        "generados": len(mutantes),
        "sobrevivientes": {
            config: sum(m["sobrevive"][config] for m in mutantes) for config in ("A", "B")
        },
        "equivalentes": sum(m["revision"] == "equivalente" for m in de_b),
        "huecos": sum(m["revision"] == "hueco" for m in de_b),
        "sin_revisar": sum(m["revision"] is None for m in de_b),
    }


def correr_mutmut(caso_dir: Path, referencia: Path, timeout_s: float) -> list[SintacticoCrudo]:
    """Muta `referencia` con mutmut y corre la suite de A y la de B contra cada mutante.

    Arma el directorio igual que la compuerta (contrato/ + parche como objetivo.py), una vez
    por configuración. Lanza `RuntimeError` si mutmut no deja un resultado por mutante o agota
    `timeout_s` (por invocación): una corrida rota no se reporta como cero sobrevivientes.
    """
    sobrevive: dict[str, dict[str, bool]] = {}
    diffs: dict[str, str] = {}
    for config in ("A", "B"):
        with tempfile.TemporaryDirectory(prefix="patchlayer-mutmut-") as tmp:
            directorio = Path(tmp)
            shutil.copytree(caso_dir / "contrato", directorio / "contrato")
            shutil.copy(referencia, directorio / "objetivo.py")
            pruebas = "".join(
                f"\n    contrato/{PRUEBAS[capa]}" for capa in CONFIGURACIONES[config]
            )
            (directorio / "setup.cfg").write_text(
                "[mutmut]\nsource_paths=objetivo.py\nalso_copy=\n    contrato\n"
                f"pytest_add_cli_args_test_selection={pruebas}\n"
            )
            proc = _mutmut(directorio, ["run"], timeout_s)
            meta = directorio / "mutants" / "objetivo.py.meta"
            codigos: dict[str, int | None] = (
                json.loads(meta.read_text())["exit_code_by_key"] if meta.exists() else {}
            )
            if proc.returncode != 0 or not codigos or None in codigos.values():
                raise RuntimeError(
                    f"mutmut no terminó sobre {referencia} (configuración {config}):\n"
                    + proc.stdout
                    + proc.stderr
                )
            for mutante, codigo in codigos.items():
                sobrevive.setdefault(mutante, {})[config] = codigo not in _DETECTADO
                if config == "B" and sobrevive[mutante]["B"]:
                    mostrado = _mutmut(directorio, ["show", mutante], timeout_s).stdout
                    # La primera línea es `# <mutante>: survived`; el diff empieza en `---`.
                    diffs[mutante] = mostrado[max(mostrado.find("--- "), 0) :]
    return [
        {"mutante": mutante, "sobrevive": por_config, "diff": diffs.get(mutante, "")}
        for mutante, por_config in sobrevive.items()
    ]


def _mutmut(
    directorio: Path, argumentos: list[str], timeout_s: float
) -> subprocess.CompletedProcess[str]:
    """Entorno casi vacío, como en la compuerta: el mutante se importa y no hereda secretos."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "mutmut", *argumentos],
            cwd=directorio,
            env={"PATH": "", "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"mutmut {argumentos[0]} agotó el tiempo límite de {timeout_s:g} s"
        ) from exc


def _sha256(archivo: Path) -> str:
    return hashlib.sha256(archivo.read_bytes()).hexdigest()


def reporte_markdown(resultado: ResultadoMutacion) -> str:
    """El reporte de mutación: conteos absolutos y lo que falta por revisar a mano (#4)."""
    firma = resultado["firma"]
    lineas = [
        "# Reporte de mutación",
        "",
        f"Generado en {resultado['generado_en']}. Fuera del corpus y de la métrica principal: "
        "mide la fiabilidad de la evidencia, no cambia ningún veredicto.",
        "",
        f"Firmado por {firma['firmado_por']} el {firma['fecha']}."
        if firma["firmado_por"]
        else "**Reporte sin firmar**: falta que una persona lo revise y llene "
        "`mutantes/firma.json`.",
        "",
        "## Mutantes semánticos (A, B y C)",
        "",
        "Solo cuentan los confirmados como inseguros por una persona. Un mutante sobrevive a "
        "una configuración si esta le da `evidencia_favorable`; un no concluyente no lo acepta, "
        "pero tampoco lo refuta, y se cuenta aparte.",
        "",
        "| Caso | Generados | Descartados | Sin confirmar | Confirmados "
        "| Sobreviven A | Sobreviven B | Sobreviven C | No concluyentes en C |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    semanticos = resultado["semanticos"]
    filas_sem = [
        [c["generados"], c["descartados"], c["sin_confirmar"], c["confirmados"]]
        + [c["sobrevivientes"][config] for config in CONFIGURACIONES]
        + [c["no_concluyentes"]]
        for c in semanticos["por_caso"].values()
    ]
    lineas += _filas(list(semanticos["por_caso"]), filas_sem)

    sin_confirmar = [m for m in semanticos["mutantes"] if m["confirmacion"] == "sin_confirmar"]
    if sin_confirmar:
        lineas += ["", "Sin confirmación humana (no cuentan en la tabla):", ""]
        lineas += [
            f"- ☐ `{m['caso']}/{m['mutante']}`: "
            + ", ".join(f"{config} {v}" for config, v in m["veredictos"].items())
            + (f"; contraejemplo `{m['contraejemplo']}`" if m["contraejemplo"] else "")
            for m in sin_confirmar
        ]

    lineas += ["", "## Mutantes sintácticos (mutmut, solo A y B)", ""]
    sintacticos = resultado["sintacticos"]
    if sintacticos is None:
        lineas.append("Los mutantes sintácticos no se corrieron en esta ejecución (recorte de #7).")
        return "\n".join(lineas) + "\n"

    lineas += [
        "Una persona clasifica cada sobreviviente de B como equivalente o hueco real de la suite.",
        "",
        "| Caso | Generados | Sobreviven A | Sobreviven B | Equivalentes | Huecos | Sin revisar |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    filas_sin = [
        [
            c["generados"],
            c["sobrevivientes"]["A"],
            c["sobrevivientes"]["B"],
            c["equivalentes"],
            c["huecos"],
            c["sin_revisar"],
        ]
        for c in sintacticos["por_caso"].values()
    ]
    lineas += _filas(list(sintacticos["por_caso"]), filas_sin)
    for caso, error in sintacticos["errores"].items():
        lineas += ["", f"**mutmut falló en `{caso}`** (sin conteo):", "", "```", error, "```"]

    for m in sintacticos["mutantes"]:
        if m["sobrevive"]["B"]:
            estado = m["revision"] or "☐ sin revisar"
            lineas += ["", f"### `{m['caso']}` · `{m['mutante']}` · {estado}", ""]
            lineas += ["```diff", m["diff"].rstrip("\n"), "```"]
    return "\n".join(lineas) + "\n"


def _filas(casos: list[str], filas: list[list[int]]) -> list[str]:
    """Una fila por caso y una de totales."""
    total = [sum(columna) for columna in zip(*filas, strict=True)]
    con_total = [*zip(casos, filas, strict=True), ("**Total**", total)]
    return [f"| {caso} | " + " | ".join(str(n) for n in fila) + " |" for caso, fila in con_total]
