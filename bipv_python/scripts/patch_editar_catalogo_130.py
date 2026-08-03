#!/usr/bin/env python3
"""
patch_editar_catalogo_130.py — Editar/eliminar paneles del catálogo desde la app (#130).

Qué hace:
  1. Verifica que los archivos actualizados existen y tienen el tamaño correcto
  2. Confirma que eliminar_panel_excel y actualizar_panel_excel están presentes
  3. Imprime instrucciones finales

No instala dependencias nuevas (usa openpyxl ya disponible).

Uso:
  python3 bipv_python/scripts/patch_editar_catalogo_130.py
"""

import sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIPV = ROOT / "bipv_python"
VENV = BIPV / "venv"
PY   = VENV / "bin" / "python3"

OK  = "[OK]"
ERR = "[ERR]"

# ── 1. Verificar archivos ─────────────────────────────────────────────────────
print("\n[1] Verificando archivos actualizados…")

checks = {
    BIPV / "datos"  / "catalogo_paneles_excel.py": ("eliminar_panel_excel", "actualizar_panel_excel"),
    BIPV / "pages"  / "14_📋_Catálogo_PDF.py":     ("tab_editar", "data_editor", "eliminar_panel_excel"),
}

all_ok = True
for path, tokens in checks.items():
    if not path.exists():
        print(f"{ERR} No se encontró: {path.name}")
        all_ok = False
        continue
    content = path.read_text(encoding="utf-8")
    missing = [t for t in tokens if t not in content]
    if missing:
        print(f"{ERR} {path.name} — faltan tokens: {missing}")
        all_ok = False
    else:
        print(f"{OK} {path.name} ({path.stat().st_size:,} bytes) — tokens presentes.")

# ── 2. Probar importación ─────────────────────────────────────────────────────
print("\n[2] Probando importación de funciones nuevas…")
test_code = (
    "import sys; sys.path.insert(0, 'bipv_python'); "
    "from datos.catalogo_paneles_excel import eliminar_panel_excel, actualizar_panel_excel; "
    "print('Funciones importadas OK')"
)
r = subprocess.run(
    [str(PY), "-c", test_code],
    cwd=str(ROOT),
    capture_output=True, text=True
)
if r.returncode == 0:
    print(f"{OK} {r.stdout.strip()}")
else:
    print(f"{ERR} Error de importación:\n{r.stderr.strip()}")
    all_ok = False

# ── 3. Resultado ──────────────────────────────────────────────────────────────
print("\n" + "="*60)
if all_ok:
    print("Parche #130 listo.")
else:
    print("Parche #130 completado con advertencias (ver arriba).")
print("Próximo paso:")
print("  pm2 restart streamlit-bipv")
print("\nNueva funcionalidad en pestaña '✏️ Editar / Eliminar':")
print("  • Filtros por marca, tecnología y nombre")
print("  • Tabla editable con st.data_editor")
print("  • Botón 'Guardar cambios editados'")
print("  • Sección para eliminar panel con confirmación")
print("="*60)
