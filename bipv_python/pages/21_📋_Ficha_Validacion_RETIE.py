"""
Página 21 — Ficha de Validación RETIE
Dashboard ejecutivo (tarjetas KPI + flujo de energía + tabla de cargas) más
un motor de validación eléctrica básica (Voc en frío, ventana MPPT, balance
entre inversores, breaker por calibre comercial) para cualquier proyecto FV
o BIPV -- no un diagrama de línea única (eso lo cubre ⚡ Diagrama Unifilar),
sino una ficha de una sola página con banderas OK/PENDIENTE/ERROR.
Auto-llenado desde el panel/inversor configurados en 📐 Dimensionamiento.
"""
import re

import streamlit as st

from calculos.ficha_validacion_retie import (
    construir_config_retie,
    calcular_retie,
    validar_retie,
    generar_ficha_svg,
    exportar_ficha_svg_bytes,
    exportar_ficha_png_bytes,
)
from calculos import ledger_auditoria as _ledger


def _nombre_archivo_seguro(nombre: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", (nombre or "proyecto").strip())
    return s.strip("_") or "proyecto"


st.set_page_config(page_title="Ficha de Validación RETIE", page_icon="📋", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()
st.title("📋 Ficha de Validación RETIE")
st.caption(
    "Generador universal — sirve para cualquier proyecto FV o BIPV, no solo el que tengas abierto ahora."
)

st.warning(
    "⚠️ **No es un documento constructivo.** Este es un borrador de apoyo para revisión, "
    "auto-poblado con los datos ya configurados del proyecto. No sustituye memorias de cálculo, "
    "estudio de cortocircuito, coordinación de protecciones, declaración de cumplimiento, "
    "inspección ni la firma de un ingeniero electricista matriculado que exige RETIE."
)

if not st.session_state.get("panel_dict") and not st.session_state.get("inversor_dict_dim"):
    st.info(
        "ℹ️ No se detecta panel ni inversor configurados todavía en 📐 Dimensionamiento. "
        "Puedes seguir de todos modos e ingresar los datos manualmente abajo."
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos del proyecto")
    nombre_proyecto = st.text_input(
        "Nombre del proyecto", value=st.session_state.get("nombre_proyecto", "Proyecto BIPV"),
    )
    propietario = st.text_input("Propietario", value="")
    direccion = st.text_input("Dirección", value="")
    municipio = st.text_input("Municipio", value="")
    operador_red = st.text_input("Operador de red", value="")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        disenador = st.text_input("Diseñó (nombre)", value="")
    with col_d2:
        matricula = st.text_input("Matrícula profesional", value="")

    st.subheader("Módulo FV")
    panel_dict = st.session_state.get("panel_dict", {}) or {}
    panel_nombre = st.text_input(
        "Módulo", value=st.session_state.get("panel_nombre_dim", ""),
        help="Auto-llenado desde 📐 Dimensionamiento si ya configuraste un panel.",
    )
    _n_paneles_detectado = (
        st.session_state.get("N_paneles_granja") or st.session_state.get("N_paneles") or 0
    )
    n_paneles = st.number_input("Número total de módulos", min_value=0, step=1, value=int(_n_paneles_detectado))
    n_serie = st.number_input(
        "Módulos en serie por string (N)", min_value=0, step=1,
        value=int(st.session_state.get("N_serie", 0) or 0),
    )
    potencia_w = st.number_input(
        "Potencia por módulo (Wp)", min_value=0.0, step=5.0,
        value=float(panel_dict.get("Pmax_stc") or 0),
    )
    with st.expander("Ficha técnica del módulo (opcional, para validar Voc frío / ventana MPPT)"):
        voc_v = st.number_input("Voc STC (V)", min_value=0.0, step=0.1, value=float(panel_dict.get("Voc_stc") or 0))
        vmp_v = st.number_input("Vmp STC (V)", min_value=0.0, step=0.1, value=float(panel_dict.get("Vmp_stc") or 0))
        isc_a = st.number_input("Isc STC (A)", min_value=0.0, step=0.1, value=float(panel_dict.get("Isc_stc") or 0))
        coef_voc_pct_c = st.number_input(
            "Coeficiente de temperatura de Voc (%/°C, típicamente negativo)",
            step=0.01, value=float(panel_dict.get("Tk_beta") or 0),
        )
        temperatura_minima_diseno_c = st.number_input(
            "Temperatura mínima de diseño del sitio (°C)", step=1.0, value=0.0,
        )

with col2:
    st.subheader("Inversor(es)")
    inversor_dict = st.session_state.get("inversor_dict_dim", {}) or {}
    inversor_nombre = st.text_input(
        "Modelo de inversor", value=st.session_state.get("inversor_nombre_dim", ""),
        help="Auto-llenado desde ⚖️ Comparador de Inversores / 📐 Dimensionamiento si ya adoptaste una configuración.",
    )
    n_inversores = st.number_input(
        "Cantidad de unidades", min_value=1, step=1,
        value=int(st.session_state.get("N_inv_total", 1) or 1),
    )
    p_ac_manual_kW = st.number_input(
        "Potencia AC nominal por unidad (kW)", min_value=0.0, step=1.0,
        value=float((inversor_dict.get("P_ac_nom_W") or 0) / 1000.0),
    )
    tension_salida_v = st.selectbox(
        "Tensión de salida (V)", options=[220, 380, 400, 440, 13200], index=2,
    )
    with st.expander("Ficha técnica del inversor (opcional, para validar Voc frío / ventana MPPT)"):
        vdc_max_v = st.number_input("Vdc máxima (V)", min_value=0.0, step=1.0, value=float(inversor_dict.get("Vdc_max") or 0))
        vmppt_min_v = st.number_input(
            "MPPT mínimo (V)", min_value=0.0, step=1.0,
            value=float(inversor_dict.get("Vmppt_min") or inversor_dict.get("Vmppt_activo_min") or 0),
        )
        vmppt_max_v = st.number_input("MPPT máximo (V)", min_value=0.0, step=1.0, value=float(inversor_dict.get("Vmppt_max") or 0))

    st.subheader("Distribución de strings por inversor")
    st.caption(
        "Opcional -- si la completas, se calcula el balance DC/AC por inversor "
        "y la tabla de cargas muestra una fila por inversor con su propio dato."
    )
    _n_strings_detectado = int(n_paneles // n_serie) if n_serie else 0
    _texto_strings = st.text_input(
        f"Strings por inversor, separados por coma (ej. 9,8) — total detectado: {_n_strings_detectado}",
        value="",
    )
    strings_por_inversor = None
    if _texto_strings.strip():
        try:
            strings_por_inversor = [int(x.strip()) for x in _texto_strings.split(",") if x.strip()]
        except ValueError:
            st.warning("⚠️ No se pudo interpretar la distribución de strings -- usa solo números separados por coma.")
            strings_por_inversor = None

    st.subheader("Punto de conexión")
    corriente_cortocircuito_pcc_ka = st.number_input(
        "Corriente de cortocircuito en el PCC (kA) — deja en 0 si no se conoce",
        min_value=0.0, step=0.1, value=0.0,
    )
    esquema_tierra = st.text_input("Esquema de puesta a tierra (ej. TT, TN-S) — opcional", value="")

st.divider()

config = construir_config_retie(
    nombre_proyecto=nombre_proyecto, propietario=propietario, direccion=direccion,
    municipio=municipio, operador_red=operador_red, disenador=disenador, matricula=matricula,
    panel_nombre=panel_nombre, potencia_w=potencia_w,
    voc_v=voc_v or None, vmp_v=vmp_v or None, isc_a=isc_a or None,
    coef_voc_pct_c=coef_voc_pct_c or None,
    inversor_nombre=inversor_nombre, potencia_ac_kw_unidad=p_ac_manual_kW,
    n_inversores=int(n_inversores), tension_salida_v=float(tension_salida_v),
    vdc_max_v=vdc_max_v or None, vmppt_min_v=vmppt_min_v or None, vmppt_max_v=vmppt_max_v or None,
    n_paneles=int(n_paneles), n_serie=int(n_serie), strings_por_inversor=strings_por_inversor,
    temperatura_minima_diseno_c=temperatura_minima_diseno_c if temperatura_minima_diseno_c else None,
    corriente_cortocircuito_pcc_ka=corriente_cortocircuito_pcc_ka or None,
    esquema_tierra=esquema_tierra,
)
calc = calcular_retie(config)
checks = validar_retie(config, calc)
svg = generar_ficha_svg(config, calc, checks)

st.subheader(f"{config['proyecto']['nombre_proyecto']}")
_n_error = sum(1 for c in checks if c["nivel"] == "ERROR")
_n_pendiente = sum(1 for c in checks if c["nivel"] == "PENDIENTE")
_n_ok = sum(1 for c in checks if c["nivel"] == "OK")
st.caption(f"✅ {_n_ok} OK · ⚠️ {_n_pendiente} pendiente(s) · ❌ {_n_error} error(es)")

st.components.v1.html(svg, height=min(1600, len(svg) // 40 + 900), scrolling=True)

_nombre_archivo = _nombre_archivo_seguro(config["proyecto"]["nombre_proyecto"])
png_bytes = exportar_ficha_png_bytes(svg)

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        "⬇️ Descargar SVG (editable)", data=exportar_ficha_svg_bytes(svg),
        file_name=f"ficha_retie_{_nombre_archivo}.svg", mime="image/svg+xml",
    )
with col_dl2:
    if png_bytes:
        st.download_button(
            "⬇️ Descargar PNG", data=png_bytes,
            file_name=f"ficha_retie_{_nombre_archivo}.png", mime="image/png",
        )
    else:
        st.caption("ℹ️ Descarga en PNG no disponible en este servidor (requiere CairoSVG). El SVG sirve igual.")

st.divider()
if st.button("🔒 Sellar en el Ledger de Auditoría", type="secondary", use_container_width=True):
    _usr = st.session_state.get("auth_email", "")
    _insumos = {
        "proyecto": config["proyecto"], "panel": config["panel"], "inversor": config["inversor"],
        "generador": config["generador"], "diseno": config["diseno"],
    }
    _resultados = {
        "potencia_dc_kwp": calc["potencia_dc_kwp"], "potencia_ac_kw": calc["potencia_ac_kw"],
        "n_ok": _n_ok, "n_pendiente": _n_pendiente, "n_error": _n_error,
    }
    _eslabon = _ledger.sellar_resultado(
        config["proyecto"]["nombre_proyecto"], _usr, "ficha_validacion_retie", _insumos, _resultados,
    ) if _usr else {}
    if _eslabon:
        st.success(f"🔒 Ficha sellada — ID {_eslabon['hash_propio'][:16]}")
    else:
        st.warning("⚠️ No se pudo sellar (revisa sesión activa y permisos/espacio).")

with st.expander("📋 Datos y validaciones usados en esta ficha"):
    st.json({"config": config, "calculos": calc, "validaciones": checks})
