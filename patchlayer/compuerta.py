"""Compuerta: corre la cadena sobre un parche candidato y arma su expediente (#6)."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pytest

from patchlayer import formal
from patchlayer.capas import PENDIENTES, Expediente, Resultado, ResultadoCapa
from patchlayer.reglas import observaciones, veredictos

Verificar = Callable[[Path, float], ResultadoCapa]

LIMITES_FIJOS = [
    "búsqueda simbólica acotada, no prueba",
    "la propiedad cubre solo lo que escribe el contrato",
    "aislamiento débil: subproceso con tiempo límite, sin entorno aislado sin red ni secretos",
]

PRUEBAS = {"funcional": "test_funcional.py", "exploit": "exploit.py"}


def revisar(
    caso_dir: Path,
    parche: str,
    verificar: Verificar = formal.verificar,
    timeout_s: float = 60,
) -> Expediente:
    """Corre siempre las tres capas sobre `parches/<parche>.py` y devuelve el expediente."""
    caso = json.loads((caso_dir / "caso.json").read_text())
    parche_py = caso_dir / "parches" / f"{parche}.py"

    with tempfile.TemporaryDirectory(prefix="patchlayer-") as tmp:
        directorio = Path(tmp)
        shutil.copytree(caso_dir / "contrato", directorio / "contrato")
        shutil.copy(parche_py, directorio / "objetivo.py")

        carga = _importar_objetivo(directorio, timeout_s)
        if carga is None:
            capas = {
                nombre: _pytest(directorio, archivo, timeout_s)
                for nombre, archivo in PRUEBAS.items()
            }
            capas["verificador"] = _verificador(verificar, directorio, timeout_s)
        else:
            capas = _sin_carga(*carga)

    resultados = {nombre: capa.resultado for nombre, capa in capas.items()}
    ver = veredictos(resultados)
    no_concluyentes = [(n, c) for n, c in capas.items() if c.resultado == "no_concluyente"]

    return {
        "caso": {k: caso[k] for k in ("id", "cwe", "vulnerabilidad", "propiedad")},
        "parche": {
            "id": parche,
            "sha256": _sha256(parche_py.read_bytes()),
            "origen": _origen(caso_dir, parche),
        },
        "contrato_sha256": _sha256_dir(caso_dir / "contrato"),
        "capas": {nombre: asdict(capa) for nombre, capa in capas.items()},
        "veredictos": ver,
        "sin_verificar": LIMITES_FIJOS
        + caso.get("limites", [])
        + [f"capa {n}: {c.detalle}" for n, c in no_concluyentes],
        "pendientes": [c.pendiente for _, c in no_concluyentes if c.pendiente],
        "observaciones": observaciones(resultados, ver),
        "generado_en": datetime.now(UTC).isoformat(),
    }


def escribir_expediente(expediente: Expediente, raiz: Path) -> Path:
    """Escribe `<raiz>/<caso>/<parche>.json` y devuelve su ruta."""
    ruta = raiz / expediente["caso"]["id"] / f"{expediente['parche']['id']}.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(expediente, ensure_ascii=False, indent=2) + "\n")
    return ruta


def _entorno(directorio: Path) -> dict[str, str]:
    return {"PYTHONPATH": str(directorio), "PATH": "", "PYTHONDONTWRITEBYTECODE": "1"}


def _importar_objetivo(directorio: Path, timeout_s: float) -> tuple[bool, str] | None:
    """None si el parche carga; si no, (agotó_el_tiempo, salida del intento)."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", "import objetivo"],
            cwd=directorio,
            env=_entorno(directorio),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        return True, _texto(exc.stderr)
    return None if proc.returncode == 0 else (False, proc.stdout + proc.stderr)


def _pytest(directorio: Path, archivo: str, timeout_s: float) -> ResultadoCapa:
    comando = [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"contrato/{archivo}"
    ]  # fmt: skip
    base = dict(
        herramienta="pytest",
        version=pytest.__version__,
        comando=" ".join(["python", *comando[1:]]),
    )
    inicio = time.monotonic()
    try:
        proc = subprocess.run(
            comando,
            cwd=directorio,
            env=_entorno(directorio),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        return ResultadoCapa(
            resultado="no_concluyente",
            duracion_s=time.monotonic() - inicio,
            salida=_texto(exc.stdout),
            detalle=f"agotó el tiempo límite de {timeout_s:g} s",
            pendiente=PENDIENTES["timeout"],
            **base,
        )
    # 0: todo en verde; 1: alguna prueba falló. Cualquier otro código (colección,
    # uso, sin pruebas) no dice nada del parche: no concluyente.
    concluyentes: dict[int, Resultado] = {0: "pasa", 1: "falla"}
    concluyente = concluyentes.get(proc.returncode)
    return ResultadoCapa(
        resultado=concluyente or "no_concluyente",
        duracion_s=time.monotonic() - inicio,
        salida=proc.stdout + proc.stderr,
        detalle=f"pytest terminó con código {proc.returncode}",
        pendiente=None if concluyente else PENDIENTES["error_capa"],
        **base,
    )


def _verificador(verificar: Verificar, directorio: Path, timeout_s: float) -> ResultadoCapa:
    """Falla cerrada: si la capa formal lanza, la capa queda no concluyente."""
    inicio = time.monotonic()
    try:
        capa = verificar(directorio, timeout_s)
        if capa.resultado not in ("pasa", "falla", "no_concluyente"):
            capa.detalle = f"resultado inválido de la capa formal: {capa.resultado!r}"
            capa.resultado = "no_concluyente"
            capa.pendiente = PENDIENTES["error_capa"]
        elif capa.resultado == "no_concluyente" and not capa.pendiente:
            capa.pendiente = PENDIENTES["no_confirmado"]
        return capa
    except Exception as exc:
        return ResultadoCapa(
            resultado="no_concluyente",
            herramienta="crosshair",
            version="desconocida",
            comando="patchlayer.formal.verificar",
            duracion_s=time.monotonic() - inicio,
            salida="",
            detalle=f"la capa formal lanzó {type(exc).__name__}: {exc}",
            pendiente=PENDIENTES["error_capa"],
        )


def _sin_carga(agoto_tiempo: bool, salida: str) -> dict[str, ResultadoCapa]:
    """Si el parche no carga, la funcional falla y lo demás queda no concluyente (#6, sección 3).

    Si importar agota el tiempo límite, las tres capas quedan no concluyentes.
    """
    if agoto_tiempo:
        detalle = "importar objetivo.py agotó el tiempo límite"
        pendiente = PENDIENTES["timeout"]
    else:
        detalle = "el parche no carga (error al importar objetivo.py)"
        pendiente = PENDIENTES["importacion"]

    def capa(resultado: Resultado, herramienta: str, version: str) -> ResultadoCapa:
        return ResultadoCapa(
            resultado=resultado,
            herramienta=herramienta,
            version=version,
            comando="python -c 'import objetivo'",
            duracion_s=0.0,
            salida=salida,
            detalle=detalle,
            pendiente=None if resultado == "falla" else pendiente,
        )

    return {
        "funcional": capa(
            "no_concluyente" if agoto_tiempo else "falla", "pytest", pytest.__version__
        ),
        "exploit": capa("no_concluyente", "pytest", pytest.__version__),
        "verificador": capa("no_concluyente", "crosshair", "no ejecutado"),
    }


def _origen(caso_dir: Path, parche: str) -> str | None:
    etiquetas = caso_dir / "parches" / "etiquetas.json"
    if not etiquetas.exists():
        return None
    return json.loads(etiquetas.read_text()).get(parche, {}).get("origen")


def _sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def _sha256_dir(directorio: Path) -> str:
    h = hashlib.sha256()
    archivos = (
        p for p in directorio.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )
    for archivo in sorted(archivos):
        h.update(archivo.relative_to(directorio).as_posix().encode() + b"\0")
        h.update(archivo.read_bytes())
    return h.hexdigest()


def _texto(salida: bytes | str | None) -> str:
    if isinstance(salida, bytes):
        return salida.decode(errors="replace")
    return salida or ""
