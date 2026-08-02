"""
Parche #124 — Guía de pasos pendientes al retomar un proyecto guardado
=======================================================================
Modifica pages/1_🏠_Proyecto.py:

A) Al hacer clic en "📂 Cargar", almacena _proyecto_recien_cargado=True
   en session_state ANTES del st.rerun().

B) Justo después del expander "Mis Proyectos" y antes de los widgets del
   formulario, muestra un banner INFO con los pasos que faltan:
     ☀️ Recurso Solar → 📊 Producción → 💰 Financiero
   El banner se adapta al estado: si ya están todos listos, se limpia solo.
   Botón "✕" permite descartarlo manualmente.

Resultado visible:
  Tras cargar "Torre Medellín" aparece:
    ℹ️ Proyecto cargado. Para activar todos los módulos,
       re-ejecuta en orden: ☀️ Recurso Solar → 📊 Producción → 💰 Financiero
       [✕]
  Al completar Producción y Financiero el banner desaparece solo.
"""
import sys, pathlib, shutil, datetime, re

TARGET = pathlib.Path(
    "/var/www/bipv/calculadora-bipv/bipv_python/pages/1_🏠_Proyecto.py"
)
if not TARGET.exists():
    print(f"[ERROR] No encontrado: {TARGET}"); sys.exit(1)

src = TARGET.read_text(encoding="utf-8")

# ── Idempotencia ──────────────────────────────────────────────────────────────
if "_proyecto_recien_cargado" in src:
    print("[OK] Parche #124 ya aplicado — sin cambios.")
    sys.exit(0)

ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bak = TARGET.with_suffix(f".py.bak_124_{ts}")
shutil.copy2(TARGET, bak)
print(f"[backup] {bak.name}")

# ── PARCHE A — marcar flag al cargar ─────────────────────────────────────────
OLD_CARGAR = (
    '                    _nombre_cargado = cargar_proyecto(_p["slug"])\n'
    '                    st.success(f"✅ Proyecto «{_nombre_cargado}» cargado. Revisa los datos abajo.")\n'
    '                    st.rerun()\n'
)
NEW_CARGAR = (
    '                    _nombre_cargado = cargar_proyecto(_p["slug"])\n'
    '                    st.session_state["_proyecto_recien_cargado"] = True\n'
    '                    st.rerun()\n'
)

if OLD_CARGAR in src:
    src = src.replace(OLD_CARGAR, NEW_CARGAR, 1)
    print("[✓] A: flag _proyecto_recien_cargado añadido al botón Cargar.")
else:
    # Fallback: buscar línea con cargar_proyecto + rerun
    m = re.search(
        r'(_nombre_cargado = cargar_proyecto\([^\n]+\n)'
        r'(\s+st\.(?:success|rerun)\([^\n]+\n)'
        r'(\s+st\.rerun\(\)\n)',
        src
    )
    if m:
        old = m.group(0)
        new = (m.group(1)
               + '                    st.session_state["_proyecto_recien_cargado"] = True\n'
               + m.group(3))
        src = src.replace(old, new, 1)
        print("[✓] A: flag añadido (regex fallback).")
    else:
        print("[ADVERTENCIA] A: no se encontró el bloque cargar_proyecto. Revisa manualmente.")

# ── PARCHE B — insertar banner de pasos pendientes ───────────────────────────
OLD_TIPOS = "# ── Tipos de instalación con defaults técnicos ────────────────────────────────\nTIPOS_INSTALACION = {"
NEW_TIPOS = """\
# ── Banner de pasos pendientes tras cargar un proyecto (#124) ────────────────
if st.session_state.get("_proyecto_recien_cargado"):
    _pasos = []
    if not st.session_state.get("recurso_solar_ok"):
        _pasos.append("☀️ **Recurso Solar**")
    if not st.session_state.get("produccion_ok"):
        _pasos.append("📊 **Producción**")
    if not st.session_state.get("financiero_ok"):
        _pasos.append("💰 **Financiero**")

    if _pasos:
        _col_banner, _col_x = st.columns([10, 1])
        _col_banner.info(
            f"📂 **Proyecto cargado.** Para activar todos los módulos, "
            f"re-ejecuta en orden: {' → '.join(_pasos)}"
        )
        if _col_x.button("✕", key="_pm_dismiss_banner", help="Descartar aviso"):
            st.session_state.pop("_proyecto_recien_cargado", None)
            st.rerun()
    else:
        st.session_state.pop("_proyecto_recien_cargado", None)

# ── Tipos de instalación con defaults técnicos ────────────────────────────────
TIPOS_INSTALACION = {"""

if OLD_TIPOS in src:
    src = src.replace(OLD_TIPOS, NEW_TIPOS, 1)
    print("[✓] B: banner de pasos pendientes insertado.")
else:
    print("[ADVERTENCIA] B: no se encontró el ancla TIPOS_INSTALACION. Revisa manualmente.")

TARGET.write_text(src, encoding="utf-8")
print(f"\n[✓] Parche #124 aplicado en {TARGET.name}")
print("    pm2 restart streamlit-bipv")
