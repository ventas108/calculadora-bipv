"""
Parche #128 — Potencia kWp en título y tooltip del modelo 3D
=============================================================
Modifica pages/9_🗺️_Vista_3D.py en dos puntos:

A) Título del layout Plotly: añade "N módulos · X.XX kWp" en la línea de subtítulo.
   Antes: Ciudad · Orientación · POA mes: X kWh/m²
   Después: Ciudad · Orientación · **24 módulos · 8.64 kWp** · POA mes: X kWh/m²

B) Hovertemplate del Mesh3d de paneles: añade la línea "Potencia: X.XX kWp"
   Antes: Módulos: 24 / 60 posibles | POA mes: X kWh/m²
   Después: Módulos: 24 / 60 posibles | Potencia: 8.64 kWp | POA mes: X kWh/m²
"""
import sys, pathlib, shutil, datetime

TARGET = pathlib.Path(
    "/var/www/bipv/calculadora-bipv/bipv_python/pages/9_🗺️_Vista_3D.py"
)
if not TARGET.exists():
    print(f"[ERROR] No encontrado: {TARGET}"); sys.exit(1)

src = TARGET.read_text(encoding="utf-8")

# ── Idempotencia ──────────────────────────────────────────────────────────────
if "módulos · {round(n_shown * pmax_panel" in src:
    print("[OK] Parche #128 ya aplicado — sin cambios.")
    sys.exit(0)

ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bak = TARGET.with_suffix(f".py.bak_128_{ts}")
shutil.copy2(TARGET, bak)
print(f"[backup] {bak.name}")

# ── PARCHE A — título del layout ──────────────────────────────────────────────
OLD_TITLE = (
    '        title=dict(\n'
    '            text=(f"<b>Modelo 3D — {nombre_proy}</b><br>"\n'
    '                  f"<sub>{ciudad} · {orient_label} · "\n'
    '                  f"POA {mes_nombre}: <b>{poa_mes:.0f} kWh/m²</b></sub>"),\n'
    '            x=0.5, xanchor=\'center\', font=dict(size=14, color=\'white\'),\n'
    '        ),'
)
NEW_TITLE = (
    '        title=dict(\n'
    '            text=(f"<b>Modelo 3D — {nombre_proy}</b><br>"\n'
    '                  f"<sub>{ciudad} · {orient_label} · "\n'
    '                  f"<b>{n_shown} módulos · {round(n_shown * pmax_panel / 1000, 2):.2f} kWp</b> · "\n'
    '                  f"POA {mes_nombre}: {poa_mes:.0f} kWh/m²</sub>"),\n'
    '            x=0.5, xanchor=\'center\', font=dict(size=14, color=\'white\'),\n'
    '        ),'
)

if OLD_TITLE in src:
    src = src.replace(OLD_TITLE, NEW_TITLE, 1)
    print("[✓] A: título Plotly actualizado con módulos + kWp.")
else:
    print("[ADVERTENCIA] A: no se encontró el bloque title=dict exacto. Revisa manualmente.")

# ── PARCHE B — hovertemplate del Mesh3d ───────────────────────────────────────
OLD_HOVER = (
    '            hovertemplate=(\n'
    '                f"<b>Paneles BIPV</b><br>"\n'
    '                f"POA {mes_nombre}: {poa_val:.0f} kWh/m²<br>"\n'
    '                f"Módulos instalados: {n_shown}"\n'
    '                + (f" / {n_capacity} posibles" if n_active < n_capacity else "")\n'
    '                + "<br><extra></extra>"\n'
    '            ),'
)
NEW_HOVER = (
    '            hovertemplate=(\n'
    '                f"<b>Paneles BIPV</b><br>"\n'
    '                f"Módulos: {n_shown}"\n'
    '                + (f" / {n_capacity} posibles" if n_active < n_capacity else "")\n'
    '                + f"<br>Potencia: {round(n_shown * pmax_panel / 1000, 2):.2f} kWp<br>"\n'
    '                f"POA {mes_nombre}: {poa_val:.0f} kWh/m²<br>"\n'
    '                f"<extra></extra>"\n'
    '            ),'
)

if OLD_HOVER in src:
    src = src.replace(OLD_HOVER, NEW_HOVER, 1)
    print("[✓] B: hovertemplate actualizado con Potencia kWp.")
else:
    print("[ADVERTENCIA] B: no se encontró el hovertemplate exacto. Revisa manualmente.")

TARGET.write_text(src, encoding="utf-8")
print(f"\n[✓] Parche #128 aplicado en {TARGET.name}")
print("    pm2 restart streamlit-bipv")
