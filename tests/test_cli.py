import subprocess


def test_la_cli_expone_revisar_y_experimento():
    salida = subprocess.run(
        ["patchwise", "--help"], capture_output=True, text=True, check=True
    ).stdout
    assert "revisar" in salida
    assert "experimento" in salida
