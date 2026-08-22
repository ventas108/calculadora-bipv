"""Página 5 — Mismatch y pérdidas de sombreado."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from calculos.mismatch import (
    calcular_sombreado_horizonte,
    calcular_mismatch_orientacion,
    cascada_perdidas,
    factor_global_perdidas,
)
from calculos.mismatch_bypass import (
    cargar_csv_fs,
    alinear_fs_con_tmy,
    combinar_fs_con_horizonte,
    cobertura_csv,
    simular_bypass_horario,
    estadisticas_fs,
)
from calculos.solar import calcular_poa, ORIENTACIONES, posiciones_solares_representativas
from datos.ciudades_colombia import CIUDADES
from calculos.tz_utils import utc_offset_latam, tz_label
from datos.tecnologias_bipv import MODULOS_BIPV
from calculos.escenarios_fase4 import (
    BASE_COMPONENTS,
    capturar_base_comparacion,
    construir_definicion_escenarios,
    validar_definicion_escenarios,
)
from calculos.ejecutor_escenarios import ejecutar_escenarios
from calculos.metricas_escenarios import (
    comparar_resultados_escenarios,
    metricas_electricas,
    metricas_solares,
)

st.set_page_config(page_title="Mismatch — BIPV", page_icon="🔀", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página
st.title("🔀 Mismatch y Pérdidas de Sombreado")
st.caption(
    "Sombreado de horizonte · Mismatch por orientación múltiple · "
    "Fabricación · Suciedad · Cableado DC"
)

# ── Alarma de validación SDM (calculada en 📐 Dimensionamiento) ────────────────
# La simulación de bypass diodes por sombra parcial (calculos/mismatch_bypass.py,
# más abajo en esta página) SÍ usa los mismos parámetros del modelo de diodo
# que Motor IV valida (I_L_ref, I_o_ref, R_s, R_sh_ref, a_ref) -- si esa
# validación falló para el panel activo, la pérdida por bypass calculada aquí
# hereda el mismo desajuste. La cascada básica de pérdidas (mismatch.py) NO
# depende del SDM, pero no se puede saber de antemano si el usuario va a usar
# también la simulación de bypass diodes en esta misma página.
if (
    st.session_state.get("motor_iv_validacion_ok") is False
    and st.session_state.get("motor_iv_validacion_panel") == st.session_state.get("panel_nombre_dim")
):
    from calculos.modelo_iv import explicar_fallo_validacion_sdm
    st.error(explicar_fallo_validacion_sdm(
        st.session_state.get("motor_iv_validacion_panel", "el panel activo"),
        st.session_state.get("motor_iv_validacion_detalle", {}),
    ))

# ── Prerequisitos ─────────────────────────────────────────────────────────────
if not st.session_state.get("recurso_solar_ok"):
    st.warning("⚠️ Primero ejecuta ☀️ Recurso Solar para obtener el TMY y la POA del sitio.")
    st.stop()

tmy       = st.session_state["tmy_df"]
ciudad    = st.session_state.get("tmy_ciudad", "—")
c         = CIUDADES[ciudad]
lat, lon, alt_m = c["lat"], c["lon"], c["alt_m"]
_tz_off_mm = st.session_state.get("utc_offset_local", utc_offset_latam(lat, lon))
_tz_lbl_mm = tz_label(_tz_off_mm)
tilt_def  = st.session_state.get("tilt_fachada", 90)
az_def    = st.session_state.get("azimuth_fachada", 0)
or_label  = st.session_state.get("orientacion_label", "Norte (0°)")

# ── Prioridad POA: multi-superficie > superficie simple ───────────────────────
_multisup_ok  = st.session_state.get("multisup_activo", False)
_poa_multisup = st.session_state.get("poa_df_multisup")
_ms_area      = st.session_state.get("area_total_multisup", 0.0)
_ms_desglose  = st.session_state.get("multisup_desglose", [])
_ms_nsups     = len(_ms_desglose)

if _multisup_ok and _poa_multisup is not None and not _poa_multisup.empty:
    poa_base  = _poa_multisup                                    # clave exclusiva — no toca poa_df
    poa_anual = float(poa_base["poa_global"].sum() / 1000.0)
    st.info(
        f"🏗️ **Modo multi-superficie activo** — POA combinada ponderada por área: "
        f"**{poa_anual:,.0f} kWh/m²/año** | {_ms_nsups} superficie(s) · "
        f"Área total: **{_ms_area:.1f} m²**. "
        "La cascada de pérdidas se aplica al sistema completo."
    )
else:
    poa_base  = st.session_state["poa_df"]
    poa_anual = st.session_state.get("poa_anual_kWh_m2", 0.0)
    st.info(
        f"📍 **{ciudad}** — POA fachada {or_label} / {tilt_def}°: "
        f"**{poa_anual:,.0f} kWh/m²/año**"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 4.2 — BASE ÚNICA DE COMPARACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🔒 Fase 2 — Base única de comparación")
st.caption(
    "Todos los escenarios deben reutilizar exactamente la misma ubicación, TMY, "
    "horas UTC, fachadas/puntos, panel, configuración eléctrica, temperatura, "
    "modelo óptico y reglas de agregación."
)

_fase4_actual = st.session_state.get("escenarios_fase4", {})
_base_live_f4 = capturar_base_comparacion(st.session_state)
_base_guardada_f4 = _fase4_actual.get("base_comparacion")
_fase4_nombre_default = (
    _fase4_actual.get("nombre_proyecto")
    or st.session_state.get("nombre_proyecto")
    or "Proyecto BIPV Bogotá Teusaquillo"
)
_fase4_fuentes = _fase4_actual.get("politica_fuentes_actual", {}).get(
    "fuentes_declaradas", ["horizonte", "sketchup"]
)

with st.container(border=True):
    _fase4_nombre = st.text_input(
        "Proyecto al que pertenece la comparación",
        value=_fase4_nombre_default,
        key="fase4_nombre_proyecto",
    )
    _f4c1, _f4c2 = st.columns(2)
    with _f4c1:
        _fase4_horizonte = st.checkbox(
            "Usar perfil de horizonte",
            value="horizonte" in _fase4_fuentes,
            key="fase4_fuente_horizonte",
            help="Perfil editado en esta página de Mismatch.",
        )
    with _f4c2:
        _fase4_sketchup = st.checkbox(
            "Usar modelo/CSV de SketchUp",
            value="sketchup" in _fase4_fuentes,
            key="fase4_fuente_sketchup",
            help="Sombreado horario proveniente del modelo 3D.",
        )
    _fase4_tipo = st.selectbox(
        "Tipo de optimización permitido",
        options=["paneles", "obstaculos", "ambos", "por_definir"],
        index=["paneles", "obstaculos", "ambos", "por_definir"].index(
            _fase4_actual.get("escenarios", {})
            .get("optimizada", {})
            .get("tipo_optimizacion", "paneles")
        ),
        format_func=lambda valor: {
            "paneles": "Ubicación, separación o distribución de paneles",
            "obstaculos": "Reducir, retirar o reubicar obstáculos",
            "ambos": "Paneles y obstáculos",
            "por_definir": "Por definir",
        }[valor],
        key="fase4_tipo_optimizacion",
    )

    _fuentes_disponibles = {
        "horizonte": bool(
            st.session_state.get("sombra_ok")
            and st.session_state.get("puntos_horiz")
        ),
        "sketchup": bool(
            st.session_state.get("csv_fs_ok")
            or st.session_state.get("csv_fs_sketchup_bytes")
            or st.session_state.get("sk_df_fs") is not None
        ),
    }
    _estado_h = "cargado" if _fuentes_disponibles["horizonte"] else "pendiente"
    _estado_s = "cargado" if _fuentes_disponibles["sketchup"] else "pendiente"
    st.caption(
        f"Disponibilidad actual: horizonte **{_estado_h}** · "
        f"SketchUp **{_estado_s}**. La declaración del escenario puede hacerse "
        "antes de recalcular ambas fuentes."
    )

    if st.button(
        "💾 Guardar definición y congelar base",
        type="primary",
        key="fase4_guardar_definicion",
    ):
        try:
            _definicion_fase4 = construir_definicion_escenarios(
                nombre_proyecto=_fase4_nombre,
                fuente_horizonte=_fase4_horizonte,
                fuente_sketchup=_fase4_sketchup,
                tipo_optimizacion=_fase4_tipo,
                panel_nombre=st.session_state.get("panel_nombre_dim"),
                inversor_nombre=st.session_state.get("inversor_nombre_dim"),
            )
            _definicion_fase4["fuentes_disponibles"] = _fuentes_disponibles
            _definicion_fase4["base_comparacion"] = _base_live_f4
            validar_definicion_escenarios(_definicion_fase4)
            st.session_state["escenarios_fase4"] = _definicion_fase4
            st.session_state["fase4_definicion_ok"] = True
            if _base_live_f4["lista_para_comparar"]:
                st.session_state["fase4_base_comparacion_ok"] = True
                st.success(
                    "✅ Definición guardada y base única congelada. "
                    f"ID: `{_base_live_f4['base_id'][:12]}`"
                )
                if _base_live_f4.get("eta_inversor") is None:
                    st.warning(
                        "⚠️ La base se congeló sin la eficiencia del inversor (η) "
                        "porque aún no se ha corrido 📊 Producción en esta sesión. "
                        "Corre Producción y vuelve a congelar la base antes de "
                        "ejecutar los escenarios."
                    )
            else:
                st.session_state["fase4_base_comparacion_ok"] = False
                st.warning(
                    "⚠️ Definición guardada como borrador. La comparación queda "
                    "bloqueada hasta completar la base única."
                )
        except ValueError as _e_fase4:
            st.error(f"❌ No se pudo guardar la definición: {_e_fase4}")

_definicion_fase4 = st.session_state.get("escenarios_fase4")
if _definicion_fase4:
    _esc_f4 = _definicion_fase4["escenarios"]
    _actual_f4 = _esc_f4["actual"]
    _opt_f4 = _esc_f4["optimizada"]
    st.markdown("#### Estado de los escenarios")
    _ec1, _ec2, _ec3 = st.columns(3)
    _ec1.success("**Referencia**\n\nSin obstáculos · FS geométrico = 0")
    if _actual_f4["estado"] == "definido_reconciliacion_pendiente":
        if st.session_state.get("bypass_horizonte_incluido"):
            _ec2.success(
                "**Situación actual**\n\n"
                "Definida · horizonte + modelo 3D combinados en el bypass "
                "(máximo hora a hora)"
            )
        else:
            _ec2.warning(
                "**Situación actual**\n\n"
                "Definida · reconciliar horizonte + SketchUp antes de comparar "
                "(actívalo en la sección del bypass)"
            )
    else:
        _ec2.success("**Situación actual**\n\nFuente de sombreado definida")
    _ec3.info(
        "**Alternativa optimizada**\n\n"
        "Pendiente de parámetros de ubicación/separación/distribución"
        if _opt_f4["estado"] == "pendiente_parametros"
        else "**Alternativa optimizada**\n\nDefinida"
    )
    st.caption(
        "🔒 Invariantes: misma ubicación, TMY, timestamps UTC, fachadas/puntos, "
        "panel, inversor, configuración eléctrica, temperatura, modelo óptico "
        "y agregación."
    )

_base_guardada_f4 = _definicion_fase4.get("base_comparacion") if _definicion_fase4 else None
if _base_guardada_f4:
    _base_cambio_f4 = (
        _base_guardada_f4.get("base_id") != _base_live_f4.get("base_id")
    )
    if _base_cambio_f4:
        st.error(
            "🚫 La base única cambió desde que fue congelada. No compares estos "
            "escenarios hasta volver a guardarla."
        )
        st.session_state["fase4_base_comparacion_ok"] = False
    elif _base_guardada_f4.get("lista_para_comparar") is True:
        st.success(
            f"✅ Base única lista para comparar · ID `{_base_guardada_f4['base_id'][:12]}`"
        )
        _component_labels_f4 = {
            "ubicacion": "Ubicación",
            "tmy": "TMY",
            "timestamps_utc": "Timestamps UTC",
            "poa_base": "POA base",
            "fachadas_y_puntos": "Fachadas y puntos",
            "panel": "Panel",
            "configuracion_electrica": "Configuración eléctrica",
            "temperatura_y_modelo_optico": "Temperatura y modelo óptico",
            "agregacion": "Agregación mensual/anual",
        }
        with st.expander("Ver componentes congelados de la base", expanded=False):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Componente": _component_labels_f4[key],
                            "Estado": "✅ Igual para todos los escenarios",
                            "Huella": value["huella"][:16],
                        }
                        for key, value in _base_guardada_f4["componentes"].items()
                        if key in BASE_COMPONENTS
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )
    else:
        st.warning(
            "⚠️ Base guardada como borrador. Faltan: "
            + "; ".join(_base_guardada_f4.get("faltantes", []))
        )

# ═══════════════════════════════════════════════════════════════════════════════
# AUDITORÍA — MÉTRICAS SOLARES VS. ELÉCTRICAS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📊 Métricas separadas del escenario actual")
st.caption(
    "Las métricas solares describen irradiancia y sombreado. Las eléctricas "
    "describen energía DC/AC. Una pérdida de POA no se presenta como pérdida "
    "equivalente de kWh AC."
)

_df_metricas_fs = st.session_state.get("df_fs_raw")
_fachada_m = st.session_state.get("bypass_fachada_sel_val")
if isinstance(_df_metricas_fs, pd.DataFrame) and _fachada_m and "fachada" in _df_metricas_fs.columns:
    _df_metricas_fs = _df_metricas_fs[
        _df_metricas_fs["fachada"] == _fachada_m
    ].copy()

_opciones_agregacion_fs = {
    "auto": "Automático (módulos → área → potencia)",
    "simple": "Promedio simple por punto",
    "modulos": "Ponderado por número de módulos",
    "area": "Ponderado por área activa",
    "potencia": "Ponderado por potencia instalada",
}
_modo_agregacion_fs = st.selectbox(
    "⚖️ Agregación espacial de fachada / fila / punto",
    options=list(_opciones_agregacion_fs),
    format_func=lambda modo: _opciones_agregacion_fs[modo],
    index=0,
    key="bypass_modo_agregacion",
    help=(
        "Automático prioriza número de módulos, luego área activa y finalmente "
        "potencia instalada. Si no existe un peso válido, usa promedio simple "
        "y deja una advertencia auditable."
    ),
)

with st.expander("⚙️ Configuración de horas y meses críticos", expanded=False):
    st.caption(
        "El diagnóstico no cambia la producción anual. Una hora solo es crítica "
        "si tiene POA suficiente y una pérdida geométrica mínima; los meses se "
        "ordenan por POA perdida acumulada."
    )
    _cc1, _cc2, _cc3, _cc4 = st.columns(4)
    _crit_poa_min = _cc1.number_input(
        "POA mínima (W/m²)",
        min_value=0.0,
        max_value=2000.0,
        value=100.0,
        step=10.0,
        key="criticos_irradiancia_minima_wm2",
        help="Evita marcar madrugada o noche con POA casi nula.",
    )
    _crit_fs_min = _cc2.number_input(
        "FS mínimo",
        min_value=0.0,
        max_value=1.0,
        value=0.05,
        step=0.01,
        format="%.2f",
        key="criticos_fs_minimo",
        help="Pérdida geométrica mínima para considerar crítica una hora.",
    )
    _crit_top_horas = _cc3.number_input(
        "Horas a mostrar",
        min_value=1,
        max_value=100,
        value=10,
        step=1,
        key="criticos_top_n_horas",
    )
    _crit_top_meses = _cc4.number_input(
        "Meses a mostrar",
        min_value=1,
        max_value=12,
        value=3,
        step=1,
        key="criticos_top_n_meses",
    )
_configuracion_criticos = {
    "irradiancia_minima_wm2": _crit_poa_min,
    "fs_minimo": _crit_fs_min,
    "top_n_horas": _crit_top_horas,
    "top_n_meses": _crit_top_meses,
}

_fs_metricas = None
_modo_fs_metricas = st.session_state.get("bypass_modo_alineacion", "mensual")
if (
    isinstance(_df_metricas_fs, pd.DataFrame)
    and not _df_metricas_fs.empty
    and "FS_geometrico" in _df_metricas_fs.columns
):
    try:
        _fs_metricas = alinear_fs_con_tmy(
            _df_metricas_fs,
            tmy.index,
            modo=_modo_fs_metricas,
            modo_agregacion=_modo_agregacion_fs,
        )
    except Exception:
        _fs_metricas = None
elif isinstance(st.session_state.get("res_sombra"), dict):
    _mask_m = st.session_state["res_sombra"].get("mascara_sombra")
    if isinstance(_mask_m, pd.Series):
        _fs_metricas = (
            _mask_m.reindex(tmy.index).fillna(False).astype(float)
        )

_poa_ef_m = None
_poa_ef_fuente_m = None
if st.session_state.get("motor_optico_ok"):
    _poa_ef_m = st.session_state.get("poa_efectiva_anual_kWh_m2")
    _poa_ef_fuente_m = "Motor Óptico (IAM + soiling + térmico)"
elif st.session_state.get("poa_efectiva_kWh_m2") is not None:
    _poa_ef_m = st.session_state.get("poa_efectiva_kWh_m2")
    _poa_ef_fuente_m = "Cascada Mismatch (POA, no energía AC)"

_metricas_solares_m = metricas_solares(
    poa_bruta_kWh_m2=poa_anual,
    poa_efectiva_kWh_m2=_poa_ef_m,
    poa_efectiva_fuente=_poa_ef_fuente_m,
    fs_horario=_fs_metricas,
    tmy_index=tmy.index,
    poa_horaria=poa_base["poa_global"] if "poa_global" in poa_base else None,
    res_sombra=st.session_state.get("res_sombra"),
    df_fs=_df_metricas_fs,
    modo_fs=_modo_fs_metricas,
    modo_agregacion_fs=_modo_agregacion_fs,
    configuracion_criticos=_configuracion_criticos,
)
_metricas_electricas_m = metricas_electricas(
    resultado_produccion=st.session_state.get("res_produccion"),
    bypass=st.session_state.get("bypass_result")
    if st.session_state.get("bypass_ok")
    else None,
    mismatch=st.session_state.get("res_mismatch_or"),
    eta_inversor=st.session_state.get("eta_inversor"),
)

with st.container(border=True):
    st.markdown("#### ☀️ Métricas solares")
    _sm1, _sm2, _sm3, _sm4 = st.columns(4)
    _sm1.metric(
        "POA bruta",
        (
            f"{_metricas_solares_m['poa_bruta_kWh_m2']:,.1f} kWh/m²/año"
            if _metricas_solares_m["poa_bruta_kWh_m2"] is not None
            else "—"
        ),
    )
    _sm2.metric(
        "POA efectiva solar",
        (
            f"{_metricas_solares_m['poa_efectiva_kWh_m2']:,.1f} kWh/m²/año"
            if _metricas_solares_m["poa_efectiva_kWh_m2"] is not None
            else "—"
        ),
        help=_metricas_solares_m["poa_efectiva_fuente"] or "Aún no calculada",
    )
    _sm3.metric(
        "FS geométrico",
        f"{_metricas_solares_m['fs_geometrico_ponderado_pct']:.2f}%",
    )
    _sm4.metric(
        "Horas con sombra",
        f"{_metricas_solares_m['horas_con_sombra']:,} h/año",
    )
    _sm5, _sm6, _sm7, _sm8 = st.columns(4)
    _sm5.metric(
        "Pérdida solar de POA",
        (
            f"{_metricas_solares_m['perdida_poa_solar_kWh_m2']:,.1f} kWh/m²/año"
            if _metricas_solares_m["perdida_poa_solar_kWh_m2"] is not None
            else "—"
        ),
        help="No equivale automáticamente a una pérdida de energía AC.",
    )
    _sm6.metric(
        "Meses críticos",
        ", ".join(_metricas_solares_m["meses_criticos"]) or "—",
        help=_metricas_solares_m["criterio_mes_critico"],
    )
    _sm7.metric(
        "Obstáculo responsable",
        _metricas_solares_m["obstaculo_responsable"] or "No identificado",
    )
    _sm8.metric(
        "Mismatch solar",
        (
            f"{_metricas_electricas_m['impacto_mismatch_poa_pct']:.2f}%"
            if _metricas_electricas_m["impacto_mismatch_poa_pct"] is not None
            else "—"
        ),
        help="Impacto de mismatch expresado como POA; no es pérdida AC.",
    )
    _tablas_solares_m = {
        "Pérdida solar por fachada": _metricas_solares_m["por_fachada"],
        "Pérdida solar por fila": _metricas_solares_m["por_fila"],
        "Pérdida solar por punto": _metricas_solares_m["por_punto"],
        "Obstáculos responsables": _metricas_solares_m["por_obstaculo"],
    }
    _aud_agregacion = _metricas_solares_m["agregacion_fs_auditoria"]
    st.caption(
        f"Agregación aplicada: **{_aud_agregacion['etiqueta']}**"
        + (
            f" · columna `{_aud_agregacion['columna_peso']}`"
            if _aud_agregacion["columna_peso"]
            else ""
        )
    )
    for _advertencia_ag in _aud_agregacion["advertencias"]:
        st.warning(f"⚠️ {_advertencia_ag}")
    _horas_criticas_m = _metricas_solares_m["horas_criticas"]
    _meses_criticos_m = _metricas_solares_m["meses_criticos_detalle"]
    if _horas_criticas_m or _meses_criticos_m:
        with st.expander("🔎 Evidencia del diagnóstico crítico", expanded=False):
            st.caption(
                f"{_metricas_solares_m['horas_candidatas_criticas']} horas "
                "superaron los dos umbrales. Se muestran los primeros registros "
                "ordenados por POA perdida."
            )
            if _horas_criticas_m:
                st.dataframe(
                    pd.DataFrame(_horas_criticas_m).rename(
                        columns={
                            "timestamp": "Timestamp",
                            "mes_nombre": "Mes",
                            "hora": "Hora",
                            "poa_Wm2": "POA (W/m²)",
                            "FS_geometrico": "FS geométrico",
                            "poa_perdida_kWh_m2": "POA perdida (kWh/m²)",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
            if _meses_criticos_m:
                st.dataframe(
                    pd.DataFrame(_meses_criticos_m).rename(
                        columns={
                            "mes_nombre": "Mes",
                            "poa_perdida_kWh_m2": "POA perdida (kWh/m²)",
                            "horas_con_sombra": "Horas con sombra",
                            "horas_criticas": "Horas críticas",
                            "fs_geometrico_medio": "FS geométrico medio",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
    for _titulo_m, _filas_m in _tablas_solares_m.items():
        if _filas_m:
            with st.expander(_titulo_m, expanded=False):
                st.dataframe(
                    pd.DataFrame(_filas_m).rename(
                        columns={
                            "grupo": "Grupo",
                            "poa_perdida_kWh_m2": "Pérdida solar POA (kWh/m²)",
                            "fs_geometrico_ponderado_pct": "FS geométrico ponderado (%)",
                            "horas_con_sombra": "Horas con sombra",
                            "agregacion": "Agregación aplicada",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
                )

with st.container(border=True):
    st.markdown("#### ⚡ Métricas eléctricas")
    _em1, _em2, _em3, _em4 = st.columns(4)
    _em1.metric(
        "Energía DC",
        (
            f"{_metricas_electricas_m['energia_dc_kWh']:,.0f} kWh/año"
            if _metricas_electricas_m["energia_dc_kWh"] is not None
            else "No simulada"
        ),
    )
    _em2.metric(
        "Energía AC",
        (
            f"{_metricas_electricas_m['energia_ac_kWh']:,.0f} kWh/año"
            if _metricas_electricas_m["energia_ac_kWh"] is not None
            else "No simulada"
        ),
    )
    _em3.metric(
        "Pérdida eléctrica total",
        (
            f"{_metricas_electricas_m['perdida_electrica_total_kWh']:,.0f} kWh/año"
            if _metricas_electricas_m["perdida_electrica_total_kWh"] is not None
            else "—"
        ),
        help="Inversor + bypass AC equivalente, cuando están disponibles.",
    )
    _em4.metric(
        "Impacto bypass",
        (
            f"{_metricas_electricas_m['perdida_bypass_ac_kWh']:,.0f} kWh AC/año"
            if _metricas_electricas_m["perdida_bypass_ac_kWh"] is not None
            else "No aplica"
        ),
    )
    _em5, _em6, _em7, _em8 = st.columns(4)
    _em5.metric(
        "Pérdida inversor",
        (
            f"{_metricas_electricas_m['perdida_inversor_kWh']:,.0f} kWh/año"
            if _metricas_electricas_m["perdida_inversor_kWh"] is not None
            else "—"
        ),
    )
    _em6.metric(
        "Impacto bypass DC",
        (
            f"{_metricas_electricas_m['perdida_bypass_dc_kWh']:,.0f} kWh/año"
            if _metricas_electricas_m["perdida_bypass_dc_kWh"] is not None
            else "No aplica"
        ),
    )
    _em7.metric(
        "Mismatch eléctrico",
        "No aislado",
        help=_metricas_electricas_m["nota_mismatch"],
    )
    _rec_f4 = (
        _definicion_fase4.get("resultados", {})
        if _definicion_fase4
        else {}
    )
    _contrato_ac_f4 = comparar_resultados_escenarios(
        _rec_f4,
        magnitud="E_AC_anual_kWh",
        unidad="kWh/año",
    )
    _em8.metric(
        "% recuperación AC",
        (
            _contrato_ac_f4["recuperacion_etiqueta"]
            if _contrato_ac_f4["escenarios_completos"]
            else "Pendiente"
        ),
        help=_contrato_ac_f4["motivo_recuperacion"],
    )
    if not _contrato_ac_f4["escenarios_completos"]:
        st.caption(
            "La energía recuperable y su porcentaje aparecerán cuando existan "
            "resultados E_AC_anual_kWh de referencia, situación actual y "
            "alternativa optimizada."
        )
    else:
        st.caption(
            "Decisión de diseño: E_AC_anual_kWh. La recuperación está limitada "
            "al intervalo 0–100%."
        )
    with st.expander("📐 Ver contrato de pérdidas y recuperación", expanded=False):
        st.markdown(
            f"- **Magnitud de decisión:** `E_AC_anual_kWh` ({_contrato_ac_f4['unidad']})\n"
            f"- **Pérdida por escenario:** `{_contrato_ac_f4['formula_perdida']}`\n"
            f"- **Recuperación:** `{_contrato_ac_f4['formula_recuperacion']}`\n"
            "- **Diagnóstico solar:** el mismo comparador puede usar `POA efectiva`, "
            "pero no sustituye la decisión basada en E_AC."
        )
        if _contrato_ac_f4["escenarios_completos"]:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Escenario": escenario.capitalize(),
                            "E_AC anual (kWh/año)": valor,
                            "Pérdida vs referencia": (
                                _contrato_ac_f4["perdidas_etiqueta"][escenario]
                            ),
                        }
                        for escenario, valor in _contrato_ac_f4["valores"].items()
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )
            st.metric(
                "Energía recuperable",
                (
                    f"{_contrato_ac_f4['energia_recuperable']:,.1f} kWh/año"
                    if _contrato_ac_f4["energia_recuperable"] is not None
                    else "No aplica"
                ),
                help=_contrato_ac_f4["motivo_recuperacion"],
            )
        else:
            st.info(
                "La comparación queda pendiente hasta contar con E_AC_anual_kWh "
                "en los tres escenarios."
            )

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — SOMBREADO DE HORIZONTE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🏙️ 1. Sombreado de horizonte")
st.markdown(
    """
Define el **perfil de obstrucciones** que rodean la fachada BIPV — edificios vecinos, árboles,
cornisas, etc. Para cada obstáculo ingresa:

- **Azimuth**: dirección desde la fachada hacia el obstáculo (0°=Norte, 90°=Este, 180°=Sur, 270°=Oeste)
- **Ángulo de elevación**: ángulo vertical del borde superior del obstáculo desde el nivel del array

> 💡 *Regla práctica*: `elevación ≈ arctan(altura_obstáculo / distancia_horizontal)`.
> Un edificio de 15 m a 30 m de distancia → elevación ≈ 26°.
"""
)

# ── Tabla editable de obstáculos ──────────────────────────────────────────────
col_tbl, col_ayuda = st.columns([2, 1])

with col_ayuda:
    st.markdown("**Ejemplos de elevación:**")
    ejemplos = pd.DataFrame({
        "Obstáculo":    ["Edificio 3 pisos (15m) a 10m", "Edificio 5 pisos (20m) a 30m",
                         "Árbol (8m) a 20m", "Cornisa (3m) a 5m"],
        "Elevación (°)": [56, 34, 22, 31],
    })
    st.dataframe(ejemplos, hide_index=True, use_container_width=True)
    st.caption("elevación = arctan(h/d) × 180/π")

with col_tbl:
    horizonte_default = pd.DataFrame({
        "Azimuth (°)": [0, 45, 90, 135, 180, 225, 270, 315],
        "Elevación obstáculo (°)": [0, 0, 0, 0, 0, 0, 0, 0],
    })

    if "horizonte_df" not in st.session_state:
        st.session_state["horizonte_df"] = horizonte_default.copy()

    horizonte_editado = st.data_editor(
        st.session_state["horizonte_df"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Azimuth (°)": st.column_config.NumberColumn(
                "Azimuth (°)",
                min_value=0, max_value=359, step=1,
                help="0=Norte, 90=Este, 180=Sur, 270=Oeste",
            ),
            "Elevación obstáculo (°)": st.column_config.NumberColumn(
                "Elevación obstáculo (°)",
                min_value=0, max_value=85, step=1,
                help="Ángulo vertical del tope del obstáculo",
            ),
        },
        key="editor_horizonte",
    )
    st.session_state["horizonte_df"] = horizonte_editado

# ── Diagrama panorámico de trayectoria solar ──────────────────────────────────
st.subheader("🌞 Diagrama de trayectoria solar y horizonte")

@st.cache_data(show_spinner=False)
def _solar_path_cache(lat, lon, alt_m):
    return posiciones_solares_representativas(lat, lon, alt_m)

solar_path = _solar_path_cache(lat, lon, alt_m)

# Parsear horizonte editado
puntos_horizonte = []
for _, row in horizonte_editado.dropna().iterrows():
    az  = float(row["Azimuth (°)"])
    elv = float(row["Elevación obstáculo (°)"])
    if elv > 0:
        puntos_horizonte.append((az, elv))

nombres_meses = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                 7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
colores_meses = px.colors.qualitative.Set3[:12]

fig_sp = go.Figure()

# Trayectorias solares por mes
for mes, grp in solar_path.groupby("mes"):
    _h_loc_mm = [f"{(h + _tz_off_mm) % 24:02d}:00" for h in grp.index.hour]
    fig_sp.add_trace(go.Scatter(
        x=grp["azimuth"],
        y=grp["apparent_elevation"],
        mode="lines",
        name=nombres_meses[mes],
        line=dict(color=colores_meses[mes - 1], width=1.5),
        opacity=0.75,
        showlegend=True,
        customdata=_h_loc_mm,
        hovertemplate=(
            f"<b>{nombres_meses[mes]}</b><br>"
            "Az: %{x:.1f}° El: %{y:.1f}°<br>"
            f"🕐 %{{customdata}} ({_tz_lbl_mm})<extra></extra>"
        ),
    ))

# Perfil de horizonte
az_linspace = np.linspace(0, 360, 721)
if puntos_horizonte:
    from calculos.mismatch import _interpolar_horizonte
    el_horizonte = _interpolar_horizonte(puntos_horizonte, az_linspace)
    fig_sp.add_trace(go.Scatter(
        x=np.concatenate([az_linspace, [360]]),
        y=np.concatenate([el_horizonte, [el_horizonte[0]]]),
        fill="tozeroy",
        fillcolor="rgba(139,90,43,0.30)",
        mode="lines",
        line=dict(color="saddlebrown", width=2),
        name="Horizonte obstáculos",
    ))
else:
    fig_sp.add_trace(go.Scatter(
        x=[0, 360], y=[0, 0],
        mode="lines",
        line=dict(color="saddlebrown", width=1.5, dash="dot"),
        name="Horizonte (sin obstáculos)",
    ))

fig_sp.update_layout(
    height=420,
    xaxis=dict(
        title="Azimuth (°) — 0=Norte, 90=Este, 180=Sur, 270=Oeste",
        tickvals=[0, 45, 90, 135, 180, 225, 270, 315, 360],
        ticktext=["N (0°)","NE","E (90°)","SE","S (180°)","SO","O (270°)","NO","N (360°)"],
        range=[0, 360],
    ),
    yaxis=dict(title="Elevación solar (°)", range=[0, 80]),
    legend=dict(orientation="h", y=-0.25, x=0, font_size=11),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(b=100),
)
st.plotly_chart(fig_sp, use_container_width=True)
st.caption(
    "Zona marrón = horizonte bloqueado por obstáculos. "
    "Las horas donde la trayectoria solar queda por debajo del horizonte son sombreadas."
)

# ── Botón calcular sombreado ──────────────────────────────────────────────────
btn_sombra = st.button(
    "🏙️ Calcular pérdidas por sombreado", type="primary", use_container_width=True
)

if btn_sombra or st.session_state.get("sombra_ok"):
    if btn_sombra:
        with st.spinner("Calculando sombreado horario sobre TMY completo..."):
            res_sombra = calcular_sombreado_horizonte(
                lat, lon, alt_m, tmy, poa_base, puntos_horizonte
            )
        st.session_state["res_sombra"]  = res_sombra
        st.session_state["sombra_ok"]   = True
        st.session_state["puntos_horiz"] = puntos_horizonte
    else:
        res_sombra       = st.session_state.get("res_sombra", {})
        puntos_horizonte = st.session_state.get("puntos_horiz", [])

    if res_sombra:
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("POA bruta",            f"{poa_anual:.0f} kWh/m²")
        sc2.metric("Pérdida solar de POA",    f"{res_sombra['energia_perdida_kWh_m2']:.1f} kWh/m²",
                   delta=f"-{res_sombra['factor_sombra_anual']*100:.1f}%",
                   delta_color="inverse",
                   help="Reducción de irradiancia POA por sombra; no es pérdida equivalente de kWh AC.")
        sc3.metric("Horas sombreadas/año", f"{res_sombra['horas_sombreadas']} h")
        sc4.metric("Factor de sombreado",
                   f"{res_sombra['factor_sombra_anual']*100:.1f}%",
                   help="Fracción de la energía POA perdida por sombreado")

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — MISMATCH POR ORIENTACIÓN MÚLTIPLE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🧭 2. Mismatch por orientación múltiple")
st.markdown(
    "Si el sistema BIPV abarca **varias fachadas con distinto azimuth** y los módulos "
    "de orientaciones diferentes están conectados **en el mismo string**, se produce una "
    "pérdida por diferencia de corriente (mismatch). Define cada grupo de módulos:"
)

multi_orient = st.toggle(
    "Tengo módulos en fachadas con distintas orientaciones en el mismo string",
    value=st.session_state.get("multi_orient", False),
    key="toggle_multi_orient",
)
st.session_state["multi_orient"] = multi_orient

res_mismatch_or = None

if multi_orient:
    n_orientaciones = st.radio(
        "¿Cuántas orientaciones distintas?",
        [2, 3], horizontal=True,
        index=0,
    )

    configs = []
    cols_or = st.columns(n_orientaciones)
    fracciones_validas = True

    orientaciones_lista = list(ORIENTACIONES.keys())

    for i, col in enumerate(cols_or):
        with col:
            st.markdown(f"**Fachada {i+1}**")
            lbl = st.selectbox(
                f"Orientación {i+1}",
                orientaciones_lista,
                index=i % len(orientaciones_lista),
                key=f"or_label_{i}",
            )
            tlt = st.slider(
                f"Inclinación {i+1} (°)",
                0, 90, tilt_def, key=f"or_tilt_{i}",
            )
            frac = st.number_input(
                f"Fracción de módulos {i+1} (0–1)",
                min_value=0.01, max_value=1.0,
                value=round(1.0 / n_orientaciones, 2),
                step=0.05,
                key=f"or_frac_{i}",
            )
            configs.append({
                "label":   lbl,
                "azimuth": ORIENTACIONES[lbl],
                "tilt":    tlt,
                "fraccion": frac,
            })

    suma_fracs = sum(c["fraccion"] for c in configs)
    if abs(suma_fracs - 1.0) > 0.05:
        st.warning(f"⚠️ La suma de fracciones es {suma_fracs:.2f} — debería ser 1.00. Ajusta los valores.")
        fracciones_validas = False
    else:
        st.success(f"✅ Suma de fracciones: {suma_fracs:.2f}")

    if fracciones_validas:
        btn_mismatch_or = st.button(
            "🧭 Calcular mismatch de orientación", type="primary", use_container_width=True
        )
        if btn_mismatch_or or st.session_state.get("mismatch_or_ok"):
            if btn_mismatch_or:
                with st.spinner("Calculando POA por orientación y factor de mismatch..."):
                    res_mismatch_or = calcular_mismatch_orientacion(
                        tmy, lat, lon, alt_m, configs
                    )
                st.session_state["res_mismatch_or"] = res_mismatch_or
                st.session_state["mismatch_or_ok"]  = True
            else:
                res_mismatch_or = st.session_state.get("res_mismatch_or", {})

            if res_mismatch_or:
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("POA media ponderada",  f"{res_mismatch_or['energia_ideal_kWh_m2']:.0f} kWh/m²")
                mc2.metric("Pérdida solar por mismatch", f"{res_mismatch_or['energia_perdida_kWh_m2']:.1f} kWh/m²",
                           delta=f"-{res_mismatch_or['factor_mismatch_pct']:.2f}%",
                           delta_color="inverse")
                mc3.metric("Factor mismatch",      f"{res_mismatch_or['factor_mismatch_pct']:.2f}%",
                           help="σ²/(2μ²) — PVsyst 1er orden")

                # Tabla POA por orientación
                df_poas = pd.DataFrame(res_mismatch_or["poas"])
                df_poas.columns = ["Fachada","Azimuth (°)","Inclinación (°)","Fracción","POA anual (kWh/m²)"]
                st.dataframe(df_poas.style.format({"Fracción": "{:.2f}", "POA anual (kWh/m²)": "{:.1f}"}),
                             use_container_width=True)
else:
    st.info("Sin mismatch de orientación — todos los módulos están en la misma fachada.")
    res_mismatch_or = {"factor_mismatch_pct": 0.0, "energia_perdida_kWh_m2": 0.0}
    st.session_state["res_mismatch_or"] = res_mismatch_or

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — PÉRDIDAS SIMPLES
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ 3. Otras pérdidas del sistema")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    pct_mismatch_fab = st.slider(
        "🔩 Mismatch de fabricación (%)",
        min_value=0.0, max_value=3.0,
        value=st.session_state.get("pct_mismatch_fab", 1.0),
        step=0.1,
        help="Diferencias entre módulos del mismo lote. IEC 61215: 0.5–2%. Típico BIPV: 1.0–1.5%.",
    )
    st.caption("Tolerancias de ±3% en Pmax generan ~1% de pérdida")

with col_s2:
    pct_soiling = st.slider(
        "🌫️ Suciedad — Soiling (%)",
        min_value=0.0, max_value=6.0,
        value=st.session_state.get("pct_soiling", 2.0),
        step=0.5,
        help="Polvo y suciedad en el vidrio. Colombia urbana: 1.5–3%. Sin limpieza periódica: hasta 5%.",
    )
    st.caption("Reducir con limpieza cada 2–3 meses")

with col_s3:
    pct_cableado = st.slider(
        "🔌 Cableado DC (%)",
        min_value=0.0, max_value=4.0,
        value=st.session_state.get("pct_cableado", 1.5),
        step=0.5,
        help="Pérdidas óhmicas en cables DC. Buena práctica: <1.5%. Instalaciones largas: hasta 3%.",
    )
    st.caption("Minimizar con sección de cable adecuada")

# Guardar sliders en session_state
st.session_state["pct_mismatch_fab"] = pct_mismatch_fab
st.session_state["pct_soiling"]      = pct_soiling
st.session_state["pct_cableado"]     = pct_cableado

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — CASCADA DE PÉRDIDAS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📉 4. Cascada de pérdidas — POA bruta → POA efectiva")

# Recuperar factores calculados
sombra_ok     = st.session_state.get("sombra_ok", False)
mismatch_or_r = st.session_state.get("res_mismatch_or", {"factor_mismatch_pct": 0.0})
sombra_r      = st.session_state.get("res_sombra",      {"factor_sombra_anual": 0.0})

factor_sombra_anual   = sombra_r.get("factor_sombra_anual", 0.0)
factor_mismatch_or_pct = mismatch_or_r.get("factor_mismatch_pct", 0.0)

if not sombra_ok:
    st.info(
        "💡 Calcula el sombreado de horizonte (sección 1) para incluirlo en la cascada. "
        "Puedes ejecutar la cascada igualmente con factor_sombra = 0."
    )

btn_cascada = st.button(
    "📉 Calcular cascada completa de pérdidas", type="primary", use_container_width=True
)

if btn_cascada or st.session_state.get("cascada_ok"):
    cascada = cascada_perdidas(
        poa_bruta_kWh_m2       = poa_anual,
        factor_sombra          = factor_sombra_anual,
        factor_mismatch_orient = factor_mismatch_or_pct,
        pct_mismatch_fab       = pct_mismatch_fab,
        pct_soiling            = pct_soiling,
        pct_cableado           = pct_cableado,
    )
    fg = factor_global_perdidas(cascada)
    st.session_state["cascada_mismatch"] = cascada
    st.session_state["factor_global_mismatch"] = fg
    st.session_state["cascada_ok"] = True

    # ── Waterfall chart ──────────────────────────────────────────────────────
    etapas     = [r["etapa"]   for r in cascada]
    energias   = [r["energia"] for r in cascada]
    perdidas   = [r["perdida"] for r in cascada]

    # Plotly waterfall
    measures = []
    y_vals   = []
    for r in cascada:
        if r["etapa"] in ("POA bruta", "POA efectiva final"):
            measures.append("absolute")
            y_vals.append(r["energia"])
        else:
            measures.append("relative")
            y_vals.append(-r["perdida"])

    fig_wf = go.Figure(go.Waterfall(
        orientation  = "v",
        measure      = measures,
        x            = etapas,
        y            = y_vals,
        connector    = dict(line=dict(color="rgb(63,63,63)", dash="dot")),
        decreasing   = dict(marker_color="#E05252"),
        increasing   = dict(marker_color="#5B9BD5"),
        totals       = dict(marker_color="#2E7D32"),
        text         = [f"{abs(v):.1f}" for v in y_vals],
        textposition = "outside",
        hovertemplate = "<b>%{x}</b><br>kWh/m²: %{y:.1f}<extra></extra>",
    ))
    fig_wf.update_layout(
        yaxis_title  = "Irradiancia POA (kWh/m²/año)",
        height       = 450,
        plot_bgcolor = "white",
        paper_bgcolor= "white",
        showlegend   = False,
        margin       = dict(t=40),
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    # ── Métricas finales ──────────────────────────────────────────────────────
    poa_efectiva = next(r["energia"] for r in cascada if r["etapa"] == "POA efectiva final")
    perdida_total = poa_anual - poa_efectiva

    cm1, cm2, cm3, cm4 = st.columns(4)
    cm1.metric("POA bruta",        f"{poa_anual:.0f} kWh/m²")
    cm2.metric("POA efectiva",     f"{poa_efectiva:.0f} kWh/m²")
    cm3.metric("Pérdida acumulada de POA",    f"{perdida_total:.0f} kWh/m²",
               delta=f"-{perdida_total/poa_anual*100:.1f}%", delta_color="inverse")
    cm4.metric("Factor global PR",  f"{fg*100:.1f}%",
                help="Factor de la cascada de POA; no representa por sí solo el PR eléctrico AC.")

    # ── Tabla detalle ─────────────────────────────────────────────────────────
    with st.expander("📋 Ver tabla detallada de la cascada"):
        df_casc = pd.DataFrame(cascada)
        df_casc.columns = ["Etapa", "Energía (kWh/m²)", "Pérdida (kWh/m²)", "% sobre POA bruta"]
        st.dataframe(
            df_casc.style.format({
                "Energía (kWh/m²)":    "{:.2f}",
                "Pérdida (kWh/m²)":    "{:.2f}",
                "% sobre POA bruta": "{:.2f}%",
            }).background_gradient(subset=["Pérdida (kWh/m²)"], cmap="Reds", low=0, high=1),
            use_container_width=True,
        )

    st.success(
        f"✅ Cascada calculada para **{ciudad}** | "
        f"POA efectiva: **{poa_efectiva:.0f} kWh/m²/año** | "
        f"Factor global PR: **{fg*100:.1f}%** | "
        f"Continúa en 📊 Producción para calcular la energía generada."
    )

    # ── Guardar en session_state para Producción ──────────────────────────────
    st.session_state["poa_efectiva_kWh_m2"]       = round(poa_efectiva, 1)
    st.session_state["factor_global_mismatch"]    = fg
    st.session_state["factor_sombra_anual"]       = factor_sombra_anual
    st.session_state["factor_mismatch_or_pct"]    = factor_mismatch_or_pct
    st.session_state["mismatch_ok"]               = True

    # ── Clave exclusiva multi-superficie (no sobreescribe poa_efectiva_kWh_m2) ─
    if _multisup_ok and _poa_multisup is not None:
        st.session_state["poa_efectiva_kWh_m2_multisup"] = round(poa_efectiva, 1)
        st.session_state["factor_global_mismatch_multisup"] = fg
        # Nota: E_ac_anual_kWh_multisup NO se recalcula aquí para evitar
        # doble conteo con el PR ya aplicado en Vista 3D. El factor_global_mismatch
        # queda disponible para que Producción lo aplique si el usuario lo decide.

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — BYPASS DIODES · Pérdida eléctrica por sombra parcial
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚡ 5. Bypass Diodes — Pérdida eléctrica por sombra parcial")

with st.expander("ℹ️ ¿Qué son los bypass diodes y por qué importan en BIPV fachada?", expanded=False):
    st.markdown("""
Cuando una fracción de módulos en un **string** queda en sombra, su corriente cae
por debajo del punto de operación del resto. Los **bypass diodes** se activan y
cortocircuitan esos módulos → se pierde **toda su tensión V_mp**, no solo la
potencia proporcional a la irradiancia reducida.

| Método | Pérdida calculada | Error típico |
|---|---|---|
| Reducción escalar (método actual) | Irradiancia × factor | Subestima 3–8% en fachadas urbanas |
| **Modelo bypass diode** | Pérdida eléctrica real por string | Exacto para sombras parciales |

**Fuente de datos:** CSV exportado desde la Calculadora de Sombreado BIPV
(`bipv.innovacionquimica.com.co`) tras ejecutar **«Cruzar Máscara + EPW»**.
Cada «Punto de Análisis» del CSV = una fila de módulos en la fachada.
    """)

# ── Uploader CSV ─────────────────────────────────────────────────────────────
st.markdown("#### 📂 Cargar CSV de la Calculadora de Sombreado")
st.caption(
    "Exporta el CSV desde bipv.innovacionquimica.com.co → Puntos de Análisis → "
    "**Exportar CSV** (después de ejecutar «Cruzar Máscara + EPW»). "
    "Columnas requeridas: **Mes, Dia, Hora, FS_geometrico**"
)

csv_file = st.file_uploader(
    "Archivo CSV con FS_geometrico horario",
    type=["csv"],
    key="uploader_csv_fs",
    help="CSV exportado por la Calculadora de Factor de Sombreado BIPV",
)

# ── CSV generado en 🌳 Sombras SketchUp (misma sesión) ──────────────────────
_csv_sk = st.session_state.get("csv_fs_sketchup_bytes")
if _csv_sk is not None and csv_file is None:
    _nom_sk = st.session_state.get("csv_fs_sketchup_nombre", "sombras_sketchup.csv")
    if st.button(f"🌳 Usar el CSV generado en Sombras SketchUp ({_nom_sk})"):
        try:
            import io as _io
            df_fs_raw, _meta_fs = cargar_csv_fs(_io.BytesIO(_csv_sk))
            st.session_state["df_fs_raw"] = df_fs_raw
            st.session_state["meta_fs"]   = _meta_fs
            st.session_state["csv_fs_ok"] = True
            st.success("CSV de SketchUp cargado — continúa igual que con un CSV subido.")
        except Exception as e:
            st.error(f"❌ Error al leer el CSV de SketchUp: {e}")
            st.session_state["csv_fs_ok"] = False

# Mantener CSV cargado entre reruns
if csv_file is not None:
    try:
        df_fs_raw, _meta_fs = cargar_csv_fs(csv_file)
        st.session_state["df_fs_raw"]  = df_fs_raw
        st.session_state["meta_fs"]    = _meta_fs
        st.session_state["csv_fs_ok"]  = True
    except Exception as e:
        st.error(f"❌ Error al leer el CSV: {e}")
        st.session_state["csv_fs_ok"] = False

csv_ok   = st.session_state.get("csv_fs_ok", False)
df_fs_raw = st.session_state.get("df_fs_raw", None)
meta_fs   = st.session_state.get("meta_fs", {})

if csv_ok and df_fs_raw is not None:
    # ── Banner fuente del FS ───────────────────────────────────────────────
    tipo_fs = meta_fs.get("tipo", "geometrico")
    if tipo_fs == "geometrico":
        st.success(meta_fs.get("descripcion", ""))
    else:
        st.warning(meta_fs.get("descripcion", ""))

    # ── #32 · Detección de convención invertida ────────────────────────────
    inversion_detectada = meta_fs.get("inversion_detectada", False)
    _adv_list = meta_fs.get("advertencias", [])

    # Separar advertencias críticas (inversión) de las informativas (multi-fachada)
    _adv_criticas = [a for a in _adv_list if "INVERTIDO" in a or "FORMATO" in a]
    _adv_info     = [a for a in _adv_list if a not in _adv_criticas]

    for adv in _adv_criticas:
        st.error(adv)
    for adv in _adv_info:
        st.warning(f"⚠️ {adv}")

    if inversion_detectada:
        st.warning(
            "💡 **Solución recomendada:** vuelve a la Calculadora de Sombreado, "
            "ejecuta **«Cruzar Máscara + EPW»** y exporta ese CSV (columna FS_geometrico incluida). "
            "Si prefieres usar este CSV de todas formas, activa la opción abajo."
        )

    # Checkbox para invertir FS (solo visible si se detectó posible inversión o el usuario lo activa)
    with st.expander("🔧 Opciones avanzadas del CSV", expanded=inversion_detectada):
        invertir_fs = st.checkbox(
            "Invertir FS (usar 1 − FS) — activa si el CSV está en formato transmitancia",
            value=inversion_detectada,
            key="bypass_invertir_fs",
            help="El CSV de 'Puntos manuales' usa FS = transmitancia (1=sin sombra). "
                 "El modelo bypass necesita FS = p_shade (0=sin sombra). "
                 "Marca esta opción para convertir automáticamente.",
        )
    st.session_state["bypass_invertir_fs_flag"] = invertir_fs

    # ── #33 · Selector de fachada ──────────────────────────────────────────
    fachadas_disp  = meta_fs.get("fachadas_disponibles", [])
    tiene_fachadas = meta_fs.get("tiene_fachada_col", False) and len(fachadas_disp) > 1

    if tiene_fachadas:
        st.markdown("#### 🏗️ Seleccionar fachada del array")
        st.caption(
            f"El CSV tiene {len(fachadas_disp)} fachadas/obstáculos distintos. "
            "Selecciona la fachada donde está instalado tu array solar para que el modelo "
            "use solo el FS de esa fachada (no el promedio de todas)."
        )
        fachada_sel = st.selectbox(
            "Fachada activa del array",
            options=["— Todas (promedio) —"] + fachadas_disp,
            index=0,
            key="bypass_fachada_sel",
            help="Usa la fachada que coincide con la orientación del array en tu proyecto",
        )
        st.session_state["bypass_fachada_sel_val"] = (
            None if fachada_sel == "— Todas (promedio) —" else fachada_sel
        )
    else:
        st.session_state["bypass_fachada_sel_val"] = None

    # ── Aplicar filtros al df antes de estadísticas y simulación ──────────
    _invertir  = st.session_state.get("bypass_invertir_fs_flag", False)
    _fachada_f = st.session_state.get("bypass_fachada_sel_val", None)

    df_fs_work = df_fs_raw.copy()
    if _fachada_f and "fachada" in df_fs_work.columns:
        df_fs_work = df_fs_work[df_fs_work["fachada"] == _fachada_f].copy()
        if df_fs_work.empty:
            st.error(f"No se encontraron filas para la fachada seleccionada: '{_fachada_f}'")
            df_fs_work = df_fs_raw.copy()  # fallback
    if _invertir:
        df_fs_work = df_fs_work.copy()
        df_fs_work["FS_geometrico"] = (
            1.0 - df_fs_work["FS_geometrico"]
        ).clip(0.0, 1.0)
        df_fs_work["FS"] = df_fs_work["FS_geometrico"]

    # ── Estadísticas del CSV ──────────────────────────────────────────────
    try:
        stats = estadisticas_fs(df_fs_work)
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Puntos de análisis", stats["n_puntos_analisis"],
                   help="Filas de módulos / posiciones en la fachada")
        sc2.metric("Timestamps en CSV",  f"{stats['n_timestamps']:,}",
                   help="Horas únicas con dato de FS")
        sc3.metric(
            f"{'FS_geom' if tipo_fs == 'geometrico' else 'FS'} medio",
            f"{stats['fs_medio']:.3f}",
            help="0 = sin sombra · 1 = sombra total — solo obstáculos físicos",
        )
        sc4.metric("Horas con FS > 0",   f"{stats['horas_fs_gt0']} h",
                   help="Horas al año con algún grado de sombreado activo")

        # Gráfica FS medio por mes
        df_fs_mes = stats["df_mensual_fs"]
        fig_fs = go.Figure(go.Bar(
            x=df_fs_mes["Mes"],
            y=df_fs_mes["FS medio"],
            marker_color=[
                "#C62828" if v > 0.3 else
                "#F9A825" if v > 0.1 else
                "#43A047"
                for v in df_fs_mes["FS medio"]
            ],
            text=[f"{v:.3f}" for v in df_fs_mes["FS medio"]],
            textposition="outside",
        ))
        fig_fs.update_layout(
            title="Factor de Sombreado medio mensual (CSV importado)",
            yaxis=dict(title="FS medio [0–1]", range=[0, max(df_fs_mes["FS medio"].max() * 1.3, 0.1)]),
            xaxis_title="Mes",
            height=320,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_fs, use_container_width=True)

    except Exception as e:
        st.warning(f"No se pudo calcular estadísticas del CSV: {e}")

    st.markdown("---")

    # ── Configuración de strings ──────────────────────────────────────────
    st.markdown("#### ⚙️ Configuración de strings para el modelo bypass")

    _n_total = st.session_state.get("N_paneles_dim", 0)
    col_bp1, col_bp2, col_bp3 = st.columns(3)

    with col_bp1:
        panel_bp_nombre = st.selectbox(
            "Panel fotovoltaico",
            list(MODULOS_BIPV.keys()),
            index=list(MODULOS_BIPV.keys()).index("ASP-ST1-T40"),
            key="bypass_panel",
            help="Debe coincidir con el panel de Producción",
        )
        panel_bp = MODULOS_BIPV[panel_bp_nombre]

    with col_bp2:
        n_series_default = 8
        # Inferir N_series desde dimensionamiento si hay datos
        if _n_total > 0:
            # Módulos típicos en serie para tensión 300-600V con paneles ~80-100Voc
            Voc_stc = panel_bp.get("Voc_stc", 100.0)
            # Apuntar a ~400V DC → N_series ≈ 400 / Voc_stc
            n_series_default = max(4, min(20, int(round(400 / Voc_stc))))

        N_series_bp = st.number_input(
            "Módulos en serie por string (N_series)",
            min_value=2, max_value=30,
            value=n_series_default,
            step=1,
            key="bypass_n_series",
            help="Número de módulos conectados en serie en cada string",
        )

    with col_bp3:
        if _n_total > 0 and N_series_bp > 0:
            n_par_default = max(1, round(_n_total / N_series_bp))
        else:
            n_par_default = 4
        N_parallel_bp = st.number_input(
            "Strings en paralelo (N_parallel)",
            min_value=1, max_value=200,
            value=n_par_default,
            step=1,
            key="bypass_n_parallel",
            help="Número de strings en paralelo en el array",
        )
        st.caption(
            f"Total módulos: **{N_series_bp * N_parallel_bp}**"
            + (f" (dimensionamiento: {_n_total})" if _n_total > 0 else "")
        )

    # ── POA base para el cálculo ──────────────────────────────────────────
    _motor_ok = st.session_state.get("motor_optico_ok", False)
    _mismatch_factor = st.session_state.get("factor_global_mismatch", 1.0)
    if _motor_ok:
        poa_bp = st.session_state["poa_efectiva_df"]["poa_global"].values
        poa_src = "Motor Óptico (IAM + Soiling + Térmico)"
    else:
        poa_bp = st.session_state["poa_df"]["poa_global"].values * _mismatch_factor
        poa_src = f"POA bruta × factor mismatch ({_mismatch_factor*100:.1f}%)"

    T_amb_bp = tmy["T2m"].values
    st.caption(f"📡 POA de referencia: **{poa_src}**")

    # ── #36 · Cobertura temporal y modo de alineación ─────────────────────
    st.markdown("#### 📅 Cobertura temporal del CSV")
    try:
        _tmy_idx = st.session_state["tmy_df"].index
        cob = cobertura_csv(df_fs_work, _tmy_idx)

        cc1, cc2, cc3 = st.columns(3)
        cc1.metric(
            "Días críticos en CSV",
            f"{len(cob['dias_criticos'])}",
            help="Días del año con datos de FS en el CSV (solsticios, equinoccios, etc.)",
        )
        cc2.metric(
            "Cobertura modo exacto",
            f"{cob['n_exacto']:,} h ({cob['pct_exacto']}%)",
            help="Horas del TMY que tienen coincidencia exacta (mes, día, hora) con el CSV",
        )
        cc3.metric(
            "Cobertura modo mensual",
            f"{cob['n_mensual']:,} h ({cob['pct_mensual']}%)",
            help="Horas cubiertas al replicar el patrón horario del día crítico a todo el mes",
        )

        # Semáforo visual
        if cob["pct_exacto"] < 2.0:
            st.warning(
                f"⚠️ **Cobertura exacta baja: {cob['pct_exacto']}% del año** — "
                f"solo {len(cob['dias_criticos'])} días críticos cubiertos. "
                "El **modo mensual** (recomendado) extiende el patrón de cada día crítico "
                f"a todos los días de su mes, elevando la cobertura al **{cob['pct_mensual']}%**."
            )
        elif cob["pct_mensual"] > 80:
            st.success(
                f"✅ **Cobertura mensual: {cob['pct_mensual']}%** — "
                "el CSV cubre todos (o casi todos) los meses del año."
            )

        # Meses sin día crítico
        meses_sin = [m for m in range(1, 13) if m not in cob["meses_cubiertos"]]
        if meses_sin:
            meses_nombres = ["Ene","Feb","Mar","Abr","May","Jun",
                             "Jul","Ago","Sep","Oct","Nov","Dic"]
            nombres_sin = [meses_nombres[m-1] for m in meses_sin]
            st.caption(
                f"🔸 Meses sin día crítico en el CSV → FS = 0 asumido: "
                f"**{', '.join(nombres_sin)}**. "
                "Para máxima precisión, incluye al menos un día de cada mes en "
                "la Calculadora de Sombreado."
            )
    except KeyError:
        st.info("ℹ️ Ejecuta Datos Meteorológicos primero para ver estadísticas de cobertura.")
    except Exception as _e:
        st.caption(f"(No se pudo calcular cobertura: {_e})")

    # ── Modo de alineación ────────────────────────────────────────────────
    modo_alineacion = st.radio(
        "🗓️ Modo de cobertura temporal",
        options=["mensual", "exacto"],
        format_func=lambda m: (
            "📅 Mensual (recomendado) — replica el patrón del día crítico a todo el mes"
            if m == "mensual"
            else "📌 Exacto — solo los días críticos del CSV (cobertura baja)"
        ),
        index=0,
        key="bypass_modo_alineacion",
        horizontal=True,
        help=(
            "**Mensual**: el FS horario del día crítico (ej. 21 de marzo) se aplica a "
            "todos los días de ese mes a la misma hora. La geometría solar varía poco "
            "dentro de un mes, así que el día crítico es representativo. "
            "Resultado: estimación anual de bypass mucho más realista.\n\n"
            "**Exacto**: el FS solo se usa para las horas exactas del CSV. "
            "El resto del año se asume FS=0 (sin bypass). Útil para verificación."
        ),
    )
    # El widget con key="bypass_modo_alineacion" ya mantiene session_state
    # sincronizado; reasignarlo tras instanciar el widget lanza StreamlitAPIException.

    # ── Horizonte: combinar con el FS 3D (#232) ───────────────────────────
    _horiz_disponible = bool(
        st.session_state.get("sombra_ok")
        and isinstance(st.session_state.get("res_sombra"), dict)
        and st.session_state["res_sombra"].get("horas_sombreadas", 0) > 0
    )
    if _horiz_disponible:
        incluir_horizonte = st.checkbox(
            "🏔️ Incluir el perfil de horizonte en el bypass (recomendado)",
            value=True,
            key="bypass_incluir_horizonte",
            help=(
                "Combina hora a hora la sombra del horizonte (montañas/edificios "
                "lejanos, sección de arriba) con el FS del modelo 3D tomando la "
                "PEOR de las dos — máximo, nunca suma, para no contar dos veces "
                "el mismo obstáculo."
            ),
        )
    else:
        incluir_horizonte = False
        if st.session_state.get("puntos_horiz") is None:
            st.caption(
                "🏔️ Sin perfil de horizonte calculado — solo se usará el FS del "
                "modelo 3D. Si el sitio tiene montañas o edificios lejanos, "
                "calcula el sombreado de horizonte arriba y vuelve."
            )

    # ── Botón de simulación ───────────────────────────────────────────────
    btn_bypass = st.button(
        "⚡ Calcular pérdida real por bypass diodes",
        type="primary",
        use_container_width=True,
        key="btn_bypass",
    )

    if btn_bypass or st.session_state.get("bypass_ok"):
        if btn_bypass:
            with st.spinner("Alineando FS con TMY y simulando bypass diodes hora a hora..."):
                try:
                    # Alinear FS con el TMY (df_fs_work: filtrado por fachada e invertido si aplica)
                    tmy_idx  = st.session_state["tmy_df"].index
                    _modo    = st.session_state.get("bypass_modo_alineacion", "mensual")
                    _modo_ag = st.session_state.get(
                        "bypass_modo_agregacion", "auto"
                    )
                    p_shade  = alinear_fs_con_tmy(
                        df_fs_work,
                        tmy_idx,
                        modo=_modo,
                        modo_agregacion=_modo_ag,
                    )
                    st.session_state["bypass_modo_usado"] = _modo
                    st.session_state["bypass_modo_agregacion_usado"] = _modo_ag

                    # Combinar con el horizonte (#232): máximo hora a hora
                    _info_horiz = None
                    if incluir_horizonte:
                        _mask_h = st.session_state["res_sombra"]["mascara_sombra"]
                        p_shade, _info_horiz = combinar_fs_con_horizonte(
                            p_shade, _mask_h
                        )
                    st.session_state["bypass_horizonte_info"] = _info_horiz
                    st.session_state["bypass_horizonte_incluido"] = bool(
                        incluir_horizonte
                    )

                    # Simular bypass
                    res_bp = simular_bypass_horario(
                        G_eff      = poa_bp,
                        T_amb      = T_amb_bp,
                        p_shade    = p_shade.values,
                        N_series   = int(N_series_bp),
                        N_parallel = int(N_parallel_bp),
                        panel      = panel_bp,
                        NOCT       = float(panel_bp.get("NOCT", 45.0)),
                        umbral_shade = 0.05,
                    )
                    st.session_state["bypass_result"]     = res_bp
                    st.session_state["bypass_p_shade"]    = p_shade
                    # OJO: no usar las keys de los widgets ("bypass_n_series",
                    # "bypass_n_parallel", "bypass_panel") — reasignarlas tras
                    # instanciar el widget lanza StreamlitAPIException.
                    st.session_state["bypass_n_series_usado"]   = int(N_series_bp)
                    st.session_state["bypass_n_parallel_usado"] = int(N_parallel_bp)
                    st.session_state["bypass_panel_usado"]      = panel_bp_nombre
                    st.session_state["bypass_ok"]         = True
                except Exception as e:
                    st.error(f"❌ Error en simulación bypass: {e}")
                    st.session_state["bypass_ok"] = False

        res_bp = st.session_state.get("bypass_result", {})

        # #232: si el checkbox de horizonte cambió después de calcular, el
        # resultado mostrado ya no corresponde a la selección — avisar.
        if res_bp and bool(incluir_horizonte) != bool(
            st.session_state.get("bypass_horizonte_incluido")
        ):
            st.warning(
                "⚠️ Cambiaste la opción del horizonte después de calcular: el "
                "resultado de abajo se calculó "
                + (
                    "SIN el horizonte incluido. "
                    if incluir_horizonte
                    else "CON el horizonte incluido. "
                )
                + "Pulsa «⚡ Calcular pérdida real por bypass diodes» para "
                "actualizarlo."
            )

        if res_bp:
            # ── Métricas resumen ───────────────────────────────────────────
            bp1, bp2, bp3, bp4 = st.columns(4)
            bp1.metric(
                "Pérdida DC por bypass",
                f"{res_bp['kwh_bypass_anual']:,.0f} kWh/año",
                delta=f"-{res_bp['pct_bypass_anual']:.2f}% de E_dc",
                delta_color="inverse",
                help="Energía DC adicional perdida por activación de bypass diodes",
            )
            bp2.metric(
                "Horas con bypass activo",
                f"{res_bp['horas_bypass']} h/año",
                help="Horas al año donde al menos un bypass diode se activa",
            )
            bp3.metric(
                "Horas con sombra (FS > 5%)",
                f"{res_bp['horas_sombra']} h/año",
                help="Horas con sombra activa en el CSV cargado",
            )
            bp4.metric(
                "E_dc con bypass",
                f"{res_bp['kwh_dc_uniforme'] - res_bp['kwh_bypass_anual']:,.0f} kWh/año",
                help="Producción DC real considerando bypass diodes",
            )

            # ── Gráfica mensual ────────────────────────────────────────────
            df_m_bp = res_bp["df_mensual_bypass"]

            fig_bp = go.Figure()
            fig_bp.add_trace(go.Bar(
                name="Producción DC con bypass (kWh)",
                x=df_m_bp.index,
                y=df_m_bp["E_dc con bypass (kWh)"].round(0),
                marker_color="#2E7D32",
                opacity=0.85,
            ))
            fig_bp.add_trace(go.Bar(
                name="Pérdida bypass diodes (kWh)",
                x=df_m_bp.index,
                y=df_m_bp["Pérdida bypass (kWh)"].round(0),
                marker_color="#C62828",
                opacity=0.80,
                text=df_m_bp["Pérdida bypass (kWh)"].apply(
                    lambda v: f"{v:,.0f}" if v > 1 else ""
                ),
                textposition="outside",
            ))
            fig_bp.update_layout(
                barmode="stack",
                title="Producción DC mensual con bypass diodes",
                yaxis_title="Energía (kWh)",
                xaxis_title="Mes",
                height=360,
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.25),
                margin=dict(b=80),
            )
            st.plotly_chart(fig_bp, use_container_width=True)

            # ── Horas de bypass por mes ────────────────────────────────────
            fig_h = go.Figure()
            fig_h.add_trace(go.Bar(
                name="Horas sombra activa",
                x=df_m_bp.index,
                y=df_m_bp["Horas con sombra"].round(0),
                marker_color="#BDBDBD",
                opacity=0.70,
            ))
            fig_h.add_trace(go.Bar(
                name="Horas bypass activo",
                x=df_m_bp.index,
                y=df_m_bp["Horas bypass activo"].round(0),
                marker_color="#E65100",
                opacity=0.85,
                text=df_m_bp["Horas bypass activo"].apply(
                    lambda v: f"{v:.0f}h" if v > 0 else ""
                ),
                textposition="outside",
            ))
            fig_h.update_layout(
                barmode="group",
                title="Horas de sombra vs horas con bypass diode activo",
                yaxis_title="Horas / mes",
                xaxis_title="Mes",
                height=300,
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend=dict(orientation="h", y=-0.30),
                margin=dict(b=80),
            )
            st.plotly_chart(fig_h, use_container_width=True)

            # ── Tabla mensual detallada ────────────────────────────────────
            with st.expander("📋 Ver tabla mensual completa de bypass diodes"):
                df_show = df_m_bp.copy()
                df_show["FS medio mensual"] = df_show["FS medio mensual"].round(3)
                st.dataframe(
                    df_show.style.format({
                        "E_dc con bypass (kWh)":  "{:,.0f}",
                        "Pérdida bypass (kWh)":   "{:,.1f}",
                        "FS medio mensual":        "{:.3f}",
                        "Horas bypass activo":     "{:.0f}",
                        "Horas con sombra":        "{:.0f}",
                    }).background_gradient(subset=["Pérdida bypass (kWh)"], cmap="Reds"),
                    use_container_width=True,
                )

            # ── Diagnóstico automático ─────────────────────────────────────
            pct = res_bp["pct_bypass_anual"]
            if pct > 5.0:
                st.error(
                    f"🔴 **Pérdida por bypass diodes: {pct:.2f}%** — "
                    "Supera el 5% de la producción DC. La sombra parcial tiene un "
                    "impacto significativo. Considerar:\n"
                    "- Reorganizar strings para agrupar módulos con igual patrón de sombra\n"
                    "- Añadir optimizadores de módulo (SolarEdge, Tigo) en las filas críticas\n"
                    "- Verificar si el diseño de fachada puede reducir la sombra en horas pico"
                )
            elif pct > 2.0:
                st.warning(
                    f"🟡 **Pérdida por bypass diodes: {pct:.2f}%** — "
                    "Moderada (2–5%). Revisar si los strings más afectados pueden "
                    "separarse en ramas de MPPT independientes del inversor."
                )
            else:
                st.success(
                    f"🟢 **Pérdida por bypass diodes: {pct:.2f}%** — "
                    "Baja (<2%). Las sombras parciales tienen impacto eléctrico controlado. "
                    f"({res_bp['horas_bypass']} horas/año con bypass activo)"
                )

            _tipo_fs_res = meta_fs.get("tipo", "geometrico")
            _col_fs_res  = meta_fs.get("col_original", "FS")
            _fs_badge    = (
                "🟩 FS geométrico (solo obstáculos físicos)"
                if _tipo_fs_res == "geometrico"
                else "⚠️ Fuente no oficial"
            )
            _modo_usado = st.session_state.get("bypass_modo_usado", "mensual")
            _modo_badge = (
                "📅 patrón mensual"
                if _modo_usado == "mensual"
                else "📌 días críticos exactos"
            )
            st.success(
                f"✅ Modelo bypass completado | "
                f"Pérdida adicional: **{res_bp['kwh_bypass_anual']:,.0f} kWh/año** "
                f"({res_bp['pct_bypass_anual']:.2f}% de E_dc) | "
                f"Bypass activo **{res_bp['horas_bypass']} h/año** · "
                f"Fuente FS: **{_col_fs_res}** ({_fs_badge}) · "
                f"Cobertura: **{_modo_badge}**"
            )
            from calculos.contrato_sombreado import etiqueta_fuente_fs as _etq_fs
            _horiz_txt = ""
            if st.session_state.get("bypass_horizonte_incluido"):
                _ih = st.session_state.get("bypass_horizonte_info") or {}
                _horiz_txt = (
                    f" · 🏔️ Horizonte incluido ({_ih.get('horas_horizonte', 0)} h/año, "
                    f"{_ih.get('horas_solo_horizonte', 0)} h solo por horizonte)"
                )
            elif st.session_state.get("sombra_ok"):
                _horiz_txt = " · 🏔️ Horizonte NO incluido en este cálculo"
            st.caption(
                "🧭 Fuente del sombreado: "
                f"**{_etq_fs(st.session_state.get('fs_fuente'))}**{_horiz_txt}"
            )

            # ── Fase 4: ejecutar escenarios sobre la base congelada ────────
            _def_f4_exec = st.session_state.get("escenarios_fase4")
            st.markdown("#### 🔁 Escenarios Fase 4 (E_AC anual por escenario)")
            if not _def_f4_exec or not isinstance(
                _def_f4_exec.get("base_comparacion"), dict
            ):
                st.info(
                    "Primero guarda la definición y congela la base única "
                    "(sección Fase 4 arriba) para poder ejecutar los escenarios."
                )
            elif (
                _def_f4_exec["base_comparacion"].get("lista_para_comparar")
                is not True
            ):
                _faltantes_f4 = _def_f4_exec["base_comparacion"].get(
                    "faltantes", []
                )
                st.warning(
                    "⚠️ La base congelada quedó **incompleta** (se guardó antes "
                    "de terminar los pasos previos). Faltaba: "
                    + ("; ".join(_faltantes_f4) if _faltantes_f4 else "—")
                    + ". Completa esos pasos y vuelve a pulsar "
                    "**💾 Guardar definición y congelar base** para poder ejecutar."
                )
            elif st.button(
                "▶️ Ejecutar escenarios (referencia / actual / optimizada)",
                key="btn_ejecutar_escenarios_f4",
                use_container_width=True,
            ):
                try:
                    # eta_inversor solo existe tras correr Producción; en una
                    # sesión nueva usar el valor congelado en la base (es el
                    # mismo contra el que el ejecutor verifica coherencia).
                    _eta_f4 = st.session_state.get("eta_inversor")
                    if _eta_f4 is None:
                        _eta_f4 = (_def_f4_exec.get("base_comparacion") or {}).get(
                            "eta_inversor"
                        )
                    if _eta_f4 is None:
                        st.error(
                            "❌ Falta la eficiencia del inversor (η). Corre una vez "
                            "la página 📊 Producción en esta sesión (o congela la "
                            "base después de correrla) y vuelve a ejecutar los "
                            "escenarios."
                        )
                        st.stop()
                    with st.spinner("Simulando los escenarios con la base congelada..."):
                        _res_f4 = ejecutar_escenarios(
                            definicion=_def_f4_exec,
                            base_estado_actual=capturar_base_comparacion(
                                st.session_state
                            ),
                            tmy=st.session_state["tmy_df"],
                            poa_global=poa_bp,
                            panel=panel_bp,
                            n_serie=int(N_series_bp),
                            n_paralelo=int(N_parallel_bp),
                            eta_inversor=float(
                                st.session_state.get("eta_inversor")
                            ),
                            df_fs_actual=df_fs_work,
                            df_fs_optimizada=st.session_state.get(
                                "df_fs_optimizada_f4"
                            ),
                            modo_alineacion=st.session_state.get(
                                "bypass_modo_alineacion", "mensual"
                            ),
                            modo_agregacion=st.session_state.get(
                                "bypass_modo_agregacion", "auto"
                            ),
                            # Horizonte (#232): obligatorio si la definición
                            # lo declara; el ejecutor valida coherencia.
                            mascara_horizonte=(
                                st.session_state["res_sombra"]["mascara_sombra"]
                                if (
                                    "horizonte"
                                    in (
                                        (_def_f4_exec.get("politica_fuentes_actual")
                                         or {}).get("fuentes_declaradas", [])
                                    )
                                    and st.session_state.get("sombra_ok")
                                    and isinstance(
                                        st.session_state.get("res_sombra"), dict
                                    )
                                )
                                else None
                            ),
                        )
                    _def_f4_exec["resultados"] = _res_f4
                    st.session_state["escenarios_fase4"] = _def_f4_exec
                    st.success(
                        "✅ Escenarios ejecutados sobre la base "
                        f"`{_res_f4['base_id'][:12]}`. "
                        "El % de recuperación AC se actualizará arriba al recargar."
                    )
                    st.rerun()
                except (ValueError, TypeError, KeyError) as _e_exec_f4:
                    st.error(f"❌ No se pudieron ejecutar los escenarios: {_e_exec_f4}")
            _res_guardados_f4 = (_def_f4_exec or {}).get("resultados")
            if _res_guardados_f4:
                _filas_res_f4 = []
                for _esc_id in ("referencia", "actual", "optimizada"):
                    _r = _res_guardados_f4.get(_esc_id, {})
                    _filas_res_f4.append(
                        {
                            "Escenario": _esc_id.capitalize(),
                            "Estado": _r.get("estado", "—"),
                            "E_AC anual (kWh/año)": _r.get("E_AC_anual_kWh"),
                            "E_DC anual (kWh/año)": _r.get("E_DC_anual_kWh"),
                            "Pérdida bypass (kWh DC/año)": _r.get(
                                "kwh_bypass_anual"
                            ),
                        }
                    )
                st.dataframe(
                    pd.DataFrame(_filas_res_f4),
                    hide_index=True,
                    use_container_width=True,
                )
                st.caption(
                    f"Base congelada: `{_res_guardados_f4.get('base_id', '')[:12]}` · "
                    "mismo método eléctrico en los tres escenarios; solo cambia "
                    "el FS geométrico."
                )

elif not csv_ok:
    st.info(
        "💡 Carga el CSV exportado desde **bipv.innovacionquimica.com.co** "
        "(Calculadora de Factor de Sombreado → Puntos de Análisis → "
        "Cruzar Máscara + EPW → Exportar CSV) para calcular la pérdida "
        "real por bypass diodes con tu modelo 3D del edificio."
    )
