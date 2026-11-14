"""El contrato de precio_final distingue al parche de control (código vulnerable)."""

import shutil
import subprocess
import sys
from pathlib import Path

CASO = Path(__file__).resolve().parents[1] / "casos" / "precio_final"


def correr_contrato(parche: Path, prueba: str, tmp_path: Path) -> int:
    """Arma el directorio como la compuerta (#6): contrato/ + parche como objetivo.py."""
    shutil.copytree(CASO / "contrato", tmp_path / "contrato")
    shutil.copy(parche, tmp_path / "objetivo.py")
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"contrato/{prueba}"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(tmp_path), "PATH": ""},
        capture_output=True,
    ).returncode


def test_el_exploit_atrapa_al_parche_de_control(tmp_path):
    assert correr_contrato(CASO / "parches" / "control.py", "exploit.py", tmp_path) == 1


def test_el_parche_de_control_pasa_la_funcional(tmp_path):
    assert correr_contrato(CASO / "parches" / "control.py", "test_funcional.py", tmp_path) == 0
