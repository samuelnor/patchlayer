import json
import shutil
import subprocess
from pathlib import Path

CASOS = Path(__file__).resolve().parents[1] / "casos"


def test_la_cli_expone_revisar_y_experimento() -> None:
    salida = subprocess.run(
        ["patchwise", "--help"], capture_output=True, text=True, check=True
    ).stdout
    assert "revisar" in salida
    assert "experimento" in salida


def test_revisar_escribe_el_expediente_e_imprime_el_veredicto_c(tmp_path: Path) -> None:
    shutil.copytree(CASOS, tmp_path / "casos")

    proc = subprocess.run(
        ["patchwise", "revisar", "precio_final", "control"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert proc.stdout.strip().splitlines()[-1] == "C: rechazado"
    assert proc.returncode == 1  # falla cerrada: solo evidencia_favorable sale con 0
    ruta = tmp_path / "expedientes" / "precio_final" / "control.json"
    expediente = json.loads(ruta.read_text())
    assert expediente["veredictos"]["C"] == "rechazado"


def test_revisar_un_parche_inexistente_falla_con_mensaje(tmp_path: Path) -> None:
    shutil.copytree(CASOS, tmp_path / "casos")

    proc = subprocess.run(
        ["patchwise", "revisar", "precio_final", "no_existe"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 2
    assert "no_existe" in proc.stderr


def test_experimento_escribe_los_resultados(tmp_path: Path) -> None:
    shutil.copytree(CASOS, tmp_path / "casos")

    proc = subprocess.run(
        ["patchwise", "experimento"], cwd=tmp_path, capture_output=True, text=True
    )

    assert proc.returncode == 0, proc.stderr
    assert "| C |" in proc.stdout
    for archivo in ("experimento.json", "reporte.html", "tabla.md"):
        assert (tmp_path / "resultados" / archivo).exists()
