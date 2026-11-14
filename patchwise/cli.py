"""CLI `patchwise` (#6, sección 7)."""

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="patchwise", description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)

    revisar = sub.add_parser(
        "revisar", help="corre la cadena sobre un parche y escribe su expediente"
    )
    revisar.add_argument("caso", help="nombre del caso en casos/")
    revisar.add_argument("parche", help="nombre del parche en casos/<caso>/parches/")

    sub.add_parser(
        "experimento", help="corre todos los pares (caso, parche) y escribe resultados/"
    )

    args = parser.parse_args(argv)
    parser.exit(1, f"patchwise {args.comando}: aún no implementado\n")
