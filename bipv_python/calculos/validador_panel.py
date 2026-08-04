"""
validador_panel.py — Validador de coherencia física para parámetros de paneles FV.

Se ejecuta DESPUÉS de la extracción PDF y ANTES de guardar en el catálogo.
Objetivo: que nunca entre al catálogo un valor en cero o físicamente
imposible sin que el usuario lo vea marcado.

Función principal:
  validar_panel(campos: dict) -> dict
    campos: {"Pmax", "Voc", "Isc", "Vmp", "Imp", "N_s", "CoefVoc",
             "CoefIsc", "CoefPmax", "NOCT", "dimensiones", "Bifacialidad",
             "Transparencia"}  (None o 0 = no disponible)
    Retorna:
      {
        "campos":   {campo: {"estado": "ok"|"warn"|"error", "detalle": str}},
        "errores":  [str, ...],   # bloquean el guardado
        "avisos":   [str, ...],   # no bloquean, pero se muestran
        "ok":       bool,         # True si no hay errores
      }

Reglas (todas con fundamento físico):
  - Pmax, Voc, Isc, Vmp, Imp son obligatorios y > 0.
  - Vmp < Voc  e  Imp < Isc (siempre, por definición de la curva IV).
  - Pmax ≈ Vmp × Imp: desviación ≤3% ok, 3–8% aviso, >8% error.
  - Voc/Ns entre 0.55 y 0.95 V/celda (silicio). Atrapa Ns de panel
    half-cut mal contado (132 vs 66) y Ns basura (2384 = dimensión).
  - Coeficientes: β Voc ∈ [−0.45, −0.20], γ Pmax ∈ [−0.50, −0.20],
    α Isc ∈ [0, +0.10] %/°C. Cero o fuera de rango → aviso.
  - NOCT ∈ [38, 50] °C.
  - Eficiencia = Pmax / (área × 1000 W/m²) ∈ [5, 25] % (BIPV
    semitransparente puede ser baja; >25% es imposible hoy).
  - Bifacialidad: 0 (monofacial) o ∈ [50, 100] %.
"""

import re
from typing import Optional


# ── Rangos de plausibilidad (min, max, unidad) ───────────────────────────────
_RANGO_COEF = {
    "CoefVoc":  (-0.45, -0.20, "β Voc"),
    "CoefPmax": (-0.50, -0.20, "γ Pmax"),
    "CoefIsc":  (0.0,    0.10, "α Isc"),
}

_V_CELDA_MIN, _V_CELDA_MAX = 0.55, 0.95   # V por celda de silicio
_NOCT_MIN, _NOCT_MAX = 38.0, 50.0
_EF_MIN, _EF_MAX = 5.0, 25.0              # % eficiencia de módulo


def _num(v) -> Optional[float]:
    """None si el valor es None, no numérico o cero (0 = 'no extraído')."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f != 0 else None


def _parse_dimensiones(dims) -> Optional[tuple]:
    """'2384x1303x33' o '2384x1303' → (largo_mm, ancho_mm) o None."""
    if not dims:
        return None
    m = re.match(r'\s*([0-9]{3,4})\s*[xX×]\s*([0-9]{3,4})', str(dims))
    if not m:
        return None
    a, b = float(m.group(1)), float(m.group(2))
    return (max(a, b), min(a, b))


def validar_panel(campos: dict) -> dict:
    est: dict = {}
    errores: list = []
    avisos: list = []

    def marcar(campo: str, estado: str, detalle: str = ""):
        # No degradar un error a warn/ok si ya fue marcado
        orden = {"ok": 0, "warn": 1, "error": 2}
        prev = est.get(campo)
        if prev is None or orden[estado] > orden[prev["estado"]]:
            est[campo] = {"estado": estado, "detalle": detalle}
        if estado == "error" and detalle:
            errores.append(detalle)
        elif estado == "warn" and detalle:
            avisos.append(detalle)

    # Tecnologías de película delgada: la celda no es de silicio cristalino,
    # así que las reglas Voc/Ns y eficiencia mínima NO aplican como bloqueo.
    _tech = str(campos.get("tecnologia") or "").strip().lower()
    es_thin_film = _tech in {"cdte", "cis", "cigs", "a-si", "thin film", "película delgada"}

    pmax = _num(campos.get("Pmax"))
    voc  = _num(campos.get("Voc"))
    isc  = _num(campos.get("Isc"))
    vmp  = _num(campos.get("Vmp"))
    imp  = _num(campos.get("Imp"))
    ns   = _num(campos.get("N_s"))
    noct = _num(campos.get("NOCT"))
    bif  = _num(campos.get("Bifacialidad"))

    # ── 1. Obligatorios ──────────────────────────────────────────────────────
    for nombre, val, etiqueta in (
        ("Pmax", pmax, "Pmax (W)"), ("Voc", voc, "Voc (V)"),
        ("Isc", isc, "Isc (A)"), ("Vmp", vmp, "Vmp (V)"), ("Imp", imp, "Imp (A)"),
    ):
        if val is None:
            marcar(nombre, "error", f"{etiqueta} está vacío o en cero — es obligatorio.")
        else:
            marcar(nombre, "ok")

    # ── 2. Orden de la curva IV ──────────────────────────────────────────────
    if vmp is not None and voc is not None and vmp >= voc:
        marcar("Vmp", "error", f"Vmp ({vmp:g} V) debe ser MENOR que Voc ({voc:g} V).")
    if imp is not None and isc is not None and imp >= isc:
        marcar("Imp", "error", f"Imp ({imp:g} A) debe ser MENOR que Isc ({isc:g} A).")

    # ── 3. Pmax ≈ Vmp × Imp ──────────────────────────────────────────────────
    if pmax and vmp and imp:
        calc = vmp * imp
        dev = abs(calc - pmax) / pmax * 100
        if dev > 8.0:
            marcar("Pmax", "error",
                   f"Pmax ({pmax:g} W) no cuadra con Vmp×Imp ({calc:.1f} W): "
                   f"desviación {dev:.1f}% (>8%). Algún valor está mal extraído.")
        elif dev > 3.0:
            marcar("Pmax", "warn",
                   f"Pmax ({pmax:g} W) vs Vmp×Imp ({calc:.1f} W): desviación {dev:.1f}%. Revisa.")

    # ── 4. Voltaje por celda (Ns) — regla de silicio cristalino ─────────────
    if ns is not None and voc is not None:
        v_celda = voc / ns
        if es_thin_film:
            # CdTe/CIS/a-Si: voltaje por celda distinto — solo avisar si es absurdo
            if not (0.3 <= v_celda <= 2.0):
                marcar("N_s", "warn",
                       f"Voc/Ns = {v_celda:.3f} V/celda inusual incluso para "
                       f"{_tech.upper()} — verifica Ns.")
            else:
                marcar("N_s", "ok")
        elif not (_V_CELDA_MIN <= v_celda <= _V_CELDA_MAX):
            sugerido = None
            # Sugerir Ns/2 (half-cut contado en medias celdas) si eso lo arregla
            if _V_CELDA_MIN <= voc / (ns / 2) <= _V_CELDA_MAX:
                sugerido = int(ns / 2)
            det = (f"Voc/Ns = {v_celda:.3f} V/celda — fuera de [0.55, 0.95]. "
                   f"Ns={ns:g} parece incorrecto.")
            if sugerido:
                det += (f" Si el panel es half-cut, las {ns:g} son MEDIAS celdas: "
                        f"usa Ns = {sugerido}.")
            marcar("N_s", "error", det)
        else:
            marcar("N_s", "ok")
    elif ns is None:
        marcar("N_s", "warn",
               "Ns (celdas en serie) vacío — el Motor IV lo necesita. "
               "Half-cut: usa la mitad de las medias celdas (ej. 132 → 66).")

    # ── 5. Coeficientes de temperatura ───────────────────────────────────────
    for campo, (lo, hi, nombre) in _RANGO_COEF.items():
        v = campos.get(campo)
        v = None if v is None else float(v)
        if v is None or v == 0:
            marcar(campo, "warn",
                   f"{nombre} vacío/cero — la simulación usará un valor genérico "
                   "menos preciso. Tómalo de la ficha.")
        elif not (lo <= v <= hi):
            marcar(campo, "warn",
                   f"{nombre} = {v:g} %/°C fuera del rango típico [{lo:g}, {hi:g}]. "
                   "Verifica signo y unidad.")
        else:
            marcar(campo, "ok")

    # ── 6. NOCT ──────────────────────────────────────────────────────────────
    if noct is None:
        marcar("NOCT", "warn", "NOCT vacío — se usará 45 °C por defecto.")
    elif not (_NOCT_MIN <= noct <= _NOCT_MAX):
        marcar("NOCT", "warn",
               f"NOCT = {noct:g} °C fuera del rango típico [{_NOCT_MIN:g}, {_NOCT_MAX:g}].")
    else:
        marcar("NOCT", "ok")

    # ── 7. Eficiencia desde dimensiones ──────────────────────────────────────
    dims = _parse_dimensiones(campos.get("dimensiones"))
    if dims and pmax:
        area_m2 = dims[0] * dims[1] * 1e-6
        ef = pmax / (area_m2 * 1000.0) * 100.0
        if ef > _EF_MAX:
            # >25% es físicamente imposible en módulos comerciales de CUALQUIER
            # tecnología → Pmax o dimensiones están mal extraídos.
            marcar("dimensiones", "error",
                   f"Eficiencia implícita {ef:.1f}% (Pmax/área) — imposible (>"
                   f"{_EF_MAX:g}%). Pmax o dimensiones están mal.")
        elif ef < _EF_MIN:
            # Eficiencia baja es VÁLIDA en BIPV semitransparente/thin-film →
            # solo avisar, nunca bloquear.
            marcar("dimensiones", "warn",
                   f"Eficiencia implícita {ef:.1f}% (<{_EF_MIN:g}%) — normal solo en "
                   "BIPV semitransparente o película delgada; si es un panel "
                   "estándar, revisa Pmax y dimensiones.")
        else:
            marcar("dimensiones", "ok")
    elif not dims:
        marcar("dimensiones", "warn",
               "Dimensiones vacías — no se puede verificar la eficiencia ni "
               "calcular el área del panel.")

    # ── 8. Bifacialidad ──────────────────────────────────────────────────────
    if bif is None:
        marcar("Bifacialidad", "ok")          # 0 = monofacial, válido
    elif not (50.0 <= bif <= 100.0):
        marcar("Bifacialidad", "warn",
               f"Bifacialidad {bif:g}% fuera del rango típico [50, 100]%.")
    else:
        marcar("Bifacialidad", "ok")

    return {
        "campos": est,
        "errores": errores,
        "avisos": avisos,
        "ok": not errores,
    }


def icono_estado(estado: str) -> str:
    return {"ok": "🟢", "warn": "🟠", "error": "🔴"}.get(estado, "⚪")
