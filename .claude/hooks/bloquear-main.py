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

if not re.search(r"\bgit\b[^;&|]*\b(commit|push)\b", comando):
    sys.exit(0)

try:
    rama = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, cwd=entrada.get("cwd") or None,
    ).stdout.strip()
except OSError:
    sys.exit(0)

empuja_a_main = re.search(r"\bgit\b[^;&|]*\bpush\b[^;&|]*\bmain\b", comando)
if rama == "main" or empuja_a_main:
    print(
        "Bloqueado: no se hace commit ni push en main. Crea primero una rama "
        "de carril con `git switch -c <carril>/<tema>` (nucleo/, formal/, "
        "corpus/ o entrega/) y abre un PR. Ver AGENTS.md, 'Pull requests'.",
        file=sys.stderr,
    )
    sys.exit(2)
