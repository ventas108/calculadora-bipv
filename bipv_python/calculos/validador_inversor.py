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
             "arquitectura"}  (None o 0 = no disponible)
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
  - P_dc_max_W > Vdc_max × I_max × n_trackers (potencia DC imposible de alcanzar).
  - P_dc_max_W < 300 W (¿quedó en kW sin convertir?).
  - n_trackers fuera de [1, 12]; n_strings_tracker fuera de [1, 6].
  - Batería fuera de [36, 1000] V.
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
        elif vdc is not None and imax is not None and ntrk is not None:
            techo = vdc * imax * ntrk
            if pdc > techo:
                marcar("P_dc_max_W", "warn",
                       f"P FV máx ({pdc:g} W) supera el techo físico "
                       f"Vdc×I×trackers ({techo:,.0f} W) — verifica corrientes "
                       "y número de trackers.")

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

    return {
        "campos": est,
        "errores": errores,
        "avisos": avisos,
        "ok": not errores,
    }


def icono_estado(estado: str) -> str:
    return {"ok": "🟢", "warn": "🟠", "error": "🔴"}.get(estado, "⚪")
