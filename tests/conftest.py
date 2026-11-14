import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

CASOS = Path(__file__).resolve().parents[1] / "casos"

Armar = Callable[[str, str], Path]


@pytest.fixture
def armar(tmp_path: Path) -> Armar:
    """Arma el directorio como la compuerta (#6): contrato/ + parche como objetivo.py."""

    def _armar(caso: str, parche: str) -> Path:
        shutil.copytree(CASOS / caso / "contrato", tmp_path / "contrato")
        (tmp_path / "objetivo.py").write_text(parche)
        return tmp_path

    return _armar
