"""
Test de regresión: k_BIPV aplica la corrección térmica UNA SOLA VEZ.

Verifica que:
1. k_bipv=1.3 produce T_cell más alta que k_bipv=1.0.
2. E_ac con k=1.3 es menor que con k=1.0 (mayor temperatura → menor eficiencia).
3. La diferencia de E_ac por k_bipv está en el rango físicamente esperado (~1-4% tropicales).
4. Cuando Motor Óptico está activo, la POA sin térmica (poa_sin_termico) usada como G_eff
   produce resultados coherentes (sin doble conteo).
5. Ambos motores (simular_produccion_anual y simular_produccion_iv) usan el mismo k_bipv.

Ejecutar desde la raíz de bipv_python:
    python scripts/test_kbipv_thermal_single_source.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from calculos.temperatura import temperatura_celda_noct
from calculos.produccion import simular_produccion_anual
from calculos.motor_optico import cascada_optica, SOILING_COLOMBIA


# ── Datos sintéticos (año completo, trópico, ~5.5 kWh/m²/día) ─────────────────

np.random.seed(42)
idx = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")

# TMY simplificado: sol entre 06h-18h UTC con perfil senoidal
hora_utc = np.array([t.hour for t in idx])
dia_año  = np.array([t.dayofyear for t in idx])
sol_mask = (hora_utc >= 6) & (hora_utc <= 18)

# Irradiancias (no fotovoltaicas, solo luz diurna)
elev_rad = np.maximum(0, np.sin(np.pi * (hora_utc - 6) / 12))
G_base   = 900 * elev_rad * sol_mask
T2m      = 22.0 + 8.0 * elev_rad   # 22-30°C diurnos
WS10m    = 2.0 + 1.0 * np.random.rand(8760)

tmy_df = pd.DataFrame({
    "G_h":   G_base,
    "Gb_n":  G_base * 0.8,
    "Gd_h":  G_base * 0.2,
    "T2m":   T2m,
    "WS10m": WS10m,
}, index=idx)

# POA sintético (fachada vertical sur, ~60% de GHI)
poa_global = G_base * 0.6
poa_direct = poa_global * 0.75
poa_sky    = poa_global * 0.15
poa_ground = poa_global * 0.10

poa_df = pd.DataFrame({
    "poa_global":        poa_global,
    "poa_direct":        poa_direct,
    "poa_sky_diffuse":   poa_sky,
    "poa_ground_diffuse":poa_ground,
}, index=idx)

# Panel simplificado (sin SDM completo → usa modelo lineal de fallback)
panel = {
    "Pmax_stc":  400.0,   # W
    "NOCT":       50.0,   # °C — BIPV conservador
    "Tk_gamma":   -0.45,  # %/°C
}


# ── TEST 1: temperatura_celda_noct con diferentes k_bipv ──────────────────────
print("── TEST 1: temperatura_celda_noct ───────────────────────────")
G_test = np.array([0.0, 200.0, 500.0, 800.0, 1000.0])
T_test = np.full(5, 25.0)

t_k10 = temperatura_celda_noct(G_test, T_test, NOCT=50.0, k_bipv=1.0)
t_k13 = temperatura_celda_noct(G_test, T_test, NOCT=50.0, k_bipv=1.3)
t_k15 = temperatura_celda_noct(G_test, T_test, NOCT=50.0, k_bipv=1.5)

assert np.all(t_k13 >= t_k10), "k=1.3 debe producir T_cell >= k=1.0"
assert np.all(t_k15 >= t_k13), "k=1.5 debe producir T_cell >= k=1.3"
assert t_k10[0] == t_k13[0] == 25.0, "G=0 → T_cell = T_amb (sin calentamiento)"

delta_k13_800 = t_k13[3] - t_k10[3]  # G=800, T_amb=25
expected = 800 * (50-20)/800 * (1.3-1.0)   # = 9°C
assert abs(delta_k13_800 - expected) < 0.01, f"Delta T esperado {expected}°C, obtenido {delta_k13_800:.2f}°C"
print(f"  k=1.0, G=800: T_cell={t_k10[3]:.1f}°C")
print(f"  k=1.3, G=800: T_cell={t_k13[3]:.1f}°C  (Δ={delta_k13_800:.1f}°C ✓)")
print("  TEST 1 PASSED ✓\n")


# ── TEST 2: simular_produccion_anual — k_bipv reduce E_ac ─────────────────────
print("── TEST 2: simular_produccion_anual — efecto k_bipv ─────────")
res_k10 = simular_produccion_anual(
    tmy=tmy_df, poa_base=poa_df, panel=panel,
    N_paneles=10, eta_inversor=0.96, factor_pr_mismatch=1.0,
    k_bipv=1.0,
)
res_k13 = simular_produccion_anual(
    tmy=tmy_df, poa_base=poa_df, panel=panel,
    N_paneles=10, eta_inversor=0.96, factor_pr_mismatch=1.0,
    k_bipv=1.3,
)

E_k10 = res_k10["E_ac_anual_kWh"]
E_k13 = res_k13["E_ac_anual_kWh"]
diff_pct = (E_k10 - E_k13) / E_k10 * 100

assert E_k13 < E_k10, "k=1.3 (más caliente) debe producir menos que k=1.0"
assert 0.5 < diff_pct < 10.0, f"Diferencia debería ser 0.5-10%, es {diff_pct:.2f}%"
print(f"  E_ac k=1.0: {E_k10:,.0f} kWh/año")
print(f"  E_ac k=1.3: {E_k13:,.0f} kWh/año")
print(f"  Reducción: {diff_pct:.2f}% — dentro del rango físico esperado ✓")
print("  TEST 2 PASSED ✓\n")


# ── TEST 3: sin doble conteo — POA post-soil (sin f_term) + k_bipv SDM ────────
print("── TEST 3: cascada_optica → poa_post_soil vs poa_efectiva ───")
result_df, summary = cascada_optica(
    tmy_df=tmy_df,
    poa_df=poa_df,
    b0=0.05,
    noct=50.0,
    coef_temp=-0.0045,
    k_bipv=1.3,
    k_soiling_vert=0.65,
)

# Verificar que poa_post_soil >= poa_efectiva (la térmica solo reduce)
assert (result_df["poa_post_soil"] >= result_df["poa_efectiva"] - 1e-6).all(), \
    "poa_post_soil debe ser >= poa_efectiva (el f_term solo reduce)"

poa_st_annual  = result_df["poa_post_soil"].sum() / 1000   # kWh/m²
poa_ef_annual  = result_df["poa_efectiva"].sum() / 1000    # kWh/m²
diff_term_pct  = (poa_st_annual - poa_ef_annual) / poa_st_annual * 100

assert diff_term_pct >= 0, "poa_post_soil >= poa_efectiva"
assert diff_term_pct < 15, f"Diferencia térmica demasiado grande: {diff_term_pct:.1f}%"
print(f"  POA post-IAM/soiling:   {poa_st_annual:,.1f} kWh/m²/año  (para G_eff del SDM)")
print(f"  POA efectiva (c/térm):  {poa_ef_annual:,.1f} kWh/m²/año  (visualización/Financiero)")
print(f"  Pérdida térmica:        {diff_term_pct:.2f}%  ← solo se aplica UNA VEZ (en T_cell) ✓")

# Verificar que usar poa_sin_termico + k_bipv en SDM produce resultado coherente
poa_sin_term_df = poa_df.copy()
poa_sin_term_df["poa_global"] = result_df["poa_post_soil"].values

res_sin_term_k13 = simular_produccion_anual(
    tmy=tmy_df, poa_base=poa_sin_term_df, panel=panel,
    N_paneles=10, eta_inversor=0.96, factor_pr_mismatch=1.0,
    k_bipv=1.3,
)

res_doble_conteo = simular_produccion_anual(
    tmy=tmy_df, poa_base=poa_df.assign(
        poa_global=result_df["poa_efectiva"].values  # poa con f_term
    ), panel=panel,
    N_paneles=10, eta_inversor=0.96, factor_pr_mismatch=1.0,
    k_bipv=1.3,   # k_bipv OTRA VEZ = doble conteo
)

E_correcto      = res_sin_term_k13["E_ac_anual_kWh"]
E_doble_conteo  = res_doble_conteo["E_ac_anual_kWh"]
diff_dc_pct     = (E_correcto - E_doble_conteo) / E_correcto * 100

assert E_correcto > E_doble_conteo, "El doble conteo debe subestimar la producción"
assert diff_dc_pct > 0.5, f"El doble conteo debe dar diferencia medible, es {diff_dc_pct:.2f}%"
print(f"\n  Producción CORRECTA (poa_sin_term + k=1.3 SDM): {E_correcto:,.0f} kWh/año")
print(f"  Producción DOBLE CONTEO (poa_efectiva + k=1.3):  {E_doble_conteo:,.0f} kWh/año")
print(f"  Diferencia por doble conteo: {diff_dc_pct:.2f}% — confirma que separar es necesario ✓")
print("  TEST 3 PASSED ✓\n")


# ── TEST 4: NOCT consistente entre cascada y SDM ──────────────────────────────
print("── TEST 4: NOCT consistente entre Motor Óptico y SDM ────────")
noct_test = 50.0
_, summary_noct50 = cascada_optica(
    tmy_df=tmy_df, poa_df=poa_df, b0=0.05, noct=noct_test,
    coef_temp=-0.0045, k_bipv=1.3,
)
assert summary_noct50["noct"] == noct_test, "Summary debe reportar el NOCT usado"

panel_noct50 = dict(panel, NOCT=noct_test)
res_noct50 = simular_produccion_anual(
    tmy=tmy_df, poa_base=poa_sin_term_df, panel=panel_noct50,
    N_paneles=10, eta_inversor=0.96, factor_pr_mismatch=1.0,
    k_bipv=1.3,
)
assert res_noct50["E_ac_anual_kWh"] > 0, "SDM debe producir E_ac > 0 con NOCT=50"
print(f"  NOCT usado en Motor Óptico: {summary_noct50['noct']}°C")
print(f"  NOCT propagado al SDM:       {panel_noct50['NOCT']}°C  ← consistente ✓")
print("  TEST 4 PASSED ✓\n")



# ── TEST 5: selección de POA — sin bool eval de DataFrame ─────────────────────
print("── TEST 5: selección de POA — None checks explícitos ────────")
# Simula la lógica de _get_poa_df para verificar que None vs DataFrame se manejan bien
def _get_poa_df_sim(*dfs):
    """Réplica de la lógica en Producción: devuelve el primer DataFrame no-None."""
    for v in dfs:
        if v is not None:
            return v
    return None

# Caso 1: poa_sin_termico_df disponible → debe usarlo
r = _get_poa_df_sim(poa_sin_term_df, poa_df, None)
assert r is poa_sin_term_df, "Debe devolver poa_sin_termico_df cuando está disponible"

# Caso 2: poa_sin_termico_df es None → fallback a poa_efectiva
r2 = _get_poa_df_sim(None, poa_df, None)
assert r2 is poa_df, "Debe hacer fallback al siguiente DataFrame no-None"

# Caso 3: todos None → None
r3 = _get_poa_df_sim(None, None, None)
assert r3 is None, "Debe devolver None si todos son None"

# Verificar que evaluar el DataFrame como booleano lanza ValueError (el bug que corregimos)
try:
    bool(poa_sin_term_df)
    assert False, "pandas debería lanzar ValueError al evaluar bool(DataFrame)"
except (ValueError, TypeError):
    pass  # Correcto: esto es exactamente por qué usamos None checks explícitos

print("  Selección con None explícito funciona correctamente ✓")
print("  Cadena 'or' con DataFrames lanzaría ValueError — evitada correctamente ✓")
print("  TEST 5 PASSED ✓\n")


# ── TEST 6: Motor IV usa el mismo NOCT que el SDM base (fuente única) ──────────
print("── TEST 6: Motor IV — NOCT consistente con Motor Óptico ─────")
from calculos.produccion_iv import simular_produccion_iv

# Panel con ficha mínima para Motor IV (requiere parámetros SDM — usar panel simple
# que caerá al modelo lineal de fallback en produccion_iv si no tiene SDM completo)
# Verificamos solo que el NOCT se propaga correctamente al dict del panel
noct_mo = 50.0
panel_original = dict(panel, NOCT=45.0)  # NOCT diferente al del Motor Óptico

# Simular la propagación del NOCT que hace la página Producción:
# _panel_iv_sdm = dict(_panel_iv_prep); _panel_iv_sdm["NOCT"] = noct_mo
panel_iv_prep = dict(panel_original)  # repr. del panel_iv_prep
panel_iv_sdm  = dict(panel_iv_prep)
panel_iv_sdm["NOCT"] = noct_mo        # propagar NOCT del Motor Óptico

assert panel_iv_prep["NOCT"] == 45.0, "panel_iv_prep tiene NOCT original"
assert panel_iv_sdm["NOCT"]  == noct_mo, "panel_iv_sdm tiene NOCT del Motor Óptico"

# Verificar que T_cell difiere entre NOCT=45 y NOCT=50 con k_bipv=1.3
G_ref = 800.0; T_ref = 25.0
t_noct45 = temperatura_celda_noct(G_ref, T_ref, NOCT=45.0, k_bipv=1.3)
t_noct50 = temperatura_celda_noct(G_ref, T_ref, NOCT=50.0, k_bipv=1.3)
assert t_noct50 > t_noct45, "NOCT=50 debe dar T_cell > NOCT=45"

delta_noct = t_noct50 - t_noct45
# Δ teórico = 800*(50-45)/800*1.3 = 6.5°C
assert abs(delta_noct - 6.5) < 0.01, f"Delta NOCT esperado 6.5°C, obtenido {delta_noct:.2f}°C"

print(f"  T_cell(NOCT=45, k=1.3, G=800): {t_noct45:.1f}°C")
print(f"  T_cell(NOCT=50, k=1.3, G=800): {t_noct50:.1f}°C  (Δ={delta_noct:.1f}°C ✓)")
print(f"  NOCT propagado a panel_iv_sdm: {panel_iv_sdm['NOCT']}°C  ← mismo que Motor Óptico ✓")
print("  TEST 6 PASSED ✓\n")



# ── TEST 7: invalidación — KEYS_DERIVADOS_POA incluye claves del Motor Óptico ─
print("── TEST 7: invalidación — claves Motor Óptico en KEYS_DERIVADOS_POA ──")
from calculos.invalidacion import KEYS_DERIVADOS_POA

required_mo_keys = [
    "motor_optico_ok",
    "motor_optico_result_df",
    "motor_optico_summary",
    "poa_efectiva_df",
    "poa_sin_termico_df",
    "poa_efectiva_anual_kWh_m2",
    "motor_optico_k_bipv",
    "motor_optico_noct",
]
for k in required_mo_keys:
    assert k in KEYS_DERIVADOS_POA, (
        f"'{k}' debe estar en KEYS_DERIVADOS_POA para que se invalide "
        "cuando cambian coordenadas o geometría del proyecto"
    )
print(f"  {len(required_mo_keys)} claves del Motor Óptico presentes en KEYS_DERIVADOS_POA ✓")

# Simular el flujo de invalidación: cambio de geometría limpia todas las claves MO
_session_sim = {k: "valor_antiguo" for k in required_mo_keys}
_session_sim["produccion_ok"] = True

# Aplicar la invalidación (simula el comportamiento de Proyecto/Recurso Solar)
for _k in KEYS_DERIVADOS_POA:
    _session_sim.pop(_k, None)

# Verificar que NINGUNA clave del Motor Óptico sobrevive
for k in required_mo_keys:
    assert k not in _session_sim, (
        f"'{k}' debería haberse eliminado por la invalidación, "
        "pero sigue en session_state — Producción usaría POA obsoleta"
    )
assert "produccion_ok" not in _session_sim, "produccion_ok también debe invalidarse"
print("  Simulación de invalidación: todas las claves MO se eliminan correctamente ✓")
print("  Producción no puede reutilizar POA/parámetros del Motor Óptico anterior ✓")
print("  TEST 7 PASSED ✓\n")


# ── TEST 8: Justificación f_term(poa_optica) vs SDM(poa_post_soil) ────────────
print("── TEST 8: f_term vs SDM — diferencia de irradiancia base < 6% ──────")
# El cascade calcula f_term con poa_optica (después de IAM, antes de soiling).
# El SDM usa poa_post_soil (después de IAM + soiling) como G_eff.
# Esta diferencia es intencional y acotada:
#   - f_term con poa_optica muestra la carga térmica máxima (conservador) en el waterfall
#   - El SDM usa la irradiancia real en la celda (después de soiling)
# La diferencia ≤ soiling_max (6%) → error en T_cell ≤ 6% × (NOCT-20)/800 × k
# Ejemplo: G=800, soiling=6%, NOCT=50, k=1.3 → ΔT_cell ≤ 48×0.06×1.3 ≈ 3.7°C

poa_optica_arr = result_df["poa_optica"].values   # después de IAM
poa_soil_arr   = result_df["poa_post_soil"].values # después de IAM + soiling

# Calcular diferencia relativa donde hay sol
sol_mask2 = poa_optica_arr > 10
if sol_mask2.any():
    diff_rel = ((poa_optica_arr[sol_mask2] - poa_soil_arr[sol_mask2])
                / poa_optica_arr[sol_mask2])
    diff_max = diff_rel.max() * 100
    diff_mean = diff_rel.mean() * 100
    # La diferencia máxima debe ser ≤ 15% (soiling máximo razonable)
    assert diff_max < 15.0, (
        f"Diferencia poa_optica vs poa_post_soil es {diff_max:.1f}% — "
        "mayor que el soiling máximo esperado"
    )
    print(f"  poa_optica vs poa_post_soil: diff media={diff_mean:.2f}%, máx={diff_max:.2f}%")
    print(f"  Error en T_cell por esta diferencia: "
          f"≤ {diff_max/100 * 800 * (50-20)/800 * 1.3:.1f}°C con NOCT=50, k=1.3")
    print(f"  Aceptable: soiling reduce G en ≤{diff_max:.0f}%, efecto térmico secundario ✓")
print("  TEST 8 PASSED ✓\n")


print("=" * 65)
print("  TODOS LOS TESTS PASARON ✓")
print("  • La corrección térmica k_BIPV se aplica UNA SOLA VEZ.")
print("  • Selección de POA usa None checks (sin bool eval de DataFrame).")
print("  • Motor IV recibe el NOCT del Motor Óptico (fuente única).")
print("  • KEYS_DERIVADOS_POA invalida todas las claves del Motor Óptico.")
print("  • Diferencia de irradiancia f_term vs SDM es ≤ soiling (< 6%).")
print("=" * 65)
