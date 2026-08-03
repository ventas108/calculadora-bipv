"""
pdf_panel_extractor.py — Extrae parámetros eléctricos de fichas técnicas PDF de paneles FV.

Usa pdfplumber (MIT) para texto + tablas. Soporta datasheets en español e inglés
de los principales fabricantes: Canadian Solar, Trina, Longi, JA Solar, SolarWorld,
Risen, Jinko, Hanwha Q Cells, etc.

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


# ── Patrones de extracción ────────────────────────────────────────────────────
# Cada entrada: (campo_destino, [regex_patrones])
# Los patrones se prueban en orden; el primer match gana.
# Grupo 1 debe capturar el valor numérico (puede incluir signo y decimales).

_PATTERNS = {
    # ── Potencia máxima (W) ───────────────────────────────────────────────────
    "Pmax": [
        r'(?:Pmax|P_max|Pmpp|Potencia\s+M[aá]xima?|Maximum\s+Power|Rated\s+Power|STC\s+Power|Peak\s+Power)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*W',
        r'([0-9]{2,3}(?:\.[0-9]+)?)\s*Wp\b',
        r'P\s*[=:]\s*([0-9]+(?:\.[0-9]+)?)\s*W',
    ],

    # ── Tensión de circuito abierto Voc (V) ───────────────────────────────────
    "Voc": [
        r'(?:Voc|V_oc|VOC|Open[- ]?[Cc]ircuit\s+[Vv]oltage|Tensi[oó]n\s+(?:de\s+)?[Cc]ircuito\s+[Aa]bierto)\s*[:\(°]?\s*([0-9]+(?:\.[0-9]+)?)\s*V',
        r'VOC?\s*\(V\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Voc\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],

    # ── Corriente de cortocircuito Isc (A) ───────────────────────────────────
    "Isc": [
        r'(?:Isc|I_sc|ISC|Short[- ]?[Cc]ircuit\s+[Cc]urrent|Corriente\s+(?:de\s+)?[Cc]ortocircuito)\s*[:\(°]?\s*([0-9]+(?:\.[0-9]+)?)\s*A',
        r'ISC?\s*\(A\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Isc\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],

    # ── Tensión en MPP Vmp (V) ────────────────────────────────────────────────
    "Vmp": [
        r'(?:Vmpp|Vmp|V_mp|VMPP|Maximum\s+Power\s+Voltage|Tensi[oó]n\s+(?:de\s+)?[Mm][aá]xima?\s+[Pp]otencia)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*V',
        r'VMPP?\s*\(V\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Vmp\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],

    # ── Corriente en MPP Imp (A) ──────────────────────────────────────────────
    "Imp": [
        r'(?:Impp|Imp|I_mp|IMPP|Maximum\s+Power\s+Current|Corriente\s+(?:de\s+)?[Mm][aá]xima?\s+[Pp]otencia)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*A',
        r'IMPP?\s*\(A\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Imp\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],

    # ── Número de celdas en serie Ns ──────────────────────────────────────────
    "N_s": [
        r'(?:N[oú]mero\s+de\s+c[eé]lulas?|Number\s+of\s+cells?|Cell\s+Number|Cells?\s+[Ss]eries?|Celdas?\s+en\s+[Ss]erie)\s*[:\|]?\s*([0-9]+)',
        r'(?:N_s|Ns|NSA)\s*[:\|=]?\s*([0-9]+)',
        r'\b([0-9]{2,3})\s+(?:cells?|c[eé]lulas?)\b',
    ],

    # ── Coeficiente de temperatura de Voc β (%/°C) ───────────────────────────
    "CoefVoc": [
        r'(?:β|beta|β_Voc|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?Voc|Temperatura\s+Voc|TK\s*Voc)\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:β|beta)V?[Oo][Cc]?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'Voc\s+coeff?\.?\s*[:\|]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
    ],

    # ── Coeficiente de temperatura de Isc α (%/°C) ───────────────────────────
    "CoefIsc": [
        r'(?:α|alpha|α_Isc|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?Isc|Temperatura\s+Isc|TK\s*Isc)\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:α|alpha)I?[Ss][Cc]?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
    ],

    # ── Coeficiente de temperatura de Pmax γ (%/°C) ──────────────────────────
    "CoefPmax": [
        r'(?:γ|gamma|γ_Pmax|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?P(?:max|mpp)|Temperatura\s+P(?:max|mpp)|TK\s*P(?:max|mpp))\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:γ|gamma)P?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'Pmax\s+coeff?\.?\s*[:\|]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
    ],

    # ── NOCT (°C) ─────────────────────────────────────────────────────────────
    "NOCT": [
        r'(?:NOCT|NMOT|Normal(?:ized)?\s+(?:Operating)?\s+Cell\s+Temp(?:erature)?|Temperatura\s+(?:de\s+)?[Oo]peraci[oó]n\s+Normal)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*°?C',
        r'NOCT\s*=\s*([0-9]+(?:\.[0-9]+)?)',
    ],

    # ── Dimensiones (ancho × alto × espesor mm) ───────────────────────────────
    "dimensiones": [
        r'([0-9]{3,4})\s*[×xX*]\s*([0-9]{3,4})\s*[×xX*]\s*([0-9]+)\s*mm',
        r'Dimensions?\s*[:\(]?\s*([0-9]{3,4})\s*[×xX*]\s*([0-9]{3,4})',
    ],
}

# ── Patrones para detectar tecnología ────────────────────────────────────────
_TECH_PATTERNS = [
    (r'(?:Mono(?:crystalline)?[- ]?Si(?:licon)?|Mono-Si|mSi|HJT|Heterojunction|TOPCon|PERC)', "Mono-Si"),
    (r'(?:Poly(?:crystalline)?[- ]?Si(?:licon)?|Multi[- ]?Si|mPoly)', "Poly-Si"),
    (r'(?:CIS|CIGS|Copper\s+Indium)', "CIS"),
    (r'(?:CdTe|Cadmium\s+Telluride)', "CdTe"),
    (r'(?:a-Si|Amorphous\s+Silicon)', "a-Si"),
    (r'(?:Thin\s+[Ff]ilm|Película\s+[Dd]elgada)', "Thin Film"),
]


def _find_first(text: str, patterns: list) -> Optional[float]:
    """Aplica una lista de patrones regex al texto; retorna el primer float encontrado."""
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
    """
    Heurística para el nombre de modelo. Busca patrones tipo
    'CS6R-400MS', 'TSM-DE09', 'JAM72S30-545/MR', etc.
    """
    # Línea que contenga combinación alfanumérica con guiones (modelo típico)
    for line in text.splitlines()[:30]:
        line = line.strip()
        m = re.match(r'^([A-Z]{2,8}[-_][A-Z0-9\-\.]{4,25})$', line)
        if m:
            return m.group(1)
    # Buscar en todo el texto
    m = re.search(r'\b([A-Z]{2,6}[-_][A-Z0-9\-\.]{4,25})\b', text)
    return m.group(1) if m else ""


def _extract_brand(text: str) -> str:
    """Detecta la marca en las primeras 20 líneas del texto."""
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


def _extract_tables(pdf_path_or_bytes) -> str:
    """
    Extrae texto de las tablas del PDF usando pdfplumber.
    Retorna texto plano para aplicar regex.
    """
    if not _HAS_PDF:
        return ""
    extra = []
    try:
        if isinstance(pdf_path_or_bytes, (bytes, bytearray)):
            source = io.BytesIO(pdf_path_or_bytes)
        else:
            source = pdf_path_or_bytes
        with pdfplumber.open(source) as pdf:
            for page in pdf.pages[:4]:   # primeras 4 páginas
                # Texto libre
                raw = page.extract_text() or ""
                extra.append(raw)
                # Tablas (pdfplumber detecta bordes y celdas)
                for table in page.extract_tables():
                    for row in table:
                        extra.append("  |  ".join(str(c or "") for c in row))
    except Exception:
        pass
    return "\n".join(extra)


def extraer_parametros_panel(pdf_bytes: bytes) -> dict:
    """
    Extrae parámetros eléctricos de una ficha técnica PDF de panel FV.

    Retorna un dict con claves:
      modelo, marca, tecnologia,
      Pmax, Voc, Isc, Vmp, Imp,
      N_s, CoefVoc, CoefIsc, CoefPmax,
      NOCT, dimensiones,
      texto_crudo  (para debug/revisión)

    Todos los valores numéricos son float o None si no se encontraron.
    """
    if not _HAS_PDF:
        return {"error": "pdfplumber no instalado. Ejecuta: pip install pdfplumber"}

    texto = _extract_tables(pdf_bytes)

    result = {
        "modelo":      _extract_model_name(texto),
        "marca":       _extract_brand(texto),
        "tecnologia":  _detect_technology(texto),
        "texto_crudo": texto[:4000],   # primeros 4000 chars para debug
    }

    # Extraer valores numéricos con patrones
    for campo, patrones in _PATTERNS.items():
        if campo == "dimensiones":
            # Dimensiones es especial: captura 2 o 3 grupos
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

    # Sanity checks básicos
    if result.get("Voc") and result["Voc"] > 200:
        result["Voc"] = None   # valor absurdo
    if result.get("Isc") and result["Isc"] > 50:
        result["Isc"] = None
    if result.get("Pmax") and result["Pmax"] > 1500:
        result["Pmax"] = None

    return result


def pdf_disponible() -> bool:
    return _HAS_PDF
