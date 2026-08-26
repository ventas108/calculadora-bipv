# -*- coding: utf-8 -*-
"""Comparativa Alternativa B — 2 × ~100 kW para Urabá 220,32 kWp.

Simulación horaria (TMY PVGIS Apartadó) con clipping AC real por inversor
+ financiero preliminar con los mismos supuestos de la Ficha Técnica.
"""
import os
import sys

import numpy as np
import pandas as pd
import pvlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calculos.motor_optico import iam_ashrae  # noqa: E402

LAT, LON, ALT = 7.884, -76.635, 30
TILT, AZ, ALBEDO = 10, 180, 0.20
N_PAN, P_PAN = 306, 720.0          # W
P_DC = N_PAN * P_PAN               # 220 320 W
GAMMA = -0.0030                    # coef. potencia %/°C JA Solar n-type
BIFACIAL = 0.08                    # ganancia bifacial (misma de la ficha)
PERD_DC = 0.92                     # pérdidas DC combinadas (soiling, mismatch, cableado, LID) ≈ 8%
B0_VIDRIO, F_IAM_DIFUSA = 0.05, 0.95  # IAM vidrio estándar liso -- mismos valores que motor_optico.cascada_optica

# Candidatos: (nombre, Pac unidad W, unidades, eficiencia euro, precio USD/unidad supuesto mercado)
INVERSORES = [
    ("Huawei SUN2000-100KTL-M1", 100_000, 2, 0.984, 5500),
    ("Sungrow SG110CX",          110_000, 2, 0.984, 5300),
    ("Growatt MAX 100KTL3 LV",   100_000, 2, 0.982, 4300),
]

# ── TMY ──────────────────────────────────────────────────────────────────────
print("Descargando TMY PVGIS para Apartadó...")
tmy, meta = pvlib.iotools.get_pvgis_tmy(LAT, LON, map_variables=True)[:2]
# tmy.index de PVGIS viene en UTC -- convertir (no reetiquetar) a hora local,
# si no la irradiancia queda desfasada ~5h respecto a la posición solar real
# (bug encontrado 26-ago-2026, ver DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md).
tmy.index = tmy.index.tz_convert("America/Bogota")

solpos = pvlib.solarposition.get_solarposition(tmy.index, LAT, LON, ALT)
dni_extra = pvlib.irradiance.get_extra_radiation(tmy.index)
poa = pvlib.irradiance.get_total_irradiance(
    TILT, AZ, solpos.apparent_zenith, solpos.azimuth,
    tmy.dni, tmy.ghi, tmy.dhi, dni_extra=dni_extra, model="haydavies", albedo=ALBEDO)

# IAM (reflexión angular, ASHRAE) -- directa según AOI real, difusa con factor
# constante IEC 61853-3. Antes de este fix el script no la modelaba (PVsyst
# la reporta como -2.43% del POA para este proyecto).
aoi_deg = pvlib.irradiance.aoi(TILT, AZ, solpos.apparent_zenith, solpos.azimuth)
f_iam_dir = iam_ashrae(aoi_deg.values, B0_VIDRIO)
poa_dir_neta = poa.poa_direct.fillna(0) * f_iam_dir
poa_dif_neta = poa.poa_diffuse.fillna(0) * F_IAM_DIFUSA
poa_g = (poa_dir_neta + poa_dif_neta).clip(lower=0)

tcell = pvlib.temperature.faiman(poa_g, tmy.temp_air, tmy.wind_speed)
p_dc = P_DC * (poa_g / 1000.0) * (1 + GAMMA * (tcell - 25.0))
p_dc = p_dc.clip(lower=0) * (1 + BIFACIAL) * PERD_DC

# ── Financiero (supuestos ficha) ─────────────────────────────────────────────
TRM = 4000.0; TARIFA = 950.0        # COP/kWh EPM
CAPEX_BASE_USD = 180_442.0          # ficha central (incluía inversor ~200kW ref 11 000 USD)
INV_REF_USD = 11_000.0
OPEX_USD_KWP = 10.0; DEG = 0.004; TASA_DESC = 0.10; VIDA = 25

def tir_van(capex_usd, e0_kwh):
    flujo = [-capex_usd]
    opex = OPEX_USD_KWP * P_DC / 1000.0
    for y in range(1, VIDA + 1):
        e = e0_kwh * (1 - DEG) ** (y - 1)
        ahorro_usd = e * TARIFA / TRM
        flujo.append(ahorro_usd - opex)
    van = sum(f / (1 + TASA_DESC) ** i for i, f in enumerate(flujo))
    tir = np.round(np.irr(flujo) if hasattr(np, "irr") else _irr(flujo), 4)
    pay = capex_usd / (e0_kwh * TARIFA / TRM - opex)
    e_tot_desc = sum(e0_kwh * (1 - DEG) ** (y - 1) / (1 + TASA_DESC) ** y for y in range(1, VIDA + 1))
    lcoe_usd = (capex_usd + sum(opex / (1 + TASA_DESC) ** y for y in range(1, VIDA + 1))) / e_tot_desc
    return tir, van, pay, lcoe_usd

def _irr(cf, lo=-0.5, hi=1.5):
    from scipy.optimize import brentq
    f = lambda r: sum(c / (1 + r) ** i for i, c in enumerate(cf))
    try: return brentq(f, lo, hi)
    except Exception: return float("nan")

rows = []
for nombre, pac_u, n_u, eff, precio_u in INVERSORES:
    pac_tot = pac_u * n_u
    p_ac = (p_dc * eff).clip(upper=pac_tot)
    e_ac = p_ac.sum() / 1000.0                      # kWh/año
    clip = 100 * (1 - p_ac.sum() / (p_dc * eff).sum())
    capex = CAPEX_BASE_USD - INV_REF_USD + precio_u * n_u
    tir, van, pay, lcoe = tir_van(capex, e_ac)
    rows.append({
        "Configuración": f"2 × {nombre}",
        "AC total (kW)": pac_tot / 1000, "Ratio DC/AC": round(P_DC / pac_tot, 2),
        "E_ac (kWh/año)": round(e_ac), "Clipping (%)": round(clip, 2),
        "Yield (kWh/kWp)": round(e_ac / (P_DC / 1000)),
        "CAPEX (USD)": round(capex), "USD/Wp": round(capex / P_DC, 3),
        "TIR (%)": round(tir * 100, 1), "VPN (USD)": round(van),
        "Payback (años)": round(pay, 1), "LCOE (USD/kWh)": round(lcoe, 4),
    })

df = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(df.to_string(index=False))
df.to_excel("/home/runner/workspace/entregables/Comparativa_Alt_B_Inversores_Uraba.xlsx", index=False)
print("\nGuardado: entregables/Comparativa_Alt_B_Inversores_Uraba.xlsx")
