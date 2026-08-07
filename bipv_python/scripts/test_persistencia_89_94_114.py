# -*- coding: utf-8 -*-
"""Pruebas de persistencia — tareas #89, #94 y #114 (roundtrip guardar→cargar)."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos import persistencia_resultados as pr
from calculos import presupuesto_store as pstore

FALLOS = 0


def check(nombre, cond, detalle=""):
    global FALLOS
    if cond:
        print(f"✅ {nombre}")
    else:
        FALLOS += 1
        print(f"❌ {nombre} {detalle}")


# ── #89: resultados de Producción ────────────────────────────────────────────
pr.RUTA_PROYECTO_ACTUAL = tempfile.mktemp(suffix=".json")

# proyecto_actual.json ya tiene datos de la página Proyecto → deben conservarse
with open(pr.RUTA_PROYECTO_ACTUAL, "w", encoding="utf-8") as f:
    json.dump({"ciudad": "Bogotá", "area_fachada_m2": 97.34}, f)

ss = {"E_ac_anual_kWh": 12345.6, "P_stc_kW_sistema": 8.1,
      "N_paneles_final": 15, "PR_sistema": 0.82, "produccion_ok": True}
check("#89 guardar resultados", pr.guardar_resultados_produccion(ss))
_data = json.load(open(pr.RUTA_PROYECTO_ACTUAL, encoding="utf-8"))
check("#89 no pisa datos de Proyecto", _data.get("ciudad") == "Bogotá")
check("#89 resultados en el JSON",
      _data["resultados_produccion"]["N_paneles_final"] == 15)

# Pestaña nueva: session_state vacío → restaurar
ss2 = {}
check("#89 restaurar en pestaña nueva", pr.restaurar_resultados_produccion(ss2))
check("#89 valores restaurados", ss2.get("E_ac_anual_kWh") == 12345.6
      and ss2.get("N_paneles_final") == 15)
check("#89 NO marca produccion_ok", not ss2.get("produccion_ok"))

# Sesión con producción viva → no tocar
ss3 = {"produccion_ok": True, "E_ac_anual_kWh": 999.0}
check("#89 no pisa sesión viva", not pr.restaurar_resultados_produccion(ss3)
      and ss3["E_ac_anual_kWh"] == 999.0)

# Sesión con valores propios (sin produccion_ok) → setdefault, no pisar
ss4 = {"E_ac_anual_kWh": 777.0}
pr.restaurar_resultados_produccion(ss4)
check("#89 no pisa valor existente", ss4["E_ac_anual_kWh"] == 777.0)

# Cambio de ciudad → limpiar
pr.limpiar_resultados_produccion()
check("#89 limpiar al cambiar ciudad",
      not pr.restaurar_resultados_produccion({}) and
      json.load(open(pr.RUTA_PROYECTO_ACTUAL, encoding="utf-8")).get("ciudad") == "Bogotá")
os.remove(pr.RUTA_PROYECTO_ACTUAL)

# ── #94: consumo_cache.json incluye el modo de entrada ───────────────────────
# (la página escribe el dict; aquí validamos el roundtrip y el saneo del radio)
_cache = {"consumo_kwh_mes": 565.0, "factura_cop": 573755.0, "cobertura_pct": 80,
          "modo_calculo": "consumo", "tarifa_cop_kwh": 1015.5,
          "entrada_consumo": "Factura COP"}
_p94 = tempfile.mktemp(suffix=".json")
with open(_p94, "w", encoding="utf-8") as f:
    json.dump(_cache, f)
_ss94 = {}
for k, v in json.load(open(_p94, encoding="utf-8")).items():
    _ss94.setdefault(k, v)
check("#94 roundtrip consumo", _ss94["factura_cop"] == 573755.0
      and _ss94["entrada_consumo"] == "Factura COP")
# saneo de valor inválido (mismo if de la página)
_ss94["entrada_consumo"] = "OTRA COSA"
if _ss94.get("entrada_consumo") not in ("Factura COP", "Consumo kWh/mes"):
    _ss94.pop("entrada_consumo", None)
check("#94 sanea radio inválido", "entrada_consumo" not in _ss94)
os.remove(_p94)

# ── #114: tablas del Presupuesto ─────────────────────────────────────────────
pstore.RUTA_PRESUPUESTO = tempfile.mktemp(suffix=".json")
filas = [{"Activo": True, "Descripcion": "Perfil L 40x40", "Ref": "AL-40",
          "Cantidad": 12.0, "Unidad": "un", "USD_un": 8.5, "Total USD": 102.0}]
check("#114 guardar sección", pstore.guardar_seccion("perfileria", filas, "Cotización ACME jul/2026"))
f2, fu2 = pstore.cargar_seccion("perfileria")
check("#114 roundtrip filas", f2 == filas and fu2 == "Cotización ACME jul/2026")
check("#114 sección no persistible rechazada",
      not pstore.guardar_seccion("catalogo", filas) and pstore.cargar_seccion("catalogo") == (None, ""))
pstore.borrar_seccion("perfileria")
check("#114 resetear borra lo guardado", pstore.cargar_seccion("perfileria") == (None, ""))
# archivo corrupto → no crash, defaults
with open(pstore.RUTA_PRESUPUESTO, "w") as f:
    f.write("{corrupto")
check("#114 tolera archivo corrupto", pstore.cargar_seccion("perfileria") == (None, ""))
os.remove(pstore.RUTA_PRESUPUESTO)

print(f"\n{'✅ TODOS LOS TESTS PASARON' if FALLOS == 0 else f'❌ {FALLOS} FALLOS'}")
sys.exit(1 if FALLOS else 0)
