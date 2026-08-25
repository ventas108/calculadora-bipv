# -*- coding: utf-8 -*-
"""Página 19 — 🔒 Ledger de Auditoría: cadena de hashes por proyecto.

Res. CREG 174 de 2021, Art. 6, exige que los cálculos tengan trazabilidad
para determinar si son reales o actualizados. Esta página deja sellar un
resultado (bancable, informativo, o diagnóstico) con un hash encadenado al
anterior del mismo proyecto -- si alguien altera un eslabón por fuera de la
app, la cadena se rompe de forma detectable. El sellado desde 📄 Reporte
PDF y 🔍 Diagnóstico ya cubre el flujo normal; esta página es para revisar
el historial completo, verificar la integridad, y exportar para un banco/ITA.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ledger de Auditoría", page_icon="🔒", layout="wide")

from calculos.auth import requerir_login
requerir_login()

from utils.ui import bloquear_traduccion, mostrar_proyecto_activo
bloquear_traduccion()
mostrar_proyecto_activo()

from calculos import ledger_auditoria as ledger

st.title("🔒 Ledger de Auditoría")
st.caption(
    "Historial verificable de resultados oficiales de este proyecto — cada eslabón "
    "encadena su hash con el anterior (SHA-256). Alterar un eslabón guardado, aunque "
    "sea un solo campo, rompe la cadena de forma detectable. **Límite honesto**: esto "
    "protege contra editar un registro sin que se note, no contra borrar el archivo "
    "completo — para eso haría falta un ancla externa, fuera de alcance por ahora."
)

_nombre_proyecto = st.session_state.get("nombre_proyecto", "Proyecto BIPV")
_usuario = st.session_state.get("auth_email", "")

if not _usuario:
    st.error("No se detectó sesión activa — inicia sesión para usar el Ledger de Auditoría.")
    st.stop()

st.info(f"📂 Proyecto activo: **{_nombre_proyecto}**")

# ══════════════════════════ Sellar manualmente ══════════════════════════════
with st.expander("🔒 Sellar el resultado actual (Producción/Financiero)", expanded=False):
    st.caption(
        "Toma un snapshot de los insumos y resultados vigentes en la sesión (panel, "
        "inversor, degradación, tarifa, CAPEX, E_ac, PR, TIR, VPN, LCOE) y lo sella "
        "como un eslabón nuevo. Úsalo para una verificación presupuestal informativa "
        "que no pasa por 📄 Reporte PDF — para bancabilidad/diagnóstico, los botones "
        "de sellado ya están integrados en sus propias páginas."
    )
    _tipo_manual = st.selectbox(
        "Tipo de resultado", options=list(ledger.TIPOS_VALIDOS),
        format_func=lambda k: ledger.TIPO_LABELS.get(k, k),
        key="sel_tipo_sello_manual",
    )
    _nota_manual = st.text_input("Nota (opcional)", key="nota_sello_manual")
    if st.button("🔒 Sellar ahora", key="btn_sellar_manual"):
        _eslabon = ledger.sellar_resultado(
            _nombre_proyecto, _usuario, _tipo_manual,
            ledger.construir_snapshot_insumos(st.session_state),
            ledger.construir_snapshot_resultados(st.session_state),
            nota=_nota_manual,
        )
        if _eslabon:
            st.success(f"🔒 Sellado — ID {_eslabon['hash_propio'][:16]} "
                      f"(eslabón #{_eslabon['id']})")
            st.rerun()
        else:
            st.error("⚠️ No se pudo escribir el eslabón a disco (permisos/espacio del servidor).")

# ══════════════════════════ Verificar integridad ════════════════════════════
_eslabones = ledger.listar_eslabones(_nombre_proyecto, _usuario)

col_v1, col_v2 = st.columns([1, 3])
with col_v1:
    _verificar = st.button("✅ Verificar integridad de la cadena", key="btn_verificar_cadena")
if _verificar:
    _r = ledger.verificar_cadena(_nombre_proyecto, _usuario)
    with col_v2:
        if _r["integra"]:
            st.success(f"🟢 Cadena íntegra — {_r['eslabones_verificados']} eslabón(es) "
                      "verificados, ninguna alteración detectada.")
        else:
            st.error(f"🔴 Cadena ROTA en el eslabón #{_r['primer_eslabon_roto']} — "
                     "algo se alteró por fuera de la app después de sellarse. "
                     "Investiga antes de entregar este historial como evidencia.")

st.markdown("---")

# ══════════════════════════ Historial de eslabones ══════════════════════════
st.subheader(f"📜 Historial — {len(_eslabones)} eslabón(es)")

if not _eslabones:
    st.info(
        "ℹ️ Aún no hay ningún resultado sellado para este proyecto. Se sellan desde "
        "📄 Reporte PDF, 🔍 Diagnóstico, o manualmente arriba."
    )
else:
    _filas = [
        {
            "#": e["id"],
            "Fecha": e["timestamp"],
            "Tipo": ledger.TIPO_LABELS.get(e["tipo"], e["tipo"]),
            "Usuario": e["usuario"],
            "Nota": e["nota"] or "—",
            "ID (hash corto)": e["hash_propio"][:16],
        }
        for e in _eslabones
    ]
    st.dataframe(pd.DataFrame(_filas), hide_index=True, use_container_width=True)

    _opciones_detalle = [f"#{e['id']} — {e['timestamp']}" for e in _eslabones]
    _idx_detalle = st.selectbox("Ver detalle de un eslabón", options=range(len(_eslabones)),
                                format_func=lambda i: _opciones_detalle[i],
                                key="sel_detalle_eslabon")
    _e_sel = _eslabones[_idx_detalle]
    col_d1, col_d2 = st.columns(2)
    col_d1.markdown("**Insumos congelados en este eslabón:**")
    col_d1.json(_e_sel["insumos"])
    col_d2.markdown("**Resultados congelados en este eslabón:**")
    col_d2.json(_e_sel["resultados"])
    st.caption(f"Hash propio: `{_e_sel['hash_propio']}`  ·  "
              f"Hash del eslabón anterior: `{_e_sel['hash_anterior']}`")

    st.markdown("---")
    st.subheader("📤 Exportar para banco / ITA")
    col_e1, col_e2 = st.columns(2)
    col_e1.download_button(
        "⬇️ Exportar historial (JSON)",
        data=ledger.exportar_cadena(_nombre_proyecto, _usuario, formato="json"),
        file_name=f"ledger_{_nombre_proyecto.replace(' ', '_')}.json",
        mime="application/json", use_container_width=True, key="dl_ledger_json",
    )
    col_e2.download_button(
        "⬇️ Exportar historial (Markdown)",
        data=ledger.exportar_cadena(_nombre_proyecto, _usuario, formato="markdown"),
        file_name=f"ledger_{_nombre_proyecto.replace(' ', '_')}.md",
        mime="text/markdown", use_container_width=True, key="dl_ledger_md",
    )
