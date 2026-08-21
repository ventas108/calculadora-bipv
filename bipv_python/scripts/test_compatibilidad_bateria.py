"""
Banco de regresión — check_compatibilidad (batería ↔ inversor, tarea #25).

Uso:  python3 bipv_python/scripts/test_compatibilidad_bateria.py
Sin dependencias externas (función pura, sin streamlit).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from calculos.compatibilidad_bateria import check_compatibilidad  # noqa: E402

CASOS = [
    # (descripcion, bat, inv, inv_nombre, estado_esperado)
    ("Sin inversor seleccionado → warning (no bloquea)",
     {"voltaje_V": 614}, {}, "", "warning"),

    ("Híbrido con rango, batería dentro → ok",
     {"voltaje_V": 51.2},
     {"es_hibrido": True, "bat_voltaje_min": 40, "bat_voltaje_max": 60},
     "DEYE SUN-7.6K-SG01LP1", "ok"),

    ("Híbrido 40-60 V con batería HV 614 V → error (caso ATESS de la tarea)",
     {"voltaje_V": 614},
     {"es_hibrido": True, "bat_voltaje_min": 40, "bat_voltaje_max": 60},
     "DEYE SUN-7.6K-SG01LP1", "error"),

    ("String real (Growatt MID) sin flag híbrido → error",
     {"voltaje_V": 51.2}, {}, "Growatt MID-25KTL3-X", "error"),

    ("Mismo MID pero flag híbrido corregido en Excel → deja de bloquear",
     {"voltaje_V": 51.2}, {"es_hibrido": True}, "Growatt MID-25KTL3-X", "ok"),

    ("Batería HV con inversor no identificado → error",
     {"voltaje_V": 614}, {}, "Inversor Genérico X", "error"),

    ("Mismo genérico con flag híbrido + rango HV → ok",
     {"voltaje_V": 614},
     {"es_hibrido": True, "bat_voltaje_min": 500, "bat_voltaje_max": 800},
     "Inversor Genérico X", "ok"),

    ("Batería 48 V con híbrido HV-only (SPH) sin rango en catálogo → error",
     {"voltaje_V": 48}, {}, "Growatt SPH-10000TL3", "error"),

    ("Mismo SPH con rango LV completado en Excel (48 V dentro de 42-59) → ok",
     {"voltaje_V": 48},
     {"bat_voltaje_min": 42, "bat_voltaje_max": 59},
     "Growatt SPH-10000TL3", "ok"),

    ("Híbrido sin voltaje de batería en catálogo → warning (no bloquea)",
     {}, {"es_hibrido": True}, "DEYE SUN-7.6K-SG01LP1", "warning"),

    ("Tipo indeterminado, batería LV → warning (no bloquea)",
     {"voltaje_V": 48}, {}, "PowerInv 20K", "warning"),

    # ── Rango completo de operación (voltaje_min_V/voltaje_max_V) ──────────
    # Antes solo se comparaba el nominal contra la ventana del inversor --
    # una batería con nominal dentro de rango pero mínimo/máximo real fuera
    # se habría marcado "ok" sin serlo.
    ("Nominal dentro de rango, pero MÍNIMO real cae por debajo → error",
     {"voltaje_V": 614.4, "voltaje_min_V": 480, "voltaje_max_V": 700},
     {"es_hibrido": True, "bat_voltaje_min": 500, "bat_voltaje_max": 800},
     "Inversor Genérico X", "error"),

    ("Nominal dentro de rango, pero MÁXIMO real supera el techo → error",
     {"voltaje_V": 614.4, "voltaje_min_V": 550, "voltaje_max_V": 820},
     {"es_hibrido": True, "bat_voltaje_min": 500, "bat_voltaje_max": 800},
     "Inversor Genérico X", "error"),

    ("Rango completo de la batería SÍ cabe dentro del inversor → ok",
     {"voltaje_V": 614.4, "voltaje_min_V": 537.6, "voltaje_max_V": 691.2},
     {"es_hibrido": True, "bat_voltaje_min": 500, "bat_voltaje_max": 800},
     "Inversor Genérico X", "ok"),

    ("Sin voltaje_min_V/voltaje_max_V en el catálogo → cae al chequeo nominal (sin cambio)",
     {"voltaje_V": 51.2},
     {"es_hibrido": True, "bat_voltaje_min": 40, "bat_voltaje_max": 60},
     "DEYE SUN-7.6K-SG01LP1", "ok"),
]

fallos = 0
for desc, bat, inv, nom, esperado in CASOS:
    estado, msg = check_compatibilidad(bat, inv, nom)
    ok = estado == esperado
    print(f"  {'✅' if ok else '❌'} {desc}  [{estado}]")
    if not ok:
        fallos += 1
        print(f"     esperado: {esperado} — msg: {msg[:160]}")

print(f"\nRESULTADO: {len(CASOS) - fallos} OK · {fallos} FALLOS")
sys.exit(1 if fallos else 0)
