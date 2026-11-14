"""Valida estructura, etiquetas y comportamiento de las 3 capas para los 4 casos adicionales."""

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

DIR_CASOS = Path(__file__).resolve().parents[1] / "casos"
CASOS_ADICIONALES = ["transferir", "ver_factura", "cancelar_pedido", "puede_leer"]


@dataclass(frozen=True)
class ExpectativaCapas:
    """Códigos de salida esperados para funcional, exploit y verificador formal."""

    funcional: int
    exploit: int
    formal: int


RESULTADOS_ESPERADOS: dict[str, ExpectativaCapas] = {
    "control": ExpectativaCapas(funcional=0, exploit=1, formal=1),
    "correcto": ExpectativaCapas(funcional=0, exploit=0, formal=0),
    "superficial": ExpectativaCapas(funcional=0, exploit=0, formal=1),
    "regresivo": ExpectativaCapas(funcional=1, exploit=0, formal=0),
}

# Documentado en evidencia/llm/REVISION.md: lanza ValueError si el pedido no existe,
# excepción que cancelar_pedido/contrato/propiedad.py rechaza explícitamente.
EXCEPCIONES_POR_PARCHE: dict[tuple[str, str], ExpectativaCapas] = {
    ("cancelar_pedido", "llm_deepseek_v4_1_flash_free"): ExpectativaCapas(
        funcional=1, exploit=0, formal=1
    ),
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
    clave = "control" if parche.stem == "control" else clase
    esperado = EXCEPCIONES_POR_PARCHE.get((caso, parche.stem), RESULTADOS_ESPERADOS[clave])

    rc_funcional = _ejecutar_en_directorio(
        caso,
        parche,
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "contrato/test_funcional.py",
        ],
        tmp_path,
    ).returncode
    assert rc_funcional == esperado.funcional, f"{parche.name}: funcional={rc_funcional}"

    rc_exploit = _ejecutar_en_directorio(
        caso,
        parche,
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "contrato/exploit.py"],
        tmp_path,
    ).returncode
    assert rc_exploit == esperado.exploit, f"{parche.name}: exploit={rc_exploit}"

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
    assert res_formal.returncode == esperado.formal, (
        f"{parche.name}: {res_formal.stdout}{res_formal.stderr}"
    )
    if esperado.formal == 1:
        assert "error:" in res_formal.stdout


def _leer_etiquetas(caso: str) -> dict[str, dict[str, str]]:
    return json.loads((DIR_CASOS / caso / "parches" / "etiquetas.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("caso", CASOS_ADICIONALES)
def test_estructura_de_caso_y_etiquetas(caso: str) -> None:
    meta_caso = json.loads((DIR_CASOS / caso / "caso.json").read_text(encoding="utf-8"))
    assert set(meta_caso) == {"id", "cwe", "vulnerabilidad", "propiedad", "limites"}
    assert meta_caso["id"] == caso
    assert isinstance(meta_caso["limites"], list)
    assert len(meta_caso["limites"]) > 0

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
    assert any(v["origen"].startswith("llm:") for v in candidatos.values())

    for nombre, meta in etiquetas.items():
        assert set(meta) == {"clase", "origen"}
        assert meta["origen"]
        assert (DIR_CASOS / caso / "parches" / f"{nombre}.py").is_file()


@pytest.mark.parametrize("caso", CASOS_ADICIONALES)
def test_control_y_candidatos_se_comportan_segun_su_etiqueta(
    caso: str, tmp_path: Path
) -> None:
    for nombre, meta in _leer_etiquetas(caso).items():
        sub = tmp_path / nombre
        sub.mkdir()
        _verificar_capas(caso, DIR_CASOS / caso / "parches" / f"{nombre}.py", meta["clase"], sub)
