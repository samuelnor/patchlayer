"""La capa verificador lee los tres resultados de CrossHair y falla cerrada."""

import shutil
from pathlib import Path

from patchwise.formal import verificar

CASOS = Path(__file__).resolve().parents[1] / "casos"

PRECIO_FINAL_CORRECTO = """\
def precio_final(precio, descuento_pct):
    if descuento_pct < 0 or descuento_pct > 100:
        raise ValueError("descuento fuera de rango")
    return precio - (precio * descuento_pct) // 100
"""


def armar(tmp_path: Path, caso: str, parche: str) -> Path:
    """Arma el directorio como la compuerta (#6): contrato/ + parche como objetivo.py."""
    shutil.copytree(CASOS / caso / "contrato", tmp_path / "contrato")
    (tmp_path / "objetivo.py").write_text(parche)
    return tmp_path


def test_el_parche_de_control_falla_con_contraejemplo(tmp_path):
    control = (CASOS / "precio_final" / "parches" / "control.py").read_text()

    capa = verificar(armar(tmp_path, "precio_final", control), timeout_s=30)

    assert capa.resultado == "falla"
    assert capa.contraejemplo == "precio_entre_cero_y_original(1, -1)"
    assert capa.pendiente is None


def test_un_parche_que_valida_el_rango_pasa(tmp_path):
    capa = verificar(armar(tmp_path, "precio_final", PRECIO_FINAL_CORRECTO), timeout_s=30)

    assert capa.resultado == "pasa"
    assert capa.contraejemplo is None
    assert capa.pendiente is None


def test_un_parche_superficial_falla_con_contraejemplo_distinto_del_exploit(tmp_path):
    superficial = PRECIO_FINAL_CORRECTO.replace("descuento_pct < 0 or ", "")

    capa = verificar(armar(tmp_path, "precio_final", superficial), timeout_s=30)

    assert capa.resultado == "falla"
    assert capa.contraejemplo == "precio_entre_cero_y_original(1, -1)"


def test_una_excepcion_no_prevista_por_el_contrato_es_falla(tmp_path):
    parche = "def precio_final(precio, descuento_pct):\n    raise TypeError('x')\n"

    capa = verificar(armar(tmp_path, "precio_final", parche), timeout_s=30)

    assert capa.resultado == "falla"
    assert capa.contraejemplo == "precio_entre_cero_y_original(0, 0)"


def test_un_parche_que_no_carga_es_no_concluyente(tmp_path):
    capa = verificar(armar(tmp_path, "precio_final", "def (\n"), timeout_s=30)

    assert capa.resultado == "no_concluyente"
    assert capa.pendiente == "el parche no carga; revisar la funcional"
    assert "SyntaxError" in capa.salida


def test_un_parche_que_no_termina_agota_el_tiempo_de_pared(tmp_path):
    parche = "def precio_final(precio, descuento_pct):\n    while True:\n        pass\n"

    capa = verificar(armar(tmp_path, "precio_final", parche), timeout_s=3)

    assert capa.resultado == "no_concluyente"
    assert capa.pendiente == "repetir con un tiempo límite mayor o acotar dominios"
    assert capa.duracion_s < 6


def test_un_parche_que_corta_el_verificador_sin_resultado_no_pasa(tmp_path):
    parche = "import os\nos._exit(0)\n"

    capa = verificar(armar(tmp_path, "precio_final", parche), timeout_s=30)

    assert capa.resultado == "no_concluyente"
    assert capa.pendiente is not None


def test_una_propiedad_que_crosshair_no_cierra_es_no_concluyente(tmp_path):
    (tmp_path / "contrato").mkdir()
    (tmp_path / "objetivo.py").write_text(
        "import hashlib\n\n"
        "def resumen(dato: bytes) -> str:\n"
        "    return hashlib.sha256(dato).hexdigest()\n"
    )
    (tmp_path / "contrato" / "propiedad.py").write_text(
        "from objetivo import resumen\n\n"
        "def nunca_es_cero(dato: bytes) -> bool:\n"
        '    """\n    post: __return__\n    """\n'
        '    return resumen(dato) != "0" * 64\n'
    )

    capa = verificar(tmp_path, timeout_s=6)

    assert capa.resultado == "no_concluyente"
    assert capa.pendiente == "revisar a mano o añadir prueba Hypothesis"
    assert "Not confirmed." in capa.salida


def test_la_capa_registra_su_procedencia(tmp_path):
    capa = verificar(armar(tmp_path, "precio_final", PRECIO_FINAL_CORRECTO), timeout_s=30)

    assert capa.herramienta == "crosshair"
    assert capa.version
    assert "crosshair check --report_all" in capa.comando
    assert "Confirmed over all paths." in capa.salida
    assert capa.duracion_s > 0
