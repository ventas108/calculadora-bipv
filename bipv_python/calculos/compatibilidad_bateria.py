"""
compatibilidad_bateria.py — Verificación batería ↔ inversor (tarea #25).

Función pura (sin streamlit) para poder testearla en el banco de regresión.
Usada por pages/11_🔋_Baterias_y_Balance.py: el estado "error" bloquea el
botón ▶️ Dimensionar batería.
"""

# Ruta de corrección común para los bloqueos heurísticos: si la ficha real del
# inversor confirma que es híbrido, el usuario puede desbloquear corrigiendo el
# catálogo — se repite en los mensajes para que siempre haya salida accionable.
_RUTA_CORRECCION = (
    "Si la ficha técnica confirma que el inversor **sí es híbrido**, corrige la hoja "
    "`Catalogo_Inversores` del Excel: marca `Inversor Híbrido (Si/No)` = **Si** y "
    "completa `Voltaje Batería Min (V)` / `Voltaje Batería Max (V)`. "
    "Si no lo es, selecciona otro inversor en **Página 4 › Dimensionamiento**."
)


def check_compatibilidad(bat_d: dict, inv_d: dict, inv_nom: str) -> tuple:
    """(estado, msg) — estado: 'ok' | 'warning' | 'error'.

    'error' bloquea el dimensionamiento; 'warning' avisa pero permite continuar.
    """
    if not inv_d and not inv_nom:
        return "warning", (
            "⚠️ **Inversor no seleccionado:** ve a Página 4 › Dimensionamiento "
            "para seleccionar el inversor antes de verificar la compatibilidad."
        )
    bat_v       = bat_d.get("voltaje_V")
    # Rango REAL de operación de la batería (varía con el estado de carga:
    # más bajo a descarga profunda, más alto a carga plena) -- cuando el
    # catálogo lo trae (hoja Catalogo_Baterias, columnas Voltaje Min/Max),
    # el chequeo de abajo verifica el rango completo contra la ventana del
    # inversor, no solo el punto nominal. Antes de esto, una batería cuyo
    # nominal cayera dentro de la ventana del inversor pero cuyo mínimo a
    # descarga profunda cayera por debajo (o el máximo a carga plena
    # superara el techo) se habría marcado "ok" sin serlo.
    bat_v_min_propio = bat_d.get("voltaje_min_V")
    bat_v_max_propio = bat_d.get("voltaje_max_V")
    es_hibrido  = inv_d.get("es_hibrido", False)
    bat_v_min   = inv_d.get("bat_voltaje_min")
    bat_v_max   = inv_d.get("bat_voltaje_max")
    inv_lower   = inv_nom.lower()

    # Heurística por nombre si no hay flag explícito
    es_string   = any(x in inv_lower for x in ["mid", "max", "mtlp", "string"])
    es_hibrido_h = any(x in inv_lower for x in ["sph", "spa", "hybrid", "storage",
                                                  "min tl-x", "min-tl-x", "bcs"])
    tipo_inv = es_hibrido or es_hibrido_h

    motivos = []

    # 1. Verificar si es inversor de string (no acepta baterías)
    if not tipo_inv and es_string:
        motivos.append(
            f"**`{inv_nom}`** parece un inversor de **string** (sin puerto DC para batería). "
            "Las baterías requieren un inversor **híbrido** (ej. Growatt SPH/SPA, Huawei SUN2000).  \n"
            f"  {_RUTA_CORRECCION}"
        )

    # 2. Verificar rango de voltaje si el inversor es híbrido y tiene rango
    if tipo_inv and bat_v and bat_v_min and bat_v_max:
        if bat_v_min_propio and bat_v_max_propio:
            # Chequeo riguroso: el rango COMPLETO de operación de la batería
            # debe caber dentro de la ventana del inversor, no solo el nominal.
            if bat_v_min_propio < bat_v_min:
                motivos.append(
                    f"El voltaje **mínimo real** de la batería a descarga profunda "
                    f"({bat_v_min_propio:.0f} V) cae por debajo del mínimo admitido por "
                    f"el inversor ({bat_v_min:.0f} V) — el nominal ({bat_v:.0f} V) no lo "
                    "muestra, pero el banco entraría fuera de rango al descargarse."
                )
            if bat_v_max_propio > bat_v_max:
                motivos.append(
                    f"El voltaje **máximo real** de la batería a carga plena "
                    f"({bat_v_max_propio:.0f} V) supera el máximo admitido por el "
                    f"inversor ({bat_v_max:.0f} V) — el nominal ({bat_v:.0f} V) no lo "
                    "muestra, pero el banco entraría fuera de rango al cargarse."
                )
        elif not (bat_v_min <= bat_v <= bat_v_max):
            motivos.append(
                f"Voltaje de batería **{bat_v:.0f} V** fuera del rango del inversor "
                f"({bat_v_min:.0f}–{bat_v_max:.0f} V). Selecciona una batería dentro del "
                "rango o cambia el inversor en **Página 4**."
            )

    # 3. Batería HV con inversor no identificado como híbrido
    if not tipo_inv and not es_string and bat_v and bat_v > 150:
        motivos.append(
            f"La batería es **alta tensión ({bat_v:.0f} V)** y el inversor no está "
            "identificado como híbrido en el catálogo.  \n"
            f"  {_RUTA_CORRECCION}"
        )

    # 4. Batería LV (≤ 80 V) con híbrido que normalmente requiere HV
    # Growatt SPH/SPA, Huawei SUN2000, Sungrow SH, Solax X-Hybrid solo aceptan
    # bancos de alta tensión (100–550 V). Una batería de 48 V no es compatible.
    _hv_only_heuristic = any(x in inv_lower for x in
                             ["sph", "spa", "sun2000", "sungrow", "sh-", "x-hybrid", "solax"])
    if tipo_inv and bat_v and bat_v <= 80 and not bat_v_min and _hv_only_heuristic:
        motivos.append(
            f"La batería es de **baja tensión ({bat_v:.0f} V)** y **`{inv_nom}`** "
            "normalmente requiere bancos de **alta tensión (100–550 V)**.  \n"
            "  Si la ficha del inversor confirma que acepta baja tensión, completa "
            "`Voltaje Batería Min/Max (V)` en la hoja `Catalogo_Inversores` del Excel "
            "para que la verificación use el rango real."
        )

    # 5. Inversor híbrido pero la batería no tiene voltaje definido en el catálogo
    if tipo_inv and not bat_v and not motivos:
        return "warning", (
            f"⚠️ **Inversor híbrido detectado ({inv_nom})** pero sin datos suficientes:  \n"
            "- La batería **no tiene voltaje definido** en el catálogo. "
            "No es posible verificar la compatibilidad de tensión con el inversor. "
            "Agregue el campo `Voltaje Nominal (V)` en la hoja `Catalogo_Baterias` del Excel."
        )

    if motivos:
        return "error", "🔴 **Incompatibilidad detectada:**\n" + "\n".join(f"- {m}" for m in motivos)
    elif tipo_inv and bat_v:
        if bat_v_min and bat_v_max:
            if bat_v_min_propio and bat_v_max_propio:
                return "ok", (
                    f"✅ Inversor híbrido · Rango de operación de la batería "
                    f"**{bat_v_min_propio:.0f}–{bat_v_max_propio:.0f} V** ✓ dentro del "
                    f"rango admitido **{bat_v_min:.0f}–{bat_v_max:.0f} V** "
                    "(chequeo sobre el rango completo, no solo el voltaje nominal)"
                )
            return "ok", (
                f"✅ Inversor híbrido · Voltaje batería **{bat_v:.0f} V** ✓ "
                f"dentro del rango admitido **{bat_v_min:.0f}–{bat_v_max:.0f} V** "
                "*(el catálogo no trae el rango de voltaje propio de la batería — "
                "verificado solo el punto nominal, no el rango completo de operación)*"
            )
        return "ok", (
            f"✅ Inversor híbrido detectado (**{inv_nom}**) · Voltaje batería {bat_v:.0f} V  \n"
            "*(Rango DC de batería no definido en el catálogo — verifique la ficha del inversor.)*"
        )
    else:
        return "warning", (
            f"⚠️ No se pudo determinar el tipo de **`{inv_nom}`** automáticamente.  \n"
            + (f"Voltaje de batería: **{bat_v:.0f} V**.  \n" if bat_v else "")
            + "Confirme en la ficha del inversor que tiene **puerto DC para batería** "
            "y que el rango de tensión es compatible. "
            "Puedes marcar `Inversor Híbrido (Si/No)` y los rangos de batería en la "
            "hoja `Catalogo_Inversores` del Excel para una verificación exacta."
        )
