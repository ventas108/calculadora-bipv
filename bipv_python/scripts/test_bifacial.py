"""
test_bifacial.py — Guardia de regresión del modelo bifacial (pvlib infinite_sheds).

Verifica que:
1. Sin `bifacial`, calcular_poa mantiene el comportamiento monofacial histórico.
2. Con `bifacial`, poa_global = poa_front + bifacialidad × poa_rear, con ganancia
   positiva y físicamente plausible para un techo plano con buen albedo.
3. bifacialidad → 0 converge al resultado monofacial.
4. Más albedo trasero ⇒ más ganancia (monotonía física).
5. El loader del catálogo expone `bifacialidad_pct` (JA Solar JAM66D46 = 80).
6. multi_superficie propaga albedo/bifacial sin romper la firma anterior.

Uso:  python scripts/test_bifacial.py   (desde bipv_python/)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

fallos = []


def check(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        fallos.append(msg)


# ── TMY sintético: un año horario con GHI/DNI/DHI de cielo despejado simple ────
idx = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")
hora = idx.hour + idx.dayofyear * 0  # solo la hora local UTC-5 aprox (Colombia)
sol = np.clip(np.sin((hora - 11.0) / 12.0 * np.pi), 0, None)  # pico ~ 17 UTC
ghi = 950.0 * sol
dhi = 0.25 * ghi
dni = np.where(sol > 0.05, (ghi - dhi) / np.maximum(sol, 0.05), 0.0)
tmy = pd.DataFrame({"G_h": ghi, "Gb_n": np.clip(dni, 0, 1000), "Gd_h": dhi,
                    "T2m": 25.0, "WS10m": 1.0, "SP": 101325.0}, index=idx)

LAT, LON, ALT = 6.25, -75.57, 1495  # Medellín

from calculos.solar import calcular_poa  # noqa: E402

print("1. Compatibilidad monofacial (sin parámetro bifacial)")
poa_mono = calcular_poa(tmy, LAT, LON, ALT, tilt=10, azimuth=180)
check(set(["poa_global", "poa_direct", "poa_diffuse"]) <= set(poa_mono.columns),
      "columnas pvlib estándar presentes")
check("poa_rear" not in poa_mono.columns, "sin columnas bifaciales en modo monofacial")
check(poa_mono["poa_global"].sum() > 0, "POA anual > 0")

print("2. Modelo bifacial: estructura y ganancia plausible (techo plano, albedo 0.5)")
cfg = {"bifacialidad": 0.80, "altura_m": 1.5, "albedo_trasero": 0.50, "gcr": 0.25}
poa_bif = calcular_poa(tmy, LAT, LON, ALT, tilt=10, azimuth=180,
                       albedo=0.20, bifacial=cfg)
check({"poa_front", "poa_rear"} <= set(poa_bif.columns), "columnas poa_front/poa_rear presentes")
suma = poa_bif["poa_front"] + 0.80 * poa_bif["poa_rear"]
check(np.allclose(poa_bif["poa_global"], suma, rtol=0.02, atol=1.0),
      "poa_global ≈ poa_front + bifacialidad × poa_rear (infinite_sheds coherente)")
gan = poa_bif["poa_global"].sum() / poa_mono["poa_global"].sum() - 1.0
check(0.005 < gan < 0.35,
      f"ganancia bifacial plausible: +{gan*100:.1f}% (esperado 0.5–35% — TMY "
      "sintético difuso-alto con albedo 0.5 se acerca al extremo superior)")
check((poa_bif["poa_rear"] >= 0).all(), "poa_rear nunca negativa")

print("3. bifacialidad → 0: solo queda el frente de infinite_sheds (≤ monofacial)")
cfg0 = dict(cfg, bifacialidad=0.0)
poa_b0 = calcular_poa(tmy, LAT, LON, ALT, tilt=10, azimuth=180,
                      albedo=0.20, bifacial=cfg0)
_ratio0 = poa_b0["poa_global"].sum() / poa_mono["poa_global"].sum()
check(np.allclose(poa_b0["poa_global"], poa_b0["poa_front"], atol=1e-6),
      "con bifacialidad 0, poa_global == poa_front (sin aporte trasero)")
check(0.85 <= _ratio0 <= 1.02,
      f"frente infinite_sheds coherente con el monofacial clásico "
      f"(ratio {_ratio0:.3f}; ≤1 esperado por sombreado fila-fila)")

print("3b. GCR alto ⇒ el frente pierde por sombreado fila-fila (coherencia geométrica)")
f_gcr_lo = calcular_poa(tmy, LAT, LON, ALT, 10, 180, 0.20,
                        dict(cfg, gcr=0.15))["poa_front"].sum()
f_gcr_hi = calcular_poa(tmy, LAT, LON, ALT, 10, 180, 0.20,
                        dict(cfg, gcr=0.85))["poa_front"].sum()
check(f_gcr_hi < f_gcr_lo,
      f"poa_front con GCR 0.85 ({f_gcr_hi/1000:.0f} kWh/m²) < GCR 0.15 ({f_gcr_lo/1000:.0f} kWh/m²)")

print("4. Monotonía: más albedo trasero ⇒ más ganancia")
g_lo = calcular_poa(tmy, LAT, LON, ALT, 10, 180, 0.20,
                    dict(cfg, albedo_trasero=0.10))["poa_global"].sum()
g_hi = calcular_poa(tmy, LAT, LON, ALT, 10, 180, 0.20,
                    dict(cfg, albedo_trasero=0.60))["poa_global"].sum()
check(g_hi > g_lo, f"albedo trasero 0.60 ({g_hi/1000:.0f} kWh/m²) > 0.10 ({g_lo/1000:.0f} kWh/m²)")

print("5. Catálogo: bifacialidad_pct expuesta por el loader")
try:
    from datos.catalogo_paneles_excel import cargar_catalogo_paneles
    cat = cargar_catalogo_paneles()
    ja = [p for n, p in cat.items() if "JAM66D46" in n.upper()]
    check(all("bifacialidad_pct" in p for p in cat.values()),
          "todos los paneles traen la clave bifacialidad_pct")
    check(bool(ja) and all(float(p.get("bifacialidad_pct") or 0) == 80.0 for p in ja),
          f"JA Solar JAM66D46 con bifacialidad 80% ({len(ja)} modelos)")
except Exception as e:  # el Excel puede no existir en algunos entornos
    print(f"  ⚠️  catálogo Excel no disponible aquí ({e}) — se omite")

print("6. multi_superficie: firma retro-compatible + passthrough bifacial")
from calculos.multi_superficie import calcular_poa_todas  # noqa: E402
sup = [{"nombre": "Techo", "tilt_deg": 10, "azimuth_deg": 180, "area_m2": 100, "activa": True}]
r_old = calcular_poa_todas(sup, tmy, LAT, LON, ALT)              # firma antigua
r_bif = calcular_poa_todas(sup, tmy, LAT, LON, ALT, bifacial=cfg)
check(not r_old["Techo"].empty and "poa_rear" not in r_old["Techo"].columns,
      "firma antigua sigue funcionando (monofacial)")
check("poa_rear" in r_bif["Techo"].columns and
      r_bif["Techo"]["poa_global"].sum() > r_old["Techo"]["poa_global"].sum(),
      "passthrough bifacial aumenta la POA de la superficie")

print()
if fallos:
    print(f"🔴 {len(fallos)} verificación(es) fallaron")
    sys.exit(1)
print("🟢 Modelo bifacial verificado — integración limpia con el flujo existente")
