"""CLI `patchlayer` (#6, sección 7)."""

import argparse
from pathlib import Path

from patchlayer.compuerta import escribir_expediente, revisar
from patchlayer.experimento import experimento, tabla_markdown
from patchlayer.mutacion import correr_mutmut, mutacion, reporte_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="patchlayer", description=__doc__)
    sub = parser.add_subparsers(dest="subcomando", required=True)

    p_revisar = sub.add_parser(
        "revisar", help="corre la cadena sobre un parche y escribe su expediente"
    )
    p_revisar.add_argument("caso", help="nombre del caso en casos/")
    p_revisar.add_argument("parche", help="nombre del parche en casos/<caso>/parches/")

    p_experimento = sub.add_parser(
        "experimento", help="corre todos los pares (caso, parche) y escribe sus resultados"
    )
    p_experimento.add_argument(
        "--salida",
        type=Path,
        default=Path("resultados"),
        help="carpeta de resultados (por defecto resultados/, ignorada por git); "
        "la corrida oficial va a evidencia/experimento/",
    )

    p_mutacion = sub.add_parser(
        "mutacion", help="corre los mutantes de mutantes/ y escribe el reporte de mutación"
    )
    p_mutacion.add_argument(
        "--sin-sintacticos", action="store_true", help="no corre mutmut (primer recorte)"
    )

    args = parser.parse_args(argv)

    if args.subcomando == "revisar":
        caso_dir = Path("casos") / args.caso
        if not (caso_dir / "parches" / f"{args.parche}.py").is_file():
            parser.error(f"no existe el parche {caso_dir}/parches/{args.parche}.py")
        expediente = revisar(caso_dir, args.parche)
        ruta = escribir_expediente(expediente, Path("expedientes"))
        print(f"expediente: {ruta}")
        veredicto_c = expediente["veredictos"]["C"]
        print(f"C: {veredicto_c}")
        return 0 if veredicto_c == "evidencia_favorable" else 1

    if args.subcomando == "mutacion":
        resultado_mutacion = mutacion(
            Path("casos"),
            Path("mutantes"),
            resultados_dir=Path("resultados"),
            expedientes_dir=Path("expedientes"),
            sintacticos=None if args.sin_sintacticos else correr_mutmut,
        )
        print(reporte_markdown(resultado_mutacion), end="")
        print("resultados: resultados/mutacion.json, resultados/mutacion.md")
        return 0

    salida: Path = args.salida
    resultado = experimento(
        Path("casos"), expedientes_dir=Path("expedientes"), resultados_dir=salida
    )
    print(tabla_markdown(resultado["tabla"]))
    print(metricas_markdown(resultado["metricas"]), end="")
    archivos = ("experimento.json", "reporte.html", "tabla.md")
    print("resultados: " + ", ".join(str(salida / a) for a in archivos))
    return 0
