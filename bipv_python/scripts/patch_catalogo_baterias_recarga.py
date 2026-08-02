#!/usr/bin/env python3
"""Parche #26 — Confirmar que el catálogo de baterías carga correctamente.

Cambios:
  - datos/catalogo_baterias_excel.py:
      + import pathlib
      + excel_mtime() — timestamp del Excel para invalidar caché al cambiar el archivo
      + cargar_catalogo_baterias(_mtime=0.0) — caché auto-invalidante por mtime
      + diagnostico_catalogo(_mtime=0.0) — idem; pasa _mtime al call interno
      + obtener_bateria / lista_baterias — llaman con _mtime=excel_mtime()
  - pages/11_🔋_Baterias_y_Balance.py:
      + Importa excel_mtime as _excel_mtime
      + Botón "🔄 Recargar catálogo" que limpia ambos cachés y relanza st.rerun()
      + Pasa _mtime_bat = _excel_mtime() a cargar_catalogo_baterias y diagnostico_catalogo
  - datos/diagnostico_catalogo_baterias.py:
      + Script CLI reescrito con detección por alias (alineado con #24)
      + Distingue campos críticos / importantes / opcionales
      + Veredicto final con instrucción de botón Recargar

Aplica desde /var/www/bipv/calculadora-bipv/:
    python3 bipv_python/scripts/patch_catalogo_baterias_recarga.py
"""
import pathlib, sys

BASE = pathlib.Path(__file__).resolve().parents[1]  # bipv_python/
ROOT = BASE.parent                                   # calculadora-bipv/


def patch(path: pathlib.Path, old: str, new: str, tag: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        first_line = new.strip().splitlines()[0].strip()
        if first_line in text:
            print(f"[SKIP] {tag} — parece ya aplicado en {path.name}")
        else:
            print(f"[WARN] {tag} — patrón no encontrado en {path.name}. Revisa manualmente.")
        return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[OK]   {tag}")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 1. datos/catalogo_baterias_excel.py
# ─────────────────────────────────────────────────────────────────────────────
CAT = ROOT / "datos" / "catalogo_baterias_excel.py"
if not CAT.exists():
    CAT = BASE / "datos" / "catalogo_baterias_excel.py"

# 1-a. import pathlib
patch(
    CAT,
    "import pandas as pd\nimport streamlit as st",
    "import pathlib\nimport pandas as pd\nimport streamlit as st",
    "catalogo_baterias_excel.py — import pathlib",
)

# 1-b. excel_mtime() después de _SHEETS
patch(
    CAT,
    "# ── Identificadores que confirman que una fila es el header real ──────────\n"
    "_MODELO_ALIASES = {\"modelo\", \"nombre\", \"model\", \"battery model\", \"bateria\"}",
    "# ── Modificación del Excel — usada para invalidar caché automáticamente ──\n"
    "def excel_mtime() -> float:\n"
    "    \"\"\"Timestamp de modificación del Excel; 0.0 si no es accesible.\"\"\"\n"
    "    try:\n"
    "        return pathlib.Path(_EXCEL).stat().st_mtime\n"
    "    except Exception:\n"
    "        return 0.0\n"
    "\n"
    "\n"
    "# ── Identificadores que confirman que una fila es el header real ──────────\n"
    "_MODELO_ALIASES = {\"modelo\", \"nombre\", \"model\", \"battery model\", \"bateria\"}",
    "catalogo_baterias_excel.py — agregar excel_mtime()",
)

# 1-c. _mtime param en cargar_catalogo_baterias
patch(
    CAT,
    "@st.cache_data(ttl=3600)\n"
    "def cargar_catalogo_baterias() -> dict:\n"
    "    \"\"\"\n"
    "    Devuelve dict {nombre: {...}} con los parámetros de cada batería.\n"
    "    Robusto frente a formatos de Excel con título en filas superiores.\n"
    "    \"\"\"",
    "@st.cache_data(ttl=3600)\n"
    "def cargar_catalogo_baterias(_mtime: float = 0.0) -> dict:\n"
    "    \"\"\"Devuelve dict {nombre: {...}} con los parámetros de cada batería.\n"
    "\n"
    "    Args:\n"
    "        _mtime: Pasar excel_mtime() para invalidar caché cuando el archivo cambia.\n"
    "    \"\"\"",
    "catalogo_baterias_excel.py — _mtime param en cargar_catalogo_baterias",
)

# 1-d. obtener_bateria y lista_baterias con mtime
patch(
    CAT,
    "def obtener_bateria(nombre: str) -> dict:\n"
    "    return cargar_catalogo_baterias().get(nombre, {})\n"
    "\n"
    "\n"
    "def lista_baterias() -> list:\n"
    "    return sorted(cargar_catalogo_baterias().keys())",
    "def obtener_bateria(nombre: str) -> dict:\n"
    "    return cargar_catalogo_baterias(_mtime=excel_mtime()).get(nombre, {})\n"
    "\n"
    "\n"
    "def lista_baterias() -> list:\n"
    "    return sorted(cargar_catalogo_baterias(_mtime=excel_mtime()).keys())",
    "catalogo_baterias_excel.py — obtener_bateria/lista_baterias con mtime",
)

# 1-e. _mtime param en diagnostico_catalogo + call interno
patch(
    CAT,
    "def diagnostico_catalogo() -> dict:\n"
    "    \"\"\"\n"
    "    Diagnóstico del catálogo: detecta columnas no reconocidas, modelos incompletos, etc.\n"
    "    Útil para debugging desde la página 11 o desde consola.\n"
    "    \"\"\"",
    "@st.cache_data(ttl=3600)\n"
    "def diagnostico_catalogo(_mtime: float = 0.0) -> dict:\n"
    "    \"\"\"Diagnóstico del catálogo: columnas no reconocidas, modelos incompletos.\n"
    "\n"
    "    Args:\n"
    "        _mtime: Pasar excel_mtime() para invalidar caché al cambiar el archivo.\n"
    "    \"\"\"",
    "catalogo_baterias_excel.py — _mtime param en diagnostico_catalogo",
)

patch(
    CAT,
    "    cat = cargar_catalogo_baterias()\n"
    "    info[\"modelos_cargados\"] = len(cat)",
    "    cat = cargar_catalogo_baterias(_mtime=_mtime)   # usa la misma entrada de caché\n"
    "    info[\"modelos_cargados\"] = len(cat)",
    "catalogo_baterias_excel.py — call interno cargar_catalogo_baterias(_mtime=_mtime)",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. pages/11_🔋_Baterias_y_Balance.py
# ─────────────────────────────────────────────────────────────────────────────
BAT = ROOT / "pages" / "11_🔋_Baterias_y_Balance.py"
if not BAT.exists():
    BAT = BASE / "pages" / "11_🔋_Baterias_y_Balance.py"

# 2-a. Import excel_mtime
patch(
    BAT,
    "from datos.catalogo_baterias_excel import (\n"
    "    cargar_catalogo_baterias,\n"
    "    obtener_bateria,\n"
    "    lista_baterias,\n"
    "    diagnostico_catalogo,\n"
    ")",
    "from datos.catalogo_baterias_excel import (\n"
    "    cargar_catalogo_baterias,\n"
    "    obtener_bateria,\n"
    "    lista_baterias,\n"
    "    diagnostico_catalogo,\n"
    "    excel_mtime as _excel_mtime,\n"
    ")",
    "Baterias_y_Balance.py — import excel_mtime",
)

# 2-b. Botón de recarga + llamadas con mtime
patch(
    BAT,
    "# ══════════════════════════════════════════════════════════════════════════════\n"
    "# B-6 — Dimensionado de baterías\n"
    "# ══════════════════════════════════════════════════════════════════════════════\n"
    "st.header(\"⚡ B-6 — Dimensionado de Baterías\")\n"
    "\n"
    "cat_bat = cargar_catalogo_baterias()\n"
    "tiene_catalogo = len(cat_bat) > 0\n"
    "\n"
    "# ── #26 — Banner de estado de carga del catálogo ─────────────────────────────\n"
    "_diag = diagnostico_catalogo()\n"
    "_hojas_disp = _diag.get(\"hojas_disponibles\", [])\n"
    "_hoja_usada = _diag.get(\"hoja_usada\")",
    "# ══════════════════════════════════════════════════════════════════════════════\n"
    "# B-6 — Dimensionado de baterías\n"
    "# ══════════════════════════════════════════════════════════════════════════════\n"
    "_hdr_col, _btn_col = st.columns([8, 2])\n"
    "with _hdr_col:\n"
    "    st.header(\"⚡ B-6 — Dimensionado de Baterías\")\n"
    "with _btn_col:\n"
    "    st.write(\"\")   # alinear verticalmente con el header\n"
    "    if st.button(\n"
    "        \"🔄 Recargar catálogo\",\n"
    "        help=(\n"
    "            \"Invalida el caché y recarga el catálogo desde el Excel del servidor. \"\n"
    "            \"Úsalo tras agregar o modificar la hoja `Catalogo_Baterias` para confirmar \"\n"
    "            \"los cambios sin reiniciar PM2.\"\n"
    "        ),\n"
    "        use_container_width=True,\n"
    "    ):\n"
    "        cargar_catalogo_baterias.clear()\n"
    "        diagnostico_catalogo.clear()\n"
    "        st.rerun()\n"
    "\n"
    "_mtime_bat = _excel_mtime()\n"
    "cat_bat = cargar_catalogo_baterias(_mtime=_mtime_bat)\n"
    "tiene_catalogo = len(cat_bat) > 0\n"
    "\n"
    "# ── #26 — Banner de estado de carga del catálogo ─────────────────────────────\n"
    "_diag = diagnostico_catalogo(_mtime=_mtime_bat)\n"
    "_hojas_disp = _diag.get(\"hojas_disponibles\", [])\n"
    "_hoja_usada = _diag.get(\"hoja_usada\")",
    "Baterias_y_Balance.py — botón Recargar + mtime en llamadas",
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Reemplazar diagnostico_catalogo_baterias.py con versión actualizada (#24/#26)
# ─────────────────────────────────────────────────────────────────────────────
DIAG_SRC = BASE / "datos" / "diagnostico_catalogo_baterias.py"
DIAG_DEST = ROOT / "datos" / "diagnostico_catalogo_baterias.py"
if not DIAG_DEST.exists():
    DIAG_DEST = DIAG_SRC  # si ya estamos en el mismo directorio
if DIAG_SRC.exists() and DIAG_SRC != DIAG_DEST:
    import shutil
    shutil.copy2(DIAG_SRC, DIAG_DEST)
    print("[OK]   diagnostico_catalogo_baterias.py — copiado desde bipv_python/datos/")
else:
    print("[SKIP] diagnostico_catalogo_baterias.py — ya en su lugar")

print("\n✅ Parche #26 completado. Reinicia el proceso:")
print("   pm2 restart streamlit-bipv")
print("\nPara confirmar que la hoja carga correctamente:")
print("   source bipv_python/venv/bin/activate")
print("   python bipv_python/datos/diagnostico_catalogo_baterias.py")
