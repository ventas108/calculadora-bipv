"""
Parche #35 — Usar producción corregida por bypass en rentabilidad financiera
=============================================================================
Modifica DOS archivos:

A) pages/6_📊_Produccion.py  — Balance energético
   Al final del bloque `if _bypass_ok and kwh_bypass > 0:` escribe dos claves
   nuevas en session_state:
     • E_ac_anual_kWh_bypass  (E_ac base - pérdida bypass en AC)
     • kwh_bypass_anual        (pérdida DC para mostrarla en Financiero)

B) pages/7_💰_Financiero.py  — Selección de E_ac
   Reemplaza la lectura directa de E_ac_anual_kWh por un bloque de prioridad:
       multi-superficie > bypass > base
   Añade banners informativos que explican qué producción se usó y cuánto
   corrigió el bypass.

Resultado:
  • Si se ejecutó Mismatch Bypass → Producción (en ese orden):
      → Financiero usa E_ac_anual_kWh_bypass automáticamente.
      → Banner "⚡ Corrección bypass diodes aplicada" con delta kWh/año.
  • Si solo hay producción base:
      → Comportamiento idéntico al anterior; caption sugiere ejecutar Bypass.
  • Multi-superficie tiene prioridad sobre ambas (sin cambio de comportamiento).
"""
import sys, pathlib, shutil, datetime, re

BASE = pathlib.Path("/var/www/bipv/calculadora-bipv/bipv_python")
PROD_FILE = BASE / "pages" / "6_📊_Produccion.py"
FIN_FILE  = BASE / "pages" / "7_💰_Financiero.py"

def backup(p: pathlib.Path, tag: str) -> pathlib.Path:
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = p.with_suffix(f".py.bak_{tag}_{ts}")
    shutil.copy2(p, bak)
    print(f"  [backup] {bak.name}")
    return bak

# ─────────────────────────────────────────────────────────────────────────────
# Verificar archivos
# ─────────────────────────────────────────────────────────────────────────────
for f in [PROD_FILE, FIN_FILE]:
    if not f.exists():
        print(f"[ERROR] No encontrado: {f}")
        sys.exit(1)

prod_src = PROD_FILE.read_text(encoding="utf-8")
fin_src  = FIN_FILE.read_text(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# PARCHE A — pages/6_📊_Produccion.py
#   Añadir escritura de E_ac_anual_kWh_bypass en el bloque bypass
# ─────────────────────────────────────────────────────────────────────────────
print("\n[A] Produccion.py — escribir E_ac_anual_kWh_bypass en session_state")

if "E_ac_anual_kWh_bypass" in prod_src:
    print("  [OK] Ya contiene E_ac_anual_kWh_bypass — sin cambios.")
    prod_changed = False
else:
    # Ancla: el st.info() del bloque bypass en el balance energético.
    # La línea final del info es siempre f"(vs {res['E_ac_anual_kWh']:,.0f} sin bypass)"
    # Añadimos las dos líneas de session_state inmediatamente después.
    OLD_BYPASS_INFO = (
        '            f"(vs {res[\'E_ac_anual_kWh\']:,.0f} sin bypass)"\n'
        '        )\n'
    )
    NEW_BYPASS_INFO = (
        '            f"(vs {res[\'E_ac_anual_kWh\']:,.0f} sin bypass)"\n'
        '        )\n'
        '        # Actualizar E_ac con corrección bypass para páginas financieras\n'
        '        st.session_state["E_ac_anual_kWh_bypass"] = round(e_ac_corr, 0)\n'
        '        st.session_state["kwh_bypass_anual"]       = round(kwh_bypass, 1)\n'
    )

    if OLD_BYPASS_INFO in prod_src:
        backup(PROD_FILE, "35A")
        prod_src = prod_src.replace(OLD_BYPASS_INFO, NEW_BYPASS_INFO, 1)
        PROD_FILE.write_text(prod_src, encoding="utf-8")
        print("  [✓] Escritura de E_ac_anual_kWh_bypass añadida.")
        prod_changed = True
    else:
        # Fallback: buscar cierre del if bypass en balance con regex
        # Buscamos el bloque completo del st.info() dentro de `if _bypass_ok and kwh_bypass > 0:`
        m = re.search(
            r'(        st\.info\(\s*\n.*?sin bypass[^\n]*\n\s*\)\s*\n)',
            prod_src, re.DOTALL
        )
        if m:
            old_block = m.group(1)
            new_block = (
                old_block
                + '        # Actualizar E_ac con corrección bypass para páginas financieras\n'
                + '        st.session_state["E_ac_anual_kWh_bypass"] = round(e_ac_corr, 0)\n'
                + '        st.session_state["kwh_bypass_anual"]       = round(kwh_bypass, 1)\n'
            )
            backup(PROD_FILE, "35A")
            prod_src = prod_src.replace(old_block, new_block, 1)
            PROD_FILE.write_text(prod_src, encoding="utf-8")
            print("  [✓] Escritura añadida vía regex fallback.")
            prod_changed = True
        else:
            print("  [ADVERTENCIA] No se encontró el ancla en Produccion.py.")
            print("    Añade manualmente tras el st.info() del bloque bypass:")
            print('        st.session_state["E_ac_anual_kWh_bypass"] = round(e_ac_corr, 0)')
            print('        st.session_state["kwh_bypass_anual"]       = round(kwh_bypass, 1)')
            prod_changed = False

# ─────────────────────────────────────────────────────────────────────────────
# PARCHE B — pages/7_💰_Financiero.py
#   Reemplazar `e_ac = st.session_state.get("E_ac_anual_kWh", 0.0)` por el
#   bloque completo de prioridad multi-superficie > bypass > base,
#   y el banner de éxito por la versión que muestra qué producción se usó.
# ─────────────────────────────────────────────────────────────────────────────
print("\n[B] Financiero.py — bloque de prioridad E_ac y banners informativos")

if "Prioridad E_ac: multi-superficie > bypass > base" in fin_src:
    print("  [OK] Ya contiene bloque de prioridad — sin cambios.")
    fin_changed = False
else:
    backup(FIN_FILE, "35B")
    fin_changed = True

    # ── B1: Reemplazar línea simple `e_ac = ...` por bloque de prioridad ────
    # Buscamos la línea simple que sigue a la definición de `ciudad` en la zona
    # de carga de datos inicial. Puede tener varias formas:
    PATRONES_E_AC_SIMPLE = [
        (
            'ciudad  = (st.session_state.get("municipio_predio")\n'
            '           or st.session_state.get("tmy_ciudad", "Bogotá"))\n'
            '\n'
            'e_ac    = float(st.session_state.get("E_ac_anual_kWh", 0.0))\n',
        ),
        (
            'ciudad  = (st.session_state.get("municipio_predio")\n'
            '           or st.session_state.get("tmy_ciudad", "Bogotá"))\n'
            '\n'
            'e_ac = float(st.session_state.get("E_ac_anual_kWh", 0.0))\n',
        ),
        (
            'ciudad  = (st.session_state.get("municipio_predio")\n'
            '           or st.session_state.get("tmy_ciudad", "Bogotá"))\n'
            '\n'
            'e_ac = st.session_state.get("E_ac_anual_kWh", 0.0)\n',
        ),
        (
            'ciudad  = (st.session_state.get("municipio_predio")\n'
            '           or st.session_state.get("tmy_ciudad", "Bogotá"))\n'
            'e_ac    = float(st.session_state.get("E_ac_anual_kWh", 0.0))\n',
        ),
        (
            'ciudad  = (st.session_state.get("municipio_predio")\n'
            '           or st.session_state.get("tmy_ciudad", "Bogotá"))\n'
            'e_ac = st.session_state.get("E_ac_anual_kWh", 0.0)\n',
        ),
    ]

    NUEVO_BLOQUE_PRIORIDAD = '''\
ciudad  = (st.session_state.get("municipio_predio")
           or st.session_state.get("tmy_ciudad", "Bogotá"))

# ── Prioridad E_ac: multi-superficie > bypass > base ─────────────────────────
# Claves exclusivas — nunca se sobreescriben entre sí
_e_ac_base     = st.session_state.get("E_ac_anual_kWh", 0.0)
_e_ac_bypass   = st.session_state.get("E_ac_anual_kWh_bypass", 0.0)
_e_ac_multisup = st.session_state.get("E_ac_anual_kWh_multisup", 0.0)
_bypass_ok     = st.session_state.get("bypass_ok", False)
_kwh_bypass    = st.session_state.get("kwh_bypass_anual", 0.0)
_multisup_ok   = st.session_state.get("multisup_activo", False)
_area_multisup = st.session_state.get("area_total_multisup", 0.0)
_desglose_ms   = st.session_state.get("multisup_desglose", [])
_n_sups        = len(_desglose_ms)

if _multisup_ok and _e_ac_multisup > 0:
    e_ac = _e_ac_multisup
elif _bypass_ok and _e_ac_bypass > 0:
    e_ac = _e_ac_bypass
else:
    e_ac = _e_ac_base
'''

    replaced_b1 = False
    for (patron,) in PATRONES_E_AC_SIMPLE:
        if patron in fin_src:
            fin_src = fin_src.replace(patron, NUEVO_BLOQUE_PRIORIDAD, 1)
            print("  [✓] B1: bloque de prioridad insertado.")
            replaced_b1 = True
            break

    if not replaced_b1:
        # Regex fallback: busca asignación e_ac simple después de ciudad =
        m = re.search(
            r'(ciudad\s*=\s*\(st\.session_state\.get\("municipio_predio"\)[^\n]*\n'
            r'\s+or st\.session_state\.get\("tmy_ciudad"[^\n]*\)\)\n)'
            r'(\n?)'
            r'(e_ac\s*=\s*(?:float\()?st\.session_state\.get\("E_ac_anual_kWh"[^\n]+\n)',
            fin_src
        )
        if m:
            old_section = m.group(0)
            fin_src = fin_src.replace(old_section, NUEVO_BLOQUE_PRIORIDAD, 1)
            print("  [✓] B1: bloque insertado vía regex fallback.")
            replaced_b1 = True
        else:
            print("  [ADVERTENCIA] B1: no se encontró la asignación simple de e_ac.")
            print("    El archivo del servidor puede tener una estructura diferente.")

    # ── B2: Reemplazar st.success() simple por banners por caso ─────────────
    # Buscamos el st.success() genérico que existía antes (sin mención de bypass)
    OLD_SUCCESS_SIMPLE_PATTERNS = [
        (
            'if prod_ok and e_ac > 0:\n'
            '    st.success(\n'
            '        f"✅ Producción cargada — **{e_ac:,.0f} kWh/año** | "\n'
            '        f"Sistema: **{p_stc:.2f} kWp** ({n_pan} módulos) | Ciudad: **{ciudad}**"\n'
            '    )\n',
        ),
        (
            'if prod_ok and e_ac > 0:\n'
            '    st.success(\n'
            '        f"✅ Producción cargada — **{e_ac:,.0f} kWh/año** |"\n'
            '        f" Sistema: **{p_stc:.2f} kWp** ({n_pan} módulos) | Ciudad: **{ciudad}**"\n'
            '    )\n',
        ),
    ]

    NUEVO_SUCCESS_BLOQUE = '''\
if prod_ok and e_ac > 0:
    if _multisup_ok and _e_ac_multisup > 0:
        st.success(
            f"✅ Sistema multi-superficie — **{e_ac:,.0f} kWh/año** | "
            f"{_n_sups} superficie(s) · Área total: **{_area_multisup:.1f} m²** | Ciudad: **{ciudad}**"
        )
        st.info(
            f"🏗️ **Modo multi-superficie activo:** TIR y Payback calculados con la suma "
            f"de todas las superficies BIPV definidas en 🗺️ Vista 3D. "
            f"Producción superficie principal: {_e_ac_base:,.0f} kWh/año."
        )
        if _desglose_ms:
            import pandas as _pd_fin
            _df_des = _pd_fin.DataFrame([
                {"Superficie": d["nombre"], "Tipo": d["tipo"],
                 "Área (m²)": f"{d['area_m2']:.1f}",
                 "POA (kWh/m²/año)": f"{d['poa_kWh_m2']:.0f}",
                 "E_ac (kWh/año)": f"{d['e_ac_kWh']:,.0f}"}
                for d in _desglose_ms
            ])
            with st.expander("📋 Desglose por superficie"):
                st.dataframe(_df_des, use_container_width=True, hide_index=True)
    elif _bypass_ok and _e_ac_bypass > 0:
        st.success(
            f"✅ Producción con corrección bypass — **{e_ac:,.0f} kWh/año** | "
            f"Sistema: **{p_stc:.2f} kWp** ({n_pan} módulos) | Ciudad: **{ciudad}**"
        )
        st.info(
            f"⚡ **Corrección bypass diodes aplicada:** "
            f"E_ac base = {_e_ac_base:,.0f} kWh/año → "
            f"pérdida bypass = {_kwh_bypass:,.0f} kWh/año → "
            f"**E_ac neta = {e_ac:,.0f} kWh/año** "
            f"({(_e_ac_base - e_ac) / _e_ac_base * 100:.1f}% menos). "
            "TIR y Payback calculados con la producción real corregida."
        )
    else:
        st.success(
            f"✅ Producción cargada — **{e_ac:,.0f} kWh/año** | "
            f"Sistema: **{p_stc:.2f} kWp** ({n_pan} módulos) | Ciudad: **{ciudad}**"
        )
        if prod_ok:
            st.caption(
                "💡 Ejecuta el modelo Bypass Diodes en Página 5 (Sección 5) para usar "
                "la E_ac corregida por sombra parcial en este análisis financiero."
            )
'''

    replaced_b2 = False
    for (patron,) in OLD_SUCCESS_SIMPLE_PATTERNS:
        if patron in fin_src:
            fin_src = fin_src.replace(patron, NUEVO_SUCCESS_BLOQUE, 1)
            print("  [✓] B2: banners informativos por caso insertados.")
            replaced_b2 = True
            break

    if not replaced_b2:
        print("  [INFO] B2: no se encontró el st.success() simple original.")
        print("    Si el archivo ya tenía banners por caso, puede estar bien.")

    FIN_FILE.write_text(fin_src, encoding="utf-8")
    print(f"  [✓] Financiero.py guardado.")

# ─────────────────────────────────────────────────────────────────────────────
# Resumen
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
if prod_changed or fin_changed:
    print("[✓] Parche #35 aplicado exitosamente.")
    print("\nPróximo paso:")
    print("  pm2 restart streamlit-bipv")
    print("\nVerificación rápida:")
    print("  1. Ejecuta Mismatch → sección Bypass Diodes")
    print("  2. Ejecuta Producción → verifica 'E_ac con bypass' en caption")
    print("  3. Navega a Financiero → debe mostrar banner '⚡ Corrección bypass'")
else:
    print("[OK] Parche ya estaba aplicado o no hubo cambios necesarios.")
