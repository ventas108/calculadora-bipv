#!/usr/bin/env python3
"""
Parche: Task #85 — Avisar en Motor IV cuando un panel no tiene datos suficientes
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_motor_iv_avisos_datos.py
    pm2 restart streamlit-bipv

Cambios:
  1. Nuevo helper _analizar_panel_motiv(): detecta errores bloqueantes (Voc/Isc/Vmp/Imp
     ausentes) y advertencias suaves (N_s, tecnología, coeficientes de temperatura ausentes)
  2. Auto-activación desde Dimensionamiento: mensaje de error específico con tabla de
     campos faltantes cuando la ficha no tiene datos IV completos
  3. Auto-activación: advertencias de campos opcionales ausentes junto al warning de estimación
  4. Selector manual: usa _analizar_panel_motiv() (corrige bug donde buscaba I_voc_ref)
  5. Selector manual: muestra campos opcionales ausentes junto al warning de estimación
  6. Fallback al default ASP-ST1-T40: ahora muestra st.warning explícito cuando el panel
     del Dimensionamiento no pudo cargarse
  7. Botón "Usar este panel": mensaje de error muestra los campos específicos faltantes
"""
import glob
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
errors = []

def patch(ruta: Path, buscar: str, reemplazar: str, desc: str):
    txt = ruta.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc); return
    ruta.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}'")

_mot_files = glob.glob(str(PAGES / "*Motor_IV*.py"))
if not _mot_files:
    print("❌  3_Motor_IV.py no encontrado"); raise SystemExit(1)
_mot = Path(_mot_files[0])

# ─────────────────────────────────────────────────────────────────────────────
# 1. Insertar helper _analizar_panel_motiv antes del selector manual
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[1] {_mot.name} — insertar helper _analizar_panel_motiv")
patch(
    _mot,
    buscar=(
        '# ── Selector manual como alternativa / fallback ────────────────────────────────\n'
        '# Combinar catálogo SDM calibrado (BIPV ASP-ST1) + catálogo Excel por tecnología\n'
        '_cat_excel = {}'
    ),
    reemplazar=(
        '# ── Helper: detectar campos faltantes para Motor IV ───────────────────────────\n'
        'def _analizar_panel_motiv(p: dict) -> tuple:\n'
        '    """\n'
        '    Retorna (errores, advertencias) donde:\n'
        '      errores      = [(campo, descripción)] — bloquean la simulación\n'
        '      advertencias = [(campo, descripción)] — estimación con default, resultados menos precisos\n'
        '    """\n'
        '    _val = lambda *keys: any(\n'
        '        p.get(k) not in (None, 0, 0.0, "", "nan", "0") for k in keys\n'
        '    )\n'
        '    errores = []\n'
        '    if not _val("Voc_stc", "Voc"):\n'
        '        errores.append(("Voc", "Tensión de circuito abierto en STC (V)"))\n'
        '    if not _val("Isc_stc", "Isc"):\n'
        '        errores.append(("Isc", "Corriente de cortocircuito en STC (A)"))\n'
        '    if not _val("Vmp_stc", "Vmp"):\n'
        '        errores.append(("Vmp", "Tensión en el punto de máxima potencia en STC (V)"))\n'
        '    if not _val("Imp_stc", "Imp"):\n'
        '        errores.append(("Imp", "Corriente en el punto de máxima potencia en STC (A)"))\n'
        '\n'
        '    advertencias = []\n'
        '    if not errores:  # solo mostramos advertencias si los campos críticos están\n'
        '        if not _val("N_s", "NsA"):\n'
        '            advertencias.append(("N_s", "Número de celdas en serie — se estimará desde Voc/0.65 V"))\n'
        '        if not p.get("tecnologia"):\n'
        '            advertencias.append(("Tecnología", "Tecnología del panel — se asumirá Mono-Si"))\n'
        '        if not _val("Tk_beta", "CoefVoc_C", "beta_oc"):\n'
        '            advertencias.append(("Coef. Temp. Voc (β)", "Coeficiente de temperatura de Voc — se usará default por tecnología"))\n'
        '        if not _val("Tk_alfa", "alpha_sc"):\n'
        '            advertencias.append(("Coef. Temp. Isc (α)", "Coeficiente de temperatura de Isc — se usará default por tecnología"))\n'
        '    return errores, advertencias\n'
        '\n'
        '\n'
        '# ── Selector manual como alternativa / fallback ────────────────────────────────\n'
        '# Combinar catálogo SDM calibrado (BIPV ASP-ST1) + catálogo Excel por tecnología\n'
        '_cat_excel = {}'
    ),
    desc="helper _analizar_panel_motiv"
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Mejorar bloque auto-activación
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[2] {_mot.name} — mejorar mensajes de auto-activación")
patch(
    _mot,
    buscar=(
        '    else:\n'
        '        # ── Ficha básica (catálogo Excel) → estimar SDM ────────────────────────\n'
        '        _sdm_est = estimar_sdm_desde_ficha(_panel_ss)\n'
        '        if _sdm_est is not None:\n'
        '            _modo_auto    = True\n'
        '            _panel_activo = _sdm_est\n'
        '            _estimado     = True\n'
        '            _metodo_est   = _sdm_est.get("_metodo", "estimado")\n'
        '            st.warning(\n'
        '                f"🟡 **Auto-activado con estimación** — Panel: **{_panel_nom_ss}** "\n'
        '                f"(catálogo Excel). Parámetros SDM estimados por **{_metodo_est}** "\n'
        '                f"desde ficha técnica. Resultados orientativos — valida con datos calibrados."\n'
        '            )\n'
        '        else:\n'
        '            st.info(\n'
        '                f"ℹ️ Panel **{_panel_nom_ss}** no tiene datos suficientes para el Motor IV "\n'
        '                f"(faltan Voc, Isc, Vmp o Imp). Selecciona manualmente un panel con ficha completa."\n'
        '            )'
    ),
    reemplazar=(
        '    else:\n'
        '        # ── Ficha básica (catálogo Excel) → estimar SDM ────────────────────────\n'
        '        _err_auto, _adv_auto = _analizar_panel_motiv(_panel_ss)\n'
        '        if _err_auto:\n'
        '            _falt_str = ", ".join(f"**{c}**" for c, _ in _err_auto)\n'
        '            st.error(\n'
        '                f"❌ **Panel `{_panel_nom_ss}` no tiene datos suficientes para el Motor IV.**  \\n"\n'
        '                f"Campos requeridos ausentes en el catálogo Excel: {_falt_str}.  \\n\\n"\n'
        '                "| Campo | Descripción |\\n|---|---|\\n"\n'
        '                + "\\n".join(f"| `{c}` | {d} |" for c, d in _err_auto)\n'
        '                + f"\\n\\n⬇️ Se usará el panel por defecto **ASP-ST1-T40** para esta simulación."\n'
        '            )\n'
        '        else:\n'
        '            _sdm_est = estimar_sdm_desde_ficha(_panel_ss)\n'
        '            if _sdm_est is not None:\n'
        '                _modo_auto    = True\n'
        '                _panel_activo = _sdm_est\n'
        '                _estimado     = True\n'
        '                _metodo_est   = _sdm_est.get("_metodo", "estimado")\n'
        '                _adv_lines = ""\n'
        '                if _adv_auto:\n'
        '                    _adv_lines = "  \\n" + "  \\n".join(\n'
        '                        f"- ⚠️ `{c}` no definido — {d}" for c, d in _adv_auto\n'
        '                    )\n'
        '                st.warning(\n'
        '                    f"🟡 **Auto-activado con estimación** — Panel: **{_panel_nom_ss}** "\n'
        '                    f"(catálogo Excel). Parámetros SDM estimados por **{_metodo_est}** "\n'
        '                    f"desde ficha técnica. Resultados orientativos.{_adv_lines}"\n'
        '                )\n'
        '            else:\n'
        '                st.error(\n'
        '                    f"❌ **No se pudo estimar el SDM para `{_panel_nom_ss}`.**  \\n"\n'
        '                    "Los datos básicos (Voc, Isc, Vmp, Imp) están presentes pero el ajuste "\n'
        '                    "De Soto no convergió. Verifica que los valores sean físicamente coherentes "\n'
        '                    "(Vmp < Voc, Imp < Isc, Pmax = Vmp × Imp).  \\n"\n'
        '                    "⬇️ Se usará el panel por defecto **ASP-ST1-T40** para esta simulación."\n'
        '                )'
    ),
    desc="auto-activación mensajes mejorados"
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Selector manual — reemplazar lógica de _falt (bug) con _analizar_panel_motiv
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[3] {_mot.name} — selector manual: usar _analizar_panel_motiv")
patch(
    _mot,
    buscar=(
        '        _p_sel = _cat_excel.get(_panel_manual_nom, {})\n'
        '        if _tiene_iv(_p_sel):\n'
        '            st.warning("🟡 Catálogo Excel — SDM estimado desde ficha. Resultados orientativos.")\n'
        '        else:\n'
        '            _falt = [f for f, k in [("Voc","Voc"),("Isc","Isc"),("Vmp","Vmp"),("Imp","Imp")]\n'
        '                     if not (_p_sel.get(k) or _p_sel.get(f"I_{k.lower()}_ref") or _p_sel.get(f"V_{k.lower()}_ref"))]\n'
        '            st.error(\n'
        '                f"⚠️ **Datos incompletos** — faltan: **{\', \'.join(_falt) if _falt else \'valores IV\'}**. "\n'
        '                f"Completa la ficha en el Excel antes de usar este panel."\n'
        '            )'
    ),
    reemplazar=(
        '        _p_sel = _cat_excel.get(_panel_manual_nom, {})\n'
        '        _err_sel, _adv_sel = _analizar_panel_motiv(_p_sel)\n'
        '        if _err_sel:\n'
        '            st.error(\n'
        '                f"❌ **Datos insuficientes para simular `{_panel_manual_nom}`.**  \\n"\n'
        '                "Campos requeridos ausentes en el catálogo Excel:\\n\\n"\n'
        '                "| Campo | Descripción |\\n|---|---|\\n"\n'
        '                + "\\n".join(f"| `{c}` | {d} |" for c, d in _err_sel)\n'
        '                + "\\n\\nCompleta estos campos en la hoja `Catalogo_Paneles` del Excel antes de usar este panel."\n'
        '            )\n'
        '        else:\n'
        '            _msg_adv = ""\n'
        '            if _adv_sel:\n'
        '                _msg_adv = "  \\n" + "  \\n".join(\n'
        '                    f"- ⚠️ `{c}` ausente — {d}" for c, d in _adv_sel\n'
        '                )\n'
        '            st.warning(\n'
        '                f"🟡 **Catálogo Excel** — SDM estimado desde ficha. Resultados orientativos.{_msg_adv}"\n'
        '            )'
    ),
    desc="selector manual: usar _analizar_panel_motiv"
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Fallback al default — aviso explícito
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[4] {_mot.name} — aviso en fallback a ASP-ST1-T40")
patch(
    _mot,
    buscar=(
        '# Si aún no hay panel activo, usar el default\n'
        'if _panel_activo is None:\n'
        '    _panel_activo = ASP_ST1_T40\n'
        '    _panel_nom_ss = "ASP-ST1-T40"\n'
        '    _estimado     = False'
    ),
    reemplazar=(
        '# Si aún no hay panel activo, usar el default con aviso explícito\n'
        'if _panel_activo is None:\n'
        '    _panel_activo = ASP_ST1_T40\n'
        '    _panel_nom_ss = "ASP-ST1-T40"\n'
        '    _estimado     = False\n'
        '    if _panel_ss and st.session_state.get("panel_nombre_dim"):\n'
        '        st.warning(\n'
        '            f"⚠️ No se pudo cargar **{st.session_state.get(\'panel_nombre_dim\')}** — "\n'
        '            "la simulación está usando el panel de referencia **ASP-ST1-T40 (SDM calibrado)**.  \\n"\n'
        '            "Selecciona manualmente un panel con ficha completa en el selector de abajo."\n'
        '        )'
    ),
    desc="aviso en fallback a ASP-ST1-T40"
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. Botón "Usar este panel" — error específico
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[5] {_mot.name} — botón 'Usar este panel': error específico")
patch(
    _mot,
    buscar=(
        '            if not _tiene_iv(_base):\n'
        '                st.error(f"❌ **{_panel_manual_nom}** — no tiene Voc, Isc, Vmp e Imp completos. Completa la ficha en el catálogo Excel.")\n'
        '                _panel_activo = None'
    ),
    reemplazar=(
        '            if not _tiene_iv(_base):\n'
        '                _err_btn, _ = _analizar_panel_motiv(_base)\n'
        '                _falt_btn = ", ".join(f"`{c}`" for c, _ in _err_btn) if _err_btn else "Voc, Isc, Vmp o Imp"\n'
        '                st.error(\n'
        '                    f"❌ **{_panel_manual_nom}** — faltan campos requeridos: {_falt_btn}.  \\n"\n'
        '                    "Completa la ficha en la hoja `Catalogo_Paneles` del Excel."\n'
        '                )\n'
        '                _panel_activo = None'
    ),
    desc="botón 'Usar este panel': error específico"
)

print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos:"); [print(f"   · {e}") for e in errors]
else:
    print("✅ Todos los parches aplicados correctamente.")
print("Próximo paso: pm2 restart streamlit-bipv")
