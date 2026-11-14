"""Valida estructura, etiquetas y comportamiento de las 3 capas para los casos núcleo."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CASOS = Path(__file__).resolve().parents[1] / "casos"
CASOS_NUEVOS = ["transferir", "ver_factura", "cancelar_pedido", "puede_leer"]


def _ejecutar_en_directorio(
    caso: str, parche: Path, cmd: list[str], tmp_path: Path
) -> subprocess.CompletedProcess[str]:
    """Arma el directorio como la compuerta (#6) y ejecuta un comando de capa."""
    shutil.copytree(CASOS / caso / "contrato", tmp_path / "contrato", dirs_exist_ok=True)
    shutil.copy(parche, tmp_path / "objetivo.py")
    return subprocess.run(
        cmd,
        cwd=tmp_path,
        env={"PYTHONPATH": str(tmp_path), "PATH": ""},
        capture_output=True,
        text=True,
        timeout=30,
    )


def _correr_pytest(caso: str, parche: Path, prueba: str, tmp_path: Path) -> int:
    return _ejecutar_en_directorio(
        caso,
        parche,
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"contrato/{prueba}"],
        tmp_path,
    ).returncode


def _correr_crosshair(caso: str, parche: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return _ejecutar_en_directorio(
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


def _leer_etiquetas(caso: str) -> dict[str, dict[str, str]]:
    return json.loads((CASOS / caso / "parches" / "etiquetas.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("caso", CASOS_NUEVOS)
def test_estructura_de_caso_y_etiquetas(caso):
    meta_caso = json.loads((CASOS / caso / "caso.json").read_text(encoding="utf-8"))
    assert set(meta_caso) == {"id", "cwe", "vulnerabilidad", "propiedad", "limites"}
    assert meta_caso["id"] == caso
    assert isinstance(meta_caso["limites"], list) and len(meta_caso["limites"]) > 0
    assert (CASOS / caso / "objetivo.py").is_file()

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
        assert (CASOS / caso / "parches" / f"{nombre}.py").is_file()


@pytest.mark.parametrize("caso", CASOS_NUEVOS)
def test_control_pasa_funcional_pero_cae_en_exploit_y_verificador(caso, tmp_path):
    parche = CASOS / caso / "parches" / "control.py"
    assert _correr_pytest(caso, parche, "test_funcional.py", tmp_path) == 0
    assert _correr_pytest(caso, parche, "exploit.py", tmp_path) == 1
    res = _correr_crosshair(caso, parche, tmp_path)
    assert res.returncode == 1
    assert "error:" in res.stdout


@pytest.mark.parametrize("caso", CASOS_NUEVOS)
def test_candidatos_se_comportan_segun_su_etiqueta(caso, tmp_path):
    etiquetas = _leer_etiquetas(caso)
    for nombre, meta in etiquetas.items():
        if nombre == "control":
            continue
        sub = tmp_path / nombre
        sub.mkdir()
        parche = CASOS / caso / "parches" / f"{nombre}.py"
        clase = meta["clase"]
        if clase == "correcto":
            assert _correr_pytest(caso, parche, "test_funcional.py", sub) == 0, nombre
            assert _correr_pytest(caso, parche, "exploit.py", sub) == 0, nombre
            res = _correr_crosshair(caso, parche, sub)
            assert res.returncode == 0, f"{nombre}: {res.stdout}{res.stderr}"
        elif clase == "superficial":
            assert _correr_pytest(caso, parche, "test_funcional.py", sub) == 0, nombre
            assert _correr_pytest(caso, parche, "exploit.py", sub) == 0, nombre
            res = _correr_crosshair(caso, parche, sub)
            assert res.returncode == 1, f"{nombre} debería fallar verificador"
            assert "error:" in res.stdout
        elif clase == "regresivo":
            assert _correr_pytest(caso, parche, "test_funcional.py", sub) == 1, nombre
            assert _correr_pytest(caso, parche, "exploit.py", sub) == 0, nombre
            res = _correr_crosshair(caso, parche, sub)
            assert res.returncode == 0, f"{nombre}: {res.stdout}{res.stderr}"
