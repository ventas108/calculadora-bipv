# -*- coding: utf-8 -*-
"""Pruebas del Asistente (guía determinista + base de conocimiento RAG)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculos.asistente import (
    BaseConocimiento, RUTA_BASE_CONOCIMIENTO, avisos_coherencia,
    contexto_sesion, evaluar_flujo, responder, siguiente_paso,
)

FALLOS = []

def check(nombre, cond, detalle=""):
    print(("✅" if cond else "❌"), nombre + (f" — {detalle}" if detalle else ""))
    if not cond:
        FALLOS.append(nombre)

# ══ 1. Sesión vacía ═══════════════════════════════════════════════════════════
chk = evaluar_flujo({})
check("Sesión vacía: ningún paso listo", all(i["estado"] != "listo" for i in chk))
sig = siguiente_paso(chk)
check("Sesión vacía: siguiente = Proyecto", sig and "Proyecto" in sig["pagina"], str(sig and sig["pagina"]))

# ══ 2. Flujo a medias ════════════════════════════════════════════════════════
estado = {"nombre_proyecto": "Urabá", "ciudad": "Apartadó", "tmy_df": object(),
          "panel_dict": {"P": 720}}
chk = evaluar_flujo(estado)
listos = [i["pagina"] for i in chk if i["estado"] == "listo"]
check("Proyecto/Recurso/MotorIV listos", len(listos) == 3, str(listos))
sig = siguiente_paso(chk)
check("Siguiente = Dimensionamiento", sig and "Dimensionamiento" in sig["pagina"], str(sig and sig["pagina"]))

# Producción bloqueada sin inversor:
prod = next(i for i in chk if "Producción" in i["pagina"])
check("Producción bloqueada (falta inversor)", prod["estado"] == "bloqueado"
      and "inversor_dict_dim" in prod["faltan_previas"])

# ══ 3. Avisos de coherencia ══════════════════════════════════════════════════
avisos = avisos_coherencia({"bypass_result": object()})
check("Aviso: bypass sin aplicar en Producción", any("Producción" in a for a in avisos))
avisos = avisos_coherencia({"csv_fs_sketchup_bytes": b"x"})
check("Aviso: CSV SketchUp pendiente de usar", any("SketchUp" in a for a in avisos))
avisos = avisos_coherencia({"metricas_financiero": object()})
check("Aviso: Financiero sin costos blandos", any("Blandos" in a or "blandos" in a for a in avisos))
check("Sesión vacía sin avisos", avisos_coherencia({}) == [])

# ══ 4. Base de conocimiento ══════════════════════════════════════════════════
check("Base de conocimiento existe", os.path.exists(RUTA_BASE_CONOCIMIENTO))
base = BaseConocimiento.cargar()
check("Base con >30 secciones", len(base.secciones) > 30, str(len(base.secciones)))

res = base.buscar("¿cómo uso las sombras desde SketchUp?")
check("Búsqueda encuentra sección de SketchUp",
      any("SketchUp" in s["titulo"] for s in res), str([s["titulo"] for s in res][:3]))

res = base.buscar("comparador de inversores clipping ratio")
check("Búsqueda encuentra el Comparador",
      any("Comparador" in s["titulo"] or "comparador" in s["texto"].lower() for s in res),
      str([s["titulo"] for s in res][:3]))

res = base.buscar("ley 1715 beneficios tributarios")
check("Búsqueda encuentra Ley 1715 (financiero)",
      any("1715" in s["texto"] for s in res), str([s["titulo"] for s in res][:3]))

check("Pregunta vacía no rompe", base.buscar("") == [])
check("Pregunta sin coincidencias no rompe", base.buscar("xyzzy quimera") == [])

# ══ 5. Contexto de sesión para el modelo ═════════════════════════════════════
ctx = contexto_sesion(estado)
check("Contexto incluye siguiente paso", "Siguiente paso" in ctx)
check("Contexto marca pasos listos", ctx.count("✅") == 3, f"{ctx.count('✅')} ✅")

# ══ 6. Sin clave de API → error claro, no silencioso ═════════════════════════
guardadas = {k: os.environ.pop(k, None)
             for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")}
try:
    try:
        responder("hola", {}, base=base)
        check("Sin clave: lanza RuntimeError", False)
    except RuntimeError as e:
        check("Sin clave: lanza RuntimeError con instrucción",
              "GEMINI_API_KEY" in str(e))
finally:
    for k, v in guardadas.items():
        if v is not None:
            os.environ[k] = v

print()
if FALLOS:
    print(f"❌ {len(FALLOS)} fallo(s): {FALLOS}")
    sys.exit(1)
print("✅ Todas las pruebas del Asistente pasaron.")
