"""Verificador de apoyo para la revisión cruzada de etiquetas.

NO es la compuerta del experimento ni sustituye al contrato de cada caso: es un
oráculo acotado que comprueba, para cada parche entregado:

- propiedad de seguridad (dominio entero acotado),
- bordes legítimos (funcional),
- exploit conocido.

Con eso propone `correcto` / `superficial` / `regresivo` y lo compara con la
etiqueta declarada en `etiquetas/<caso>.json`. Sirve para que el revisor
independiente confirme o dispute las etiquetas sin depender de la compuerta que
se está midiendo.

Uso:  uv run python evidencia/llm/verificar_etiquetas.py
Salida: una línea por parche y código 1 si alguna etiqueta no coincide.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
USUARIO, ADMIN = 1, 2

CLASES = {
    "correcto": "CORRECT",
    "superficial": "INSECURE",
    "regresivo": "REGRESSIVE",
}


def cargar(path: Path, nombre: str):
    loader = importlib.machinery.SourceFileLoader(nombre, str(path))
    spec = importlib.util.spec_from_loader(nombre, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def seguro(fn, *args):
    try:
        return fn(*args), None
    except Exception as exc:  # noqa: BLE001
        return None, exc


def _lanza(fn, *args, exc=PermissionError):
    try:
        fn(*args)
    except exc:
        return True
    except Exception:  # noqa: BLE001
        return False
    return False


def _niega(fn, *args):
    """Acepta False o una excepción de rechazo como denegación."""
    try:
        return fn(*args) is False
    except (ValueError, PermissionError):
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------- propiedad de seguridad ----------

def prop_precio(mod):
    for precio in range(0, 13):
        for desc in range(-5, 121):
            v, e = seguro(mod.precio_final, precio, desc)
            if e is not None:
                if isinstance(e, ValueError):
                    continue
                return False, f"excepción no declarada {type(e).__name__} en ({precio},{desc})"
            if not (0 <= v <= precio):
                return False, f"precio_final({precio}, {desc}) = {v}"
    return True, "sin contraejemplo en el dominio acotado"


def prop_transferir(mod):
    for origen in range(0, 9):
        for destino in range(0, 9):
            for monto in range(-5, 11):
                v, e = seguro(mod.transferir, origen, destino, monto)
                if e is not None:
                    if isinstance(e, ValueError):
                        continue
                    return False, f"excepción no declarada {type(e).__name__} en ({origen},{destino},{monto})"
                try:
                    a, b = v
                except Exception:  # noqa: BLE001
                    return False, f"no devuelve par en ({origen},{destino},{monto}): {v!r}"
                if a + b != origen + destino or not (0 <= a <= origen):
                    return False, f"transferir({origen}, {destino}, {monto}) = {(a, b)}"
                if monto < 0:
                    return False, f"acepta monto negativo ({origen}, {destino}, {monto}) = {(a, b)}"
    return True, "sin contraejemplo en el dominio acotado"


def prop_factura(mod):
    for fid in range(0, 3):
        for owner in range(0, 3):
            for total in range(0, 6):
                for actor in range(-1, 3):
                    v, e = seguro(mod.ver_factura, mod.Factura(fid, owner, total), actor)
                    if e is not None:
                        if isinstance(e, (PermissionError, ValueError)):
                            continue
                        return False, f"excepción no declarada {type(e).__name__} en ({fid},{owner},{total},{actor})"
                    if owner != actor:
                        return False, f"ver_factura(Factura({fid},{owner},{total}), {actor}) = {v}"
    return True, "sin contraejemplo en el dominio acotado"


def prop_cancelar(mod):
    for o0 in range(0, 3):
        for o1 in range(0, 3):
            for o2 in range(0, 3):
                duenos = {0: o0, 1: o1, 2: o2}
                for actor in range(0, 3):
                    for pedido in range(0, 3):
                        for declared in range(0, 3):
                            v, e = seguro(mod.cancelar_pedido, duenos, actor, pedido, declared)
                            if e is not None:
                                if isinstance(e, (ValueError, PermissionError)):
                                    continue
                                return False, f"excepción en {duenos},{actor},{pedido},{declared}: {e}"
                            if v and duenos[pedido] != actor:
                                return False, f"cancelar_pedido({duenos}, {actor}, {pedido}, {declared}) = True"
    return True, "sin contraejemplo en el dominio acotado"


def prop_leer(mod):
    for org in range(0, 2):
        for owner in range(0, 3):
            for privado in (False, True):
                for aid in range(0, 3):
                    for aorg in range(0, 3):
                        for rol in (USUARIO, ADMIN, 0):
                            v, e = seguro(mod.puede_leer, mod.Documento(org, owner, privado), mod.Actor(aid, aorg, rol))
                            if e is not None:
                                if isinstance(e, (ValueError, PermissionError)):
                                    continue
                                return False, f"excepción en ({org},{owner},{privado}),({aid},{aorg},{rol}): {e}"
                            if v:
                                ok = org == aorg and (not privado or owner == aid or rol == ADMIN)
                                if not ok:
                                    return False, f"puede_leer(Documento({org},{owner},{privado}), Actor({aid},{aorg},{rol})) = True"
    return True, "sin contraejemplo en el dominio acotado"


PROPS = {
    "precio_final": prop_precio,
    "transferir": prop_transferir,
    "ver_factura": prop_factura,
    "cancelar_pedido": prop_cancelar,
    "puede_leer": prop_leer,
}


# ---------- bordes legítimos y exploit conocido ----------

def funcional(caso, mod):
    if caso == "precio_final":
        f = mod.precio_final
        checks = [
            ("(1000, 0) == 1000", lambda: f(1000, 0) == 1000),
            ("(1000, 100) == 0", lambda: f(1000, 100) == 0),
            ("(1000, 25) == 750", lambda: f(1000, 25) == 750),
            ("(0, 50) == 0", lambda: f(0, 50) == 0),
        ]
    elif caso == "transferir":
        f = mod.transferir
        checks = [
            ("transferir todo (100, 0, 100)", lambda: f(100, 0, 100) == (0, 100)),
            ("parcial (100, 0, 40)", lambda: f(100, 0, 40) == (60, 40)),
            ("rechaza monto negativo", lambda: _lanza(f, 100, 0, -50, exc=ValueError)),
        ]
    elif caso == "ver_factura":
        f, F = mod.ver_factura, mod.Factura
        checks = [
            ("el dueño lee su factura", lambda: f(F(1, 7, 999), 7) == 999),
            ("un ajeno no lee", lambda: _lanza(f, F(1, 7, 999), 8, exc=PermissionError)),
            ("actor no autenticado", lambda: _lanza(f, F(1, 7, 999), 0, exc=PermissionError)),
        ]
    elif caso == "cancelar_pedido":
        f = mod.cancelar_pedido
        checks = [
            ("el dueño cancela", lambda: f({7: 1}, 1, 7, 1) is True),
            ("pedido inexistente devuelve False", lambda: f({7: 1}, 1, 999, 1) is False),
            ("un ajeno no cancela", lambda: _niega(f, {7: 1}, 2, 7, 2)),
            ("un ajeno no cancela aunque declare otro dueño", lambda: _niega(f, {7: 1}, 2, 7, 1)),
        ]
    elif caso == "puede_leer":
        f, D, A = mod.puede_leer, mod.Documento, mod.Actor
        checks = [
            ("público de la misma org", lambda: f(D(1, 9, False), A(5, 1, USUARIO)) is True),
            ("privado propio", lambda: f(D(1, 5, True), A(5, 1, USUARIO)) is True),
            ("privado de la misma org por admin", lambda: f(D(1, 9, True), A(6, 1, ADMIN)) is True),
            ("rol desconocido devuelve False", lambda: f(D(1, 9, False), A(5, 1, 0)) is False),
            ("otra org bloqueada", lambda: _niega(f, D(1, 9, False), A(5, 2, USUARIO))),
        ]
    else:
        return []
    out = []
    for nombre, chk in checks:
        try:
            out.append((nombre, bool(chk()), ""))
        except Exception as exc:  # noqa: BLE001
            out.append((nombre, False, f"{type(exc).__name__}: {exc}"))
    return out


def exploit(caso, mod):
    if caso == "precio_final":
        v, e = seguro(mod.precio_final, 1000, 150)
        return e is not None, f"precio_final(1000, 150) -> {v!r} / {type(e).__name__ if e else 'sin excepción'}"
    if caso == "transferir":
        v, e = seguro(mod.transferir, 100, 0, -500)
        return e is not None, f"transferir(100, 0, -500) -> {v!r} / {type(e).__name__ if e else 'sin excepción'}"
    if caso == "ver_factura":
        v, e = seguro(mod.ver_factura, mod.Factura(1, 1, 999), 2)
        return e is not None, f"ver_factura(Factura(1,1,999), 2) -> {v!r} / {type(e).__name__ if e else 'sin excepción'}"
    if caso == "cancelar_pedido":
        v, e = seguro(mod.cancelar_pedido, {7: 1}, 2, 7, 2)
        return v is False or e is not None, f"cancelar_pedido({{7:1}}, 2, 7, 2) -> {v!r}"
    if caso == "puede_leer":
        v, e = seguro(mod.puede_leer, mod.Documento(1, 1, False), mod.Actor(9, 2, USUARIO))
        return (v is False) or e is not None, f"puede_leer(Documento(1,1,False), Actor(9,2,USUARIO)) -> {v!r}"
    return False, "caso desconocido"


def evaluar(caso: str, path: Path) -> dict:
    try:
        mod = cargar(path, f"patch_{caso}_{path.stem}")
    except Exception as exc:  # noqa: BLE001
        return {"carga": False, "error": f"{type(exc).__name__}: {exc}", "clase_sugerida": "invalido"}
    prop_ok, prop_detalle = PROPS[caso](mod)
    func = funcional(caso, mod)
    func_ok = all(ok for _, ok, _ in func)
    expl_ok, expl_detalle = exploit(caso, mod)
    if not prop_ok:
        clase = "inseguro"
    elif not func_ok or not expl_ok:
        clase = "regresivo"
    else:
        clase = "correcto"
    return {
        "carga": True,
        "propiedad": {"pasa": prop_ok, "detalle": prop_detalle},
        "funcional": [{"prueba": n, "pasa": ok, "detalle": d} for n, ok, d in func],
        "funcional_pasa": func_ok,
        "exploit_bloqueado": expl_ok,
        "exploit_detalle": expl_detalle,
        "clase_sugerida": clase,
    }


def main() -> int:
    fallos = 0
    for caso in sorted(PROPS):
        etiquetas = json.loads((BASE / "etiquetas" / f"{caso}.json").read_text(encoding="utf-8"))
        print(f"\n== {caso} ==")
        for parche in sorted(etiquetas):
            path = BASE / "parches" / caso / f"{parche}.py"
            r = evaluar(caso, path)
            declarada = etiquetas[parche]["clase"]
            if not r["carga"]:
                print(f"  {parche:34} INVALIDO  {r['error'][:70]}")
                fallos += 1
                continue
            # El oráculo habla en la taxonomía de #5 (INSECURE); el archivo de
            # etiquetas usa el vocabulario de #6 (superficial).
            sugerida = {"inseguro": "superficial"}.get(r["clase_sugerida"], r["clase_sugerida"])
            coincide = sugerida == declarada
            marca = "ok " if coincide else "DISPUTA"
            if not coincide:
                fallos += 1
            print(
                f"  {marca} {parche:32} declarada={declarada:10} "
                f"sugerida={sugerida:10} "
                f"prop={r['propiedad']['pasa']} func={r['funcional_pasa']} "
                f"expl={r['exploit_bloqueado']}"
            )
            if not r["propiedad"]["pasa"]:
                print(f"        {r['propiedad']['detalle']}")
            for f in r["funcional"]:
                if not f["pasa"]:
                    print(f"        falla funcional: {f['prueba']} {f['detalle']}")
    print(f"\n{fallos} discrepancias")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
