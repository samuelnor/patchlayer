"""Comprueba que cada caso respeta el formato de disco del issue #6."""
import json
from pathlib import Path

import pytest

from patchwise.capas import ResultadoCapa
from patchwise.formal import verificar

CASOS = Path(__file__).resolve().parent.parent / "casos"
CLASES = {"correcto", "superficial", "regresivo"}


def casos():
    return sorted(p for p in CASOS.iterdir() if p.is_dir())


@pytest.mark.parametrize("caso", casos(), ids=lambda p: p.name)
def test_caso_respeta_el_formato(caso):
    for archivo in ["objetivo.py", "caso.json", "contrato/propiedad.py",
                    "contrato/exploit.py", "contrato/test_funcional.py",
                    "parches/etiquetas.json"]:
        assert (caso / archivo).is_file(), archivo

    meta = json.loads((caso / "caso.json").read_text())
    assert meta["id"] == caso.name
    assert {"cwe", "vulnerabilidad", "propiedad", "limites"} <= meta.keys()

    etiquetas = json.loads((caso / "parches/etiquetas.json").read_text())
    parches = {p.stem for p in (caso / "parches").glob("*.py")}
    assert parches == etiquetas.keys()
    assert all(e["clase"] in CLASES and e["origen"] for e in etiquetas.values())
    assert (caso / "parches/control.py").read_text() == (caso / "objetivo.py").read_text()
    assert etiquetas["control"]["clase"] == "superficial"


def test_firma_de_la_capa_formal(tmp_path):
    resultado = verificar(tmp_path, timeout_s=1.0)
    assert isinstance(resultado, ResultadoCapa)
    assert resultado.resultado in {"pasa", "falla", "no_concluyente"}
