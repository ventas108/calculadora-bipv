"""
Tests del combinador de curvas IV por MPPT (#157) — calculos/mppt_combinado.py

Casos:
  1. Un solo grupo → pérdida ≈ 0 (curva combinada = curva del grupo).
  2. Dos grupos IDÉNTICOS (misma G/T) → pérdida ≈ 0 (mismo Vmp).
  3. Dos grupos con G muy distinta (1000 vs 300 W/m²) misma orientación de curva
     → pérdida pequeña pero > 0 (Vmp cercanos, corrientes distintas).
  4. Consistencia con el Motor IV: Pmp combinada de un grupo (Ns=1, Np=1)
     ≈ p_mp de pvlib singlediode para el módulo (tolerancia de malla < 0.5%).
  5. Escalado serie/paralelo: grupo Ns=8, Np=2 a G uniforme ≈ 16 × Pmp módulo.
  6. Ventana MPPT degenerada/simetría: con ventana amplia el resultado no cambia.
  7. simular_mppts_proyecto agrega bien dos MPPTs.
  8. Pérdida siempre >= 0 y p_comb <= p_indep hora a hora.
"""

import sys, os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pvlib
from calculos.mppt_combinado import (
    simular_mppt_compartido, simular_mppts_proyecto, _params_grupo,
)
from calculos.modelo_iv import estimar_sdm_desde_ficha

FALLOS = []

def check(nombre, cond, detalle=""):
    estado = "✅" if cond else "❌"
    print(f"{estado} {nombre} {detalle}")
    if not cond:
        FALLOS.append(nombre)

# ── Panel de prueba: ficha ASP-ST1-T40 (CdTe) calibrada con el Motor IV ───────
ficha = {
    "Voc": 87.4, "Isc": 1.04, "Vmp": 65.9, "Imp": 0.91,
    "Voc_stc": 87.4, "Isc_stc": 1.04, "Vmp_stc": 65.9, "Imp_stc": 0.91,
    "Pmax_stc": 60.0, "N_s": 154, "tecnologia": "CdTe",
    "Tk_alfa": 0.04, "Tk_beta": -0.29, "Tk_gamma": -0.257, "NOCT": 45.0,
}
sdm = estimar_sdm_desde_ficha(ficha)
assert sdm is not None, "No se pudo calibrar el SDM del panel de prueba"
panel = {**ficha, **sdm}

H = 48
G_alta  = np.full(H, 1000.0)
G_media = np.full(H, 600.0)
G_baja  = np.full(H, 300.0)
T25     = np.full(H, 25.0)

def grupo(nombre, G, T=T25, ns=8, npar=2):
    return {"nombre": nombre, "G": G, "T_cel": T, "panel": panel,
            "n_serie": ns, "n_paralelo": npar}

# 1. Un solo grupo → pérdida ~0
r1 = simular_mppt_compartido([grupo("A", G_alta)])
check("1. Un grupo: pérdida ≈ 0", abs(r1["perdida_pct"]) < 0.05,
      f"(pérdida={r1['perdida_pct']}%)")

# 2. Dos grupos idénticos → pérdida ~0
r2 = simular_mppt_compartido([grupo("A", G_alta), grupo("B", G_alta.copy())])
check("2. Grupos idénticos: pérdida ≈ 0", abs(r2["perdida_pct"]) < 0.05,
      f"(pérdida={r2['perdida_pct']}%)")

# 3. G distinta → pérdida > 0 pero acotada (<5% para mismo panel/misma T)
r3 = simular_mppt_compartido([grupo("Sol", G_alta), grupo("Sombra", G_baja)])
check("3. G 1000 vs 300: pérdida > 0", r3["perdida_pct"] > 0.0,
      f"(pérdida={r3['perdida_pct']}%)")
check("3b. …y acotada (<5%)", r3["perdida_pct"] < 5.0,
      f"(pérdida={r3['perdida_pct']}%)")

# 4. Consistencia con singlediode (módulo suelto Ns=1, Np=1)
I_L, I_o, R_s, R_sh, nNsVth, _d2mutau, _NsVbi = _params_grupo(G_alta[:1], T25[:1], panel, 1, 1)
res_sd = pvlib.pvsystem.singlediode(
    photocurrent=I_L, saturation_current=I_o, resistance_series=R_s,
    resistance_shunt=R_sh, nNsVth=nNsVth, method='lambertw')
pmp_ref = float(np.asarray(res_sd["p_mp"])[0])
r4 = simular_mppt_compartido([grupo("solo", G_alta[:1], T25[:1], ns=1, npar=1)],
                             n_puntos=300)
pmp_malla = float(r4["p_dc_comb_W"][0])
err4 = abs(pmp_malla - pmp_ref) / pmp_ref * 100
check("4. Malla vs singlediode < 0.5%", err4 < 0.5, f"(err={err4:.3f}%)")

# 5. Escalado: Ns=8 × Np=2 ≈ 16 × módulo
r5 = simular_mppt_compartido([grupo("g", G_alta[:1], T25[:1], ns=8, npar=2)],
                             n_puntos=300)
esc = float(r5["p_dc_comb_W"][0]) / (16 * pmp_ref)
check("5. Escalado 8s×2p ≈ 16× módulo", abs(esc - 1.0) < 0.01, f"(ratio={esc:.4f})")

# 6. Ventana MPPT amplia no cambia el resultado
r6 = simular_mppt_compartido([grupo("Sol", G_alta), grupo("Sombra", G_baja)],
                             v_mppt_min=1.0, v_mppt_max=5000.0)
dif6 = abs(r6["e_dc_comb_kWh"] - r3["e_dc_comb_kWh"]) / max(r3["e_dc_comb_kWh"], 1e-9)
check("6. Ventana amplia ≈ sin ventana", dif6 < 0.01, f"(dif={dif6*100:.2f}%)")

# 7. Agregación por proyecto
r7 = simular_mppts_proyecto(
    {1: ["A"], 2: ["B", "C"]},
    {"A": grupo("A", G_alta), "B": grupo("B", G_media), "C": grupo("C", G_baja)},
)
suma = r7["por_mppt"][1]["e_dc_comb_kWh"] + r7["por_mppt"][2]["e_dc_comb_kWh"]
check("7. Total proyecto = suma de MPPTs",
      abs(r7["e_dc_comb_kWh"] - suma) < 0.2, f"({r7['e_dc_comb_kWh']} vs {suma})")

# 8. Invariantes: pérdida >= 0 y p_comb <= p_indep en todas las horas
ok8 = bool(np.all(r3["p_dc_comb_W"] <= r3["p_dc_indep_W"] + 1e-9))
check("8. p_comb <= p_indep en todas las horas", ok8)
check("8b. Pérdida total >= 0",
      all(r["perdida_kWh"] >= 0 for r in (r1, r2, r3)))

# 9. Snapshot peor hora coherente
ph = r3["peor_hora"]
check("9. Snapshot: I_total = Σ I_grupos",
      bool(np.allclose(ph["I_total"], np.sum(ph["I_grupos"], axis=0), atol=1e-6)))

print()
if FALLOS:
    print(f"💥 {len(FALLOS)} test(s) fallaron: {FALLOS}")
    sys.exit(1)
print("🎉 Todos los tests de mppt_combinado pasaron.")
