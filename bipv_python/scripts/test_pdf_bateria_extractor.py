"""
Banco de regresión del extractor de fichas PDF de baterías.

Misma regla que los bancos de paneles e inversores: cada ficha que haya
fallado alguna vez entra aquí como fixture con sus valores esperados, y
NINGÚN fix futuro puede romper una ficha del banco.

Uso:  python scripts/test_pdf_bateria_extractor.py
      (requiere pdfplumber; los fixtures PDF viven en scripts/fixtures_fichas/)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.pdf_bateria_extractor import extraer_parametros_bateria
from calculos.validador_bateria import validar_bateria

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


def _leer(nombre):
    with open(os.path.join(_FIXTURES, nombre), "rb") as f:
        return f.read()


# ═════════════════════════════════════════════════════════════════════════════
# 1. Rack HV interior BR172R/186R/200R/215R (ficha en español, multi-modelo,
#    tabla de módulo 14.336 kWh/51.2 V que NO debe contaminar los racks)
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 1: Rack BR172R/186R/200R/215R ──")
r = extraer_parametros_bateria(_leer("bateria_rack_br_hv.pdf"))

check("4 modelos detectados",
      sorted(r["modelos_detectados"]) == ["BR172R", "BR186R", "BR200R", "BR215R"],
      f"(obtuvo {r['modelos_detectados']})")

_ESPERADO_1 = {
    # modelo: (kWh, V, Ah, kW estimado a 0.5C)
    "BR172R": (172.032, 614.4, 280.0, 86.02),
    "BR186R": (186.368, 665.6, 280.0, 93.18),
    "BR200R": (200.704, 716.8, 280.0, 100.35),
    "BR215R": (215.04, 768.0, 280.0, 107.52),
}
for mod, (kwh, v, ah, kw) in _ESPERADO_1.items():
    vals = r["valores_por_modelo"].get(mod, {})
    check(f"{mod}: {kwh} kWh", approx(vals.get("capacidad_kWh"), kwh),
          f"(obtuvo {vals.get('capacidad_kWh')})")
    check(f"{mod}: {v} V", approx(vals.get("voltaje_V"), v),
          f"(obtuvo {vals.get('voltaje_V')})")
    check(f"{mod}: {ah} Ah", approx(vals.get("capacidad_Ah"), ah),
          f"(obtuvo {vals.get('capacidad_Ah')})")
    check(f"{mod}: potencia {kw} kW (0.5C)", approx(vals.get("potencia_kW"), kw),
          f"(obtuvo {vals.get('potencia_kW')})")

check("Ningún modelo heredó el kWh del MÓDULO (14.336)",
      all(not approx(v.get("capacidad_kWh"), 14.336)
          for v in r["valores_por_modelo"].values()))
check("Ningún modelo heredó el voltaje del MÓDULO (51.2)",
      all(not approx(v.get("voltaje_V"), 51.2)
          for v in r["valores_por_modelo"].values()))
check("Química = Litio (la ficha no dice LFP)", r["quimica"] == "Litio",
      f"(obtuvo {r['quimica']!r})")
check("Ciclos = 6000", approx(r["ciclos"], 6000))
check("C-rate nominal = 0.5 (no el 1C opcional)", approx(r["c_rate"], 0.5),
      f"(obtuvo {r['c_rate']})")
check("DoD ausente → None (no inventar)", r["dod_pct"] is None,
      f"(obtuvo {r['dod_pct']})")
check("RTE ausente → None (no inventar)", r["rte_pct"] is None,
      f"(obtuvo {r['rte_pct']})")
check("Potencia marcada como estimada",
      all(v.get("potencia_estimada") for v in r["valores_por_modelo"].values()))
check("PDF digital (sin OCR)", not r["es_escaneado"] and not r["uso_ocr"])

# El resultado debe pasar el validador (#162) sin errores bloqueantes
_v215 = r["valores_por_modelo"]["BR215R"]
_val = validar_bateria({
    "capacidad_kWh": _v215["capacidad_kWh"], "potencia_kW": _v215["potencia_kW"],
    "voltaje_V": _v215["voltaje_V"], "dod_pct": r["dod_pct"],
    "eta_rte_pct": r["rte_pct"], "ciclos_vida": r["ciclos"],
})
check("BR215R extraído pasa el validador sin bloqueos", _val["ok"],
      f"(errores: {_val['errores']})")

# ═════════════════════════════════════════════════════════════════════════════
# 2. Gabinetes BC75T/100T + BR75T/100T/138T/145T — modelos EMPAREJADOS que
#    comparten columna ("BC75T BR75T") deben heredar el mismo valor
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha 2: Gabinetes BC/BR (modelos emparejados) ──")
r2 = extraer_parametros_bateria(_leer("bateria_gabinete_bc_br.pdf"))

check("6 modelos detectados",
      sorted(r2["modelos_detectados"])
      == ["BC100T", "BC75T", "BR100T", "BR138T", "BR145T", "BR75T"],
      f"(obtuvo {r2['modelos_detectados']})")

_ESPERADO_2 = {
    "BC75T":  (76.8, 384.0),
    "BR75T":  (76.8, 384.0),      # pareja de BC75T — misma columna
    "BC100T": (107.52, 537.6),
    "BR100T": (107.52, 537.6),    # pareja de BC100T
    "BR138T": (138.24, 691.2),
    "BR145T": (145.92, 729.6),
}
for mod, (kwh, v) in _ESPERADO_2.items():
    vals = r2["valores_por_modelo"].get(mod, {})
    check(f"{mod}: {kwh} kWh / {v} V",
          approx(vals.get("capacidad_kWh"), kwh) and approx(vals.get("voltaje_V"), v),
          f"(obtuvo {vals.get('capacidad_kWh')} kWh / {vals.get('voltaje_V')} V)")

check("Ah compartido = 200 en todos",
      all(approx(v.get("capacidad_Ah"), 200.0)
          for v in r2["valores_por_modelo"].values()))
check("Ciclos = 6000", approx(r2["ciclos"], 6000))
check("C-rate nominal = 0.5", approx(r2["c_rate"], 0.5))

# ═════════════════════════════════════════════════════════════════════════════
# 3. Ficha de UN solo modelo con tabla de MÓDULO antes que la del rack:
#    el extractor debe quedarse con el rack (valor más grande), nunca el módulo
#    (regresión detectada en auditoría: _mejor_fila empataba 1-1 y ganaba la
#    primera línea = módulo)
# ═════════════════════════════════════════════════════════════════════════════
print("── Ficha sintética single-model (módulo antes que rack) ──")
from calculos.pdf_bateria_extractor import _max_todas_filas, _ROW_SPECS

_TXT_SM = """BR215R
Especificaciones del módulo de batería
Capacidad nominal          280Ah
Energía nominal            14.336kWh
Voltaje nominal            51.2V
Rango de voltaje           44.8~57.6V
Especificaciones del rack de baterías
Capacidad nominal          280Ah
Energía nominal            215.04kWh
Voltaje nominal            768V
Rango de voltaje           672~864V
""".splitlines()

_esp_sm = {"capacidad_kWh": 215.04, "voltaje_V": 768.0, "capacidad_Ah": 280.0}
for campo, lbl_re, val_re, (lo, hi) in _ROW_SPECS:
    v = _max_todas_filas(_TXT_SM, lbl_re, val_re, lo, hi)
    check(f"single-model {campo} = {_esp_sm[campo]} (rack, no módulo)",
          approx(v, _esp_sm[campo]), f"(obtuvo {v})")

# ═════════════════════════════════════════════════════════════════════════════
# 3b. Ficha ESCANEADA multi-modelo (Felicity FLA-EU) — OCR + bloques verticales
# ═════════════════════════════════════════════════════════════════════════════
from calculos.pdf_bateria_extractor import _parse_bloques_verticales

# Unitario del parser de bloques (no requiere OCR): formato típico del OCR
_TXT_VB = """Model
Nominal Energy
NominalVoltage
FLA48100-EU

5.12kWh
51.2V
44.8-57.6V
100A
150A
7,500W
Max. 15 pcsin
Parallel(76.8kWh)
| FLA48250-EU

12.5kWh
51.2v
44.8-57.6V
150A
200A
10,000W
Parallel(187.5kWh)
""".splitlines()
_vb = _parse_bloques_verticales(_TXT_VB)
print("── Bloques verticales (formato OCR Felicity) ──")
check("VB detecta 2 modelos", sorted(_vb) == ["FLA48100-EU", "FLA48250-EU"], f"(obtuvo {sorted(_vb)})")
if _vb:
    check("VB FLA48100-EU 5.12 kWh / 51.2 V",
          approx(_vb["FLA48100-EU"]["capacidad_kWh"], 5.12) and approx(_vb["FLA48100-EU"]["voltaje_V"], 51.2))
    check("VB potencia = corriente continua × V (100A → 5.12 kW)",
          approx(_vb["FLA48100-EU"]["potencia_kW"], 5.12) and _vb["FLA48100-EU"]["potencia_estimada"])
    check("VB ignora Parallel(...) como capacidad",
          approx(_vb["FLA48250-EU"]["capacidad_kWh"], 12.5), f"(obtuvo {_vb['FLA48250-EU']['capacidad_kWh']})")
    check("VB voltaje minúscula '51.2v' y corriente 150A → 7.68 kW",
          approx(_vb["FLA48250-EU"]["potencia_kW"], 7.68))

# End-to-end con la ficha real escaneada (requiere OCR: pytesseract + poppler)
from calculos.pdf_panel_extractor import _HAS_OCR
_F_FLA = os.path.join(_FIXTURES, "bateria_felicity_fla_eu.pdf")
if _HAS_OCR and os.path.exists(_F_FLA):
    print("── Ficha escaneada Felicity FLA-EU (OCR) ──")
    rf = extraer_parametros_bateria(open(_F_FLA, "rb").read())
    vf = rf.get("valores_por_modelo", {})
    check("Felicity: usa OCR (ficha escaneada)", rf.get("es_escaneado") and rf.get("uso_ocr"))
    check("Felicity: 4 modelos FLA", sorted(vf) ==
          ["FLA48100-EU", "FLA48171-EU", "FLA48230-EU", "FLA48250-EU"], f"(obtuvo {sorted(vf)})")
    _esp_fla = {"FLA48100-EU": (5.12, 51.2, 5.12), "FLA48171-EU": (8.75, 51.2, 6.14),
                "FLA48230-EU": (11.8, 51.2, 7.68), "FLA48250-EU": (12.5, 51.2, 7.68)}
    for mod, (kwh, v, kw) in _esp_fla.items():
        c = vf.get(mod, {})
        check(f"Felicity {mod}: {kwh} kWh / {v} V / {kw} kW",
              approx(c.get("capacidad_kWh"), kwh) and approx(c.get("voltaje_V"), v)
              and approx(c.get("potencia_kW"), kw), f"(obtuvo {c})")
    check("Felicity: DoD 95% (línea suelta '>95%')", approx(rf.get("dod_pct"), 95.0), f"(obtuvo {rf.get('dod_pct')})")
    check("Felicity: garantía 10 años ('10-year long warranty')",
          approx(rf.get("garantia_anos"), 10.0), f"(obtuvo {rf.get('garantia_anos')})")
    check("Felicity: LFP / 6000 ciclos / fabricante Felicity",
          rf.get("quimica") == "LFP" and approx(rf.get("ciclos"), 6000) and rf.get("fabricante") == "Felicity")
    check("Felicity: RTE ausente → None (no inventar)", rf.get("rte_pct") is None, f"(obtuvo {rf.get('rte_pct')})")
else:
    print("── Ficha Felicity: OCR no disponible en este entorno — test omitido ──")

# ═════════════════════════════════════════════════════════════════════════════
# 4. Robustez: entradas que no son fichas de baterías
# ═════════════════════════════════════════════════════════════════════════════
print("── Robustez ──")
r3 = extraer_parametros_bateria(b"esto no es un pdf")
check("Bytes basura → sin modelos, sin crash",
      r3.get("modelos_detectados") == [] or r3.get("error"),
      f"(obtuvo {r3.get('modelos_detectados')})")

# Siglas técnicas NUNCA deben detectarse como modelos
from calculos.pdf_bateria_extractor import _codigos_en_linea
check("IP20 / UN38.3 / RS485 / 16S1P / IEC62619 no son modelos",
      _codigos_en_linea("IP20 UN38 RS485 16S1P IEC62619 ROHS CE CB BMS") == [],
      f"(obtuvo {_codigos_en_linea('IP20 UN38 RS485 16S1P IEC62619 ROHS CE CB BMS')})")
check("BR215R y BC75T sí son modelos",
      [c for _, c in _codigos_en_linea("BR215R   BC75T")] == ["BR215R", "BC75T"])

print(f"\n{'='*50}\nRESULTADO: {PASS} ✅  /  {FAIL} ❌")
sys.exit(1 if FAIL else 0)
