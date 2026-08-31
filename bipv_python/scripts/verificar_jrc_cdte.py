# -*- coding: utf-8 -*-
"""Verificación cruzada CdTe (31-ago-2026): corre el power-rating model de
Huld/JRC (calculos/modelo_jrc_cdte.py) sobre el TMY REAL de Teusaquillo,
Bogotá (mismo sitio, misma fuente de datos, mismo pipeline de POA que
`FICHA_PVSYST_TEUSAQUILLO.md`), para comparar contra el PR=100,6%/101,2%
que dio el motor principal (SDM De Soto) de la app -- ver el docstring de
`calculos/modelo_jrc_cdte.py` para las 2 hipótesis que este script busca
distinguir.

Uso: python scripts/verificar_jrc_teusaquillo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculos.solar import obtener_tmy_pvgis, calcular_poa  # noqa: E402
from calculos.modelo_jrc_cdte import calcular_pr_jrc_cdte  # noqa: E402

# Sitio real: Bogotá (Teusaquillo) -- datos/ciudades_colombia.py
LAT, LON, ALT_M = 4.711, -74.072, 2600
TILT, AZIMUTH, ALBEDO = 90.0, 180.0, 0.20  # fachada vertical, sur, convención pvlib

# Panel real: ASP-ST1-T40 (datos/tecnologias_bipv.py) -- 128 módulos, 63 W/módulo STC
P_STC_MODULO_W = 63.0
N_MODULOS = 128
P_STC_TOTAL_W = P_STC_MODULO_W * N_MODULOS  # 8064 W = 8,064 kWp, igual que la ficha real

print(f"Descargando TMY real PVGIS para Bogotá ({LAT}, {LON})...")
tmy = obtener_tmy_pvgis(LAT, LON)
print(f"  {len(tmy)} horas descargadas.")

print("Calculando POA (Hay-Davies, mismo modelo que usa la app)...")
poa = calcular_poa(tmy, LAT, LON, ALT_M, TILT, AZIMUTH, ALBEDO)
poa_global = poa["poa_global"]

print(f"  POA anual bruta: {poa_global.sum() / 1000.0:.1f} kWh/m²/año "
      f"(referencia app: 807,8 kWh/m²/año -- sin Motor Óptico)")

print("\nCorriendo power-rating model de Huld/JRC para CdTe (128 módulos, 8,064 kWp)...")
r = calcular_pr_jrc_cdte(
    poa_wm2=poa_global.to_numpy(),
    t_ambiente_c=tmy["T2m"].to_numpy(),
    viento_ms=tmy["WS10m"].to_numpy(),
    p_stc_w=P_STC_TOTAL_W,
)

print("\n" + "=" * 70)
print("RESULTADO -- power-rating model JRC/Huld (CdTe), sobre POA BRUTA")
print("(sin Motor Óptico: mismo punto de comparación que la fila")
print(" 'Sin Motor Óptico' de FICHA_PVSYST_TEUSAQUILLO.md)")
print("=" * 70)
print(f"POA anual usada     : {r['POA_anual_kWh_m2']:.1f} kWh/m²/año")
print(f"E_dc anual (JRC)     : {r['E_anual_kWh']:.0f} kWh/año")
print(f"PR (JRC)             : {r['PR_pct']:.2f}%")
print()
print("Comparación:")
print(f"  App (SDM De Soto, sin Motor Óptico)  : PR = 100,6%  (E_ac 6.554 kWh/año)")
print(f"  JRC/Huld (este script)                : PR = {r['PR_pct']:.2f}%")
print(f"  Literatura CdTe BIPV tropical (Kumar)  : PR = 74,92% a 77,36% (techo)")
print(f"                                            66,42% a 76,26% (fachada)")
