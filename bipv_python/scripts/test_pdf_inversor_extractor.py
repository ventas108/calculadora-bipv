"""
Banco de regresión del extractor de fichas PDF de inversores + validador físico.

Ejecuta desde consola (sin Streamlit) el MISMO banco de casos sintéticos de la
página 16 (scripts/casos_test_inversores.py, vía extractor_inversor_core) y
además prueba el validador de coherencia física (calculos/validador_inversor.py).

Regla: NINGÚN fix futuro puede romper un caso del banco.

Uso:  python scripts/test_pdf_inversor_extractor.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.extractor_inversor_core import extraer_desde_texto
from calculos.validador_inversor import validar_inversor
from calculos.campos_inversor import CAMPOS_CRITICOS
from scripts.casos_test_inversores import CASOS

PASS = FAIL = 0


def check(nombre, cond, detalle=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nombre}")
    else:
        FAIL += 1
        print(f"  ❌ {nombre} {detalle}")


def _coincide(extraido, esperado, tol=0.05, strict_nd=False):
    """
    Convención de la página 16: esperado None = N/D.
    strict_nd=True (regresión de consola): un campo N/D que aparezca con valor
    extraído es FALLO — atrapa extractores que rellenan basura donde no hay dato.
    (La página 16 sigue mostrando esos casos como 🔵 informativos.)
    """
    if esperado is None:
        return extraido is None if strict_nd else True
    if extraido is None:
        return False
    try:
        e, x = float(esperado), float(extraido)
    except (TypeError, ValueError):
        return str(esperado) == str(extraido)
    if e == 0:
        return x == 0
    return abs(x - e) / abs(e) <= tol


# ═════════════════════════════════════════════════════════════════════════════
# 1. Banco completo de casos sintéticos por fabricante (mismo código que PDFs)
# ═════════════════════════════════════════════════════════════════════════════
print(f"── Banco de casos de fabricantes ({len(CASOS)} fichas) ──")
for caso in CASOS:
    res_base = extraer_desde_texto(caso["texto"])          # salida sin merge (como página 16)
    # Si la ficha es multi-modelo, valores específicos del modelo del caso
    _vpm = (res_base.get("valores_por_modelo") or {}).get(caso["modelo"])
    res = {**res_base, **{k: v for k, v in (_vpm or {}).items() if v is not None}}
    fallos = []
    for campo in CAMPOS_CRITICOS:
        if campo not in caso["esperado"]:
            continue
        esperado = caso["esperado"][campo]
        if esperado is None:
            # Estricto sobre la salida SIN merge: un campo N/D que aparezca con
            # valor es un extractor rellenando basura. (Los valores por modelo
            # legítimos, ej. P_dc de Deye, viven en el merge y no cuentan aquí.)
            if not _coincide(res_base.get(campo), None, strict_nd=True):
                fallos.append(f"{campo}: esperado N/D, obtuvo {res_base.get(campo)}")
        elif not _coincide(res.get(campo), esperado):
            fallos.append(f"{campo}: esperado {esperado}, obtuvo {res.get(campo)}")
    check(f"{caso['fabricante']} {caso['modelo']}", not fallos,
          "→ " + "; ".join(fallos) if fallos else "")

# ═════════════════════════════════════════════════════════════════════════════
# 2. Validador físico — invariantes universales y errores históricos
# ═════════════════════════════════════════════════════════════════════════════
print("── Validador de coherencia física ──")

# 2.1 Inversor correcto (Growatt MID-25KTL3-X) → sin errores
r = validar_inversor({"Vdc_max": 1100, "Vmppt_min": 200, "Vmppt_max": 1000,
                      "V_arranque": 200, "n_trackers": 3, "n_strings_tracker": 2,
                      "I_max_tracker": 22, "Isc_max_tracker": 27.5,
                      "P_dc_max_W": 37500})
check("Inversor correcto → ok", r["ok"], f"(errores: {r['errores']})")

# 2.2 Vdc_max = 0 → bloquea (obligatorio duro)
r = validar_inversor({"Vdc_max": 0, "Vmppt_min": 200, "Vmppt_max": 1000})
check("Vdc_max=0 → bloquea", not r["ok"])

# 2.3 Rango MPPT invertido → bloquea
r = validar_inversor({"Vdc_max": 1100, "Vmppt_min": 1000, "Vmppt_max": 200})
check("MPPT mín>máx → bloquea", not r["ok"])

# 2.4 MPPT máx > Vdc_max → bloquea (imposible físico)
r = validar_inversor({"Vdc_max": 550, "Vmppt_min": 200, "Vmppt_max": 1000})
check("MPPT máx>Vdc máx → bloquea", not r["ok"])

# 2.5 Isc < I_max (intercambiados) → bloquea
r = validar_inversor({"Vdc_max": 1100, "Vmppt_min": 200, "Vmppt_max": 1000,
                      "I_max_tracker": 27.5, "Isc_max_tracker": 22})
check("Isc<I_max → bloquea", not r["ok"])

# 2.6 Isc/I_max > 2 → avisa sin bloquear (posible Isc total del equipo)
r = validar_inversor({"Vdc_max": 1100, "Vmppt_min": 200, "Vmppt_max": 1000,
                      "n_trackers": 3, "I_max_tracker": 22, "Isc_max_tracker": 55,
                      "P_dc_max_W": 37500})
check("Isc/I_max>2 → avisa sin bloquear",
      r["ok"] and any("ratio" in a for a in r["avisos"]), f"({r['errores']})")

# 2.7 P_dc en kW sin convertir (37.5) → avisa
r = validar_inversor({"Vdc_max": 1100, "Vmppt_min": 200, "Vmppt_max": 1000,
                      "n_trackers": 3, "I_max_tracker": 22, "P_dc_max_W": 37.5})
check("P_dc=37.5 W (kW sin ×1000) → avisa",
      r["ok"] and any("kW" in a for a in r["avisos"]), f"({r['avisos']})")

# 2.8 P_dc > techo físico Vdc×I×trackers → avisa
r = validar_inversor({"Vdc_max": 600, "Vmppt_min": 200, "Vmppt_max": 550,
                      "n_trackers": 1, "I_max_tracker": 13, "P_dc_max_W": 50000})
check("P_dc>techo físico → avisa",
      r["ok"] and any("techo" in a for a in r["avisos"]), f"({r['avisos']})")

# 2.9 Híbrido con batería invertida → bloquea
r = validar_inversor({"Vdc_max": 500, "Vmppt_min": 120, "Vmppt_max": 450,
                      "es_hibrido": True, "bat_voltaje_min": 60, "bat_voltaje_max": 40})
check("Batería mín>máx → bloquea", not r["ok"])

# 2.10 Híbrido sin datos de batería → avisa sin bloquear
r = validar_inversor({"Vdc_max": 500, "Vmppt_min": 120, "Vmppt_max": 450,
                      "es_hibrido": True})
check("Híbrido sin batería → avisa sin bloquear",
      r["ok"] and any("batería" in a.lower() for a in r["avisos"]))

# 2.11 V_arranque de batería confundido (48 V con MPPT 200–1000) → avisa
r = validar_inversor({"Vdc_max": 1100, "Vmppt_min": 200, "Vmppt_max": 1000,
                      "V_arranque": 48})
check("V_arranque=48 V sospechoso → avisa",
      r["ok"] and any("arranque" in a for a in r["avisos"]), f"({r['avisos']})")

# 2.12 V_mppt_activo > Vdc_max → bloquea
r = validar_inversor({"Vdc_max": 550, "Vmppt_min": 120, "Vmppt_max": 500,
                      "V_mppt_activo": 800})
check("MPPT activo>Vdc máx → bloquea", not r["ok"])

# 2.13 Microinversor legítimo (Vdc_max 60 V) → no bloquea
r = validar_inversor({"Vdc_max": 60, "Vmppt_min": 25, "Vmppt_max": 55,
                      "n_trackers": 2, "I_max_tracker": 14, "P_dc_max_W": 730})
check("Microinversor 60 V → ok", r["ok"], f"(errores: {r['errores']})")

# 2.14 Off-grid sin V_arranque ni Isc (MUST/POWEST) → avisa, no bloquea
r = validar_inversor({"Vdc_max": 450, "Vmppt_min": 120, "Vmppt_max": 430,
                      "n_trackers": 1, "I_max_tracker": 18, "P_dc_max_W": 4000})
check("Off-grid sin Isc/arranque → no bloquea", r["ok"], f"(errores: {r['errores']})")

# 2.15 Ficha vacía (extracción fallida total) → bloquea solo por Vdc_max
r = validar_inversor({})
check("Todo vacío → bloquea por Vdc_max", not r["ok"] and len(r["errores"]) == 1,
      f"({r['errores']})")

# ═════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}\nRESULTADO: {PASS} OK · {FAIL} FALLOS")
sys.exit(1 if FAIL else 0)
