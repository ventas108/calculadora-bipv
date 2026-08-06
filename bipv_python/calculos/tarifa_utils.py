"""Tarifa eléctrica local — sincronización entre Proyecto y Financiero.

Réplica del patrón TRM: fuente de verdad global en session_state,
widget editable con provenance (ciudad, operador, fuente).

Keys de session_state:
  tarifa_cop_kwh          — valor COP/kWh (clave canónica)
  tarifa_cop_kWh          — alias legacy (se mantiene para compatibilidad)
  tarifa_ciudad_origen    — ciudad donde se pre-cargó la tarifa
  tarifa_operador         — operador local (EPM, Codensa, EDEQ…)
  tarifa_fuente           — "catálogo", "Proyecto", "Financiero", "valor por defecto"

Uso:
    from calculos.tarifa_utils import init_tarifa, set_tarifa_from_ciudad, tarifa_widget

    # Al inicio de cada página (antes de renderizar):
    init_tarifa()                         # Financiero (no necesita ciudad)
    init_tarifa(ciudad, CIUDADES)         # Proyecto

    # Al cambiar ciudad en Proyecto:
    set_tarifa_from_ciudad(ciudad, CIUDADES)

    # Widget (reemplaza st.number_input de tarifa):
    tarifa_kwh = tarifa_widget("proy")    # en Proyecto
    tarifa_cop = tarifa_widget("fin")     # en Financiero
"""
from __future__ import annotations

import streamlit as st

# ── Constantes ────────────────────────────────────────────────────────────────
TARIFA_DEFAULT    = 850.0
_KEY_VALOR        = "tarifa_cop_kwh"       # clave canónica
_KEY_VALOR_LEGACY = "tarifa_cop_kWh"       # alias legacy
_KEY_CIUDAD       = "tarifa_ciudad_origen"
_KEY_OPERADOR     = "tarifa_operador"
_KEY_FUENTE       = "tarifa_fuente"

_ALERTA_MUY_BAJA  = 300.0   # error — casi con certeza incorrecto
_ALERTA_BAJA      = 500.0   # warning — puede ser residencial subsidiada
_ALERTA_ALTA      = 1_800.0 # warning — inusualmente alto

# Mapeo de page_key → etiqueta legible para la fuente
_LABELS_FUENTE = {
    "proy": "Proyecto",
    "fin":  "Financiero",
}


# ── Inicialización temprana ───────────────────────────────────────────────────
def init_tarifa(ciudad: str = "", ciudades_dict: dict | None = None) -> None:
    """Inicializa tarifa_cop_kwh en session_state si aún no existe.

    Llamar al inicio de cada página que use la tarifa eléctrica,
    antes de cualquier render.

    Si la clave ya existe (usuario ya visitó Proyecto), es un no-op.
    Si no existe (primera carga o sesión nueva), la pre-carga desde
    el catálogo de ciudades o usa 850 COP/kWh como valor por defecto.

    Args:
        ciudad: Nombre de la ciudad actual del proyecto (vacío = sin info).
        ciudades_dict: Diccionario CIUDADES de ciudades_colombia.py.
    """
    if _KEY_VALOR in st.session_state:
        return  # ya inicializado — no sobreescribir

    valor    = TARIFA_DEFAULT
    operador = ""
    fuente   = "valor por defecto"

    if ciudad and ciudades_dict:
        c = ciudades_dict.get(ciudad, {})
        if "tarifa_comercial_cop_kwh" in c:
            valor  = float(c["tarifa_comercial_cop_kwh"])
            fuente = "catálogo"
        operador = c.get("operador", "")

    st.session_state[_KEY_VALOR]        = valor
    st.session_state[_KEY_VALOR_LEGACY] = valor
    st.session_state[_KEY_CIUDAD]       = ciudad or "—"
    st.session_state[_KEY_OPERADOR]     = operador
    st.session_state[_KEY_FUENTE]       = fuente


# ── Actualización por cambio de ciudad ───────────────────────────────────────
def set_tarifa_from_ciudad(ciudad: str, ciudades_dict: dict) -> None:
    """Actualizar tarifa cuando el usuario cambia de ciudad en Proyecto.

    A diferencia de init_tarifa, SIEMPRE sobreescribe — la ciudad
    cambió, por lo que la tarifa del operador anterior ya no aplica.

    Args:
        ciudad: Nueva ciudad seleccionada.
        ciudades_dict: Diccionario CIUDADES de ciudades_colombia.py.
    """
    c        = ciudades_dict.get(ciudad, {})
    operador = c.get("operador", "")

    if "tarifa_comercial_cop_kwh" in c:
        valor = float(c["tarifa_comercial_cop_kwh"])
        st.session_state[_KEY_VALOR]        = valor
        st.session_state[_KEY_VALOR_LEGACY] = valor

    st.session_state[_KEY_CIUDAD]   = ciudad
    st.session_state[_KEY_OPERADOR] = operador
    st.session_state[_KEY_FUENTE]   = "catálogo"


# ── Widget reutilizable ───────────────────────────────────────────────────────
def tarifa_widget(page_key: str = "default") -> float:
    """Widget de tarifa eléctrica sincronizado entre Proyecto y Financiero.

    Muestra el valor actual (pre-cargado desde el catálogo de ciudades o
    editado manualmente), provenance (ciudad, operador, fuente) y alertas
    si el valor es inusual. Escribe el resultado en
    st.session_state["tarifa_cop_kwh"] como fuente de verdad global.

    Args:
        page_key: Sufijo único por página ("proy", "fin") para evitar
                  colisiones de key de widgets en Streamlit.

    Returns:
        float: Tarifa activa en COP/kWh (ya sincronizada en session_state).
    """
    _val      = float(st.session_state.get(_KEY_VALOR,    TARIFA_DEFAULT))
    _ciudad   = st.session_state.get(_KEY_CIUDAD,   "")
    _operador = st.session_state.get(_KEY_OPERADOR, "")
    _fuente   = st.session_state.get(_KEY_FUENTE,   "valor por defecto")

    # ── Texto de ayuda ────────────────────────────────────────────────────────
    _ciudad_info = ""
    if _ciudad and _ciudad not in ("", "—"):
        _ciudad_info = f"📍 **{_ciudad}**" + (f" ({_operador})" if _operador else "")

    _help = (
        "Tarifa comercial/industrial sin subsidio.  \n"
        "Bogotá 2024: ~550–750 COP/kWh · Residencial est. 4–6: ~600–850 COP/kWh.  \n"
        + (_ciudad_info + "  \n" if _ciudad_info else "")
        + f"🔁 Fuente actual: *{_fuente}*  \n"
        "Edita el valor aquí y se propagará automáticamente a la otra sección."
    )

    # ── #93: re-sembrar el widget si el global cambió FUERA de este widget ──
    # Streamlit ignora `value=` cuando la key del widget ya existe, así que un
    # cambio externo (ciudad en Proyecto, edición en la otra página) dejaría el
    # número viejo en pantalla y la línea final lo re-escribiría sobre el
    # global, revirtiendo la sincronización. La clave sombra guarda el último
    # valor que ESTE widget mostró: si el global difiere de ella, el cambio
    # vino de afuera y hay que re-sembrar la key del widget antes de renderizar.
    _wkey = f"_tarifa_num_{page_key}"
    _skey = f"_tarifa_sync_{page_key}"
    if _wkey in st.session_state and st.session_state.get(_skey) != _val:
        st.session_state[_wkey] = min(max(_val, 100.0), 2_000.0)

    nuevo = st.number_input(
        "Tarifa electricidad (COP/kWh)",
        min_value=100.0,
        max_value=2_000.0,
        value=_val,
        step=25.0,
        key=_wkey,
        help=_help,
    )
    # Sombra: lo que este widget mostró en este run (para detectar cambios externos)
    st.session_state[_skey] = nuevo

    # ── Caption de provenance ─────────────────────────────────────────────────
    if _ciudad and _ciudad not in ("", "—"):
        _icono = "📍" if _fuente == "catálogo" else "✏️"
        _op_txt = f" · {_operador}" if _operador else ""
        st.caption(
            f"{_icono} **{_ciudad}{_op_txt}** · Fuente: {_fuente} · "
            f"{nuevo:,.0f} COP/kWh"
        )
    else:
        st.caption(f"✏️ {_fuente} · {nuevo:,.0f} COP/kWh")

    # ── Alertas ───────────────────────────────────────────────────────────────
    if nuevo < _ALERTA_MUY_BAJA:
        st.error(
            f"⚠️ Tarifa {nuevo:,.0f} COP/kWh parece muy baja (mínimo ~300 COP/kWh). "
            "Revisa el valor ingresado — puede estar afectando el análisis financiero."
        )
    elif nuevo < _ALERTA_BAJA:
        st.warning(
            f"⚠️ Tarifa {nuevo:,.0f} COP/kWh es baja — típica de residencial subsidiado. "
            "Para proyectos comerciales/industriales verifica la factura real del cliente."
        )
    elif nuevo > _ALERTA_ALTA:
        st.warning(
            f"⚠️ Tarifa {nuevo:,.0f} COP/kWh parece alta (ref. máx. ~1.800 COP/kWh). "
            "Confirma con la factura del cliente o la circular CREG vigente."
        )

    # ── Escribir en session_state (fuente de verdad global) ──────────────────
    st.session_state[_KEY_VALOR]        = nuevo
    st.session_state[_KEY_VALOR_LEGACY] = nuevo
    if nuevo != _val:
        # Usuario editó manualmente → registrar en qué página ocurrió
        label = _LABELS_FUENTE.get(page_key, page_key)
        st.session_state[_KEY_FUENTE] = label

    return nuevo
