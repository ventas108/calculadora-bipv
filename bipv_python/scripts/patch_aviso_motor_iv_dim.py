"""
Parche #118 — Avisar en Dimensionamiento cuando el panel no puede simularse en Motor IV
========================================================================================
Aplica tres cambios coordinados:

A) Crea calculos/panel_iv_check.py con analizar_panel_motiv() — función
   compartida extraída de Motor IV. Detecta si un panel tiene Voc, Isc,
   Vmp, Imp para el modelo SDM De Soto. Devuelve (errores, advertencias).

B) pages/3_🔬_Motor_IV.py — importa analizar_panel_motiv desde el módulo
   compartido y elimina la definición local duplicada.

C) pages/4_📐_Dimensionamiento.py — importa el helper y muestra:
   • st.warning si faltan campos críticos (Voc/Isc/Vmp/Imp)
   • st.info si solo faltan opcionales (N_s, coefs. temp.)
   El aviso aparece inmediatamente después de cargar el panel seleccionado.
"""
import sys, pathlib, shutil, datetime, textwrap

BASE     = pathlib.Path("/var/www/bipv/calculadora-bipv/bipv_python")
F_CHECK  = BASE / "calculos" / "panel_iv_check.py"
F_MOTIV  = BASE / "pages" / "3_🔬_Motor_IV.py"
F_DIM    = BASE / "pages" / "4_📐_Dimensionamiento.py"

for f in [F_MOTIV, F_DIM]:
    if not f.exists():
        print(f"[ERROR] No encontrado: {f}"); sys.exit(1)

def backup(path, tag):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.with_suffix(f".py.bak_{tag}_{ts}")
    shutil.copy2(path, bak)
    return bak

# ── A: crear módulo compartido ────────────────────────────────────────────────
print("\n[A] Creando calculos/panel_iv_check.py...")
if F_CHECK.exists() and "analizar_panel_motiv" in F_CHECK.read_text(encoding="utf-8"):
    print("  [OK] Ya existe — sin cambios.")
else:
    F_CHECK.write_text(textwrap.dedent("""\
        \"\"\"
        panel_iv_check.py — Validación de datos IV para Motor IV (SDM De Soto).
        Módulo compartido usado por Dimensionamiento y Motor IV.
        \"\"\"
        from calculos.modelo_iv import verificar_ns_halfcut


        def analizar_panel_motiv(p: dict) -> tuple:
            \"\"\"
            Analiza si un panel tiene los datos necesarios para el Motor IV.
            Retorna (errores, advertencias) donde errores bloquean la simulación.
            \"\"\"
            _val = lambda *keys: any(
                p.get(k) not in (None, 0, 0.0, "", "nan", "0") for k in keys
            )
            errores = []
            if not _val("Voc_stc", "Voc"):
                errores.append(("Voc", "Tensión de circuito abierto en STC (V)"))
            if not _val("Isc_stc", "Isc"):
                errores.append(("Isc", "Corriente de cortocircuito en STC (A)"))
            if not _val("Vmp_stc", "Vmp"):
                errores.append(("Vmp", "Tensión en el punto de máxima potencia en STC (V)"))
            if not _val("Imp_stc", "Imp"):
                errores.append(("Imp", "Corriente en el punto de máxima potencia en STC (A)"))

            advertencias = []
            if not errores:
                if not _val("N_s", "NsA"):
                    advertencias.append(("N_s", "Número de celdas en serie — se estimará desde Voc/0.65 V"))
                else:
                    _hc = verificar_ns_halfcut(p)
                    if _hc and _hc["tipo"] == "ns_duplicado":
                        _r = _hc["rango_esperado"]
                        advertencias.append((
                            "⚠️ N_s incorrecto (half-cut)",
                            f"N_s={_hc['N_s_ingresado']} da Voc/celda = {_hc['Voc_por_celda']:.3f} V "
                            f"(rango esperado {_r[0]:.2f}–{_r[1]:.2f} V). "
                            f"Valor correcto para SDM: N_s = {_hc['N_s_sugerido']}. "
                            f"Corrige `Ns (Celdas Serie)` en el Excel."
                        ))
                    elif _hc and _hc["tipo"] == "ns_mitad":
                        _r = _hc["rango_esperado"]
                        advertencias.append((
                            "⚠️ N_s incorrecto (muy bajo)",
                            f"N_s={_hc['N_s_ingresado']} da Voc/celda = {_hc['Voc_por_celda']:.3f} V "
                            f"(rango esperado {_r[0]:.2f}–{_r[1]:.2f} V). "
                            f"Valor sugerido: N_s = {_hc['N_s_sugerido']}."
                        ))
                if not p.get("tecnologia"):
                    advertencias.append(("Tecnología", "Tecnología del panel — se asumirá Mono-Si"))
                if not _val("Tk_beta", "CoefVoc_C", "beta_oc"):
                    advertencias.append(("Coef. Temp. Voc (β)", "Se usará default por tecnología"))
                if not _val("Tk_alfa", "alpha_sc"):
                    advertencias.append(("Coef. Temp. Isc (α)", "Se usará default por tecnología"))
            return errores, advertencias
    """), encoding="utf-8")
    print("  [✓] panel_iv_check.py creado.")

# ── B: Motor IV — importar desde módulo compartido + eliminar función local ───
print("\n[B] Actualizando Motor IV...")
src_motiv = F_MOTIV.read_text(encoding="utf-8")
_b_ok = True

if "from calculos.panel_iv_check import analizar_panel_motiv" not in src_motiv:
    OLD_IMP = (
        "from calculos.modelo_iv import (\n"
        "    resolver_curva_iv,\n"
        "    validar_sdm_vs_ficha,\n"
        "    tiene_sdm_completo,\n"
        "    estimar_sdm_desde_ficha,\n"
        "    verificar_ns_halfcut,\n"
        ")"
    )
    NEW_IMP = OLD_IMP + "\nfrom calculos.panel_iv_check import analizar_panel_motiv as _analizar_panel_motiv"
    if OLD_IMP in src_motiv:
        backup(F_MOTIV, "118B")
        src_motiv = src_motiv.replace(OLD_IMP, NEW_IMP, 1)
        print("  [✓] Import añadido.")
    else:
        print("  [ADVERTENCIA] Bloque de imports no encontrado — añade manualmente:")
        print("    from calculos.panel_iv_check import analizar_panel_motiv as _analizar_panel_motiv")
        _b_ok = False

# Eliminar función local si aún existe
_LOCAL_START = "# ── Helper: detectar campos faltantes para Motor IV ───────────────────────────\ndef _analizar_panel_motiv"
_LOCAL_END   = "\n\n# ── Selector manual como alternativa / fallback ────────────────────────────────"
if _LOCAL_START in src_motiv:
    _s = src_motiv.find(_LOCAL_START)
    _e = src_motiv.find(_LOCAL_END, _s)
    if _e != -1:
        if not any(b.name.endswith("118B.py") for b in F_MOTIV.parent.glob("*.bak*")):
            backup(F_MOTIV, "118B")
        src_motiv = src_motiv[:_s] + src_motiv[_e + 2:]  # +2 para saltar el \n\n
        F_MOTIV.write_text(src_motiv, encoding="utf-8")
        print("  [✓] Función local _analizar_panel_motiv eliminada.")
    else:
        print("  [ADVERTENCIA] No se encontró el límite de la función. Revisa manualmente.")
else:
    if _b_ok:
        F_MOTIV.write_text(src_motiv, encoding="utf-8")
    print("  [OK] Función local ya eliminada — sin cambios adicionales.")

# ── C: Dimensionamiento — importar helper + mostrar aviso ────────────────────
print("\n[C] Actualizando Dimensionamiento...")
src_dim = F_DIM.read_text(encoding="utf-8")

if "_check_iv_dim" in src_dim and "⚠️" in src_dim and "Motor IV" in src_dim:
    print("  [OK] Parche #118 ya aplicado en Dimensionamiento — sin cambios.")
else:
    backup(F_DIM, "118C")

    # Import
    OLD_IMP_D = (
        "from datos.catalogo_paneles_excel import cargar_catalogo_excel, obtener_panel_excel\n"
        "from datos.catalogo_inversores_excel import cargar_catalogo_inversores, obtener_inversor_excel\n"
        "from datos.catalogo_inversores import INVERSORES, seleccionar_inversor"
    )
    NEW_IMP_D = OLD_IMP_D + "\nfrom calculos.panel_iv_check import analizar_panel_motiv as _check_iv_dim"
    if OLD_IMP_D in src_dim:
        src_dim = src_dim.replace(OLD_IMP_D, NEW_IMP_D, 1)
        print("  [✓] Import añadido.")
    else:
        print("  [ADVERTENCIA] Bloque de imports de catálogos no encontrado.")

    # Aviso
    OLD_TMY = (
        "# ── Auto-población de temperaturas desde TMY ──────────────────────────────────"
    )
    NEW_AVISO = """\
# ── Aviso Motor IV: panel sin datos IV suficientes (#118) ─────────────────────
_iv_err, _iv_adv = _check_iv_dim(panel)
if _iv_err:
    _falt = ", ".join(f"`{c}`" for c, _ in _iv_err)
    st.warning(
        f"⚠️ **{panel_nombre}** no tiene datos IV suficientes para Motor IV.  \\n"
        f"Campos requeridos ausentes: {_falt}.  \\n"
        f"El dimensionamiento eléctrico funcionará, pero la curva I-V no podrá "
        f"simularse en Motor IV. Completa el catálogo Excel con estos valores."
    )
elif _iv_adv:
    _adv_campos = [c for c, _ in _iv_adv if not c.startswith("⚠️")]
    if _adv_campos:
        st.info(
            f"ℹ️ **{panel_nombre}** puede simularse en Motor IV con estimaciones.  \\n"
            f"Campos opcionales ausentes: {', '.join(f'`{c}`' for c in _adv_campos)} "
            f"— se usarán defaults por tecnología."
        )

# ── Auto-población de temperaturas desde TMY ──────────────────────────────────"""
    if OLD_TMY in src_dim:
        src_dim = src_dim.replace(OLD_TMY, NEW_AVISO, 1)
        print("  [✓] Bloque de aviso Motor IV insertado.")
    else:
        print("  [ADVERTENCIA] Ancla 'Auto-población de temperaturas' no encontrada.")

    F_DIM.write_text(src_dim, encoding="utf-8")

print("\n" + "="*60)
print("[✓] Parche #118 aplicado.")
print("    pm2 restart streamlit-bipv")
print("""
Verificar en Dimensionamiento:
  • Al seleccionar un panel SIN Voc/Isc/Vmp/Imp → aparece st.warning en naranja
  • Al seleccionar un panel CON datos pero sin N_s → aparece st.info en azul
  • Al seleccionar ASP-ST1-T40 (SDM completo) → sin aviso
""")
