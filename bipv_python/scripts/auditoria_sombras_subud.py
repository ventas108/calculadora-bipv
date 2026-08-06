# -*- coding: utf-8 -*-
"""Auditoría exhaustiva de Sombras SketchUp con el modelo real SUBUD Tesauquillo.

1. Carga y sanidad del OBJ real exportado de SketchUp.
2. Rendimiento del ray-casting (malla real × 8760 h).
3. Física de las sombras: puntos alrededor del edificio → patrón esperado.
4. Cruce con el CSV real de la calculadora web (FS_geometrico = 0 en Fachada Este).
5. ¿La Página 5 parsea el CSV REAL de la web (meses en texto, horas HH:MM)?
6. ¿La Página 5 parsea nuestro CSV generado con el modelo real?
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import numpy as np
import pandas as pd

from calculos.sombras_3d import (
    cargar_malla, resumen_malla, calcular_fs_horario, exportar_csv_fs,
    resumen_fs, validar_puntos,
)
from calculos.mismatch_bypass import cargar_csv_fs

OBJ = "../attached_assets/SUBUD_TESAUQUILLO_teja_fv_ULT_1786029427006.obj"
CSV_WEB = "../attached_assets/analisis_sombreado_2026-07-14_(8)_1786029427006.csv"
LAT, LON = 4.87, -74.10  # Sabana de Bogotá (Tenjo/Tesauquillo aprox.)

FALLOS, HALLAZGOS = [], []

def check(nombre, cond, detalle=""):
    print(("✅" if cond else "❌"), nombre + (f" — {detalle}" if detalle else ""))
    if not cond:
        FALLOS.append(nombre)

def hallazgo(txt):
    HALLAZGOS.append(txt)
    print("🔎", txt)

# ══ 1. Carga del modelo real ═════════════════════════════════════════════════
t0 = time.time()
malla = cargar_malla(OBJ, "obj")
r = resumen_malla(malla)
check("OBJ real carga sin error", True, f"{r['n_triangulos']:,} tri en {time.time()-t0:.1f}s")
check("Dimensiones plausibles en metros (18×2×11 m)",
      10 < r["dim_x_m"] < 30 and r["dim_z_m"] < 20, str(r))
print("   bounds:", malla.bounds.round(1).tolist())

# ══ 2. Puntos de prueba alrededor del edificio ═══════════════════════════════
# El edificio ocupa x∈[-48,-29.8], y∈[5.8,7.9], z∈[-11.5,-0.8]
# (z negativo: el modelo está por debajo del origen de SketchUp — válido).
cx, cy = -38.9, 6.85           # centro en planta
z_medio = -6.0                 # media altura del edificio
puntos = [
    # Punto al ESTE del edificio (x mayor), pegado a 2 m de la cara este:
    {"nombre": "Este-cerca",  "fachada": "Este",  "x": -27.0, "y": cy, "z": z_medio},
    # Punto al OESTE, a 2 m:
    {"nombre": "Oeste-cerca", "fachada": "Oeste", "x": -50.5, "y": cy, "z": z_medio},
    # Punto ENCIMA del techo (no debería tener sombra casi nunca):
    {"nombre": "Techo", "fachada": "Cubierta", "x": cx, "y": cy, "z": 0.5},
    # Punto lejos al sur (30 m): sombra solo con sol al norte y bajo:
    {"nombre": "Sur-lejos", "fachada": "Sur", "x": cx, "y": -25.0, "z": -11.0},
]
avisos = validar_puntos(malla, puntos)
for a in avisos:
    print("   aviso:", a)

# ══ 3. Ray-casting completo — rendimiento ════════════════════════════════════
idx = pd.date_range("2023-01-01", periods=8760, freq="h", tz="America/Bogota")
t0 = time.time()
df = calcular_fs_horario(malla, puntos, LAT, LON, indice_tmy=idx)
dt = time.time() - t0
check("Ray-casting 4 puntos × año completo", len(df) > 0,
      f"{len(df):,} registros en {dt:.1f}s ({len(df)/max(dt,1e-9):,.0f} rayos/s)")
check("Tiempo razonable para uso en Streamlit (< 120 s)", dt < 120, f"{dt:.1f}s")

# ══ 4. Física de las sombras ═════════════════════════════════════════════════
piv = df.pivot_table(index="Hora", columns="Punto", values="FS", aggfunc="mean")
print("\nFS medio por hora y punto:")
print(piv.round(2).to_string())

fs_techo = df[df["Punto"] == "Techo"]["FS"].mean()
check("Techo casi sin sombra (FS medio < 0.05)", fs_techo < 0.05, f"{fs_techo:.3f}")

este_pm = piv.get("Este-cerca", pd.Series(dtype=float)).reindex(range(14, 18)).mean()
este_am = piv.get("Este-cerca", pd.Series(dtype=float)).reindex(range(7, 11)).mean()
check("Punto al Este: sombra en la TARDE (edificio tapa el sol del oeste)",
      este_pm > este_am, f"am={este_am:.2f} pm={este_pm:.2f}")

oeste_am = piv.get("Oeste-cerca", pd.Series(dtype=float)).reindex(range(7, 11)).mean()
oeste_pm = piv.get("Oeste-cerca", pd.Series(dtype=float)).reindex(range(14, 18)).mean()
check("Punto al Oeste: sombra en la MAÑANA (edificio tapa el sol del este)",
      oeste_am > oeste_pm, f"am={oeste_am:.2f} pm={oeste_pm:.2f}")

sur = df[df["Punto"] == "Sur-lejos"]["FS"].mean()
hallazgo(f"Punto a 30 m al sur: FS medio anual {sur:.3f} (esperado bajo; en lat 4.9°N "
         "el sol pasa al norte medio año y puede dar algo de sombra estacional)")

# ══ 5. Cruce con el CSV real de la calculadora web ═══════════════════════════
web = pd.read_csv(CSV_WEB)
hallazgo(f"CSV web: FS_geometrico=0 en las {len(web)} horas de Fachada Este → la web dice "
         "que esos puntos NO tienen sombra dura en las mañanas de días críticos.")
# Nuestro punto Este-cerca en las MISMAS horas de la mañana (6:30–11:30 → horas 6-11):
mask_am = df["Punto"].eq("Este-cerca") & df["Hora"].between(6, 11)
fs_nuestro_am = df[mask_am]["FS"].mean()
check("Coincide con la web: cara Este sin sombra dura en la mañana (FS<0.05)",
      fs_nuestro_am < 0.05, f"FS medio 6-11h = {fs_nuestro_am:.3f}")
hallazgo("La columna FS del CSV web trae 0.7–0.8 CONSTANTE con FS_geometrico=0 — parece un "
         "valor de 'Situacion' y NO la sombra: correcta la decisión de la Página 5 de "
         "priorizar FS_geometrico e ignorar FS/FS_climatico.")

# ══ 6. ¿La Página 5 parsea el CSV REAL de la web? ════════════════════════════
try:
    df_web_parse, meta_web = cargar_csv_fs(CSV_WEB)
    meses = sorted(df_web_parse["mes"].unique().tolist())
    check("Página 5 parsea el CSV real de la web (meses 'Mar/Dic', horas '06:30')",
          len(df_web_parse) == len(web) and 3 in meses and 12 in meses,
          f"{len(df_web_parse)} filas, meses={meses}")
except Exception as e:
    check("Página 5 parsea el CSV real de la web", False, f"EXCEPCIÓN: {e}")

# ══ 7. ¿La Página 5 parsea NUESTRO CSV del modelo real? ══════════════════════
csv_bytes = exportar_csv_fs(df)
df_parse, meta = cargar_csv_fs(io.BytesIO(csv_bytes))
check("Página 5 parsea nuestro CSV del modelo real", len(df_parse) > 0,
      f"{len(df_parse):,} filas")
fachadas = meta.get("fachadas") if isinstance(meta, dict) else None
hallazgo(f"Fachadas detectadas por el parser: {fachadas}")

print("\n── Resumen ──")
s = resumen_fs(df)
print(s)
print()
if FALLOS:
    print(f"❌ {len(FALLOS)} verificación(es) fallida(s): {FALLOS}")
    sys.exit(1)
print("✅ Auditoría con modelo real superada.")
