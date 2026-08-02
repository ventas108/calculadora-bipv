"""TRM — Tasa Representativa del Mercado (COP/USD).

Módulo compartido entre Presupuesto y Financiero.
Fuentes (en orden de prioridad):
  1. Superfinanciera / datos.gov.co  — TRM oficial certificada Colombia
  2. open.er-api.com                 — respaldo gratuito, sin clave
  3. Último valor en session_state o default 4 200

Uso:
    from calculos.trm_utils import init_trm, trm_widget

    init_trm()        # llamar al inicio de la página (antes de renderizar)
    tc = trm_widget("ppto")   # widget en Presupuesto  → devuelve float
    tc = trm_widget("fin")    # widget en Financiero   → devuelve float
"""
from __future__ import annotations

import streamlit as st

try:
    import requests as _requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

# ── Constantes ────────────────────────────────────────────────────────────────
TRM_DEFAULT    = 4_200.0
_KEY_VALOR     = "tipo_cambio"
_KEY_FECHA     = "tipo_cambio_fecha"
_KEY_FUENTE    = "tipo_cambio_fuente"
_ALERTA_BAJA   = 3_800.0
_ALERTA_ALTA   = 6_000.0


# ── Fetch con caché de 1 hora (no martillar las APIs) ─────────────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def _fetch_trm_api() -> tuple[float, str, str]:
    """Devuelve (valor_cop_usd, fecha_str, fuente). Lanza RuntimeError si falla."""
    if not _REQUESTS_OK:
        raise RuntimeError("requests no instalado")

    # ── Fuente 1: Superfinanciera via datos.gov.co (TRM oficial Colombia) ──────
    try:
        url = (
            "https://www.datos.gov.co/resource/32sa-8pi3.json"
            "?$order=vigenciadesde+DESC&$limit=1"
        )
        resp = _requests.get(url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            if data and "valor" in data[0]:
                valor = float(data[0]["valor"])
                fecha = str(data[0].get("vigenciadesde", ""))[:10]
                return valor, fecha, "Banco de la República (datos.gov.co)"
    except Exception:
        pass

    # ── Fuente 2: open.er-api.com (respaldo gratuito, sin clave) ──────────────
    try:
        resp = _requests.get("https://open.er-api.com/v6/latest/USD", timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            cop = data.get("rates", {}).get("COP")
            if cop:
                fecha = str(data.get("time_last_update_utc", ""))[:16]
                return float(cop), fecha, "open.er-api.com"
    except Exception:
        pass

    raise RuntimeError("No se pudo obtener TRM de ninguna fuente externa")


# ── Inicialización temprana ───────────────────────────────────────────────────
def init_trm(default: float = TRM_DEFAULT) -> None:
    """Inicializa TRM en session_state si aún no existe.

    Llama a esta función al inicio de cada página que use TRM
    (antes de cualquier render) para garantizar que la primera lectura
    de st.session_state["tipo_cambio"] ya tenga el valor en tiempo real.
    """
    if _KEY_VALOR not in st.session_state:
        try:
            valor, fecha, fuente = _fetch_trm_api()
            st.session_state[_KEY_VALOR]  = valor
            st.session_state[_KEY_FECHA]  = fecha
            st.session_state[_KEY_FUENTE] = fuente
        except Exception:
            st.session_state[_KEY_VALOR]  = default
            st.session_state[_KEY_FECHA]  = ""
            st.session_state[_KEY_FUENTE] = "valor por defecto"


# ── Widget reutilizable ───────────────────────────────────────────────────────
def trm_widget(page_key: str = "default") -> float:
    """Widget TRM sincronizado entre páginas.

    Muestra el valor actual (obtenido del API o editado manualmente),
    permite refrescar desde el API con un clic, y escribe el resultado
    en st.session_state["tipo_cambio"] como fuente de verdad global.

    Args:
        page_key: Sufijo único por página ("ppto", "fin", etc.) para
                  evitar colisiones de key de widgets en Streamlit.

    Returns:
        float: TRM activa (ya sincronizada en session_state).
    """
    _val    = float(st.session_state.get(_KEY_VALOR,  TRM_DEFAULT))
    _fecha  = st.session_state.get(_KEY_FECHA,  "")
    _fuente = st.session_state.get(_KEY_FUENTE, "valor por defecto")

    # ── Layout: input numérico + botón de refresco ────────────────────────────
    col_inp, col_btn = st.columns([5, 1])

    with col_inp:
        nuevo = st.number_input(
            "💱 TRM (COP/USD)",
            min_value=1_000.0,
            max_value=15_000.0,
            value=_val,
            step=50.0,
            key=f"_trm_num_{page_key}",
            help=(
                f"**Fuente:** {_fuente}"
                + (f"  \n**Fecha:** {_fecha}" if _fecha else "")
                + "\n\nEdita el valor manualmente o clica **🔄** para "
                  "actualizar desde la API del Banco de la República."
            ),
        )

    with col_btn:
        # Botón alineado verticalmente con el input
        st.write("")   # espaciador
        if st.button(
            "🔄",
            key=f"_trm_refresh_{page_key}",
            help="Actualizar TRM desde datos.gov.co (Banco de la República) "
                 "o open.er-api.com como respaldo",
            use_container_width=True,
        ):
            _fetch_trm_api.clear()   # invalida caché → fuerza nuevo fetch
            try:
                nuevo, _fecha, _fuente = _fetch_trm_api()
                st.session_state[_KEY_FECHA]  = _fecha
                st.session_state[_KEY_FUENTE] = _fuente
                st.toast(
                    f"✅ TRM actualizada: **{nuevo:,.0f} COP/USD**  \n"
                    f"📅 {_fecha}  \n📡 {_fuente}",
                    icon="✅",
                )
            except Exception as exc:
                st.warning(
                    f"⚠️ No se pudo obtener TRM del API ({exc}). "
                    "Usando el valor ingresado manualmente."
                )

    # ── Fuente activa y fecha ─────────────────────────────────────────────────
    if _fuente and _fuente != "valor por defecto":
        _icono = "📡" if "datos.gov" in _fuente else "🌐" if "er-api" in _fuente else "✏️"
        st.caption(
            f"{_icono} **{_fuente}**"
            + (f" · {_fecha}" if _fecha else "")
            + f" · {nuevo:,.0f} COP/USD"
        )
    else:
        st.caption(f"✏️ Valor ingresado manualmente · {nuevo:,.0f} COP/USD")

    # ── Alertas ───────────────────────────────────────────────────────────────
    if nuevo < _ALERTA_BAJA:
        st.warning(
            f"⚠️ TRM {nuevo:,.0f} COP/USD parece baja (ref. 2025-2026: ~4.000–4.500). "
            "Clica 🔄 para obtener el valor oficial del Banco de la República."
        )
    elif nuevo > _ALERTA_ALTA:
        st.warning(f"⚠️ TRM {nuevo:,.0f} COP/USD parece muy alta. Verifica la fuente.")

    # ── Escribir en session_state (fuente de verdad global) ──────────────────
    st.session_state[_KEY_VALOR]  = nuevo
    if nuevo != _val:
        # Usuario editó manualmente → actualizar fuente
        st.session_state[_KEY_FUENTE] = "valor manual"
        st.session_state[_KEY_FECHA]  = ""

    return nuevo
