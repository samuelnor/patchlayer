"""Valida estructura, etiquetas y comportamiento de las 3 capas para los 4 casos adicionales."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

DIR_CASOS = Path(__file__).resolve().parents[1] / "casos"
CASOS_ADICIONALES = ["transferir", "ver_factura", "cancelar_pedido", "puede_leer"]

# (funcional_rc, exploit_rc, crosshair_rc) esperados por rol/etiqueta
RESULTADOS_ESPERADOS: dict[str, tuple[int, int, int]] = {
    "control": (0, 1, 1),
    "correcto": (0, 0, 0),
    "superficial": (0, 0, 1),
    "regresivo": (1, 0, 0),
}


def _ejecutar_en_directorio(
    caso: str, parche: Path, cmd: list[str], tmp_path: Path
) -> subprocess.CompletedProcess[str]:
    """Arma el directorio como la compuerta (#6) y ejecuta un comando de capa."""
    shutil.copytree(DIR_CASOS / caso / "contrato", tmp_path / "contrato", dirs_exist_ok=True)
    shutil.copy(parche, tmp_path / "objetivo.py")
    return subprocess.run(
        cmd,
        cwd=tmp_path,
        env={"PYTHONPATH": str(tmp_path), "PATH": ""},
        capture_output=True,
        text=True,
        timeout=30,
    )


def _verificar_capas(caso: str, parche: Path, clase: str, tmp_path: Path) -> None:
    """Comprueba que funcional, exploit y CrossHair devuelven los códigos esperados."""
    esp_funcional, esp_exploit, esp_formal = RESULTADOS_ESPERADOS[clase]

    rc_funcional = _ejecutar_en_directorio(
        caso,
        parche,
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "contrato/test_funcional.py"],
        tmp_path,
    ).returncode
    assert rc_funcional == esp_funcional, f"{parche.name}: funcional={rc_funcional}"

    rc_exploit = _ejecutar_en_directorio(
        caso,
        parche,
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "contrato/exploit.py"],
        tmp_path,
    ).returncode
    assert rc_exploit == esp_exploit, f"{parche.name}: exploit={rc_exploit}"

    res_formal = _ejecutar_en_directorio(
        caso,
        parche,
        [
            sys.executable,
            "-m",
            "crosshair",
            "check",
            "--report_all",
            "--analysis_kind=PEP316",
            "contrato/propiedad.py",
        ],
        tmp_path,
    )
    assert res_formal.returncode == esp_formal, f"{parche.name}: {res_formal.stdout}{res_formal.stderr}"
    if esp_formal == 1:
        assert "error:" in res_formal.stdout


def _leer_etiquetas(caso: str) -> dict[str, dict[str, str]]:
    return json.loads((DIR_CASOS / caso / "parches" / "etiquetas.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("caso", CASOS_ADICIONALES)
def test_estructura_de_caso_y_etiquetas(caso):
    meta_caso = json.loads((DIR_CASOS / caso / "caso.json").read_text(encoding="utf-8"))
    assert set(meta_caso) == {"id", "cwe", "vulnerabilidad", "propiedad", "limites"}
    assert meta_caso["id"] == caso
    assert isinstance(meta_caso["limites"], list) and len(meta_caso["limites"]) > 0

    objetivo = (DIR_CASOS / caso / "objetivo.py").read_text(encoding="utf-8")
    control = (DIR_CASOS / caso / "parches" / "control.py").read_text(encoding="utf-8")
    assert control == objetivo

    etiquetas = _leer_etiquetas(caso)
    assert etiquetas["control"] == {"clase": "superficial", "origen": "control"}

    candidatos = {k: v for k, v in etiquetas.items() if k != "control"}
    assert len(candidatos) == 4
    clases = [v["clase"] for v in candidatos.values()]
    assert clases.count("correcto") == 1
    assert clases.count("superficial") == 2
    assert clases.count("regresivo") == 1

    for nombre, meta in etiquetas.items():
        assert set(meta) == {"clase", "origen"}
        assert meta["origen"]
        assert (DIR_CASOS / caso / "parches" / f"{nombre}.py").is_file()


@pytest.mark.parametrize("caso", CASOS_ADICIONALES)
def test_control_y_candidatos_se_comportan_segun_su_etiqueta(caso, tmp_path):
    for nombre, meta in _leer_etiquetas(caso).items():
        sub = tmp_path / nombre
        sub.mkdir()
        clave = "control" if nombre == "control" else meta["clase"]
        _verificar_capas(caso, DIR_CASOS / caso / "parches" / f"{nombre}.py", clave, sub)
