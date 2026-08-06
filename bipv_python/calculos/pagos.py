# -*- coding: utf-8 -*-
"""
Configuración de pagos (Fase 2 monetización) — links de pago Wompi,
precios y datos de transferencia, editables desde el panel de administración.

Se persiste en datos/config_pagos.json (solo en el servidor, gitignored):
un git pull nunca pisa la configuración comercial del admin.
"""
from __future__ import annotations

import json
import os
from urllib.parse import urlsplit

_DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CONFIG_PAGOS = os.path.join(_DIR_BASE, "datos", "config_pagos.json")

# Dominios oficiales de links de pago Wompi (hostname EXACTO, sin subdominios
# comodín): evita phishing tipo https://checkout.wompi.co@malicioso.com/...
DOMINIOS_WOMPI = {"checkout.wompi.co", "pago.wompi.co"}


def validar_link_wompi(url: str) -> str:
    """Devuelve '' si el link es válido, o el motivo del rechazo."""
    url = (url or "").strip()
    if not url:
        return ""                          # vacío = no configurado, permitido
    try:
        p = urlsplit(url)
    except ValueError:
        return "URL malformada."
    if p.scheme != "https":
        return "El link debe empezar por https://"
    if p.username is not None or p.password is not None or "@" in p.netloc:
        return "El link no puede contener credenciales (símbolo @)."
    if p.hostname not in DOMINIOS_WOMPI:
        return ("Solo se aceptan links oficiales de Wompi "
                f"({', '.join(sorted(DOMINIOS_WOMPI))}).")
    return ""

DEFAULTS = {
    "precio_mensual_cop": 150_000,
    "precio_anual_cop": 1_400_000,
    "link_wompi_mensual": "",      # link de pago creado en el panel de Wompi
    "link_wompi_anual": "",
    "datos_transferencia": "",     # ej. "Bancolombia Ahorros 123-456789-00 — INNOVACION QUIMICA SAS, NIT ..."
    "contacto": "",                # ej. "WhatsApp +57 300 000 0000 · ventas@innovacionquimica.com.co"
}


def cargar_config_pagos() -> dict:
    cfg = dict(DEFAULTS)
    try:
        with open(RUTA_CONFIG_PAGOS, encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, dict):
            cfg.update({k: datos[k] for k in DEFAULTS if k in datos})
    except (OSError, json.JSONDecodeError):
        pass
    # Defensa en profundidad: aunque el JSON haya sido alterado a mano,
    # jamás renderizar un botón de pago hacia un dominio no oficial.
    for k in ("link_wompi_mensual", "link_wompi_anual"):
        if validar_link_wompi(cfg.get(k, "")):
            cfg[k] = ""
    return cfg


def guardar_config_pagos(cfg: dict) -> None:
    limpio = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
    for k in ("link_wompi_mensual", "link_wompi_anual"):
        motivo = validar_link_wompi(limpio.get(k, ""))
        if motivo:
            raise ValueError(f"Link de pago inválido: {motivo}")
    os.makedirs(os.path.dirname(RUTA_CONFIG_PAGOS), exist_ok=True)
    tmp = RUTA_CONFIG_PAGOS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(limpio, f, ensure_ascii=False, indent=2)
    os.replace(tmp, RUTA_CONFIG_PAGOS)


def _fmt_cop(valor) -> str:
    try:
        return f"${int(valor):,.0f} COP".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)


def mostrar_opciones_pago(st, *, compacto: bool = False) -> bool:
    """Renderiza los botones/datos de pago configurados.

    compacto=True → versión breve para la barra lateral.
    Devuelve True si hay al menos una opción de pago configurada.
    """
    cfg = cargar_config_pagos()
    hay_links = bool(cfg["link_wompi_mensual"] or cfg["link_wompi_anual"])
    hay_transf = bool(cfg["datos_transferencia"].strip())
    if not (hay_links or hay_transf):
        return False

    if compacto:
        if cfg["link_wompi_mensual"]:
            st.link_button(f"💳 Renovar mes · {_fmt_cop(cfg['precio_mensual_cop'])}",
                           cfg["link_wompi_mensual"], use_container_width=True)
        if cfg["link_wompi_anual"]:
            st.link_button(f"💳 Renovar año · {_fmt_cop(cfg['precio_anual_cop'])}",
                           cfg["link_wompi_anual"], use_container_width=True)
        return True

    st.markdown("### 💳 Opciones de pago")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Plan Mensual — {_fmt_cop(cfg['precio_mensual_cop'])}**")
        if cfg["link_wompi_mensual"]:
            st.link_button("Pagar con Wompi (tarjeta · PSE · Nequi)",
                           cfg["link_wompi_mensual"], use_container_width=True,
                           type="primary")
    with c2:
        st.markdown(f"**Plan Anual — {_fmt_cop(cfg['precio_anual_cop'])}**")
        if cfg["link_wompi_anual"]:
            st.link_button("Pagar con Wompi (tarjeta · PSE · Nequi)",
                           cfg["link_wompi_anual"], use_container_width=True,
                           type="primary")
    if hay_transf:
        st.markdown("**🏦 Transferencia bancaria (sin recargo):**")
        st.code(cfg["datos_transferencia"], language=None)
    if cfg["contacto"].strip():
        st.caption(f"Tras pagar, envía el comprobante a: {cfg['contacto']} — "
                   "tu acceso se activa el mismo día.")
    else:
        st.caption("Tras pagar, envía el comprobante al administrador — "
                   "tu acceso se activa el mismo día.")
    return True
