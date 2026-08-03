"""
Motor de extracción automática de fichas técnicas de inversores/cargadores BIPV.

Soporta: Growatt, Solis, Deye, MUST, SolaX, LuxPower, POWEST, Huawei, SMA,
         Fronius, GoodWe, Sofar, Sungrow, Victron, Solaredge, Delta, Chint,
         Ginlong, Kstar, Voltronic/Axpert, MPPSolar, Schneider y compatibles.

Campos extraídos (13 columnas del catálogo):
  Vdc_max, Vmppt_min, Vmppt_max, V_mppt_activo, V_arranque,
  n_trackers, n_strings_tracker, I_max_tracker, Isc_max_tracker,
  P_dc_max_W, es_hibrido, bat_voltaje_min, bat_voltaje_max

Referencia de alias: Mapa_de_Alias_Catalogo_Inversores (INNOVAQ/EINNOVA 2026).
"""

import re

# ── Disponibilidad de dependencias ────────────────────────────────────────────
try:
    import pdfplumber
    _HAS_PDF = True
except ImportError:
    _HAS_PDF = False

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    _HAS_OCR = True
except ImportError:
    _HAS_OCR = False


# ══════════════════════════════════════════════════════════════════════════════
# Marcas conocidas de inversores BIPV / fotovoltaicos
# ══════════════════════════════════════════════════════════════════════════════
_BRANDS = [
    "Growatt", "Solis", "Ginlong", "Deye", "MUST", "SolaX", "LuxPower",
    "POWEST", "Huawei", "SMA", "Fronius", "ABB", "Schneider", "GoodWe",
    "Sofar", "Sungrow", "Victron", "Outback", "Solaredge", "Enphase",
    "Delta", "Chint", "Kstar", "Voltronic", "Axpert", "MPPSolar",
    "Phocos", "Studer", "Steca", "SolarEdge", "Power Electronics",
    "Ingeteam", "Refu", "TMEIC", "Siemens", "ABB", "Omnik", "AEG",
    "Samil", "Zeversolar", "Enecsys", "Tabuchi", "Yaskawa",
    "Magnetek", "Advanced Energy", "Aros", "Danfoss", "Schneider",
    "Xantrex", "Outback", "Morningstar",
]

# Arquitecturas reconocidas (para campo tecnologia / tipo)
_ARCH_PATTERNS = [
    ("Híbrido / Off-grid",    r"(?:hybrid|h[íi]brido|HES|ESS|storage|all[- ]in[- ]one)",         re.IGNORECASE),
    ("Inversor de red trifásico", r"(?:3[- ]?phase|tri[- ]?f[aá]sico|3ph|3-ph|TL3|3P\b)",         re.IGNORECASE),
    ("Inversor de red monofásico", r"(?:1[- ]?phase|mono[- ]?f[aá]sico|1ph|1-ph|TL(?!3))",         re.IGNORECASE),
    ("Cargador off-grid puro", r"(?:off[- ]?grid|stand[- ]?alone|PV\s*charger|UPS|charge\s*controller)", re.IGNORECASE),
]


# ══════════════════════════════════════════════════════════════════════════════
# Patrones de extracción por campo
# Formato: lista de (patron, group_indices, transform)
#   group_indices: tupla de grupos a capturar; transform: función o None
# ══════════════════════════════════════════════════════════════════════════════

def _num(s):
    """Convierte string a float (acepta coma decimal)."""
    if s is None:
        return None
    s = str(s).replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _first(*vals):
    """Retorna el primer valor no-None de la lista."""
    for v in vals:
        if v is not None:
            return v
    return None


# ── Regex para rangos tipo "100 ~ 850 V" / "100-850 V" / "100 to 850 V"
#    Gap 1 (Fronius/SMA): añadido separador "..." / ".." (180...800 V)
# ─────────────────────────────────────────────────────────────────────────────
_RANGE_RE = re.compile(
    r"([0-9]+(?:[.,][0-9]+)?)\s*(?:\.{2,3}|~|–|—|-|to|a)\s*([0-9]+(?:[.,][0-9]+)?)\s*V",
    re.IGNORECASE,
)

# ── Regex para formato "2/(2:2)" (trackers / strings) ────────────────────────
# Gap 3 (LuxPower variantes): acepta también "2 x (2:2)" y "2x(2)" con 'x'
_TRACKER_STR_RE = re.compile(
    r"(\d+)\s*(?:/|x)\s*\(\s*(\d+)(?:\s*:\s*\d+)*\s*\)",
    re.IGNORECASE,
)


def _find(patterns, text):
    """Prueba lista de (regex, group) en el texto y retorna el primer float."""
    for pat, grp in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            try:
                return _num(m.group(grp))
            except (IndexError, AttributeError):
                pass
    return None


# ── Regex SMA "DC voltage range, min." / "DC voltage range, max." separados ──
# Gap 2: algunas fichas SMA/Fronius reportan mín y máx en campos distintos,
#         no como un rango "X ~ Y V" en una sola línea.
_SMA_MIN_RE = re.compile(
    r"DC\s+voltage\s+range,?\s*min\.?\s*[:\|]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",
    re.IGNORECASE,
)
_SMA_MAX_RE = re.compile(
    r"DC\s+voltage\s+range,?\s*max\.?\s*[:\|]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",
    re.IGNORECASE,
)
_UMIN_RE = re.compile(
    r"U_?(?:MPP|mpp|DC|dc),?\s*min\.?\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",
    re.IGNORECASE,
)
_UMAX_RE = re.compile(
    r"U_?(?:MPP|mpp|DC|dc),?\s*max\.?\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",
    re.IGNORECASE,
)


def _find_range(label_patterns, text):
    """
    Busca una etiqueta seguida de un rango "X ~ Y V" y devuelve (min, max).

    Gap 2 (SMA/Fronius): si no hay rango en una sola línea, intenta extraer
    min y max de campos separados usando _SMA_MIN_RE / _SMA_MAX_RE / _U*_RE.
    Gap 5: ventana ampliada de 200 → 400 chars para tablas multicolumna.
    Retorna (None, None) si no encuentra.
    """
    for lp in label_patterns:
        m_label = re.search(lp, text, re.IGNORECASE)
        if not m_label:
            continue
        # Gap 5: ventana 400 chars (antes 200)
        chunk = text[m_label.start(): m_label.start() + 400]
        m_range = _RANGE_RE.search(chunk)
        if m_range:
            lo = _num(m_range.group(1))
            hi = _num(m_range.group(2))
            if lo is not None and hi is not None:
                return (lo, hi) if lo < hi else (hi, lo)

    # Gap 2: fallback para fichas SMA/Fronius con min y max en líneas separadas
    lo_sep = hi_sep = None
    for pat in (_SMA_MIN_RE, _UMIN_RE):
        m = pat.search(text)
        if m:
            lo_sep = _num(m.group(1))
            break
    for pat in (_SMA_MAX_RE, _UMAX_RE):
        m = pat.search(text)
        if m:
            hi_sep = _num(m.group(1))
            break
    if lo_sep is not None and hi_sep is not None and lo_sep < hi_sep:
        return (lo_sep, hi_sep)

    return (None, None)


# ─────────────────────────────────────────────────────────────────────────────
# Vdc_max — Tensión DC Máxima (límite físico absoluto)
# ─────────────────────────────────────────────────────────────────────────────
_PAT_VDCMAX = [
    # Inglés directo
    (r"Max(?:imum)?\.?\s*(?:PV\s+)?(?:Input|Array|DC)\s+(?:Open\s+Circuit\s+)?[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V(?!\s*/)", 1),
    (r"Max(?:imum)?\s+PV\s+VOC\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"Max\.\s*DC\s+[Ii]nput\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"PV\s+input\s+voltage\s*\(max\.\?\)\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"PV\s+[Vv]oltage\s+[Rr]ange.*?~\s*([0-9]+(?:[.,][0-9]+)?)\s*V",             1),
    # Español
    (r"Tensi[oó]n\s+DC\s+M[aá]xima?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",      1),
    (r"Tensi[oó]n\s+M[aá]xima?\s+(?:FV|PV|Entrada)\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"Max\.\s*PV\s+array\s+open\s+circuit\s+voltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    # SMA / Fronius style
    (r"DC\s+voltage\s+range,\s*max\.\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",     1),
    (r"U_PV,max\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",                         1),
]

# ─────────────────────────────────────────────────────────────────────────────
# Vmppt_min, Vmppt_max — Rango MPPT (se extraen juntos desde el rango)
# ─────────────────────────────────────────────────────────────────────────────
_LABEL_MPPT_RANGE = [
    r"MPP(?:T)?\s+[Vv]oltage\s+[Rr]ange",
    r"MPPT\s+[Rr]ange",
    r"MPP\s+[Tt]racker\s+[Vv]oltage\s+[Rr]ange",
    r"MPPT\s+[Vv]oltage\s+[Oo]perat(?:ing|ion)",
    r"Rango\s+(?:de\s+)?[Oo]peraci[oó]n\s+PV\s+MPPT",
    r"Rango\s+MPPT",
    r"MPPT\s+Range\s+@\s+Operating",
    r"DC\s+[Vv]oltage\s+[Rr]ange",
    r"Input\s+[Vv]oltage\s+[Rr]ange",
    r"PV\s+[Vv]oltage\s+[Rr]ange",
    r"U_MPP\s+[Rr]ange",
    r"V_MPP\s+range",
]

# ─────────────────────────────────────────────────────────────────────────────
# V_mppt_activo — Tensión mínima con carga completa (Deye: Full Load DC Voltage Range)
# ─────────────────────────────────────────────────────────────────────────────
_LABEL_MPPT_ACTIVO = [
    r"Full\s+[Ll]oad\s+DC\s+[Vv]oltage\s+[Rr]ange",
    r"Full\s+[Ll]oad\s+[Vv]oltage\s+[Rr]ange",
    r"Rated\s+(?:DC\s+)?[Vv]oltage\s+[Rr]ange",
    r"Normal\s+(?:DC\s+)?[Oo]peration\s+[Vv]oltage",
    r"Tensi[oó]n\s+M[ií]nima\s+MPPT\s+[Aa]ctivo",
]

# ─────────────────────────────────────────────────────────────────────────────
# V_arranque — Tensión de arranque (PV, no batería)
# ─────────────────────────────────────────────────────────────────────────────
_PAT_VARRANQUE = [
    (r"Start[- ]?up\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",         1),
    (r"[Ss]tart(?:ing|up)?\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",  1),
    (r"[Mm]in(?:imum)?\s+[Ss]tart(?:ing)?\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"Tensi[oó]n\s+de\s+[Aa]rranque\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",     1),
    # SMA: Minimum input voltage (start)
    (r"Minimum\s+input\s+voltage\s*\(start\)\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"U_PV,start\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",                        1),
    # Growatt/SolaX: Startup Voltage
    (r"Startup\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",              1),
]

# ─────────────────────────────────────────────────────────────────────────────
# n_trackers — Número de trackers MPPT
# ─────────────────────────────────────────────────────────────────────────────
_PAT_NTRACKERS = [
    # "Number of MPP trackers" / "No. of MPP trackers"
    (r"N(?:o|umber|úmero)?\.?\s+(?:of\s+)?(?:independent\s+)?MPP(?:T)?\s+(?:trackers?|inputs?|channels?)\s*[:\|]?\s*([0-9]+)", 1),
    (r"MPPT\s+[Nn]umber\s*[:\|]?\s*([0-9]+)",                                      1),
    (r"#\s*(?:of\s+)?MPPT\s*[:\|]?\s*([0-9]+)",                                    1),
    (r"Trackers?\s+MPPT\s*[:\|]?\s*([0-9]+)",                                      1),
    (r"N[úu]mero\s+de\s+[Rr]astreadores?\s*[:\|]?\s*([0-9]+)",                     1),
    # formato "2/(2:2)" — primer número = total trackers
    (r"(\d+)\s*/\s*\(\s*\d+(?:\s*:\s*\d+)*\s*\)",                                  1),
    # Victron/SMA: nMPPT = 2
    (r"n(?:MPPT|_MPPT)\s*[=:\|]?\s*([0-9]+)",                                      1),
]

# ─────────────────────────────────────────────────────────────────────────────
# n_strings_tracker — Strings por tracker
# ─────────────────────────────────────────────────────────────────────────────
_PAT_NSTRINGS = [
    (r"[Ss]trings?\s+per\s+MPP(?:T)?\s+[Tt]racker\s*[:\|]?\s*([0-9]+)",           1),
    (r"[Ss]trings?\s+per\s+[Ii]nput\s*[:\|]?\s*([0-9]+)",                          1),
    (r"[Cc]adenas?\s+por\s+[Tt]racker\s*[:\|]?\s*([0-9]+)",                        1),
    # formato "2/(2:2)" → segundo número (strings por tracker uniforme)
    (r"\d+\s*/\s*\(\s*(\d+)(?:\s*:\s*\d+)*\s*\)",                                  1),
]

# ─────────────────────────────────────────────────────────────────────────────
# I_max_tracker — Corriente máxima de entrada por tracker
# ─────────────────────────────────────────────────────────────────────────────
_PAT_IMAX = [
    (r"Max(?:imum)?\.?\s+PV\s+[Ii]nput\s+[Cc]urrent\s+(?:per\s+MPPT|per\s+[Tt]racker)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Max(?:imum)?\s+[Ii]nput\s+[Cc]urrent\s*(?:\(per\s+MPPT\))?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Maximum\s+PV\s+[Cc]harge\s+[Cc]urrent\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Max\.\s*DC\s+[Ii]nput\s+[Cc]urrent\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"I_?max(?:_?DC|_?pv)?\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A",             1),
    (r"Corriente\s+M[aá]xima\s+(?:por\s+)?[Tt]racker\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Max\.\s*input\s+current\s+\[A\]\s*[:\|]?\s*([0-9]+(?:[.,][0-9]+)?)",       1),
]

# ─────────────────────────────────────────────────────────────────────────────
# Isc_max_tracker — Corriente de cortocircuito máxima por tracker
# ─────────────────────────────────────────────────────────────────────────────
_PAT_ISC = [
    (r"Max(?:imum)?\.?\s+(?:PV\s+)?[Ss]hort[- ]?[Cc]ircuit\s+[Cc]urrent\s*(?:per\s+MPPT|input)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Max(?:imum)?\s+PV\s+ISC\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A",           1),
    (r"Max\.\s+ISC\s+per\s+MPPT\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A",          1),
    (r"I_?sc_?max\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A",                        1),
    (r"Corriente\s+de?\s+[Cc]ortocircuito\s+M[aá]xima?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Max\.\s*short\s+circuit\s+current\s*\[A\]\s*[:\|]?\s*([0-9]+(?:[.,][0-9]+)?)", 1),
]

# ─────────────────────────────────────────────────────────────────────────────
# P_dc_max_W — Potencia FV máxima recomendada (W)
# ─────────────────────────────────────────────────────────────────────────────
_PAT_PDCMAX = [
    # kWp (SolaX con corchetes) — multiplicar ×1000 en la lógica de extracción
    (r"Max(?:imum)?\.?\s+PV\s+(?:array\s+)?(?:input\s+)?[Pp]ower\s*\[?kWp?\]?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kWp?", 1),
    # Gap 4: kW sin 'p' (Sungrow, Huawei) — también ×1000 en lógica
    (r"Max(?:imum)?\.?\s+(?:PV\s+)?(?:DC\s+)?(?:[Ii]nput\s+)?[Pp]ower\s*\[?kW\]?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kW(?!p)", 1),
    (r"Recommended\s+max(?:imum)?\s+PV\s+power\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kW(?!p)", 1),
    # Watts directo
    (r"Max(?:imum)?\.?\s+PV\s+[Aa]rray\s+[Pp]ower\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W",   1),
    (r"Max(?:imum)?\s+DC\s+[Ii]nput\s+[Pp]ower\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W",       1),
    (r"Max\.\s+PV\s+array\s+input\s+power\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W",             1),
    (r"Max\s+PV\s+power\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W",                               1),
    (r"Potencia\s+FV\s+M[aá]xima?\s+(?:[Rr]ecomendada?)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W", 1),
    (r"PV\s+array\s+max(?:imum)?\s+power\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W", 1),
    # SMA
    (r"DC\s+power,\s*max\.\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W",               1),
]

# Regex independiente para detectar kW sin p (para conversión ×1000 en extracción)
_KW_NO_P_RE = re.compile(
    r"Max(?:imum)?\.?\s+(?:PV\s+)?(?:DC\s+)?(?:[Ii]nput\s+)?[Pp]ower\s*\[?kW\]?\s*[:\(]?\s*[0-9]+(?:[.,][0-9]+)?\s*kW(?!p)",
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────────────────────
# Batería — voltaje mín/máx
# ─────────────────────────────────────────────────────────────────────────────
_LABEL_BAT_RANGE = [
    r"[Bb]attery\s+[Vv]oltage\s+[Rr]ange",
    r"[Bb]at(?:tery|\.)\s+[Vv]oltage\s+[Rr]ange",
    r"Rango\s+de\s+[Vv]oltaje\s+(?:de\s+)?[Bb]ater[íi]a",
    r"[Bb]attery\s+[Oo]perat(?:ing|ion)\s+[Vv]oltage",
]
_PAT_BAT_MIN = [
    (r"[Bb]attery\s+[Vv]oltage\s*\(?\s*[Mm]in\.?\s*\)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"[Mm]in(?:imum)?\s+[Bb]attery\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",       1),
]
_PAT_BAT_MAX = [
    (r"[Bb]attery\s+[Vv]oltage\s*\(?\s*[Mm]ax\.?\s*\)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"[Mm]ax(?:imum)?\s+[Bb]attery\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",       1),
]

# ── Detección de inversor híbrido ─────────────────────────────────────────────
_HYBRID_RE = re.compile(
    r"(?:hybrid|h[íi]brido|HES\b|ESS\b|all[- ]in[- ]one|storage|bateria|battery)",
    re.IGNORECASE,
)


# ══════════════════════════════════════════════════════════════════════════════
# Extracción de texto del PDF
# ══════════════════════════════════════════════════════════════════════════════

def _extract_text_pdfplumber(pdf_bytes: bytes) -> tuple[str, bool]:
    """Extrae texto de las primeras 4 páginas. Retorna (texto, es_escaneado)."""
    text_parts = []
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages[:4]:
            t = page.extract_text() or ""
            text_parts.append(t)
            # Intentar extraer tablas
            for table in page.extract_tables():
                for row in table:
                    if row:
                        text_parts.append("  ".join(str(c or "") for c in row))
    full = "\n".join(text_parts)
    es_escaneado = len(full.strip()) < 120
    return full, es_escaneado


def _ocr_pdf(pdf_bytes: bytes) -> str:
    """OCR fallback para PDFs escaneados (requiere pdf2image + tesseract)."""
    if not _HAS_OCR:
        return ""
    import io
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=200, first_page=1, last_page=3)
        parts = []
        for img in pages:
            for lang in ("spa+eng", "eng", None):
                try:
                    kw = {"lang": lang} if lang else {}
                    t = pytesseract.image_to_string(img, **kw)
                    if t:
                        parts.append(t)
                        break
                except Exception:
                    pass
        return "\n".join(parts)
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# Detección de marca / modelo / tecnología
# ══════════════════════════════════════════════════════════════════════════════

def _extract_brand(text: str) -> str:
    lines = text.split("\n")[:25]
    for brand in _BRANDS:
        for line in lines:
            if re.search(r"\b" + re.escape(brand) + r"\b", line, re.IGNORECASE):
                return brand
    # Segunda pasada en todo el texto
    for brand in _BRANDS:
        if re.search(r"\b" + re.escape(brand) + r"\b", text, re.IGNORECASE):
            return brand
    return ""


def _extract_model(text: str, brand: str) -> str:
    lines = text.split("\n")[:40]
    # Patrón 1: línea completa que parece un modelo (alfanumérica con guiones)
    for line in lines[:15]:
        line = line.strip()
        if re.fullmatch(r"[A-Z0-9][A-Z0-9\-\._ ]{3,35}", line):
            if len(line) >= 5 and not line.lower() in ("datasheet", "technical", "specifications"):
                return line
    # Patrón 2: buscar código de modelo típico
    m = re.search(r"\b([A-Z]{2,8}[-_][A-Z0-9\-\.]{3,25})\b", text[:1500])
    if m:
        return m.group(1)
    return ""


def _extract_arch(text: str) -> str:
    for arch, pat, flags in _ARCH_PATTERNS:
        if re.search(pat, text, flags):
            return arch
    return "Inversor de red"


# ══════════════════════════════════════════════════════════════════════════════
# Función principal de extracción
# ══════════════════════════════════════════════════════════════════════════════

def extraer_parametros_inversor(pdf_bytes: bytes) -> dict:
    """
    Extrae los parámetros eléctricos de una ficha técnica de inversor BIPV.

    Retorna dict con campos:
        modelo, marca, arquitectura, es_hibrido,
        Vdc_max, Vmppt_min, Vmppt_max, V_mppt_activo, V_arranque,
        n_trackers, n_strings_tracker, I_max_tracker, Isc_max_tracker,
        P_dc_max_W, bat_voltaje_min, bat_voltaje_max,
        es_escaneado, uso_ocr, ocr_disponible, texto_crudo, error (opcional)
    """
    if not _HAS_PDF:
        return {"error": "pdfplumber no instalado. Ejecuta: pip install pdfplumber"}

    import io
    pdf_io = io.BytesIO(pdf_bytes)

    # ── Extracción de texto ───────────────────────────────────────────────────
    try:
        texto, es_escaneado = _extract_text_pdfplumber(pdf_io)
    except Exception as e:
        return {"error": f"Error leyendo el PDF: {e}"}

    uso_ocr = False
    if es_escaneado:
        ocr_text = _ocr_pdf(pdf_bytes)
        if len(ocr_text.strip()) >= 120:
            texto = ocr_text
            uso_ocr = True

    # ── Metadatos ─────────────────────────────────────────────────────────────
    marca       = _extract_brand(texto)
    modelo      = _extract_model(texto, marca)
    arquitectura = _extract_arch(texto)
    es_hibrido  = bool(_HYBRID_RE.search(texto[:2000]))

    # ── Vdc_max ───────────────────────────────────────────────────────────────
    Vdc_max = _find(_PAT_VDCMAX, texto)

    # ── Rango MPPT (Vmppt_min, Vmppt_max) ────────────────────────────────────
    Vmppt_min, Vmppt_max = _find_range(_LABEL_MPPT_RANGE, texto)

    # Fallback: extraer rango del texto completo si no se encontró por etiqueta
    if Vmppt_min is None:
        m = _RANGE_RE.search(texto)
        if m:
            lo, hi = _num(m.group(1)), _num(m.group(2))
            if lo and hi and lo < hi and hi > 100:
                Vmppt_min, Vmppt_max = (lo, hi)

    # ── V_mppt_activo ─────────────────────────────────────────────────────────
    Vmppt_act_lo, Vmppt_act_hi = _find_range(_LABEL_MPPT_ACTIVO, texto)
    V_mppt_activo = Vmppt_act_lo  # interés: límite inferior con carga completa

    # ── V_arranque ────────────────────────────────────────────────────────────
    V_arranque = _find(_PAT_VARRANQUE, texto)

    # ── n_trackers ────────────────────────────────────────────────────────────
    n_trackers = _find(_PAT_NTRACKERS, texto)
    n_strings_tracker = _find(_PAT_NSTRINGS, texto)

    # Verificar formato "2/(2:2)" para ambos campos a la vez
    m_ts = _TRACKER_STR_RE.search(texto)
    if m_ts:
        if n_trackers is None:
            n_trackers = _num(m_ts.group(1))
        if n_strings_tracker is None:
            n_strings_tracker = _num(m_ts.group(2))

    # ── I_max_tracker ─────────────────────────────────────────────────────────
    I_max_tracker = _find(_PAT_IMAX, texto)

    # ── Isc_max_tracker ───────────────────────────────────────────────────────
    Isc_max_tracker = _find(_PAT_ISC, texto)

    # ── P_dc_max_W ────────────────────────────────────────────────────────────
    # Intento 1: kWp explícito (SolaX) — multiplicar ×1000
    p_kw_converted = None
    m_kwp = re.search(
        r"Max(?:imum)?\.?\s+PV\s+(?:array\s+)?(?:input\s+)?[Pp]ower\s*\[?kWp?\]?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kWp?",
        texto, re.IGNORECASE,
    )
    if m_kwp:
        v = _num(m_kwp.group(1))
        if v and v < 1000:           # sanity: viene en kWp no en W
            p_kw_converted = v * 1000

    # Intento 2: Gap 4 — kW sin 'p' (Sungrow, Huawei) — también ×1000
    if p_kw_converted is None and _KW_NO_P_RE.search(texto):
        m_kw = re.search(
            r"(?:Max(?:imum)?\.?\s+(?:PV\s+)?(?:DC\s+)?(?:[Ii]nput\s+)?[Pp]ower"
            r"|Recommended\s+max(?:imum)?\s+PV\s+power)"
            r"\s*\[?kW\]?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kW(?!p)",
            texto, re.IGNORECASE,
        )
        if m_kw:
            v = _num(m_kw.group(1))
            if v and v < 10000:      # sanity: valor razonable en kW
                p_kw_converted = v * 1000

    P_dc_max_W = p_kw_converted or _find(_PAT_PDCMAX, texto)

    # ── Batería ───────────────────────────────────────────────────────────────
    bat_min_r, bat_max_r = _find_range(_LABEL_BAT_RANGE, texto)
    bat_voltaje_min = _first(bat_min_r, _find(_PAT_BAT_MIN, texto))
    bat_voltaje_max = _first(bat_max_r, _find(_PAT_BAT_MAX, texto))

    # ── Sanity checks ─────────────────────────────────────────────────────────
    # Vdc_max: típico 50–1500 V
    if Vdc_max is not None and not (50 <= Vdc_max <= 1500):
        Vdc_max = None
    # Vmppt: min debe ser menor que max; ambos entre 10–1500 V
    if Vmppt_min is not None and Vmppt_max is not None:
        if not (10 <= Vmppt_min < Vmppt_max <= 1500):
            Vmppt_min = Vmppt_max = None
    # n_trackers: entre 1 y 12
    if n_trackers is not None and not (1 <= n_trackers <= 12):
        n_trackers = None
    # n_strings_tracker: entre 1 y 6
    if n_strings_tracker is not None and not (1 <= n_strings_tracker <= 6):
        n_strings_tracker = None
    # Corrientes: entre 1 y 200 A
    for campo in [I_max_tracker, Isc_max_tracker]:
        pass  # validación inline abajo
    if I_max_tracker is not None and not (1 <= I_max_tracker <= 200):
        I_max_tracker = None
    if Isc_max_tracker is not None and not (1 <= Isc_max_tracker <= 200):
        Isc_max_tracker = None
    # P_dc_max_W: entre 100 W y 10 MW
    if P_dc_max_W is not None and not (100 <= P_dc_max_W <= 10_000_000):
        P_dc_max_W = None
    # Baterías: entre 10 y 1200 V
    if bat_voltaje_min is not None and not (10 <= bat_voltaje_min <= 1200):
        bat_voltaje_min = None
    if bat_voltaje_max is not None and not (10 <= bat_voltaje_max <= 1200):
        bat_voltaje_max = None

    return {
        "modelo":           modelo,
        "marca":            marca,
        "arquitectura":     arquitectura,
        "es_hibrido":       es_hibrido,
        "Vdc_max":          Vdc_max,
        "Vmppt_min":        Vmppt_min,
        "Vmppt_max":        Vmppt_max,
        "V_mppt_activo":    V_mppt_activo,
        "V_arranque":       V_arranque,
        "n_trackers":       n_trackers,
        "n_strings_tracker": n_strings_tracker,
        "I_max_tracker":    I_max_tracker,
        "Isc_max_tracker":  Isc_max_tracker,
        "P_dc_max_W":       P_dc_max_W,
        "bat_voltaje_min":  bat_voltaje_min,
        "bat_voltaje_max":  bat_voltaje_max,
        "es_escaneado":     es_escaneado,
        "uso_ocr":          uso_ocr,
        "ocr_disponible":   _HAS_OCR,
        "texto_crudo":      texto[:4000],
    }


def pdf_disponible() -> bool:
    return _HAS_PDF


def ocr_disponible() -> bool:
    return _HAS_OCR
