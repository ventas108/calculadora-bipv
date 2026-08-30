"""
validador_inversor.py — Validador de coherencia física para parámetros de inversores.

Se ejecuta DESPUÉS de la extracción PDF y ANTES de guardar en el catálogo
(página 15). Objetivo: que nunca entre al catálogo un inversor con valores
en cero o físicamente imposibles sin que el usuario lo vea marcado.

Función principal:
  validar_inversor(campos: dict) -> dict
    campos: {"Vdc_max", "Vmppt_min", "Vmppt_max", "V_mppt_activo",
             "V_arranque", "n_trackers", "n_strings_tracker",
             "I_max_tracker", "Isc_max_tracker", "P_dc_max_W",
             "es_hibrido", "bat_voltaje_min", "bat_voltaje_max",
             "bat_corriente_carga_max", "arquitectura"}
             (None o 0 = no disponible)
    Retorna:
      {
        "campos":  {campo: {"estado": "ok"|"warn"|"error", "detalle": str}},
        "errores": [str, ...],   # bloquean el guardado
        "avisos":  [str, ...],   # no bloquean, pero se muestran
        "ok":      bool,
      }

Reglas (bloqueo SOLO en invariantes universales; el resto avisa):
  ERROR:
  - Vdc_max obligatorio y > 0.
  - Vmppt_min < Vmppt_max (si ambos existen).
  - Vmppt_max ≤ Vdc_max (el rango MPPT no puede superar el límite físico).
  - Isc_max_tracker ≥ I_max_tracker (por definición: cortocircuito ≥ operación).
  - V_mppt_activo dentro de [Vmppt_min, Vmppt_max] estrictamente si lo excede
    por arriba del Vdc_max (imposible).
  - Batería (solo híbridos con ambos valores): bat_min < bat_max.
  WARN:
  - Vmppt_min / Vmppt_max / n_trackers / I_max_tracker / P_dc_max_W vacíos
    (el Dimensionamiento los necesita).
  - Vdc_max fuera de [60, 1500] V (60 V cubre microinversores).
  - V_arranque fuera de [0.5×Vmppt_min, Vmppt_max].
  - V_mppt_activo fuera del rango MPPT (algunos fabricantes lo definen distinto).
  - Isc/I_max con ratio > 2 (posible confusión de campos).
  - P_dc_max_W > Vmppt_min × I_max × n_trackers (potencia DC imposible de
    alcanzar a la tensión MÍNIMA del rango MPPT -- el peor caso real de
    corriente, no Vdc_max, que da un techo artificialmente generoso; fix
    30-ago-2026. Para híbridos sin n_trackers publicado -- común en
    equipos de un solo cargador FV -- se asume 1 en vez de omitir el
    chequeo).
  - P_dc_max_W < 300 W (¿quedó en kW sin convertir?).
  - n_trackers fuera de [1, 12]; n_strings_tracker fuera de [1, 6].
  - Batería fuera de [36, 1000] V.
  - bat_corriente_carga_max vacío en híbridos (no bloquea; solo avisa que
    sin ese dato no se puede verificar compatibilidad con la batería real).
"""

from typing import Optional


def _num(v) -> Optional[float]:
    """None si el valor es None, no numérico o cero (0 = 'no disponible')."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f != 0 else None


def validar_inversor(campos: dict) -> dict:
    est: dict = {}
    errores: list = []
    avisos: list = []

    def marcar(campo: str, estado: str, detalle: str = ""):
        orden = {"ok": 0, "warn": 1, "error": 2}
        prev = est.get(campo)
        if prev is None or orden[estado] > orden[prev["estado"]]:
            est[campo] = {"estado": estado, "detalle": detalle}
        if estado == "error" and detalle:
            errores.append(detalle)
        elif estado == "warn" and detalle:
            avisos.append(detalle)

    vdc   = _num(campos.get("Vdc_max"))
    vmin  = _num(campos.get("Vmppt_min"))
    vmax  = _num(campos.get("Vmppt_max"))
    vact  = _num(campos.get("V_mppt_activo"))
    varr  = _num(campos.get("V_arranque"))
    ntrk  = _num(campos.get("n_trackers"))
    nstr  = _num(campos.get("n_strings_tracker"))
    imax  = _num(campos.get("I_max_tracker"))
    iscm  = _num(campos.get("Isc_max_tracker"))
    pdc   = _num(campos.get("P_dc_max_W"))
    bmin  = _num(campos.get("bat_voltaje_min"))
    bmax  = _num(campos.get("bat_voltaje_max"))
    hib   = bool(campos.get("es_hibrido"))
    bcarg = _num(campos.get("bat_corriente_carga_max"))

    # ── 1. Vdc_max: el único obligatorio duro ────────────────────────────────
    if vdc is None:
        marcar("Vdc_max", "error",
               "Tensión DC Máxima vacía o en cero — es el límite físico del "
               "inversor y es obligatoria para dimensionar strings.")
    elif not (60 <= vdc <= 1500):
        marcar("Vdc_max", "warn",
               f"Vdc máx = {vdc:g} V fuera del rango típico [60, 1500] V "
               "(60 V solo en microinversores). Verifica.")
    else:
        marcar("Vdc_max", "ok")

    # ── 2. Campos necesarios para Dimensionamiento: vacíos → aviso ──────────
    for campo, val, etiqueta in (
        ("Vmppt_min", vmin, "Rango MPPT mín"), ("Vmppt_max", vmax, "Rango MPPT máx"),
        ("n_trackers", ntrk, "N° trackers MPPT"),
        ("I_max_tracker", imax, "Corriente máx por tracker"),
        ("P_dc_max_W", pdc, "Potencia FV máx recomendada"),
    ):
        if val is None:
            marcar(campo, "warn",
                   f"{etiqueta} vacío — el Dimensionamiento no podrá verificar "
                   "este límite. Tómalo de la ficha.")
        else:
            marcar(campo, "ok")

    # ── 3. Orden de voltajes (invariantes universales) ───────────────────────
    if vmin is not None and vmax is not None and vmin >= vmax:
        marcar("Vmppt_min", "error",
               f"Rango MPPT invertido: mín ({vmin:g} V) debe ser MENOR que "
               f"máx ({vmax:g} V).")
    if vmax is not None and vdc is not None and vmax > vdc:
        marcar("Vmppt_max", "error",
               f"MPPT máx ({vmax:g} V) no puede superar la Tensión DC Máxima "
               f"({vdc:g} V) — algún valor está mal extraído.")

    # ── 4. V_mppt_activo y V_arranque ────────────────────────────────────────
    if vact is not None:
        if vdc is not None and vact > vdc:
            marcar("V_mppt_activo", "error",
                   f"MPPT activo ({vact:g} V) supera la Tensión DC Máxima "
                   f"({vdc:g} V) — imposible.")
        elif vmin is not None and vmax is not None and not (vmin <= vact <= vmax):
            marcar("V_mppt_activo", "warn",
                   f"MPPT activo ({vact:g} V) fuera del rango MPPT "
                   f"[{vmin:g}, {vmax:g}] V — algunos fabricantes lo definen "
                   "distinto, pero verifícalo.")
        else:
            marcar("V_mppt_activo", "ok")
    if varr is not None:
        if vdc is not None and varr > vdc:
            marcar("V_arranque", "error",
                   f"V arranque ({varr:g} V) supera la Tensión DC Máxima "
                   f"({vdc:g} V) — imposible.")
        elif vmin is not None and vmax is not None and not (0.5 * vmin <= varr <= vmax):
            marcar("V_arranque", "warn",
                   f"V arranque ({varr:g} V) inusual frente al rango MPPT "
                   f"[{vmin:g}, {vmax:g}] V. Verifica que no sea el de batería.")
        else:
            marcar("V_arranque", "ok")

    # ── 5. Corrientes: Isc ≥ I_max siempre ───────────────────────────────────
    if imax is not None and iscm is not None:
        if iscm < imax:
            marcar("Isc_max_tracker", "error",
                   f"Isc máx ({iscm:g} A) debe ser MAYOR O IGUAL que la corriente "
                   f"de operación máx ({imax:g} A) — están intercambiados o mal "
                   "extraídos.")
        elif iscm > 2.0 * imax:
            marcar("Isc_max_tracker", "warn",
                   f"Isc/I_max = {iscm / imax:.2f} (>2) — ratio inusual; el típico "
                   "es 1.2–1.6. Verifica que Isc no sea el total del equipo.")
        else:
            marcar("Isc_max_tracker", "ok")
    elif iscm is None:
        marcar("Isc_max_tracker", "warn",
               "Isc máx por tracker vacío — algunos fabricantes (MUST, POWEST) "
               "no lo publican; si la ficha lo trae, agrégalo.")

    # ── 6. Trackers y strings ────────────────────────────────────────────────
    if ntrk is not None and not (1 <= ntrk <= 12):
        marcar("n_trackers", "warn", f"N° trackers = {ntrk:g} fuera de [1, 12].")
    if nstr is not None and not (1 <= nstr <= 6):
        marcar("n_strings_tracker", "warn",
               f"Strings/tracker = {nstr:g} fuera de [1, 6].")
    elif nstr is None:
        marcar("n_strings_tracker", "warn",
               "Strings por tracker vacío — el Dimensionamiento asumirá 1.")

    # ── 7. Potencia DC plausible ─────────────────────────────────────────────
    if pdc is not None:
        if pdc < 300:
            marcar("P_dc_max_W", "warn",
                   f"P FV máx = {pdc:g} W parece muy baja — ¿la ficha la reporta "
                   "en kW y faltó multiplicar ×1000?")
        elif imax is not None:
            # Bug real corregido (30-ago-2026): el "techo físico" usaba
            # Vdc_max (el límite ABSOLUTO superior), que da el peor caso más
            # GENEROSO posible -- P=V×I, a igual potencia la corriente real
            # es MAYOR cuanto MENOR es la tensión, así que el peor caso real
            # de corriente ocurre en Vmppt_min, no en Vdc_max. Usar Vdc_max
            # infla artificialmente el techo (falso negativo: nunca avisa
            # aunque la potencia sea electricamente incoherente con la
            # corriente del cargador a baja tensión).
            v_peor_caso = vmin if vmin is not None else vdc
            # n_trackers en None es MUY común en híbridos de un solo
            # cargador FV (ninguna ficha MUST de esta auditoría lo publica);
            # antes esto saltaba el chequeo por completo. Para híbridos sin
            # el dato, asumir 1 tracker (patrón confirmado en toda la
            # familia MUST) en vez de dejar el chequeo ciego.
            n_efectivo = ntrk if ntrk is not None else (1.0 if hib else None)
            if v_peor_caso is not None and n_efectivo is not None:
                techo = v_peor_caso * imax * n_efectivo
                if pdc > techo:
                    marcar("P_dc_max_W", "warn",
                           f"P FV máx ({pdc:g} W) supera el techo físico a "
                           f"tensión mínima MPPT ({v_peor_caso:g} V × {imax:g} A × "
                           f"{n_efectivo:g} tracker(es) = {techo:,.0f} W) — "
                           "verifica corrientes y número de trackers.")

    # ── 8. Batería (solo híbridos) ───────────────────────────────────────────
    if hib:
        if bmin is not None and bmax is not None and bmin >= bmax:
            marcar("bat_voltaje_min", "error",
                   f"Rango de batería invertido: mín ({bmin:g} V) debe ser MENOR "
                   f"que máx ({bmax:g} V).")
        for campo, val in (("bat_voltaje_min", bmin), ("bat_voltaje_max", bmax)):
            if val is not None and not (36 <= val <= 1000):
                marcar(campo, "warn",
                       f"Voltaje de batería {val:g} V fuera del rango típico "
                       "[36, 1000] V (48 V residencial – alta tensión comercial).")
            elif val is None:
                marcar(campo, "warn",
                       "Inversor híbrido sin rango de voltaje de batería — la "
                       "verificación de compatibilidad de baterías quedará ciega.")

    # ── 9. Corriente máxima de carga de batería (solo híbridos) ─────────────
    # Dato fijo del hardware del cargador (no depende de qué batería se
    # instale, a diferencia del voltaje) -- ver bat_corriente_carga_max en
    # calculos/pdf_inversor_extractor.py. Aquí solo se marca "ok"/"warn" de
    # presencia; la comparación real contra la batería del proyecto es
    # manual (esta app no conoce la batería real que el usuario instalará).
    if hib:
        if bcarg is not None:
            marcar("bat_corriente_carga_max", "ok")
        else:
            marcar("bat_corriente_carga_max", "warn",
                   "Corriente máxima de carga de batería vacía — no publicada "
                   "en la ficha, o el fabricante usa un fraseo distinto. Sin "
                   "este dato no podrás verificar si tu batería real acepta "
                   "la corriente de carga del inversor.")

    return {
        "campos": est,
        "errores": errores,
        "avisos": avisos,
        "ok": not errores,
    }


def icono_estado(estado: str) -> str:
    return {"ok": "🟢", "warn": "🟠", "error": "🔴"}.get(estado, "⚪")


# Campos donde tiene sentido esperar monotonía dentro de una misma familia
# (a mayor variante, igual o mayor valor) -- no incluye campos de rango
# eléctrico compartido por toda la familia (Vdc_max, Vmppt_min/max), que
# suelen ser iguales en todos los modelos, ni bat_voltaje_*, que depende de
# la batería, no del modelo.
_CAMPOS_MONOTONOS_FAMILIA = [
    "P_dc_max_W", "I_max_tracker", "Isc_max_tracker", "bat_corriente_carga_max",
]


def validar_coherencia_familia(modelos_detectados: list, valores_por_modelo: dict) -> dict:
    """
    Coherencia CRUZADA entre submodelos de una misma ficha multi-modelo
    (idea real del usuario, 30-ago-2026): no intenta parsear la potencia
    del nombre del modelo (varía por fabricante) -- en cambio, verifica que
    los campos numéricos por modelo sean monótonos NO decrecientes en el
    mismo orden en que la ficha los lista. Los fabricantes siempre listan
    la familia de menor a mayor potencia (verificado en las 3 fichas MUST
    de esta auditoría) -- si un campo baja donde otro sube entre el mismo
    par de modelos, es indicio de una columna mal alineada durante la
    extracción (el mismo tipo de bug real ya encontrado y corregido en
    P_dc_max_W/modelo singular en esta sesión), no de un dato real.

    Parameters
    ----------
    modelos_detectados : lista en el orden real de la ficha (ver
                          `_extraer_multimodelo()` en pdf_inversor_extractor.py).
    valores_por_modelo : dict {modelo: {campo: valor}} de la misma función.

    Returns
    -------
    {"avisos": [str, ...], "ok": bool}  -- nunca bloquea el guardado, solo avisa.
    """
    avisos: list = []
    if len(modelos_detectados) < 2:
        return {"avisos": avisos, "ok": True}

    for campo in _CAMPOS_MONOTONOS_FAMILIA:
        pares_validos = [
            (i, valores_por_modelo.get(m, {}).get(campo))
            for i, m in enumerate(modelos_detectados)
        ]
        pares_validos = [(i, v) for i, v in pares_validos if v is not None]
        if len(pares_validos) < 2:
            continue
        for (i1, v1), (i2, v2) in zip(pares_validos, pares_validos[1:]):
            if v2 < v1:
                avisos.append(
                    f"{campo}: {modelos_detectados[i2]} ({v2:g}) es MENOR que "
                    f"{modelos_detectados[i1]} ({v1:g}) — los fabricantes listan "
                    "la familia de menor a mayor potencia; esto sugiere una "
                    "columna mal alineada en la extracción, no un dato real. "
                    "Verifica contra la ficha antes de guardar."
                )

    return {"avisos": avisos, "ok": not avisos}
