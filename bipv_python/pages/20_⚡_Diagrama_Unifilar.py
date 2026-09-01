"""
Página 20 — Diagrama Unifilar (Fase 1: MVP · Fase 2: batería · Fase 3:
multi-superficie · Fase 4: sellado en Ledger)
Generador universal de diagrama unifilar para proyectos FV y BIPV.
Auto-llenado desde el panel/inversor configurados en Dimensionamiento, la
batería configurada en 🔋 Baterías y Balance, y las superficies de 🗺️ Vista
3D, si existen.
"""
import re

import streamlit as st

from calculos.diagrama_unifilar import (
    construir_config_unifilar,
    generar_diagrama_unifilar,
    exportar_unifilar_bytes,
)
from calculos.dimensionamiento import diseno_electrico_confirmado
from calculos.compatibilidad_bateria import check_compatibilidad
from calculos import ledger_auditoria as _ledger


def _nombre_archivo_seguro(nombre: str) -> str:
    """Nombre de proyecto -> nombre de archivo válido en cualquier SO.
    `nombre_proyecto` es texto libre del usuario (puede traer '/', ':',
    '*', etc., inválidos en Windows/nombres de descarga) -- antes de esta
    función el código solo reemplazaba espacios, dejando pasar el resto de
    caracteres inválidos sin sanitizar. Encontrado en auditoría (27-ago-2026)."""
    s = re.sub(r"[^\w\-]+", "_", (nombre or "proyecto").strip())
    return s.strip("_") or "proyecto"

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

# ── Vigencia del diseño confirmado (31-ago-2026) ───────────────────────────────
# Esta página auto-llena "Módulos en serie" (N_serie) y "Número total de
# módulos" (N_paneles_granja) desde el último diseño CONFIRMADO en
# Dimensionamiento -- pero como aquí todo es un campo editable (a propósito,
# es un generador universal, no exclusivo del proyecto abierto), un valor
# desactualizado puede pasar desapercibido, generarse en el diagrama y
# sellarse en el Ledger sin que nadie lo note. Pregunta explícita del
# usuario: "varias métricas antes del módulo dimensionamiento influyen en
# esta función y no las hemos ni revisado, ni auditado". Mismo rigor que las
# otras 6 páginas que ya muestran la alerta de vigencia
# (`DIAGNOSTICO_ALERTA_VIGENCIA_DISENO.md`) -- esta era la única que había
# quedado sin auditar.
_diseno_unif = diseno_electrico_confirmado(st.session_state)
if _diseno_unif["aviso"]:
    st.warning(_diseno_unif["aviso"])

# Segunda alerta, específica de esta página: "Número total de módulos" se
# auto-llena desde N_paneles_granja, que Dimensionamiento ya protege con su
# propia firma de invalidación (N_paneles_granja_inversor_ref, del bug real
# del 29-ago-2026 donde ese total quedaba pegado al inversor anterior) --
# pero esa protección solo se aplicaba DENTRO de Dimensionamiento; esta
# página nunca la revisaba. Mismo principio anti-falso-positivo: solo avisa
# si hay una referencia guardada que YA NO coincide con el inversor actual.
_npg_ref = st.session_state.get("N_paneles_granja_inversor_ref")
_inv_actual_dim = st.session_state.get("inversor_nombre_dim")
_npg_valor = st.session_state.get("N_paneles_granja")
if _npg_ref and _inv_actual_dim and _npg_ref != _inv_actual_dim and _npg_valor:
    st.warning(
        f"⚠️ El total de módulos auto-llenado ({_npg_valor}) viene del cálculo de "
        f"Proyecto completo con **{_npg_ref}**, pero el inversor seleccionado ahora en "
        f"📐 Dimensionamiento es **{_inv_actual_dim}** — vuelve a correr "
        "\"▶️ Optimizar N paneles/string\" o \"Prorrateo preliminar\" con el inversor "
        "actual, o revisa a mano el número de módulos abajo antes de generar el diagrama."
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
        "generador FV — por eso el diagrama la dibuja como una segunda entrada DC "
        "del mismo inversor, no como un equipo aparte."
    )
    # ── Re-verificación en vivo, no el flag "bateria_ok" (31-ago-2026) ──────
    # `bateria_ok` es una foto fija de cuando se dio clic en "▶️ Dimensionar
    # batería" en 🔋 Baterías y Balance, validada CONTRA EL INVERSOR QUE
    # ESTABA seleccionado en ese momento -- si después el usuario vuelve a
    # 📐 Dimensionamiento y cambia de inversor (p.ej. a uno de string, no
    # híbrido), ese flag no se invalida solo. Antes, esta página confiaba
    # ciegamente en `bateria_ok` para afirmar "verificado por rango de
    # voltaje" en el diagrama -- el diagrama podía dibujar (y declarar
    # verificada) una batería colgada de un inversor que ya no era el
    # validado. Corregido re-corriendo check_compatibilidad() aquí mismo,
    # contra el inversor ACTUAL (inversor_dict/inversor_nombre, ya
    # recalculados arriba en esta misma página), justo antes de dibujar.
    _compat_estado_vivo, _compat_msg_vivo = check_compatibilidad(
        bateria_dict, inversor_dict, inversor_nombre
    )
    if _compat_estado_vivo == "error":
        st.error(_compat_msg_vivo)
        st.warning(
            "⚠️ El diagrama se generará igual si continúas, con la batería dibujada "
            "como conectada a este inversor — pero esa conexión **no está "
            "verificada** con los datos actuales. Corrige el inversor o la batería "
            "antes de usar este diagrama para un trámite RETIE."
        )
    elif _compat_estado_vivo == "warning":
        st.warning(_compat_msg_vivo)
    else:
        st.success(_compat_msg_vivo)

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
        for _i_sup, sup in enumerate(_desglose):
            col_s1, col_s2 = st.columns([3, 1])
            with col_s1:
                # .get(clave, default) solo aplica el default si la CLAVE
                # falta -- si viniera presente con valor None (no debería,
                # pero no se valida en Pagina 9), ".0f" reventaria. `or`
                # cubre ambos casos. Encontrado en auditoria (27-ago-2026).
                st.caption(
                    f"**{sup.get('nombre') or 'Superficie'}** ({sup.get('tipo') or ''}) — "
                    f"{sup.get('area_m2') or 0:.0f} m²"
                )
            with col_s2:
                n_pan_sup = st.number_input(
                    "Módulos", min_value=0, step=1, value=0,
                    # key con índice, no solo nombre: dos superficies pueden
                    # tener el mismo nombre (Página 9 no exige que sean
                    # únicos) y una key duplicada rompe la página entera con
                    # DuplicateWidgetID -- encontrado en auditoría (27-ago-2026).
                    key=f"unif_sup_{_i_sup}_{sup.get('nombre')}",
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

st.subheader("🧾 Detalle RETIE (opcional)")
with st.expander(
    "Agregar anotaciones típicas de una revisión RETIE — protecciones "
    "detalladas, equipotencialidad, notas y pendientes"
):
    equipotencialidad_val = st.checkbox(
        "Incluir nota de equipotencialidad en el generador (estructura → PE)",
        value=False,
    )
    detalle_dc_val = st.multiselect(
        "Ítems de protección DC a detallar",
        options=[
            "Fusibles gPV por string (+/-)",
            "Seccionador DC bajo carga",
            "DPS DC Tipo 2, Ucpv ≥ Voc máx.",
            "Cable solar Cu H1Z2Z2-K",
        ],
    )
    detalle_ac_val = st.multiselect(
        "Ítems de protección AC a detallar",
        options=["Interruptor AC 3P", "DPS AC Tipo 2 + seccionamiento"],
    )
    _plantilla_retie = st.checkbox(
        "Usar plantilla genérica de notas/pendientes RETIE (editable abajo)",
        value=False,
    )
    _notas_default = (
        "Verificar Voc, Isc y coeficientes térmicos del módulo contra el fusible máximo.\n"
        "Comprobar Voc del string a temperatura mínima y compatibilidad MPPT del inversor.\n"
        "Calcular calibres, caída de tensión, Icc, Icu/Ics y selectividad de protecciones."
        if _plantilla_retie else ""
    )
    _pendientes_default = (
        "Fichas técnicas oficiales del módulo e inversor.\n"
        "Icc disponible en el punto de conexión y esquema de puesta a tierra.\n"
        "Datos del operador de red, transformador y medición."
        if _plantilla_retie else ""
    )
    notas_texto = st.text_area(
        "Notas para revisión RETIE (una por línea)", value=_notas_default, height=90,
    )
    pendientes_texto = st.text_area(
        "Pendientes para versión constructiva (una por línea)", value=_pendientes_default, height=90,
    )
    st.caption(
        "ℹ️ Estas anotaciones son texto libre que aporta quien diligencia el "
        "formulario -- este módulo no inventa valores normativos ni sustituye "
        "la memoria de cálculo del ingeniero responsable."
    )
notas_retie_val = [l.strip() for l in notas_texto.splitlines() if l.strip()]
pendientes_retie_val = [l.strip() for l in pendientes_texto.splitlines() if l.strip()]

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
    equipotencialidad=equipotencialidad_val,
    detalle_proteccion_dc=detalle_dc_val or None,
    detalle_proteccion_ac=detalle_ac_val or None,
    notas_retie=notas_retie_val or None,
    pendientes_retie=pendientes_retie_val or None,
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
_nombre_archivo = _nombre_archivo_seguro(config["nombre_proyecto"])

st.subheader(f"{config['nombre_proyecto']}" + (f" · {config['cliente']}" if config["cliente"] else ""))
st.image(png_bytes, use_container_width=False)

_retie = config.get("retie", {})
if _retie.get("notas") or _retie.get("pendientes"):
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        if _retie.get("notas"):
            st.markdown("**📋 Notas para revisión RETIE**")
            for _nota in _retie["notas"]:
                st.markdown(f"- {_nota}")
    with col_n2:
        if _retie.get("pendientes"):
            st.markdown("**🚧 Pendientes para versión constructiva**")
            for _pend in _retie["pendientes"]:
                st.markdown(f"- {_pend}")

col_dl1, col_dl2, col_dl3 = st.columns(3)
with col_dl1:
    st.download_button(
        "⬇️ Descargar PNG", data=png_bytes,
        file_name=f"unifilar_{_nombre_archivo}.png",
        mime="image/png",
    )
with col_dl2:
    st.download_button(
        "⬇️ Descargar SVG (editable)", data=exportar_unifilar_bytes(drawing, "svg"),
        file_name=f"unifilar_{_nombre_archivo}.svg",
        mime="image/svg+xml",
    )
with col_dl3:
    st.download_button(
        "⬇️ Descargar PDF", data=exportar_unifilar_bytes(drawing, "pdf"),
        file_name=f"unifilar_{_nombre_archivo}.pdf",
        mime="application/pdf",
    )

st.divider()
# ── 🔒 Ledger de Auditoría — mismo diagrama, sellado con hash encadenado.
# Botón dedicado (no un selector genérico de tipo) porque para esta página
# solo hay un tipo que tiene sentido sellar: "diagrama_unifilar" -- mismo
# patrón que 🔍 Diagnóstico, distinto del selector de 📄 Reporte PDF (que sí
# ofrece varios tipos porque ahí sí aplica más de uno).
if st.button("🔒 Sellar en el Ledger de Auditoría", type="secondary", use_container_width=True):
    _usr_unif = st.session_state.get("auth_email", "")
    _insumos_unif = {
        "generador": config["generador"],
        "inversores": config["inversores"],
        "bateria": config["bateria"],
        "superficies": config["superficies"],
        "tension_red_V": config["tension_red_V"],
        "medidor": config["medidor"],
        "proteccion_dc_A": config["proteccion_dc_A"],
        "proteccion_ac_A": config["proteccion_ac_A"],
    }
    _resultados_unif = {
        "p_dc_total_kWp": (
            round(sum(s["p_dc_kWp"] or 0 for s in config["superficies"]), 2)
            if config["superficies"] else config["generador"]["p_dc_kWp"]
        ),
        "p_ac_total_kW": config["inversores"]["p_ac_total_kW"],
        "tiene_bateria": config["bateria"]["activa"],
        "n_superficies": len(config["superficies"]) if config["superficies"] else 1,
    }
    _eslabon_unif = _ledger.sellar_resultado(
        config["nombre_proyecto"], _usr_unif, "diagrama_unifilar",
        _insumos_unif, _resultados_unif,
    ) if _usr_unif else {}
    if _eslabon_unif:
        st.success(f"🔒 Diagrama sellado — ID {_eslabon_unif['hash_propio'][:16]}")
    else:
        st.warning("⚠️ No se pudo sellar (revisa sesión activa y permisos/espacio).")

with st.expander("📋 Datos usados para este diagrama"):
    st.json(config)
