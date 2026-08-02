"""
Parche #88 — PDF: mostrar ubicación real del predio, no la ciudad de referencia
==============================================================================
Modifica `pages/10_📄_Reporte_PDF.py`:
  - Añade bloque de detección de ubicación real (municipio + coords del predio)
    justo después de la primera lectura de `ciudad`.
  - Reemplaza la fila "Ciudad / Localización" en tabla_kv con `_localizacion_pdf`
    y `_localizacion_nota` en lugar del string de ciudad de referencia.

Resultado:
  • Si el usuario ingresó coordenadas distintas a las de la ciudad:
      → Muestra "Municipio  (lat°N, lon°O)"  (o solo coords si no hubo geocoding)
      → Nota: "Ciudad de referencia climática TMY: <ciudad>"
  • Si no hay coordenadas personalizadas:
      → Muestra municipio detectado o ciudad de referencia (igual que antes)
      → Nota: "TMY descargado para referencia climática: <ciudad>" (si difieren)
"""
import re, sys, pathlib, shutil, datetime

TARGET = pathlib.Path("/var/www/bipv/calculadora-bipv/bipv_python/pages/10_📄_Reporte_PDF.py")

# ── Verificar existencia ──────────────────────────────────────────────────────
if not TARGET.exists():
    print(f"[ERROR] No se encontró: {TARGET}")
    sys.exit(1)

src = TARGET.read_text(encoding="utf-8")

# ── Idempotencia ──────────────────────────────────────────────────────────────
if "tarea #88" in src:
    print("[OK] El parche #88 ya estaba aplicado — no se modifica nada.")
    sys.exit(0)

# ── Backup ────────────────────────────────────────────────────────────────────
ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bak = TARGET.with_suffix(f".py.bak_88_{ts}")
shutil.copy2(TARGET, bak)
print(f"[backup] {bak}")

# ═══════════════════════════════════════════════════════════════════════════════
# PARCHE 1 — Insertar bloque de detección de ubicación real después de la
#            primera lectura de "ciudad" en generar_html_reporte()
# ═══════════════════════════════════════════════════════════════════════════════
OLD_CIUDAD_LINE = (
    "    ciudad          = st.session_state.get(\"tmy_ciudad\", "
    "st.session_state.get(\"ciudad\", \"—\"))\n"
)
NEW_CIUDAD_BLOCK = (
    "    ciudad          = st.session_state.get(\"tmy_ciudad\", "
    "st.session_state.get(\"ciudad\", \"—\"))\n"
    "    # ── Localización real del predio (tarea #88) ──────────────────────────────\n"
    "    _ciudad_ref     = st.session_state.get(\"ciudad\", \"—\")\n"
    "    _lat_pdf        = st.session_state.get(\"lat_proyecto\")\n"
    "    _lon_pdf        = st.session_state.get(\"lon_proyecto\")\n"
    "    _municipio_pdf  = st.session_state.get(\"municipio_predio\", \"\")\n"
    "    from datos.ciudades_colombia import CIUDADES as _CIUDADES_PDF\n"
    "    _c_ref_data     = _CIUDADES_PDF.get(_ciudad_ref, {})\n"
    "    _coord_es_predio = (\n"
    "        _lat_pdf is not None and _c_ref_data and\n"
    "        abs(float(_lat_pdf) - _c_ref_data.get(\"lat\", 0)) > 0.001\n"
    "    )\n"
    "    if _coord_es_predio:\n"
    "        if _municipio_pdf:\n"
    "            _localizacion_pdf  = f\"{_municipio_pdf}  ({float(_lat_pdf):.4f}°N, {abs(float(_lon_pdf)):.4f}°O)\"\n"
    "        else:\n"
    "            _localizacion_pdf  = f\"Predio: {float(_lat_pdf):.5f}°N, {float(_lon_pdf):.5f}°O\"\n"
    "        _localizacion_nota = f\"Ciudad de referencia climática TMY: {_ciudad_ref}\"\n"
    "    else:\n"
    "        # Sin coordenadas personalizadas: usar municipio detectado > ciudad de referencia > tmy_ciudad\n"
    "        _localizacion_pdf  = _municipio_pdf if _municipio_pdf else _ciudad_ref\n"
    "        _localizacion_nota = (\n"
    "            f\"TMY descargado para referencia climática: {ciudad}\"\n"
    "            if ciudad != _ciudad_ref\n"
    "            else \"Clima extraído de base TMY/PVGIS\"\n"
    "        )\n"
)

if OLD_CIUDAD_LINE not in src:
    print("[ERROR] No se encontró la línea ancla de ciudad en generar_html_reporte(). "
          "Verifica si el archivo del servidor ya tiene una versión distinta.")
    sys.exit(1)

src = src.replace(OLD_CIUDAD_LINE, NEW_CIUDAD_BLOCK, 1)
print("[PARCHE 1] Bloque de localización real insertado.")

# ═══════════════════════════════════════════════════════════════════════════════
# PARCHE 2 — Reemplazar la fila "Ciudad / Localización" en tabla_kv
#            (busca el patrón más probable del archivo original en el servidor)
# ═══════════════════════════════════════════════════════════════════════════════
# Hay varias formas en que podría aparecer; probamos de más específica a menos.
PATRONES_CIUDAD_ROW = [
    # Con ciudad directa
    '        ("Ciudad / Localización", ciudad,              "",         ""),\n',
    '        ("Ciudad / Localización", ciudad,              "",  ""),\n',
    '        ("Ciudad / Localización", ciudad, "", ""),\n',
    '        ("Ciudad / Localización", str(ciudad),         "",         ""),\n',
    # Con f-string
    '        ("Ciudad / Localización", f"{ciudad}",         "",         ""),\n',
]

NUEVA_FILA = (
    '        ("Ciudad / Localización", _localizacion_pdf,         "",         _localizacion_nota),\n'
)

reemplazado = False
for patron in PATRONES_CIUDAD_ROW:
    if patron in src:
        src = src.replace(patron, NUEVA_FILA, 1)
        print(f"[PARCHE 2] Fila 'Ciudad / Localización' actualizada (patrón: {repr(patron[:60])}...)")
        reemplazado = True
        break

if not reemplazado:
    # Búsqueda flexible con regex como fallback
    match = re.search(
        r'(\s*\("Ciudad / Localización",\s*)([^,\n]+)(,\s*"",\s*""\),)',
        src
    )
    if match:
        old_row = match.group(0)
        new_row = '        ("Ciudad / Localización", _localizacion_pdf,         "",         _localizacion_nota),'
        src = src.replace(old_row, new_row, 1)
        print(f"[PARCHE 2] Fila actualizada vía regex fallback.")
        reemplazado = True
    else:
        print("[ADVERTENCIA] No se encontró la fila 'Ciudad / Localización' para actualizar.")
        print("  Verifica manualmente que tabla_kv use `_localizacion_pdf` y `_localizacion_nota`.")

# ── Escribir ──────────────────────────────────────────────────────────────────
TARGET.write_text(src, encoding="utf-8")
print(f"\n[✓] Parche #88 aplicado exitosamente en:\n    {TARGET}")
print("\nPróximo paso: pm2 restart streamlit-bipv")
