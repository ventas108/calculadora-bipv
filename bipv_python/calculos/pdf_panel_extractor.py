"""
pdf_panel_extractor.py — Extrae parámetros eléctricos de fichas técnicas PDF de paneles FV.

Usa pdfplumber (MIT) para texto + tablas. Soporta datasheets en español e inglés
de los principales fabricantes: Canadian Solar, Trina, Longi, JA Solar, SolarWorld,
Risen, Jinko, Hanwha Q Cells, etc.

Fallback OCR (pdf2image + pytesseract) para PDFs escaneados/imagen.

Función principal:
  extraer_parametros_panel(pdf_bytes: bytes) -> dict
"""

import re
import io
import unicodedata
from typing import Optional

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

# Umbral mínimo de texto para considerar el PDF como digital (no escaneado)
_MIN_TEXT_CHARS = 120


# ── Patrones de extracción ────────────────────────────────────────────────────
_PATTERNS = {
    "Pmax": [
        r'(?:Pmax|P_max|Pmpp|Potencia\s+M[aá]xima?|Maximum\s+Power|Rated\s+Power|STC\s+Power|Peak\s+Power)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*W',
        r'([0-9]{2,3}(?:\.[0-9]+)?)\s*Wp\b',
        r'P\s*[=:]\s*([0-9]+(?:\.[0-9]+)?)\s*W',
    ],
    "Voc": [
        r'(?:Voc|V_oc|VOC|Open[- ]?[Cc]ircuit\s+[Vv]oltage|Tensi[oó]n\s+(?:de\s+)?[Cc]ircuito\s+[Aa]bierto)\s*[:\(°]?\s*([0-9]+(?:\.[0-9]+)?)\s*V',
        r'VOC?\s*\(V\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Voc\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "Isc": [
        r'(?:Isc|I_sc|ISC|Short[- ]?[Cc]ircuit\s+[Cc]urrent|Corriente\s+(?:de\s+)?[Cc]ortocircuito)\s*[:\(°]?\s*([0-9]+(?:\.[0-9]+)?)\s*A',
        r'ISC?\s*\(A\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Isc\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "Vmp": [
        r'(?:Vmpp|Vmp|V_mp|VMPP|Maximum\s+Power\s+Voltage|Tensi[oó]n\s+(?:de\s+)?[Mm][aá]xima?\s+[Pp]otencia)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*V',
        r'VMPP?\s*\(V\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Vmp\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "Imp": [
        r'(?:Impp|Imp|I_mp|IMPP|Maximum\s+Power\s+Current|Corriente\s+(?:de\s+)?[Mm][aá]xima?\s+[Pp]otencia)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*A',
        r'IMPP?\s*\(A\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Imp\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "N_s": [
        r'(?:N[oú]mero\s+de\s+c[eé]lulas?|Number\s+of\s+cells?|Cell\s+Number|Cells?\s+[Ss]eries?|Celdas?\s+en\s+[Ss]erie)\s*[:\|]?\s*([0-9]+)',
        r'(?:N_s|Ns|NSA)\s*[:\|=]?\s*([0-9]+)',
        r'\b([0-9]{2,3})\s+(?:cells?|c[eé]lulas?)\b',
    ],
    "CoefVoc": [
        r'(?:β|beta|β_Voc|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?Voc|Temperatura\s+Voc|TK\s*Voc)\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:β|beta)V?[Oo][Cc]?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'Voc\s+coeff?\.?\s*[:\|]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        # NCL BIPV: "Coeficiente de temperatura para voltaje  -0.28%/ºC"
        r'temperatura\s+para\s+voltaje[^%\n]*?([+-]?[0-9]*\.?[0-9]+)\s*%',
    ],
    "CoefIsc": [
        r'(?:α|alpha|α_Isc|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?Isc|Temperatura\s+Isc|TK\s*Isc)\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:α|alpha)I?[Ss][Cc]?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
    ],
    "CoefPmax": [
        r'(?:γ|gamma|γ_Pmax|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?P(?:max|mpp)|Temperatura\s+P(?:max|mpp)|TK\s*P(?:max|mpp))\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:γ|gamma)P?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'Pmax\s+coeff?\.?\s*[:\|]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
    ],
    "NOCT": [
        r'(?:NOCT|NMOT|Normal(?:ized)?\s+(?:Operating)?\s+Cell\s+Temp(?:erature)?|Temperatura\s+(?:de\s+)?[Oo]peraci[oó]n\s+Normal)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*°?C',
        r'NOCT\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "dimensiones": [
        r'([0-9]{3,4})\s*[×xX*]\s*([0-9]{3,4})\s*[×xX*]\s*([0-9]+)\s*mm',
        r'Dimensions?\s*[:\(]?\s*([0-9]{3,4})\s*[×xX*]\s*([0-9]{3,4})',
    ],
}

_TECH_PATTERNS = [
    (r'(?:Mono(?:crystalline)?[- ]?Si(?:licon)?|Mono-Si|mSi|HJT|Heterojunction|TOPCon|PERC)', "Mono-Si"),
    (r'(?:Poly(?:crystalline)?[- ]?Si(?:licon)?|Multi[- ]?Si|mPoly)', "Poly-Si"),
    (r'(?:CIS|CIGS|Copper\s+Indium)', "CIS"),
    (r'(?:CdTe|Cadmium\s+Telluride|Telururo\s+de\s+Cadmio)', "CdTe"),
    (r'(?:a-Si|Amorphous\s+Silicon)', "a-Si"),
    (r'(?:Thin\s+[Ff]ilm|Pel[ií]cula\s+[Dd]elgada)', "Thin Film"),
]

# ── Multi-modelo: constantes para extracción por columna ─────────────────────

# Detecta códigos de modelo tipo "CS6R-400MS", "NCL-BP-P-C02-327", "LR5-72HTH-540M"
_MODEL_CODE_RE = re.compile(
    r'\b([A-Z][A-Z0-9]{1,7}[-][A-Z0-9][-A-Z0-9\-\.]{3,40})\b'
)

# Campos variables entre variantes de una misma familia de paneles
_MULTIMODEL_VAR_PATTERNS = {
    "Pmax": [
        r'(?:Pmax|P[\s_]?max|Potencia\s+(?:nominal|m[aá]xima?)'
        r'|Maximum\s+Power|Rated\s+Power|Peak\s+Power)',
    ],
    "Voc": [
        r'(?:Voc\b|V[\s_]?oc\b'
        r'|Voltaje\s+en\s+circuito\s+abierto'
        r'|Open[\s-]?Circuit\s+Volt)',
    ],
    "Isc": [
        r'(?:Isc\b|I[\s_]?sc\b'
        r'|Corriente\s+de\s+corto[- ]?circuito'
        r'|Short[\s-]?Circuit\s+Curr)',
    ],
    "Vmp": [
        r'(?:Vmpp|Vmp\b|V[\s_]?mp\b'
        r'|Voltaje\s+en\s+m[aá]xima\s+potencia'
        r'|Maximum\s+Power\s+Volt)',
    ],
    "Imp": [
        r'(?:Impp|Imp\b|I[\s_]?mp\b'
        r'|Corriente\s+m[aá]xima\s+potencia'
        r'|Maximum\s+Power\s+Curr)',
    ],
}

# Rangos plausibles para filtrar ruido numérico del PDF
_MULTIMODEL_PLAUSIBLE: dict = {
    "Pmax":          (5.0,  2000.0),
    "Voc":           (5.0,   300.0),
    "Isc":           (0.05,   60.0),
    "Vmp":           (5.0,   250.0),
    "Imp":           (0.05,   60.0),
    "Transparencia": (0.0,   100.0),   # % de transparencia del vidrio BIPV
}


def _extract_row_numbers(line: str, from_pos: int = 0) -> list:
    """
    Extrae todos los números de una línea a partir de `from_pos`.
    Maneja valores con unidades embebidas: '327.8W', '124.2V', '3.74A', '1A'.
    """
    return [float(m) for m in re.findall(r'([0-9]+(?:\.[0-9]+)?)', line[from_pos:])]


# Reconocimiento de campo por abreviatura entre paréntesis — máxima prioridad,
# unambigua: "(Voc)", "(Vmp)", "(Imp)", "(Isc)", "(Pmax)", "(Pm)"
_ABBREV_IN_PARENS: dict = {
    "Pmax": re.compile(r'\(\s*(?:Pmax|Pmpp|P\.?m\.?)\s*\)', re.I),
    "Voc":  re.compile(r'\(\s*Voc\s*\)',                       re.I),
    "Isc":  re.compile(r'\(\s*Isc\s*\)',                       re.I),
    "Vmp":  re.compile(r'\(\s*V(?:mp|mpp)\s*\)',               re.I),
    "Imp":  re.compile(r'\(\s*I(?:mp|mpp)\s*\)',               re.I),
}

# Patrones de etiqueta para identificar filas en tablas estructuradas de pdfplumber.
# IMPORTANTE: el orden importa — los más específicos primero.
# "potencia" sola no es suficiente (aparece en "máxima potencia" de Vmp e Imp).
_TABLE_LABEL_RE: dict = {
    # Voc: ANTES de Pmax porque "circuito abierto" puede contener "ot" de "potencia"
    "Voc": re.compile(
        r'voc\b|v[\s_]*oc\b'
        r'|circuito[\s\-]+abierto|open[\s\-]?circuit'
        r'|tens[ií](?:on|ón).*abierto|voltaje.*abierto'
        r'|tensión.*circuito|voltaje.*circuito', re.I | re.UNICODE),
    # Isc: antes de Imp para no confundir "corto" con "corriente máx"
    "Isc": re.compile(
        r'isc\b|i[\s_]*sc\b'
        r'|corto[\s\-]?circuito|cortocircuito|short[\s\-]?circuit'
        r'|corriente.*corto', re.I | re.UNICODE),
    # Vmp: ANTES de Pmax — detecta "tensión en máxima potencia" y similares
    "Vmp": re.compile(
        r'vmpp?\b|v[\s_]*mpp?\b'
        r'|mpp.*tens|mpp.*volt'
        r'|maximum\s+power\s+volt'
        r'|tens[ií](?:on|ón).*m[aá]x'
        r'|voltaje.*m[aá]x'
        r'|m[aá]xima?\s+potencia.*(?:tens|volt)', re.I | re.UNICODE),
    # Imp: ANTES de Pmax — detecta "corriente en máxima potencia"
    "Imp": re.compile(
        r'impp?\b|i[\s_]*mpp?\b'
        r'|mpp.*corr'
        r'|maximum\s+power\s+curr'
        r'|corriente.*m[aá]x'
        r'|m[aá]xima?\s+potencia.*corr', re.I | re.UNICODE),
    # Pmax: AL FINAL y más específico — "potencia nominal/pico/cresta"
    "Pmax": re.compile(
        r'pmax\b|pmpp?\b|p[\s_]*max\b'
        r'|potencia\s+(?:nominal|m[aá]xima?|pico|cresta|punta)'
        r'|peak\s+power|rated\s+power'
        r'|maximum\s+power(?!\s+(?:volt|curr))', re.I | re.UNICODE),
}


def _extract_multimodel_from_tables(pdf_bytes: bytes) -> dict:
    """
    Extrae modelos y parámetros directamente de tablas estructuradas con pdfplumber.
    
    Estrategia: busca la fila donde ≥2 celdas son códigos de modelo.
    Luego asigna a cada columna el valor de las filas de parámetros (Pmax, Voc, …).
    Este método es más robusto que el basado en texto plano cuando pdfplumber 
    fragmenta columnas en líneas separadas.
    """
    EMPTY: dict = {"modelos_detectados": [], "valores_por_modelo": {}}
    if not _HAS_PDF:
        return EMPTY
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in (page.extract_tables() or []):
                    if not table or len(table) < 3:
                        continue

                    # ── Paso 1: encontrar fila de cabecera de modelos ─────────
                    model_row_idx: int = -1
                    model_names: list = []
                    model_col_indices: list = []

                    for ri, row in enumerate(table):
                        if row is None:
                            continue
                        cells = [str(c or "").strip() for c in row]
                        codes = [
                            (ci, c) for ci, c in enumerate(cells)
                            if _MODEL_CODE_RE.fullmatch(c) and re.search(r"\d", c)
                        ]
                        if len(codes) >= 2:
                            model_row_idx = ri
                            model_col_indices = [ci for ci, _ in codes]
                            model_names = [c for _, c in codes]
                            break

                    if model_row_idx == -1 or len(model_names) < 2:
                        continue

                    n = len(model_names)
                    por_modelo: dict = {m: {} for m in model_names}

                    # Algunas tablas (ej. NCL BIPV) alternan filas con etiqueta y filas
                    # sin etiqueta:  Pmax→Voc(vacío)→Isc→Vmp(vacío)→Imp→Transp(vacío)
                    # Mapeo: el campo que viene en la fila vacía SIGUIENTE a cada campo
                    _EMPTY_FOLLOWS: dict = {"Pmax": "Voc", "Isc": "Vmp", "Imp": "Transparencia"}
                    last_field_hit: str | None = None

                    # ── Paso 2: extraer filas de parámetros ──────────────────
                    for row in table[model_row_idx + 1:]:
                        if not row:
                            continue
                        # Normalizar a NFC para que ó/á/í/é en NFD también coincidan
                        cells = [
                            unicodedata.normalize("NFC", str(c or "")).strip()
                            for c in row
                        ]
                        if not cells:
                            continue

                        # Label: SIEMPRE cells[0] — primera columna = columna de etiqueta.
                        # NO usar next(c for c in cells if c) porque para filas sin
                        # etiqueta eso devuelve el primer VALOR (ej. '124.2V') en lugar
                        # de '' (vacío), impidiendo la detección de fila-sin-etiqueta.
                        label = cells[0]
                        label_nfc = unicodedata.normalize("NFC", label)

                        field_hit: str | None = None

                        if not label_nfc:
                            # Fila sin etiqueta — inferir campo por el campo anterior
                            field_hit = _EMPTY_FOLLOWS.get(last_field_hit)  # type: ignore[arg-type]
                        else:
                            # Identificar campo — prioridad 1: abreviatura entre paréntesis
                            for field, pat in _ABBREV_IN_PARENS.items():
                                if pat.search(label_nfc):
                                    field_hit = field
                                    break
                            # Prioridad 2: patrón de texto de la etiqueta (NFC normalizado)
                            if field_hit is None:
                                for field, pat in _TABLE_LABEL_RE.items():
                                    if pat.search(label_nfc):
                                        field_hit = field
                                        break

                        if field_hit is None:
                            continue

                        # Actualizar contexto solo cuando la fila tiene etiqueta real
                        if label_nfc:
                            last_field_hit = field_hit

                        lo, hi = _MULTIMODEL_PLAUSIBLE[field_hit]

                        def _nums_in(s: str) -> list:
                            return [
                                float(m) for m in
                                re.findall(r'[0-9]+(?:\.[0-9]+)?', s)
                            ]

                        # Intento 1: extracción por índice exacto de columna
                        hits_by_idx: dict = {}
                        for mi, col_idx in enumerate(model_col_indices):
                            if mi >= n or col_idx >= len(cells):
                                continue
                            for v in _nums_in(cells[col_idx]):
                                if lo <= v <= hi:
                                    hits_by_idx[mi] = v
                                    break

                        # Intento 2: si menos de la mitad de modelos obtuvo valor,
                        # usar extracción posicional (recoge todos los números
                        # plausibles de la fila ignorando columna de etiqueta/unidad)
                        if len(hits_by_idx) < max(1, n // 2):
                            plausible_vals: list = []
                            for ci, cell in enumerate(cells):
                                if ci == 0:         # columna de etiqueta
                                    continue
                                if not re.search(r'[0-9]', cell):
                                    continue        # columna de unidades ("V","A","W")
                                for v in _nums_in(cell):
                                    if lo <= v <= hi:
                                        plausible_vals.append(v)
                                        break
                            # Asignar posicionalmente al número de modelos
                            if len(plausible_vals) >= n:
                                hits_by_idx = {mi: plausible_vals[mi] for mi in range(n)}
                            elif len(plausible_vals) == 1:
                                # valor único (celda fusionada) → mismo para todos
                                hits_by_idx = {mi: plausible_vals[0] for mi in range(n)}

                        for mi, v in hits_by_idx.items():
                            por_modelo[model_names[mi]][field_hit] = v

                    # Considerar exitoso si al menos Pmax fue extraído
                    if any("Pmax" in v for v in por_modelo.values()):
                        return {
                            "modelos_detectados": model_names,
                            "valores_por_modelo": por_modelo,
                        }
    except Exception:
        pass
    return EMPTY


def _extract_multimodel_panel(text: str) -> dict:
    """
    Detecta y extrae parámetros por columna en fichas técnicas multi-modelo.

    Soporta dos formatos de salida de pdfplumber:
    (a) Texto plano (extract_text / pdftotext):
            "NCL-BP-P-C02-108  NCL-BP-P-C08-95  NCL-BP-P-C10-83  NCL-BP-P-C15-60"
            "Potencia nominal (Pm)  108W  95W  83W  60W  217W  193W  169.2W  121.5W"
    (b) Tablas pipe-separated (extract_tables):
            "Potencia nominal  |  108  |  95  |  83  |  60"

    Los campos compartidos entre variantes (CoefVoc, CoefIsc, CoefPmax, NOCT, Ns,
    tecnología, dimensiones) se siguen extrayendo con _apply_patterns() sobre el
    texto completo.

    Retorna:
        {
          'modelos_detectados': ['NCL-BP-P-C02-108', 'NCL-BP-P-C08-95', ...],
          'valores_por_modelo': {
              'NCL-BP-P-C02-108': {'Pmax': 108.0, 'Voc': 124.2, 'Isc': 1.21,
                                    'Vmp': 96.0,  'Imp': 1.11},
              ...
          }
        }
    """
    EMPTY: dict = {"modelos_detectados": [], "valores_por_modelo": {}}
    lines = text.splitlines()

    # ── Paso 1: detectar línea de cabecera con ≥2 códigos de modelo ──────────
    model_names: list = []

    for line in lines:
        # (a) Pipe-separated table header — la tabla de specs puede estar en cualquier página
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            codes = [
                p for p in parts
                if _MODEL_CODE_RE.fullmatch(p) and re.search(r"\d", p)
            ]
            if len(codes) >= 2:
                model_names = codes
                break

        # (b) Texto plano: múltiples códigos en la misma línea
        codes = [c for c in _MODEL_CODE_RE.findall(line) if re.search(r"\d", c)]
        if len(codes) >= 2:
            model_names = codes
            break

    # Fallback: línea con label de Pmax que contiene ≥2 valores plausibles
    if not model_names:
        for line in lines:
            for pat in _MULTIMODEL_VAR_PATTERNS["Pmax"]:
                m_lbl = re.search(pat, line, re.IGNORECASE)
                if not m_lbl:
                    continue
                nums = _extract_row_numbers(line, m_lbl.end())
                plausible = [v for v in nums if 5.0 <= v <= 2000.0]
                if len(plausible) >= 2:
                    model_names = [
                        f"{int(v)}Wp" if v == int(v) else f"{v}Wp"
                        for v in plausible
                    ]
                    break
            if model_names:
                break

    if len(model_names) < 2:
        return EMPTY

    n = len(model_names)
    por_modelo: dict = {m: {} for m in model_names}

    # ── Paso 2: extraer campos variables de las filas de especificaciones ─────
    for field, pats in _MULTIMODEL_VAR_PATTERNS.items():
        lo, hi = _MULTIMODEL_PLAUSIBLE[field]

        for line in lines:
            for pat in pats:
                m_lbl = re.search(pat, line, re.IGNORECASE)
                if not m_lbl:
                    continue

                if "|" in line:
                    # Formato pipe: extraer primer número de cada celda tras el label
                    cells = [c.strip() for c in line.split("|")]
                    vals = []
                    for cell in cells[1:]:
                        mn = re.search(r"([0-9]+(?:\.[0-9]+)?)", cell)
                        if mn:
                            vals.append(float(mn.group(1)))
                else:
                    # Texto plano: números plausibles después del label
                    vals = [
                        v for v in _extract_row_numbers(line, m_lbl.end())
                        if lo <= v <= hi
                    ]

                if len(vals) >= n:
                    for model, val in zip(model_names, vals[:n]):
                        por_modelo[model][field] = val
                    break
                elif len(vals) >= 2:
                    # Asignación parcial (menos valores que modelos)
                    for i, val in enumerate(vals[:n]):
                        por_modelo[model_names[i]][field] = val
                    break
            else:
                continue
            break  # campo asignado; pasar al siguiente

    return {"modelos_detectados": model_names, "valores_por_modelo": por_modelo}


def _find_first(text: str, patterns: list) -> Optional[float]:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", "."))
            except (ValueError, IndexError):
                pass
    return None


def _detect_technology(text: str) -> str:
    for pat, tech in _TECH_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return tech
    return ""


def _extract_model_name(text: str) -> str:
    for line in text.splitlines()[:30]:
        line = line.strip()
        m = re.match(r'^([A-Z]{2,8}[-_][A-Z0-9\-\.]{4,25})$', line)
        if m:
            return m.group(1)
    m = re.search(r'\b([A-Z]{2,6}[-_][A-Z0-9\-\.]{4,25})\b', text)
    return m.group(1) if m else ""


def _extract_brand(text: str) -> str:
    BRANDS = [
        "Canadian Solar", "Trina Solar", "LONGi", "JA Solar", "Jinko",
        "Hanwha", "Q CELLS", "REC", "SolarWorld", "Yingli", "Risen",
        "CSUN", "Seraphim", "SunPower", "Panasonic", "LG", "BYD",
        "Hyundai", "Mitsubishi", "Sharp", "Kyocera", "GreenBrilliance",
        "Solartech Universal", "Vikram", "Waaree", "Adani", "Axitec",
        "Aleo", "IBC Solar", "Solarwatt",
    ]
    snippet = "\n".join(text.splitlines()[:20])
    for b in BRANDS:
        if re.search(re.escape(b), snippet, re.IGNORECASE):
            return b
    return ""


def _extract_text_pdftotext(pdf_bytes: bytes) -> str:
    """
    Extrae texto preservando layout de columnas con pdftotext -layout (poppler-utils).
    Es más confiable que pdfplumber.extract_text() para tablas multi-columna.
    Retorna string vacío si pdftotext no está disponible.
    """
    import subprocess
    import tempfile
    import os
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", tmp_path, "-"],
            capture_output=True,
            timeout=20,
        )
        os.unlink(tmp_path)
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace")
    except Exception:
        pass
    return ""


def _extract_text_pdfplumber(pdf_bytes: bytes) -> str:
    """Extrae texto + tablas de un PDF digital usando pdfplumber."""
    if not _HAS_PDF:
        return ""
    extra = []
    try:
        source = io.BytesIO(pdf_bytes)
        with pdfplumber.open(source) as pdf:
            for page in pdf.pages[:4]:
                raw = page.extract_text() or ""
                extra.append(raw)
                for table in page.extract_tables():
                    for row in table:
                        extra.append("  |  ".join(str(c or "") for c in row))
    except Exception:
        pass
    return "\n".join(extra)


def _dump_tables_pdfplumber(pdf_bytes: bytes) -> str:
    """
    Debug: devuelve un volcado legible de todas las tablas que extrae pdfplumber.
    Solo se llama cuando se necesita diagnosticar fallos de extracción.
    """
    if not _HAS_PDF:
        return "(pdfplumber no instalado)"
    lines = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for pi, page in enumerate(pdf.pages):
                tables = page.extract_tables() or []
                for ti, table in enumerate(tables):
                    lines.append(f"=== Página {pi+1}, Tabla {ti+1} ({len(table)} filas) ===")
                    for ri, row in enumerate(table[:15]):
                        lines.append(f"  R{ri}: {[str(c or '')[:40] for c in (row or [])]}")
                    if len(table) > 15:
                        lines.append(f"  ... ({len(table)-15} filas más)")
    except Exception as e:
        lines.append(f"ERROR: {e}")
    return "\n".join(lines) or "(sin tablas detectadas)"


def _ocr_pdf(pdf_bytes: bytes) -> str:
    """
    Fallback OCR: convierte las primeras 3 páginas a imagen y corre Tesseract.
    Requiere pdf2image (poppler-utils) y pytesseract (tesseract-ocr).
    """
    if not _HAS_OCR:
        return ""
    try:
        images = convert_from_bytes(
            pdf_bytes,
            dpi=200,
            first_page=1,
            last_page=3,
            fmt="jpeg",
        )
        textos = []
        for img in images:
            # Intentar español + inglés; si falla, solo inglés
            try:
                t = pytesseract.image_to_string(img, lang="spa+eng")
            except Exception:
                try:
                    t = pytesseract.image_to_string(img, lang="eng")
                except Exception:
                    t = pytesseract.image_to_string(img)
            textos.append(t)
        return "\n".join(textos)
    except Exception:
        return ""


def _apply_patterns(texto: str) -> dict:
    """Aplica todos los patrones de extracción al texto y retorna dict de resultados."""
    result = {}
    for campo, patrones in _PATTERNS.items():
        if campo == "dimensiones":
            val = None
            for pat in patrones:
                m = re.search(pat, texto, re.IGNORECASE)
                if m:
                    try:
                        val = f"{m.group(1)}x{m.group(2)}"
                        if len(m.groups()) >= 3:
                            val += f"x{m.group(3)}"
                    except IndexError:
                        pass
                    break
            result["dimensiones"] = val
        else:
            result[campo] = _find_first(texto, patrones)
    return result


def extraer_parametros_panel(pdf_bytes: bytes) -> dict:
    """
    Extrae parámetros eléctricos de una ficha técnica PDF de panel FV.

    Flujo:
      1. pdfplumber extrae texto digital (rápido, preciso).
      2. Si el texto es muy corto (<120 chars), se activa el fallback OCR con
         pdf2image + pytesseract (lento ~5-15 s, requiere sistema deps).
      3. Si OCR tampoco está disponible, retorna campos vacíos con flag
         `es_escaneado=True, ocr_disponible=False`.

    Retorna dict con claves:
      modelo, marca, tecnologia,
      Pmax, Voc, Isc, Vmp, Imp,
      N_s, CoefVoc, CoefIsc, CoefPmax,
      NOCT, dimensiones,
      es_escaneado, uso_ocr, ocr_disponible,
      texto_crudo  (para debug)
    """
    if not _HAS_PDF:
        return {"error": "pdfplumber no instalado. Ejecuta: pip install pdfplumber"}

    # ── Paso 1: extracción digital ────────────────────────────────────────────
    texto = _extract_text_pdfplumber(pdf_bytes)
    es_escaneado = len(texto.strip()) < _MIN_TEXT_CHARS
    uso_ocr = False

    # ── Paso 2: fallback OCR ──────────────────────────────────────────────────
    if es_escaneado:
        if _HAS_OCR:
            texto_ocr = _ocr_pdf(pdf_bytes)
            if len(texto_ocr.strip()) >= _MIN_TEXT_CHARS:
                texto = texto_ocr
                uso_ocr = True
            # Si OCR también devuelve poco texto, dejamos texto vacío
        # Si no hay OCR disponible, texto sigue vacío

    # ── Paso 3: aplicar patrones ──────────────────────────────────────────────
    result = {
        "modelo":          _extract_model_name(texto),
        "marca":           _extract_brand(texto),
        "tecnologia":      _detect_technology(texto),
        "es_escaneado":    es_escaneado,
        "uso_ocr":         uso_ocr,
        "ocr_disponible":  _HAS_OCR,
        "texto_crudo":     texto[:4000],
    }

    vals = _apply_patterns(texto)
    result.update(vals)

    # Sanity checks (parámetros base del texto completo)
    if result.get("Voc") and result["Voc"] > 300:
        result["Voc"] = None
    if result.get("Isc") and result["Isc"] > 60:
        result["Isc"] = None
    if result.get("Pmax") and result["Pmax"] > 2000:
        result["Pmax"] = None

    # ── Extracción multi-modelo (fichas con varios modelos en columnas) ────────
    # Prioridad 1: tablas estructuradas de pdfplumber
    mm = _extract_multimodel_from_tables(pdf_bytes)

    if len(mm["modelos_detectados"]) < 2:
        # Prioridad 2: pdftotext -layout (preserva columnas; más fiable para tablas)
        texto_pt = _extract_text_pdftotext(pdf_bytes)
        if texto_pt.strip():
            mm = _extract_multimodel_panel(texto_pt)

    if len(mm["modelos_detectados"]) < 2:
        # Prioridad 3: texto de pdfplumber (peor preservación de columnas)
        mm = _extract_multimodel_panel(texto)

    result["modelos_detectados"] = mm["modelos_detectados"]
    result["valores_por_modelo"]  = mm["valores_por_modelo"]

    # Volcado de tablas pdfplumber para diagnóstico (se muestra en el expander de debug)
    result["_debug_tables"] = _dump_tables_pdfplumber(pdf_bytes)

    return result


def pdf_disponible() -> bool:
    return _HAS_PDF


def ocr_disponible() -> bool:
    return _HAS_OCR
