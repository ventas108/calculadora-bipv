"""
Página 20 — Diagrama Unifilar (Fase 1 + Fase 2: batería)
Generador universal de diagrama unifilar para proyectos FV y BIPV.
Auto-llenado desde el panel/inversor configurados en Dimensionamiento y la
batería configurada en 🔋 Baterías y Balance, si existe.
"""
import streamlit as st

from calculos.diagrama_unifilar import (
    construir_config_unifilar,
    generar_diagrama_unifilar,
    exportar_unifilar_bytes,
)

st.set_page_config(page_title="Diagrama Unifilar", page_icon="⚡", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()
st.title("⚡ Diagrama Unifilar")
st.caption("Generador universal — sirve para cualquier proyecto FV o BIPV, no solo el que tengas abierto ahora.")

st.warning(
    "⚠️ **No es un documento certificado.** Este es un borrador técnico auto-poblado "
    "con los datos ya configurados del proyecto. El diagrama unifilar para trámite "
    "RETIE formal requiere firma de un ingeniero electricista matriculado — usa esto "
    "como punto de partida, no como entregable final."
)

# ── Prerequisitos ──────────────────────────────────────────────────────────────
if not st.session_state.get("panel_dict") and not st.session_state.get("inversor_dict_dim"):
    st.info(
        "ℹ️ No se detecta panel ni inversor configurados todavía en 📐 Dimensionamiento. "
        "Puedes seguir de todos modos e ingresar los datos manualmente abajo, o "
        "configurar primero Dimensionamiento para que se auto-llenen."
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos del proyecto")
    nombre_proyecto = st.text_input(
        "Nombre del proyecto",
        value=st.session_state.get("nombre_proyecto", "Proyecto BIPV"),
    )
    cliente = st.text_input("Cliente", value=st.session_state.get("cliente_proyecto", ""))
    tipo_instalacion = st.session_state.get("tipo_instalacion", "")
    if tipo_instalacion:
        st.caption(f"Tipo de instalación (desde 🏠 Proyecto): **{tipo_instalacion}**")

    st.subheader("Generador FV")
    panel_dict = st.session_state.get("panel_dict", {}) or {}
    panel_nombre = st.text_input(
        "Módulo",
        value=st.session_state.get("panel_nombre_dim", ""),
        help="Auto-llenado desde 📐 Dimensionamiento si ya configuraste un panel.",
    )
    _n_paneles_detectado = (
        st.session_state.get("N_paneles_granja")
        or st.session_state.get("N_paneles")
        or 0
    )
    n_paneles = st.number_input(
        "Número total de módulos", min_value=0, step=1,
        value=int(_n_paneles_detectado),
    )
    n_serie = st.number_input(
        "Módulos en serie por string (N)", min_value=0, step=1,
        value=int(st.session_state.get("N_serie", 0) or 0),
    )
    pmax_stc_manual = st.number_input(
        "Potencia por módulo (Wp) — solo si no se auto-llenó arriba",
        min_value=0.0, step=5.0,
        value=float(panel_dict.get("Pmax_stc") or 0),
    )
    if pmax_stc_manual:
        panel_dict = {**panel_dict, "Pmax_stc": pmax_stc_manual}

with col2:
    st.subheader("Inversor(es)")
    inversor_dict = st.session_state.get("inversor_dict_dim", {}) or {}
    inversor_nombre = st.text_input(
        "Modelo de inversor",
        value=st.session_state.get("inversor_nombre_dim", ""),
        help="Auto-llenado desde ⚖️ Comparador de Inversores / 📐 Dimensionamiento si ya adoptaste una configuración.",
    )
    n_inversores = st.number_input(
        "Cantidad de unidades",
        min_value=1, step=1,
        value=int(st.session_state.get("N_inv_total", 1) or 1),
    )
    p_ac_manual_kW = st.number_input(
        "Potencia AC nominal por unidad (kW) — solo si no se auto-llenó",
        min_value=0.0, step=1.0,
        value=float((inversor_dict.get("P_ac_nom_W") or 0) / 1000.0),
    )
    if p_ac_manual_kW:
        inversor_dict = {**inversor_dict, "P_ac_nom_W": p_ac_manual_kW * 1000.0}

    st.subheader("Protecciones y punto de conexión")
    tension_red_V = st.selectbox(
        "Tensión de red en el punto de conexión (V)",
        options=[220, 380, 400, 440, 13200],
        index=2,
        help="220/380 monofásico o trifásico BT típico; 400/440 trifásico BT; 13200 = ejemplo de conexión en MT.",
    )
    proteccion_dc_manual = st.number_input(
        "Protección DC (A) — deja en 0 para no mostrar amperaje",
        min_value=0.0, step=1.0, value=0.0,
    )
    proteccion_ac_manual = st.number_input(
        "Protección AC (A) — deja en 0 para que se estime automáticamente (NEC, FS 1.25)",
        min_value=0.0, step=1.0, value=0.0,
    )
    medidor = st.selectbox("Tipo de medidor", ["Bidireccional", "Unidireccional"], index=0)

st.subheader("🔋 Batería (opcional)")
_bateria_detectada = bool(st.session_state.get("bateria_ok"))
incluir_bateria = st.checkbox(
    "Incluir batería en el diagrama",
    value=_bateria_detectada,
    help="Se preselecciona automáticamente si ya configuraste una batería en 🔋 Baterías y Balance.",
)
bateria_dict, bateria_nombre_val, n_baterias_val = {}, "", 0
proteccion_bat_manual = 0.0
if incluir_bateria:
    if _bateria_detectada:
        st.caption("🔋 Batería detectada desde 🔋 Baterías y Balance — revisa y ajusta si hace falta.")
    bateria_dict = st.session_state.get("bateria_dict", {}) or {}
    bateria_dim = st.session_state.get("bateria_dim", {}) or {}
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        bateria_nombre_val = st.text_input(
            "Modelo de batería",
            value=st.session_state.get("bateria_nombre", ""),
        )
    with col_b2:
        n_baterias_val = st.number_input(
            "Cantidad de unidades",
            min_value=0, step=1,
            value=int(bateria_dim.get("N_baterias", 0) or 0),
        )
    with col_b3:
        cap_manual = st.number_input(
            "Capacidad por unidad (kWh) — solo si no se auto-llenó",
            min_value=0.0, step=1.0,
            value=float(bateria_dim.get("cap_unitaria_kWh") or bateria_dict.get("capacidad_kWh") or 0),
        )
        if cap_manual:
            bateria_dict = {**bateria_dict, "capacidad_kWh": cap_manual}
    proteccion_bat_manual = st.number_input(
        "Protección DC de la batería (A) — deja en 0 para no mostrar amperaje",
        min_value=0.0, step=1.0, value=0.0,
    )
    st.caption(
        "ℹ️ En esta app la batería se conecta al **mismo inversor híbrido** que el "
        "generador FV (verificado por rango de voltaje, ver ⚙️ Compatibilidad en "
        "🔋 Baterías y Balance) — por eso el diagrama la dibuja como una segunda "
        "entrada DC del mismo inversor, no como un equipo aparte."
    )

st.subheader("🗺️ Multi-superficie (opcional)")
_multisup_detectado = bool(st.session_state.get("multisup_activo"))
incluir_multisup = st.checkbox(
    "Incluir varias superficies en el diagrama (en vez de un solo generador)",
    value=_multisup_detectado,
    help="Se preselecciona si ya configuraste multi-superficie en 🗺️ Vista 3D (Página 9).",
)
superficies_val: list[dict] = []
if incluir_multisup:
    _desglose = st.session_state.get("multisup_desglose", []) or []
    if _desglose:
        st.caption(
            "🗺️ Superficies detectadas desde 🗺️ Vista 3D — el número de módulos por "
            "superficie no viene de ahí (esa página trabaja con áreas y POA, no con "
            "conteo de paneles), complétalo abajo."
        )
        for sup in _desglose:
            col_s1, col_s2 = st.columns([3, 1])
            with col_s1:
                st.caption(f"**{sup.get('nombre', 'Superficie')}** ({sup.get('tipo', '')}) — {sup.get('area_m2', 0):.0f} m²")
            with col_s2:
                n_pan_sup = st.number_input(
                    "Módulos", min_value=0, step=1, value=0,
                    key=f"unif_sup_{sup.get('nombre')}",
                    label_visibility="collapsed",
                )
            if n_pan_sup:
                superficies_val.append({
                    "nombre": sup.get("nombre"), "tipo": sup.get("tipo"), "n_paneles": int(n_pan_sup),
                })
    else:
        st.info(
            "ℹ️ No se detectan superficies en 🗺️ Vista 3D. Puedes definirlas manualmente: "
            "escribe nombre y número de módulos separados por coma, una superficie por línea "
            "(ej. `Fachada Sur, 40`)."
        )
        _texto_manual = st.text_area("Superficies manuales", value="", height=100)
        for _linea in _texto_manual.splitlines():
            if "," not in _linea:
                continue
            _nombre_s, _n_s = _linea.rsplit(",", 1)
            try:
                _n_s = int(_n_s.strip())
            except ValueError:
                continue
            if _n_s > 0:
                superficies_val.append({"nombre": _nombre_s.strip(), "n_paneles": _n_s})

st.divider()

config = construir_config_unifilar(
    nombre_proyecto=nombre_proyecto,
    cliente=cliente,
    tipo_instalacion=tipo_instalacion,
    panel_nombre=panel_nombre,
    panel=panel_dict,
    n_paneles=int(n_paneles),
    n_serie=int(n_serie),
    inversor_nombre=inversor_nombre,
    inversor=inversor_dict,
    n_inversores=int(n_inversores),
    proteccion_dc_A=proteccion_dc_manual or None,
    proteccion_ac_A=proteccion_ac_manual or None,
    tension_red_V=float(tension_red_V),
    medidor=medidor,
    bateria_nombre=bateria_nombre_val,
    bateria=bateria_dict,
    n_baterias=int(n_baterias_val),
    proteccion_bat_A=proteccion_bat_manual or None,
    superficies=superficies_val or None,
)

if incluir_multisup and superficies_val and config["superficies"] is None:
    st.info(
        "ℹ️ Con menos de 2 superficies con módulos ingresados, el diagrama muestra "
        "un solo generador (el multi-superficie necesita al menos 2)."
    )

if config["generador"]["string_incompleto"]:
    st.warning(
        f"⚠️ {config['generador']['n_paneles']} módulos no es múltiplo de "
        f"{config['generador']['n_serie']} en serie — quedaría un string incompleto. "
        "Revisa el número de módulos o el N en serie antes de usar este diagrama."
    )

drawing = generar_diagrama_unifilar(config)
png_bytes = exportar_unifilar_bytes(drawing, "png")

st.subheader(f"{config['nombre_proyecto']}" + (f" · {config['cliente']}" if config["cliente"] else ""))
st.image(png_bytes, use_container_width=False)

col_dl1, col_dl2, col_dl3 = st.columns(3)
with col_dl1:
    st.download_button(
        "⬇️ Descargar PNG", data=png_bytes,
        file_name=f"unifilar_{config['nombre_proyecto'].replace(' ', '_')}.png",
        mime="image/png",
    )
with col_dl2:
    st.download_button(
        "⬇️ Descargar SVG (editable)", data=exportar_unifilar_bytes(drawing, "svg"),
        file_name=f"unifilar_{config['nombre_proyecto'].replace(' ', '_')}.svg",
        mime="image/svg+xml",
    )
with col_dl3:
    st.download_button(
        "⬇️ Descargar PDF", data=exportar_unifilar_bytes(drawing, "pdf"),
        file_name=f"unifilar_{config['nombre_proyecto'].replace(' ', '_')}.pdf",
        mime="application/pdf",
    )

with st.expander("📋 Datos usados para este diagrama"):
    st.json(config)
