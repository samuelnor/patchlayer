#!/usr/bin/env python3
"""PreToolUse hook: impide hacer commit o push estando en main.

Nada entra a main sin PR (ver AGENTS.md). Si el agente intenta `git commit`
o `git push` con la rama actual en main, se bloquea y se le pide crear una
rama de carril (nucleo/..., formal/..., corpus/..., entrega/...).
"""
import json
import re
import subprocess
import sys

entrada = json.load(sys.stdin)
comando = entrada.get("tool_input", {}).get("command", "")

# Solo cuentan los segmentos que empiezan con `git` (no el texto de un
# heredoc o de un mensaje que mencione git push main).
segmentos = [s.strip() for s in re.split(r"&&|\|\||[;|\n]", comando)]
git = [s for s in segmentos if re.match(r"(\w+=\S*\s+)*git\s", s)]
if not any(re.search(r"\b(commit|push)\b", s) for s in git):
    sys.exit(0)

try:
    rama = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, cwd=entrada.get("cwd") or None,
    ).stdout.strip()
except OSError:
    sys.exit(0)

empuja_a_main = any(
    re.search(r"\bpush\b.*\s(\S+:)?main\b", s) for s in git
)
if rama == "main" or empuja_a_main:
    print(
        "Bloqueado: no se hace commit ni push en main. Crea primero una rama "
        "de carril con `git switch -c <carril>/<tema>` (nucleo/, formal/, "
        "corpus/ o entrega/) y abre un PR. Ver AGENTS.md, 'Pull requests'.",
        file=sys.stderr,
    )
    sys.exit(2)
