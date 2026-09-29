"""Opciones del sistema multi-superficie que comparten ⚡ Diagrama Unifilar y
📋 Ficha RETIE (Spec 07/unifilar-retie-multisuperficie).

Los optimizadores y el inversor de la batería son datos del proyecto (se
guardan con él), no de una página: el mismo sistema debe verse igual en el
diagrama y en la ficha.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from calculos.topologia_electrica import (
    CLAVE_BATERIA_INVERSOR,
    CLAVE_OPTIMIZADORES,
    topologia_desde_estado,
)


def opciones_sistema_multisuperficie() -> dict | None:
    """Muestra las opciones del sistema y devuelve la topología con ellas, o
    ``None`` si no hay multi-superficie con grupos de strings."""
    estado = st.session_state
    base = topologia_desde_estado(estado, incluir_bateria=False)
    if base is None:
        return None
    # Sin `key`: el valor vive en la clave de datos del proyecto; una clave de
    # widget se borraría al cambiar de página (ver campos_persistentes).
    estado[CLAVE_OPTIMIZADORES] = st.checkbox(
        "Optimizadores MLPE (uno por módulo)",
        value=bool(estado.get(CLAVE_OPTIMIZADORES)),
        help="Se dibujan en cada string y la ficha los marca por revisar: la app todavía no "
             "valida strings con optimizador (longitud y voltaje los fija el fabricante). "
             "No cambia la energía calculada.",
    )
    incluir_bateria = False
    ids = [i["inversor_id"] for i in base["inversores"]]
    if estado.get("bateria_ok") and ids:
        incluir_bateria = st.checkbox("Incluir la batería de 🔋 Baterías y Balance", value=True)
        if incluir_bateria:
            actual = estado.get(CLAVE_BATERIA_INVERSOR)
            if actual and actual not in ids:
                st.warning(f"⚠️ La batería estaba conectada a «{actual}», que ya no existe en el "
                           f"diseño; se conecta a «{ids[0]}». Revísalo.")
            estado[CLAVE_BATERIA_INVERSOR] = st.selectbox(
                "Inversor al que se conecta la batería", ids,
                index=ids.index(actual) if actual in ids else 0,
                help="La batería necesita un inversor híbrido (con puerto de batería).",
            )
    return topologia_desde_estado(estado, incluir_bateria=incluir_bateria)


def mostrar_resumen_topologia(topo: dict) -> None:
    """Tabla del sistema (una fila por grupo de strings) y estado eléctrico."""
    filas = []
    for inv in topo["inversores"]:
        for rama in inv["ramas"]:
            for g in rama["grupos"]:
                filas.append({
                    "Inversor · MPPT": f"{inv['inversor_id']} · {rama['mppt']}",
                    "Superficie · grupo": f"{g['superficie']} · {g['gid']}",
                    "Panel": g["panel"],
                    "N serie × strings": f"{g['n_serie']} × {g['n_paralelo']}",
                    "Módulos": g["modulos"],
                    "Isc diseño módulo (A)": (round(g["isc_stc_A"], 2) if g.get("isc_stc_A") else None),
                    "Cruza a otra superficie": g.get("cruce_texto") or "—",
                    "Caja combinadora": "sí" if rama["caja_combinadora"] else "no",
                })
    st.caption(
        f"🗺️ Sistema tomado de Vista 3D: {len(topo['superficies'])} superficie(s), "
        f"{topo['n_modulos']} módulos, {len(topo['inversores'])} inversor(es). "
        "Para cambiarlo, edita los grupos de strings en 🗺️ Vista 3D."
    )
    st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
    if topo["sin_asignar"]:
        st.error("🔴 Grupos sin inversor o MPPT válido (no se dibujan): " + ", ".join(topo["sin_asignar"]))
    from calculos.diseno_electrico_multisup import resumen_estado_electrico
    resumen = resumen_estado_electrico(topo["diagnostico"])
    {"rojo": st.error, "amarillo": st.warning}.get(resumen["estado"], st.success)(resumen["texto"])
