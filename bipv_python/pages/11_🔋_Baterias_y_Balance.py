"""
Página 11 — Baterías y Balance Energético
B-6: Dimensionado eléctrico strings + baterías
B-7: Balance energético mensual + Clasificación A+/A/B/C/D
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from datos.catalogo_baterias_excel import (
    cargar_catalogo_baterias,
    obtener_bateria,
    lista_baterias,
    diagnostico_catalogo,
    excel_mtime as _excel_mtime,
)
from calculos.baterias_balance import (
    dimensionar_bateria,
    balance_mensual,
    metricas_balance,
    clasificar_energia,
    distribuir_consumo_anual,
    tabla_clasificaciones,
    PERFILES_TIPICOS,
    MESES,
)

st.set_page_config(
    page_title="Baterías y Balance — BIPV",
    page_icon="🔋",
    layout="wide",
)
st.title("🔋 Baterías y Balance Energético")
st.caption(
    "B-6: Dimensionado de baterías · "
    "B-7: Balance mensual producción vs consumo · "
    "Clasificación energética A+/A/B/C/D"
)

# ── Pre-requisitos ────────────────────────────────────────────────────────────
prod_ok   = st.session_state.get("produccion_ok", False)
df_m_prod = st.session_state.get("df_mensual_produccion", None)

# Prioridad E_ac: multi-superficie > bypass > base (claves exclusivas)
_e_ac_base_bat     = float(st.session_state.get("E_ac_anual_kWh", 0.0))
_e_ac_bypass_bat   = float(st.session_state.get("E_ac_anual_kWh_bypass", 0.0))
_e_ac_multisup_bat = float(st.session_state.get("E_ac_anual_kWh_multisup", 0.0))
_bypass_ok_bat     = st.session_state.get("bypass_ok", False)
_multisup_ok_bat   = st.session_state.get("multisup_activo", False)
_kwh_bp_bat        = float(st.session_state.get("kwh_bypass_anual", 0.0))

if _multisup_ok_bat and _e_ac_multisup_bat > 0:
    e_ac_anual = _e_ac_multisup_bat
elif _bypass_ok_bat and _e_ac_bypass_bat > 0:
    e_ac_anual = _e_ac_bypass_bat
else:
    e_ac_anual = _e_ac_base_bat

if not prod_ok or df_m_prod is None or e_ac_anual <= 0:
    st.warning(
        "⚠️ **Producción no calculada.** "
        "Complete primero la Página 6 — Producción Anual para obtener los datos mensuales "
        "que necesita esta página."
    )
    st.info(
        "💡 Puede continuar configurando baterías, pero el balance energético "
        "requiere los resultados de producción."
    )

# Banner bypass (#37)
if prod_ok and _bypass_ok_bat and _e_ac_bypass_bat > 0:
    st.info(
        f"⚡ **Corrección bypass activa:** "
        f"E_ac base = {_e_ac_base_bat:,.0f} kWh/año → "
        f"pérdida bypass = {_kwh_bp_bat:,.0f} kWh/año → "
        f"**E_ac usada en el balance = {e_ac_anual:,.0f} kWh/año** "
        f"({(_e_ac_base_bat - e_ac_anual) / _e_ac_base_bat * 100:.1f}% menos). "
        "La autogeneración y el dimensionamiento de la batería se calculan con la producción real."
    )
elif prod_ok and e_ac_anual > 0:
    st.caption(
        "💡 Ejecuta el modelo Bypass Diodes en Página 5 para usar la E_ac corregida "
        "por sombra parcial en este balance energético."
    )

# ══════════════════════════════════════════════════════════════════════════════
# B-6 — Dimensionado de baterías
# ══════════════════════════════════════════════════════════════════════════════
_hdr_col, _btn_col = st.columns([8, 2])
with _hdr_col:
    st.header("⚡ B-6 — Dimensionado de Baterías")
with _btn_col:
    st.write("")   # alinear verticalmente con el header
    # #26 — Botón de recarga inmediata (invalida caché sin reiniciar PM2)
    if st.button(
        "🔄 Recargar catálogo",
        help=(
            "Invalida el caché y recarga el catálogo de baterías desde el Excel del servidor. "
            "Úsalo tras agregar o modificar la hoja `Catalogo_Baterias` para confirmar "
            "que los cambios se ven en la app sin necesidad de reiniciar PM2."
        ),
        use_container_width=True,
    ):
        cargar_catalogo_baterias.clear()
        diagnostico_catalogo.clear()
        st.rerun()

# Caché auto-invalidante: si el Excel cambia en disco, _mtime cambia → cache miss
_mtime_bat = _excel_mtime()
cat_bat = cargar_catalogo_baterias(_mtime=_mtime_bat)
tiene_catalogo = len(cat_bat) > 0

# ── #26 — Banner de estado de carga del catálogo ─────────────────────────────
_diag = diagnostico_catalogo(_mtime=_mtime_bat)
_hojas_disp = _diag.get("hojas_disponibles", [])
_hoja_usada = _diag.get("hoja_usada")

if not tiene_catalogo:
    if "error" in _diag:
        st.error(f"🔴 **Excel no accesible:** {_diag['error']}")
    elif not _hoja_usada:
        st.error(
            f"🔴 **Hoja `Catalogo_Baterias` no encontrada** en el archivo Excel del servidor. "
            f"Hojas disponibles: `{'`, `'.join(_hojas_disp) if _hojas_disp else 'ninguna'}`"
        )
    else:
        st.warning("🟡 **Catálogo vacío** — la hoja existe pero no se cargaron modelos. "
                   "Verifique que las columnas del Excel coincidan con el formato esperado.")
else:
    _n_modelos   = _diag.get("modelos_cargados", len(cat_bat))
    _incompletos = _diag.get("modelos_incompletos", [])
    _no_mapeadas = _diag.get("columnas_no_mapeadas", [])
    # #24 — campos cuyo alias no apareció en NINGUNA columna del Excel
    _ausentes    = _diag.get("campos_sin_columna_excel", [])
    # #123 — modelos que aparecen más de una vez en el Excel
    _duplicados  = _diag.get("modelos_duplicados", [])

    _criticos_aus    = [c for c in _ausentes if c.get("critico")]
    _importantes_aus = [c for c in _ausentes if c.get("importante") and not c.get("critico")]

    # ── Alertas de columnas ausentes — visibles sin abrir el expander ──────────
    if _criticos_aus:
        st.error(
            "🔴 **Columnas críticas ausentes en el Excel** — sin ellas ninguna batería "
            "puede dimensionarse: `"
            + "`, `".join(c["campo"] for c in _criticos_aus) + "`  \n"
            "Abre el diagnóstico ↓ para ver exactamente qué encabezados agregar al Excel."
        )
    if _importantes_aus:
        st.warning(
            "⚠️ **Columnas importantes ausentes en el Excel**: `"
            + "`, `".join(c["campo"] for c in _importantes_aus) + "`  \n"
            "Se usarán valores por defecto (80 % DoD · 95 % RTE · 3 000 ciclos). "
            "Abre el diagnóstico ↓ para ver qué encabezados agregar."
        )

    if _ausentes or _incompletos or _no_mapeadas or _duplicados:
        st.warning(
            f"🟡 **Catálogo parcial** — hoja `{_hoja_usada}` · **{_n_modelos} modelos** cargados"
            + (f" · {len(_ausentes)} columnas ausentes en Excel" if _ausentes else "")
            + (f" · {len(_incompletos)} modelos con valores vacíos" if _incompletos else "")
            + (f" · {len(_no_mapeadas)} columnas no reconocidas" if _no_mapeadas else "")
            + (f" · {len(_duplicados)} modelos duplicados" if _duplicados else "")
        )
    else:
        st.success(
            f"✅ **Catálogo OK** — hoja `{_hoja_usada}` · **{_n_modelos} modelos** · "
            "todas las columnas reconocidas y sin valores vacíos"
        )

# ── #24 — Expander de diagnóstico detallado ──────────────────────────────────
if tiene_catalogo:
    _incompletos = _diag.get("modelos_incompletos", [])
    _no_mapeadas = _diag.get("columnas_no_mapeadas", [])
    _ausentes    = _diag.get("campos_sin_columna_excel", [])
    _duplicados  = _diag.get("modelos_duplicados", [])
    if _ausentes or _incompletos or _no_mapeadas or _duplicados:
        with st.expander("🔍 Diagnóstico detallado del catálogo"):

            # ① Columnas completamente ausentes del Excel (#24)
            if _ausentes:
                st.markdown("**① Columnas sin ningún alias en el Excel:**")
                st.caption(
                    "Estas columnas internas no tienen NINGUNA columna mapeada en tu Excel. "
                    "Agrega **UNA** de las opciones sugeridas como encabezado de columna en "
                    f"la hoja `{_diag.get('hoja_usada', 'Catalogo_Baterias')}`."
                )
                _rows_aus = []
                for _c in _ausentes:
                    _nivel = (
                        "🔴 Crítico"    if _c.get("critico")    else
                        "🟡 Importante" if _c.get("importante") else
                        "🔵 Opcional"
                    )
                    _rows_aus.append({
                        "Campo interno":  _c["campo"],
                        "Nivel":          _nivel,
                        "Agregar UNA de estas columnas al Excel":
                            " | ".join(_c.get("columnas_sugeridas", [])),
                    })
                st.dataframe(pd.DataFrame(_rows_aus), use_container_width=True, hide_index=True)

            # ② Columnas del Excel no reconocidas
            if _no_mapeadas:
                st.markdown("**② Columnas del Excel NO reconocidas por el loader:**")
                st.code(", ".join(_no_mapeadas))
                st.caption(
                    "Estas columnas están en el Excel pero no tienen un alias en el loader. "
                    "Si contienen datos importantes, agrega el nombre exacto al `_COL_MAP` "
                    "en `datos/catalogo_baterias_excel.py`."
                )

            # ③ Modelos con valores vacíos (la columna existe pero la celda está vacía)
            if _incompletos:
                st.markdown("**③ Modelos con valores vacíos en campos críticos:**")
                _rows_inc = []
                for _m in _incompletos:
                    _rows_inc.append({
                        "Modelo":                   _m["modelo"],
                        "Campos con valor vacío":   ", ".join(_m["campos_faltantes"]) if _m["campos_faltantes"] else "—",
                        "Ficha marcada completa":   "✅ Sí" if _m.get("datos_completos") else "🟡 No",
                    })
                st.dataframe(
                    pd.DataFrame(_rows_inc), use_container_width=True, hide_index=True
                )
                st.caption(
                    "Modelos sin `capacidad_kWh` no pueden dimensionarse. "
                    "Modelos sin `dod_pct`, `eta_rte_pct` o `ciclos_vida` usan valores por defecto "
                    "(80 % DoD · 95 % RTE · 3 000 ciclos)."
                )

            # ④ Modelos duplicados en el Excel (solo sobrevive la última fila)
            _duplicados = _diag.get("modelos_duplicados", [])
            if _duplicados:
                st.markdown("**④ Modelos duplicados en el Excel:**")
                _rows_dup = [{
                    "Modelo":            _d["modelo"],
                    "Veces que aparece": _d["n"],
                    "Filas en el Excel": ", ".join(str(f) for f in _d["filas_excel"]),
                } for _d in _duplicados]
                st.dataframe(
                    pd.DataFrame(_rows_dup), use_container_width=True, hide_index=True
                )
                st.warning(
                    "⚠️ Cuando un modelo se repite, **solo se carga la última fila** y las "
                    "anteriores se descartan en silencio. Elimina o renombra las filas "
                    "duplicadas en el Excel para saber exactamente qué datos se están usando.",
                    icon="⚠️",
                )
elif not tiene_catalogo:
    with st.expander("📋 Columnas esperadas en la hoja Catalogo_Baterias"):
        st.markdown("""
| Columna | Descripción | Ejemplo |
|---|---|---|
| Modelo | Nombre del modelo | BYD Battery-Box HVM |
| Datos completos (Si/No) | Si / No | Si |
| Capacidad (kWh) | Capacidad nominal | 11.04 |
| Potencia Continua (kW) | Potencia de carga/descarga | 5.0 |
| Voltaje Nominal (V) | Tensión del bus DC | 48 |
| DoD Máximo (%) | Profundidad de descarga máxima | 90 |
| Ciclos de Vida | Ciclos garantizados a DoD nominal | 4000 |
| Eficiencia RTE (%) | Rendimiento round-trip | 96 |
| Tecnología | Química | LFP |
| Costo (USD) | Precio unitario sin IVA | 4200 |
| Garantía (años) | Años de garantía | 10 |
        """)

col_b1, col_b2 = st.columns([1, 1])

with col_b1:
    st.subheader("Selección de batería")

    if not tiene_catalogo:
        # El banner de error ya fue mostrado arriba — solo bloquear la selección
        st.info("👆 Ver instrucciones arriba para agregar la hoja al Excel del servidor.")
        usa_bateria = False
    else:
        lista = lista_baterias()
        bat_sel = st.selectbox("Batería del catálogo", lista, key="bat_nombre_sel")
        bat = obtener_bateria(bat_sel)

        # Indicador completitud ficha
        if bat.get("datos_completos"):
            st.success("🟢 Ficha completa")
        else:
            _falt = [k for k in ["capacidad_kWh", "potencia_kW", "dod_pct", "ciclos_vida"]
                     if not bat.get(k)]
            st.warning(f"🟡 Datos incompletos — faltan: {', '.join(_falt)}" if _falt
                       else "🟡 Ficha marcada como incompleta en catálogo")

        # ── #25 — Compatibilidad batería ↔ inversor ───────────────────────────
        _inv_dim    = st.session_state.get("inversor_dict_dim", {})
        _inv_nombre = st.session_state.get("inversor_nombre_dim", "")
        _bat_v      = bat.get("voltaje_V")

        def _check_compatibilidad(bat_d: dict, inv_d: dict, inv_nom: str) -> tuple:
            """(estado, msg) — estado: 'ok' | 'warning' | 'error'"""
            if not inv_d and not inv_nom:
                return "warning", (
                    "⚠️ **Inversor no seleccionado:** ve a Página 4 › Dimensionamiento "
                    "para seleccionar el inversor antes de verificar la compatibilidad."
                )
            bat_v       = bat_d.get("voltaje_V")
            es_hibrido  = inv_d.get("es_hibrido", False)
            bat_v_min   = inv_d.get("bat_voltaje_min")
            bat_v_max   = inv_d.get("bat_voltaje_max")
            inv_lower   = inv_nom.lower()

            # Heurística por nombre si no hay flag explícito
            es_string   = any(x in inv_lower for x in ["mid", "max", "mtlp", "string"])
            es_hibrido_h = any(x in inv_lower for x in ["sph", "spa", "hybrid", "storage",
                                                          "min tl-x", "min-tl-x", "bcs"])
            tipo_inv = es_hibrido or es_hibrido_h

            motivos = []

            # 1. Verificar si es inversor de string (no acepta baterías)
            if not tipo_inv and es_string:
                motivos.append(
                    f"**`{inv_nom}`** es un inversor de **string** (sin puerto DC para batería). "
                    "Las baterías requieren un inversor **híbrido** (ej. Growatt SPH/SPA, Huawei SUN2000)."
                )

            # 2. Verificar rango de voltaje si el inversor es híbrido y tiene rango
            if tipo_inv and bat_v and bat_v_min and bat_v_max:
                if not (bat_v_min <= bat_v <= bat_v_max):
                    motivos.append(
                        f"Voltaje de batería **{bat_v:.0f} V** fuera del rango del inversor "
                        f"({bat_v_min:.0f}–{bat_v_max:.0f} V)."
                    )

            # 3. Batería HV con inversor no identificado como híbrido
            if not tipo_inv and not es_string and bat_v and bat_v > 150:
                motivos.append(
                    f"La batería es **alta tensión ({bat_v:.0f} V)**. "
                    "Confirme que el inversor seleccionado es **híbrido** y soporta ese rango de voltaje."
                )

            # 4. Batería LV (≤ 80 V) con híbrido que normalmente requiere HV
            # Growatt SPH/SPA, Huawei SUN2000, Sungrow SH, Solax X-Hybrid solo aceptan
            # bancos de alta tensión (100–550 V). Una batería de 48 V no es compatible.
            _hv_only_heuristic = any(x in inv_lower for x in
                                     ["sph", "spa", "sun2000", "sungrow", "sh-", "x-hybrid", "solax"])
            if tipo_inv and bat_v and bat_v <= 80 and not bat_v_min and _hv_only_heuristic:
                motivos.append(
                    f"La batería es de **baja tensión ({bat_v:.0f} V)** y **`{inv_nom}`** "
                    "normalmente requiere bancos de **alta tensión (100–550 V)**. "
                    "Verifique el rango de tensión DC de batería en la ficha técnica del inversor."
                )

            # 5. Inversor híbrido pero la batería no tiene voltaje definido en el catálogo
            if tipo_inv and not bat_v and not motivos:
                motivos_advertencia = [
                    "La batería **no tiene voltaje definido** en el catálogo. "
                    "No es posible verificar la compatibilidad de tensión con el inversor. "
                    "Agregue el campo `Voltaje Nominal (V)` en la hoja `Catalogo_Baterias` del Excel."
                ]
                return "warning", (
                    f"⚠️ **Inversor híbrido detectado ({inv_nom})** pero sin datos suficientes:  \n"
                    + "\n".join(f"- {m}" for m in motivos_advertencia)
                )

            if motivos:
                return "error", "🔴 **Incompatibilidad detectada:**\n" + "\n".join(f"- {m}" for m in motivos)
            elif tipo_inv and bat_v:
                if bat_v_min and bat_v_max:
                    return "ok", (
                        f"✅ Inversor híbrido · Voltaje batería **{bat_v:.0f} V** ✓ "
                        f"dentro del rango admitido **{bat_v_min:.0f}–{bat_v_max:.0f} V**"
                    )
                return "ok", (
                    f"✅ Inversor híbrido detectado (**{inv_nom}**) · Voltaje batería {bat_v:.0f} V  \n"
                    "*(Rango DC de batería no definido en el catálogo — verifique la ficha del inversor.)*"
                )
            elif not _inv_dim and not inv_nom:
                return "warning", (
                    "ℹ️ Selecciona el inversor en **Página 4 › Dimensionamiento** para "
                    "verificar la compatibilidad antes de dimensionar."
                )
            else:
                return "warning", (
                    f"⚠️ No se pudo determinar el tipo de **`{inv_nom}`** automáticamente.  \n"
                    + (f"Voltaje de batería: **{bat_v:.0f} V**.  \n" if bat_v else "")
                    + "Confirme en la ficha del inversor que tiene **puerto DC para batería** "
                    "y que el rango de tensión es compatible."
                )

        _compat_estado, _compat_msg = _check_compatibilidad(bat, _inv_dim, _inv_nombre)
        if _compat_estado == "error":
            st.error(_compat_msg)
        elif _compat_estado == "warning":
            st.warning(_compat_msg)
        else:
            st.success(_compat_msg)

        # Ficha técnica
        with st.expander("📋 Ficha técnica del modelo seleccionado"):
            ficha = {
                "Capacidad (kWh)":      bat.get("capacidad_kWh", "—"),
                "Potencia (kW)":        bat.get("potencia_kW", "—"),
                "Voltaje nominal (V)":  bat.get("voltaje_V", "—"),
                "DoD máximo (%)":       bat.get("dod_pct", "—"),
                "Ciclos de vida":       bat.get("ciclos_vida", "—"),
                "Eficiencia RTE (%)":   bat.get("eta_rte_pct", "—"),
                "Tecnología":           bat.get("tipo", "—"),
                "Costo unitario (USD)": f"${bat.get('costo_usd', 0):,.0f}" if bat.get("costo_usd") else "—",
                "Garantía (años)":      bat.get("garantia_anos", "—"),
            }
            if _inv_nombre:
                ficha["Inversor del proyecto"] = _inv_nombre
            st.table(pd.DataFrame(ficha.items(), columns=["Parámetro", "Valor"]))

        usa_bateria = st.checkbox("✅ Incluir batería en el balance energético", value=True)

with col_b2:
    st.subheader("Parámetros de diseño")

    # Consumo diario — tomarlo de session_state o calcular desde anual
    consumo_diario_default = round(e_ac_anual / 365, 1) if e_ac_anual > 0 else 30.0
    E_consumo_diario = st.number_input(
        "Consumo diario del edificio (kWh/día)",
        min_value=1.0,
        max_value=5000.0,
        value=float(st.session_state.get("consumo_diario_kWh", consumo_diario_default)),
        step=1.0,
        help="Promedio diario. Si tiene la factura mensual, divida por 30.",
        key="consumo_diario_kWh",
    )

    autonomia_h = st.slider(
        "Autonomía deseada (horas sin sol / red)",
        min_value=1,
        max_value=48,
        value=int(st.session_state.get("autonomia_baterias_h", 4)),
        step=1,
        key="autonomia_baterias_h",
        help="Horas que la batería debe cubrir sin producción solar ni red. "
             "Valor típico: 4–8 h (respaldo nocturno). "
             "24 h = autonomía completa 1 día.",
    )

if tiene_catalogo and st.button("▶️ Dimensionar batería", type="primary"):
    if not bat.get("capacidad_kWh"):
        st.error("❌ La batería seleccionada no tiene capacidad definida en el catálogo.")
    else:
        dim = dimensionar_bateria(bat, E_consumo_diario, autonomia_h)
        if "error" in dim:
            st.error(f"❌ {dim['error']}")
        else:
            st.session_state["bateria_dim"] = dim
            st.session_state["bateria_nombre"] = bat_sel
            st.session_state["bateria_dict"] = bat
            st.session_state["bateria_ok"] = True

# Mostrar resultado del dimensionamiento
dim_res = st.session_state.get("bateria_dim")
if dim_res and not dim_res.get("error"):
    st.success(f"✅ Dimensionamiento calculado — {st.session_state.get('bateria_nombre','')}")
    bat_nom = st.session_state.get("bateria_nombre", "—")

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Unidades requeridas", dim_res["N_baterias"])
    col_r2.metric("Capacidad instalada", f"{dim_res['C_instalada_kWh']:.1f} kWh")
    col_r3.metric("Capacidad útil (DoD+η)", f"{dim_res['C_util_kWh']:.1f} kWh")
    col_r4.metric("Vida estimada", f"{dim_res['vida_estimada_anos']} años")

    col_r5, col_r6, col_r7, col_r8 = st.columns(4)
    col_r5.metric("DoD real de operación", f"{dim_res['dod_real_pct']:.1f}%",
                  delta=f"Máx: {dim_res['dod_max_pct']}%", delta_color="off")
    col_r6.metric("Eficiencia RTE", f"{dim_res['eta_rte_pct']:.0f}%")
    col_r7.metric("Ciclos garantizados", f"{dim_res['ciclos_vida']:,}")
    if dim_res.get("costo_total_usd"):
        col_r8.metric("Costo total baterías",
                      f"USD {dim_res['costo_total_usd']:,.0f}",
                      delta=f"USD {dim_res['costo_unitario_usd']:,.0f}/unid", delta_color="off")
    else:
        col_r8.metric("Costo total baterías", "No disponible")

    for adv in dim_res.get("advertencias", []):
        st.warning(f"⚠️ {adv}")

    # ── #25 — Check potencia post-dimensionamiento ────────────────────────────
    # Una vez conocido N_baterias, verificar que la potencia total del banco no
    # supere la capacidad del inversor (cuello de botella de carga/descarga).
    _n_bat       = dim_res.get("N_baterias", 1)
    _p_bat_unit  = bat.get("potencia_kW") or 0
    _p_bat_total = _n_bat * _p_bat_unit
    _p_inv_w     = (_inv_dim.get("P_ac_nom_W") or _inv_dim.get("P_dc_max_W") or 0)
    _p_inv_kw    = _p_inv_w / 1000
    if _p_bat_total > 0 and _p_inv_kw > 0:
        _ratio = _p_bat_total / _p_inv_kw
        if _ratio > 1.5:
            st.error(
                f"🔴 **Potencia del banco sobredimensionada:** {_n_bat} × {_p_bat_unit:.1f} kW = "
                f"**{_p_bat_total:.1f} kW** vs inversor **{_p_inv_kw:.1f} kW**.  \n"
                f"El inversor limitará la carga/descarga a {_p_inv_kw:.1f} kW — "
                "considera reducir el número de unidades o usar un inversor de mayor potencia."
            )
        elif _ratio > 1.1:
            st.warning(
                f"⚠️ **Potencia del banco ({_p_bat_total:.1f} kW) supera la del inversor "
                f"({_p_inv_kw:.1f} kW) en {(_ratio-1)*100:.0f}%.** "
                "El inversor será el cuello de botella en picos de carga/descarga."
            )
        else:
            st.info(
                f"⚡ Potencia del banco: **{_p_bat_total:.1f} kW** "
                f"({_n_bat} × {_p_bat_unit:.1f} kW) — "
                f"dentro de la capacidad del inversor ({_p_inv_kw:.1f} kW)."
            )

    with st.expander("📐 Tabla de dimensionamiento detallada"):
        tabla_dim = {
            "Parámetro":  [
                "Modelo seleccionado", "Capacidad unitaria (kWh)", "Número de unidades",
                "Capacidad instalada total (kWh)", "Capacidad útil aprovechable (kWh)",
                "DoD real de operación (%)", "DoD máximo del fabricante (%)",
                "Eficiencia round-trip (%)", "Ciclos de vida garantizados",
                "Vida estimada de operación (años)", "Costo total baterías (USD)"
            ],
            "Valor": [
                bat_nom,
                dim_res["cap_unitaria_kWh"],
                dim_res["N_baterias"],
                dim_res["C_instalada_kWh"],
                dim_res["C_util_kWh"],
                f"{dim_res['dod_real_pct']:.1f}%",
                f"{dim_res['dod_max_pct']:.0f}%",
                f"{dim_res['eta_rte_pct']:.0f}%",
                f"{dim_res['ciclos_vida']:,}",
                dim_res["vida_estimada_anos"],
                f"USD {dim_res['costo_total_usd']:,.0f}" if dim_res.get("costo_total_usd") else "—",
            ],
        }
        st.table(pd.DataFrame(tabla_dim))

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# B-7 — Balance energético mensual + Clasificación
# ══════════════════════════════════════════════════════════════════════════════
st.header("📊 B-7 — Balance Energético Mensual y Clasificación")

# ── Sección consumo ──────────────────────────────────────────────────────────
st.subheader("1️⃣ Perfil de consumo del edificio")

modo_consumo = st.radio(
    "¿Cómo desea ingresar el consumo?",
    ["Consumo anual + perfil típico", "Ingresar 12 valores mensuales manualmente"],
    horizontal=True,
    key="modo_consumo_b7",
)

if modo_consumo == "Consumo anual + perfil típico":
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        consumo_anual_input = st.number_input(
            "Consumo anual total (kWh/año)",
            min_value=100.0,
            max_value=10_000_000.0,
            value=float(st.session_state.get("consumo_anual_edificio_kWh",
                        max(e_ac_anual * 1.2, 10000.0))),
            step=500.0,
            key="consumo_anual_edificio_kWh",
            help="Puede obtenerlo sumando 12 meses de facturas de energía.",
        )
    with col_c2:
        perfil_sel = st.selectbox(
            "Perfil de distribución mensual",
            list(PERFILES_TIPICOS.keys()),
            key="perfil_consumo_tipico",
            help="Distribución estacional del consumo. 'Uniforme' si no sabe.",
        )
    consumo_mensual_list = distribuir_consumo_anual(consumo_anual_input, perfil_sel)

else:
    st.info("Ingrese el consumo de cada mes (kWh). Puede basarse en facturas históricas.")
    cols_mes = st.columns(6)
    consumo_mensual_list = []
    defaults_mens = st.session_state.get(
        "consumo_mensual_manual",
        [round(max(e_ac_anual * 1.2, 10000) / 12, 0)] * 12
    )
    for i, mes in enumerate(MESES):
        col = cols_mes[i % 6]
        val = col.number_input(
            mes, min_value=0.0, max_value=500_000.0,
            value=float(defaults_mens[i]),
            step=100.0, key=f"cons_mes_{i}"
        )
        consumo_mensual_list.append(val)
    st.session_state["consumo_mensual_manual"] = consumo_mensual_list

# Vista previa del consumo
with st.expander("👁️ Vista previa del perfil de consumo"):
    df_cons_prev = pd.DataFrame({
        "Mes": MESES,
        "Consumo (kWh)": [round(v, 0) for v in consumo_mensual_list],
    })
    fig_cons = px.bar(df_cons_prev, x="Mes", y="Consumo (kWh)",
                      title="Perfil de consumo mensual",
                      color_discrete_sequence=["#3498db"])
    fig_cons.update_layout(height=280, margin=dict(t=40, b=20))
    st.plotly_chart(fig_cons, use_container_width=True)
    st.caption(f"Total anual: **{sum(consumo_mensual_list):,.0f} kWh/año**")

# ── Calcular balance ─────────────────────────────────────────────────────────
st.subheader("2️⃣ Calcular balance")

if st.button("▶️ Calcular balance energético mensual", type="primary",
             disabled=(df_m_prod is None)):
    if df_m_prod is None:
        st.error("❌ No hay datos de producción mensual. Complete primero la Página 6.")
    else:
        _bat_dim_activo = (st.session_state.get("bateria_dim")
                           if (usa_bateria if tiene_catalogo else False)
                              and st.session_state.get("bateria_ok")
                           else None)
        try:
            df_bal = balance_mensual(df_m_prod, consumo_mensual_list, _bat_dim_activo)
            metr   = metricas_balance(df_bal)
            clase  = clasificar_energia(metr["fraccion_solar_pct"])

            st.session_state["balance_mensual_df"]       = df_bal
            st.session_state["balance_metricas"]         = metr
            st.session_state["clasificacion_energetica"] = clase
            st.session_state["fraccion_solar_pct"]       = metr["fraccion_solar_pct"]
            st.session_state["consumo_anual_edificio_kWh_calc"] = metr["E_consumo_anual_kWh"]
            st.session_state["balance_ok"]               = True
            st.success("✅ Balance calculado correctamente")
        except Exception as e:
            st.error(f"❌ Error en el cálculo: {e}")

# ── Mostrar resultados ───────────────────────────────────────────────────────
df_bal  = st.session_state.get("balance_mensual_df")
metr    = st.session_state.get("balance_metricas")
clase   = st.session_state.get("clasificacion_energetica")

if df_bal is not None and metr and clase:

    # ── Clasificación energética ────────────────────────────────────────────
    st.divider()
    st.subheader("3️⃣ Clasificación energética del edificio")

    col_cl1, col_cl2 = st.columns([1, 2])
    with col_cl1:
        color = clase["color_hex"]
        clase_letra = clase["clase"]
        frac = clase["fraccion_solar_pct"]
        st.markdown(
            f"""
            <div style="
                background:{color}22;
                border: 3px solid {color};
                border-radius: 16px;
                padding: 24px;
                text-align: center;
            ">
                <div style="font-size:64px; font-weight:900; color:{color};">
                    {clase_letra}
                </div>
                <div style="font-size:18px; font-weight:600; color:{color}; margin-top:4px;">
                    {clase['emoji']} {clase['descripcion']}
                </div>
                <div style="font-size:28px; font-weight:700; margin-top:12px;">
                    {frac:.1f}%
                </div>
                <div style="font-size:13px; color:#666;">
                    fracción solar (% consumo cubierto)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_cl2:
        st.markdown("**Tabla de clasificaciones energéticas**")
        df_clases = tabla_clasificaciones()
        # Resaltar la fila activa
        def _highlight_row(row):
            if row["Clase"].endswith(clase_letra) or clase_letra in row["Clase"]:
                return [f"background-color:{color}33; font-weight:bold"] * len(row)
            return [""] * len(row)
        st.dataframe(df_clases.style.apply(_highlight_row, axis=1),
                     use_container_width=True, hide_index=True)

    # ── KPIs anuales ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("4️⃣ Indicadores anuales del balance")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Producción solar",
              f"{metr['E_solar_anual_kWh']:,.0f} kWh/año")
    k2.metric("Consumo edificio",
              f"{metr['E_consumo_anual_kWh']:,.0f} kWh/año")
    k3.metric("Autoconsumo solar",
              f"{metr['E_autoconsumo_anual_kWh']:,.0f} kWh/año",
              delta=f"{metr['fraccion_solar_pct']:.1f}% del consumo")
    k4.metric("Excedente exportado",
              f"{metr['E_exportacion_anual_kWh']:,.0f} kWh/año",
              delta=f"{metr['tasa_autoconsumo_pct']:.1f}% autoc. solar")
    k5.metric("Déficit residual",
              f"{metr['E_deficit_anual_kWh']:,.0f} kWh/año",
              delta=f"Ratio solar/consumo: {metr['ratio_solar_consumo']:.2f}x",
              delta_color="off")

    if metr.get("E_bateria_total_kWh", 0) > 0:
        st.info(
            f"🔋 **Contribución batería:** {metr['E_bateria_total_kWh']:,.0f} kWh/año "
            f"(energía descargada que cubre consumo nocturno/déficit)"
        )

    # ── Gráfico de balance mensual ───────────────────────────────────────────
    st.divider()
    st.subheader("5️⃣ Balance mensual — Producción vs Consumo")

    fig = go.Figure()

    # Barras apiladas del autoconsumo
    fig.add_trace(go.Bar(
        name="Autoconsumo directo (solar→edificio)",
        x=df_bal["mes"], y=df_bal["autoconsumo_directo_kWh"],
        marker_color="#27ae60",
        hovertemplate="%{y:,.0f} kWh<extra>Autoconsumo directo</extra>",
    ))
    if df_bal["E_bateria_descargada_kWh"].sum() > 0:
        fig.add_trace(go.Bar(
            name="Batería → edificio",
            x=df_bal["mes"], y=df_bal["E_bateria_descargada_kWh"],
            marker_color="#2ecc71",
            hovertemplate="%{y:,.0f} kWh<extra>Batería → edificio</extra>",
        ))
    fig.add_trace(go.Bar(
        name="Déficit (de la red)",
        x=df_bal["mes"], y=df_bal["deficit_neto_kWh"],
        marker_color="#e74c3c",
        hovertemplate="%{y:,.0f} kWh<extra>Déficit (red)</extra>",
    ))
    fig.add_trace(go.Bar(
        name="Excedente exportado",
        x=df_bal["mes"], y=df_bal["exportacion_kWh"],
        marker_color="#f39c12", opacity=0.7,
        hovertemplate="%{y:,.0f} kWh<extra>Excedente exportado</extra>",
    ))

    # Línea de consumo total
    fig.add_trace(go.Scatter(
        name="Consumo edificio",
        x=df_bal["mes"], y=df_bal["E_consumo_kWh"],
        mode="lines+markers",
        line=dict(color="#2c3e50", width=2.5, dash="dot"),
        marker=dict(size=7),
        hovertemplate="%{y:,.0f} kWh<extra>Consumo</extra>",
    ))

    # Línea de producción solar
    fig.add_trace(go.Scatter(
        name="Producción solar (E_ac)",
        x=df_bal["mes"], y=df_bal["E_solar_kWh"],
        mode="lines+markers",
        line=dict(color="#e67e22", width=2.5),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="%{y:,.0f} kWh<extra>Producción solar</extra>",
    ))

    fig.update_layout(
        barmode="stack",
        title="Balance energético mensual — Autoconsumo · Déficit · Excedente",
        xaxis_title="Mes",
        yaxis_title="Energía (kWh)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        margin=dict(t=80, b=40),
        plot_bgcolor="white",
    )
    fig.update_xaxes(gridcolor="#f0f0f0")
    fig.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig, use_container_width=True)

    # ── Gráfico fracción solar mensual ──────────────────────────────────────
    fig2 = go.Figure()

    colores_bar = []
    for v in df_bal["fraccion_solar_pct"]:
        if v >= 90:   colores_bar.append("#2ecc71")
        elif v >= 75: colores_bar.append("#27ae60")
        elif v >= 50: colores_bar.append("#f39c12")
        elif v >= 25: colores_bar.append("#e67e22")
        else:         colores_bar.append("#e74c3c")

    fig2.add_trace(go.Bar(
        x=df_bal["mes"],
        y=df_bal["fraccion_solar_pct"],
        marker_color=colores_bar,
        text=[f"{v:.0f}%" for v in df_bal["fraccion_solar_pct"]],
        textposition="outside",
        name="Fracción solar mensual",
        hovertemplate="%{y:.1f}%<extra>Fracción solar</extra>",
    ))

    # Líneas de clasificación
    for umbral, clase_l, _, color_l, _ in [
        (90, "A+", "", "#2ecc71", ""),
        (75, "A",  "", "#27ae60", ""),
        (50, "B",  "", "#f39c12", ""),
        (25, "C",  "", "#e67e22", ""),
    ]:
        fig2.add_hline(
            y=umbral, line_dash="dash", line_color=color_l, line_width=1.5,
            annotation_text=f" {clase_l} ({umbral}%)",
            annotation_position="right",
        )

    fig2.update_layout(
        title="Fracción solar mensual — % del consumo cubierto por solar",
        xaxis_title="Mes",
        yaxis_title="Fracción solar (%)",
        yaxis=dict(range=[0, 115]),
        height=380,
        plot_bgcolor="white",
        margin=dict(t=60, b=40),
    )
    fig2.update_xaxes(gridcolor="#f0f0f0")
    fig2.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig2, use_container_width=True)

    # ── Tabla detallada ──────────────────────────────────────────────────────
    with st.expander("📋 Tabla detallada del balance mensual"):
        df_show = df_bal[[
            "mes", "E_solar_kWh", "E_consumo_kWh",
            "autoconsumo_directo_kWh", "E_bateria_descargada_kWh",
            "autoconsumo_total_kWh", "deficit_neto_kWh",
            "exportacion_kWh", "fraccion_solar_pct",
        ]].copy()
        df_show.columns = [
            "Mes", "Solar (kWh)", "Consumo (kWh)",
            "Autoconsumo directo", "Batería→edificio",
            "Autoconsumo total", "Déficit (red)", "Exportado", "Fracción solar (%)",
        ]
        # Fila de totales
        totales = {
            "Mes": "TOTAL",
            "Solar (kWh)": df_show["Solar (kWh)"].sum(),
            "Consumo (kWh)": df_show["Consumo (kWh)"].sum(),
            "Autoconsumo directo": df_show["Autoconsumo directo"].sum(),
            "Batería→edificio": df_show["Batería→edificio"].sum(),
            "Autoconsumo total": df_show["Autoconsumo total"].sum(),
            "Déficit (red)": df_show["Déficit (red)"].sum(),
            "Exportado": df_show["Exportado"].sum(),
            "Fracción solar (%)": round(metr["fraccion_solar_pct"], 1),
        }
        df_show = pd.concat([df_show, pd.DataFrame([totales])], ignore_index=True)
        st.dataframe(df_show.style.format({
            "Solar (kWh)": "{:,.0f}",
            "Consumo (kWh)": "{:,.0f}",
            "Autoconsumo directo": "{:,.0f}",
            "Batería→edificio": "{:,.0f}",
            "Autoconsumo total": "{:,.0f}",
            "Déficit (red)": "{:,.0f}",
            "Exportado": "{:,.0f}",
            "Fracción solar (%)": "{:.1f}%",
        }), use_container_width=True, hide_index=True)

    # ── Flujo de ahorro estimado ─────────────────────────────────────────────
    tarifa = float(st.session_state.get(
        "tarifa_cop_kwh",                        # clave canónica (Proyecto/Financiero)
        st.session_state.get("tarifa_cop_kWh", 650.0)  # fallback legacy
    ))
    if tarifa > 0 and metr["E_autoconsumo_anual_kWh"] > 0:
        ahorro_anual_cop = metr["E_autoconsumo_anual_kWh"] * tarifa
        tipo_cambio = float(st.session_state.get("tipo_cambio", 4100.0))
        ahorro_anual_usd = ahorro_anual_cop / tipo_cambio
        st.divider()
        st.subheader("6️⃣ Estimación de ahorro en factura")
        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("Autoconsumo anual",
                      f"{metr['E_autoconsumo_anual_kWh']:,.0f} kWh")
        col_a2.metric("Ahorro anual estimado",
                      f"COP {ahorro_anual_cop / 1e6:,.1f}M",
                      delta=f"USD {ahorro_anual_usd:,.0f}")
        col_a3.metric("Ahorro mensual promedio",
                      f"COP {ahorro_anual_cop / 12 / 1e3:,.0f}K/mes")
        st.caption(
            f"Cálculo: {metr['E_autoconsumo_anual_kWh']:,.0f} kWh × "
            f"{tarifa:,.0f} COP/kWh = {ahorro_anual_cop/1e6:.2f} M COP/año. "
            "Tarifa y TRM tomadas de la página Financiero."
        )

    # ── Guardar en session_state para Financiero y Reporte ──────────────────
    st.session_state["balance_ok"]               = True
    st.session_state["fraccion_solar_pct"]       = metr["fraccion_solar_pct"]
    st.session_state["clasificacion_energetica"] = clase
    st.session_state["balance_metricas"]         = metr

    # Nota de integración con Financiero
    with st.expander("🔗 Integración con otras páginas"):
        st.markdown("""
| Página | Dato que recibe de esta página |
|---|---|
| **7 — Financiero** | `fraccion_solar_pct`, `E_autoconsumo_anual_kWh` para calcular LCOE con storage |
| **8 — Presupuesto** | `bateria_dim` → N baterías × costo unitario se suman al CAPEX |
| **10 — Reporte PDF** | Clase energética A+/A/B/C/D, tabla de balance, KPIs de autoconsumo |

Los valores se propagan automáticamente vía `session_state` cuando calcule en esta página primero.
        """)

else:
    if prod_ok and df_m_prod is not None:
        st.info("👆 Configure el perfil de consumo y haga clic en **Calcular balance energético mensual**")
