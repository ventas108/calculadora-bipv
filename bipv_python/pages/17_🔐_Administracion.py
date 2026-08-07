# -*- coding: utf-8 -*-
"""🔐 Administración — gestión de usuarios, planes y vencimientos (solo admin)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from calculos.auth import (
    PLANES, crear_usuario, listar_usuarios, extender_vencimiento,
    actualizar_usuario, cambiar_password, eliminar_usuario,
    dias_restantes, requerir_login,
)

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()   # #63 — proyecto activo visible en cada página

admin = requerir_login(solo_admin=True)

st.title("🔐 Administración de usuarios")
st.caption("Crea cuentas de prueba o de pago, renueva vencimientos y "
           "desactiva accesos. Solo tú ves esta página.")

# ── Crear usuario ────────────────────────────────────────────────────────────
with st.expander("➕ Crear usuario nuevo", expanded=False):
    with st.form("form_nuevo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre")
        email = c2.text_input("Correo")
        c3, c4 = st.columns(2)
        empresa = c3.text_input("Empresa (opcional)")
        password = c4.text_input("Contraseña inicial", type="password",
                                 help="Compártesela al cliente; puede cambiarse luego.")
        c5, c6 = st.columns(2)
        plan = c5.selectbox("Plan", PLANES, index=0)
        dias = c6.number_input("Días de vigencia", min_value=1, max_value=3650,
                               value=14,
                               help="Prueba: 14 · Mensual: 30 · Anual: 365")
        es_admin = st.checkbox("Es administrador (acceso total, sin vencimiento)")
        ok = st.form_submit_button("Crear usuario", type="primary")
    if ok:
        try:
            crear_usuario(
                email, password, nombre, empresa=empresa,
                rol="admin" if es_admin else "cliente",
                plan="ilimitado" if es_admin else plan,
                dias_vigencia=None if (es_admin or plan == "ilimitado") else int(dias),
            )
            st.success(f"✅ Usuario **{email}** creado ({plan}, {int(dias)} días)."
                       if not es_admin else f"✅ Administrador **{email}** creado.")
        except ValueError as e:
            st.error(str(e))

# ── Tabla de usuarios ────────────────────────────────────────────────────────
usuarios = listar_usuarios()
st.subheader(f"👥 Usuarios ({len(usuarios)})")

filas = []
for u in usuarios:
    d = dias_restantes(u)
    if not u["activo"]:
        estado = "🚫 Desactivado"
    elif d is None:
        estado = "✅ Sin vencimiento"
    elif d < 0:
        estado = f"⛔ Vencido hace {-d} d"
    elif d <= 7:
        estado = f"⚠️ Vence en {d} d"
    else:
        estado = f"✅ {d} d restantes"
    filas.append({
        "Correo": u["email"], "Nombre": u["nombre"], "Empresa": u["empresa"],
        "Rol": u["rol"], "Plan": u["plan"],
        "Vence": u["fecha_vencimiento"] or "—", "Estado": estado,
        "Último acceso": (u["ultimo_acceso"] or "nunca")[:16].replace("T", " "),
    })
st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

# ── Gestionar un usuario ─────────────────────────────────────────────────────
st.subheader("🛠️ Gestionar usuario")
emails = [u["email"] for u in usuarios]
sel = st.selectbox("Selecciona el usuario", emails)
u_sel = next(u for u in usuarios if u["email"] == sel)
es_yo = sel == admin["email"]

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Renovar / extender**")
    dias_ext = st.number_input("Días a sumar", 1, 3650, 30, key="dias_ext")
    if st.button("➕ Extender vigencia", use_container_width=True):
        nuevo = extender_vencimiento(sel, int(dias_ext))
        st.success(f"Nueva fecha de vencimiento: **{nuevo}**")
        st.rerun()
    nuevo_plan = st.selectbox("Cambiar plan", PLANES,
                              index=PLANES.index(u_sel["plan"])
                              if u_sel["plan"] in PLANES else 0)
    if st.button("Aplicar plan", use_container_width=True):
        actualizar_usuario(sel, plan=nuevo_plan,
                           sin_vencimiento=(nuevo_plan == "ilimitado"))
        st.success(f"Plan actualizado a **{nuevo_plan}**.")
        st.rerun()

with c2:
    st.markdown("**Contraseña**")
    pwd = st.text_input("Nueva contraseña", type="password", key="pwd_reset")
    if st.button("🔑 Cambiar contraseña", use_container_width=True):
        try:
            cambiar_password(sel, pwd)
            st.success("Contraseña actualizada (sus sesiones abiertas se cerraron).")
        except ValueError as e:
            st.error(str(e))

with c3:
    st.markdown("**Acceso**")
    if u_sel["activo"]:
        if st.button("🚫 Desactivar cuenta", use_container_width=True,
                     disabled=es_yo,
                     help="No puedes desactivarte a ti mismo." if es_yo else None):
            actualizar_usuario(sel, activo=False)
            st.rerun()
    else:
        if st.button("✅ Reactivar cuenta", use_container_width=True):
            actualizar_usuario(sel, activo=True)
            st.rerun()
    st.markdown("---")
    conf = st.checkbox("Confirmo eliminar definitivamente", key="conf_del",
                       disabled=es_yo)
    if st.button("🗑️ Eliminar usuario", use_container_width=True,
                 disabled=(not conf or es_yo)):
        eliminar_usuario(sel)
        st.rerun()

# ── Configuración de pagos (Fase 2) ─────────────────────────────────────────
st.markdown("---")
st.subheader("💳 Configuración de pagos")
from calculos.pagos import (cargar_config_pagos, guardar_config_pagos,
                            validar_link_wompi)

cfg = cargar_config_pagos()
with st.form("form_pagos"):
    c1, c2 = st.columns(2)
    precio_m = c1.number_input("Precio Plan Mensual (COP)", 0, 100_000_000,
                               int(cfg["precio_mensual_cop"]), step=10_000)
    precio_a = c2.number_input("Precio Plan Anual (COP)", 0, 1_000_000_000,
                               int(cfg["precio_anual_cop"]), step=50_000)
    link_m = c1.text_input("Link de pago Wompi — Mensual",
                           value=cfg["link_wompi_mensual"],
                           placeholder="https://checkout.wompi.co/l/...")
    link_a = c2.text_input("Link de pago Wompi — Anual",
                           value=cfg["link_wompi_anual"],
                           placeholder="https://checkout.wompi.co/l/...")
    transf = st.text_area("Datos para transferencia bancaria (opcional)",
                          value=cfg["datos_transferencia"],
                          placeholder="Bancolombia Ahorros 123-456789-00 — "
                                      "INNOVACION QUIMICA SAS, NIT 900.xxx.xxx")
    contacto = st.text_input("Contacto para enviar comprobante",
                             value=cfg["contacto"],
                             placeholder="WhatsApp +57 3xx xxx xxxx · correo@empresa.com")
    ok_pagos = st.form_submit_button("💾 Guardar configuración de pagos",
                                     type="primary")
if ok_pagos:
    for nombre, link in (("Mensual", link_m), ("Anual", link_a)):
        motivo = validar_link_wompi(link)
        if motivo:
            st.error(f"Link {nombre}: {motivo}")
            st.stop()
    guardar_config_pagos({
        "precio_mensual_cop": int(precio_m), "precio_anual_cop": int(precio_a),
        "link_wompi_mensual": link_m.strip(), "link_wompi_anual": link_a.strip(),
        "datos_transferencia": transf.strip(), "contacto": contacto.strip(),
    })
    st.success("✅ Configuración guardada. Los clientes con plan vencido o por "
               "vencer verán estos botones de pago.")

st.markdown("---")
st.caption(
    "💡 Flujo de venta: crea la cuenta de **prueba (14 días)** → al vencer, el "
    "cliente ve los botones de pago Wompi/transferencia configurados arriba → "
    "paga y te envía el comprobante → aquí extiendes 30 días (mensual) o 365 "
    "(anual). Los datos de usuarios (`datos/usuarios.db`) y esta configuración "
    "(`datos/config_pagos.json`) viven solo en el servidor (no se suben a git)."
)
