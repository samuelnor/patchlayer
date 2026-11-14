"""CLI `patchwise` (carril Núcleo)."""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="patchwise")
    sub = parser.add_subparsers(dest="comando", required=True)
    revisar = sub.add_parser("revisar", help="corre la cadena sobre un parche candidato")
    revisar.add_argument("caso")
    revisar.add_argument("parche")
    sub.add_parser("experimento", help="corre todos los pares (caso, parche)")
    parser.parse_args(argv)
    raise SystemExit("sin implementar todavía (issue #9)")
