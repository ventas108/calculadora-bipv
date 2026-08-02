"""
Parche B-5A/B/C — Vista 3D del edificio
========================================
Despliega dos archivos al servidor:

A) calculos/multi_superficie.py  (364 líneas)
   Módulo de soporte para instalaciones BIPV multi-superficie:
   • Tipos: Fachada, Techo, Pérgola, Marquesina
   • calcular_poa_superficie()  — POA por inclinación y azimuth via pvlib
   • calcular_poa_todas()       — batch para lista de superficies
   • produccion_superficie()    — E_ac por superficie con PR y degradación
   • mapear_fachadas_csv()      — alinea FS del CSV de Mismatch por superficie
   • fs_mensual_por_superficie()— factor de sombra mensual por superficie
   • e_ac_total_multisup()      — suma de producción de todas las superficies
   • color_tipo/poa/fs()        — helpers de color para visualización

B) pages/9_🗺️_Vista_3D.py  (1 827 líneas)
   Página completa con tres tabs:
   • 🗺️ Mapa del Sitio (B-5A) — edificio extruido en mapa Pydeck/Carto,
     polígono georreferenciado, flecha de orientación, capa de fachada
   • 🏗️ Modelo 3D con Paneles (B-5B) — volumen Plotly Mesh3d, cuadrícula
     de paneles coloreada por POA mensual, rayo solar, comparación mensual
   • 🌞 Diagrama Solar (B-5C) — 4 sub-tabs:
       1. Gestor de superficies BIPV múltiples
       2. Vista 3D multi-superficie (Plotly)
       3. Producción por superficie (barras apiladas + bypass individual)
       4. Trayectoria solar (diagrama polar, heatmap productividad,
          horizonte de obstáculos, comparación con factor de sombra Mismatch)

Dependencias ya en servidor: pvlib, pydeck, plotly, calculos/solar.py,
calculos/tz_utils.py, calculos/mismatch_bypass.py, datos/ciudades_colombia.py
"""
import sys, pathlib, shutil, datetime, textwrap

BASE = pathlib.Path("/var/www/bipv/calculadora-bipv/bipv_python")

# ── Paths destino ─────────────────────────────────────────────────────────────
DST_MULTISUP = BASE / "calculos" / "multi_superficie.py"
DST_VISTA3D  = BASE / "pages"   / "9_🗺️_Vista_3D.py"

# ── Paths fuente en Replit (mismo repo, directorio relativo al script) ────────
# El script corre EN el servidor, por lo que los fuentes se incrustan en él.
# Se generan con textwrap.dedent desde strings literales; ver partes A y B.

def backup(p: pathlib.Path, tag: str):
    if p.exists():
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = p.with_suffix(f".py.bak_{tag}_{ts}")
        shutil.copy2(p, bak)
        print(f"  [backup] {bak.name}")

for f in [BASE / "calculos", BASE / "pages"]:
    if not f.exists():
        print(f"[ERROR] Directorio no encontrado: {f}")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# PARTE A — calculos/multi_superficie.py
# ══════════════════════════════════════════════════════════════════════════════
print("\n[A] Desplegando calculos/multi_superficie.py")

# Leer fuente desde el repositorio Replit (mismo árbol de archivos)
_script_dir = pathlib.Path(__file__).parent          # bipv_python/scripts/
_src_multisup = _script_dir.parent / "calculos" / "multi_superficie.py"

if not _src_multisup.exists():
    print(f"  [ERROR] Fuente no encontrada: {_src_multisup}")
    sys.exit(1)

backup(DST_MULTISUP, "B5A")

shutil.copy2(_src_multisup, DST_MULTISUP)
print(f"  [✓] multi_superficie.py copiado ({_src_multisup.stat().st_size:,} bytes)")

# ══════════════════════════════════════════════════════════════════════════════
# PARTE B — pages/9_🗺️_Vista_3D.py
# ══════════════════════════════════════════════════════════════════════════════
print("\n[B] Desplegando pages/9_🗺️_Vista_3D.py")

_src_vista3d = _script_dir.parent / "pages" / "9_🗺️_Vista_3D.py"

if not _src_vista3d.exists():
    print(f"  [ERROR] Fuente no encontrada: {_src_vista3d}")
    sys.exit(1)

backup(DST_VISTA3D, "B5B")

shutil.copy2(_src_vista3d, DST_VISTA3D)
print(f"  [✓] 9_🗺️_Vista_3D.py copiado ({_src_vista3d.stat().st_size:,} bytes)")

# ── Verificar dependencias del módulo ──────────────────────────────────────────
print("\n[C] Verificando dependencias...")
_deps = [
    BASE / "calculos" / "solar.py",
    BASE / "calculos" / "tz_utils.py",
    BASE / "calculos" / "mismatch_bypass.py",
    BASE / "datos"    / "ciudades_colombia.py",
]
all_ok = True
for dep in _deps:
    if dep.exists():
        print(f"  [✓] {dep.name}")
    else:
        print(f"  [⚠] FALTA: {dep}  ← requerido por Vista 3D")
        all_ok = False

# Verificar pydeck en el entorno Python
try:
    import pydeck  # noqa: F401
    print("  [✓] pydeck disponible")
except ImportError:
    print("  [⚠] pydeck NO instalado — Tab 'Mapa del Sitio' mostrará aviso")
    print("       Para instalar: pip install pydeck")

# ── Resumen ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if all_ok:
    print("[✓] Parche B-5A/B/C aplicado exitosamente.")
else:
    print("[⚠] Parche aplicado con advertencias — revisar dependencias faltantes.")

print("""
Próximo paso:
  pm2 restart streamlit-bipv

Verificación (una vez reiniciado):
  1. Navega a 🗺️ Vista 3D en el menú lateral
  2. Tab "🗺️ Mapa del Sitio"    → edificio extruido en mapa satelital
  3. Tab "🏗️ Modelo 3D"         → volumen Plotly + paneles coloreados por POA
  4. Tab "🌞 Diagrama Solar"     → gestor multi-sup + trayectoria solar
     Subtab "Trayectoria solar" requiere TMY (ejecutar ☀️ Recurso Solar primero)

Funcionalidad por tab:
  B-5A Mapa:       Pydeck → edificio, fachada, orientación, tooltip de área
  B-5B Modelo 3D:  Plotly → volumen + cuadrícula paneles + rayo solar mensual
  B-5C Diagrama:   Multi-sup BIPV + producción por superficie + heatmap solar
""")
