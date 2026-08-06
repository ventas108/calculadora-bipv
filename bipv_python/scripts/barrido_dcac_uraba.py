# -*- coding: utf-8 -*-
"""Alternativa E — Barrido de ratio DC/AC para Urabá 220,32 kWp.

Misma simulación horaria (TMY PVGIS Apartadó) que la comparativa Alt B;
se varía la capacidad AC instalada y se mide clipping, CAPEX, TIR y LCOE.
Costo de inversor: ~43 USD/kW AC (referencia Growatt clase 100 kW).
"""
import numpy as np
import pandas as pd
import pvlib
from scipy.optimize import brentq

LAT, LON, ALT = 7.884, -76.635, 30
TILT, AZ, ALBEDO = 10, 180, 0.20
P_DC = 306 * 720.0
GAMMA, BIFACIAL, PERD_DC, EFF = -0.0030, 0.08, 0.92, 0.982

tmy, meta = pvlib.iotools.get_pvgis_tmy(LAT, LON, map_variables=True)[:2]
tmy.index = pd.date_range("2023-01-01", periods=len(tmy), freq="h", tz="America/Bogota")
solpos = pvlib.solarposition.get_solarposition(tmy.index, LAT, LON, ALT)
poa = pvlib.irradiance.get_total_irradiance(
    TILT, AZ, solpos.apparent_zenith, solpos.azimuth,
    tmy.dni, tmy.ghi, tmy.dhi,
    dni_extra=pvlib.irradiance.get_extra_radiation(tmy.index),
    model="haydavies", albedo=ALBEDO)
poa_g = poa.poa_global.fillna(0).clip(lower=0)
tcell = pvlib.temperature.faiman(poa_g, tmy.temp_air, tmy.wind_speed)
p_dc = (P_DC * (poa_g / 1000.0) * (1 + GAMMA * (tcell - 25.0))).clip(lower=0) * (1 + BIFACIAL) * PERD_DC
p_ac_sin_limite = p_dc * EFF
print("Pico AC sin límite:", round(p_ac_sin_limite.max() / 1000, 1), "kW")

TRM, TARIFA = 4000.0, 950.0
CAPEX_SIN_INV = 180_442.0 - 11_000.0
USD_POR_KW_AC = 43.0
OPEX_USD_KWP, DEG, TASA, VIDA = 10.0, 0.004, 0.10, 25

def indicadores(capex, e0):
    opex = OPEX_USD_KWP * P_DC / 1000.0
    cf = [-capex] + [e0 * (1 - DEG) ** (y - 1) * TARIFA / TRM - opex for y in range(1, VIDA + 1)]
    f = lambda r: sum(c / (1 + r) ** i for i, c in enumerate(cf))
    try: tir = brentq(f, -0.5, 2.0)
    except Exception: tir = float("nan")
    van = sum(c / (1 + TASA) ** i for i, c in enumerate(cf))
    pay = capex / (e0 * TARIFA / TRM - opex)
    e_desc = sum(e0 * (1 - DEG) ** (y - 1) / (1 + TASA) ** y for y in range(1, VIDA + 1))
    lcoe = (capex + sum(opex / (1 + TASA) ** y for y in range(1, VIDA + 1))) / e_desc
    return tir, van, pay, lcoe

rows = []
# Configuraciones AC realistas (2 equipos o equipos comerciales existentes)
for etiqueta, ac_kw in [
    ("2 × 110 kW (SG110CX)", 220), ("2 × 100 kW", 200), ("2 × 90 kW", 180),
    ("2 × 80 kW", 160), ("2 × 75 kW", 150), ("2 × 70 kW", 140),
    ("2 × 60 kW", 120), ("2 × 50 kW", 100),
]:
    pac = p_ac_sin_limite.clip(upper=ac_kw * 1000)
    e_ac = pac.sum() / 1000.0
    clip = 100 * (1 - pac.sum() / p_ac_sin_limite.sum())
    capex = CAPEX_SIN_INV + USD_POR_KW_AC * ac_kw
    tir, van, pay, lcoe = indicadores(capex, e_ac)
    rows.append({
        "Configuración AC": etiqueta, "AC (kW)": ac_kw, "Ratio DC/AC": round(P_DC / 1000 / ac_kw, 2),
        "E_ac (kWh/año)": round(e_ac), "Clipping (%)": round(clip, 2),
        "CAPEX (USD)": round(capex), "TIR (%)": round(tir * 100, 1),
        "VPN (USD)": round(van), "Payback (años)": round(pay, 2),
        "LCOE (USD/kWh)": round(lcoe, 4),
    })

df = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(df.to_string(index=False))
df.to_excel("/home/runner/workspace/entregables/Barrido_DCAC_Uraba.xlsx", index=False)
print("OK")
