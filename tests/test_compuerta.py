"""`revisar` corre la cadena sobre un parche y arma su expediente (#6, secciones 2 a 5)."""

import hashlib
import shutil
from pathlib import Path

from patchwise.capas import ResultadoCapa
from patchwise.compuerta import Verificar, revisar

CASO = Path(__file__).resolve().parents[1] / "casos" / "precio_final"


def verificador_que_encuentra(contraejemplo: str | None) -> Verificar:
    def verificar(directorio: Path, timeout_s: float) -> ResultadoCapa:
        assert (directorio / "objetivo.py").exists()
        assert (directorio / "contrato" / "propiedad.py").exists()
        return ResultadoCapa(
            resultado="falla",
            herramienta="crosshair",
            version="stub",
            comando="crosshair check contrato/propiedad.py",
            duracion_s=0.0,
            salida="",
            detalle="contraejemplo encontrado",
            contraejemplo=contraejemplo,
        )

    return verificar


def verificador_que_lanza(directorio: Path, timeout_s: float) -> ResultadoCapa:
    raise NotImplementedError("pendiente: carril Capa formal")


def test_el_parche_de_control_queda_rechazado_por_b_y_c() -> None:
    exp = revisar(CASO, "control", verificar=verificador_que_encuentra("precio_final(1, 101)"))

    assert {k: v["resultado"] for k, v in exp["capas"].items()} == {
        "funcional": "pasa",
        "exploit": "falla",
        "verificador": "falla",
    }
    assert exp["veredictos"] == {
        "A": "evidencia_favorable",
        "B": "rechazado",
        "C": "rechazado",
    }
    assert exp["capas"]["verificador"]["contraejemplo"] == "precio_final(1, 101)"


def test_el_expediente_registra_caso_parche_y_procedencia_sin_la_etiqueta() -> None:
    exp = revisar(CASO, "control", verificar=verificador_que_encuentra("x"))

    assert exp["caso"] == {
        "id": "precio_final",
        "cwe": "CWE-20",
        "vulnerabilidad": exp["caso"]["vulnerabilidad"],
        "propiedad": exp["caso"]["propiedad"],
    }
    assert exp["parche"] == {
        "id": "control",
        "sha256": hashlib.sha256((CASO / "parches" / "control.py").read_bytes()).hexdigest(),
        "origen": "control",
    }
    assert len(exp["contrato_sha256"]) == 64
    assert "superficial" not in str(exp)
    assert exp["capas"]["funcional"]["herramienta"] == "pytest"
    assert exp["generado_en"].startswith("20")


def test_sin_verificar_trae_los_limites_fijos_y_los_del_caso() -> None:
    exp = revisar(CASO, "control", verificar=verificador_que_encuentra("x"))

    assert "búsqueda simbólica acotada, no prueba" in exp["sin_verificar"]
    assert "Solo cubre enteros (céntimos); no cubre float ni Decimal." in exp["sin_verificar"]


def test_un_verificador_que_lanza_deja_la_capa_no_concluyente_con_pendiente() -> None:
    exp = revisar(CASO, "control", verificar=verificador_que_lanza)

    verificador = exp["capas"]["verificador"]
    assert verificador["resultado"] == "no_concluyente"
    assert verificador["pendiente"] in exp["pendientes"]
    assert any(s.startswith("capa verificador:") for s in exp["sin_verificar"])


def test_un_parche_que_no_carga_falla_la_funcional_y_deja_lo_demas_no_concluyente(
    tmp_path: Path,
) -> None:
    caso = tmp_path / "precio_final"
    shutil.copytree(CASO, caso)
    (caso / "parches" / "roto.py").write_text("def precio_final(:\n")

    llamado: list[Path] = []

    def verificar(directorio: Path, timeout_s: float) -> ResultadoCapa:
        llamado.append(directorio)
        raise AssertionError("el verificador no debe correr si el parche no carga")

    exp = revisar(caso, "roto", verificar=verificar)

    assert {k: v["resultado"] for k, v in exp["capas"].items()} == {
        "funcional": "falla",
        "exploit": "no_concluyente",
        "verificador": "no_concluyente",
    }
    assert llamado == []
    assert "el parche no carga; revisar la funcional" in exp["pendientes"]
    assert exp["parche"]["origen"] is None


def test_una_capa_que_agota_el_tiempo_queda_no_concluyente(tmp_path: Path) -> None:
    caso = tmp_path / "precio_final"
    shutil.copytree(CASO, caso)
    (caso / "parches" / "lento.py").write_text(
        "def precio_final(precio, descuento_pct):\n    while True:\n        pass\n"
    )

    exp = revisar(caso, "lento", verificar=verificador_que_encuentra("x"), timeout_s=2)

    assert exp["capas"]["funcional"]["resultado"] == "no_concluyente"
    assert exp["capas"]["funcional"]["pendiente"]


def test_un_verificador_con_resultado_invalido_queda_no_concluyente_con_pendiente() -> None:
    def verificar(directorio: Path, timeout_s: float) -> ResultadoCapa:
        capa = verificador_que_encuentra(None)(directorio, timeout_s)
        capa.resultado = "ok"  # pyright: ignore[reportAttributeAccessIssue] - inválido a propósito
        return capa

    exp = revisar(CASO, "control", verificar=verificar)

    assert exp["capas"]["verificador"]["resultado"] == "no_concluyente"
    assert exp["capas"]["verificador"]["pendiente"] in exp["pendientes"]


def test_un_verificador_no_concluyente_sin_pendiente_recibe_uno_del_catalogo() -> None:
    def verificar(directorio: Path, timeout_s: float) -> ResultadoCapa:
        capa = verificador_que_encuentra(None)(directorio, timeout_s)
        capa.resultado = "no_concluyente"
        return capa

    exp = revisar(CASO, "control", verificar=verificar)

    assert exp["capas"]["verificador"]["pendiente"]
    assert exp["capas"]["verificador"]["pendiente"] in exp["pendientes"]


def test_el_error_de_importacion_queda_en_la_salida_de_la_funcional(tmp_path: Path) -> None:
    caso = tmp_path / "precio_final"
    shutil.copytree(CASO, caso)
    (caso / "parches" / "roto.py").write_text("def precio_final(:\n")

    exp = revisar(caso, "roto", verificar=verificador_que_lanza)

    assert "SyntaxError" in exp["capas"]["funcional"]["salida"]


def test_un_parche_que_se_cuelga_al_importar_deja_todo_no_concluyente(tmp_path: Path) -> None:
    caso = tmp_path / "precio_final"
    shutil.copytree(CASO, caso)
    (caso / "parches" / "colgado.py").write_text("while True:\n    pass\n")

    exp = revisar(caso, "colgado", verificar=verificador_que_lanza, timeout_s=1)

    assert {v["resultado"] for v in exp["capas"].values()} == {"no_concluyente"}


def test_un_contrato_sin_pruebas_deja_la_capa_no_concluyente(tmp_path: Path) -> None:
    caso = tmp_path / "precio_final"
    shutil.copytree(CASO, caso)
    (caso / "contrato" / "exploit.py").write_text("from objetivo import precio_final\n")

    exp = revisar(caso, "control", verificar=verificador_que_lanza)

    assert exp["capas"]["exploit"]["resultado"] == "no_concluyente"
