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
    (r'(?:CdTe|Cadmium\s+Telluride)', "CdTe"),
    (r'(?:a-Si|Amorphous\s+Silicon)', "a-Si"),
    (r'(?:Thin\s+[Ff]ilm|Película\s+[Dd]elgada)', "Thin Film"),
]


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

    # Sanity checks
    if result.get("Voc") and result["Voc"] > 200:
        result["Voc"] = None
    if result.get("Isc") and result["Isc"] > 50:
        result["Isc"] = None
    if result.get("Pmax") and result["Pmax"] > 1500:
        result["Pmax"] = None

    return result


def pdf_disponible() -> bool:
    return _HAS_PDF


def ocr_disponible() -> bool:
    return _HAS_OCR
