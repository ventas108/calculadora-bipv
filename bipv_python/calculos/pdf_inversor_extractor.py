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
# Aliases sin word-boundary (marcas compuestas como "solaxpower")
_BRAND_ALIASES: dict = {
    "solaxpower": "SolaX",
    "voltronicpower": "Voltronic",
    "infinisolar": "Voltronic",
    "ginlong":    "Solis",
    "sma-regul":  "SMA",
}

_BRANDS = [
    "Growatt", "Solis", "Ginlong", "Deye", "MUST", "SolaX", "LuxPower", "Felicity",
    "POWEST", "Huawei", "SMA", "Fronius", "ABB", "Schneider", "GoodWe", "SAJ",
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
    # Gap 6 (SolaX X3-PRO, Growatt): acepta "200V ~ 1000V" donde la V del mínimo
    # precede al separador.  La V final también es opcional ("160 ~ 800" sin unidad).
    # Voltronic: "350 VDC ~ 850 VDC" — unidad VDC completa a ambos lados
    r"([0-9]+(?:[.,][0-9]+)?)\s*(?:[Vv](?:DC|dc)?)?\s*(?:\.{2,3}|~|–|—|-|to|a)\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:V(?:DC|dc)?)?",
    re.IGNORECASE,
)

# ── Regex para formato "2/(2:2)" (trackers / strings) ────────────────────────
# Gap 3 (LuxPower variantes): acepta también "2 x (2:2)" y "2x(2)" con 'x'
_TRACKER_STR_RE = re.compile(
    r"(\d+)\s*(?:/|x)\s*\(\s*(\d+)(?:\s*:\s*\d+)*\s*\)",
    re.IGNORECASE,
)

# Fila combinada con etiqueta doble: "No. of MPP trackers / strings per MPP
# tracker 3 / 2" (también con la etiqueta partida en dos líneas, Growatt MID:
# "No. of MPP trackers/strings per\nMPP tracker 2/2 ...").
# Grupo 1 = trackers, grupo 2 = strings por tracker.
_TRACKER_STR_LABEL_RE = re.compile(
    r"No\.?\s*of\s+MPP\s+trackers?\s*/\s*strings?\s+per"
    r"(?:\s*\n?\s*MPP\s+trackers?)?\s*[:\|]?\s*(\d+)\s*/\s*(\d+)",
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


def _find_range(label_patterns, text, use_sma_fallback=True):
    """
    Busca una etiqueta seguida de un rango "X ~ Y V" y devuelve (min, max).

    Gap 2 (SMA/Fronius): si no hay rango en una sola línea, intenta extraer
    min y max de campos separados usando _SMA_MIN_RE / _SMA_MAX_RE / _U*_RE.
    NOTA: use_sma_fallback=False al buscar rangos de batería, para evitar
    que "DC voltage range, min./max." (SMA MPPT) sea confundido con batería.
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
                if lo == hi:
                    # Pseudo-rango (ej: "27A 27A" en tablas multicolumna, donde
                    # la 'A' de amperios matchea el separador 'a') — probar
                    # con la siguiente etiqueta
                    continue
                if max(lo, hi) > 2000:
                    # Sanidad: ningún rango de tensión FV/batería supera 2000 V —
                    # descartar pares numéricos no eléctricos en tablas densas
                    continue
                return (lo, hi) if lo < hi else (hi, lo)

    if not use_sma_fallback:
        return (None, None)

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
    # SAJ español con unidad entre corchetes: "Tensión máxima de entrada [V] 1100"
    (r"Tensi[oó]n\s+m[aá]xima\s+de\s+entrada\s*\[\s*V\s*\]\s*([0-9]{3,4})\b", 1),
    # Voltronic/InfiniSolar (etiquetas dobles con '/'): el segundo valor es el máximo
    # "Nominal DC Voltage / Maximum DC Voltage 720 VDC / 900 VDC"
    (r"Nominal\s+DC\s+Voltage\s*/\s*Max(?:imum)?\.?\s+DC\s+Voltage\s+[0-9.]+\s*V(?:DC)?\s*/\s*([0-9.]+)\s*V(?:DC)?", 1),
    # Tabla de 2 columnas (label y valor en líneas distintas): "Max. DC voltage\n1100 V"
    # Requiere 3-4 dígitos seguidos de V para no capturar otros números
    (r"Max(?:imum)?\.?\s+(?:PV\s+|DC\s+)(?:input\s+)?voltage\s*\n\s*([0-9]{3,4})\s*V\b", 1),
    # Patrón primario: acepta cualquier separador sin dígito ni newline (≤15 chars) entre
    # el label y el valor. Cubre:
    #   · "Max. PV input voltage: 1100 V"          (separador ": ")
    #   · "Max. PV input voltage (V): 600"          (LuxPower)
    #   · "Max. PV input voltage [V]: 800"          (X3-PRO)
    #   · "Max. PV input voltage  V  1100"          (X3-FORTH pdfplumber 3-columnas)
    #   · "Max. PV input voltage ① 1100 V"          (X3-FORTH pdfplumber, misma línea)
    # NO cruza salto de línea ([^\d\n]), por lo que falla limpiamente cuando el valor
    # está en la línea siguiente (pdftotext -layout) → cae al patrón multilinea.
    (r"Max(?:imum)?\.?\s*(?:PV\s+)?(?:Input|Array|DC)\s+(?:Open\s+Circuit\s+)?[Vv]oltage[^\d\n]{0,15}([0-9]+(?:[.,][0-9]+)?)\s*V?(?!\s*/)", 1),
    # Gap 7 (X3-PRO) mantenido como seguridad — ya cubierto arriba
    (r"Max(?:imum)?\.?\s*(?:PV\s+)?[Ii]nput\s+[Vv]oltage\s*\[V\]\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)", 1),
    # Multilinea pdftotext -layout: label en línea N (con notas ①②③), valor en línea N+1
    # Ej: "Max. PV input voltage   ①\n                          1100 V"
    # IMPORTANTE: este patrón actúa como FALLBACK cuando el patrón primario falla.
    # Con pdfplumber el valor ya está en la misma línea que el label → el patrón
    # primario lo captura y NUNCA llega aquí; así se evita capturar "580 V@220 V"
    # (tensión nominal con red 220 V) que aparece en la línea inmediatamente siguiente.
    (r"Max(?:imum)?\.?\s+(?:DC\s+)?(?:PV\s+)?[Ii]nput\s+[Vv]oltage[^\n]*\n\s*([0-9]+(?:[.,][0-9]+)?)\s*[Vv]?", 1),
    (r"Max(?:imum)?\s+PV\s+VOC\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"Max\.\s*DC\s+[Ii]nput\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"PV\s+input\s+voltage\s*\(max\.?\)\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",  1),
    (r"PV\s+[Vv]oltage\s+[Rr]ange.*?~\s*([0-9]+(?:[.,][0-9]+)?)\s*V",             1),
    # Español
    (r"Tensi[oó]n\s+DC\s+M[aá]xima?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",      1),
    # Growatt español: "Máximo voltaje CD 1100V"
    (r"M[aá]ximo\s+[Vv]oltaje\s+(?:CD|DC|CC)\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    # Huawei español: "Tensión máxima de entrada 1 1100 V" (el '1' suelto es nota al pie)
    (r"Tensi[oó]n\s+m[aá]xima\s+de\s+entrada(?:\s+\d)?\s+([0-9]{3,4})\s*V",       1),
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
    # Español (Growatt): "Rango de voltaje de MPPT 180V-850VDC"
    r"Rango\s+de\s+[Vv]oltaje\s+de\s+MPPT",
    # SAJ español: "Rango de tensión MPPT [V] 180~1000"
    r"Rango\s+de\s+tensi[oó]n\s+MPPT",
    # Huawei español (pdfplumber pega palabras): "Tensiónde funcionamientoMPPT 2 200 V ~ 1000 V"
    r"Tensi[oó]n\s*de\s*funcionamiento\s*(?:de\s*)?MPPT",
    r"MPP(?:T)?\s+[Vv]oltage\s+[Rr]ange",
    r"MPPT\s+[Rr]ange",
    r"MPP\s+[Tt]racker\s+[Vv]oltage\s+[Rr]ange",
    r"MPPT\s+[Vv]oltage\s+[Oo]perat(?:ing|ion)",
    r"Rango\s+(?:de\s+)?[Oo]peraci[oó]n\s+PV\s+MPPT",
    r"Rango\s+MPPT",
    r"MPPT\s+Range\s+@\s+Operating",
    # Growatt MID: "Normal Voltage 200V-1000V" (rango operativo de entrada CC).
    # El lookahead excluye líneas de CA ("... VAC", "... AC") para no confundir
    # el rango de red con el rango MPPT
    r"Normal\s+Voltage(?![^\n]*V?A[Cc]\b)",
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
    # Español (Growatt): "Rango de potencia máxima 370-600V" = rango de voltaje
    # a potencia completa → el límite inferior es la tensión mínima MPPT activa
    r"Rango\s+de\s+potencia\s+m[aá]xima",
]

# ─────────────────────────────────────────────────────────────────────────────
# V_arranque — Tensión de arranque (PV, no batería)
# ─────────────────────────────────────────────────────────────────────────────
_PAT_VARRANQUE = [
    # SAJ español: "Tensión de arranque [V] 200"
    (r"Tensi[oó]n\s+de\s+arranque\s*\[\s*V\s*\]\s*([0-9]+(?:[.,][0-9]+)?)\b", 1),
    # Voltronic/InfiniSolar: "Start-up Voltage / Initial Feeding Voltage 320 VDC / 350 VDC"
    (r"Start[- ]?up\s+Voltage\s*/\s*Initial\s+Feeding\s+Voltage\s+([0-9.]+)\s*V",  1),
    # "(V): N" format (LuxPower, Deye): "Start-up Voltage (V): 140"
    # (?<![A-Za-z]) evita capturar "Auto Restart Voltage 120" como arranque PV
    (r"(?<![A-Za-z])Start[- ]?up\s+[Vv]oltage\s*(?:\([Vv]\))?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*[Vv]?", 1),
    (r"(?<![A-Za-z])[Ss]tart(?:ing|up)?\s+[Vv]oltage\s*(?:\([Vv]\))?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*[Vv]?", 1),
    (r"[Mm]in(?:imum)?\s+[Ss]tart(?:ing)?\s+[Vv]oltage\s*(?:\([Vv]\))?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*[Vv]?", 1),
    (r"Tensi[oó]n\s+de\s+[Aa]rranque\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",     1),
    # Español (Growatt): "Voltaje de arranque 195V"
    (r"Voltaje\s+de\s+[Aa]rranque\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",        1),
    # SMA: Minimum input voltage (start)
    (r"Minimum\s+input\s+voltage\s*\(start\)\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V", 1),
    (r"U_PV,start\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*V",                        1),
    # Growatt/SolaX: Startup Voltage
    (r"Startup\s+[Vv]oltage\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*[Vv]?",          1),
]

# ─────────────────────────────────────────────────────────────────────────────
# n_trackers — Número de trackers MPPT
# ─────────────────────────────────────────────────────────────────────────────
_PAT_NTRACKERS = [
    # SAJ español: "No. de MPPT 3 4" → primer valor (modelo base)
    (r"No\.?\s*de\s+MPPT\s+([0-9]{1,2})\b", 1),
    # Voltronic/InfiniSolar: "Number of MPP Trackers / Maximum Input Current 2 / 2 x 18.6A"
    (r"Number\s+of\s+MPP\s+Trackers?\s*/\s*Max(?:imum)?\.?\s+Input\s+Current\s+([0-9]+)\s*/", 1),
    # Tabla de especificaciones — máxima prioridad (spec table beats feature bullets)
    # "No. of MPP trackers / strings per MPP tracker   9 / 2"
    (r"N(?:o|umber|úmero)?\.?\s+(?:of\s+)?(?:independent\s+)?MPP(?:T)?\s+(?:trackers?|inputs?|channels?)\s*[:\|/]?\s*(?:strings?\s+per\s+MPP(?:T)?\s+tracker\s*)?[:\|]?\s*([0-9]+)", 1),
    # Gap 8 (Sungrow): "Number of MPPT: 3" sin sufijo "trackers"
    (r"[Nn]umber\s+of\s+MPPT\s*[:\|]?\s*([0-9]+)",                                 1),
    (r"MPPT\s+[Nn]umber\s*[:\|]?\s*([0-9]+)",                                      1),
    (r"#\s*(?:of\s+)?MPPT\s*[:\|]?\s*([0-9]+)",                                    1),
    (r"Trackers?\s+MPPT\s*[:\|]?\s*([0-9]+)",                                      1),
    (r"N[úu]mero\s+de\s+[Rr]astreadores?\s*[:\|]?\s*([0-9]+)",                     1),
    # Español (Growatt): "Número de MPPTs 8"
    (r"N[úu]mero\s+de\s+MPPTs?\s*[:\|]?\s*([0-9]+)",                               1),
    # Felicity: "No.of MPP Trackers 4" (sin espacio tras "No.")
    (r"No\.?\s*of\s+MPP\s+[Tt]rackers?\s*[:\|]?\s*([0-9]+)",                       1),
    # Huawei español: "Cantidad de MPPTs 6"
    (r"Cantidad\s+de\s+MPPTs?\s*[:\|]?\s*([0-9]+)",                                1),
    # formato "2/(2:2)" — primer número = total trackers
    (r"(\d+)\s*/\s*\(\s*\d+(?:\s*:\s*\d+)*\s*\)",                                  1),
    # Victron/SMA: nMPPT = 2
    (r"n(?:MPPT|_MPPT)\s*[=:\|]?\s*([0-9]+)",                                      1),
    # SolaX X3-FORTH feature bullet — solo como fallback (puede describir el máximo de la familia)
    # IMPORTANTE: viene al final para que la tabla de spec tenga prioridad
    (r"Max\.\s+([0-9]+)\s+MPPTs?",                                                  1),
]

# ─────────────────────────────────────────────────────────────────────────────
# n_strings_tracker — Strings por tracker
# ─────────────────────────────────────────────────────────────────────────────
_PAT_NSTRINGS = [
    # SolaX X3-FORTH features: "Max. 12 MPPTs, 2 strings per MPP tracker"
    # PRIMERO: captura N antes de "strings" cuando viene precedido de "MPPTs,"
    (r"MPPTs?\s*,\s*([0-9]+)\s+strings?\s+per\s+MPP",                              1),
    # Genérico bullet: "N strings per MPP tracker" — usa [ \t] para NO cruzar newlines
    (r"\b([0-9]+)[ \t]+strings?[ \t]+per[ \t]+MPP(?:[ \t]+tracker)?(?=\b|,|$|[ \t])", 1),
    # Tabla: "Strings per MPP tracker: N" o "Strings per MPP tracker [N]" — separador explícito
    (r"[Ss]trings?\s+per\s+MPP(?:T)?\s+[Tt]racker\s*[:\|\[]\s*([0-9]+)",          1),
    (r"[Ss]trings?\s+per\s+[Ii]nput\s*[:\|]?\s*([0-9]+)",                          1),
    (r"[Cc]adenas?\s+por\s+[Tt]racker\s*[:\|]?\s*([0-9]+)",                        1),
    # Español (Growatt): "Cadenas por MPPT 2"
    (r"[Cc]adenas?\s+por\s+MPPT\s*[:\|]?\s*([0-9]+)",                              1),
    # Felicity: "No.of Strings Per MPP Tracker 2"
    (r"No\.?\s*of\s+[Ss]trings\s+[Pp]er\s+MPP\s+[Tt]racker\s*[:\|]?\s*([0-9]+)",   1),
    # Huawei español: "Cantidad máxima de entradas por MPPT 2"
    (r"Cantidad\s+m[aá]xima\s+de\s+entradas\s+por\s+MPPT\s*[:\|]?\s*([0-9]+)",     1),
    # Tabla sin separador o de 2 columnas (label y valor en líneas distintas):
    # "Strings per MPP tracker 2" / "Strings per MPP tracker\n2".
    # Va al final (menor prioridad); 1 dígito y validación 1-6 posterior.
    # Guardas: la etiqueta no puede venir de una fila combinada
    # "No. of MPP trackers / strings per MPP tracker 3 / 2" (ahí el primer
    # número es el conteo de trackers) → se exige que NO haya "/" antes de la
    # etiqueta en la misma línea ni después del dígito capturado
    (r"(?<![/])(?<![/] )[Ss]trings?\s+per\s+MPP(?:T)?\s+[Tt]racker\s*\n?\s*([0-9])\b(?!\s*/)", 1),
    # formato "2/(2:2)" → segundo número (strings por tracker uniforme)
    (r"\d+\s*/\s*\(\s*(\d+)(?:\s*:\s*\d+)*\s*\)",                                  1),
]

# ─────────────────────────────────────────────────────────────────────────────
# I_max_tracker — Corriente máxima de entrada por tracker
# ─────────────────────────────────────────────────────────────────────────────
_PAT_IMAX = [
    # Deye/TriP2: "Max. PV input current per MPPT (A) 20 / 20 / 20" → por MPPT = 1er valor
    (r"Max\.?\s*PV\s+input\s+current\s+per\s+MPPT\s*\(\s*A\s*\)\s*([0-9]+(?:[.,][0-9]+)?)", 1),
    # Growatt MID: "Max.input current per MPP tracker 27A" (sin espacio tras "Max.")
    (r"Max\.?\s*input\s+current\s+per\s+MPP\s+tracker\s*[:\s]\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # SAJ español: "Corriente máxima de entrada [A] 32/32/32" → por MPPT = 1er valor
    (r"Corriente\s+m[aá]xima\s+de\s+entrada\s*\[\s*A\s*\]\s*([0-9]+(?:[.,][0-9]+)?)\s*/", 1),
    # Voltronic/InfiniSolar: "Number of MPP Trackers / Maximum Input Current 2 / 2 x 18.6A"
    # → corriente POR tracker es el valor tras la 'x'
    (r"Number\s+of\s+MPP\s+Trackers?\s*/\s*Max(?:imum)?\.?\s+Input\s+Current\s+[0-9]+\s*/\s*[0-9]+\s*x\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # "\s*" (no "\s+") antes del sufijo opcional para cubrir "current: 15A" sin espacio previo
    (r"Max(?:imum)?\.?\s+PV\s+[Ii]nput\s+[Cc]urrent\s*(?:per\s+MPPT|per\s+[Tt]racker)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # Gap 7 (SolaX X3-PRO): "Max. PV input current [A]: 32"
    (r"Max(?:imum)?\.?\s+PV\s+[Ii]nput\s+[Cc]urrent\s*\[A\]\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)", 1),
    (r"Max(?:imum)?\s+[Ii]nput\s+[Cc]urrent\s*(?:\(per\s+MPPT\))?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # SolaX X3-FORTH: "Max. input current per MPPT" (sin paréntesis)
    (r"Max(?:imum)?\.?\s+[Ii]nput\s+[Cc]urrent\s+per\s+MPPT\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # SolaX X3-FORTH features: "32A per MPP tracker"
    (r"([0-9]+(?:[.,][0-9]+)?)\s*A\s+per\s+MPP(?:\s+tracker)?",                    1),
    (r"Maximum\s+PV\s+[Cc]harge\s+[Cc]urrent\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Max\.\s*DC\s+[Ii]nput\s+[Cc]urrent\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"I_?max(?:_?DC|_?pv)?\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A",             1),
    (r"Corriente\s+M[aá]xima\s+(?:por\s+)?[Tt]racker\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # Español (Growatt): "Máxima corriente por MPPT 40A"
    (r"M[aá]xima\s+corriente\s+(?:de\s+entrada\s+)?por\s+MPPT\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # Huawei español: "Corriente de entrada máxima por MPPT 22 A"
    (r"Corriente\s+de\s+entrada\s+m[aá]xima\s+(?:por\s+MPPT)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # Felicity: "PV Input Current 36+36+36+36(A)" — corriente POR tracker (primer sumando)
    (r"PV\s+Input\s+Current\s+([0-9]+(?:[.,][0-9]+)?)\s*\+",                       1),
    (r"Max\.\s*input\s+current\s+\[A\]\s*[:\|]?\s*([0-9]+(?:[.,][0-9]+)?)",       1),
]

# ─────────────────────────────────────────────────────────────────────────────
# Isc_max_tracker — Corriente de cortocircuito máxima por tracker
# ─────────────────────────────────────────────────────────────────────────────
_PAT_ISC = [
    # Deye/TriP2: "Max. PV short-circuit current input per MPPT 25 / 25 / 25" (sin unidad A)
    (r"short[- ]?circuit\s+current\s+input\s+per\s+MPPT\s*(?:\(\s*A\s*\))?\s*([0-9]+(?:[.,][0-9]+)?)\s*/", 1),
    # Growatt MID (etiqueta partida en dos líneas): "Max. short-circuit current per\nMPP tracker 33.8A"
    (r"(?m)short[- ]?circuit\s+current\s+per\s*\n\s*MPP\s+tracker\s+([0-9]+(?:[.,][0-9]+)?)\s*A\b", 1),
    # SAJ español: "Corriente máxima de cortocircuito CC [A] 38.4/38.4/38.4" → por MPPT
    (r"Corriente\s+m[aá]xima\s+de\s+cortocircuito\s+CC\s*\[\s*A\s*\]\s*([0-9]+(?:[.,][0-9]+)?)", 1),
    # Genérico: cubre "short circuit current per MPPT", "short-circuit current input per MPPT"
    (r"Max(?:imum)?\.?\s+(?:PV\s+)?[Ss]hort[- ]?[Cc]ircuit\s+[Cc]urrent\s*(?:input\s+)?(?:per\s+MPPT|per\s+[Tt]racker)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # SolaX X3-FORTH: "Max. input short circuit current per MPPT" (con "input" antes de "short")
    (r"Max(?:imum)?\.?\s+[Ii]nput\s+[Ss]hort[- ]?[Cc]ircuit\s+[Cc]urrent\s+per\s+MPPT\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Max(?:imum)?\s+PV\s+ISC\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A",           1),
    (r"Max\.\s+ISC\s+per\s+MPPT\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A",          1),
    (r"I_?sc_?max\s*[:\(=]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A",                        1),
    (r"Corriente\s+de?\s+[Cc]ortocircuito\s+M[aá]xima?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    (r"Max\.\s*short\s+circuit\s+current\s*\[A\]\s*[:\|]?\s*([0-9]+(?:[.,][0-9]+)?)", 1),
    # Español (Growatt): "Corriente de corto circuito por MPPT 50A"
    (r"Corriente\s+de\s+corto\s*circuito\s+por\s+MPPT\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*A", 1),
    # Felicity: "Max. PV Isc 55+55+55+55(A)" — Isc POR tracker (primer sumando)
    (r"Max\.?\s*PV\s*Isc\s*([0-9]+(?:[.,][0-9]+)?)\s*\+",                          1),
]

# ─────────────────────────────────────────────────────────────────────────────
# P_dc_max_W — Potencia FV máxima recomendada (W)
# ─────────────────────────────────────────────────────────────────────────────
_PAT_PDCMAX = [
    # SAJ español: "Potencia máxima FV [Wp]@STC 30000 37500 45000" → 1er valor
    (r"Potencia\s+m[aá]xima\s+FV\s*\[\s*Wp?\s*\]\s*(?:@\s*STC)?\s*([0-9]{4,6})\b", 1),
    # Voltronic/InfiniSolar: "Maximum PV Input Power 14850W"
    (r"Max(?:imum)?\.?\s+PV\s+Input\s+Power\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W\b", 1),
    # kWp (SolaX con corchetes): "power [kWp]: 36" o "power: 36 kWp"
    # NOTA: la unidad final es opcional porque puede haber sido consumida en [kWp]
    (r"Max(?:imum)?\.?\s+PV\s+(?:array\s+)?(?:input\s+)?[Pp]ower\s*\[?kWp?\]?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)(?:\s*kWp?)?", 1),
    # Gap 4: kW sin 'p' (Sungrow, Huawei) — también ×1000 en lógica
    (r"Max(?:imum)?\.?\s+(?:PV\s+)?(?:DC\s+)?(?:[Ii]nput\s+)?[Pp]ower\s*\[?kW\]?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kW(?!p)", 1),
    (r"Recommended\s+max(?:imum)?\s+PV\s+power\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kW(?!p)", 1),
    # SolaX X3-FORTH tabla 3 columnas: "Max. recommended PV array power  kWp  150"
    # pdfplumber une [Parámetro | Unidad | Valor] → "kWp" queda entre label y número
    (r"Max(?:imum)?\.?\s+recommended\s+PV\s+(?:array\s+)?[Pp]ower\s+kWp?\s+([0-9]+(?:[.,][0-9]+)?)", 1),
    # SolaX X3-FORTH misma línea: "Max. recommended PV array power: 150 kWp"
    (r"Max(?:imum)?\.?\s+recommended\s+PV\s+(?:array\s+)?[Pp]ower\s*[:\|]?\s*([0-9]+(?:[.,][0-9]+)?)\s*kWp?", 1),
    # Watts directo — acepta "(W): N" (unit en paréntesis antes del valor)
    (r"Max(?:imum)?\.?\s+(?:DC\s+)?[Ii]nput\s+[Pp]ower\s*(?:\([A-Za-z]+\))?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)", 1),
    (r"Max(?:imum)?\.?\s+PV\s+[Aa]rray\s+[Pp]ower\s*(?:\([A-Za-z]+\))?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*[Ww]?", 1),
    (r"Max(?:imum)?\.?\s+PV\s+array\s+input\s+[Pp]ower\s*(?:\([A-Za-z]+\))?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*[Ww]?", 1),
    (r"Max\s+PV\s+power\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W",                               1),
    (r"Potencia\s+FV\s+M[aá]xima?\s+(?:[Rr]ecomendada?)?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W", 1),
    (r"PV\s+array\s+max(?:imum)?\s+power\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W", 1),
    # SMA
    (r"DC\s+power,\s*max\.\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)\s*W",               1),
]

# Regex independiente para detectar kW sin p (para conversión ×1000 en extracción)
_KW_NO_P_RE = re.compile(
    # Gap 8 (Sungrow): cubre "label [kW]: 30" Y "label: 30 kW" (hasta fin de línea)
    r"(?:Max(?:imum)?\.?\s+(?:PV\s+)?(?:DC\s+)?(?:[Ii]nput\s+)?[Pp]ower"
    r"|Recommended\s+max(?:imum)?\s+PV\s+power)"
    r"[^\n]*\b[0-9]+(?:[.,][0-9]+)?\s*kW(?!p)",
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

def _extract_text_pdfplumber(pdf_bytes: bytes) -> tuple[str, bool, int]:
    """
    Extrae texto de hasta 8 páginas del PDF. Retorna (texto, es_escaneado, n_pages_total).

    Estrategia adaptativa:
      - Lee hasta 8 páginas (cubre datasheets multi-producto como SolaX X3-FORTH
        donde las especificaciones pueden estar en páginas 4-7).
      - Si las primeras 4 páginas dan texto suficiente (> 400 chars), deja de leer
        páginas adicionales que suelen ser solo marketing/imágenes.
    """
    text_parts = []
    with pdfplumber.open(pdf_bytes) as pdf:
        n_pages_total = len(pdf.pages)
        for i, page in enumerate(pdf.pages[:8]):
            t = page.extract_text() or ""
            text_parts.append(t)
            # Intentar extraer tablas (recupera datos en celdas no capturados por extract_text)
            # Usa las "tablas reparadas" del extractor de paneles: pdfplumber puede
            # devolver None en la última columna aunque el valor exista en el PDF
            # (falta el borde de la celda); la reparación recorta la página en el
            # bbox columna×fila y recupera el texto.
            try:
                try:
                    from calculos.pdf_panel_extractor import _extract_tables_reparadas
                    _tablas = _extract_tables_reparadas(page)
                except Exception:
                    _tablas = page.extract_tables()
                for table in _tablas:
                    for row in table:
                        if row:
                            text_parts.append("  ".join(str(c or "") for c in row))
            except Exception:
                pass
            # Heurística: si ya tenemos texto sustancial en las primeras 4 páginas
            # y la página actual está vacía, seguimos buscando (podrían ser páginas
            # de imágenes). Pero si tenemos más de 2000 chars y ya pasamos la 4a
            # página, podemos parar para no incorporar tablas de garantía / índices.
            current_len = len("\n".join(text_parts).strip())
            if i >= 4 and current_len > 2000:
                break
    full = "\n".join(text_parts)
    es_escaneado = len(full.strip()) < 120
    return full, es_escaneado, n_pages_total


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
    # Tercera pasada: aliases sin word-boundary (marcas compuestas: "solaxpower")
    text_lower = text.lower()
    for alias, brand in _BRAND_ALIASES.items():
        if alias in text_lower:
            return brand
    return ""


def _extract_model(text: str, brand: str) -> str:
    lines = text.split("\n")[:40]
    # Patrón 1: línea completa que parece un modelo (alfanumérica con guiones)
    for line in lines[:15]:
        line = line.strip()
        line = line.strip("_ ")   # OCR: "50KVA_" → "50KVA"
        if re.fullmatch(r"[A-Z0-9][A-Z0-9\-\._ ]{3,35}", line):
            if (len(line) >= 5
                    and line.lower() not in ("datasheet", "technical", "specifications")
                    and "SERIES" not in line.upper()  # "HYBRID SERIES" = título de gama, no modelo
                    and not re.match(r"^MPPT?\b|^MPPT?\d", line)  # "MPPT 1"/"MPPT1"/"MPPT 10 N" del diagrama unifilar
                    and not re.fullmatch(r"\d+\s*K?[VW]A?", line, re.IGNORECASE)):  # "50KVA" = potencia, no modelo
                return line
    # Patrón 2: buscar código de modelo típico
    m = re.search(r"\b([A-Z]{2,8}[-_][A-Z0-9\-\.]{3,25})\b", text[:1500])
    if m and m.group(1).upper() not in ("RS-232", "RS-485", "AS-400"):
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

# ══════════════════════════════════════════════════════════════════════════════
# Multi-modelo: detectar modelos como columnas y extraer valores por columna
# Usada cuando una ficha técnica cubre varios modelos (ej: SolaX X3-FORTH
# con 75K / 80K / 100K / 110K / 120K / 125K en columnas paralelas).
# ══════════════════════════════════════════════════════════════════════════════
_MODEL_COL_RE = re.compile(r'[A-Z][A-Z0-9\-\.]{3,25}', re.IGNORECASE)


def _extract_multimodel_values(text: str) -> dict:
    """
    Detecta datasheets con múltiples modelos como columnas y extrae valores
    por columna para los campos que varían por modelo.

    Algoritmo:
      1. Busca en las primeras 80 líneas una fila con ≥ 2 tokens que parezcan
         nombres de modelo (tienen dígitos y guiones, ej: X3-FTH-75K).
      2. Registra la posición horizontal (índice de carácter) de cada nombre.
      3. Para cada fila de datos (P_dc_max, n_trackers), extrae todos los
         valores numéricos y los asigna al modelo cuya posición sea más cercana.
      4. Propaga el valor asignado al modelo más cercano a los que quedan vacíos.

    Returns:
        {
            'modelos': ['X3-FTH-75K', ...],   # vacío si es hoja de un solo modelo
            'por_modelo': {
                'X3-FTH-75K': {'P_dc_max_W': 120000, 'n_trackers': 9.0, 'n_strings_tracker': 2.0},
                ...
            }
        }
    """
    _EMPTY: dict = {'modelos': [], 'por_modelo': {}}
    lines = text.split('\n')

    # ── 1. Detectar fila de encabezado con ≥ 2 nombres de modelo ───────────────
    header_positions: list[tuple[str, int]] = []
    header_line_idx = -1
    for li, line in enumerate(lines[:80]):
        candidates = [
            (m.group(), m.start())
            for m in _MODEL_COL_RE.finditer(line)
            # Con guion (X3-FTH-75K) o sin guion pero largo (IVGM50KHP3G2, ≥10):
            # el mínimo de 10 evita falsos positivos como IEC62116 / IEEE1547
            if re.search(r'\d', m.group())
               and re.search(r'[A-Za-z]', m.group())   # debe tener letras: no aceptar
               # tokens puramente numéricos/puntuación como "nombres de modelo"
               and ('-' in m.group() or len(m.group()) >= 10)
               and not re.match(r'^\d', m.group())          # no empieza con número
               # Artefacto de PDFs con texto duplicado carácter a carácter:
               # "MMAAXX5500" / "KKTTLL33--XXLL22" (cada char aparece 2 veces seguidas)
               and not re.fullmatch(r'(?:(.)\1)+', m.group())
        ]
        if len(candidates) >= 2:
            header_positions = candidates
            header_line_idx = li
            break

    if not header_positions:
        return _EMPTY

    model_names = [name for name, _ in header_positions]

    # Nombres repetidos con el sufijo de potencia en la MISMA línea
    # ("Model SNA2-EU-LT 10K SNA2-EU-LT 12K SNA2-EU-LT 14K"): el sufijo (10K)
    # empieza con dígito y queda fuera del match del nombre → completarlo con
    # los tokens numéricos entre cada nombre y el siguiente.
    # Nombres repetidos con el diferenciador como PREFIJO numérico pegado
    # ("Master 9R-280R Master 15R-280R" → el regex excluye tokens que empiezan
    # con dígito, dejando "R-280R" dos veces) → recuperar los dígitos previos.
    if len(set(model_names)) < len(model_names):
        hline = lines[header_line_idx]
        nuevos_pf, pos_pf = [], []
        for name, pos in header_positions:
            ini = pos
            while ini > 0 and hline[ini - 1].isdigit():
                ini -= 1
            nuevos_pf.append(hline[ini:pos] + name)
            pos_pf.append(ini)
        if len(set(nuevos_pf)) == len(nuevos_pf):
            model_names = nuevos_pf
            header_positions = list(zip(nuevos_pf, pos_pf))

    if len(set(model_names)) < len(model_names):
        hline = lines[header_line_idx]
        nuevos_sl = []
        for i, (name, pos) in enumerate(header_positions):
            fin = header_positions[i + 1][1] if i + 1 < len(header_positions) else len(hline)
            seg = hline[pos + len(name):fin]
            sufs = [t for t in re.findall(r'\S+', seg) if re.match(r'^\d[\w.,]*$', t)]
            nuevos_sl.append((name + ' ' + ' '.join(sufs)).strip() if sufs else name)
        if len(set(nuevos_sl)) == len(nuevos_sl):
            model_names = nuevos_sl
            header_positions = [(nuevos_sl[i], header_positions[i][1])
                                for i in range(len(nuevos_sl))]

    # Nombres partidos en dos líneas (Deye/TriP2): "Model TriP2-LB- TriP2-LB- ..."
    # + línea siguiente "3P 5K 3P 6K ..." — completar cada nombre con los tokens
    # de la línea de continuación asignados a la columna más cercana
    if len(set(model_names)) < len(model_names) and 0 <= header_line_idx + 1 < len(lines):
        cont = lines[header_line_idx + 1]
        cols_x = [pos for _, pos in header_positions]
        toks = re.findall(r"\S+", cont)
        n_m = len(model_names)
        sufijos: dict = {i: [] for i in range(n_m)}
        if toks and len(toks) % n_m == 0:
            # La línea de continuación no está alineada por columnas: repartir
            # los tokens en n grupos iguales en orden ("3P 5K 3P 6K ..." → 2 c/u)
            paso = len(toks) // n_m
            for i in range(n_m):
                sufijos[i] = toks[i * paso:(i + 1) * paso]
            # Validar forma: cada sufijo debe contener un dígito (variante de
            # potencia); si no, la línea no es continuación de modelos →
            # reintentar por posición de columna
            if not all(any(re.search(r"\d", t_) for t_ in sufijos[i]) for i in range(n_m)):
                sufijos = {i: [] for i in range(n_m)}
        if not any(sufijos.values()):
            for m_tok in re.finditer(r"\S+", cont):
                idx = min(range(n_m), key=lambda i: abs(cols_x[i] - m_tok.start()))
                sufijos[idx].append(m_tok.group())
        nuevos = [
            (model_names[i] + " ".join(sufijos[i])).strip() if sufijos[i] else model_names[i]
            for i in range(n_m)
        ]
        if len(set(nuevos)) == len(nuevos):
            model_names = nuevos
            header_positions = list(zip(model_names, cols_x))
    model_x     = [pos  for _,    pos in header_positions]
    n           = len(model_names)
    result: dict = {
        'modelos': model_names,
        'por_modelo': {
            m: {'P_dc_max_W': None, 'n_trackers': None, 'n_strings_tracker': None,
                'I_max_tracker': None, 'Isc_max_tracker': None}
            for m in model_names
        },
    }

    def _nearest_idx(val_x: int) -> int:
        """Índice del modelo con posición horizontal más cercana a val_x."""
        return min(range(n), key=lambda i: abs(model_x[i] - val_x))

    def _fill_gaps(by_idx: dict) -> dict:
        """
        Rellena índices sin valor copiando del vecino asignado a la DERECHA
        (si existe), si no del de la izquierda. En datasheets con celdas
        combinadas ("18000 | 24000" para 3 modelos) el valor combinado cubre
        los modelos superiores → el modelo intermedio agrupa con el mayor
        (verificado con coordenadas x del PDF SNA2-EU-LT 10-14K: 24000/35/44
        están centrados sobre las columnas 12K+14K).
        """
        assigned = sorted(by_idx.keys())
        if not assigned:
            return by_idx
        for i in range(n):
            if i not in by_idx:
                der = [j for j in assigned if j > i]
                izq = [j for j in assigned if j < i]
                by_idx[i] = by_idx[der[0]] if der else by_idx[izq[-1]]
        return by_idx

    # ── 2. P_dc_max por columna ─────────────────────────────────────────────────
    for line in lines:
        # Inglés (SolaX): "recommended PV array power"; Español (Growatt): la
        # etiqueta se parte en dos líneas y los valores quedan en "recomendada (STC) 100000W ..."
        if not re.search(r'recommended\s+PV\s+(?:array\s+)?power'
                         # Growatt MID: etiqueta partida — valores en línea "(for module STC) 22500W ..."
                         r'|for\s+module\s+STC'
                         r'|recomendada\s*\(STC\)'
                         r'|M[aá]xima\s+potencia\s+FV'
                         r'|Potencia\s+m[aá]xima\s+FV'
                         r'|Max\.?\s*PV\s+input\s+power'
                         r'|Max\.?\s*DC\s+Input\s+Power', line, re.IGNORECASE):
            continue
        # Enmascarar contenido entre paréntesis conservando posiciones:
        # "18000 (9000/9000) 24000 (12000/12000)" → los desgloses por MPPT
        # no deben confundirse con la potencia total del modelo
        line_m = re.sub(r'\([^)]*\)', lambda m_: ' ' * len(m_.group()), line)
        found = [
            (float(m.group(1).replace(',', '.')), m.start())
            for m in re.finditer(r'([0-9]+(?:[.,][0-9]+)?)\s*kWp?\b', line_m, re.IGNORECASE)
        ]
        if not found:
            # Valores directamente en W (Growatt: "100000W 120000W ...") → /1000 para
            # reutilizar la lógica kW→W de abajo
            found = [
                (float(m.group(1)) / 1000.0, m.start())
                for m in re.finditer(r'([0-9]{4,7})\s*W\b', line_m)
            ]
        if not found:
            # SAJ: valores sin unidad tras la etiqueta ("[Wp]@STC 30000 37500 45000")
            found = [
                (float(m.group(1)) / 1000.0, m.start())
                for m in re.finditer(r'\b([0-9]{4,7})\b', line_m)
            ]
        if not found:
            continue   # etiqueta partida en dos líneas (Growatt) — seguir buscando
        if len(found) == n:
            # Mapeo 1:1 por orden izquierda→derecha
            for (v, _), model in zip(found, model_names):
                if 0 < v < 10000:
                    result['por_modelo'][model]['P_dc_max_W'] = v * 1000
        elif found:
            # Menos valores que modelos (celdas combinadas): anclar primer
            # valor a la primera columna y último a la última; el resto por
            # posición. Los huecos heredan del vecino derecho (_fill_gaps).
            by_idx: dict = {}
            fs = sorted(found, key=lambda t: t[1])
            if 0 < fs[0][0] < 10000:
                by_idx[0] = fs[0][0] * 1000
            if 0 < fs[-1][0] < 10000:
                by_idx[n - 1] = fs[-1][0] * 1000
            for v, vx in fs[1:-1]:
                idx = _nearest_idx(vx)
                if idx not in by_idx and 0 < v < 10000:
                    by_idx[idx] = v * 1000
            _fill_gaps(by_idx)
            for i, model in enumerate(model_names):
                if i in by_idx:
                    result['por_modelo'][model]['P_dc_max_W'] = by_idx[i]
        break

    # ── 3. n_trackers / n_strings por columna ──────────────────────────────────
    # Buscar la fila de la TABLA (ej: "No. of MPP trackers / strings per MPP tracker   9/2   12/2")
    # No parar en filas de features que también contienen "MPP tracker" sin valores N/M
    for line in lines:
        # #146 — Deye SG01LP1: "Number of MPPT / Strings per MPPT  2/1+1  2/2+1 ..."
        if not re.search(r'MPP\s+tracker|Number\s+of\s+MPPT\s*/\s*Strings\s+per\s+MPPT',
                         line, re.IGNORECASE):
            continue
        found = [
            (int(m.group(1)), int(m.group(2)), m.start())
            for m in re.finditer(r'(\d+)\s*/\s*(\d+)', line)
        ]
        if not found:
            continue   # línea de feature bullet sin N/M — seguir buscando
        if len(found) == n:
            for (nt, ns, _), model in zip(found, model_names):
                result['por_modelo'][model]['n_trackers']        = float(nt)
                result['por_modelo'][model]['n_strings_tracker'] = float(ns)
        else:
            by_idx: dict = {}
            for nt, ns, vx in found:
                idx = _nearest_idx(vx)
                if idx not in by_idx:
                    by_idx[idx] = (float(nt), float(ns))
            _fill_gaps(by_idx)
            for i, model in enumerate(model_names):
                if i in by_idx:
                    nt, ns = by_idx[i]
                    result['por_modelo'][model]['n_trackers']        = nt
                    result['por_modelo'][model]['n_strings_tracker'] = ns
        break

    # ── 3b. Corrientes por columna ──────────────────────────────────────────────
    # "Max. PV input current per MPPT (A) 26 / 26 35 / 35" — cada columna trae
    # "I1 / I2" (una corriente por MPPT); tomamos el máximo del par.
    # #146 — Deye SG01LP1: "PV Input Current (A) 13+13 26+13 ..." y
    # "Max. PV ISC (A) 17+17 34+17 ..." — cada columna trae "I1+I2" (una
    # corriente por MPPT); igual que con "/", se toma el máximo del par.
    for campo, patron in (
        ('I_max_tracker',   r'Max\.?\s*PV\s+input\s+current|PV\s+Input\s+Current\s*\(A\)'),
        ('Isc_max_tracker', r'Max\.?\s*PV\s+short[-\s]?circuit\s+current|Max\.?\s*PV\s+ISC\b'),
    ):
        for line in lines:
            m_lab = re.search(patron, line, re.IGNORECASE)
            if not m_lab:
                continue
            resto_ini = m_lab.end()
            found = [
                (max(float(m.group(1).replace(',', '.')),
                     float(m.group(2).replace(',', '.'))), m.start())
                for m in re.finditer(
                    r'([0-9]+(?:[.,][0-9]+)?)\s*[/+]\s*([0-9]+(?:[.,][0-9]+)?)', line)
                if m.start() >= resto_ini
            ]
            if not found:
                found = [
                    (float(m.group(1).replace(',', '.')), m.start())
                    for m in re.finditer(r'([0-9]+(?:[.,][0-9]+)?)\s*A?\b', line)
                    if m.start() >= resto_ini
                ]
            if not found:
                continue
            if len(found) == n:
                for (v, _), model in zip(found, model_names):
                    result['por_modelo'][model][campo] = v
            else:
                # Menos valores que modelos: en texto comprimido las posiciones
                # no distinguen columnas → anclar primer valor a la primera
                # columna y último a la última; el resto por posición.
                by_idx: dict = {}
                fs = sorted(found, key=lambda t: t[1])
                by_idx[0] = fs[0][0]
                by_idx[n - 1] = fs[-1][0]
                for v, vx in fs[1:-1]:
                    idx = _nearest_idx(vx)
                    if idx not in by_idx:
                        by_idx[idx] = v
                _fill_gaps(by_idx)
                for i, model in enumerate(model_names):
                    if i in by_idx:
                        result['por_modelo'][model][campo] = by_idx[i]
            break

    # ── 4. n_trackers por columna, formato SAJ español: "No. de MPPT 3 4 4" ────
    if all(result['por_modelo'][m]['n_trackers'] is None for m in model_names):
        mejor: list = []
        for line in lines:
            m_lab = re.match(r'\s*No\.?\s*de\s+MPPT\b(.*)$', line, re.IGNORECASE)
            if not m_lab:
                continue
            vals = [int(x) for x in re.findall(r'\b([0-9]{1,2})\b', m_lab.group(1))]
            if len(vals) == n:
                mejor = vals
                break
            if vals and not mejor:
                mejor = vals
        if mejor:
            if len(mejor) < n:
                mejor = mejor + [mejor[-1]] * (n - len(mejor))
            for v, model in zip(mejor, model_names):
                result['por_modelo'][model]['n_trackers'] = float(v)
        # Strings por MPPT: "No. de cadenas por MPPT 2/2/2 2/2/2/2"
        for line in lines:
            m_lab = re.match(r'\s*No\.?\s*de\s+cadenas\s+por\s+MPPT\b(.*)$', line, re.IGNORECASE)
            if m_lab:
                m_v = re.search(r'\b([0-9]{1,2})\s*/', m_lab.group(1))
                if m_v:
                    for model in model_names:
                        result['por_modelo'][model]['n_strings_tracker'] = float(m_v.group(1))
                break

    return result


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
        texto, es_escaneado, n_pages_total = _extract_text_pdfplumber(pdf_io)
    except Exception as e:
        return {"error": f"Error leyendo el PDF: {e}"}

    uso_ocr = False
    if es_escaneado:
        ocr_text = _ocr_pdf(pdf_bytes)
        if len(ocr_text.strip()) >= 120:
            texto = ocr_text
            uso_ocr = True

    # ── Normalizar notación d.c./a.c. (SolaX X3-FORTH y similar) ─────────────
    # "1100 d.c. V" → "1100 V"  |  "32 d.c. A" → "32 A"
    texto = re.sub(r"\s*d\.c\.?\s*", " ", texto)
    texto = re.sub(r"\s*a\.c\.?\s*", " ", texto)
    # Eliminar caracteres de control incrustados (Growatt: "MAX\x0150KTL3-XL\x012"
    # parte los nombres de modelo y rompe la detección multi-modelo)
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texto)
    # Separador de miles (Huawei español: "1,100 V", "60,000 W") → "1100 V"
    # Seguro frente a decimales tipo "0,8" o "99,90" (no tienen 3 dígitos tras la coma)
    texto = re.sub(r"(\d),(\d{3})(?!\d)", r"\1\2", texto)

    # ── Metadatos ─────────────────────────────────────────────────────────────
    marca       = _extract_brand(texto)
    modelo      = _extract_model(texto, marca)
    arquitectura = _extract_arch(texto)
    es_hibrido  = bool(_HYBRID_RE.search(texto[:2000]))

    campos = _extraer_campos(texto)

    # ── Multi-modelo: columnas (SolaX/Growatt) o folleto de familia (Voltronic) ─
    multimodel = _extraer_multimodelo(texto)

    # Si hay P_dc real por modelo, descartar la estimación global (ratio 1.5)
    tiene_pdc_pm = any(
        (v or {}).get('P_dc_max_W') and not (v or {}).get('P_dc_estimado')
        for v in multimodel.get('por_modelo', {}).values()
    )
    if campos.get('P_dc_estimado') and tiene_pdc_pm:
        campos['P_dc_max_W'] = None
        campos['P_dc_estimado'] = False

    return {
        "modelo":           modelo,
        "marca":            marca,
        "arquitectura":     arquitectura,
        "es_hibrido":       es_hibrido,
        **campos,
        "es_escaneado":     es_escaneado,
        "uso_ocr":          uso_ocr,
        "ocr_disponible":   _HAS_OCR,
        "n_pages_total":    n_pages_total,
        "n_chars_extraidos": len(texto.strip()),
        "texto_crudo":      texto[:6000],
        # Multi-modelo: vacío si la ficha sólo tiene un modelo
        "modelos_detectados":  multimodel.get('modelos', []),
        "valores_por_modelo":  multimodel.get('por_modelo', {}),
    }


# Campos críticos que la UI usa para detectar un fallo silencioso del extractor.
# Si más de 3 quedan en None, casi seguro el extractor no reconoció el formato
# de la ficha (no es un dato suelto ausente, es el datasheet completo sin leer).
# #155: definición canónica en calculos/campos_inversor.py; re-export aquí
# para mantener la API pública del extractor.
from calculos.campos_inversor import CAMPOS_CRITICOS_INVERSOR  # noqa: F401


def contar_campos_vacios(resultado: dict) -> list:
    """
    Devuelve la lista de campos críticos que quedaron en None tras la extracción.

    Considera también los valores por modelo (multi-modelo): si un campo está
    vacío en el resultado global pero fue extraído para al menos un modelo de la
    ficha, NO se cuenta como vacío (el dato existe, solo vive en `valores_por_modelo`).

    La UI puede alertar cuando `len(contar_campos_vacios(res)) > 3`, señal de que
    el extractor probablemente falló en silencio con ese formato de PDF.

    Args:
        resultado: dict devuelto por `extraer_parametros_inversor` (o
                   `extraer_desde_texto`).

    Returns:
        list[str] — nombres de los campos críticos en None (posiblemente vacía).
    """
    if not isinstance(resultado, dict):
        return list(CAMPOS_CRITICOS_INVERSOR)

    por_modelo = resultado.get("valores_por_modelo") or {}

    vacios = []
    for campo in CAMPOS_CRITICOS_INVERSOR:
        if resultado.get(campo) is not None:
            continue
        # ¿Algún modelo de la ficha sí trae este campo? → no está realmente vacío
        cubierto_por_modelo = any(
            (vals or {}).get(campo) is not None
            for vals in por_modelo.values()
        )
        if not cubierto_por_modelo:
            vacios.append(campo)
    return vacios


def _extraer_multimodelo(texto: str) -> dict:
    """
    Ruta multi-modelo unificada: primero columnas (SolaX/Growatt/SAJ/TriP2) y,
    si no hay encabezado de columnas, folleto de familia (Voltronic) con varias
    tablas "MODEL <nombre>".  La usan tanto el extractor de PDFs como
    `extraer_desde_texto` (harness) para garantizar la misma cobertura.
    """
    multimodel = _extract_multimodel_values(texto)
    if not multimodel.get('modelos'):
        fam = _detect_family_sections(texto)
        if sum(len(nombres) for nombres, _ in fam) >= 2:
            modelos_fam, por_modelo_fam = [], {}
            for nombres, sec in fam:
                campos_sec = _extraer_campos(sec)
                for nombre in nombres:
                    nombre = re.sub(r"\s+", " ", nombre).strip()
                    # Basura de tablas reparadas: tokens repetidos ("InfiniSolar 5KW lar 5KW")
                    palabras = nombre.split()
                    if len(set(palabras)) != len(palabras):
                        continue
                    if nombre in por_modelo_fam:
                        # Sección duplicada (texto repetido): rellenar solo los huecos
                        prev = por_modelo_fam[nombre]
                        for k, v in campos_sec.items():
                            if prev.get(k) is None and v is not None:
                                prev[k] = v
                    else:
                        modelos_fam.append(nombre)
                        por_modelo_fam[nombre] = dict(campos_sec)
            if len(modelos_fam) >= 2:
                multimodel = {'modelos': modelos_fam, 'por_modelo': por_modelo_fam}
    return multimodel


# Folletos de familia (Voltronic InfiniSolar): varias tablas "MODEL <nombre(s)>"
_FAMILY_MODEL_RE = re.compile(r"^\s*MODEL(?:O)?\b[ \t]+(\S[^\n]{2,90})$", re.MULTILINE | re.IGNORECASE)


def _split_model_names(s: str) -> list:
    """Divide 'InfiniSolar 2KW InfiniSolar Plus 3KW' por repetición de la 1ª palabra."""
    words = s.split()
    if not words:
        return []
    first = words[0]
    idxs = [i for i, w in enumerate(words) if w == first]
    if len(idxs) >= 2:
        names = []
        for j, i0 in enumerate(idxs):
            i1 = idxs[j + 1] if j + 1 < len(idxs) else len(words)
            names.append(" ".join(words[i0:i1]))
        return names
    return [s.strip()]


def _detect_family_sections(texto: str) -> list:
    """
    Detecta folletos con varias tablas de especificaciones encabezadas por
    'MODEL <nombre>'. Devuelve [(nombres, texto_seccion), ...] — cada sección
    va desde su línea MODEL hasta la siguiente (o el final del documento).
    """
    matches = list(_FAMILY_MODEL_RE.finditer(texto))
    if not matches:
        return []
    secciones = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        nombres = _split_model_names(m.group(1).strip())
        if nombres:
            secciones.append((nombres, texto[start:end]))
    return secciones


def _extraer_campos(texto: str) -> dict:
    """Extrae los campos eléctricos desde texto plano (documento o sección)."""
    # ── Vdc_max ───────────────────────────────────────────────────────────────
    Vdc_max = _find(_PAT_VDCMAX, texto)

    # ── Rango MPPT (Vmppt_min, Vmppt_max) ────────────────────────────────────
    Vmppt_min, Vmppt_max = _find_range(_LABEL_MPPT_RANGE, texto)

    # Fallback conservador: si la ficha no publica tensión DC máxima (Growatt
    # en español), usar el tope del rango MPPT — nunca sobreestima el límite
    if Vdc_max is None and Vmppt_max is not None:
        Vdc_max = Vmppt_max

    # Fallback: extraer rango del texto completo si no se encontró por etiqueta
    if Vmppt_min is None:
        m = _RANGE_RE.search(texto)
        if m:
            lo, hi = _num(m.group(1)), _num(m.group(2))
            if lo and hi and lo < hi and hi > 100:
                Vmppt_min, Vmppt_max = (lo, hi)

    # ── V_mppt_activo ─────────────────────────────────────────────────────────
    # use_sma_fallback=False: "DC voltage range" de SMA es rango MPPT, no activo
    Vmppt_act_lo, Vmppt_act_hi = _find_range(_LABEL_MPPT_ACTIVO, texto, use_sma_fallback=False)
    V_mppt_activo = Vmppt_act_lo  # interés: límite inferior con carga completa

    # Voltronic/InfiniSolar (etiqueta doble): "MPP Voltage Range / Full Load MPP
    # Voltage Range 350 VDC ~ 850 VDC / 400 VDC ~ 800 VDC" → activo = 3er valor
    m_volt = re.search(
        r"MPP\s+Voltage\s+Range\s*/\s*Full\s+Load\s+MPP\s+Voltage\s+Range\s+"
        r"[0-9.]+\s*V(?:DC)?\s*~\s*[0-9.]+\s*V(?:DC)?\s*/\s*([0-9.]+)\s*V(?:DC)?\s*~",
        texto, re.IGNORECASE,
    )
    if m_volt:
        V_mppt_activo = _num(m_volt.group(1))

    # Fallback: tensión nominal/rated de entrada FV como valor único
    # (SolaX: "Rated PV input voltage 600 V@230 V"; Huawei/Sungrow: "Rated input voltage")
    if V_mppt_activo is None:
        m_rated = re.search(
            r"(?:Rated|Nominal)\s+(?:PV|DC)\s+input\s+voltage"
            # V final opcional: "Rated PV input voltage (V) 690" (unidad en la etiqueta)
            r"[^\n0-9]*([0-9]{2,4}(?:[.,][0-9]+)?)\s*V?\b",
            texto, re.IGNORECASE,
        )
        # Español (Growatt XMV): "Voltaje nominal 720V" en sección de entrada CD.
        # El lookahead (?!\s*CA) evita capturar "Voltaje nominal CA 277V/480V".
        if not m_rated:
            m_rated = re.search(
                r"Voltaje\s+nominal(?!\s*\(?\s*CA)\s*[:\(]?\s*([0-9]{2,4}(?:[.,][0-9]+)?)\s*V",
                texto, re.IGNORECASE,
            )
        # Huawei español: "Tensión nominal de entrada 600 V @380 Vac ..."
        if not m_rated:
            m_rated = re.search(
                r"Tensi[oó]n\s+nominal\s+de\s+entrada\s*(?:\[\s*V\s*\])?\s*[:\(]?\s*([0-9]{2,4}(?:[.,][0-9]+)?)\s*V?",
                texto, re.IGNORECASE,
            )
        # Growatt MID: "MPPT voltage range 580V" — un solo valor (tensión MPPT
        # nominal a plena carga); el (?![-~]) evita capturar un rango real
        if not m_rated:
            m_rated = re.search(
                r"MPPT\s+voltage\s+range\s*[:\s]\s*([0-9]{2,4})\s*V\b\s*(?![-~–—]|to\b)",
                texto, re.IGNORECASE,
            )
        if m_rated:
            v = _num(m_rated.group(1))
            # Sanity: dentro del rango MPPT si se conoce; si no, 100–1500 V
            lo_ok = Vmppt_min if Vmppt_min is not None else 100
            hi_ok = Vmppt_max if Vmppt_max is not None else 1500
            if v is not None and lo_ok <= v <= hi_ok:
                V_mppt_activo = v

    # Sanity final V_mppt_activo: debe ser tensión PV plausible (≥60 V) y caer
    # dentro del rango MPPT conocido — descarta rangos no eléctricos capturados
    # por etiquetas genéricas (p. ej. porcentajes junto a 'Rango de potencia máxima')
    if V_mppt_activo is not None:
        if (V_mppt_activo < 60
                or (Vmppt_min is not None and V_mppt_activo < Vmppt_min)
                or (Vmppt_max is not None and V_mppt_activo > Vmppt_max)):
            V_mppt_activo = None

    # ── V_arranque ────────────────────────────────────────────────────────────
    V_arranque = _find(_PAT_VARRANQUE, texto)
    # Sanity: V_arranque PV típica ≥60 V; valores < 60 V corresponden a tensión
    # mínima de batería (p. ej. "Minimum start voltage: 48 V" en inversores híbridos)
    if V_arranque is not None and V_arranque < 60:
        V_arranque = None

    # ── n_trackers ────────────────────────────────────────────────────────────
    n_trackers = _find(_PAT_NTRACKERS, texto)
    n_strings_tracker = _find(_PAT_NSTRINGS, texto)

    # Fila combinada etiquetada "No. of MPP trackers / strings per MPP tracker 3 / 2"
    m_tsl = _TRACKER_STR_LABEL_RE.search(texto)
    if m_tsl:
        if n_trackers is None:
            n_trackers = _num(m_tsl.group(1))
        if n_strings_tracker is None:
            n_strings_tracker = _num(m_tsl.group(2))

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
        r"Max(?:imum)?\.?\s+PV\s+(?:array\s+)?(?:input\s+)?[Pp]ower"
        r"\s*\[?kWp?\]?\s*[:\(]?\s*([0-9]+(?:[.,][0-9]+)?)(?:\s*kWp?)?",
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
            r"[^\n]*\b([0-9]+(?:[.,][0-9]+)?)\s*kW(?!p)",
            texto, re.IGNORECASE,
        )
        if m_kw:
            v = _num(m_kw.group(1))
            if v and 0 < v < 10000:  # sanity: valor razonable en kW
                p_kw_converted = v * 1000

    # Intento 3a: SolaX X3-FORTH misma línea — "Max. recommended PV array power   120 kWp"
    # (pdftotext -layout / pdfplumber tabla con todo en una línea)
    if p_kw_converted is None:
        m_rec_sl = re.search(
            r"Max(?:imum)?\.?\s+recommended\s+PV\s+(?:array\s+)?[Pp]ower"
            r"[^\n]*?([0-9]+(?:[.,][0-9]+)?)\s*kWp?\b",
            texto, re.IGNORECASE,
        )
        if m_rec_sl:
            v = _num(m_rec_sl.group(1))
            if v and v < 10000:
                p_kw_converted = v * 1000

    # Intento 3b: SolaX X3-FORTH multilinea — "Max. recommended PV array power\n...\n120 kWp"
    # (tabla vertical donde label y valor están en líneas distintas)
    if p_kw_converted is None:
        m_rec = re.search(
            r"Max(?:imum)?\.?\s+recommended\s+PV\s+(?:array\s+)?[Pp]ower[^\n]*\n"
            r"(?:[^\n]*\n){0,5}\s*([0-9]+(?:[.,][0-9]+)?)\s*kWp?\b",
            texto, re.IGNORECASE,
        )
        if m_rec:
            v = _num(m_rec.group(1))
            if v and v < 10000:
                p_kw_converted = v * 1000

    # Intento 4: tabla 3 columnas — "Max. recommended PV array power  kWp  150"
    # (pdfplumber une [Parámetro | Unidad | Valor]: unidad queda antes del número)
    if p_kw_converted is None:
        m_rec_3c = re.search(
            r"Max(?:imum)?\.?\s+recommended\s+PV\s+(?:array\s+)?[Pp]ower\s+kWp?\s+([0-9]+(?:[.,][0-9]+)?)",
            texto, re.IGNORECASE,
        )
        if m_rec_3c:
            v = _num(m_rec_3c.group(1))
            if v and v < 10000:
                p_kw_converted = v * 1000

    P_dc_max_W = p_kw_converted or _find(_PAT_PDCMAX, texto)

    # ── Estimación de P_dc cuando la ficha no la publica (Huawei y similares) ──
    # Se estima desde la potencia CA nominal con ratio DC/AC 1.5 (práctica
    # estándar de sobredimensionamiento).
    P_dc_estimado = False
    if P_dc_max_W is None:
        m_pac = re.search(
            r"(?:Potencia\s+nominal\s+(?:CA|AC)|Potencia\s+activa"
            r"|Rated\s+(?:AC\s+)?[Oo]utput\s+[Pp]ower|Rated\s+[Aa]ctive\s+[Pp]ower"
            r"|Nominal\s+(?:AC\s+)?[Oo]utput\s+[Pp]ower|AC\s+[Rr]ated\s+[Pp]ower)"
            r"[^\n0-9]{0,20}([0-9]+(?:[.,][0-9]+)?)\s*(k?)W\b",
            texto, re.IGNORECASE,
        )
        if m_pac:
            p_ac = _num(m_pac.group(1))
            if p_ac is not None:
                if m_pac.group(2).lower() == 'k' or p_ac < 1000:
                    p_ac *= 1000
                if 500 <= p_ac <= 5_000_000:
                    P_dc_max_W = round(p_ac * 1.5)
                    P_dc_estimado = True

    # ── Batería ───────────────────────────────────────────────────────────────
    # use_sma_fallback=False para evitar que "DC voltage range, min./max." de SMA
    # sea confundido con voltaje de batería
    bat_min_r, bat_max_r = _find_range(_LABEL_BAT_RANGE, texto, use_sma_fallback=False)
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
    # n_trackers: entre 1 y 24 (inversor C&I de hasta 24 MPPTs)
    if n_trackers is not None and not (1 <= n_trackers <= 24):
        n_trackers = None
    # n_strings_tracker: entre 1 y 6
    if n_strings_tracker is not None and not (1 <= n_strings_tracker <= 6):
        n_strings_tracker = None
    # Corrientes: entre 1 y 200 A
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
        # True si P_dc_max_W fue estimada desde la potencia CA nominal (ratio 1.5)
        "P_dc_estimado":    P_dc_estimado,
        "bat_voltaje_min":  bat_voltaje_min,
        "bat_voltaje_max":  bat_voltaje_max,
    }


def pdf_disponible() -> bool:
    return _HAS_PDF


def ocr_disponible() -> bool:
    return _HAS_OCR
