# -*- coding: utf-8 -*-
"""Tareas #124/#127 — al cargar un proyecto, los flags *_ok NO deben revivir.

proyectos_manager importa streamlit (no disponible localmente), así que se
verifica vía AST sobre el código real, igual que test_invalidacion_ciudad.py:
1. "recurso_solar_ok" está en _claves_reset (#127).
2. Dentro de cargar_proyecto hay una limpieza de _claves_reset DESPUÉS del
   bucle que vuelca el estado guardado (si solo se limpia antes, el JSON
   revive los flags y el banner de #124 no avisa).
"""
import ast
import os
import sys

RUTA = os.path.join(os.path.dirname(__file__), "..", "calculos", "proyectos_manager.py")

FALLOS = 0


def check(nombre, cond):
    global FALLOS
    if cond:
        print(f"✅ {nombre}")
    else:
        FALLOS += 1
        print(f"❌ {nombre}")


tree = ast.parse(open(RUTA, encoding="utf-8").read())

fn = next(n for n in ast.walk(tree)
          if isinstance(n, ast.FunctionDef) and n.name == "cargar_proyecto")

# 1) Extraer el set _claves_reset asignado dentro de cargar_proyecto
claves = None
for n in ast.walk(fn):
    if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_claves_reset" for t in n.targets):
        claves = {ast.literal_eval(e) for e in n.value.elts}
check("#127 recurso_solar_ok en _claves_reset",
      claves is not None and "recurso_solar_ok" in claves)
check("#124 flags de simulación en _claves_reset",
      claves is not None and {"produccion_ok", "financiero_ok"} <= claves)

# 2) Ordenar eventos por línea: volcado de `estado` vs bucles de limpieza
linea_volcado = None
lineas_limpieza = []
for n in ast.walk(fn):
    if isinstance(n, ast.For):
        src = ast.dump(n.iter)
        if "estado" in src and "items" in src:
            linea_volcado = n.lineno
        if isinstance(n.iter, ast.Name) and n.iter.id == "_claves_reset":
            lineas_limpieza.append(n.lineno)

check("#127 existe volcado del estado guardado", linea_volcado is not None)
check("#127 hay limpieza de flags DESPUÉS del volcado",
      linea_volcado is not None and any(l > linea_volcado for l in lineas_limpieza))

print(f"\n{'✅ TODOS LOS TESTS PASARON' if FALLOS == 0 else f'❌ {FALLOS} FALLOS'}")
sys.exit(1 if FALLOS else 0)
