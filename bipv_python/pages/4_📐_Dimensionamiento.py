"""Página 4 — Dimensionamiento de strings."""
import math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from calculos.dimensionamiento import (
    mapear_inversores_catalogo,
    optimizar_n_serie,
    dimensionar_sistema,
    proyecto_completo,
    resolver_n_strings_tracker,
    curva_electrica_temperatura,
    interpretar_curva_electrica,
    diseno_electrico_confirmado,
)
from calculos.graficos_compatibilidad import figura_compatibilidad_electrica
from calculos.campos_persistentes import campo_persistente
from calculos.temperatura import (
    KEYS_TEMPS_DISENO,
    temperaturas_a_aplicar,
    temps_diseno_en_cero,
)
from calculos.modelo_iv import (
    preparar_panel_iv, resolver_curva_iv, resolver_panel_calibrado,
    validar_sdm_vs_ficha, explicar_fallo_validacion_sdm,
)
from datos.tecnologias_bipv import MODULOS_BIPV
from datos.catalogo_paneles_excel import cargar_catalogo_excel, obtener_panel_excel
from datos.catalogo_inversores_excel import (
    cargar_catalogo_inversores,
    obtener_inversor_excel,
    diagnostico_catalogo_inversores as _diag_inv_fn,
    excel_mtime_inv as _mtime_inv,
    cargar_catalogo_inversores as _cargar_cat_inv,
)
from datos.catalogo_inversores import INVERSORES, seleccionar_inversor
from datos.ciudades_colombia import CIUDADES
from calculos.panel_iv_check import analizar_panel_motiv as _check_iv_dim
from calculos.compatibilidad_bateria import check_compatibilidad as _check_compat_bateria_dim

st.set_page_config(page_title="Dimensionamiento — BIPV", page_icon="📐", layout="wide")

from calculos.auth import requerir_login
requerir_login()

# ── #225: restaurar panel/inversor predeterminados del usuario ────────────────
# Debe correr ANTES de instanciar los selectores (patrón widgets keyed).
from calculos.persistencia_resultados import (
    cargar_seleccion_equipos,
    guardar_seleccion_equipos,
)
_auth_email_dim = st.session_state.get("auth_email", "")
if not st.session_state.get("_sel_equipos_restaurada"):
    st.session_state["_sel_equipos_restaurada"] = True
    _sel_pers = cargar_seleccion_equipos(_auth_email_dim)
    if _sel_pers.get("panel") and "panel_pref_persistido" not in st.session_state:
        st.session_state["panel_pref_persistido"] = _sel_pers["panel"]
    if _sel_pers.get("inversor") and not st.session_state.get("inversor_nombre_dim"):
        st.session_state["inversor_nombre_dim"] = _sel_pers["inversor"]

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página
st.title("📐 Dimensionamiento de Strings")
st.caption("Equivalente de Mod_OptimizarStringSizing + Mod_CalculoStringSizing (VBA)")

col1, col2 = st.columns(2)

with col1:
    _cat_excel = cargar_catalogo_excel()
    _lista_paneles = list(_cat_excel.keys()) if _cat_excel else list(MODULOS_BIPV.keys())
    _panel_pref = st.session_state.get("panel_pref_persistido", "")
    if _panel_pref in _lista_paneles:
        _idx_default = _lista_paneles.index(_panel_pref)
    else:
        _idx_default = _lista_paneles.index("ASP-ST1-T40") if "ASP-ST1-T40" in _lista_paneles else 0
    # #118 — badge ✅/⚠️ en la lista (mismo criterio que Motor IV: faltan Voc/Isc/Vmp/Imp)
    def _fmt_panel_dim(name: str) -> str:
        _p = (_cat_excel.get(name) if _cat_excel else None) or MODULOS_BIPV.get(name) or {}
        _err, _ = _check_iv_dim(_p)
        return f"{'⚠️' if _err else '✅'} {name}"
    panel_nombre   = st.selectbox("Panel", _lista_paneles, index=_idx_default,
                                  format_func=_fmt_panel_dim)
    _cat_inv = cargar_catalogo_inversores()
    _lista_inv = list(_cat_inv.keys()) if _cat_inv else list(INVERSORES.keys())
    _inv_default = st.session_state.get("inversor_nombre_dim", "")
    _idx_inv = (
        _lista_inv.index(_inv_default)
        if _inv_default in _lista_inv
        else next(
            (i for i, k in enumerate(_lista_inv)
             if "MID15KTL3" in k or "MID 15KTL3" in k),
            0,
        )
    )
    # El botón del mapeo puede solicitar un cambio de modelo antes del rerun.
    # Se usa una clave explícita para que el selector visible se sincronice
    # realmente, sin pisar una selección manual del usuario.
    _inv_pendiente = st.session_state.pop("_inversor_nombre_dim_pendiente", None)
    if _inv_pendiente in _lista_inv:
        st.session_state["inversor_selector_dim"] = _inv_pendiente
    elif (
        "inversor_selector_dim" not in st.session_state
        or st.session_state["inversor_selector_dim"] not in _lista_inv
    ):
        st.session_state["inversor_selector_dim"] = _lista_inv[_idx_inv]
    inversor_nombre = st.selectbox(
        "Inversor",
        _lista_inv,
        key="inversor_selector_dim",
    )
    # #225 — fijar la selección actual como predeterminada del usuario
    if st.button(
        "📌 Fijar panel + inversor como predeterminados",
        key="btn_fijar_seleccion_equipos",
        help=(
            "Guarda esta selección en tu cuenta: al abrir la app en una nueva "
            "sesión (F5 o reinicio del servidor), estos serán los valores "
            "preseleccionados en vez de los defaults de fábrica."
        ),
    ):
        if guardar_seleccion_equipos(_auth_email_dim, panel_nombre, inversor_nombre):
            st.session_state["panel_pref_persistido"] = panel_nombre
            st.success(
                f"📌 Guardado: **{panel_nombre}** + **{inversor_nombre}** "
                "quedarán preseleccionados en tus próximas sesiones."
            )
        else:
            st.warning("No se pudo guardar la selección (revisa permisos del servidor).")

# Cargar dicts antes de col2 para que estén disponibles al calcular N_min_scan
_panel_catalogo = obtener_panel_excel(panel_nombre) if _cat_excel else MODULOS_BIPV[panel_nombre]
panel    = resolver_panel_calibrado(_panel_catalogo)
inversor = obtener_inversor_excel(inversor_nombre) if _cat_inv else seleccionar_inversor(inversor_nombre)

# ── Aviso Motor IV: panel sin datos IV suficientes (#118) ─────────────────────
_iv_err, _iv_adv = _check_iv_dim(panel)
if _iv_err:
    _falt = ", ".join(f"`{c}`" for c, _ in _iv_err)
    st.warning(
        f"⚠️ **{panel_nombre}** no tiene datos IV suficientes para Motor IV.  \n"
        f"Campos requeridos ausentes: {_falt}.  \n"
        f"El dimensionamiento eléctrico funcionará, pero la curva I-V no podrá "
        f"simularse en Motor IV. Completa el catálogo Excel con estos valores."
    )
elif _iv_adv:
    _adv_campos = [c for c, _ in _iv_adv if not c.startswith("⚠️")]
    if _adv_campos:
        st.info(
            f"ℹ️ **{panel_nombre}** puede simularse en Motor IV con estimaciones.  \n"
            f"Campos opcionales ausentes: {', '.join(f'`{c}`' for c in _adv_campos)} "
            f"— se usarán defaults por tecnología."
        )

# ── #58 — Aviso cuando las especificaciones del panel son estimadas ──────────
# El catálogo Excel trae Confianza="Media" cuando las dimensiones físicas del
# panel son aproximadas (no confirmadas con ficha del fabricante). El área y el
# número de paneles calculados heredan ese margen de error.
# Auditoría: el catálogo mezcla 'Alta'/'high'/'Alta — ficha oficial…' con
# 'Media'/'medium'. Solo se avisa cuando la confianza declarada es media/baja;
# valores vacíos, 'nan' (celda vacía de pandas) o desconocidos NO disparan.
_confianza_panel = str(panel.get("confianza", "") or "").strip().lower()
_es_estimado = _confianza_panel.startswith(("media", "medium", "baja", "low"))
if _es_estimado:
    st.warning(
        f"ℹ️ **Datos estimados** — la confianza del catálogo para "
        f"**{panel_nombre}** es *{panel.get('confianza')}*: sus dimensiones "
        f"físicas son aproximadas.  \n"
        f"Los cálculos de **área y número de paneles** pueden tener margen de "
        f"error. Confirma las dimensiones exactas con el fabricante antes de "
        f"cotizar."
    )

# ── Temperaturas de diseño desde el TMY (Spec 03/temperaturas-diseno) ───────
# Se recalculan cuando cambia la firma del TMY o el NOCT del panel (otra
# ciudad, otras coordenadas, otra versión de PVGIS, otro panel), cuando falta
# alguna o cuando las tres están en 0. Si no, se respeta lo que el usuario
# escribió. Antes dependía solo del nombre de la ciudad (29-sep-2026).
_tmy_df = st.session_state.get("tmy_df")
_t2m_dim = None
if _tmy_df is not None:
    _t2m_dim = _tmy_df["T2m"] if "T2m" in _tmy_df.columns else _tmy_df.iloc[:, 0]
_noct_dim = float(panel.get("NOCT", 45.0) or 45.0)

# #229 — aviso: el proyecto restaurado traía las temperaturas en cero y se
# descartaron (JSON legado con el bug de ciudades). Se re-siembran del TMY si
# existe; si no, de los valores de la ciudad.
if st.session_state.pop("_temps_diseno_saneadas", False):
    st.info(
        "🌡️ El proyecto guardado traía las temperaturas de diseño en 0 °C "
        "(un estado inválido de una versión anterior). Se descartaron y se "
        "recalcularán automáticamente desde el TMY de ☀️ Recurso Solar — "
        "verifica los valores antes de dimensionar."
    )

try:
    _temps_nuevas = temperaturas_a_aplicar(st.session_state, _t2m_dim, _noct_dim)
except (TypeError, ValueError):
    _temps_nuevas = None
if _temps_nuevas:
    st.session_state.update(_temps_nuevas)

with col2:
    # No pasar value= junto con key= cuando session_state ya trae el valor:
    # Streamlit advierte "created with a default value but also had its value
    # set via the Session State API". Se siembra el default solo si falta.
    #
    # Bug real encontrado y corregido (4-sep-2026, ver
    # FANTASMA NEGATIVO Y POSITIVO EN TEMPERATURA BMODULO PRODUCCION.docx):
    # los 3 defaults eran valores mágicos fijos (-5.0/36.35/41.94) que
    # coincidían por casualidad con 2 de los 3 reales de Bogotá (T_cel_
    # realista/extremo), pero NO con T_min_diseno (el real de Bogotá en
    # datos/ciudades_colombia.py es 5.0, no -5.0 -- quedó desincronizado del
    # fix que ya corrigió ese mismo valor ahí). Para cualquier otra ciudad
    # los 3 eran directamente incorrectos (ej. Cali real: 12.0/47.0/55.0).
    # Se mostraban/usaban en cálculos reales (Voc_max, compatibilidad de
    # string) cada vez que el usuario abría esta página ANTES de que
    # ☀️ Recurso Solar cacheara el TMY completo (tmy_df en session_state) --
    # el bloque de arriba solo recalcula desde el TMY real cuando ya existe.
    # Corregido: el placeholder ahora es el valor real de la ciudad activa
    # (mismo dato que ya usa 🏠 Proyecto), no un número universal inventado.
    #
    # 29-sep-2026 (Spec 03/temperaturas-diseno): el dato vive en su clave de
    # siempre y el campo en «_w_<clave>» (campo_persistente). Con la misma
    # clave para los dos, Streamlit la borraba al abrir otra página y al
    # volver quedaban los valores de la ciudad (Apartadó: 20/55/64 en vez de
    # 20.9/54.2/63.6 del TMY), o en 0.
    _ciudad_activa_dim = st.session_state.get("ciudad", "Bogotá")
    _ciudad_defaults = CIUDADES.get(_ciudad_activa_dim, CIUDADES.get("Bogotá", {}))
    if temps_diseno_en_cero(st.session_state):
        for _k in KEYS_TEMPS_DISENO:
            st.session_state.pop(_k, None)
    T_frio = campo_persistente(
        st.session_state, st.number_input, "T_mín diseño (°C)", "T_min_diseno",
        float(_ciudad_defaults.get("T_min_diseno", 5.0)), min_value=-40.0, max_value=45.0,
        step=0.1, format="%.2f",
        help="Mínima del año típico (TMY) de ☀️ Recurso Solar. Determina Voc_max y riesgo sobre Vdc_max del inversor.")
    T_real = campo_persistente(
        st.session_state, st.number_input, "T_celda caliente realista (°C)", "T_cel_realista",
        float(_ciudad_defaults.get("T_cel_realista", 36.35)), min_value=-10.0, max_value=110.0,
        step=0.1, format="%.2f",
        help="T_amb P95 + (NOCT-20)/800×800 W/m². Determina Vmp de operación habitual.")
    T_extr = campo_persistente(
        st.session_state, st.number_input, "T_celda caliente extremo (°C)", "T_cel_extremo",
        float(_ciudad_defaults.get("T_cel_extremo", 41.94)), min_value=-10.0, max_value=120.0,
        step=0.1, format="%.2f",
        help="T_amb máxima histórica + (NOCT-20)/800×1000 W/m². Determina Vmp mínimo (peor caso MPPT).")
    # N_strings/tracker: dos mecanismos posibles, ver docstring de
    # resolver_n_strings_tracker() para la comparación honesta contra la
    # referencia estándar internacional que motivó agregar el mecanismo
    # "total" (29-ago-2026).
    #
    # Sugerencia orientativa del total -- antes este campo no tenía NINGUNA
    # orientación (ni el área, ni ningún otro dato del proyecto lo sugería),
    # había que escribir un número a ciegas. Dos fuentes posibles, en orden
    # de prioridad (idea del usuario, 29-ago-2026: reusar el mismo cálculo
    # que ya usa ⚡ Diagrama Unifilar):
    #   1) REAL -- calculos/diagrama_unifilar.py::normalizar_proyecto_unifilar()
    #      calcula n_strings = N_paneles_granja // N_serie -- el conteo real
    #      del "Proyecto completo" (ya incorpora cuántos inversores hacen
    #      falta), no una aproximación. Se usa si ya se corrió "▶️ Optimizar
    #      N paneles/string" al menos una vez (N_paneles_granja existe).
    #   2) ÁREA (respaldo) -- si todavía no existe ese dato (sesión nueva,
    #      optimizador no corrido aún): área útil ÷ área del panel ÷ N/string
    #      ya confirmado o estimado eléctricamente. Menos exacto (no
    #      considera cuántos inversores hacen falta), pero disponible desde
    #      el primer render.
    # Ninguna se autocompleta en el campo -- son puramente informativas.
    _vmppt_min_sug = inversor.get("Vmppt_activo_min") or inversor.get("Vmppt_min") or 0
    _vmp_panel_sug = panel.get("Vmp_stc") or panel.get("Vmp") or 1
    _n_serie_elec_sug = max(1, math.ceil(_vmppt_min_sug / _vmp_panel_sug)) if _vmppt_min_sug else 8
    _n_serie_sug = int(st.session_state.get("N_serie") or _n_serie_elec_sug)

    # Bug real (29-ago-2026): N_paneles_granja no se invalidaba al cambiar de
    # inversor -- quedaba pegado al total del inversor ANTERIOR (ej. 126
    # paneles de un SNA-3K ya explorado) mientras N_serie ya reflejaba el
    # inversor NUEVO (ej. 7 del TriP 6K-HV), dando una "sugerencia real" que
    # en verdad mezclaba dos diseños distintos y no correspondía a ninguno.
    # Se usa solo si el inversor que produjo ese total sigue siendo el
    # actualmente seleccionado.
    _n_paneles_granja_sug = int(st.session_state.get("N_paneles_granja") or 0)
    _n_paneles_granja_vigente = (
        st.session_state.get("N_paneles_granja_inversor_ref") == inversor_nombre
    )
    _fuente_sug = None
    if _n_paneles_granja_sug > 0 and _n_serie_sug > 0 and _n_paneles_granja_vigente:
        _total_cadenas_sug = _n_paneles_granja_sug // _n_serie_sug
        _fuente_sug = "real"
        _detalle_sug = (
            f"{_n_paneles_granja_sug} paneles del Proyecto completo ÷ "
            f"{_n_serie_sug} módulos/string (mismo cálculo que usa ⚡ Diagrama Unifilar)"
        )
    else:
        _area_bruta_sug = float(st.session_state.get("area_fachada_m2", 97.34))
        _f_ocup_sug = float(st.session_state.get("factor_ocupacion_pct", 100.0))
        _area_util_sug = _area_bruta_sug * _f_ocup_sug / 100.0
        _area_panel_sug = float(panel.get("area_m2") or 0)
        _total_cadenas_sug = (
            int(_area_util_sug / _area_panel_sug / _n_serie_sug)
            if _area_panel_sug and _n_serie_sug else 0
        )
        if _total_cadenas_sug > 0:
            _fuente_sug = "area"
            _detalle_sug = (
                f"{_area_util_sug:.0f} m² de área disponible con ≈{_n_serie_sug} "
                "módulos/string (aproximado por área -- corre '▶️ Optimizar N "
                "paneles/string' más abajo para una cifra más exacta)"
            )

    N_total_cadenas = st.number_input(
        "N total de cadenas para el proyecto (opcional — referencia estándar internacional)",
        min_value=0, value=int(st.session_state.get("N_total_cadenas_proyecto", 0)),
        key="N_total_cadenas_proyecto",
        help=(
            "Si ya sabes cuántas cadenas quieres en TOTAL para todo el "
            "generador, ponlas aquí — se reparten solas entre los trackers "
            "del inversor, igual que en los software de simulación de "
            "referencia estándar internacional. "
            "Déjalo en 0 para que la app siga sugiriendo el máximo que "
            "soporta el inversor según el catálogo (mejor cuando aún estás "
            "explorando cuánto cabe, no verificando un diseño ya decidido)."
            + (
                f"  \n💡 Orientación: ~{_total_cadenas_sug} cadenas, desde {_detalle_sug}."
                if _fuente_sug else ""
            )
        ),
    )
    if _fuente_sug and int(N_total_cadenas) == 0:
        _icono_sug = "📐" if _fuente_sug == "real" else "💡"
        st.caption(
            f"{_icono_sug} Orientación (no vinculante): **~{_total_cadenas_sug} cadenas**, "
            f"desde {_detalle_sug}."
        )
        if _fuente_sug == "area" and _n_paneles_granja_sug > 0 and not _n_paneles_granja_vigente:
            st.caption(
                "ℹ️ Hay un total de Proyecto completo guardado, pero es de "
                f"**{st.session_state.get('N_paneles_granja_inversor_ref', 'otro inversor')}** "
                f"(no de **{inversor_nombre}**) -- corre \"▶️ Optimizar N paneles/string\" "
                "de nuevo con este inversor para una sugerencia real."
            )
    _res_n_str_tr = resolver_n_strings_tracker(
        inversor, inversor_nombre, st.session_state, N_total_cadenas=int(N_total_cadenas)
    )
    N_str_tr = st.number_input(
        "N_strings por tracker (vía combinadoras)",
        min_value=1, key="N_str_tr",
        help=(
            f"{'Calculado desde el total declarado arriba' if _res_n_str_tr['fuente'] == 'total' else f'Autocalculado del catálogo: {inversor_nombre} soporta'} "
            f"{_res_n_str_tr['sugerido']} strings/tracker. Ajústalo si tu "
            "diseño real usa una combinadora con menos strings."
        ),
    )
    if _res_n_str_tr["recalculado"] and _res_n_str_tr["fuente"] == "total":
        st.caption(
            f"🧮 Referencia estándar internacional: **{int(N_total_cadenas)}** cadenas totales ÷ "
            f"**{_res_n_str_tr['n_trackers']}** trackers = "
            f"**{_res_n_str_tr['sugerido']}** strings/tracker."
        )
    elif _res_n_str_tr["recalculado"]:
        st.caption(
            f"🔄 Autocalculado desde el catálogo: **{_res_n_str_tr['sugerido']}** "
            f"strings/tracker para **{inversor_nombre}**."
        )
    elif int(N_str_tr) != _res_n_str_tr["sugerido"]:
        _origen = (
            f"el total declarado ({int(N_total_cadenas)} cadenas)"
            if _res_n_str_tr["fuente"] == "total"
            else f"el catálogo de {inversor_nombre}"
        )
        st.caption(
            f"ℹ️ Ajuste manual — {_origen} sugiere "
            f"**{_res_n_str_tr['sugerido']}** strings/tracker."
        )
    col_nm1, col_nm2 = st.columns(2)
    with col_nm1:
        # Auto-calcular N_min eléctrico desde MPPT del inversor para evitar que
        # un restart resetee a 5 y el optimizador proponga N inviables para el MPPT
        # Vmppt_activo_min primero: es el piso real que evalúa optimizar_n_serie()
        # (semáforo v2/v3) más abajo -- usar Vmppt_min (arranque, no MPPT típico)
        # dejaba entrar al barrido configuraciones N que luego salían FALLA de
        # todos modos, con un N_min sugerido más bajo de lo real. Encontrado en
        # auditoría (27-ago-2026): para Growatt MAX 100KTL3 LV el N mínimo
        # eléctrico correcto es 21, no 5.
        _vmppt_min  = inversor.get("Vmppt_activo_min") or inversor.get("Vmppt_min") or 0
        _vmp_panel  = panel.get("Vmp_stc") or panel.get("Vmp") or 1
        _n_min_elec = max(1, math.ceil(_vmppt_min / _vmp_panel)) if _vmppt_min else 5
        # Bug real (29-ago-2026): el max(_n_min_elec, _n_min_guardado) de abajo
        # nunca BAJA -- si un inversor con Vmppt_activo_min alto (ej. Growatt
        # MAX 100KTL3 LV, 850V → N_min_elec=21) dejó N_min_scan=21 guardado, y
        # el usuario cambia a un inversor que necesita mucho menos (ej.
        # SOLIS-60K), el 21 sobrevive -- si N_max_scan sigue en su default
        # (20), N_min(21) > N_max(20) y optimizar_n_serie() devuelve una lista
        # vacía, haciendo TRONAR la página más abajo (KeyError de pandas al
        # estilizar un DataFrame sin columnas). Se resetea al valor eléctrico
        # fresco cada vez que cambia el inversor -- un ajuste manual posterior
        # para ESE MISMO inversor se sigue respetando igual que antes.
        if st.session_state.get("N_min_scan_inversor_ref") != inversor_nombre:
            st.session_state["N_min_scan"] = _n_min_elec
            st.session_state["N_min_scan_inversor_ref"] = inversor_nombre
        _n_min_guardado = int(
            st.session_state.get("N_min_scan", _n_min_elec)
        )
        _n_min_def = max(_n_min_elec, _n_min_guardado)
        _n_min_ajuste_manual = _n_min_def > _n_min_elec
        N_min_scan = st.number_input(
            (
                f"N mínimo a explorar "
                f"({'ajuste manual; eléctrico: ' + str(_n_min_elec) if _n_min_ajuste_manual else 'eléctrico: ' + str(_n_min_elec)})"
            ),
            value=_n_min_def, min_value=1, max_value=40, key="N_min_scan",
            help=f"Calculado como ⌈Vmppt_min({_vmppt_min}V) / Vmp_panel({_vmp_panel:.1f}V)⌉ = {_n_min_elec}"
        )
        if _n_min_ajuste_manual:
            st.caption(
                f"ℹ️ El mínimo eléctrico es **{_n_min_elec}**; se está explorando "
                f"desde **{_n_min_def}** por un valor manual guardado. "
                "Puedes reducirlo para incluir también configuraciones menores."
            )
    with col_nm2:
        N_max_scan = st.number_input("N máximo a explorar", value=int(st.session_state.get("N_max_scan", 20)), min_value=2, max_value=40, key="N_max_scan")

if N_min_scan > N_max_scan:
    st.warning(
        f"⚠️ N mínimo a explorar (**{int(N_min_scan)}**) es mayor que N máximo "
        f"(**{int(N_max_scan)}**) -- no hay ningún N que evaluar en ese rango. "
        "Sube el N máximo o baja el N mínimo antes de correr \"▶️ Optimizar N "
        "paneles/string\"."
    )

# ── Banner Motor Óptico ───────────────────────────────────────────────────────
_motor_ok_dim   = st.session_state.get("motor_optico_ok", False)
_mo_summary_dim = st.session_state.get("motor_optico_summary", {})
if _motor_ok_dim:
    _poa_ef_anual = st.session_state.get("poa_efectiva_anual_kWh_m2", 0.0)
    _factor_mo    = _mo_summary_dim.get("factor_global", 1.0)
    st.info(
        f"🔆 **Motor Óptico activo** — POA efectiva: **{_poa_ef_anual:,.0f} kWh/m²/año** "
        f"(factor global **{_factor_mo*100:.1f}%** = IAM + Soiling + Térmico).  \n"
        "El dimensionamiento eléctrico no depende de la POA; la corrección óptica se aplica "
        "automáticamente en 📊 **Producción** al simular."
    )

# Caption estable de temperaturas (siempre presente → evita removeChild de React)
if _t2m_dim is not None:
    st.caption(
        f"🌡️ Temperaturas desde el TMY de **{st.session_state.get('tmy_ciudad', '—')}** "
        f"(PVGIS {st.session_state.get('_solar_pvgis_guardada', '—')}) — "
        f"T_mín: {T_frio:.1f}°C · T_cel realista: {T_real:.1f}°C · "
        f"T_cel extremo: {T_extr:.1f}°C  "
        f"*(NOCT {_noct_dim:.0f}°C · editable manualmente)*"
    )
else:
    st.caption(
        f"🌡️ Sin año típico en esta sesión: T_mín {T_frio:.1f}°C · T_cel realista "
        f"{T_real:.1f}°C · T_cel extremo {T_extr:.1f}°C son los guardados o los de "
        "referencia de la ciudad. Abre ☀️ Recurso Solar para calcularlas desde el TMY."
    )

# (panel e inversor ya cargados arriba)
if panel.get("costo_usd"):
    st.session_state["costo_modulo_usd"] = panel["costo_usd"]

# ── Indicador de datos para Motor IV ──────────────────────────────────────────
# Este estado debe usar el mismo validador que el aviso superior y Motor IV:
# Voc/Isc/Vmp/Imp son obligatorios; N_s, tecnología y coeficientes tienen
# defaults. Evita mostrar simultáneamente "puede simularse" y "solo energético".
if not _iv_err:
    st.success(
        "🟢 Datos IV obligatorios completos — Motor IV se activará automáticamente"
    )
else:
    _faltantes_obligatorios = ", ".join(c for c, _ in _iv_err)
    st.error(
        f"🔴 Ficha incompleta para Motor IV — faltan: "
        f"{_faltantes_obligatorios} | solo cálculo energético"
    )
if _iv_adv and not _iv_err:
    _adv_motor = ", ".join(c for c, _ in _iv_adv)
    st.info(
        f"ℹ️ Motor IV usará estimaciones/defaults en: {_adv_motor}. "
        "La simulación estará disponible, pero con menor precisión."
    )
if panel.get("notas"):
    st.caption(f"📋 {panel['notas'][:120]}")

# ── Motor IV automático — curva IV real para paneles 🟢 ───────────────────────
if not _iv_err:  # Voc/Isc/Vmp/Imp presentes; opcionales usan defaults
    _panel_iv = preparar_panel_iv(panel)
    if _panel_iv is not None:
        # ── Alarma real de validación SDM vs ficha (#Motor IV) ────────────────
        # Antes, la única forma de enterarse de que un panel calibrado NO
        # reproduce su ficha técnica (>5% de error) era entrar manualmente a
        # 🔬 Motor IV y presionar el botón de validación -- sin ninguna alarma
        # en el resto de la app. Corre aquí automáticamente porque este panel
        # ya está resuelto en este punto de la página, sin costo de API (es
        # una comparación numérica determinista, no un agente de IA).
        if _panel_iv.get("_estimado"):
            st.session_state.pop("motor_iv_validacion_ok", None)
            st.session_state.pop("motor_iv_validacion_detalle", None)
            st.session_state.pop("motor_iv_validacion_panel", None)
        else:
            _val_sdm_dim = validar_sdm_vs_ficha(_panel_iv)
            st.session_state["motor_iv_validacion_ok"] = _val_sdm_dim["validacion_ok"]
            st.session_state["motor_iv_validacion_detalle"] = _val_sdm_dim
            st.session_state["motor_iv_validacion_panel"] = panel_nombre
            if _val_sdm_dim["validacion_ok"]:
                st.caption(
                    "✅ Motor IV: SDM validado contra la ficha técnica "
                    "(Voc/Isc/Vmp/Imp/Pmax dentro de 5% de error)."
                )
            else:
                st.error(explicar_fallo_validacion_sdm(panel_nombre, _val_sdm_dim))

        with st.expander("📈 Curva I-V real (Motor IV activado automáticamente)", expanded=False):
            _col_iv1, _col_iv2 = st.columns(2)
            with _col_iv1:
                _G_iv = st.slider("Irradiancia (W/m²)", 100, 1200, 1000, 100, key="iv_G")
                _T_iv = st.slider("T celda (°C)", 15, 75, 25, 5, key="iv_T")
            try:
                _res = resolver_curva_iv(float(_G_iv), float(_T_iv), _panel_iv, n_puntos=200)
                if _res["V"] is not None:
                    _V = _res["V"]
                    _I = _res["I"]
                    _P = _V * _I

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=list(_V), y=list(_I),
                        name="I-V", line=dict(color="#1f77b4", width=2),
                        yaxis="y1",
                    ))
                    fig.add_trace(go.Scatter(
                        x=list(_V), y=list(_P),
                        name="P-V", line=dict(color="#ff7f0e", width=2, dash="dash"),
                        yaxis="y2",
                    ))
                    # Punto MPP
                    fig.add_trace(go.Scatter(
                        x=[_res["Vmp"]], y=[_res["Pmax"]],
                        name=f"MPP ({_res['Pmax']:.1f} W)",
                        mode="markers",
                        marker=dict(size=10, color="red", symbol="star"),
                        yaxis="y2",
                    ))
                    fig.update_layout(
                        xaxis_title="Voltaje (V)",
                        yaxis=dict(title="Corriente (A)", side="left"),
                        yaxis2=dict(title="Potencia (W)", side="right", overlaying="y"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=340,
                        margin=dict(l=10, r=10, t=30, b=10),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Métricas STC
                    _mc1, _mc2, _mc3, _mc4, _mc5 = st.columns(5)
                    _mc1.metric("Voc", f"{_res['Voc']:.2f} V")
                    _mc2.metric("Isc", f"{_res['Isc']:.3f} A")
                    _mc3.metric("Vmp", f"{_res['Vmp']:.2f} V")
                    _mc4.metric("Imp", f"{_res['Imp']:.3f} A")
                    _mc5.metric("FF", f"{_res['FF']*100:.1f} %")

                    if _panel_iv.get("_estimado"):
                        _metodo = _panel_iv.get("_metodo", "fit_desoto")
                        st.caption(
                            f"⚠️ Parámetros SDM estimados vía **{_metodo}** desde ficha técnica "
                            f"(NsA={panel.get('NsA', '?')}, n={panel.get('n_idealidad', '?')}). "
                            "Resultado orientativo — para calibración exacta se requieren mediciones de laboratorio."
                        )
                    else:
                        st.caption("✅ Parámetros SDM calibrados directamente del catálogo.")
                else:
                    st.info("G=0 — introduce irradiancia > 0 para ver la curva.")
            except Exception as _e_iv:
                st.warning(f"Motor IV: no se pudo calcular la curva ({_e_iv})")

# ── Guardar panel en session_state para Motor IV automático (#7) ─────────────
st.session_state["panel_dict"]        = panel
st.session_state["panel_nombre_dim"]  = panel_nombre
# Spec 05/panel-por-superficie: si cambió el panel del proyecto y alguna
# superficie de 🗺️ Vista 3D lo sigue, se retira la energía multi-superficie
# publicada con el panel anterior (no esperar a abrir Vista 3D).
if st.session_state.get("superficies_bipv"):
    from calculos.panel_superficie import invalidar_por_cambio_panel as _inv_panel_ms
    if _inv_panel_ms(st.session_state):
        st.info(
            "ℹ️ Cambió el panel del proyecto: se retiró la energía multi-superficie "
            "publicada con el panel anterior. Vuelve a publicarla en 🗺️ Vista 3D."
        )
# inversor ya cargado antes de col2
if inversor.get("costo_usd"):
    st.session_state["costo_inversor_usd"] = inversor["costo_usd"]
# Propagar inversor a session_state para compatibilidad baterías (#25)
st.session_state["inversor_nombre_dim"] = inversor_nombre
st.session_state["inversor_dict_dim"]   = inversor

# ── 🔋 Compatibilidad con la batería ya configurada (hueco #1, 1-sep-2026) ────
# Antes, este selector no sabía nada de baterías -- se podía cambiar
# libremente a cualquier inversor (incluido uno de string, sin puerto DC)
# sin ninguna alerta, aunque el proyecto ya tuviera una batería configurada
# en 🔋 Baterías y Balance. La verificación real solo ocurría ahí, nunca
# "hacia arriba" en este selector. Misma función pura que ya usan la
# página 11 y ⚡ Diagrama Unifilar (mismo fix aplicado ahí el mismo día
# para el hueco #2 de staleness) -- re-verificada aquí, en vivo, contra el
# inversor recién seleccionado. Solo se muestra si YA hay una batería
# configurada (session_state["bateria_dict"]); un proyecto sin batería no
# ve nada -- nunca inventa la alerta.
_bateria_dict_dim = st.session_state.get("bateria_dict")
if _bateria_dict_dim:
    _bat_estado_dim, _bat_msg_dim = _check_compat_bateria_dim(
        _bateria_dict_dim, inversor, inversor_nombre
    )
    _bat_contexto_dim = (
        "🔋 Ya tienes una batería configurada en 🔋 Baterías y Balance — "
        "verificación contra el inversor seleccionado aquí:  \n"
    )
    if _bat_estado_dim == "error":
        st.error(_bat_contexto_dim + _bat_msg_dim)
    elif _bat_estado_dim == "warning":
        st.warning(_bat_contexto_dim + _bat_msg_dim)
    else:
        st.caption(_bat_contexto_dim + _bat_msg_dim)

if inversor.get("datos_completos"):
    st.success("🟢 Inversor: ficha completa")
else:
    _inv_falt = [k for k in ["Vdc_max","Vmppt_min","Vmppt_max","n_trackers","n_strings_tracker","I_max_tracker","P_dc_max_W"] if not inversor.get(k)]
    st.warning(f"🟡 Inversor incompleto — faltan: {', '.join(_inv_falt)}" if _inv_falt else "🟡 Inversor marcado como incompleto en catálogo")

# ── 🌎 Auditoría de compatibilidad regional (31-ago-2026) ─────────────────────
# Pedido explícito del usuario: "que la app reconozca -- con los mismos
# criterios reales que ya documentaste (GHI, temperatura, humedad, fenómenos
# críticos) -- si ese panel/tecnología simplemente no encaja con esa región".
# Matriz portada 1:1 desde la app hermana bipv.innovacionquimica.com.co (no
# reinventada) -- juicio experto real por familia de producto (estructural,
# estética, salinidad, logística), no solo energía. Alarma informativa, NO
# bloqueante -- nunca impide continuar. No aparece si no se puede clasificar
# con evidencia positiva la familia del panel (ver calculos/compatibilidad_
# regional.py -- nunca falsa precisión).
_ciudad_dim = st.session_state.get("ciudad") or st.session_state.get("tmy_ciudad")
if _ciudad_dim:
    from calculos.compatibilidad_regional import evaluar_compatibilidad_regional_desde_ciudad
    # marca/texto_adicional -- bug real corregido 6-sep-2026: sin la marca,
    # 5 de las 21 familias de la matriz eran inalcanzables (ej. un panel
    # EINNOVA real con "Tile" en Tecnologia siempre resolvía a la familia
    # HIITIO/EINNOVA por defecto, nunca a la variante correcta de su propia
    # marca). "nombre"+"notas" llevan la palabra que a veces falta en
    # "tecnologia" (ej. "plana" está en Notas, no en Tecnologia, para
    # distinguir teja plana de teja BC). Ver calculos.compatibilidad_regional.
    _compat_regional = evaluar_compatibilidad_regional_desde_ciudad(
        panel.get("tecnologia"), _ciudad_dim,
        marca=panel.get("marca"),
        texto_adicional=f"{panel.get('nombre', '')} {panel.get('notas', '')}",
    )
    if _compat_regional:
        _msg_regional = (
            f"{_compat_regional['icono']} **Compatibilidad regional — {_compat_regional['region_etiqueta']}**: "
            f"{panel_nombre} está calificado como **{_compat_regional['nivel'].replace('_', ' ')}** "
            f"para esta región (auditoría de juicio experto, no un veredicto). {_compat_regional['notas']}"
        )
        if _compat_regional["score"] == 1:
            st.error(_msg_regional)
        elif _compat_regional["score"] == 2:
            st.warning(_msg_regional)
        else:
            st.caption(_msg_regional)
    st.session_state["compatibilidad_regional_bipv"] = _compat_regional

# ── Vigencia del diseño confirmado (31-ago-2026) ──────────────────────────────
# El resultado de "▶️ Optimizar N paneles/string" solo se redibuja en el mismo
# render donde se oprime el botón -- si después cambias panel/inversor sin
# volver a oprimirlo, esa tabla simplemente desaparece de la vista sin avisar
# que N_serie/N_str_tr_usado (lo que Producción y el resto ya están usando)
# quedó apuntando al diseño viejo. Este aviso persiste independientemente de
# si el botón se oprimió en este render o no.
_diseno_vigencia = diseno_electrico_confirmado(st.session_state)
if _diseno_vigencia["aviso"]:
    st.warning(_diseno_vigencia["aviso"])
elif _diseno_vigencia["N_serie"]:
    st.caption(
        f"✅ Diseño confirmado vigente: N={_diseno_vigencia['N_serie']} en serie, "
        f"{_diseno_vigencia['N_strings_tracker']} string(s)/tracker, con "
        f"{panel_nombre} / {inversor_nombre}."
    )

st.markdown("---")
st.subheader("🧭 Mapeo de inversores opcionales para este panel")
st.caption(
    "Esta es una regla eléctrica informativa: se evalúa todo el catálogo contra "
    "el rango de N/string indicado. Puedes cargar un modelo compatible para "
    "actualizar la selección y obtener un prorrateo preliminar."
)
with st.container(border=True):
    st.caption(
        "✅ **Regla aplicada:** un inversor es opcional si al menos un "
        "**N/string** del rango explorado cumple simultáneamente Voc en frío, "
        "MPPT mínimo y máximo, y corriente máxima por tracker. "
        "El rango de este mapeo es independiente del inversor seleccionado. "
        "La selección del proyecto solo cambia cuando confirmas el botón de carga."
    )
    _map_c1, _map_c2 = st.columns(2)
    with _map_c1:
        _n_min_mapeo = st.number_input(
            "N mínimo para el mapeo",
            min_value=1,
            max_value=40,
            value=1,
            step=1,
            key="N_min_mapeo_inversores",
        )
    with _map_c2:
        _n_max_mapeo = st.number_input(
            "N máximo para el mapeo",
            min_value=1,
            max_value=40,
            value=max(20, int(N_max_scan)),
            step=1,
            key="N_max_mapeo_inversores",
        )
    if _n_max_mapeo < _n_min_mapeo:
        st.warning("El N máximo debe ser igual o mayor que el N mínimo.")
        _n_max_mapeo = _n_min_mapeo
    _cat_inv_mapeo = _cat_inv or INVERSORES
    _mapeo_inv = mapear_inversores_catalogo(
        panel=panel,
        inversores=_cat_inv_mapeo,
        N_min=int(_n_min_mapeo),
        N_max=int(_n_max_mapeo),
        T_frio=float(T_frio),
        T_real=float(T_real),
        T_extremo=float(T_extr),
        N_strings_tracker=int(N_str_tr),
    )
    _df_mapeo = pd.DataFrame(_mapeo_inv)
    _n_mapeo_ok = sum(fila["compatible"] for fila in _mapeo_inv)
    _n_mapeo_no_eval = sum(fila["estado"] == "🟡 No evaluable" for fila in _mapeo_inv)
    _n_mapeo_rech = len(_mapeo_inv) - _n_mapeo_ok - _n_mapeo_no_eval
    _mc1, _mc2, _mc3 = st.columns(3)
    _mc1.metric("✅ Compatibles", _n_mapeo_ok)
    _mc2.metric("🔴 No compatibles", _n_mapeo_rech)
    _mc3.metric("🟡 No evaluables", _n_mapeo_no_eval)
    st.caption(
        f"Panel evaluado: **{panel_nombre}** · rango mapeado: "
        f"**N={int(_n_min_mapeo)}–{int(_n_max_mapeo)} módulos/string** · "
        f"{len(_mapeo_inv)} inversores del catálogo."
    )
    if not _df_mapeo.empty:
        _cols_mapeo = [
            "modelo", "estado", "N_string_recomendado",
            "recomendado_con_margen_ajustado", "N_viables",
            "Voc_frio_V", "Vmp_real_V", "Isc_tracker_A", "Vdc_max_V",
            "MPPT_V", "trackers", "strings_tracker", "P_ac_nom_kW",
            "costo_usd", "motivo",
        ]
        _sel_mapeo = st.dataframe(
            _df_mapeo[_cols_mapeo],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="tabla_mapeo_inversores",
            column_config={
                "recomendado_con_margen_ajustado": st.column_config.CheckboxColumn(
                    "⚠️ Margen ajustado",
                    help=(
                        "El N recomendado pasa los límites eléctricos, pero con menos "
                        "del 7,5% de margen de seguridad (mismo umbral que usa "
                        "'▶️ Optimizar N paneles/string') -- considera un N menor si "
                        "quieres más colchón."
                    ),
                ),
            },
        )
        st.caption(
            "💡 Haz clic en una fila de la tabla para llevar ese modelo "
            "directamente a la casilla «Inversor compatible» de abajo."
        )
        _modelo_click_tabla = ""
        try:
            _filas_sel = _sel_mapeo.selection.rows
            if _filas_sel:
                _modelo_click_tabla = str(
                    _df_mapeo[_cols_mapeo].iloc[_filas_sel[0]]["modelo"]
                )
        except Exception:
            _modelo_click_tabla = ""
        _compatibles_mapeo = [
            fila for fila in _mapeo_inv
            if fila.get("compatible") and fila.get("N_string_recomendado")
        ]
        if _compatibles_mapeo:
            st.markdown("#### ⚡ Cargar un inversor compatible")
            st.caption(
                "Selecciona un modelo compatible para cargar su ficha en el selector "
                "principal y recalcular automáticamente un prorrateo preliminar."
            )
            _compatibles_por_nombre = {
                fila["modelo"]: fila for fila in _compatibles_mapeo
            }
            _opciones_compatibles = list(_compatibles_por_nombre)
            # Clic en la tabla → llevar el modelo a la casilla de abajo.
            # Solo cuando la selección de la tabla CAMBIA (no en cada rerun),
            # y ANTES de instanciar el selectbox (patrón widgets keyed).
            if (
                _modelo_click_tabla
                and _modelo_click_tabla
                != st.session_state.get("_ultimo_modelo_click_tabla", "")
            ):
                st.session_state["_ultimo_modelo_click_tabla"] = _modelo_click_tabla
                if _modelo_click_tabla in _opciones_compatibles:
                    st.session_state["selector_inversor_compatible_mapeo"] = (
                        _modelo_click_tabla
                    )
                else:
                    st.warning(
                        f"**{_modelo_click_tabla}** no es compatible con este "
                        "panel en el rango de N/string mapeado, así que no se "
                        "puede cargar en la casilla."
                    )
            _modelo_prelim_default = st.session_state.get(
                "prorrateo_preliminar_modelo", ""
            )
            _idx_compatible = (
                _opciones_compatibles.index(_modelo_prelim_default)
                if _modelo_prelim_default in _opciones_compatibles
                else 0
            )
            _modelo_compatible = st.selectbox(
                "Inversor compatible",
                _opciones_compatibles,
                index=_idx_compatible,
                format_func=lambda modelo: (
                    f"{modelo} · N/string recomendado: "
                    f"{_compatibles_por_nombre[modelo]['N_string_recomendado']}"
                    + (
                        " ⚠️ margen ajustado"
                        if _compatibles_por_nombre[modelo].get("recomendado_con_margen_ajustado")
                        else ""
                    )
                ),
                key="selector_inversor_compatible_mapeo",
            )
            _fila_compatible = _compatibles_por_nombre[_modelo_compatible]
            if st.button(
                "⚡ Cargar y recalcular prorrateo preliminar",
                type="primary",
                key="cargar_inversor_compatible_mapeo",
            ):
                st.session_state["_inversor_nombre_dim_pendiente"] = _modelo_compatible
                st.session_state["inversor_nombre_dim"] = _modelo_compatible
                st.session_state["N_serie"] = int(
                    _fila_compatible["N_string_recomendado"]
                )
                # Resultado (sobrevive F5, a diferencia de la key del widget)
                st.session_state["N_str_tr_usado"] = int(N_str_tr)
                # Referencia de vigencia (31-ago-2026, ver
                # diseno_electrico_confirmado()): con qué panel/inversor se
                # confirmó este N -- si cualquiera de los dos cambia después
                # sin volver a confirmar, esa función avisa sola.
                st.session_state["N_serie_panel_ref"] = panel_nombre
                st.session_state["N_serie_inversor_ref"] = _modelo_compatible
                # Clave PROPIA del prorrateo (distinta de N_str_tr_usado, que
                # también escribe el botón "Optimizar N paneles/string" más
                # abajo para su propio propósito) -- evita que ese otro botón
                # "refresque" por accidente la validez de este cálculo.
                st.session_state["prorrateo_preliminar_n_str_tr"] = int(N_str_tr)
                st.session_state["prorrateo_preliminar_modelo"] = _modelo_compatible
                st.session_state["prorrateo_preliminar_N"] = int(
                    _fila_compatible["N_string_recomendado"]
                )
                st.session_state["prorrateo_preliminar_alerta_margen"] = bool(
                    _fila_compatible.get("recomendado_con_margen_ajustado")
                )
                st.session_state["prorrateo_preliminar_panel"] = panel_nombre
                # #225 — persistir también al cargar un compatible
                guardar_seleccion_equipos(_auth_email_dim, panel_nombre, _modelo_compatible)
                st.session_state["panel_pref_persistido"] = panel_nombre
                st.rerun()
        else:
            st.info(
                "No hay inversores compatibles con el rango N/string seleccionado. "
                "Amplía el rango o revisa los datos eléctricos del catálogo."
            )
        st.download_button(
            "⬇️ Descargar mapeo de inversores (CSV)",
            _df_mapeo.to_csv(index=False).encode("utf-8-sig"),
            "mapeo_inversores_panel.csv",
            "text/csv",
            key="descargar_mapeo_inversores_panel",
        )

# ── Prorrateo preliminar desde un inversor compatible del mapeo ───────────────
_prelim_modelo = st.session_state.get("prorrateo_preliminar_modelo")
_prelim_n = st.session_state.get("prorrateo_preliminar_N")
if _prelim_modelo and (
    _prelim_modelo != inversor_nombre
    or st.session_state.get("prorrateo_preliminar_panel") != panel_nombre
    # Bug real (29-ago-2026): el N recomendado se guardaba en el momento del
    # clic y NUNCA se invalidaba si el usuario cambiaba después "N total de
    # cadenas para el proyecto" o ajustaba N_strings/tracker a mano -- el N
    # (viejo) se combinaba con el N_str_tr (nuevo) en dimensionar_sistema()
    # más abajo, dando un "Paneles/inversor" que no correspondía a NINGUNA
    # recomendación real (encontrado con TriP 6K-HV: 128 paneles/inversor
    # usando N=8 viejo × N_str_tr=8 nuevo, cuando el N recomendado real para
    # N_str_tr=8 es 7, no 8). Invalida también si N_str_tr cambió desde el
    # último cálculo.
    or st.session_state.get("prorrateo_preliminar_n_str_tr") != int(N_str_tr)
):
    # Evita presentar un cálculo anterior después de una selección manual,
    # al cambiar de panel, o al cambiar N_strings/tracker (catálogo o total
    # declarado) -- el N recomendado podría ya no aplicar.
    st.session_state.pop("prorrateo_preliminar_modelo", None)
    st.session_state.pop("prorrateo_preliminar_N", None)
    st.session_state.pop("prorrateo_preliminar_panel", None)
    st.session_state.pop("prorrateo_preliminar_alerta_margen", None)
    st.session_state.pop("prorrateo_preliminar_n_str_tr", None)
    _prelim_modelo = None
    _prelim_n = None
def _mostrar_proyecto_completo(pc: dict, area_util: float, f_ocup: float,
                               N_serie: int, modelo: str, nivel_titulo: str) -> None:
    """Muestra y publica «🏭 Proyecto completo» (Spec
    03-dimensionamiento/proyecto-completo): strings completos que caben en el
    área útil o los declarados, repartidos entre los inversores necesarios."""
    _tit = "área útil para paneles" if f_ocup < 100.0 else "toda el área"
    st.markdown(f"{nivel_titulo} 🏭 Proyecto completo ({_tit})")
    _g1, _g2, _g3, _g4, _g5 = st.columns(5)
    _g1.metric("Inversores", pc["N_inversores"])
    _g2.metric("Paneles totales", f"{pc['N_paneles']:,}")
    _g3.metric("kWp instalados", f"{pc['P_dc_kWp']:,.1f} kWp")
    _g4.metric("Área cubierta", f"{pc['area_m2']:,.0f} m²")
    _g5.metric("Cobertura del área útil" if f_ocup < 100.0 else "Cobertura total",
               f"{pc['cobertura_pct']} %",
               help=f"Área de los módulos ÷ {area_util:,.0f} m² útiles. Puede pasar "
                    "de 100 % solo si declaraste más cadenas de las que caben.")
    if pc["fuente"] == "declarado":
        _origen = "declarados en «N total de cadenas»"
    else:
        _origen = (f"los que caben en {area_util:,.0f} m² útiles: ⌊{area_util:,.0f} ÷ "
                   f"({N_serie} × área del módulo)⌋")
    if pc["N_inversores"]:
        st.caption(
            f"🧮 **{pc['N_strings_total']} strings** de {N_serie} módulos ({_origen}). "
            f"Un inversor admite {pc['capacidad_strings_inversor']} strings (MPPT × strings "
            f"por MPPT) → **{pc['N_inversores']} inversor(es)**, reparto "
            f"**{' + '.join(str(x) for x in pc['reparto'])}** strings."
        )
    if not pc["cabe"]:
        if pc["N_strings_total"] == 0:
            st.error(
                f"🔴 No cabe ni un string de {N_serie} módulos: necesita "
                f"{pc['faltan_m2'] + area_util:,.0f} m² y el área útil es "
                f"{area_util:,.0f} m². Revisa el área en 🏠 Proyecto o baja N en serie."
            )
        else:
            st.error(
                f"🔴 Las {pc['N_strings_total']} cadenas declaradas ocupan "
                f"{pc['area_m2']:,.0f} m² y el área útil es {area_util:,.0f} m²: "
                f"faltan **{pc['faltan_m2']:,.0f} m²**. Baja «N total de cadenas» o "
                "revisa el área y el factor de ocupación en 🏠 Proyecto."
            )
    _dc = pc["dcac"]
    if _dc["evaluable"]:
        _txt = (f"**Relación DC/AC del proyecto = {_dc['ratio']:.2f}** "
                f"({pc['P_dc_kWp']:,.1f} kWp ÷ {pc['N_inversores']} inversor(es))"
                + (f" · inversor más cargado: {pc['dcac_max_inversor']:.2f}"
                   if pc["dcac_max_inversor"] and pc["N_inversores"] > 1 else "")
                + f"  \n{_dc['mensaje']}")
        {"🔴": st.error, "🟠": st.warning}.get(_dc["nivel"], st.success)(f"{_dc['nivel']} {_txt}")
    elif pc["N_inversores"]:
        from calculos.potencia_ac_inversor import MENSAJE_SIN_POTENCIA_AC
        st.info(f"🟡 {MENSAJE_SIN_POTENCIA_AC}")
    st.session_state["N_inv_total"] = pc["N_inversores"]
    st.session_state["P_dc_total_kWp"] = round(pc["P_dc_kWp"], 2)
    st.session_state["N_paneles_granja"] = pc["N_paneles"]
    st.session_state["N_paneles_granja_inversor_ref"] = modelo
    st.session_state["reparto_strings_inversores"] = list(pc["reparto"])


if _prelim_modelo and _prelim_n:
    _prelim_inversor = obtener_inversor_excel(_prelim_modelo) if _cat_inv else (
        seleccionar_inversor(_prelim_modelo)
    )
    try:
        _prelim_n = int(_prelim_n)
        _prelim_n_mppt = int(
            float(
                _prelim_inversor.get("N_mppt")
                or _prelim_inversor.get("n_trackers")
                or 0
            )
        )
    except (TypeError, ValueError):
        _prelim_n_mppt = 0
    if _prelim_n_mppt > 0:
        _prelim_area_bruta = float(
            st.session_state.get("area_fachada_m2", 97.34)
        )
        _prelim_f_ocup = float(
            st.session_state.get("factor_ocupacion_pct", 100.0)
        )
        _prelim_area = _prelim_area_bruta * _prelim_f_ocup / 100.0
        _prelim_dim = dimensionar_sistema(
            panel,
            _prelim_area,
            _prelim_n,
            int(N_str_tr),
            _prelim_n_mppt,
        )
        st.markdown("### ⚡ Prorrateo preliminar del inversor cargado")
        st.success(
            f"✅ **{_prelim_modelo}** cargado desde el mapeo · "
            f"**{_prelim_n} módulos/string** · "
            f"{_prelim_n_mppt} tracker(s)"
        )
        if st.session_state.get("prorrateo_preliminar_alerta_margen"):
            st.warning(
                "⚠️ Este N/string es eléctricamente compatible, pero pasa "
                "los límites del inversor con **menos del 7,5% de margen de "
                "seguridad** (mismo umbral que usa '▶️ Optimizar N paneles/"
                "string' más abajo). Considera bajar un N/string si prefieres "
                "más colchón para el proyecto real."
            )
        _pc1, _pc2, _pc3, _pc4 = st.columns(4)
        _pc1.metric("Paneles / inversor", _prelim_dim["N_paneles"])
        _pc2.metric("P_DC / inversor", f"{_prelim_dim['P_dc_stc_kW']:.2f} kW")
        _pc3.metric("Área / inversor", f"{_prelim_dim['area_ocupada_m2']} m²")
        _pc4.metric("Cobertura unitaria", f"{_prelim_dim['cobertura_pct']}%")

        _prelim_pc = proyecto_completo(
            panel, _prelim_area, _prelim_n, int(N_str_tr), _prelim_n_mppt,
            N_total_cadenas=int(N_total_cadenas),
            P_ac_nom_W=_prelim_inversor.get("P_ac_nom_W"),
        )
        _mostrar_proyecto_completo(_prelim_pc, _prelim_area, _prelim_f_ocup,
                                   _prelim_n, _prelim_modelo, "####")
    else:
        st.warning(
            f"El inversor **{_prelim_modelo}** no tiene un número válido de "
            "trackers para calcular el prorrateo preliminar."
        )

# ── #122 — Diagnóstico del catálogo de inversores (patrón #24 de baterías) ───
_diag_inv = _diag_inv_fn(mtime=_mtime_inv())
if _diag_inv["estado"] == "error":
    st.error(
        f"🔴 **Catálogo de inversores con problemas** — "
        f"{_diag_inv.get('detalle', 'faltan columnas críticas')}.  \n"
        f"Columnas críticas ausentes: "
        f"{', '.join(_diag_inv['columnas_criticas_faltantes']) or '—'}. "
        f"El dimensionamiento de strings puede salir incorrecto."
    )
elif _diag_inv["estado"] == "parcial":
    _resumen_p = []
    if _diag_inv["columnas_importantes_faltantes"]:
        _resumen_p.append(f"{len(_diag_inv['columnas_importantes_faltantes'])} columnas importantes ausentes")
    if _diag_inv["modelos_duplicados"]:
        _resumen_p.append(f"{len(_diag_inv['modelos_duplicados'])} modelos duplicados")
    if _diag_inv["modelos_incompletos"]:
        _resumen_p.append(f"{len(_diag_inv['modelos_incompletos'])} modelos incompletos")
    st.warning(f"🟡 Catálogo de inversores parcial: {' · '.join(_resumen_p)} — detalles abajo.")

with st.expander("🔍 Diagnóstico del catálogo de inversores", expanded=False):
    st.caption(f"Hoja usada: `{_diag_inv.get('hoja_usada', '—')}` · "
               f"Modelos cargados: **{_diag_inv.get('modelos_cargados', 0)}** · "
               f"Hojas en el Excel: {', '.join(_diag_inv.get('hojas_disponibles', []))}")
    if _diag_inv["columnas_criticas_faltantes"]:
        st.error("🔴 Columnas críticas ausentes: "
                 + ", ".join(f"`{c}`" for c in _diag_inv["columnas_criticas_faltantes"]))
    if _diag_inv["columnas_importantes_faltantes"]:
        st.warning("🟡 Columnas importantes ausentes: "
                   + ", ".join(f"`{c}`" for c in _diag_inv["columnas_importantes_faltantes"]))
    for _d in _diag_inv["modelos_duplicados"]:
        st.warning(f"🟡 **{_d['modelo']}** aparece {len(_d['filas_excel'])} veces "
                   f"(filas Excel {_d['filas_excel']}) — solo la última fila se usa.")
    for _m in _diag_inv["modelos_incompletos"]:
        st.info(f"ℹ️ **{_m['modelo']}**: faltan {', '.join(_m['campos_faltantes'])}")
    if _diag_inv["estado"] == "ok":
        st.success("🟢 Catálogo OK — columnas completas, sin duplicados ni modelos incompletos.")
    if st.button("🔄 Recargar catálogo de inversores", key="_reload_cat_inv",
                 help="Vuelve a leer el Excel del servidor (limpia la caché)."):
        _cargar_cat_inv.clear()
        _diag_inv_fn.clear()
        st.rerun()

if st.button("▶️ Optimizar N paneles/string", type="primary"):
    resultados = optimizar_n_serie(
        panel, inversor,
        T_frio=T_frio, T_real=T_real, T_extremo=T_extr,
        N_strings_tracker=int(N_str_tr),
        N_min=int(N_min_scan), N_max=int(N_max_scan),
    )

    # Bug real (29-ago-2026): con N_min_scan > N_max_scan, optimizar_n_serie()
    # recorre un range() vacío y retorna una lista vacía -- pd.DataFrame([])
    # sale sin columnas, y el .style.map(subset=[...]) más abajo revienta con
    # KeyError ("None of [...] are in the [columns]"), tumbando la página con
    # un traceback crudo. Encontrado con Growatt MAX 100KTL3 LV → SOLIS-60K:
    # N_min_scan había quedado pegado en 21 (el mínimo eléctrico del Growatt,
    # ver comentario de "N_min eléctrico" arriba) por el max() que nunca baja
    # el valor guardado al cambiar de inversor, mientras N_max_scan seguía en
    # el default 20 -- 21 > 20, rango vacío. Guard explícito en vez de dejar
    # que pandas/Streamlit revienten con un traceback ilegible para el usuario.
    if not resultados:
        st.error(
            f"🔴 No hay ningún N/string que evaluar: **N mínimo a explorar "
            f"({int(N_min_scan)})** es mayor que **N máximo ({int(N_max_scan)})**. "
            "Sube el N máximo o baja el N mínimo arriba, y vuelve a intentar."
        )
        st.stop()

    filas = []
    for r in resultados:
        filas.append({
            "N/string": r.N_serie,
            "Voc frío (V)": r.Voc_frio,
            "Vmp realista (V)": r.Vmp_real,
            "Vmp extremo (V)": r.Vmp_extremo,
            "I equiv (A)": r.I_equiv_tracker,
            "1-Voc≤Vdc": r.v1_voc_max,
            "2-Vmp≥Vmppt_min": r.v2_vmp_real,
            "3-Vmp_ext≥Vmppt_min": r.v3_vmp_extr,
            "4-I≤Imax": r.v4_i_max,
            "5-Vmp≤Vmppt_max": r.v5_vmp_max,
            "MPPT util %": r.mppt_util_pct,
            "Riesgos": r.riesgos,
            "": r.semaforo_color(),
        })

    df = pd.DataFrame(filas)

    def colorear(val):
        if val == "FALLA":
            return "background-color: #FFCCCC; color: #CC0000; font-weight: bold"
        elif val == "ALERTA":
            return "background-color: #FFF3CD; color: #856404; font-weight: bold"
        elif val == "OK":
            return "background-color: #D4EDDA; color: #155724; font-weight: bold"
        return ""

    styled = df.style.map(colorear,
                          subset=["1-Voc≤Vdc", "2-Vmp≥Vmppt_min",
                                  "3-Vmp_ext≥Vmppt_min", "4-I≤Imax",
                                  "5-Vmp≤Vmppt_max"])
    st.dataframe(styled, use_container_width=True)

    # Mejor opción: N con 0 riesgos y MÁXIMA utilización del rango MPPT
    # (Vmp_real / Vmppt_max). Con el check v5 activo, candidatos con Vmp > Vmppt_max
    # ya quedan excluidos por riesgos > 0, así que max(mppt_util_pct) es seguro.
    sin_riesgos = [r for r in resultados if r.riesgos == 0]
    if sin_riesgos:
        mejor = max(sin_riesgos, key=lambda r: r.mppt_util_pct if r.mppt_util_pct > 0 else r.Vmp_real)
        _util_msg = f" · {mejor.mppt_util_pct:.1f}% MPPT" if mejor.mppt_util_pct > 0 else ""
        st.success(
            f"✅ N óptimo = **{mejor.N_serie} paneles/string** — "
            f"0 riesgos · Vmp = {mejor.Vmp_real:.1f} V{_util_msg}"
        )
        st.session_state["N_serie"] = mejor.N_serie
        st.session_state["N_str_tr_usado"] = int(N_str_tr)
        # Referencia de vigencia (31-ago-2026, ver diseno_electrico_confirmado()):
        # con qué panel/inversor se confirmó este N.
        st.session_state["N_serie_panel_ref"] = panel_nombre
        st.session_state["N_serie_inversor_ref"] = inversor_nombre

        # ── Gráfico Voc/Vmp vs. temperatura + interpretación del N elegido ────
        # Visibilizado también aquí (pedido explícito del usuario, 30-ago-2026,
        # tras agregarlo primero al Reporte PDF y luego a 📊 Producción): este
        # es el módulo donde el usuario elige el N/string, así que ver de una
        # vez el comportamiento eléctrico completo del N óptimo (no solo el
        # semáforo OK/ALERTA/FALLA de la tabla de arriba) evita tener que ir
        # a otra página para confirmar el margen real de cada punto.
        _curva_dim = curva_electrica_temperatura(
            panel, inversor, mejor.N_serie,
            T_frio=T_frio, T_real=T_real, T_extremo=T_extr,
            N_strings_tracker=int(N_str_tr),
        )
        if _curva_dim.get("voc_curva") and _curva_dim.get("vmp_curva"):
            with st.expander(
                "⚡ Compatibilidad eléctrica string–inversor vs. temperatura "
                f"(N={mejor.N_serie})",
                expanded=False,
            ):
                fig_dim = figura_compatibilidad_electrica(
                    _curva_dim, T_frio, T_real, T_extr
                )
                st.plotly_chart(fig_dim, use_container_width=True)
                st.caption(
                    "Voc y Vmp son funciones lineales de la temperatura de celda: los 3 "
                    "puntos de diseño (frío, real, extremo) cubren con certeza matemática "
                    "toda la curva continua entre ellos — este gráfico visualiza el mismo "
                    "resultado de la tabla de arriba, no evalúa nada distinto."
                )
                for _p in interpretar_curva_electrica(_curva_dim):
                    _icono = {"ok": "🟢", "ajustado": "🟠", "critico": "🔴"}[_p["nivel"]]
                    _texto_p = f"{_icono} **{_p['punto']}** — {_p['texto']}"
                    if _p["nivel"] == "critico":
                        st.error(_texto_p)
                    elif _p["nivel"] == "ajustado":
                        st.warning(_texto_p)
                    else:
                        st.caption(_texto_p)

        # Dimensionamiento del sistema — respeta el factor de ocupación
        # (Granja fotovoltaica: los paneles solo cubren un % del terreno; el
        # resto queda libre para el cultivo. Otros tipos: ver mensaje neutro
        # abajo -- bug real corregido 29-ago-2026, ver 🏠 Proyecto)
        _area_bruta = float(st.session_state.get("area_fachada_m2", 97.34))
        _f_ocup     = float(st.session_state.get("factor_ocupacion_pct", 100.0))
        _tipo_inst_ocup = st.session_state.get("tipo_instalacion", "")
        area        = _area_bruta * _f_ocup / 100.0
        if _f_ocup < 100.0 and _tipo_inst_ocup == "Granja fotovoltaica":
            st.info(
                f"🌱 **Factor de ocupación {_f_ocup:.0f}%** — de los "
                f"{_area_bruta:,.0f} m² del terreno solo se dimensionan paneles "
                f"sobre **{area:,.0f} m²**; el resto queda libre para el cultivo. "
                f"(Se ajusta en 🏠 Proyecto.)"
            )
        elif _f_ocup < 100.0:
            st.info(
                f"ℹ️ **Factor de ocupación {_f_ocup:.0f}%** — de los "
                f"{_area_bruta:,.0f} m² disponibles solo se dimensionan paneles "
                f"sobre **{area:,.0f} m²**; el resto no se cubre con paneles. "
                f"(Se ajusta en 🏠 Proyecto.)"
            )
        dim  = dimensionar_sistema(panel, area, mejor.N_serie,
                                    int(N_str_tr), inversor["N_mppt"])

        st.markdown("### 📊 Un inversor lleno (todos sus MPPT)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Paneles / inversor", dim["N_paneles"])
        c2.metric("P_DC / inversor",    f"{dim['P_dc_stc_kW']:.2f} kW")
        c3.metric("Área / inversor",    f"{dim['area_ocupada_m2']} m²")
        c4.metric("Cobertura unitaria", f"{dim['cobertura_pct']}%")

        # Relación DC/AC -- homóloga al aviso real de PVsyst 8.1.5 ("Proporción
        # Pnom", Teusaquillo 29-ago-2026). Desde el 29-sep-2026 se evalúa con el
        # sistema real del Proyecto completo, no con un inversor lleno (Spec
        # 03-dimensionamiento/proyecto-completo).
        _pc = proyecto_completo(
            panel, area, mejor.N_serie, int(N_str_tr), inversor["N_mppt"],
            N_total_cadenas=int(N_total_cadenas),
            P_ac_nom_W=inversor.get("P_ac_nom_W"),
        )
        _mostrar_proyecto_completo(_pc, area, _f_ocup, mejor.N_serie, inversor_nombre, "###")
    else:
        st.error("❌ Ningún N válido en el rango. Revisar parámetros del inversor o temperaturas.")
