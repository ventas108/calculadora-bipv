"""
extractor_inversor_core.py
Núcleo de extracción de texto plano → parámetros de inversor.
Expone `extraer_desde_texto(texto)` para uso directo en tests y debug,
sin necesitar un PDF real.  pdf_inversor_extractor.py lo usa internamente.
"""
from calculos.pdf_inversor_extractor import (
    _find, _find_range,
    _PAT_VDCMAX, _LABEL_MPPT_RANGE, _LABEL_MPPT_ACTIVO,
    _PAT_VARRANQUE, _PAT_NTRACKERS, _PAT_NSTRINGS,
    _PAT_IMAX, _PAT_ISC, _PAT_PDCMAX,
    _LABEL_BAT_RANGE, _PAT_BAT_MIN, _PAT_BAT_MAX,
    _TRACKER_STR_RE, _HYBRID_RE, _RANGE_RE, _KW_NO_P_RE,
    _extract_brand, _extract_model, _extract_arch,
)
import re


def extraer_desde_texto(texto: str) -> dict:
    """
    Extrae parámetros de inversor desde texto plano (sin PDF).
    Útil para tests unitarios, debug de datasheets y harness de cobertura.
    """
    import re as _re

    def _num(s):
        if s is None: return None
        try: return float(str(s).replace(",", ".").strip())
        except: return None

    # Normalizar notación d.c./a.c. (SolaX X3-FORTH y similar)
    texto = _re.sub(r"\s*d\.c\.?\s*", " ", texto)
    texto = _re.sub(r"\s*a\.c\.?\s*", " ", texto)

    marca        = _extract_brand(texto)
    modelo       = _extract_model(texto, marca)
    arquitectura = _extract_arch(texto)
    es_hibrido   = bool(_HYBRID_RE.search(texto[:2000]))

    Vdc_max = _find(_PAT_VDCMAX, texto)

    Vmppt_min, Vmppt_max = _find_range(_LABEL_MPPT_RANGE, texto)
    if Vmppt_min is None:
        m = _RANGE_RE.search(texto)
        if m:
            lo, hi = _num(m.group(1)), _num(m.group(2))
            if lo and hi and lo < hi and hi > 100:
                Vmppt_min, Vmppt_max = lo, hi

    Vmppt_act_lo, _ = _find_range(_LABEL_MPPT_ACTIVO, texto, use_sma_fallback=False)
    V_mppt_activo   = Vmppt_act_lo
    V_arranque      = _find(_PAT_VARRANQUE, texto)
    if V_arranque is not None and V_arranque < 60:
        V_arranque = None

    n_trackers        = _find(_PAT_NTRACKERS, texto)
    n_strings_tracker = _find(_PAT_NSTRINGS, texto)
    m_ts = _TRACKER_STR_RE.search(texto)
    if m_ts:
        if n_trackers is None:
            n_trackers = _num(m_ts.group(1))
        if n_strings_tracker is None:
            n_strings_tracker = _num(m_ts.group(2))

    I_max_tracker   = _find(_PAT_IMAX, texto)
    Isc_max_tracker = _find(_PAT_ISC, texto)

    # P_dc_max_W — kWp (SolaX) y kW sin p (Sungrow/Huawei)
    p_kw_converted = None
    m_kwp = re.search(
        r"Max(?:imum)?\.?\s+PV\s+(?:array\s+)?(?:input\s+)?[Pp]ower"
        r"\s*\[?kWp?\]?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)(?:\s*kWp?)?",
        texto, re.IGNORECASE,
    )
    if m_kwp:
        v = _num(m_kwp.group(1))
        if v and v < 1000:
            p_kw_converted = v * 1000
    if p_kw_converted is None and _KW_NO_P_RE.search(texto):
        m_kw = re.search(
            r"(?:Max(?:imum)?\.?\s+(?:PV\s+)?(?:DC\s+)?(?:[Ii]nput\s+)?[Pp]ower"
            r"|Recommended\s+max(?:imum)?\s+PV\s+power)"
            r"[^\n]*\b([0-9]+(?:[.,][0-9]+)?)\s*kW(?!p)",
            texto, re.IGNORECASE,
        )
        if m_kw:
            v = _num(m_kw.group(1))
            if v and 0 < v < 10000:
                p_kw_converted = v * 1000
    # Intento 3: SolaX X3-FORTH — "Max. recommended PV array power" + kWp multi-línea
    if p_kw_converted is None:
        m_rec = _re.search(
            r"Max\.\s+recommended\s+PV\s+(?:array\s+)?[Pp]ower[^\n]*\n"
            r"(?:[^\n]*\n){1,3}\s*([0-9]+(?:[.,][0-9]+)?)\s*kWp?\b",
            texto, _re.IGNORECASE,
        )
        if m_rec:
            v = _num(m_rec.group(1))
            if v and v < 1000:
                p_kw_converted = v * 1000
    P_dc_max_W = p_kw_converted or _find(_PAT_PDCMAX, texto)

    # use_sma_fallback=False: "DC voltage range" SMA es MPPT, no batería
    bat_min_r, bat_max_r = _find_range(_LABEL_BAT_RANGE, texto, use_sma_fallback=False)
    bat_voltaje_min = bat_min_r or _find(_PAT_BAT_MIN, texto)
    bat_voltaje_max = bat_max_r or _find(_PAT_BAT_MAX, texto)

    return {
        "modelo": modelo, "marca": marca,
        "arquitectura": arquitectura, "es_hibrido": es_hibrido,
        "Vdc_max": Vdc_max, "Vmppt_min": Vmppt_min, "Vmppt_max": Vmppt_max,
        "V_mppt_activo": V_mppt_activo, "V_arranque": V_arranque,
        "n_trackers": n_trackers, "n_strings_tracker": n_strings_tracker,
        "I_max_tracker": I_max_tracker, "Isc_max_tracker": Isc_max_tracker,
        "P_dc_max_W": P_dc_max_W,
        "bat_voltaje_min": bat_voltaje_min, "bat_voltaje_max": bat_voltaje_max,
    }
