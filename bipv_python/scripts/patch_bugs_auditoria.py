#!/usr/bin/env python3
"""
Parche: 4 bugs de cálculo detectados en auditoría (agosto 2026)
Aplicar en el servidor: python3 patch_bugs_auditoria.py

Bugs corregidos:
  1. baterias_balance.py  — eta_rte aplicada dos veces en cap_mensual
  2. modelo_iv.py         — alpha_sc en unidades incorrectas (%/°C vs A/°C)
  3. produccion.py        — mismo alpha_sc + Y_r usaba POA efectiva (inflaba PR)
  4. mismatch_bypass.py   — mismo alpha_sc
  5. financiero.py        — docstring Art.12 describía fórmula incorrecta
"""
import re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent   # bipv_python/
CALCULOS = BASE / "calculos"

def patch(ruta: Path, buscar: str, reemplazar: str, descripcion: str) -> bool:
    texto = ruta.read_text(encoding="utf-8")
    if buscar not in texto:
        print(f"  ⚠  '{descripcion}' — fragmento NO encontrado en {ruta.name} (¿ya aplicado?)")
        return False
    nuevo = texto.replace(buscar, reemplazar, 1)
    ruta.write_text(nuevo, encoding="utf-8")
    print(f"  ✅  '{descripcion}' aplicado en {ruta.name}")
    return True


# ── 1. baterias_balance.py ─────────────────────────────────────────────────────
patch(
    CALCULOS / "baterias_balance.py",
    buscar=
        "        cap_mensual = C_util * dias * eta_rte\n"
        "            # Se carga con el excedente solar (limitado por cap mensual)\n"
        "            bat_cargada[m]    = min(excedente[m], cap_mensual)",
    reemplazar=
        "        cap_mensual = C_util * dias\n"
        "            # Se carga con el excedente solar (limitado por cap mensual)\n"
        "            # Nota: C_util ya incluye el factor eta_rte aplicado en dimensionar_bateria().\n"
        "            # No multiplicar de nuevo para evitar doble conteo de pérdidas RTE.\n"
        "            bat_cargada[m]    = min(excedente[m], cap_mensual)",
    descripcion="bug#1 — eliminar doble eta_rte en cap_mensual",
)

# ── 2. modelo_iv.py ────────────────────────────────────────────────────────────
patch(
    CALCULOS / "modelo_iv.py",
    buscar=
        "    I_L, I_o, R_s, _R_sh_pvlib, nNsVth = pvlib.pvsystem.calcparams_desoto(\n"
        "        effective_irradiance = G,\n"
        "        temp_cell            = T_cel_C,\n"
        "        alpha_sc             = panel[\"Tk_alfa\"] / 100.0,",
    reemplazar=
        "    # alpha_sc: pvlib espera A/°C (no %/°C).\n"
        "    # Conversión: Tk_alfa [%/°C] / 100 × Isc_stc [A] = A/°C\n"
        "    _Isc_stc = float(panel.get(\"Isc_stc\") or panel.get(\"Isc\") or 1.0)\n"
        "    _alpha_sc = panel[\"Tk_alfa\"] / 100.0 * _Isc_stc\n\n"
        "    I_L, I_o, R_s, _R_sh_pvlib, nNsVth = pvlib.pvsystem.calcparams_desoto(\n"
        "        effective_irradiance = G,\n"
        "        temp_cell            = T_cel_C,\n"
        "        alpha_sc             = _alpha_sc,",
    descripcion="bug#2 — alpha_sc en A/°C en modelo_iv.py",
)

# ── 3. produccion.py — alpha_sc ────────────────────────────────────────────────
patch(
    CALCULOS / "produccion.py",
    buscar='        alpha_sc             = panel["Tk_alfa"] / 100.0,',
    reemplazar='        alpha_sc             = panel["Tk_alfa"] / 100.0 * float(panel.get("Isc_stc") or panel.get("Isc") or 1.0),',
    descripcion="bug#2 — alpha_sc en A/°C en produccion.py",
)

# ── 4. produccion.py — Y_r ────────────────────────────────────────────────────
patch(
    CALCULOS / "produccion.py",
    buscar=
        "    H_i  = float(G_raw.sum()) / 1000.0          # GHI bruta kWh/m²\n"
        "    H_ef = float(G_eff.sum()) / 1000.0          # POA efectiva kWh/m²\n"
        "    Y_r  = H_ef                                  # Reference yield [h]  (G_STC = 1 kW/m²)",
    reemplazar=
        "    H_i  = float(G_raw.sum()) / 1000.0          # POA bruta kWh/m²\n"
        "    H_ef = float(G_eff.sum()) / 1000.0          # POA efectiva kWh/m² (post-mismatch)\n"
        "    Y_r  = H_i                                   # Reference yield [h] = H_t / G_STC (IEC 61724)\n"
        "    # NOTA: Y_r usa POA bruta (H_i), no H_ef, para que el PR incluya las pérdidas\n"
        "    # de mismatch como una pérdida real (PR más conservador y correcto según IEC 61724).",
    descripcion="bug#3 — Y_r usa POA bruta (IEC 61724), no POA efectiva",
)

# ── 5. mismatch_bypass.py — alpha_sc ──────────────────────────────────────────
patch(
    CALCULOS / "mismatch_bypass.py",
    buscar='        alpha_sc             = panel["Tk_alfa"] / 100.0,',
    reemplazar='        alpha_sc             = panel["Tk_alfa"] / 100.0 * float(panel.get("Isc_stc") or panel.get("Isc") or 1.0),',
    descripcion="bug#2 — alpha_sc en A/°C en mismatch_bypass.py",
)

# ── 6. financiero.py — docstring ───────────────────────────────────────────────
patch(
    CALCULOS / "financiero.py",
    buscar=
        "    Art. 12 — Exclusión IVA\n"
        "        Los equipos para SRFNC están excluidos de IVA (19%).\n"
        "        Ahorro = IVA que NO se paga = 0.19 / 1.19 × CAPEX_equipos\n"
        "        (porque el precio cotizado NO incluye IVA para estos proyectos)",
    reemplazar=
        "    Art. 12 — Exclusión IVA\n"
        "        Los equipos para SRFNC están excluidos de IVA (Ley 1715/Art.12).\n"
        "        Ahorro = IVA que NO se paga = 0.19 × CAPEX_equipos\n"
        "        Supuesto: el CAPEX ingresado en la app es el precio SIN IVA (precio base del proyecto).\n"
        "        Si el CAPEX ingresado YA incluye IVA, usar 0.19/1.19 en su lugar.",
    descripcion="bug#4 — docstring Art.12 corregido",
)

print("\nListo. Reiniciar con: pm2 restart streamlit-bipv")
