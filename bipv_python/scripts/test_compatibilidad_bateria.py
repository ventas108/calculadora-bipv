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
