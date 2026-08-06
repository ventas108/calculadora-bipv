# -*- coding: utf-8 -*-
"""Banco de pruebas — calculos/comparador_inversores.py (tarea #180).

Correr desde bipv_python/:  python3 scripts/test_comparador_inversores.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from calculos.comparador_inversores import (
    barrido_dc_ac,
    comparar_configuraciones,
    energia_con_clipping,
    filtrar_inversores_compatibles,
    unidades_necesarias,
)

FALLOS = []

def check(nombre, cond, detalle=""):
    estado = "✅" if cond else "❌"
    print(f"{estado} {nombre}" + (f" — {detalle}" if detalle else ""))
    if not cond:
        FALLOS.append(nombre)

# ── Panel de referencia: JA Solar 720W bifacial (proyecto Urabá) ──────────────
PANEL = {"Voc_stc": 49.0, "Vmp_stc": 41.0, "Isc_stc": 18.6, "Imp_stc": 17.6,
         "Tk_beta": -0.25, "Tk_gamma": -0.30, "Pmax_stc": 720.0}

INVERSORES = {
    # 12 trackers × 2 strings, 26 A/tracker → NO pasa con 2 strings (46.5 A)
    # pero SÍ con 1 string (23.25 A ≤ 26) → modo "1 string/tracker"
    "Huawei-100K": {"Vdc_max": 1500, "Vmppt_activo_min": 200, "Vmppt_min": 200,
                    "Vmppt_max": 1500, "n_trackers": 12, "n_strings_tracker": 2,
                    "I_max_tracker": 26, "Isc_max_tracker": 32.5,
                    "P_ac_nom_W": 100_000, "costo_usd": 5500},
    # 3 trackers × 2 strings, Isc_max 50 A → pasa en modo normal (46.5 ≤ 50)
    "TriP-30K":    {"Vdc_max": 1000, "Vmppt_activo_min": 200, "Vmppt_min": 200,
                    "Vmppt_max": 900, "n_trackers": 3, "n_strings_tracker": 2,
                    "I_max_tracker": 40, "Isc_max_tracker": 50,
                    "P_ac_nom_W": 30_000, "costo_usd": 2000},
    # Voc frío 882 V > 600 V → incompatible por tensión
    "Chico-600V":  {"Vdc_max": 600, "Vmppt_activo_min": 100, "Vmppt_min": 100,
                    "Vmppt_max": 550, "n_trackers": 2, "n_strings_tracker": 1,
                    "I_max_tracker": 20, "Isc_max_tracker": 25,
                    "P_ac_nom_W": 10_000, "costo_usd": 800},
    # Corriente insuficiente incluso con 1 string (Isc×1.25=23.25 > 15)
    "Debil-15A":   {"Vdc_max": 1100, "Vmppt_activo_min": 200, "Vmppt_min": 200,
                    "Vmppt_max": 1000, "n_trackers": 4, "n_strings_tracker": 1,
                    "I_max_tracker": 15, "Isc_max_tracker": 15,
                    "P_ac_nom_W": 25_000, "costo_usd": 1500},
    # Ficha incompleta
    "SinDatos":    {"Vdc_max": None, "Vmppt_max": None, "n_trackers": None,
                    "P_ac_nom_W": None, "costo_usd": None},
}

# ══ 1. Filtro de compatibilidad ══════════════════════════════════════════════
df = filtrar_inversores_compatibles(PANEL, INVERSORES, N_serie=18, T_frio=10.0, T_real=36.35)
by = df.set_index("modelo")

check("Huawei compatible en modo 1 string/tracker",
      bool(by.loc["Huawei-100K", "compatible"]) and by.loc["Huawei-100K", "modo"] == "1 string/tracker",
      f"modo={by.loc['Huawei-100K', 'modo']}")
check("Huawei strings_max = n_trackers (12)", by.loc["Huawei-100K", "strings_max"] == 12)
check("TriP-30K compatible en modo normal (Vmp 731V dentro de MPPT 900)",
      bool(by.loc["TriP-30K", "compatible"]) and by.loc["TriP-30K", "modo"] == "normal")
check("TriP-30K strings_max = 6", by.loc["TriP-30K", "strings_max"] == 6)
check("Chico-600V rechazado por Voc frío", not by.loc["Chico-600V", "compatible"]
      and "Voc" in by.loc["Chico-600V", "motivo"])
check("Debil-15A rechazado por corriente", not by.loc["Debil-15A", "compatible"]
      and "A por tracker" in by.loc["Debil-15A", "motivo"])
check("SinDatos rechazado por ficha incompleta", not by.loc["SinDatos", "compatible"]
      and "incompleta" in by.loc["SinDatos", "motivo"])

# Voc frío a 10 °C con Tk_beta −0.25%/°C: el frío SUBE el Voc →
# 18×49×(1+0.0025×15) = 885.3 V ≤ 1000 → TriP pasa
voc_frio = 18 * 49.0 * (1 + 0.0025 * 15)
check("Voc frío calculado con coef. térmico (≈885 V)",
      abs(df["Voc_string_frio (V)"].iloc[0] - round(voc_frio)) <= 1.0,
      f"esperado ≈{voc_frio:.0f}")

# ══ 2. unidades_necesarias ═══════════════════════════════════════════════════
check("17 strings / 12 entradas → 2 unidades", unidades_necesarias(17, 12) == 2)
check("17 strings / 6 entradas → 3 unidades", unidades_necesarias(17, 6) == 3)
check("strings_max=0 → 0 unidades (sin división por cero)", unidades_necesarias(17, 0) == 0)

# ══ 3. energia_con_clipping ══════════════════════════════════════════════════
# Serie sintética: 10 horas a 100 kW → 1000 kWh sin límite
p = np.full(10, 100_000.0)
e, c = energia_con_clipping(p, 80_000.0)
check("Clipping 20% con límite al 80% del pico", abs(e - 800.0) < 0.1 and abs(c - 20.0) < 0.1,
      f"E={e}, clip={c}")
e2, c2 = energia_con_clipping(p, None)
check("Sin límite → sin clipping", e2 == 1000.0 and c2 == 0.0)
p_nan = np.array([100_000.0, np.nan, 100_000.0])
e3, _ = energia_con_clipping(p_nan, 200_000.0)
check("NaN horarios tratados como 0", abs(e3 - 200.0) < 0.1)

# ══ 4. comparar_configuraciones (integración con financiero.py) ══════════════
horas = np.zeros(8760)
horas[6*365:12*365] = 150_000.0   # ~2190 h a 150 kW
cfgs = [
    {"nombre": "Inv-A", "p_ac_unidad_W": 100_000, "n_unidades": 2, "costo_unidad_usd": 5000},
    {"nombre": "Inv-B", "p_ac_unidad_W": 60_000, "n_unidades": 2, "costo_unidad_usd": 3000},
]
df_cmp = comparar_configuraciones(
    horas, cfgs, p_dc_stc_kW=220.32, capex_sin_inversores_usd=160_000,
    tarifa_cop_kwh=950, tipo_cambio=4000,
)
check("Comparativa devuelve 2 filas con columnas financieras",
      len(df_cmp) == 2 and {"TIR (%)", "LCOE (USD/kWh)", "Clipping (%)"} <= set(df_cmp.columns))
check("Config con 200 kW AC no recorta (pico 150 kW)",
      df_cmp.iloc[0]["Clipping (%)"] == 0.0)
check("Config con 120 kW AC recorta 20%",
      abs(df_cmp.iloc[1]["Clipping (%)"] - 20.0) < 0.1,
      f"clip={df_cmp.iloc[1]['Clipping (%)']}")
check("CAPEX incluye inversores (160k + 2×5k = 170k)",
      df_cmp.iloc[0]["CAPEX (USD)"] == 170_000)

# ══ 5. barrido_dc_ac ═════════════════════════════════════════════════════════
df_sw = barrido_dc_ac(
    horas, p_dc_stc_kW=220.32, capex_sin_inversores_usd=160_000,
    costo_usd_por_kw_ac=43.0, tarifa_cop_kwh=950, tipo_cambio=4000,
)
check("Barrido devuelve los 10 ratios por defecto", len(df_sw) == 10)
check("Exactamente un óptimo marcado", (df_sw["óptimo"] == "⭐").sum() == 1)
check("Clipping crece monótonamente con el ratio",
      df_sw["Clipping (%)"].is_monotonic_increasing)
_opt = df_sw[df_sw["óptimo"] == "⭐"].iloc[0]
check("El óptimo tiene el LCOE mínimo",
      _opt["LCOE (USD/kWh)"] == df_sw["LCOE (USD/kWh)"].min())

print()
if FALLOS:
    print(f"❌ {len(FALLOS)} prueba(s) fallida(s): {FALLOS}")
    sys.exit(1)
print("✅ Todas las pruebas del comparador pasaron.")
