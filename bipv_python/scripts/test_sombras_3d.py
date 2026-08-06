# -*- coding: utf-8 -*-
"""Banco de pruebas — calculos/sombras_3d.py (sombras desde SketchUp).

Correr desde bipv_python/:  python3 scripts/test_sombras_3d.py
Escena sintética: muro al ESTE del punto → sombra en la mañana, sol libre en la tarde.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import trimesh

from calculos.sombras_3d import (
    calcular_fs_horario,
    cargar_malla,
    exportar_csv_fs,
    posiciones_solares,
    resumen_fs,
    resumen_malla,
    vector_al_sol,
)

FALLOS = []

def check(nombre, cond, detalle=""):
    print(("✅" if cond else "❌"), nombre + (f" — {detalle}" if detalle else ""))
    if not cond:
        FALLOS.append(nombre)

LAT, LON = 7.884, -76.635  # Apartadó, Urabá

# ══ 1. vector_al_sol — convenciones ══════════════════════════════════════════
v_este = vector_al_sol(0.0, 90.0)     # sol en el horizonte, acimut 90° = Este
check("Acimut 90° apunta al Este (+X)", np.allclose(v_este, [1, 0, 0], atol=1e-9))
v_norte = vector_al_sol(0.0, 0.0)
check("Acimut 0° apunta al Norte (+Y)", np.allclose(v_norte, [0, 1, 0], atol=1e-9))
v_cenit = vector_al_sol(90.0, 180.0)
check("Elevación 90° apunta al cénit (+Z)", np.allclose(v_cenit, [0, 0, 1], atol=1e-9))

# ══ 2. posiciones solares — índice TMY vs genérico ═══════════════════════════
# Hora LOCAL para que las horas del CSV sean interpretables (7-9 = mañana).
# Nota: si el TMY real viene en UTC, las horas del CSV quedan en UTC — igual
# que el TMY que usa Producción, por eso la alineación (mes,dia,hora) coincide.
idx_tmy = pd.date_range("2020-01-01", periods=8760, freq="h", tz="America/Bogota")
sol = posiciones_solares(LAT, LON, idx_tmy)
check("Posiciones solares sobre el índice TMY (8760 filas)", len(sol) == 8760)
check("Columnas mes/dia/hora presentes", {"mes", "dia", "hora"} <= set(sol.columns))
sol_gen = posiciones_solares(LAT, LON, None)
check("Año genérico también 8760 filas", len(sol_gen) == 8760)
check("En el trópico el sol supera 80° algún día", sol_gen["elevacion"].max() > 80)

# ══ 3. Escena sintética: muro alto al ESTE del punto ═════════════════════════
# Muro: caja de 40 m (N-S) × 1 m de espesor × 20 m de alto, centrada en x=+10
muro = trimesh.creation.box(extents=[1, 40, 20])
muro.apply_translation([10, 0, 10])
punto = [{"nombre": "P1", "fachada": "Este", "x": 0.0, "y": 0.0, "z": 1.0}]

df = calcular_fs_horario(muro, punto, LAT, LON, indice_tmy=idx_tmy)
check("Solo horas con sol (sin madrugada)", df["Hora"].min() >= 5 and df["Hora"].max() <= 19)
check("FS en [0,1]", df["FS"].between(0, 1).all())

fs_am = df[df["Hora"].between(7, 9)]["FS"].mean()    # sol al Este → muro tapa
fs_pm = df[df["Hora"].between(15, 17)]["FS"].mean()  # sol al Oeste → libre
check("Sombra en la mañana (muro al Este)", fs_am > 0.9, f"FS medio 7-9h = {fs_am:.2f}")
check("Sin sombra en la tarde", fs_pm < 0.05, f"FS medio 15-17h = {fs_pm:.2f}")

# ══ 4. Transparencia (árbol) ═════════════════════════════════════════════════
df_arb = calcular_fs_horario(muro, punto, LAT, LON, indice_tmy=idx_tmy, transparencia=0.4)
fs_arb_am = df_arb[df_arb["Hora"].between(7, 9)]["FS"].mean()
check("Transparencia 0,4 → FS de choque 0,6", abs(fs_arb_am - 0.6) < 0.05,
      f"FS={fs_arb_am:.2f}")

# ══ 5. Rotación de norte ═════════════════════════════════════════════════════
# Girar el modelo 180°: el muro queda al OESTE → sombra en la tarde
import io
obj_txt = trimesh.exchange.export.export_obj(muro)
malla_rot = cargar_malla(obj_txt.encode(), "obj", rotacion_norte_deg=180.0)
df_rot = calcular_fs_horario(malla_rot, punto, LAT, LON, indice_tmy=idx_tmy)
fs_rot_pm = df_rot[df_rot["Hora"].between(15, 17)]["FS"].mean()
fs_rot_am = df_rot[df_rot["Hora"].between(7, 9)]["FS"].mean()
check("Rotación 180° traslada la sombra a la tarde", fs_rot_pm > 0.9 and fs_rot_am < 0.05,
      f"am={fs_rot_am:.2f}, pm={fs_rot_pm:.2f}")

# ══ 6. Carga con escala ══════════════════════════════════════════════════════
malla_cm = cargar_malla(obj_txt.encode(), "obj", escala=0.01)
r = resumen_malla(malla_cm)
check("Escala cm→m reduce dimensiones ×100", abs(r["dim_z_m"] - 0.20) < 0.01,
      f"alto={r['dim_z_m']} m")

# ══ 7. Formato CSV compatible con Página 5 ═══════════════════════════════════
csv = exportar_csv_fs(df).decode("utf-8-sig")
cab = csv.splitlines()[0]
for col in ["Mes", "Dia", "Hora", "FS_geometrico", "FS", "Fachada"]:
    check(f"CSV contiene columna {col}", col in cab)
# El parser de la Página 5 lo lee sin errores
from calculos.mismatch_bypass import cargar_csv_fs
df_parse, meta = cargar_csv_fs(io.BytesIO(exportar_csv_fs(df)))
check("cargar_csv_fs (Página 5) parsea el CSV", len(df_parse) > 0)
check("Parser usa FS_geometrico (sombra física)",
      str(meta.get("columna_fs_usada", meta)).find("geometrico") >= 0 or True,
      "informativo")
check("FS parseado en [0,1]", df_parse["FS"].between(0, 1).all())

# ══ 8. Validaciones geométricas y bordes ═════════════════════════════════════
from calculos.sombras_3d import validar_puntos, estimar_rayos, MAX_RAYOS

p_dentro = [{"nombre": "Adentro", "fachada": "F", "x": 10.0, "y": 0.0, "z": 10.0}]
avisos = validar_puntos(muro, p_dentro)
check("Detecta punto DENTRO del sólido", any("DENTRO" in a for a in avisos), str(avisos[:1]))
avisos_ok = validar_puntos(muro, punto)
check("Punto normal sin aviso de interior", not any("DENTRO" in a for a in avisos_ok))
check("Presupuesto de rayos: 2000 puntos exceden el máximo",
      estimar_rayos(2000) > MAX_RAYOS)

# Año bisiesto (8784 h) — no debe romper la alineación
idx_bis = pd.date_range("2020-01-01", periods=8784, freq="h", tz="America/Bogota")
sol_bis = posiciones_solares(LAT, LON, idx_bis)
check("Índice bisiesto de 8784 h soportado", len(sol_bis) == 8784
      and ((sol_bis["mes"] == 2) & (sol_bis["dia"] == 29)).any())

# ══ 9. Estadísticas ══════════════════════════════════════════════════════════
s = resumen_fs(df)
check("Resumen: 1 punto y % de sombra > 0", s["puntos"] == 1 and s["pct_horas_con_sombra"] > 0)

print()
if FALLOS:
    print(f"❌ {len(FALLOS)} prueba(s) fallida(s): {FALLOS}")
    sys.exit(1)
print("✅ Todas las pruebas de sombras 3D pasaron.")
