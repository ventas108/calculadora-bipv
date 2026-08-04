"""
validador_bateria.py — Validador de coherencia física para baterías del catálogo.

Se ejecuta al seleccionar una batería en la página 11 (Baterías y Balance),
ANTES de permitir el dimensionamiento. Objetivo: que nunca se dimensione un
banco con datos en cero o físicamente imposibles sin que el usuario lo vea.

Las baterías llegan desde la hoja Catalogo_Baterias del Excel del servidor
(no hay extractor PDF), así que este validador es la única barrera entre un
dato mal digitado en el Excel y un balance energético equivocado.

Función principal:
  validar_bateria(campos: dict) -> dict
    campos: {"capacidad_kWh", "potencia_kW", "voltaje_V", "dod_pct",
             "eta_rte_pct", "ciclos_vida", "tipo", "costo_usd",
             "garantia_anos"}  (None o 0 = no disponible)
    Retorna:
      {
        "campos":  {campo: {"estado": "ok"|"warn"|"error", "detalle": str}},
        "errores": [str, ...],   # bloquean el dimensionamiento
        "avisos":  [str, ...],   # no bloquean, pero se muestran
        "ok":      bool,
      }

Reglas (bloqueo SOLO en imposibles físicos; el resto avisa):
  ERROR:
  - capacidad_kWh vacía/0 (sin ella no hay dimensionamiento posible).
  - DoD > 100 % o RTE > 100 % (imposibles por definición).
  - RTE < 50 % (ninguna química comercial baja de ahí; dato mal digitado).
  - C-rate = potencia/capacidad > 6 (ninguna batería estacionaria comercial).
  - Voltaje nominal fuera de [10, 1500] V.
  WARN:
  - potencia_kW o voltaje_V vacíos (compatibilidad con inversor queda ciega).
  - DoD fuera de [50, 100] % (plomo-ácido llega a 50; menos es sospechoso).
  - RTE fuera de [80, 100] % (plomo ~75-85 → avisa; litio 90-98).
  - C-rate fuera de [0.2, 3] (LFP típico 0.5–1C).
  - Ciclos fuera de [500, 15000].
  - Garantía > 25 años.
  - Costo/kWh fuera de [50, 1500] USD (mercado 2026: LFP ~100–400).
"""

from typing import Optional


def _num(v) -> Optional[float]:
    """None si el valor es None, no numérico o cero (0 = 'no disponible')."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f != 0 else None


def validar_bateria(campos: dict) -> dict:
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

    cap  = _num(campos.get("capacidad_kWh"))
    pot  = _num(campos.get("potencia_kW"))
    volt = _num(campos.get("voltaje_V"))
    dod  = _num(campos.get("dod_pct"))
    rte  = _num(campos.get("eta_rte_pct"))
    cic  = _num(campos.get("ciclos_vida"))
    usd  = _num(campos.get("costo_usd"))
    gar  = _num(campos.get("garantia_anos"))

    # ── 1. Capacidad: el único obligatorio duro ──────────────────────────────
    if cap is None:
        marcar("capacidad_kWh", "error",
               "Capacidad (kWh) vacía o en cero — sin ella no se puede "
               "dimensionar el banco. Agrégala en la hoja Catalogo_Baterias.")
    elif not (0.5 <= cap <= 2000):
        marcar("capacidad_kWh", "warn",
               f"Capacidad {cap:g} kWh fuera del rango típico [0.5, 2000] kWh "
               "por unidad — ¿está en Wh o Ah por error?")
    else:
        marcar("capacidad_kWh", "ok")

    # ── 2. Potencia y C-rate ─────────────────────────────────────────────────
    if pot is None:
        marcar("potencia_kW", "warn",
               "Potencia continua (kW) vacía — no se podrá verificar el cuello "
               "de botella de carga/descarga contra el inversor.")
    elif cap is not None:
        c_rate = pot / cap
        if c_rate > 6:
            marcar("potencia_kW", "error",
                   f"C-rate = {c_rate:.1f}C (potencia {pot:g} kW / capacidad "
                   f"{cap:g} kWh) — imposible en baterías estacionarias. "
                   "Potencia o capacidad están mal digitadas.")
        elif not (0.2 <= c_rate <= 3):
            marcar("potencia_kW", "warn",
                   f"C-rate = {c_rate:.2f}C inusual (típico LFP: 0.5–1C). "
                   "Verifica potencia y capacidad.")
        else:
            marcar("potencia_kW", "ok")
    else:
        marcar("potencia_kW", "ok")

    # ── 3. Voltaje nominal ───────────────────────────────────────────────────
    if volt is None:
        marcar("voltaje_V", "warn",
               "Voltaje nominal (V) vacío — la verificación de compatibilidad "
               "con el inversor híbrido queda ciega (#25).")
    elif not (10 <= volt <= 1500):
        marcar("voltaje_V", "error",
               f"Voltaje nominal {volt:g} V fuera de [10, 1500] V — imposible "
               "en bancos comerciales; dato mal digitado.")
    else:
        marcar("voltaje_V", "ok")

    # ── 4. DoD ───────────────────────────────────────────────────────────────
    if dod is None:
        marcar("dod_pct", "warn", "DoD vacío — se usará 80 % por defecto.")
    elif dod > 100:
        marcar("dod_pct", "error",
               f"DoD = {dod:g} % — imposible (>100 %). Dato mal digitado.")
    elif dod < 50:
        marcar("dod_pct", "warn",
               f"DoD = {dod:g} % muy bajo (plomo-ácido llega a 50 %; litio "
               "80–100 %). Verifica.")
    else:
        marcar("dod_pct", "ok")

    # ── 5. Eficiencia round-trip ─────────────────────────────────────────────
    if rte is None:
        marcar("eta_rte_pct", "warn", "RTE vacío — se usará 95 % por defecto.")
    elif rte > 100:
        marcar("eta_rte_pct", "error",
               f"Eficiencia RTE = {rte:g} % — imposible (>100 %).")
    elif rte < 50:
        marcar("eta_rte_pct", "error",
               f"Eficiencia RTE = {rte:g} % — ninguna química comercial baja "
               "de 50 %; dato mal digitado.")
    elif rte < 80:
        marcar("eta_rte_pct", "warn",
               f"RTE = {rte:g} % bajo (plomo ~75–85 %, litio 90–98 %). "
               "Si la batería es litio, revisa el dato.")
    else:
        marcar("eta_rte_pct", "ok")

    # ── 6. Ciclos de vida ────────────────────────────────────────────────────
    if cic is None:
        marcar("ciclos_vida", "warn", "Ciclos de vida vacíos — se usará 3000.")
    elif not (500 <= cic <= 15000):
        marcar("ciclos_vida", "warn",
               f"Ciclos de vida = {cic:g} fuera del rango típico [500, 15000].")
    else:
        marcar("ciclos_vida", "ok")

    # ── 7. Costo por kWh ─────────────────────────────────────────────────────
    if usd is not None and cap is not None:
        usd_kwh = usd / cap
        if not (50 <= usd_kwh <= 1500):
            marcar("costo_usd", "warn",
                   f"Costo/kWh = {usd_kwh:,.0f} USD/kWh fuera del rango de "
                   "mercado [50, 1500] — verifica costo o capacidad.")
        else:
            marcar("costo_usd", "ok")

    # ── 8. Garantía ──────────────────────────────────────────────────────────
    if gar is not None and gar > 25:
        marcar("garantia_anos", "warn",
               f"Garantía de {gar:g} años inusual (típico 5–15).")

    return {
        "campos": est,
        "errores": errores,
        "avisos": avisos,
        "ok": not errores,
    }


def icono_estado(estado: str) -> str:
    return {"ok": "🟢", "warn": "🟠", "error": "🔴"}.get(estado, "⚪")
