"""
Pruebas del validador de coherencia física de baterías (#162).

Regla: NINGÚN fix futuro puede romper un caso de este banco.

Uso:  python scripts/test_validador_bateria.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.validador_bateria import validar_bateria

PASS = FAIL = 0


def check(nombre, cond, detalle=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nombre}")
    else:
        FAIL += 1
        print(f"  ❌ {nombre} {detalle}")


print("── Validador de coherencia física de baterías ──")

# 1. Batería LFP típica correcta (ej. 48 V residencial) → sin errores
r = validar_bateria({"capacidad_kWh": 11.04, "potencia_kW": 5.0, "voltaje_V": 48,
                     "dod_pct": 90, "eta_rte_pct": 96, "ciclos_vida": 4000,
                     "costo_usd": 4200, "garantia_anos": 10})
check("LFP 48V correcta → ok", r["ok"], f"(errores: {r['errores']})")

# 2. Batería HV comercial correcta (banco 400 V) → sin errores
r = validar_bateria({"capacidad_kWh": 100, "potencia_kW": 50, "voltaje_V": 409.6,
                     "dod_pct": 95, "eta_rte_pct": 94, "ciclos_vida": 6000})
check("HV 400V correcta → ok", r["ok"], f"(errores: {r['errores']})")

# 3. Capacidad vacía → bloquea (obligatorio duro)
r = validar_bateria({"potencia_kW": 5.0, "voltaje_V": 48})
check("Capacidad vacía → bloquea", not r["ok"])

# 4. DoD > 100 % → bloquea (imposible)
r = validar_bateria({"capacidad_kWh": 10, "potencia_kW": 5, "voltaje_V": 48,
                     "dod_pct": 900})
check("DoD=900% → bloquea", not r["ok"])

# 5. RTE > 100 % → bloquea
r = validar_bateria({"capacidad_kWh": 10, "potencia_kW": 5, "voltaje_V": 48,
                     "eta_rte_pct": 960})
check("RTE=960% → bloquea", not r["ok"])

# 6. RTE < 50 % (mal digitado, p.ej. 0.96 escrito como 9.6) → bloquea
r = validar_bateria({"capacidad_kWh": 10, "potencia_kW": 5, "voltaje_V": 48,
                     "eta_rte_pct": 9.6})
check("RTE=9.6% → bloquea", not r["ok"])

# 7. C-rate imposible: 100 kW sobre 10 kWh (¿capacidad en Ah?) → bloquea
r = validar_bateria({"capacidad_kWh": 10, "potencia_kW": 100, "voltaje_V": 48})
check("C-rate=10C → bloquea", not r["ok"])

# 8. Voltaje absurdo (48000 V — ¿mWh digitados?) → bloquea
r = validar_bateria({"capacidad_kWh": 10, "potencia_kW": 5, "voltaje_V": 48000})
check("Voltaje=48000V → bloquea", not r["ok"])

# 9. Plomo-ácido legítimo (DoD 50, RTE 80) → NO bloquea
r = validar_bateria({"capacidad_kWh": 9.6, "potencia_kW": 2.4, "voltaje_V": 48,
                     "dod_pct": 50, "eta_rte_pct": 80, "ciclos_vida": 1500})
check("Plomo-ácido DoD 50/RTE 80 → ok", r["ok"], f"(errores: {r['errores']})")

# 10. RTE 75 % (plomo) → avisa sin bloquear
r = validar_bateria({"capacidad_kWh": 9.6, "potencia_kW": 2.4, "voltaje_V": 48,
                     "dod_pct": 50, "eta_rte_pct": 75})
check("RTE=75% → avisa sin bloquear",
      r["ok"] and any("RTE" in a for a in r["avisos"]), f"({r['avisos']})")

# 11. C-rate 2C (HV de potencia) → avisa sin bloquear
r = validar_bateria({"capacidad_kWh": 10, "potencia_kW": 35, "voltaje_V": 400})
check("C-rate=3.5C → avisa sin bloquear",
      r["ok"] and any("C-rate" in a for a in r["avisos"]), f"({r['errores']})")

# 12. Solo capacidad (defaults del loader ausentes) → avisa, no bloquea
r = validar_bateria({"capacidad_kWh": 15})
check("Solo capacidad → avisa sin bloquear", r["ok"] and len(r["avisos"]) >= 2)

# 13. Costo absurdo (42 USD para 11 kWh → 3.8 USD/kWh) → avisa
r = validar_bateria({"capacidad_kWh": 11.04, "potencia_kW": 5, "voltaje_V": 48,
                     "costo_usd": 42})
check("Costo 3.8 USD/kWh → avisa",
      r["ok"] and any("kWh" in a for a in r["avisos"]), f"({r['avisos']})")

# 14. Capacidad sospechosa (5000 — ¿está en Wh?) → avisa sin bloquear
r = validar_bateria({"capacidad_kWh": 5000, "voltaje_V": 48})
check("Capacidad=5000 kWh → avisa",
      r["ok"] and any("Wh" in a for a in r["avisos"]), f"({r['avisos']})")

# 15. Todo vacío → bloquea solo por capacidad
r = validar_bateria({})
check("Todo vacío → bloquea por capacidad", not r["ok"] and len(r["errores"]) == 1,
      f"({r['errores']})")

# 16. Defaults del loader marcados → avisa que no vienen del Excel
r = validar_bateria({"capacidad_kWh": 10, "potencia_kW": 5, "voltaje_V": 48,
                     "dod_pct": 80, "eta_rte_pct": 95, "ciclos_vida": 3000,
                     "_defaults_aplicados": ["dod_pct", "eta_rte_pct", "ciclos_vida"]})
check("Defaults del loader → avisa sin bloquear",
      r["ok"] and sum("por defecto" in a for a in r["avisos"]) == 3
      and r["campos"]["dod_pct"]["estado"] == "warn", f"({r['avisos']})")

print(f"\n{'='*60}\nRESULTADO: {PASS} OK · {FAIL} FALLOS")
sys.exit(1 if FAIL else 0)
