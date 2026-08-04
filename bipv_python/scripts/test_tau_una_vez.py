"""
test_tau_una_vez.py — Guardia de regresión para la tarea #56.

Verifica que la transparencia τ de paneles BIPV se aplica EXACTAMENTE UNA VEZ
en el flujo de energía:

  1. El Motor Óptico NO debe restar τ de `poa_efectiva` (la POA que va a
     Producción): el modelo SDM usa Isc_stc del panel real, donde el
     fabricante ya midió la corriente con el vidrio semitransparente
     (Isc_real = Isc_celda × (1−τ)). Restar τ del POA daría doble conteo.
  2. `perdida_tau` y `poa_efectiva_celda` existen SOLO como indicadores
     informativos, y el summary debe declararlo (`_tau_solo_informacional`).
  3. Producción no debe volver a multiplicar por (1−τ): con el mismo POA y
     el mismo panel, la energía calculada no depende del slider τ.

Uso:  python scripts/test_tau_una_vez.py   (exit 0 = OK, 1 = falla)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculos.motor_optico import cascada_optica  # noqa: E402

fallos = []


def check(cond: bool, msg: str) -> None:
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        fallos.append(msg)


# ── TMY y POA sintéticos (8760 h) ─────────────────────────────────────────────
idx = pd.date_range("2023-01-01", periods=8760, freq="h")
hora = idx.hour.values
sol = ((hora >= 6) & (hora <= 18)).astype(float)
poa = 600.0 * np.sin(np.pi * (hora - 6) / 12.0).clip(0) * sol

tmy_df = pd.DataFrame({"T2m": np.full(8760, 25.0),
                       "G(h)": poa, "Gb_n": poa * 0.8,
                       "RH": np.full(8760, 70.0)}, index=idx)
poa_df = pd.DataFrame({"poa_global": poa,
                       "poa_directa": poa * 0.7,
                       "poa_difusa": poa * 0.3,
                       "aoi": np.full(8760, 30.0)}, index=idx)

kwargs = dict(tmy_df=tmy_df, poa_df=poa_df, b0=0.05, noct=50.0,
              coef_temp=-0.45, k_bipv=1.2, soiling_config=None,
              f_iam_dif=0.95, k_soiling_vert=0.5)

print("1. Motor Óptico: τ=0% vs τ=40% deben producir la MISMA poa_efectiva")
r0, s0 = cascada_optica(transparencia=0.0, **kwargs)
r40, s40 = cascada_optica(transparencia=0.40, **kwargs)

check(np.allclose(r0["poa_efectiva"].values, r40["poa_efectiva"].values),
      "poa_efectiva idéntica con τ=0% y τ=40% (τ no se resta del POA)")
check(np.allclose(r40["poa_efectiva"].values, r40["poa_post_term"].values),
      "poa_efectiva == poa_post_term (última etapa real de la cascada)")
check(s40.get("_tau_solo_informacional") is True,
      "summary declara _tau_solo_informacional=True")
check(s40["perdida_tau_kWh_m2_info"] > 0,
      "perdida_tau informativa > 0 con τ=40%")
check(abs(s40["perdida_total_kWh_m2"]
          - (s40["perdida_iam_kWh_m2"] + s40["perdida_soil_kWh_m2"]
             + s40["perdida_term_kWh_m2"])) < 0.5,
      "perdida_total NO incluye la pérdida τ informativa")
check(np.allclose(r40["poa_efectiva_celda"].values,
                  r40["poa_post_term"].values * 0.60, atol=1e-6),
      "poa_efectiva_celda = poa_post_term × (1−τ) (solo informativa)")

print("2. Producción: la energía no depende del slider τ (τ vive en Isc_stc)")
try:
    from calculos.produccion import calcular_produccion_horaria  # noqa: E402
    import inspect
    src = inspect.getsource(sys.modules["calculos.produccion"])
    check("transparencia" not in src and "(1 - tau" not in src
          and "(1-tau" not in src,
          "calculos/produccion.py no contiene ninguna corrección por τ")
except ImportError as e:  # pvlib u otra dependencia ausente en el entorno
    print(f"  ⚠️  produccion no importable aquí ({e}) — se valida por fuente")
    src = (Path(__file__).resolve().parent.parent
           / "calculos" / "produccion.py").read_text(encoding="utf-8")
    check("transparencia" not in src, "produccion.py no menciona transparencia")

if fallos:
    print(f"\n🔴 {len(fallos)} verificación(es) fallaron — riesgo de doble conteo de τ")
    sys.exit(1)
print("\n🟢 τ se aplica exactamente una vez en todo el flujo — sin doble conteo")
