"""
Banco de regresión del extractor de fichas PDF de paneles + validador físico.

Cada ficha que haya fallado alguna vez entra aquí como fixture con sus
valores esperados. Regla: NINGÚN fix futuro puede romper una ficha del banco.

Uso:  python scripts/test_pdf_panel_extractor.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos import pdf_panel_extractor as ex
from calculos.validador_panel import validar_panel

_FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures_fichas")

PASS = FAIL = 0


def check(nombre, cond, detalle=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nombre}")
    else:
        FAIL += 1
        print(f"  ❌ {nombre} {detalle}")


def approx(a, b, tol=1e-6):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


# ═════════════════════════════════════════════════════════════════════════════
# 1. JA Solar JAM66D46 — OCR real (falló ago-2026: coefs 0, Ns=2384, dims 0,
#    modelo tomado del pie de página "EN-20250709C")
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 1: JA Solar JAM66D46 (OCR real) ──")
texto = open(os.path.join(_FIXTURES, "jasolar_jam66d46_ocr.txt"), encoding="utf-8").read()
v = ex._apply_patterns(texto)

check("Pmax = 715",        approx(v.get("Pmax"), 715.0))
check("Voc = 48.80",       approx(v.get("Voc"), 48.8))
check("Isc = 18.55",       approx(v.get("Isc"), 18.55))
check("Vmp = 41.00",       approx(v.get("Vmp"), 41.0))
check("Imp = 17.44",       approx(v.get("Imp"), 17.44))
check("β Voc = -0.250",    approx(v.get("CoefVoc"), -0.250))
check("α Isc = +0.045",    approx(v.get("CoefIsc"), 0.045))
check("γ Pmax = -0.290",   approx(v.get("CoefPmax"), -0.290))
check("NOCT = 45",         approx(v.get("NOCT"), 45.0))
check("Bifacialidad = 80", approx(v.get("Bifacialidad"), 80.0))
check("Dimensiones 2384x1303x33", v.get("dimensiones") == "2384x1303x33",
      f"(obtuvo {v.get('dimensiones')})")
# El OCR destruyó "132(6×22)": el extractor DEBE devolver None, nunca basura
check("Ns irrecuperable → None (no 2384, no 22)",
      v.get("N_s") is None, f"(obtuvo {v.get('N_s')})")
check("Modelo = JAM66D46LB (no el 'Version No.')",
      ex._extract_model_name(texto) == "JAM66D46LB",
      f"(obtuvo {ex._extract_model_name(texto)!r})")

# ═════════════════════════════════════════════════════════════════════════════
# 2. Estilo SolTech — OCR español con abreviaturas entre paréntesis
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 2: estilo SolTech (OCR español) ──")
texto_st = """
Potencia Máxima (Pmax) 520
Voltaje Circuito Abierto (Voc) 49.8
Corriente Corto Circuito (Isc) 13.56
Voltaje Máximo (Vmp) 42.3
Corriente Máxima (Imp) 12.31
N De Celdas 144 (12 x 12)
Coeficientes de temperatura de Voc TKβ(%/℃) -0.321
Coeficientes de temperatura de Isc TKα(%/℃) +0.06
Coeficientes de temperatura de Pm TKγ(%/℃) -0.214
Temperatura Operativa Nominal Del Módulo 41 +/-2°C
Dimensions: 2278 x 1134 x 30 mm
"""
v2 = ex._apply_patterns(texto_st)
for campo, esperado in [("Pmax", 520), ("Voc", 49.8), ("Isc", 13.56),
                        ("Vmp", 42.3), ("Imp", 12.31), ("N_s", 144),
                        ("CoefVoc", -0.321), ("CoefIsc", 0.06),
                        ("CoefPmax", -0.214), ("NOCT", 41)]:
    check(f"{campo} = {esperado}", approx(v2.get(campo), esperado),
          f"(obtuvo {v2.get(campo)})")
check("Dimensiones 2278x1134x30", v2.get("dimensiones") == "2278x1134x30",
      f"(obtuvo {v2.get('dimensiones')})")

# ═════════════════════════════════════════════════════════════════════════════
# 3. Estilo NCL BIPV — coeficiente en frase española
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 3: estilo NCL (frases en español) ──")
texto_ncl = "Coeficiente de temperatura para voltaje  -0.28%/ºC\n327.8W Potencia\n"
v3 = ex._apply_patterns(texto_ncl)
check("CoefVoc = -0.28", approx(v3.get("CoefVoc"), -0.28), f"(obtuvo {v3.get('CoefVoc')})")

# ═════════════════════════════════════════════════════════════════════════════
# 4. Validador físico — debe atrapar los errores históricos
# ═════════════════════════════════════════════════════════════════════════════
print("── Validador de coherencia física ──")

# 4.1 Panel correcto (JAM66D46-715 con Ns=66) → sin errores
r = validar_panel({"Pmax": 715, "Voc": 48.8, "Isc": 18.55, "Vmp": 41.0,
                   "Imp": 17.44, "N_s": 66, "CoefVoc": -0.25, "CoefIsc": 0.045,
                   "CoefPmax": -0.29, "NOCT": 45, "dimensiones": "2384x1303x33",
                   "Bifacialidad": 80})
check("Panel correcto → ok (sin errores)", r["ok"], f"(errores: {r['errores']})")

# 4.2 Ns=2384 (el bug histórico) → error con Voc/Ns absurdo
r = validar_panel({"Pmax": 715, "Voc": 48.8, "Isc": 18.55, "Vmp": 41.0,
                   "Imp": 17.44, "N_s": 2384})
check("Ns=2384 → bloquea", not r["ok"] and any("Ns" in e or "celda" in e for e in r["errores"]))

# 4.3 Half-cut mal contado: Ns=132 con Voc=48.8 → error y sugiere 66
r = validar_panel({"Pmax": 715, "Voc": 48.8, "Isc": 18.55, "Vmp": 41.0,
                   "Imp": 17.44, "N_s": 132})
check("Ns=132 half-cut → bloquea y sugiere 66",
      not r["ok"] and any("66" in e for e in r["errores"]), f"({r['errores']})")

# 4.4 Coeficientes en cero (el fallo de esta ficha) → aviso, no bloquea
r = validar_panel({"Pmax": 715, "Voc": 48.8, "Isc": 18.55, "Vmp": 41.0,
                   "Imp": 17.44, "N_s": 66, "CoefVoc": 0, "CoefIsc": 0, "CoefPmax": 0})
check("Coefs en 0 → avisa sin bloquear",
      r["ok"] and sum("genérico" in a for a in r["avisos"]) == 3, f"({r['avisos']})")

# 4.5 Vmp > Voc (extracción cruzada) → bloquea
r = validar_panel({"Pmax": 715, "Voc": 41.0, "Isc": 18.55, "Vmp": 48.8, "Imp": 17.44})
check("Vmp>Voc → bloquea", not r["ok"])

# 4.6 Imp > Isc → bloquea
r = validar_panel({"Pmax": 715, "Voc": 48.8, "Isc": 17.44, "Vmp": 41.0, "Imp": 18.55})
check("Imp>Isc → bloquea", not r["ok"])

# 4.7 Pmax incoherente con Vmp×Imp (>8%) → bloquea
r = validar_panel({"Pmax": 500, "Voc": 48.8, "Isc": 18.55, "Vmp": 41.0, "Imp": 17.44})
check("Pmax≠Vmp×Imp (43%) → bloquea", not r["ok"])

# 4.8 Pmax vacío → bloquea
r = validar_panel({"Pmax": 0, "Voc": 48.8, "Isc": 18.55, "Vmp": 41.0, "Imp": 17.44})
check("Pmax=0 → bloquea", not r["ok"])

# 4.9 Eficiencia imposible (dimensiones mal) → bloquea
r = validar_panel({"Pmax": 715, "Voc": 48.8, "Isc": 18.55, "Vmp": 41.0,
                   "Imp": 17.44, "N_s": 66, "dimensiones": "1200x600"})
check("Eficiencia 99% (dims mal) → bloquea", not r["ok"])

# 4.10 Panel BIPV semitransparente de baja eficiencia (CdTe) → válido
r = validar_panel({"Pmax": 108, "Voc": 124.2, "Isc": 1.21, "Vmp": 96.0,
                   "Imp": 1.11, "dimensiones": "1200x600"})
check("BIPV CdTe 15% eficiencia → ok", r["ok"], f"(errores: {r['errores']})")

# 4.11 Thin-film CdTe con Ns "raro" para silicio → NO bloquea (regla por tecnología)
r = validar_panel({"Pmax": 120, "Voc": 88.7, "Isc": 1.97, "Vmp": 66.9,
                   "Imp": 1.79, "N_s": 264, "tecnologia": "CdTe"})
check("CdTe Ns=264 (0.34 V/celda) → no bloquea", r["ok"], f"(errores: {r['errores']})")

# 4.12 BIPV vidrio muy transparente, eficiencia 4% → avisa, no bloquea
r = validar_panel({"Pmax": 40, "Voc": 24.0, "Isc": 2.2, "Vmp": 19.5,
                   "Imp": 2.05, "dimensiones": "1200x800", "tecnologia": "a-Si"})
check("BIPV 4.2% eficiencia → avisa sin bloquear",
      r["ok"] and any("eficiencia" in a.lower() for a in r["avisos"]), f"({r['errores']} {r['avisos']})")

# 4.13 Eficiencia >25% sigue bloqueando (imposible en cualquier tecnología)
r = validar_panel({"Pmax": 715, "Voc": 48.8, "Isc": 18.55, "Vmp": 41.0,
                   "Imp": 17.44, "N_s": 66, "dimensiones": "1200x600", "tecnologia": "CdTe"})
check("Eficiencia 99% → bloquea aun siendo CdTe", not r["ok"])

# ═════════════════════════════════════════════════════════════════════════════
# 5. Regex nuevas contra estilos de otros fabricantes (sintéticos)
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 5: estilos Trina / Canadian / LONGi (sintéticos) ──")

# Trina: etiquetas con guión y unidad pegada
v5 = ex._apply_patterns("""
Maximum Power (Pmax) [W] 400
Open Circuit Voltage (Voc) [V] 41.10
Short Circuit Current (Isc) [A] 12.16
Maximum Power Voltage (Vmp) [V] 34.10
Maximum Power Current (Imp) [A] 11.74
Temperature Coefficient of Pmax -0.34%/°C
Temperature Coefficient of Voc -0.25%/°C
Temperature Coefficient of Isc +0.04%/°C
Dimensions 1754×1096×30 mm
""")
for campo, esperado in [("Pmax", 400), ("Voc", 41.10), ("Isc", 12.16),
                        ("Vmp", 34.10), ("Imp", 11.74),
                        ("CoefPmax", -0.34), ("CoefVoc", -0.25), ("CoefIsc", 0.04)]:
    check(f"Trina-style {campo} = {esperado}", approx(v5.get(campo), esperado),
          f"(obtuvo {v5.get(campo)})")
check("Trina-style dims 1754x1096x30", v5.get("dimensiones") == "1754x1096x30",
      f"(obtuvo {v5.get('dimensiones')})")

# El patrón "(Voc) [V]" no debe disparar sin la abreviatura entre paréntesis
v6 = ex._apply_patterns("Este texto menciona el voltaje 9999 sin abreviaturas de panel.")
check("Sin abreviaturas → Voc None (no captura basura)", v6.get("Voc") is None,
      f"(obtuvo {v6.get('Voc')})")

# ═════════════════════════════════════════════════════════════════════════════
# 6. Hiitio CdTe (BIPV): labels descriptivos y espesor decimal
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 6: Hiitio CdTe (labels descriptivos + complemento OCR) ──")

v7 = ex._apply_patterns("""
Size 1200*600*16.2mm
Maximum power temperature coefficient -0.29%°C
Open circuit voltage temperature coefficient -0.28%°C
Short circuit current temperature coefficient +0.04%°C
""")
check("Hiitio CoefPmax = -0.29", approx(v7.get("CoefPmax"), -0.29), f"(obtuvo {v7.get('CoefPmax')})")
check("Hiitio CoefVoc = -0.28", approx(v7.get("CoefVoc"), -0.28), f"(obtuvo {v7.get('CoefVoc')})")
check("Hiitio CoefIsc = +0.04", approx(v7.get("CoefIsc"), 0.04), f"(obtuvo {v7.get('CoefIsc')})")
check("Hiitio dims 1200x600x16.2", v7.get("dimensiones") == "1200x600x16.2",
      f"(obtuvo {v7.get('dimensiones')})")

# E2E con la ficha real: PDF "mixto" (texto digital escaso, tablas en imagen).
# Requiere OCR; si no está disponible se omite sin fallar.
_hiitio_pdf = os.path.join(_FIXTURES, "panel_hiitio_cdte.pdf")
if ex._HAS_OCR and os.path.exists(_hiitio_pdf):
    with open(_hiitio_pdf, "rb") as f:
        r7 = ex.extraer_parametros_panel(f.read())
    check("Hiitio e2e: 3 modelos detectados",
          set(r7["modelos_detectados"]) == {"HC-JL-B5", "HC-JL-B6", "HC-JL-B8"},
          f"(obtuvo {r7['modelos_detectados']})")
    vpm = r7["valores_por_modelo"].get("HC-JL-B5", {})
    check("Hiitio e2e: HC-JL-B5 Pmax = 115", approx(vpm.get("Pmax"), 115.0),
          f"(obtuvo {vpm.get('Pmax')})")
    check("Hiitio e2e: tecnologia CdTe (via OCR)", r7.get("tecnologia") == "CdTe",
          f"(obtuvo {r7.get('tecnologia')!r})")
    check("Hiitio e2e: CoefPmax complementado = -0.29", approx(r7.get("CoefPmax"), -0.29),
          f"(obtuvo {r7.get('CoefPmax')})")
    check("Hiitio e2e: dims complementadas 1200x600x16.2",
          r7.get("dimensiones") == "1200x600x16.2", f"(obtuvo {r7.get('dimensiones')})")
    check("Hiitio e2e: uso_ocr marcado como complemento", r7.get("uso_ocr") is True)
else:
    print("  (OCR no disponible o fixture ausente — e2e Hiitio omitido)")

# 6.b El complemento OCR NO debe dispararse cuando solo falta Bifacialidad
# (paneles monofaciales completos). Se monkeypatchea _ocr_pdf para detectarlo.
_ocr_llamado = {"n": 0}
_orig_ocr = ex._ocr_pdf
def _ocr_spy(pdf_bytes):
    _ocr_llamado["n"] += 1
    return ""
ex._ocr_pdf = _ocr_spy
_orig_plumber = ex._extract_text_pdfplumber
_texto_completo = """
Monocrystalline Silicon module TEST-MOD-400
Maximum Power (Pmax) [W] 400
Open Circuit Voltage (Voc) [V] 41.10
Short Circuit Current (Isc) [A] 12.16
Maximum Power Voltage (Vmp) [V] 34.10
Maximum Power Current (Imp) [A] 11.74
Temperature Coefficient of Pmax -0.34%/°C
Temperature Coefficient of Voc -0.25%/°C
Temperature Coefficient of Isc +0.04%/°C
NOCT 45°C
Number of cells 144
Dimensions 1754×1096×30 mm
""" + "x" * 200
ex._extract_text_pdfplumber = lambda b: _texto_completo
try:
    r8 = ex.extraer_parametros_panel(b"%PDF-fake")
    check("Ficha completa sin bifacialidad → OCR NO se dispara",
          _ocr_llamado["n"] == 0, f"(llamadas OCR: {_ocr_llamado['n']})")
    check("Ficha completa → uso_ocr False", r8.get("uso_ocr") is False)
finally:
    ex._ocr_pdf = _orig_ocr
    ex._extract_text_pdfplumber = _orig_plumber

# 6.c Si el OCR solo aporta la tecnología, uso_ocr debe quedar True
_texto_sin_tec = _texto_completo.replace("Monocrystalline Silicon module", "Module")
ex._extract_text_pdfplumber = lambda b: _texto_sin_tec
ex._ocr_pdf = lambda b: ("CdTe thin film technology datasheet " + "y" * 200)
try:
    r9 = ex.extraer_parametros_panel(b"%PDF-fake")
    check("Solo tecnología por OCR → tecnologia = CdTe", r9.get("tecnologia") == "CdTe",
          f"(obtuvo {r9.get('tecnologia')!r})")
    check("Solo tecnología por OCR → uso_ocr True", r9.get("uso_ocr") is True)
finally:
    ex._ocr_pdf = _orig_ocr
    ex._extract_text_pdfplumber = _orig_plumber

# ═════════════════════════════════════════════════════════════════════════════
# 7. HL-XWB13 (PV wall): mismo código de modelo repetido en 3 variantes
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 7: HL-XWB13 (código duplicado en variantes de potencia) ──")

_xwb_pdf = os.path.join(_FIXTURES, "panel_hl_xwb13.pdf")
if os.path.exists(_xwb_pdf):
    with open(_xwb_pdf, "rb") as f:
        r10 = ex.extraer_parametros_panel(f.read())
    check("HL-XWB13: 3 variantes con nombre único",
          r10["modelos_detectados"] == ["HL-XWB13 (125W)", "HL-XWB13 (130W)", "HL-XWB13 (135W)"],
          f"(obtuvo {r10['modelos_detectados']})")
    v135 = r10["valores_por_modelo"].get("HL-XWB13 (135W)", {})
    for campo, esperado in [("Pmax", 135.0), ("Voc", 10.44), ("Isc", 16.19),
                            ("Vmp", 8.8), ("Imp", 15.35)]:
        check(f"HL-XWB13 135W {campo} = {esperado}", approx(v135.get(campo), esperado),
              f"(obtuvo {v135.get(campo)})")
    v125 = r10["valores_por_modelo"].get("HL-XWB13 (125W)", {})
    check("HL-XWB13 125W Pmax = 125 (no pisado por otras columnas)",
          approx(v125.get("Pmax"), 125.0), f"(obtuvo {v125.get('Pmax')})")
else:
    print("  (fixture panel_hl_xwb13.pdf ausente — omitido)")

# 7.b HJT curtain wall: coeficientes con orden invertido ("Temperature
# coefficient of open circuit voltage (Voc)-0.24%/℃"), Isc sin signo y
# NOCT como "Rated operating temperature of battery (NOCT) 44±2℃"
v11 = ex._apply_patterns("""
Temperature coefficient
Rated operating temperature of battery (NOCT) 44±2℃
Maximum power temperature coefficient (Pmax) -0.26%/℃
Temperature coefficient of open circuit voltage (Voc)-0.24%/℃
Temperature coefficient of short-circuit current (Isc)0.04%/℃
""")
for campo, esperado in [("CoefPmax", -0.26), ("CoefVoc", -0.24),
                        ("CoefIsc", 0.04), ("NOCT", 44.0)]:
    check(f"HJT-wall {campo} = {esperado}", approx(v11.get(campo), esperado),
          f"(obtuvo {v11.get(campo)})")

# 7.c Fallback genérico de coeficientes (#166): redacciones nunca vistas,
# en cualquier orden, con/sin signo, español o inglés
print("── Fallback genérico de coeficientes (#166) ──")
v12 = ex._apply_patterns("Pmax temp. coefficient : -0.35 %/K")
check("Genérico: 'Pmax temp. coefficient' = -0.35", approx(v12.get("CoefPmax"), -0.35),
      f"(obtuvo {v12.get('CoefPmax')})")
v13 = ex._apply_patterns("Coeficiente de temperatura de la tensión de vacío -0.27 %")
check("Genérico: español 'tensión de vacío' = -0.27", approx(v13.get("CoefVoc"), -0.27),
      f"(obtuvo {v13.get('CoefVoc')})")
v14 = ex._apply_patterns("temperature coeff (short-circuit current) 0.05%/C tolerancia ±0.01%")
check("Genérico: Isc sin signo ignora tolerancia ±", approx(v14.get("CoefIsc"), 0.05),
      f"(obtuvo {v14.get('CoefIsc')})")
# Valores fuera de rango físico NO se aceptan (evita capturar ruido)
v15 = ex._apply_patterns("temperature coefficient of maximum power 45%")
check("Genérico: 45% fuera de rango → None", v15.get("CoefPmax") is None,
      f"(obtuvo {v15.get('CoefPmax')})")
# Voc positivo es implausible → rechazado por el fallback (redacción que
# NO coincide con ningún patrón específico, para probar el rango del genérico)
v16 = ex._apply_patterns("Voc temp. coefficient 0.30%")
check("Genérico: Voc positivo → None", v16.get("CoefVoc") is None,
      f"(obtuvo {v16.get('CoefVoc')})")

# 7.d Ns desde conteo de semiceldas (#67)
print("── Ns desde semiceldas (#67) ──")
v17 = ex._apply_patterns("28 half-piece/Double-glass Non-transparent\nOpen-circuit voltage (Voc) 10.44V")
check("28 half-piece + Voc 10.44 → Ns = 14", v17.get("N_s") == 14.0,
      f"(obtuvo {v17.get('N_s')})")
v18 = ex._apply_patterns("Module with 144 half cells\nVoc 49.5V")
check("144 half cells + Voc 49.5 → Ns = 72", v18.get("N_s") == 72.0,
      f"(obtuvo {v18.get('N_s')})")
# Sin Voc: usa la mitad por defecto
v19 = ex._apply_patterns("132 semiceldas half-cut")
check("132 semiceldas sin Voc → Ns = 66", v19.get("N_s") == 66.0,
      f"(obtuvo {v19.get('N_s')})")
# Ns explícito tiene prioridad sobre el conteo de semiceldas
v20 = ex._apply_patterns("Number of cells 72\nModule of 144 half cells")
check("Ns explícito 72 no se pisa", v20.get("N_s") == 72.0,
      f"(obtuvo {v20.get('N_s')})")
if os.path.exists(_xwb_pdf):
    with open(_xwb_pdf, "rb") as f:
        r11 = ex.extraer_parametros_panel(f.read())
    check("HL-XWB13 e2e: Ns inferido = 14 (28 half-piece)", r11.get("N_s") == 14.0,
          f"(obtuvo {r11.get('N_s')})")

# Dedupe sintético: sin Pmax cae a numeración de variante
_nombres = ex._dedupe_model_names(["AA-1", "AA-1"], [{}, {}])
check("Dedupe sin Pmax → numeración", _nombres == ["AA-1 (var. 1)", "AA-1 (var. 2)"],
      f"(obtuvo {_nombres})")

# ═════════════════════════════════════════════════════════════════════════════
# 8. Suntech STP-410-A72-Pnh-Bifacial — falso "multi-modelo" por auto-verificación
#    (falló ago-2026: 1 solo panel detectado como "2 modelos" 410.18Wp/410Wp)
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 8: Suntech STP-410 (falso multi-modelo por nota ✓) ──")

# La ficha real trae, en la MISMA línea del valor de Pmax, una nota de
# auto-verificación cruzada que re-cita el mismo valor redondeado:
# "Potencia máxima calculada (Vmpp × Impp) 410.18 W ✓ coincide con 410.0 Wp".
# Antes del fix, _extract_row_numbers() tomaba TODOS los números de la línea
# (410.18 Y el 410.0 de la nota) como si fueran 2 columnas de modelo distinto.
_texto_suntech = """
Ficha Técnica — Módulo Fotovoltaico Bifacial
Suntech STP-410-A72-Pnh-Bifacial
1. Identificación del producto
Potencia nominal (STC)    410.0 Wp  (tolerancia -0.0% / +3.0%)
2. Parámetros eléctricos en condiciones STC
Corriente de cortocircuito (Isc)    10.490 A
Voltaje de circuito abierto (Voc)    48.90 V
Corriente en punto de máxima potencia (Impp)    9.980 A
Voltaje en punto de máxima potencia (Vmpp)    41.10 V
Potencia máxima calculada (Vmpp × Impp)    410.18 W  ✓ coincide con 410.0 Wp
4. Eficiencia (verificación cruzada)
Eficiencia sobre área de módulo    20.19 %  ✓ (410 W / 2.032 m² / 10)
"""
_mm_suntech = ex._extract_multimodel_panel(_texto_suntech)
check("Suntech: NO detecta multi-modelo falso (ficha de 1 solo panel)",
      _mm_suntech["modelos_detectados"] == [], f"(obtuvo {_mm_suntech['modelos_detectados']})")

# E2E con el PDF real (aportado por el usuario tras reportar el bug, con Isc
# también corrompido -- ver abajo). Antes del fix: modelos_detectados =
# ['410.18Wp', '410Wp'] y, al elegir "410Wp" en la UI, el merge de la página
# sobrescribía el Isc YA correcto (10.49 A) con el 0.05 A falso que salía de
# la MISMA línea de coeficiente de temperatura ("µIsc 5.2 mA/°C (+0.050
# %/°C)") mal interpretada como 2 columnas de Isc -- reportado por el usuario
# como "Isc = 0.05 A" en el formulario. Verificado con el PDF real que el fix
# de _extract_row_numbers() resuelve TODO el cascade (Pmax e Isc), no solo Pmax.
_suntech_pdf = os.path.join(_FIXTURES, "panel_suntech_stp410_bifacial.pdf")
if os.path.exists(_suntech_pdf):
    with open(_suntech_pdf, "rb") as f:
        r_suntech = ex.extraer_parametros_panel(f.read())
    check("Suntech e2e (PDF real): NO detecta multi-modelo falso",
          r_suntech["modelos_detectados"] == [], f"(obtuvo {r_suntech['modelos_detectados']})")
    check("Suntech e2e (PDF real): Isc = 10.49 (no 0.05 del coef. de temperatura)",
          approx(r_suntech.get("Isc"), 10.49), f"(obtuvo {r_suntech.get('Isc')})")
    check("Suntech e2e (PDF real): Pmax = 410.0",
          approx(r_suntech.get("Pmax"), 410.0), f"(obtuvo {r_suntech.get('Pmax')})")
    check("Suntech e2e (PDF real): Voc = 48.9",
          approx(r_suntech.get("Voc"), 48.9), f"(obtuvo {r_suntech.get('Voc')})")
    check("Suntech e2e (PDF real): Vmp = 41.1",
          approx(r_suntech.get("Vmp"), 41.1), f"(obtuvo {r_suntech.get('Vmp')})")
    check("Suntech e2e (PDF real): Imp = 9.98",
          approx(r_suntech.get("Imp"), 9.98), f"(obtuvo {r_suntech.get('Imp')})")
else:
    print("  (fixture panel_suntech_stp410_bifacial.pdf ausente — e2e omitido)")

# Generalización pedida explícitamente por el usuario: "revisa la lógica del
# extractor para que no confunda coeficientes de temperatura con valores
# absolutos... es un error que se puede repetir con cualquier otra ficha".
# El fix inicial solo cortaba en '✓'; esto prueba el caso SIN checkmark: una
# fila de coeficiente de temperatura (mA/°C, V/°C) que aparece ANTES de la
# fila real en una tabla multi-modelo genuina (2 modelos con códigos reales,
# no el fallback numérico) no debe robarle la asignación a la fila correcta.
_texto_coef_sin_check = """
CS6R-400MS  CS6R-410MS
Pmax  400  410
Isc temperature coefficient 5.2 mA/°C 6.1 mA/°C
Isc  10.20  10.45
"""
_mm_coef = ex._extract_multimodel_panel(_texto_coef_sin_check)
_isc_400 = _mm_coef["valores_por_modelo"].get("CS6R-400MS", {}).get("Isc")
_isc_410 = _mm_coef["valores_por_modelo"].get("CS6R-410MS", {}).get("Isc")
check("Coeficiente sin ✓ (mA/°C) no roba la fila real de Isc",
      approx(_isc_400, 10.20) and approx(_isc_410, 10.45),
      f"(obtuvo CS6R-400MS={_isc_400}, CS6R-410MS={_isc_410})")

# Control: una ficha multi-modelo REAL (sin notas ✓) debe seguir detectándose
# por la misma vía de fallback numérico -- el fix no debe volverse tan
# agresivo que rompa el caso legítimo que la vía existe para cubrir.
_texto_multi_real = """
Potencia nominal (Pm)  108W  95W  83W  60W
"""
_mm_real = ex._extract_multimodel_panel(_texto_multi_real)
check("Multi-modelo real (sin ✓) sigue detectándose: 4 variantes",
      set(_mm_real["modelos_detectados"]) == {"108Wp", "95Wp", "83Wp", "60Wp"},
      f"(obtuvo {_mm_real['modelos_detectados']})")

# ═════════════════════════════════════════════════════════════════════════════
# 9. Solar First ST1/ST2 — tabla multi-modelo "por fila" (10 variantes, código
#    corto tipo "ST1-72" que _MODEL_CODE_RE rechaza) + falso positivo de marca
#    "LG" dentro de "película delgada" (falló ago-2026)
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 9: Solar First ST1/ST2 (tabla por fila + falso positivo de marca) ──")

# 9.a Unitario: _detectar_tabla_modelos_por_fila() contra una tabla sintética
# con la MISMA estructura real (encabezado "Modelo" + columnas, códigos
# cortos de 2 caracteres tras el guion).
_tabla_por_fila = [
    ["Modelo", "Transp.", "Pmax", "Voc", "Vmpp", "Isc", "Impp", "Dimensiones"],
    ["ST1-72", "10%", "72 W", "116 V", "90.5 V", "0.88 A", "0.8 A", "1200x600x6.8mm"],
    ["ST1-64", "20%", "64 W", "116 V", "90.5 V", "0.78 A", "0.71 A", "1200x600x6.8mm"],
    ["ST2-80", "No (opaco)", "80 W", "58.8 V", "47.4 V", "1.90 A", "1.68 A", "1200x600x6.8mm"],
]
_mm_fila = ex._detectar_tabla_modelos_por_fila(_tabla_por_fila)
check("Tabla por fila: detecta las 3 filas como modelos",
      _mm_fila["modelos_detectados"] == ["ST1-72", "ST1-64", "ST2-80"],
      f"(obtuvo {_mm_fila['modelos_detectados']})")
_v_st1_72 = _mm_fila["valores_por_modelo"].get("ST1-72", {})
check("Tabla por fila: ST1-72 Pmax=72, Voc=116, Isc=0.88, Transp=10",
      approx(_v_st1_72.get("Pmax"), 72.0) and approx(_v_st1_72.get("Voc"), 116.0)
      and approx(_v_st1_72.get("Isc"), 0.88) and approx(_v_st1_72.get("Transparencia"), 10.0),
      f"(obtuvo {_v_st1_72})")

# 9.b Falso positivo de marca "LG" dentro de "película delgada"
check("'película delgada' NO se detecta como marca 'LG'",
      ex._extract_brand("Tecnología: CdTe, película delgada") == "",
      f"(obtuvo {ex._extract_brand('Tecnología: CdTe, película delgada')!r})")
# Control: "LG" como marca real (palabra propia, con límites) sigue detectándose
check("'Panel LG NeON' sí detecta marca 'LG'",
      ex._extract_brand("Panel LG NeON 2 400W") == "LG",
      f"(obtuvo {ex._extract_brand('Panel LG NeON 2 400W')!r})")

# 9.c E2E con el PDF real (aportado por el usuario, con el CSV de verificación
# de la UI mostrando los 5 campos obligatorios en rojo -- 0 datos extraídos).
_solarfirst_pdf = os.path.join(_FIXTURES, "panel_solarfirst_st1_st2.pdf")
if os.path.exists(_solarfirst_pdf):
    with open(_solarfirst_pdf, "rb") as f:
        r_sf = ex.extraer_parametros_panel(f.read())
    check("Solar First e2e (PDF real): marca = 'Solar First' (no 'LG')",
          r_sf.get("marca") == "Solar First", f"(obtuvo {r_sf.get('marca')!r})")
    check("Solar First e2e (PDF real): 10 modelos detectados",
          set(r_sf["modelos_detectados"]) == {
              "ST1-72", "ST1-64", "ST1-56", "ST1-48", "ST1-40",
              "ST1-32", "ST1-24", "ST1-16", "ST2-80", "ST2-85",
          }, f"(obtuvo {r_sf['modelos_detectados']})")
    _vpm_sf = r_sf["valores_por_modelo"]
    check("Solar First e2e: ST1-72 Pmax=72, Voc=116, Vmp=90.5, Isc=0.88, Imp=0.80",
          approx(_vpm_sf.get("ST1-72", {}).get("Pmax"), 72.0)
          and approx(_vpm_sf.get("ST1-72", {}).get("Voc"), 116.0)
          and approx(_vpm_sf.get("ST1-72", {}).get("Vmp"), 90.5)
          and approx(_vpm_sf.get("ST1-72", {}).get("Isc"), 0.88)
          and approx(_vpm_sf.get("ST1-72", {}).get("Imp"), 0.80),
          f"(obtuvo {_vpm_sf.get('ST1-72')})")
    check("Solar First e2e: ST2-85 Pmax=85, Voc=60.2, Isc=1.97 (opaco, sin Transparencia)",
          approx(_vpm_sf.get("ST2-85", {}).get("Pmax"), 85.0)
          and approx(_vpm_sf.get("ST2-85", {}).get("Voc"), 60.2)
          and approx(_vpm_sf.get("ST2-85", {}).get("Isc"), 1.97)
          and "Transparencia" not in _vpm_sf.get("ST2-85", {}),
          f"(obtuvo {_vpm_sf.get('ST2-85')})")
else:
    print("  (fixture panel_solarfirst_st1_st2.pdf ausente — e2e omitido)")

# ═════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}\nRESULTADO: {PASS} OK · {FAIL} FALLOS")
sys.exit(1 if FAIL else 0)
