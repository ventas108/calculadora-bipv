#!/usr/bin/env python3
"""
Parche: Task #72 — Evitar que O&M por defecto subestime costos en instalaciones grandes
Aplicar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    python3 bipv_python/scripts/patch_opex_sugerir_y_floor.py
    pm2 restart streamlit-bipv

Cambios en pages/8_Presupuesto.py (pestaña OPEX Anual):
  1. Añadir botón "🪄 Sugerir valores O&M" junto al botón Resetear.
     Al presionarlo, llama a _calc_parametrico con el tipo/zona/escenario actuales
     y pre-llena los 8 ítems de _OPEX_DEFAULT con valores de referencia Colombia.

  2. Añadir aviso de piso mínimo por kWp después de mostrar los KPIs:
     - < 60% de la referencia mínima → st.error (muy peligroso para TIR/VPN)
     - < referencia mínima → st.warning (subestimado)
     - > 130% de la referencia máxima → st.info (verificar duplicados)
     - OPEX == 0 con sistema conocido → st.info pidiendo sugerir o ingresar
"""
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
PRES  = BASE / "pages" / "8_💼_Presupuesto.py"
errors = []

def patch(buscar, reemplazar, desc):
    txt = PRES.read_text(encoding="utf-8")
    if buscar not in txt:
        print(f"  ⚠  '{desc}' — fragmento NOT found (already applied?)")
        errors.append(desc); return
    PRES.write_text(txt.replace(buscar, reemplazar, 1), encoding="utf-8")
    print(f"  ✅  '{desc}'")

# ── 1. Añadir botón Sugerir O&M + lógica de sugerencia ───────────────────────
print(f"\n[1] {PRES.name} — botón Sugerir O&M")
patch(
    buscar=(
        '    ss_opex = "df_sec_opex"\n'
        '    col_ro, col_fo = st.columns([2, 4])\n'
        '    if col_ro.button("↺ Resetear \'OPEX\'", key="reset_opex"):\n'
        '        st.session_state.pop(ss_opex, None)\n'
        '        st.rerun()\n'
        '    fuente_o = col_fo.text_input("Fuente / cotización OPEX",\n'
        '        value=st.session_state.get("fuente_opex",""),\n'
        '        placeholder="Ej.: Contrato O&M empresa Z, póliza seguro W, julio 2026",\n'
        '        key="fuente_inp_opex", label_visibility="collapsed")\n'
        '    st.session_state["fuente_opex"] = fuente_o\n'
        '\n'
        '    if ss_opex not in st.session_state:\n'
        '        st.session_state[ss_opex] = _df_con_activo(_OPEX_DEFAULT)\n'
    ),
    reemplazar=(
        '    ss_opex = "df_sec_opex"\n'
        '    col_ro, col_sug_o, col_fo = st.columns([2, 2, 4])\n'
        '    if col_ro.button("↺ Resetear \'OPEX\'", key="reset_opex"):\n'
        '        st.session_state.pop(ss_opex, None)\n'
        '        st.rerun()\n'
        '\n'
        '    # ── #72 — Botón sugerir valores O&M desde benchmarks paramétricos ─────────\n'
        '    _btn_sug_o = col_sug_o.button("🪄 Sugerir valores O&M", key="sug_opex",\n'
        '        help="Rellena los ítems con valores de referencia Colombia 2026 calculados "\n'
        '             "desde el tipo de instalación, zona geográfica y potencia del sistema.")\n'
        '    if _btn_sug_o:\n'
        '        if p_stc > 0:\n'
        '            _tipo_sug = st.session_state.get("est_tipo", list(_BENCH.keys())[1])\n'
        '            _esc_sug  = st.session_state.get("est_esc",  "Base")\n'
        '            _zona_sug = st.session_state.get("est_zona", list(_ZONA_FACTOR.keys())[0])\n'
        '            _r_sug = _calc_parametrico(p_stc, _tipo_sug, _esc_sug, _zona_sug)\n'
        '            _sug_rows = [\n'
        '                ["O&M preventivo — visitas técnicas anuales",   "OM-001", 1.0, "año",  round(_r_sug["opex_om"],   2)],\n'
        '                ["Limpieza de módulos (aprox. 4 veces/año)",    "OM-002", 4.0, "serv", round(_r_sug["opex_limp"] / 4, 2)],\n'
        '                ["Seguro operativo — todo riesgo instalación",  "SEG-002",1.0, "año",  round(_r_sug["opex_seg"],  2)],\n'
        '                ["Monitoreo remoto (plataforma Growatt/SCADA)", "MON-001",1.0, "año",  round(_r_sug["opex_mon"],  2)],\n'
        '                ["Revisión anual inversor y comunicaciones",    "OM-003", 1.0, "año",  0.0],\n'
        '                ["Fondo de reposición inversor (año 12–15)",    "RES-001",1.0, "año",  round(_r_sug["opex_repos"] * 0.70, 2)],\n'
        '                ["Fondo de reposición módulos / garantías",     "RES-002",1.0, "año",  round(_r_sug["opex_repos"] * 0.30, 2)],\n'
        '                ["Administración y costos fijos anuales",       "ADM-001",1.0, "año",  0.0],\n'
        '            ]\n'
        '            st.session_state[ss_opex] = _df_con_activo(_sug_rows)\n'
        '            st.toast(\n'
        '                f"✅ OPEX sugerido: USD {{_r_sug[\'opex_total\']:,.0f}}/año "\n'
        '                f"≈ {{_r_sug[\'opex_total\']/p_stc:.0f}} USD/kWp·año "\n'
        '                f"({{_tipo_sug}} · {{_esc_sug}} · {{_zona_sug}})", icon="🪄"\n'
        '            )\n'
        '        else:\n'
        '            st.warning("⚠️ Completa 📐 Dimensionamiento primero para conocer la potencia del sistema.")\n'
        '\n'
        '    fuente_o = col_fo.text_input("Fuente / cotización OPEX",\n'
        '        value=st.session_state.get("fuente_opex",""),\n'
        '        placeholder="Ej.: Contrato O&M empresa Z, póliza seguro W, julio 2026",\n'
        '        key="fuente_inp_opex", label_visibility="collapsed")\n'
        '    st.session_state["fuente_opex"] = fuente_o\n'
        '\n'
        '    if ss_opex not in st.session_state:\n'
        '        st.session_state[ss_opex] = _df_con_activo(_OPEX_DEFAULT)\n'
    ),
    desc="botón Sugerir O&M"
)

# ── 2. Añadir aviso de piso mínimo por kWp ────────────────────────────────────
print(f"\n[2] {PRES.name} — aviso piso mínimo OPEX/kWp")
patch(
    buscar=(
        '    st.caption(f"📋 {len(ed_opex)} ítems — {int(act_o.sum())} activos. → Este valor reemplaza el slider O&M en 💰 Financiero.")\n'
    ),
    reemplazar=(
        '    st.caption(f"📋 {len(ed_opex)} ítems — {int(act_o.sum())} activos. → Este valor reemplaza el slider O&M en 💰 Financiero.")\n'
        '\n'
        '    # ── #72 — Avisar cuando OPEX por kWp está por debajo del mínimo referencia ──\n'
        '    if p_stc > 0 and sub7 > 0:\n'
        '        _opex_kw_real = sub7 / p_stc\n'
        '        _tipo_inst_t7 = str(st.session_state.get("tipo_instalacion", "")).lower()\n'
        '        if any(x in _tipo_inst_t7 for x in ["bipv", "fachada", "pergola", "pérgola", "marquesina"]):\n'
        '            _opex_ref_lo, _opex_ref_hi, _tipo_lbl = 18.0, 32.0, "BIPV fachada/pérgola"\n'
        '        elif any(x in _tipo_inst_t7 for x in ["techo", "roof", "cubierta"]):\n'
        '            _opex_ref_lo, _opex_ref_hi, _tipo_lbl = 9.0,  16.0, "techo industrial"\n'
        '        else:\n'
        '            _opex_ref_lo, _opex_ref_hi, _tipo_lbl = 8.0,  14.0, "granja FV campo"\n'
        '        if _opex_kw_real < _opex_ref_lo * 0.6:\n'
        '            st.error(\n'
        '                f"🚨 **OPEX muy bajo: USD {_opex_kw_real:.0f}/kWp·año** — "\n'
        '                f"la referencia para {_tipo_lbl} es **{_opex_ref_lo:.0f}–{_opex_ref_hi:.0f} USD/kWp·año**. "\n'
        '                f"Un OPEX subestimado sobreestima la TIR y el VPN en el análisis financiero. "\n'
        '                f"Usa **🪄 Sugerir valores O&M** para obtener valores de referencia."\n'
        '            )\n'
        '        elif _opex_kw_real < _opex_ref_lo:\n'
        '            st.warning(\n'
        '                f"⚠️ **OPEX bajo: USD {_opex_kw_real:.0f}/kWp·año** — "\n'
        '                f"la referencia para {_tipo_lbl} es {_opex_ref_lo:.0f}–{_opex_ref_hi:.0f} USD/kWp·año. "\n'
        '                f"Verifica que estén incluidos seguro, monitoreo y fondos de reposición."\n'
        '            )\n'
        '        elif _opex_kw_real > _opex_ref_hi * 1.3:\n'
        '            st.info(\n'
        '                f"ℹ️ OPEX alto: USD {_opex_kw_real:.0f}/kWp·año (ref. {_tipo_lbl}: "\n'
        '                f"{_opex_ref_lo:.0f}–{_opex_ref_hi:.0f}). Revisa si hay ítems duplicados."\n'
        '            )\n'
        '    elif p_stc > 0 and sub7 == 0:\n'
        '        st.info(\n'
        '            "ℹ️ **OPEX = USD 0** — usa **🪄 Sugerir valores O&M** para pre-llenar con benchmarks "\n'
        '            "de mercado colombiano, o ingresa los costos reales de O&M, seguro y reposición."\n'
        '        )\n'
    ),
    desc="aviso piso mínimo OPEX/kWp"
)

print("\n" + "="*60)
if errors:
    print(f"⚠  {len(errors)} parche(s) omitidos:"); [print(f"   · {e}") for e in errors]
else:
    print("✅ Todos los parches aplicados.")
print("Próximo paso: pm2 restart streamlit-bipv")
