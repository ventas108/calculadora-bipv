"""
pdf_bateria_extractor.py — Extrae parámetros de fichas técnicas PDF de baterías.

Mismo espíritu que pdf_panel_extractor / pdf_inversor_extractor: texto digital
primero (pdftotext -layout preserva columnas), OCR como último recurso, y
None antes que un valor falso.

Las fichas de bancos de baterías suelen traer DOS tablas: la del MÓDULO
(ej. 14.336 kWh / 51.2 V) y la del RACK/GABINETE completo (ej. 215 kWh / 768 V).
Lo que va al catálogo es el rack: por eso, para cada campo se elige la fila
del label con MÁS valores (la tabla multi-modelo), y en fichas de un solo
modelo se toma el valor MÁS GRANDE (rack > módulo siempre).

Multi-modelo: la fila de cabecera trae ≥2 códigos de modelo (BR172R, BC75T…).
Cada código se asigna al valor de columna más cercano POR POSICIÓN DE
CARACTERES en el texto -layout — así los pares tipo "BC75T BR75T" que
comparten columna heredan el mismo valor.

Función principal:
  extraer_parametros_bateria(pdf_bytes: bytes) -> dict
    {
      "fabricante": str, "quimica": str,
      "ciclos": float|None, "c_rate": float|None,
      "dod_pct": float|None, "rte_pct": float|None, "garantia_anos": float|None,
      "modelos_detectados": [str, ...],
      "valores_por_modelo": {
          modelo: {"capacidad_kWh", "capacidad_Ah", "voltaje_V",
                   "potencia_kW", "potencia_estimada"}
      },
      "es_escaneado": bool, "uso_ocr": bool, "ocr_disponible": bool,
      "texto_crudo": str,
    }
"""

import re
from typing import Optional

# Reutilizar la infraestructura de texto/OCR del extractor de paneles
from calculos.pdf_panel_extractor import (
    _extract_text_pdftotext,
    _extract_text_pdfplumber,
    _ocr_pdf,
    _HAS_PDF,
    _HAS_OCR,
    _MIN_TEXT_CHARS,
)

# ── Detección de códigos de modelo ───────────────────────────────────────────
# "BR215R", "BC75T", "US5000", "LUNA2000-5-S0", "SBR128"… Debe contener dígitos.
_MODEL_CODE_RE = re.compile(r'\b([A-Z]{2,6}[0-9]{2,5}(?:[A-Z0-9\-]{0,8}[A-Z0-9])?)\b')

# Siglas técnicas que el patrón anterior confunde con modelos
_JUNK_CODES = re.compile(
    r'^(?:IP\d+|UN\d+|IEC\d+|UL\d*|RS\d+|CAN\d*|\d+S\d+P'
    r'|CE|CB|BMS|BPU|SOC|LCD|MSDS|ROHS|STC|NOCT|PV\d*|AC\d*|DC\d*)$'
)

# ── Filas per-modelo: (campo, regex_label, regex_valor, rango_plausible) ─────
_ROW_SPECS = [
    ("capacidad_kWh",
     re.compile(r'Energ[ií]a\s+(?:nominal|utilizable|total)|(?:Rated|Usable|Nominal)\s+Energy', re.I),
     re.compile(r'([0-9]+(?:\.[0-9]+)?)\s*kWh', re.I),
     (0.5, 5000.0)),
    ("capacidad_Ah",
     re.compile(r'Capacidad\s+nominal|(?:Rated|Nominal)\s+Capacity', re.I),
     re.compile(r'([0-9]+(?:\.[0-9]+)?)\s*Ah\b', re.I),
     (5.0, 20000.0)),
    ("voltaje_V",
     re.compile(r'(?:Voltaje|Tensi[oó]n)\s+nominal|Nominal\s+Voltage', re.I),
     re.compile(r'([0-9]+(?:\.[0-9]+)?)\s*V\b'),
     (10.0, 1500.0)),
]
# NOTA: el peso (kg) se descartó a propósito — en fichas multi-modelo la fila
# de pesos queda desalineada respecto a las columnas de modelos (números más
# cortos → centros corridos) y asignaba el peso del modelo vecino.

# Filas que NO deben confundirse con las anteriores
_ROW_EXCLUDE = re.compile(r'Rango\s+de\s+voltaje|Voltage\s+Range|densidad|density', re.I)


def _codigos_en_linea(linea: str) -> list:
    """[(posicion_centro, codigo), ...] de códigos de modelo válidos en la línea."""
    out = []
    for m in _MODEL_CODE_RE.finditer(linea):
        c = m.group(1)
        if _JUNK_CODES.match(c) or not re.search(r'\d', c):
            continue
        out.append(((m.start() + m.end()) / 2.0, c))
    return out


def _detectar_modelos(lines: list) -> list:
    """
    Busca la línea de cabecera con MÁS códigos de modelo (≥2).
    Retorna [(pos, codigo), ...] o [] si la ficha parece de un solo modelo.
    """
    best: list = []
    for linea in lines:
        codes = _codigos_en_linea(linea)
        # Deduplicar conservando orden (un código puede repetirse en la línea)
        vistos, unicos = set(), []
        for pos, c in codes:
            if c not in vistos:
                vistos.add(c)
                unicos.append((pos, c))
        if len(unicos) >= 2 and len(unicos) > len(best):
            best = unicos
    return best


def _mejor_fila(lines: list, lbl_re, val_re, lo: float, hi: float) -> list:
    """
    De todas las líneas cuyo label coincide, retorna la lista de matches
    [(pos, valor), ...] de la línea con MÁS valores plausibles.
    (La tabla del rack multi-modelo siempre le gana a la del módulo.)
    """
    best: list = []
    for linea in lines:
        if _ROW_EXCLUDE.search(linea) or not lbl_re.search(linea):
            continue
        vals = []
        for m in val_re.finditer(linea):
            try:
                v = float(m.group(1))
            except ValueError:
                continue
            if lo <= v <= hi:
                vals.append((m.start(), v))
        if len(vals) > len(best):
            best = vals
    return best


def _max_todas_filas(lines: list, lbl_re, val_re, lo: float, hi: float):
    """
    Para fichas de UN solo modelo: recorre TODAS las líneas cuyo label
    coincide (módulo Y rack pueden compartir label con 1 valor cada una)
    y retorna el valor plausible MÁS GRANDE — el rack siempre supera al
    módulo en kWh/V/Ah, así que el máximo global es el del banco completo.
    """
    mejor = None
    for linea in lines:
        if _ROW_EXCLUDE.search(linea) or not lbl_re.search(linea):
            continue
        for m in val_re.finditer(linea):
            try:
                v = float(m.group(1))
            except ValueError:
                continue
            if lo <= v <= hi and (mejor is None or v > mejor):
                mejor = v
    return mejor


# Distancia máxima (en caracteres) entre el código del modelo y su columna
_MAX_DIST_COL = 45

# ── Formato "bloques verticales" (típico de OCR en fichas escaneadas) ────────
# El OCR de fichas tipo Felicity lista los labels en un bloque y luego CADA
# modelo con sus valores debajo:
#   FLA48100-EU        ← línea con SOLO el código del modelo
#   5.12kWh            ← energía nominal
#   51.2V              ← voltaje nominal
#   44.8-57.6V         ← rango (se ignora: trae '-')
#   100A               ← corriente continua máx (la primera A del bloque)
#   ...
_VB_KWH_RE = re.compile(r'^\W*([0-9]+(?:[.,][0-9]+)?)\s*kWh\W*$', re.I)
_VB_VOLT_RE = re.compile(r'^\W*([0-9]+(?:[.,][0-9]+)?)\s*V\W*$', re.I)
_VB_AMP_RE = re.compile(r'^\W*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*A\W*$', re.I)


def _linea_solo_modelo(linea: str):
    """Si la línea contiene ÚNICAMENTE un código de modelo (± puntuación OCR
    tipo '|'), retorna el código; si no, None."""
    limpio = linea.strip().strip('|').strip()
    codes = _codigos_en_linea(limpio)
    if len(codes) == 1 and codes[0][1] == limpio:
        return limpio
    return None


def _parse_bloques_verticales(lines: list) -> dict:
    """
    Fallback para texto OCR en bloques verticales: detecta líneas que son
    SOLO un código de modelo y lee kWh / V / A en las líneas siguientes
    hasta el próximo modelo. Retorna {modelo: {campo: valor}} o {} si la
    ficha no tiene ≥2 bloques de modelo.
    """
    idx_modelos = []
    for i, linea in enumerate(lines):
        c = _linea_solo_modelo(linea)
        if c:
            idx_modelos.append((i, c))
    if len(idx_modelos) < 2:
        return {}

    out: dict = {}
    for n, (i, modelo) in enumerate(idx_modelos):
        fin = idx_modelos[n + 1][0] if n + 1 < len(idx_modelos) else min(len(lines), i + 20)
        cap = volt = amp = None
        for linea in lines[i + 1:fin]:
            # "Parallel(76.8kWh)" es escalabilidad, no capacidad del modelo
            if re.search(r'[Pp]arallel|[Ss]calab|[Ee]scalab', linea):
                continue
            if cap is None:
                m = _VB_KWH_RE.match(linea)
                if m:
                    v = float(m.group(1).replace(",", "."))
                    if 0.5 <= v <= 5000:
                        cap = v
                        continue
            # Voltaje nominal: línea de UN solo valor en V (los rangos traen '-')
            if volt is None and '-' not in linea:
                m = _VB_VOLT_RE.match(linea)
                if m:
                    v = float(m.group(1).replace(",", "."))
                    if 10 <= v <= 1500:
                        volt = v
                        continue
            # Primera corriente del bloque = continua máx (la pico viene después)
            if amp is None:
                m = _VB_AMP_RE.match(linea)
                if m:
                    v = float(m.group(1).replace(",", ""))
                    if 1 <= v <= 5000:
                        amp = v
        # Exigir capacidad Y voltaje: un bloque con solo uno de los dos suele
        # ser ruido de OCR — mejor omitir el modelo que inventarle datos.
        if cap is None or volt is None:
            continue
        out[modelo] = {
            "capacidad_kWh": cap,
            "capacidad_Ah": round(cap * 1000 / volt, 1) if (cap and volt) else None,
            "voltaje_V": volt,
            # Potencia continua real = corriente continua máx × voltaje nominal
            "potencia_kW": round(amp * volt / 1000.0, 2) if (amp and volt) else None,
            "potencia_estimada": bool(amp and volt),
        }
    return out if len(out) >= 2 else {}


def _asignar_por_columna(modelos: list, vals: list) -> dict:
    """
    Asigna a cada modelo el valor cuya posición de columna esté más cerca.
    Modelos emparejados ("BC75T BR75T") comparten columna → mismo valor.
    Si la columna más cercana queda a más de _MAX_DIST_COL chars → None
    (mejor vacío que un valor de otra columna).
    """
    out: dict = {}
    for pos_m, modelo in modelos:
        mejor, dist = None, None
        for pos_v, v in vals:
            d = abs(pos_m - pos_v)
            if dist is None or d < dist:
                mejor, dist = v, d
        out[modelo] = mejor if (dist is not None and dist <= _MAX_DIST_COL) else None
    return out


def _find_num(text: str, patterns: list, lo: float, hi: float) -> Optional[float]:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            g = next((g for g in m.groups() if g), None)
            if g is None:
                continue
            try:
                v = float(g.replace(",", "."))
            except ValueError:
                continue
            if lo <= v <= hi:
                return v
    return None


def _detectar_quimica(text: str) -> str:
    if re.search(r'LiFePO4?|LFP\b|[Ff]osfato\s+de\s+hierro|[Ll]itio\s*[- ]?ferro', text):
        return "LFP"
    if re.search(r'\bNMC\b|[Nn][ií]quel\s+[Mm]anganeso', text):
        return "NMC"
    if re.search(r'[Ll]itio|[Ll]ithium|Li-?[Ii]on', text):
        return "Litio"
    if re.search(r'[Pp]lomo|[Ll]ead[- ][Aa]cid|\bAGM\b|\bGEL\b', text):
        return "Plomo-ácido"
    return ""


def _detectar_fabricante(text: str) -> str:
    MARCAS = [
        "Pylontech", "Deye", "BYD", "Huawei", "Growatt", "Dyness", "Felicity",
        "SRNE", "Sungrow", "CATL", "EVE", "Victron", "Hoppecke", "Trojan",
        "Freedom Won", "Solis", "GoodWe", "Sacolar", "Must", "Vision",
    ]
    snippet = "\n".join(text.splitlines()[:40])
    for m in MARCAS:
        if re.search(re.escape(m), snippet, re.IGNORECASE):
            return m
    return ""


def _c_rate_nominal(text: str) -> Optional[float]:
    """
    C-rate nominal de carga/descarga. Las fichas listan el nominal y el
    opcional ("0.5C" y "1C(Opcional)"): se toma el MENOR plausible — el
    nominal siempre es ≤ que el opcional.
    """
    rates = []
    for linea in text.splitlines():
        if not re.search(r'[Cc]arga|[Dd]escarga|[Cc]harge|C-?rate', linea):
            continue
        for m in re.finditer(r'\b([0-9](?:\.[0-9]+)?)\s*C\b', linea):
            v = float(m.group(1))
            if 0.1 <= v <= 6:
                rates.append(v)
    return min(rates) if rates else None


def extraer_parametros_bateria(pdf_bytes: bytes) -> dict:
    """Extrae parámetros de una ficha técnica PDF de batería. Ver docstring del módulo."""
    if not _HAS_PDF:
        return {"error": "pdfplumber no instalado. Ejecuta: pip install pdfplumber"}

    # ── 1. Texto: pdftotext -layout (columnas) → pdfplumber → OCR ────────────
    texto = _extract_text_pdftotext(pdf_bytes)
    if len(texto.strip()) < _MIN_TEXT_CHARS:
        texto = _extract_text_pdfplumber(pdf_bytes)
    es_escaneado = len(texto.strip()) < _MIN_TEXT_CHARS
    uso_ocr = False
    if es_escaneado and _HAS_OCR:
        t_ocr = _ocr_pdf(pdf_bytes)
        if len(t_ocr.strip()) >= _MIN_TEXT_CHARS:
            texto, uso_ocr = t_ocr, True

    lines = texto.splitlines()

    # ── 2. Campos compartidos de toda la ficha ───────────────────────────────
    ciclos = _find_num(texto, [
        r'([0-9][0-9.,]{2,5})\s*ciclos',
        r'ciclos[^0-9\n]{0,20}([0-9]{3,6})',
        r'([0-9]{3,6})\s*cycles',
        r'[Cc]ycle\s+[Ll]ife[^0-9\n]{0,20}([0-9]{3,6})',
    ], 100, 30000)
    dod = _find_num(texto, [
        r'DoD[^0-9\n]{0,15}([0-9]{1,3}(?:\.[0-9]+)?)\s*%',
        r'[Pp]rofundidad\s+de\s+descarga[^0-9\n]{0,15}([0-9]{1,3})\s*%',
        r'[Dd]epth\s+of\s+[Dd]ischarge[^0-9\n]{0,15}([0-9]{1,3})\s*%',
    ], 10, 100)
    # OCR deja el valor en línea suelta (">95%") lejos del label DOD —
    # solo confiable si hay label DOD y UN único porcentaje suelto en la ficha.
    if dod is None and re.search(r'\bDOD\b|[Dd]epth\s+of\s+[Dd]ischarge|[Pp]rofundidad\s+de\s+descarga', texto):
        sueltos = {m.group(1) for m in re.finditer(
            r'^\W*[>≥=~]?\s*([0-9]{2,3})\s*%\W*$', texto, re.MULTILINE)}
        if len(sueltos) == 1:
            v = float(sueltos.pop())
            if 10 <= v <= 100:
                dod = v
    rte = _find_num(texto, [
        r'(?:RTE|round[- ]?trip)[^0-9\n%]{0,25}([0-9]{2,3}(?:\.[0-9]+)?)\s*%',
        r'[Ee]ficiencia[^0-9\n%]{0,25}([0-9]{2,3}(?:\.[0-9]+)?)\s*%',
        r'[Ee]fficiency[^0-9\n%]{0,25}([0-9]{2,3}(?:\.[0-9]+)?)\s*%',
    ], 50, 100)
    garantia = _find_num(texto, [
        r'[Gg]arant[ií]a[^0-9\n]{0,20}([0-9]{1,2})\s*a[ñn]os',
        r'([0-9]{1,2})[- ][Yy]ear\s+[Ww]arranty',
        r'[Ww]arranty[^0-9\n]{0,20}([0-9]{1,2})\s*[Yy]ears',
        # "Up to 10-year long warranty" (Felicity)
        r'([0-9]{1,2})-[Yy]ear\b[^\n]{0,30}[Ww]arranty',
    ], 1, 30)
    # OCR pega el valor en línea suelta ("10Years") lejos del label
    # "Warranty Period" — solo confiable si la ficha menciona garantía.
    if garantia is None and re.search(r'[Ww]arranty|[Gg]arant[ií]a', texto):
        m = re.search(r'^\W*([0-9]{1,2})\s*Years?\W*$', texto, re.MULTILINE)
        if m:
            v = float(m.group(1))
            if 1 <= v <= 30:
                garantia = v
    c_rate = _c_rate_nominal(texto)
    quimica = _detectar_quimica(texto)
    fabricante = _detectar_fabricante(texto)

    # ── 3. Multi-modelo por posición de columnas ─────────────────────────────
    modelos = _detectar_modelos(lines)
    valores: dict = {}

    if len(modelos) >= 2:
        por_campo: dict = {}
        for campo, lbl_re, val_re, (lo, hi) in _ROW_SPECS:
            vals = _mejor_fila(lines, lbl_re, val_re, lo, hi)
            if not vals:
                continue
            if len(vals) == 1 and campo == "capacidad_Ah":
                # Ah suele ser único y compartido (misma celda para todos)
                por_campo[campo] = {m: vals[0][1] for _, m in modelos}
            elif len(vals) == 1 and campo in ("capacidad_kWh", "voltaje_V"):
                # Un solo valor para varios modelos: solo aceptarlo si NO hay
                # tabla de módulo que lo contradiga — mejor None que el módulo.
                continue
            else:
                por_campo[campo] = _asignar_por_columna(modelos, vals)
        for _, m in modelos:
            valores[m] = {campo: por_campo.get(campo, {}).get(m) for campo, *_ in _ROW_SPECS}
    else:
        # ── Ficha de UN modelo: valor más grande por campo (rack > módulo) ──
        # OJO: se recorren TODAS las líneas del label (no solo la "mejor"):
        # módulo y rack suelen compartir label con 1 valor cada uno, y
        # _mejor_fila se quedaría con la primera (podía ser la del módulo).
        unico: dict = {}
        for campo, lbl_re, val_re, (lo, hi) in _ROW_SPECS:
            unico[campo] = _max_todas_filas(lines, lbl_re, val_re, lo, hi)
        # Nombre: primer código de modelo válido en las primeras líneas
        nombre = ""
        for linea in lines[:40]:
            codes = _codigos_en_linea(linea)
            if codes:
                nombre = codes[0][1]
                break
        if any(v is not None for v in unico.values()):
            valores[nombre or "(modelo sin nombre)"] = unico
        modelos = [(0, k) for k in valores.keys()]

    # ── 3b. Fallback: bloques verticales (OCR de fichas escaneadas) ──────────
    # Si el mapeo por columnas no logró llenar ningún campo per-modelo,
    # intentar el formato "modelo en una línea, valores debajo".
    sin_datos = not valores or all(
        all(v in (None, False) for v in campos.values())
        for campos in valores.values()
    )
    if sin_datos:
        vb = _parse_bloques_verticales(lines)
        if vb:
            valores = vb
            modelos = [(0, m) for m in vb.keys()]

    # ── 4. Potencia continua = C-rate nominal × capacidad ────────────────────
    for m, campos in valores.items():
        if campos.get("potencia_kW") is not None:
            continue  # ya calculada (p. ej. corriente × voltaje en bloques verticales)
        cap = campos.get("capacidad_kWh")
        if cap and c_rate:
            campos["potencia_kW"] = round(c_rate * cap, 2)
            campos["potencia_estimada"] = True
        else:
            campos["potencia_kW"] = None
            campos["potencia_estimada"] = False

    return {
        "fabricante": fabricante,
        "quimica": quimica,
        "ciclos": ciclos,
        "c_rate": c_rate,
        "dod_pct": dod,
        "rte_pct": rte,
        "garantia_anos": garantia,
        "modelos_detectados": [m for _, m in modelos],
        "valores_por_modelo": valores,
        "es_escaneado": es_escaneado,
        "uso_ocr": uso_ocr,
        "ocr_disponible": _HAS_OCR,
        "texto_crudo": texto[:4000],
    }
