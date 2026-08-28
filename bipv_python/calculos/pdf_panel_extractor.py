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
        r'\(\s*Pmax\s*\)\s*\[?W?\]?\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'(?:Pmax|P_max|Pmpp|Potencia\s+M[aá]xima?|Maximum\s+Power|Rated\s+Power|STC\s+Power|Peak\s+Power)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*W',
        r'([0-9]{2,3}(?:\.[0-9]+)?)\s*Wp\b',
        r'P\s*[=:]\s*([0-9]+(?:\.[0-9]+)?)\s*W',
        # SolTech OCR: "Potencia Máxima (Pmax) 520" — sin unidad tras el número
        r'Potencia\s+M[aá]xima\s*\([^)\n]{1,12}\)\s*[:\|]?\s*([0-9]{2,4}(?:\.[0-9]+)?)\b',
    ],
    "Voc": [
        r'\(\s*Voc\s*\)\s*\[?V?\]?\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'(?:Voc|V_oc|VOC|Open[- ]?[Cc]ircuit\s+[Vv]oltage|Tensi[oó]n\s+(?:de\s+)?[Cc]ircuito\s+[Aa]bierto)\s*[:\(°]?\s*([0-9]+(?:\.[0-9]+)?)\s*V',
        r'VOC?\s*\(V\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Voc\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        # SolTech OCR: "Voltaje Circuito Abierto (Voc) 49.8"
        r'(?:Voltaje|Tensi[oó]n)\s+(?:de\s+)?[Cc]ircuito\s+[Aa]bierto\s*\([^)\n]{1,10}\)\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "Isc": [
        r'\(\s*Isc\s*\)\s*\[?A?\]?\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'(?:Isc|I_sc|ISC|Short[- ]?[Cc]ircuit\s+[Cc]urrent|Corriente\s+(?:de\s+)?[Cc]ortocircuito)\s*[:\(°]?\s*([0-9]+(?:\.[0-9]+)?)\s*A',
        r'ISC?\s*\(A\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Isc\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        # SolTech OCR: "Corriente Corto Circuito (Isc) 13.56"
        r'Corriente\s+(?:de\s+)?[Cc]orto\s*[Cc]ircuito\s*\([^)\n]{1,10}\)\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "Vmp": [
        r'\(\s*V(?:mp|mpp)\s*\)\s*\[?V?\]?\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'(?:Vmpp|Vmp|V_mp|VMPP|Maximum\s+Power\s+Voltage|Tensi[oó]n\s+(?:de\s+)?[Mm][aá]xima?\s+[Pp]otencia)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*V',
        r'VMPP?\s*\(V\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Vmp\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        # SolTech OCR: "Voltaje Máximo (Vmp) 42.3" — el subíndice se pierde en OCR
        r'Voltaje\s+M[aá]ximo\s*\([^)\n]{1,10}\)\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "Imp": [
        r'\(\s*I(?:mp|mpp)\s*\)\s*\[?A?\]?\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'(?:Impp|Imp|I_mp|IMPP|Maximum\s+Power\s+Current|Corriente\s+(?:de\s+)?[Mm][aá]xima?\s+[Pp]otencia)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*A',
        r'IMPP?\s*\(A\)\s*[:\|]?\s*([0-9]+(?:\.[0-9]+)?)',
        r'Imp\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        # SolTech OCR: "Corriente Máxima (Imp) 12.31"
        r'Corriente\s+M[aá]xima\s*\([^)\n]{1,10}\)\s*([0-9]+(?:\.[0-9]+)?)',
    ],
    "N_s": [
        r'(?:N[oú]mero\s+de\s+c[eé]lulas?|Number\s+of\s+cells?|Cell\s+Number|Cells?\s+[Ss]eries?|Celdas?\s+en\s+[Ss]erie)\s*[:\|]?\s*([0-9]+)',
        # "No. of cells 132(6×22)" — JA Solar y similares. El número debe venir
        # INMEDIATAMENTE tras la etiqueta: si el OCR degradó el valor (p.ej.
        # "EG 22)") es mejor devolver None que un Ns falso.
        r'No\.?\s*(?:of|de|el)?\s*cells?\s*[:\|]?\s*([0-9]{2,3})\b',
        # \b obligatorio: sin él, "Dimensio ns 2384" hacía match y Ns quedaba en 2384
        r'\b(?:N_s|Ns|NSA)\b\s*[:\|=]?\s*([0-9]+)',
        r'\b([0-9]{2,3})\s+(?:cells?|c[eé]lulas?)\b',
        # SolTech OCR: "N De Celdas 144 (12 x 12)"
        r'N[°º]?\s*[Dd]e\s+[Cc]eldas\s*[:\|]?\s*([0-9]{1,3})\b',
    ],
    "CoefVoc": [
        r'(?:β|beta|β_Voc|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?Voc|Temperatura\s+Voc|TK\s*Voc)\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:β|beta)V?[Oo][Cc]?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'Voc\s+coeff?\.?\s*[:\|]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        # NCL BIPV: "Coeficiente de temperatura para voltaje  -0.28%/ºC"
        r'temperatura\s+para\s+voltaje[^%\n]*?([+-]?[0-9]*\.?[0-9]+)\s*%',
        # SolTech: "Coeficientes de temperatura de Voc TKβ(%/℃) -0.321"
        # (el % viene ANTES del número, dentro de la unidad entre paréntesis)
        r'temp(?:eratura)?\s+de\s+Voc\b[^\n0-9+-]*([+-]?[0-9]+\.[0-9]+)',
        # JA Solar/Trina inglés: "Temperature Coefficient of Voc (β_Voc) -0.250%/°C"
        # (OCR degrada β a "B"; se exige signo y % para no capturar ruido)
        r'Coefficient\s+of\s+Voc[^\n]{0,40}?([+-][0-9]+\.[0-9]+)\s*%',
        r'\(\s*[βB]_?Voc\s*\)[^\n0-9]{0,20}([+-]?[0-9]+\.[0-9]+)\s*%',
        # Hiitio CdTe: "Open circuit voltage temperature coefficient -0.28%°C"
        r'Open\s+circuit\s+voltage\s+temperature\s+coefficient[^\n0-9+-]{0,15}([+-]?[0-9]+\.[0-9]+)\s*%',
        # HJT curtain wall (orden invertido): "Temperature coefficient of open
        # circuit voltage (Voc)-0.24%/℃" (valor pegado al paréntesis, sin espacio)
        r'Temperature\s+coefficient\s+of\s+open[\s-]?circuit\s+voltage[^\n0-9+-]{0,15}([+-]?[0-9]+\.[0-9]+)\s*%',
    ],
    "CoefIsc": [
        r'(?:α|alpha|α_Isc|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?Isc|Temperatura\s+Isc|TK\s*Isc)\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:α|alpha)I?[Ss][Cc]?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        # SolTech: "Coeficientes de temperatura de Isc TKα(%/℃) +0.06"
        r'temp(?:eratura)?\s+de\s+Isc\b[^\n0-9+-]*([+-]?[0-9]+\.[0-9]+)',
        # JA Solar/Trina inglés: "Temperature Coefficient of Isc (α_Isc) +0.045%/°C"
        # (OCR degrada α a "a")
        r'Coefficient\s+of\s+Isc[^\n]{0,40}?([+-][0-9]+\.[0-9]+)\s*%',
        r'\(\s*[αa]_?Isc\s*\)[^\n0-9]{0,20}([+-]?[0-9]+\.[0-9]+)\s*%',
        # Hiitio CdTe: "Short circuit current temperature coefficient +0.04%°C"
        r'Short\s+circuit\s+current\s+temperature\s+coefficient[^\n0-9+-]{0,15}([+-]?[0-9]+\.[0-9]+)\s*%',
        # HJT curtain wall (orden invertido, valor puede venir sin signo):
        # "Temperature coefficient of short-circuit current (Isc)0.04%/℃"
        r'Temperature\s+coefficient\s+of\s+short[\s-]?circuit\s+current[^\n0-9+-]{0,15}([+-]?[0-9]+\.[0-9]+)\s*%',
    ],
    "CoefPmax": [
        r'(?:γ|gamma|γ_Pmax|Coef(?:icient)?\s+(?:of\s+)?(?:Temp(?:erature)?\s+(?:of\s+)?)?P(?:max|mpp)|Temperatura\s+P(?:max|mpp)|TK\s*P(?:max|mpp))\s*[:\(]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'(?:γ|gamma)P?\s*=?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        r'Pmax\s+coeff?\.?\s*[:\|]?\s*([+-]?[0-9]*\.?[0-9]+)\s*%',
        # SolTech: "Coeficientes de temperatura de Pm TKγ(%/℃) -0.214"
        r'temp(?:eratura)?\s+de\s+Pm(?:ax|pp)?\b[^\n0-9+-]*([+-]?[0-9]+\.[0-9]+)',
        # JA Solar/Trina inglés: "Temperature Coefficient of Pmax (γ_Pmp) -0.290%/°C"
        # (OCR degrada γ a "y")
        r'Coefficient\s+of\s+Pmax[^\n]{0,40}?([+-][0-9]+\.[0-9]+)\s*%',
        r'\(\s*[γy]_?Pm(?:p|ax|pp)?\s*\)[^\n0-9]{0,20}([+-]?[0-9]+\.[0-9]+)\s*%',
        # Hiitio CdTe: "Maximum power temperature coefficient -0.29%°C"
        # (se exige "power temperature" pegados para no capturar la fila de Voc)
        r'(?:Maximum\s+)?power\s+temperature\s+coefficient[^\n0-9+-]{0,15}([+-]?[0-9]+\.[0-9]+)\s*%',
    ],
    "NOCT": [
        r'(?:NOCT|NMOT|Normal(?:ized)?\s+(?:Operating)?\s+Cell\s+Temp(?:erature)?|Temperatura\s+(?:de\s+)?[Oo]peraci[oó]n\s+Normal)\s*[:\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*°?C',
        r'NOCT\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        # SolTech OCR: "Temperatura Operativa Nominal Del Módulo 41 +/-2°C"
        r'Temperatura\s+Operativa\s+Nominal[^\n0-9]*([0-9]{2}(?:\.[0-9]+)?)',
        # "NOCT 45±2°C" — tolerancia pegada al valor (OCR: "45+2°C")
        r'NOCT[^\n0-9]{0,10}([0-9]{2})\b',
        # "Rated operating temperature of battery (NOCT) 44±2℃" (traducción china
        # de NOCT; 'battery' aquí es el módulo, no una batería)
        r'Rated\s+operating\s+temperature[^\n0-9]{0,30}([0-9]{2})\b',
    ],
    "Bifacialidad": [
        # "Bifaciality: 80%±5%" / "Bifacialidad 70 ± 5 %" / "Bifacial factor 0.8"(→%)
        r'(?:Bifacialidad|Bifaciality|Bifacial\s+(?:factor|gain|coefficient|Faktor))'
        r'[^0-9\n%]{0,25}([0-9]{1,3}(?:\.[0-9]+)?)\s*%',
        # variante sin % pegado al número: "Bifaciality 80±5 %"
        r'(?:Bifacialidad|Bifaciality)[^0-9\n]{0,25}([0-9]{2,3})\s*(?:±|\+/?-)\s*[0-9]+\s*%',
        # fracción: "Bifacial factor 0.80"
        r'(?:Bifacialidad|Bifaciality|Bifacial\s+factor)[^0-9\n]{0,25}(0\.[0-9]{1,2})\b',
    ],
    "dimensiones": [
        # Espesor puede traer decimales: "1200*600*16.2mm" (vidrio BIPV)
        r'([0-9]{3,4})\s*[×xX*]\s*([0-9]{3,4})\s*[×xX*]\s*([0-9]+(?:\.[0-9]+)?)\s*mm',
        # Con tolerancia ±N mm entre números: "2384±2mm×1303±2mm×33±1mm"
        # (el OCR degrada ± a ":t", "+", "-+", etc.)
        r'([0-9]{3,4})[^\n×xX*]{0,6}?mm\s*[×xX*]\s*([0-9]{3,4})[^\n×xX*]{0,6}?mm\s*[×xX*]\s*([0-9]{2,3})',
        r'Dimensions?\s*[:\(]?\s*([0-9]{3,4})\s*[×xX*]\s*([0-9]{3,4})',
        r'Dimensione?s?\b[^\n0-9]{0,15}([0-9]{3,4})\s*[^0-9×xX*\n]{0,8}(?:mm)?\s*[×xX*]\s*([0-9]{3,4})',
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
        r'|Maximum\s+Power\s+Volt'
        r'|Optimum\s+operating\s+voltage)',
    ],
    "Imp": [
        r'(?:Impp|Imp\b|I[\s_]?mp\b'
        r'|Corriente\s+m[aá]xima\s+potencia'
        r'|Maximum\s+Power\s+Curr'
        r'|Optimum\s+operating\s+current)',
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


# Un número seguido (con o sin unidad corta de por medio: mA, mV, %, ...) de
# "/°C", "/℃" (glifo único, visto en fichas SolTech reales) o "/K" es un
# COEFICIENTE de temperatura, nunca el valor absoluto de un modelo -- aunque
# caiga dentro del rango numérico plausible de Pmax/Voc/Isc/Vmp/Imp. Ver el
# uso en _extract_row_numbers().
_COEF_UNIT_AHEAD_RE = re.compile(r'^\s*[a-zA-Z%µμ]{0,3}\s*(?:/\s*[°ºoO]?\s*[CK]\b|℃)')


def _extract_row_numbers(line: str, from_pos: int = 0) -> list:
    """
    Extrae todos los números de una línea a partir de `from_pos`.
    Maneja valores con unidades embebidas: '327.8W', '124.2V', '3.74A', '1A'.

    Dos filtros para no confundir anotaciones/coeficientes con columnas de
    modelo real -- generalizados a partir de un bug real reportado por el
    usuario con la ficha Suntech STP-410-A72-Pnh-Bifacial (28-ago-2026),
    donde la fila "Coeficiente de temperatura µIsc  5.2 mA/°C  (+0.050 %/°C)"
    se leyó como si fueran 2 columnas de modelo con Isc=5.2 y Isc=0.05,
    sobrescribiendo el Isc real (10.49 A) ya extraído correctamente:

    1. Corta el segmento en el primer '✓' -- fichas con auto-verificación
       cruzada (p.ej. "Potencia máxima calculada (Vmpp × Impp) 410.18 W
       ✓ coincide con 410.0 Wp") re-citan el mismo valor dentro de la nota.

    2. Descarta cualquier número seguido de una unidad de coeficiente por
       grado ("mA/°C", "V/°C", "%/°C", "/K", con o sin el símbolo de grado,
       con o sin unidad corta antepuesta) -- no es específico del caso ✓:
       una fila de coeficiente SIN checkmark ("Isc temp. coefficient 5.2
       mA/°C") tiene el mismo riesgo si alguna vez queda dentro del barrido
       de una tabla multi-modelo detectada por códigos de modelo reales (no
       por el fallback numérico que ya corta en ✓). Pedido explícito del
       usuario tras el hallazgo: "revisa la lógica del extractor para que
       no confunda coeficientes de temperatura con valores absolutos... es
       un error que se puede repetir con cualquier otra ficha".
    """
    segmento = line[from_pos:]
    corte = segmento.find("✓")
    if corte != -1:
        segmento = segmento[:corte]
    numeros = []
    for m in re.finditer(r'([0-9]+(?:\.[0-9]+)?)', segmento):
        if _COEF_UNIT_AHEAD_RE.match(segmento[m.end():]):
            continue
        numeros.append(float(m.group(1)))
    return numeros


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
    # Transparencia: para vidrio BIPV (fila puede venir reparada CON etiqueta)
    # "transp\." cubre el encabezado abreviado "Transp." (Solar First, tabla
    # multi-modelo por fila) -- exige el punto para no matchear otras
    # palabras que empiecen "transp" (p.ej. "transporte").
    "Transparencia": re.compile(r'transparen|transp\.', re.I | re.UNICODE),
}


# ── Mapeo fila-vacía → campo (tablas multi-modelo que alternan labeled/unlabeled rows) ──
# Definido a nivel de módulo para no redefinirlo en cada iteración de tabla.
_EMPTY_FOLLOWS: dict = {"Pmax": "Voc", "Isc": "Vmp", "Imp": "Transparencia"}


def _nums_in(s: str) -> list:
    """Extrae todos los números flotantes de una cadena de texto."""
    return [float(m) for m in re.findall(r'[0-9]+(?:\.[0-9]+)?', s)]


# ── Patrones para tablas auxiliares de 1 fila: CoefVoc / CoefIsc / CoefPmax / NOCT ──
_AUX_LABEL_RE: dict = {
    # etiqueta → campo → (regex_etiqueta, regex_valor)
    "CoefVoc":  (
        re.compile(r'coef[^%\n]*?voltaje|coef[^%\n]*?voc|temp[^%\n]*?voc|β\s*[Vv]oc', re.I),
        re.compile(r'([+-]?[0-9]+\.?[0-9]*)\s*%'),
    ),
    "CoefIsc":  (
        re.compile(r'coef[^%\n]*?corriente|coef[^%\n]*?isc|temp[^%\n]*?isc|α\s*[Ii]sc', re.I),
        re.compile(r'([+-]?[0-9]+\.?[0-9]*)\s*%'),
    ),
    "CoefPmax": (
        re.compile(r'coef[^%\n]*?p(?:max|mpp)|temp[^%\n]*?p(?:max|mpp)|γ\s*[Pp]', re.I),
        re.compile(r'([+-]?[0-9]+\.?[0-9]*)\s*%'),
    ),
    "NOCT": (
        re.compile(r'noct|nominal\s+operating\s+cell|temperatura\s+nominal\s+de\s+operaci', re.I),
        re.compile(r'([0-9]+\.?[0-9]*)\s*[°º]?\s*[Cc]\b'),
    ),
}


def _extract_tables_reparadas(page) -> list:
    """
    Como page.extract_tables(), pero repara celdas None recuperando su texto
    con un crop de la página en el rectángulo columna×fila.

    pdfplumber pierde celdas (devuelve None) cuando la grilla de una fila no
    define el borde de una columna — típico en filas SIN etiqueta de tablas
    multi-modelo, donde la última columna queda como None aunque el valor sí
    existe en el PDF (ej. filas de Voc/Vmp/Transparencia del brochure NCL).
    """
    try:
        found = page.find_tables() or []
    except Exception:
        return page.extract_tables() or []
    tablas: list = []
    for t in found:
        try:
            data = t.extract()
        except Exception:
            continue
        if not data:
            continue
        # Fila de referencia: la que tenga más celdas bbox definidas
        try:
            ref = max(t.rows, key=lambda r: sum(1 for c in r.cells if c))
            ref_cells = ref.cells
            for ri, trow in enumerate(t.rows):
                if ri >= len(data) or not data[ri]:
                    continue
                # Solo reparar filas MAYORMENTE completas (≥ mitad de celdas con
                # dato). Filas de encabezado o con celdas fusionadas (colspan)
                # tienen muchas None legítimas — croparlas inyecta texto basura
                # (fragmentos de la celda fusionada vecina).
                _presentes = sum(1 for c in data[ri] if c not in (None, ""))
                # Techo verdadero de la mitad: en filas de ancho impar (ej. 5
                # columnas) exigir 3 presentes, no 2 (floor dejaría pasar filas
                # dispersas/fusionadas que no deben repararse).
                if _presentes < max(2, (len(data[ri]) + 1) // 2):
                    continue
                for ci, cellbox in enumerate(trow.cells):
                    if (
                        ci < len(data[ri])
                        and cellbox is None
                        and data[ri][ci] is None
                        and ci < len(ref_cells)
                        and ref_cells[ci] is not None
                    ):
                        x0, _, x1, _ = ref_cells[ci]
                        top, bottom = trow.bbox[1], trow.bbox[3]
                        try:
                            txt = page.crop((x0, top, x1, bottom)).extract_text()
                        except Exception:
                            txt = None
                        # Sanidad: aceptar solo texto de UNA línea y corto.
                        # Celdas fusionadas (colspan) cropeadas producen texto
                        # multilínea o fragmentos largos de la celda vecina —
                        # eso es basura y no debe inyectarse como valor.
                        if txt:
                            txt = txt.strip()
                            if txt and "\n" not in txt and len(txt) <= 60:
                                data[ri][ci] = txt
        except Exception:
            pass
        tablas.append(data)
    return tablas


def _extract_aux_table_shared(pdf_bytes: bytes) -> dict:
    """
    Escanea tablas de 1 fila con 2 celdas (label | valor) en busca de
    coeficientes de temperatura y NOCT que no están en la tabla multi-modelo.

    Devuelve dict vacío si no encuentra nada o si pdfplumber no está disponible.
    Esto evita el problema de que pdfplumber rompa en varias líneas la celda de
    valor, haciendo que el patrón regex sobre texto plano no encuentre el número.
    """
    shared: dict = {}
    if not _HAS_PDF:
        return shared
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for tbl in _extract_tables_reparadas(page):
                    if not tbl:
                        continue
                    for row in tbl:
                        if not row or len(row) < 2:
                            continue
                        cells = [
                            unicodedata.normalize("NFC", str(c or "")).strip()
                            for c in row
                        ]
                        # Solo filas con exactamente 2 celdas no vacías
                        non_empty = [c for c in cells if c]
                        if len(non_empty) != 2:
                            continue
                        label_cell, val_cell = non_empty[0], non_empty[1]
                        for field, (lbl_re, val_re) in _AUX_LABEL_RE.items():
                            if field in shared:
                                continue        # ya encontrado
                            if lbl_re.search(label_cell):
                                m = val_re.search(val_cell)
                                if m:
                                    v = float(m.group(1))
                                    if field == "NOCT" and not (30 <= v <= 80):
                                        continue
                                    shared[field] = v
                                    break
    except Exception:
        pass
    return shared


def _dedupe_model_names(model_names: list, por_columna: list) -> list:
    """
    Algunas fichas repiten el MISMO código de modelo para varias variantes de
    potencia (p.ej. HL-XWB13 en 3 columnas: 125 W / 130 W / 135 W). Si hay
    nombres duplicados, se distinguen con la Pmax de su columna:
    'HL-XWB13 (135W)'. Si tampoco hay Pmax, se numera la variante.
    """
    if len(set(model_names)) == len(model_names):
        return model_names
    counts: dict = {}
    for m in model_names:
        counts[m] = counts.get(m, 0) + 1
    nuevos: list = []
    vistos: set = set()
    for i, m in enumerate(model_names):
        nombre = m
        if counts[m] > 1:
            pm = por_columna[i].get("Pmax") if i < len(por_columna) else None
            if pm is not None:
                pot = int(pm) if float(pm).is_integer() else pm
                nombre = f"{m} ({pot}W)"
            else:
                nombre = f"{m} (var. {i + 1})"
        if nombre in vistos:  # colisión residual (misma Pmax duplicada)
            nombre = f"{nombre} #{i + 1}"
        vistos.add(nombre)
        nuevos.append(nombre)
    return nuevos


def _detectar_tabla_modelos_por_fila(table: list) -> dict:
    """
    Extrae modelos y parámetros de una tabla en orientación "por fila": cada
    FILA es un modelo distinto (no cada COLUMNA, como en
    _extract_multimodel_from_tables() Paso 1) -- formato típico de fichas de
    familia con muchas variantes en una sola tabla vertical, p.ej.:
        Modelo   | Transp. | Pmax | Voc   | Vmpp   | Isc    | Impp
        ST1-72   | 10%     | 72 W | 116 V | 90.5 V | 0.88 A | 0.8 A
        ST1-64   | 20%     | 64 W | 116 V | 90.5 V | 0.78 A | 0.71 A
        ...

    A diferencia del Paso 1 (que exige códigos de modelo "largos" vía
    _MODEL_CODE_RE, ≥3 caracteres tras el guion -- pensado para nombres tipo
    "CS6R-400MS"), aquí el nombre de modelo se toma literalmente de la
    primera columna bajo el encabezado "Modelo"/"Model", sin exigir ningún
    formato de código -- el propio encabezado ya desambigua cuál columna es
    el nombre. Cubre códigos cortos como "ST1-72" (Solar First, solo 2
    caracteres tras el guion) que _MODEL_CODE_RE rechaza.

    Encontrado auditando por qué el extractor no identificaba NINGÚN
    parámetro en la ficha Solar First ST1/ST2 (28-ago-2026, reportado por el
    usuario con el CSV de verificación de la UI, los 5 campos obligatorios en
    rojo): pdfplumber SÍ parseaba la tabla perfecto (confirmado con
    _dump_tables_pdfplumber -- 11 filas limpias, columnas correctas), el bug
    era que ningún criterio existente la reconocía como tabla multi-modelo
    (ni el de Paso 1, por los códigos cortos; ni el heurístico de texto plano
    de _extract_multimodel_panel(), porque la etiqueta "Pmax" vive en la fila
    de encabezado, separada de los valores por N filas -- no en la misma
    línea que exige ese heurístico).
    """
    EMPTY: dict = {"modelos_detectados": [], "valores_por_modelo": {}}
    if not table or len(table) < 3:
        return EMPTY

    header_idx = -1
    col_field: dict = {}   # índice de columna -> nombre de campo
    for ri, row in enumerate(table):
        if not row:
            continue
        cells = [unicodedata.normalize("NFC", str(c or "")).strip() for c in row]
        if not cells or cells[0].lower() not in ("modelo", "model"):
            continue
        _map: dict = {}
        for ci, cell in enumerate(cells[1:], start=1):
            for field, pat in _TABLE_LABEL_RE.items():
                if pat.search(cell):
                    _map[ci] = field
                    break
        if len(_map) >= 2:   # al menos 2 campos reconocidos además de "Modelo"
            header_idx = ri
            col_field = _map
            break

    if header_idx == -1:
        return EMPTY

    model_names: list = []
    valores_list: list = []
    for row in table[header_idx + 1:]:
        if not row:
            break
        cells = [unicodedata.normalize("NFC", str(c or "")).strip() for c in row]
        if not cells or not cells[0]:
            break   # fila vacía = fin de la tabla (siguiente sección de la ficha)
        valores: dict = {}
        for ci, field in col_field.items():
            if ci >= len(cells):
                continue
            lo, hi = _MULTIMODEL_PLAUSIBLE.get(field, (0.0, 1e9))
            for v in _nums_in(cells[ci]):
                if lo <= v <= hi:
                    valores[field] = v
                    break
        if "Pmax" not in valores:
            continue   # fila sin Pmax reconocible no es un modelo real
        model_names.append(cells[0])
        valores_list.append(valores)

    if len(model_names) < 2:
        return EMPTY

    model_names = _dedupe_model_names(model_names, valores_list)
    return {
        "modelos_detectados": model_names,
        "valores_por_modelo": dict(zip(model_names, valores_list)),
    }


def _extract_multimodel_from_tables(pdf_bytes: bytes) -> dict:
    """
    Extrae modelos y parámetros directamente de tablas estructuradas con pdfplumber.

    Estrategia: busca la fila donde ≥2 celdas son códigos de modelo.
    Luego asigna a cada columna el valor de las filas de parámetros (Pmax, Voc, …).
    Este método es más robusto que el basado en texto plano cuando pdfplumber
    fragmenta columnas en líneas separadas.

    Si esa estrategia (orientación "por columna": modelos en el encabezado,
    campos en las filas) no encuentra nada, se intenta la orientación "por
    fila" (modelos en las filas, campos en el encabezado) vía
    _detectar_tabla_modelos_por_fila() -- ver su docstring para el caso real
    que la motivó.
    """
    EMPTY: dict = {"modelos_detectados": [], "valores_por_modelo": {}, "shared_values": {}}
    if not _HAS_PDF:
        return EMPTY
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in _extract_tables_reparadas(page):
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
                        # Elegir la fila con MÁS códigos de modelo (no la primera
                        # con ≥2): filas de encabezado con celdas fusionadas pueden
                        # contener algunos códigos sueltos y ganarle a la fila real.
                        if len(codes) >= 2 and len(codes) > len(model_names):
                            model_row_idx = ri
                            model_col_indices = [ci for ci, _ in codes]
                            model_names = [c for _, c in codes]

                    if model_row_idx == -1 or len(model_names) < 2:
                        # Orientación "por columna" no encontró nada -- intentar
                        # "por fila" (ver _detectar_tabla_modelos_por_fila()).
                        por_fila = _detectar_tabla_modelos_por_fila(table)
                        if len(por_fila["modelos_detectados"]) >= 2:
                            por_fila["shared_values"] = _extract_aux_table_shared(pdf_bytes)
                            return por_fila
                        continue

                    n = len(model_names)
                    # Lista posicional: soporta códigos de modelo duplicados
                    por_columna: list = [{} for _ in range(n)]

                    # _EMPTY_FOLLOWS es constante — definida a nivel de módulo arriba.
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
                            # Fila con etiqueta desconocida → romper la cadena de contexto
                            # para evitar que la siguiente fila vacía herede el último
                            # campo válido (p.ej. R8 "Estructura vidrio" no reconocido
                            # no debe dejar que R9 vacía se trate como otra Transparencia).
                            if label_nfc:
                                last_field_hit = None
                            continue

                        # Actualizar contexto solo cuando la fila tiene etiqueta real
                        if label_nfc:
                            last_field_hit = field_hit

                        lo, hi = _MULTIMODEL_PLAUSIBLE[field_hit]

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
                            por_columna[mi][field_hit] = v

                    # Considerar exitoso si al menos Pmax fue extraído
                    if any("Pmax" in v for v in por_columna):
                        model_names = _dedupe_model_names(model_names, por_columna)
                        return {
                            "modelos_detectados": model_names,
                            "valores_por_modelo": {
                                m: por_columna[i] for i, m in enumerate(model_names)
                            },
                            "shared_values": _extract_aux_table_shared(pdf_bytes),
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
    # Lista posicional: soporta códigos de modelo duplicados (variantes de potencia)
    por_columna: list = [{} for _ in range(n)]

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
                    for i, val in enumerate(vals[:n]):
                        por_columna[i][field] = val
                    break
                elif len(vals) >= 2:
                    # Asignación parcial (menos valores que modelos)
                    for i, val in enumerate(vals[:n]):
                        por_columna[i][field] = val
                    break
            else:
                continue
            break  # campo asignado; pasar al siguiente

    model_names = _dedupe_model_names(model_names, por_columna)
    return {
        "modelos_detectados": model_names,
        "valores_por_modelo": {m: por_columna[i] for i, m in enumerate(model_names)},
    }


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
    # Prioridad 1: fichas con columna "Modelo" — el código aparece tras la línea
    # "(Rendimiento a STC:...)": p.ej. SolTech "SMF 520J - 12X 12UW".
    # Es más confiable que buscar códigos sueltos (el OCR genera basura tipo
    # "m4Zm-2700" que de otro modo ganaría).
    m = re.search(
        r'\(Rendimiento\s+a\s+STC[^)\n]*\)\s*([A-Z0-9][A-Za-z0-9 \-\./]{3,40}?)\s*$',
        text, re.IGNORECASE | re.MULTILINE,
    )
    if m:
        return m.group(1).strip()
    # Prioridad 2: código de familia tipo "JAM66D46 LB", "LR5-72HTH", "TSM-DE21"
    # en las primeras líneas (título de la ficha). Se filtran líneas de pie de
    # página ("Version No.", "Global-EN", e-mail, web) que contienen códigos
    # basura tipo "EN-20250709C".
    _JUNK_LINE = re.compile(r'version\s*no|global[-_]|e-?mail|www\.|http|@', re.I)
    for line in text.splitlines()[:30]:
        line = line.strip()
        if _JUNK_LINE.search(line):
            continue
        # "JAM 66D46 LB" (OCR mete espacios) o "JAM66D46-LB"
        m = re.match(r'^([A-Z]{2,5}\s?[0-9]{2}[A-Z][0-9]{2}[\s\-][A-Z]{1,3})\b', line)
        if m:
            return m.group(1).replace(" ", "")
        m = re.match(r'^([A-Z]{2,8}[-_][A-Z0-9\-\.]{4,25})$', line)
        if m:
            return m.group(1)
    for line in text.splitlines():
        if _JUNK_LINE.search(line):
            continue
        m = re.search(r'\b([A-Z]{2,6}[-_][A-Z0-9\-\.]{4,25})\b', line)
        if m:
            return m.group(1)
    return ""


def _extract_brand(text: str) -> str:
    BRANDS = [
        "Canadian Solar", "Trina Solar", "LONGi", "JA Solar", "Jinko",
        "Hanwha", "Q CELLS", "REC", "SolarWorld", "Yingli", "Risen",
        "CSUN", "Seraphim", "SunPower", "Panasonic", "LG", "BYD",
        "Hyundai", "Mitsubishi", "Sharp", "Kyocera", "GreenBrilliance",
        "Solartech Universal", "Vikram", "Waaree", "Adani", "Axitec",
        "Aleo", "IBC Solar", "Solarwatt", "SolTech", "NCL", "Solar First",
        "Suntech", "Hiitio",
    ]
    snippet = "\n".join(text.splitlines()[:20])
    for b in BRANDS:
        # \b...\b: sin límites de palabra, marcas cortas (LG, REC, NCL) hacen
        # falso positivo dentro de palabras españolas que las contienen como
        # substring (p.ej. "película delgada" -> "LG" via "de-LG-ada").
        # Encontrado auditando la ficha Solar First (28-ago-2026): CdTe
        # "película delgada" se detectaba como marca "LG".
        if re.search(r'\b' + re.escape(b) + r'\b', snippet, re.IGNORECASE):
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


# ── Fallback genérico de coeficientes de temperatura (#166) ─────────────────
# Cada fabricante redacta el label en otro orden ("X temperature coefficient",
# "Temperature coefficient of X", "Coeficiente de temperatura de X", …). En vez
# de una regex por redacción, se detecta la LÍNEA que menciona "coeficiente de
# temperatura" + la magnitud (en cualquier orden) y se toma el valor en %.
_COEF_LINE_RE = re.compile(
    r'temp(?:erature|eratura)?\.?\s+coefficient'      # "temperature coefficient"
    r'|coeficientes?\s+de\s+temp(?:eratura)?'         # "coeficiente de temperatura"
    r'|temperature\s+coeff?',                         # "temperature coeff."
    re.IGNORECASE,
)
# Orden importa: Voc/Isc antes que Pmax (cuyo keyword "power" es más genérico)
_COEF_FIELD_KEYWORDS = [
    ("CoefVoc",  re.compile(r'\bVoc\b|open[\s-]?circuit\s+voltage'
                            r'|circuito\s+abierto|tensi[oó]n\s+de\s+vac[ií]o', re.IGNORECASE)),
    ("CoefIsc",  re.compile(r'\bIsc\b|short[\s-]?circuit\s+current'
                            r'|corto[\s-]?circuito', re.IGNORECASE)),
    ("CoefPmax", re.compile(r'\bP\s*max\b|\bPmpp?\b|maximum\s+power|\bpower\b'
                            r'|potencia', re.IGNORECASE)),
]
# Rango físico plausible de coeficientes (%/°C). Voc/Pmax son negativos
# (~-0.2 a -0.5); Isc es pequeño y puede ser positivo.
_COEF_PLAUSIBLE = {
    "CoefVoc":  (-1.0, 0.0),
    "CoefPmax": (-1.0, 0.0),
    "CoefIsc":  (-0.2, 0.2),
}
_COEF_VALUE_RE = re.compile(r'(±\s*)?([+-]?[0-9]+(?:\.[0-9]+)?)\s*%')


# ── Ns desde conteo de semiceldas (#67) ─────────────────────────────────────
# Fichas half-cut suelen decir "28 half-piece", "144 half cells", "132 semiceldas".
# El Motor IV necesita las celdas EN SERIE: normalmente la mitad del conteo
# (dos cadenas en paralelo). Se usa el Voc para decidir entre total y mitad.
_NS_HALFCELL_RES = [
    # Exigir contexto de CONTEO de celdas: "28 half-piece", "144 half cells",
    # "120 half-cut cells". 'half-cut' solo cuenta si le sigue 'cells' para no
    # capturar marketing tipo "5 half-cut technology".
    re.compile(r'([0-9]{1,3})\s*half[\s-]?(?:pieces?|cells?)\b', re.IGNORECASE),
    re.compile(r'([0-9]{1,3})\s*half[\s-]?cut\s+(?:solar\s+)?cells?\b', re.IGNORECASE),
    re.compile(r'([0-9]{1,3})\s*(?:medias?\s+celdas|semi[\s-]?celdas)', re.IGNORECASE),
]


def _ns_desde_semiceldas(texto: str, result: dict) -> None:
    """
    Rellena N_s cuando la ficha declara el conteo de semiceldas (half-cut).
    Por defecto usa la mitad (dos strings en paralelo); si el Voc extraído
    indica que TODAS van en serie (Voc/total plausible), usa el total.
    Marca `_ns_de_semiceldas` para que el guard de plausibilidad 10–300 no
    descarte valores legítimamente bajos (tejas/BIPV: Ns=14).
    """
    if result.get("N_s") is not None:
        return
    for pat in _NS_HALFCELL_RES:
        m = pat.search(texto)
        if not m:
            continue
        total = int(m.group(1))
        if total < 8:      # conteos reales van de 28 (tejas BIPV) a 156; <8 es ruido
            return
        mitad = total // 2 if total % 2 == 0 else total
        ns = mitad
        voc = result.get("Voc")
        if voc:
            # Voc/celda plausible para silicio: 0.4–1.0 V
            ok_total = 0.4 <= voc / total <= 1.0
            ok_mitad = 0.4 <= voc / mitad <= 1.0
            if ok_total and not ok_mitad:
                ns = total          # todas las semiceldas en serie
        result["N_s"] = float(ns)
        result["_ns_de_semiceldas"] = True
        return


def _coef_fallback(texto: str, result: dict) -> None:
    """
    Rellena CoefVoc/CoefIsc/CoefPmax aún None analizando línea por línea,
    sin depender del orden de redacción del fabricante. Solo acepta valores
    dentro del rango físico plausible y descarta tolerancias (±).
    """
    faltan = {k for k in ("CoefVoc", "CoefIsc", "CoefPmax") if result.get(k) is None}
    if not faltan:
        return
    for line in texto.splitlines():
        if not _COEF_LINE_RE.search(line):
            continue
        campo = next((c for c, pat in _COEF_FIELD_KEYWORDS
                      if c in faltan and pat.search(line)), None)
        if campo is None:
            continue
        lo, hi = _COEF_PLAUSIBLE[campo]
        for m in _COEF_VALUE_RE.finditer(line):
            if m.group(1):          # "±0.05%" es tolerancia, no el coeficiente
                continue
            v = float(m.group(2))
            if lo <= v <= hi and v != 0.0:
                result[campo] = v
                faltan.discard(campo)
                break
        if not faltan:
            return


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
    # Fallback genérico: coeficientes con redacciones no vistas antes (#166).
    # Los patrones específicos de _PATTERNS siempre tienen prioridad.
    _coef_fallback(texto, result)
    # Ns desde conteo de semiceldas en fichas half-cut (#67)
    _ns_desde_semiceldas(texto, result)
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
    # Ns plausible: 10–300 celdas en serie (2384 era la dimensión del panel).
    # Excepción: Ns derivado de conteo de semiceldas (#67) puede ser bajo
    # legítimamente (tejas/BIPV: 28 half-piece → Ns=14).
    if (result.get("N_s") and not result.get("_ns_de_semiceldas")
            and not (10 <= result["N_s"] <= 300)):
        result["N_s"] = None
    # Bifacialidad: aceptar fracción (0.80 → 80%) y descartar valores implausibles
    _bif = result.get("Bifacialidad")
    if _bif is not None:
        if 0 < _bif <= 1.0:
            _bif *= 100.0
        result["Bifacialidad"] = _bif if 30.0 <= _bif <= 100.0 else None

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

    # Aplicar valores compartidos (CoefVoc, CoefIsc, CoefPmax, NOCT) extraídos
    # de tablas auxiliares de 1 fila. Estos no están en la tabla multi-modelo y
    # el extractor de texto falla cuando pdfplumber rompe la celda en líneas.
    for _k, _v in mm.get("shared_values", {}).items():
        if result.get(_k) is None:
            result[_k] = _v

    # ── Complemento OCR para PDFs "mixtos" ────────────────────────────────────
    # Algunas fichas (p. ej. Hiitio CdTe) tienen una capa de texto digital escasa
    # (superan _MIN_TEXT_CHARS) pero las tablas de coeficientes/dimensiones son
    # imágenes. Si faltan campos clave y hay OCR, se complementa SIN sobrescribir
    # lo ya extraído del texto digital.
    # Bifacialidad NO dispara el OCR por sí sola (falta legítimamente en paneles
    # monofaciales), pero sí se rellena si el OCR corre por otros faltantes.
    _CAMPOS_GATILLO = ("CoefVoc", "CoefIsc", "CoefPmax", "NOCT", "N_s",
                       "dimensiones")
    _CAMPOS_COMPLEMENTO = _CAMPOS_GATILLO + ("Bifacialidad",)
    if not uso_ocr and _HAS_OCR:
        gatillo = [k for k in _CAMPOS_GATILLO if result.get(k) is None]
        if gatillo or not result.get("tecnologia"):
            texto_ocr = _ocr_pdf(pdf_bytes)
            if len(texto_ocr.strip()) >= _MIN_TEXT_CHARS:
                vals_ocr = _apply_patterns(texto_ocr)
                for k in _CAMPOS_COMPLEMENTO:
                    if result.get(k) is None and vals_ocr.get(k) is not None:
                        result[k] = vals_ocr[k]
                        result["uso_ocr"] = True  # se usó OCR como complemento
                        # Propagar el origen del Ns para que el sanity check
                        # de abajo no anule valores bajos legítimos (#67)
                        if k == "N_s" and vals_ocr.get("_ns_de_semiceldas"):
                            result["_ns_de_semiceldas"] = True
                if not result.get("tecnologia"):
                    tec_ocr = _detect_technology(texto_ocr)
                    if tec_ocr:
                        result["tecnologia"] = tec_ocr
                        result["uso_ocr"] = True
                # Sanity checks sobre lo complementado (mismos límites del paso 3)
                if (result.get("N_s") and not result.get("_ns_de_semiceldas")
                        and not (10 <= result["N_s"] <= 300)):
                    result["N_s"] = None
                _bif = result.get("Bifacialidad")
                if _bif is not None:
                    if 0 < _bif <= 1.0:
                        _bif *= 100.0
                    result["Bifacialidad"] = _bif if 30.0 <= _bif <= 100.0 else None

    # Volcado de tablas pdfplumber para diagnóstico (se muestra en el expander de debug)
    result["_debug_tables"] = _dump_tables_pdfplumber(pdf_bytes)

    # Limpiar flags internos: la UI/catálogo solo deben ver campos de dominio
    result.pop("_ns_de_semiceldas", None)

    return result


def pdf_disponible() -> bool:
    return _HAS_PDF


def ocr_disponible() -> bool:
    return _HAS_OCR
