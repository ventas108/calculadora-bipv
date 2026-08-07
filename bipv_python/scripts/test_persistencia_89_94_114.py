# -*- coding: utf-8 -*-
"""Pruebas de persistencia POR USUARIO — tareas #89, #94 y #114."""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos import persistencia_resultados as pr
from calculos import presupuesto_store as pstore

# Aislar todo en un directorio temporal
_TMPDIR = tempfile.mkdtemp()
pr.DIR_PERSISTENCIA = _TMPDIR

USR_A = "cliente_a@ejemplo.com"
USR_B = "cliente_b@ejemplo.com"

FALLOS = 0


def check(nombre, cond, detalle=""):
    global FALLOS
    if cond:
        print(f"✅ {nombre}")
    else:
        FALLOS += 1
        print(f"❌ {nombre} {detalle}")


# ── #89: resultados de Producción ────────────────────────────────────────────
ss = {"E_ac_anual_kWh": 12345.6, "P_stc_kW_sistema": 8.1, "N_paneles_final": 15,
      "PR_sistema": 0.82, "produccion_ok": True,
      "ciudad": "Bogotá", "lat_proyecto": 4.6097, "lon_proyecto": -74.0817}
check("#89 guardar resultados", pr.guardar_resultados_produccion(ss, USR_A))
check("#89 sin usuario → no guarda", not pr.guardar_resultados_produccion(ss, ""))

# Pestaña nueva del MISMO usuario → restaurar
ss2 = {}
check("#89 restaurar en pestaña nueva", pr.restaurar_resultados_produccion(ss2, USR_A))
check("#89 valores restaurados", ss2.get("E_ac_anual_kWh") == 12345.6
      and ss2.get("N_paneles_final") == 15)
check("#89 NO marca produccion_ok", not ss2.get("produccion_ok"))

# OTRO usuario del mismo servidor → NUNCA ve los datos del primero
check("#89 aislamiento entre usuarios",
      not pr.restaurar_resultados_produccion({}, USR_B))

# Sesión con otra ciudad → huella no coincide → no restaurar datos obsoletos
ss_otra = {"ciudad": "Medellín"}
check("#89 no restaura con otra ciudad",
      not pr.restaurar_resultados_produccion(ss_otra, USR_A)
      and "E_ac_anual_kWh" not in ss_otra)
ss_coord = {"ciudad": "Bogotá", "lat_proyecto": 4.9, "lon_proyecto": -74.0817}
check("#89 no restaura con otras coordenadas",
      not pr.restaurar_resultados_produccion(ss_coord, USR_A))

# Sesión con producción viva → no tocar
ss3 = {"produccion_ok": True, "E_ac_anual_kWh": 999.0}
check("#89 no pisa sesión viva", not pr.restaurar_resultados_produccion(ss3, USR_A)
      and ss3["E_ac_anual_kWh"] == 999.0)

# Sesión con valores propios (sin produccion_ok) → setdefault, no pisar
ss4 = {"E_ac_anual_kWh": 777.0, "ciudad": "Bogotá"}
pr.restaurar_resultados_produccion(ss4, USR_A)
check("#89 no pisa valor existente", ss4["E_ac_anual_kWh"] == 777.0)

# Cambio de ciudad/proyecto → limpiar
pr.limpiar_resultados_produccion(USR_A)
check("#89 limpiar borra lo guardado", not pr.restaurar_resultados_produccion({}, USR_A))

# ── #94: consumo_cache por usuario incluye el modo de entrada ────────────────
_cache = {"consumo_kwh_mes": 565.0, "factura_cop": 573755.0, "cobertura_pct": 80,
          "modo_calculo": "consumo", "tarifa_cop_kwh": 1015.5,
          "entrada_consumo": "Factura COP"}
_p94 = pr.ruta_datos_usuario("consumo_cache.json", USR_A)
os.makedirs(os.path.dirname(_p94), exist_ok=True)
with open(_p94, "w", encoding="utf-8") as f:
    json.dump(_cache, f)
_ss94 = {}
for k, v in json.load(open(_p94, encoding="utf-8")).items():
    _ss94.setdefault(k, v)
check("#94 roundtrip consumo", _ss94["factura_cop"] == 573755.0
      and _ss94["entrada_consumo"] == "Factura COP")
check("#94 archivo de A no es el de B",
      _p94 != pr.ruta_datos_usuario("consumo_cache.json", USR_B))
# saneo de valor inválido (mismo if de la página)
_ss94["entrada_consumo"] = "OTRA COSA"
if _ss94.get("entrada_consumo") not in ("Factura COP", "Consumo kWh/mes"):
    _ss94.pop("entrada_consumo", None)
check("#94 sanea radio inválido", "entrada_consumo" not in _ss94)

# ── #114: tablas del Presupuesto ─────────────────────────────────────────────
filas = [{"Activo": True, "Descripcion": "Perfil L 40x40", "Ref": "AL-40",
          "Cantidad": 12.0, "Unidad": "un", "USD_un": 8.5, "Total USD": 102.0}]
check("#114 guardar sección",
      pstore.guardar_seccion("perfileria", filas, USR_A, "Cotización ACME jul/2026"))
f2, fu2 = pstore.cargar_seccion("perfileria", USR_A)
check("#114 roundtrip filas", f2 is not None and f2[0]["Descripcion"] == "Perfil L 40x40"
      and fu2 == "Cotización ACME jul/2026")
check("#114 aislamiento entre usuarios",
      pstore.cargar_seccion("perfileria", USR_B) == (None, ""))
check("#114 sección no persistible rechazada",
      not pstore.guardar_seccion("catalogo", filas, USR_A)
      and pstore.cargar_seccion("catalogo", USR_A) == (None, ""))

# Esquema viejo/incompleto → se descarta (plantilla), no KeyError
pstore.guardar_seccion("mano_obra", [{"Descripcion": "solo esto"}], USR_A)
check("#114 esquema incompleto → plantilla",
      pstore.cargar_seccion("mano_obra", USR_A) == (None, ""))
# Fila sin columnas opcionales → se completan defaults
pstore.guardar_seccion("sistema_fv",
                       [{"Descripcion": "Módulo", "Cantidad": 10, "USD_un": 95.0}], USR_A)
f3, _ = pstore.cargar_seccion("sistema_fv", USR_A)
check("#114 completa columnas opcionales",
      f3 and f3[0]["Activo"] is True and f3[0]["Ref"] == "" and f3[0]["Unidad"] == "")

pstore.borrar_seccion("perfileria", USR_A)
check("#114 resetear borra lo guardado",
      pstore.cargar_seccion("perfileria", USR_A) == (None, ""))
# archivo corrupto → no crash, defaults
with open(pr.ruta_datos_usuario("presupuesto_guardado.json", USR_A), "w") as f:
    f.write("{corrupto")
check("#114 tolera archivo corrupto",
      pstore.cargar_seccion("sistema_fv", USR_A) == (None, ""))

shutil.rmtree(_TMPDIR, ignore_errors=True)
print(f"\n{'✅ TODOS LOS TESTS PASARON' if FALLOS == 0 else f'❌ {FALLOS} FALLOS'}")
sys.exit(1 if FALLOS else 0)
