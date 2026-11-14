"""El contrato de precio_final distingue al parche de control y a los 4 candidatos."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CASO = Path(__file__).resolve().parents[1] / "casos" / "precio_final"


def _ejecutar_en_directorio(
    parche: Path, cmd: list[str], tmp_path: Path
) -> subprocess.CompletedProcess[str]:
    """Arma el directorio como la compuerta (#6) y ejecuta un comando de capa."""
    shutil.copytree(CASO / "contrato", tmp_path / "contrato", dirs_exist_ok=True)
    shutil.copy(parche, tmp_path / "objetivo.py")
    return subprocess.run(
        cmd,
        cwd=tmp_path,
        env={"PYTHONPATH": str(tmp_path), "PATH": ""},
        capture_output=True,
        text=True,
        timeout=30,
    )


def correr_contrato(parche: Path, prueba: str, tmp_path: Path) -> int:
    """Corre pytest sobre un archivo de `contrato/` contra el parche armado."""
    return _ejecutar_en_directorio(
        parche,
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"contrato/{prueba}"],
        tmp_path,
    ).returncode


def correr_verificador(parche: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Corre CrossHair sobre `contrato/propiedad.py` contra el parche armado."""
    return _ejecutar_en_directorio(
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


def test_el_exploit_atrapa_al_parche_de_control(tmp_path):
    assert correr_contrato(CASO / "parches" / "control.py", "exploit.py", tmp_path) == 1


def test_el_parche_de_control_pasa_la_funcional(tmp_path):
    assert correr_contrato(CASO / "parches" / "control.py", "test_funcional.py", tmp_path) == 0


def test_el_verificador_rechaza_al_parche_de_control(tmp_path):
    res = correr_verificador(CASO / "parches" / "control.py", tmp_path)
    assert res.returncode == 1
    assert "error:" in res.stdout


def test_el_parche_correcto_pasa_las_tres_capas(tmp_path):
    parche = CASO / "parches" / "correcto.py"
    assert correr_contrato(parche, "test_funcional.py", tmp_path) == 0
    assert correr_contrato(parche, "exploit.py", tmp_path) == 0
    res = correr_verificador(parche, tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.parametrize(
    "nombre_archivo",
    ["superficial_solo_maximo.py", "superficial_precio_no_negativo.py"],
)
def test_parche_superficial_burla_b_y_cae_en_c(nombre_archivo, tmp_path):
    parche = CASO / "parches" / nombre_archivo
    assert correr_contrato(parche, "test_funcional.py", tmp_path) == 0
    assert correr_contrato(parche, "exploit.py", tmp_path) == 0
    res = correr_verificador(parche, tmp_path)
    assert res.returncode == 1
    assert "error:" in res.stdout


def test_parche_regresivo_cae_en_funcional_aunque_pase_exploit_y_verificador(tmp_path):
    parche = CASO / "parches" / "regresivo_bordes.py"
    assert correr_contrato(parche, "test_funcional.py", tmp_path) == 1
    assert correr_contrato(parche, "exploit.py", tmp_path) == 0
    res = correr_verificador(parche, tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr


def test_estructura_de_caso_y_etiquetas():
    caso = json.loads((CASO / "caso.json").read_text(encoding="utf-8"))
    assert set(caso) == {"id", "cwe", "vulnerabilidad", "propiedad", "limites"}
    assert caso["id"] == "precio_final"
    assert isinstance(caso["limites"], list) and len(caso["limites"]) > 0

    etiquetas = json.loads((CASO / "parches" / "etiquetas.json").read_text(encoding="utf-8"))
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
        assert (CASO / "parches" / f"{nombre}.py").is_file()
