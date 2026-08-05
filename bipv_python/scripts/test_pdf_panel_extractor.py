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

# Dedupe sintético: sin Pmax cae a numeración de variante
_nombres = ex._dedupe_model_names(["AA-1", "AA-1"], [{}, {}])
check("Dedupe sin Pmax → numeración", _nombres == ["AA-1 (var. 1)", "AA-1 (var. 2)"],
      f"(obtuvo {_nombres})")

# ═════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}\nRESULTADO: {PASS} OK · {FAIL} FALLOS")
sys.exit(1 if FAIL else 0)
