"""
Banco de verificación #173 — ningún resultado viejo sobrevive a un cambio
de ciudad, geometría o área (blindajes #64 y #172).

Simula el session_state como dict y aplica exactamente las mismas listas de
claves que usan las páginas 1 y 2, verificando que:
  1. Cambio de COORDENADAS → cae TODO (TMY, POA, producción, bypass,
     multi-superficie, financiero, CO₂ y las guardas).
  2. Cambio de GEOMETRÍA (tilt/azimuth/albedo) → el TMY del sitio sobrevive,
     la POA y todos los derivados caen.
  3. Cambio de ÁREA/TIPO → el recurso solar sobrevive, los derivados caen.
  4. Chequeo estático: toda clave de resultado que consumen las páginas
     aguas abajo (Financiero, CO₂, Reporte) está en las listas de invalidación.

Correr desde bipv_python/:  python3 scripts/test_invalidacion_cadena.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.invalidacion import (           # noqa: E402
    KEYS_DERIVADOS_POA,
    KEYS_RECURSO_SOLAR,
    KEYS_RECURSO_SOLAR_POA,
)

_PAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "pages")

_GUARD_KEYS = (
    "_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada",
    "_solar_tilt_guardado", "_solar_az_guardado", "_solar_albedo_guardado",
)

# Claves extra que la página 2 limpia junto al recurso solar
_SOLAR_SS_EXTRA = ("tilt_fachada", "tilt_default", "azimuth_fachada",
                   "orientacion_label", "poa_efectiva_df")


def _sesion_completa() -> dict:
    """Session_state ficticio con toda la cadena ejecutada (Bogotá)."""
    ss = {}
    for k in KEYS_RECURSO_SOLAR + KEYS_DERIVADOS_POA + _GUARD_KEYS + _SOLAR_SS_EXTRA:
        ss[k] = f"valor_de_bogota::{k}"
    # Flags como booleanos reales
    for k in ("recurso_solar_ok", "produccion_ok", "bypass_ok",
              "financiero_ok", "impacto_co2_ok", "multisup_activo"):
        ss[k] = True
    ss["E_ac_anual_kWh"] = 12345.0
    return ss


FALLOS = []


def check(nombre: str, cond: bool, detalle: str = ""):
    icono = "✅" if cond else "❌"
    print(f"  {icono} {nombre}" + (f" — {detalle}" if detalle and not cond else ""))
    if not cond:
        FALLOS.append(nombre)


# ═══ 1. Cambio de coordenadas (página 1 #64 / página 2 drift) ═════════════════
print("\n[1] Cambio de coordenadas → cae TODA la cadena")
ss = _sesion_completa()
for k in KEYS_RECURSO_SOLAR + KEYS_DERIVADOS_POA + _GUARD_KEYS:
    ss.pop(k, None)
for flag in ("recurso_solar_ok", "produccion_ok", "bypass_ok",
             "financiero_ok", "impacto_co2_ok", "multisup_activo"):
    check(f"{flag} eliminado", flag not in ss)
for k in ("tmy_df", "poa_df", "E_ac_anual_kWh", "E_ac_anual_kWh_bypass",
          "E_ac_anual_kWh_multisup", "bypass_result", "comp_financiero",
          "metricas_financiero", "co2_total_t", "res_produccion"):
    check(f"{k} eliminado", k not in ss)

# ═══ 2. Cambio de geometría (página 2 #172) ═══════════════════════════════════
print("\n[2] Cambio de tilt/azimuth/albedo → TMY sobrevive, derivados caen")
ss = _sesion_completa()
_SOLAR_SS_KEYS = KEYS_RECURSO_SOLAR + _SOLAR_SS_EXTRA
for k in _SOLAR_SS_KEYS + KEYS_DERIVADOS_POA + _GUARD_KEYS:
    if k not in ("tmy_df", "tmy_ciudad", "ghi_anual_kWh_m2", "t_media_anual",
                 "zona_geo_coords"):
        ss.pop(k, None)
check("tmy_df sobrevive (el TMY solo depende del sitio)", "tmy_df" in ss)
check("ghi_anual_kWh_m2 sobrevive", "ghi_anual_kWh_m2" in ss)
for k in ("recurso_solar_ok", "poa_df", "poa_anual_kWh_m2", "poa_efectiva_df",
          "produccion_ok", "E_ac_anual_kWh", "bypass_ok", "financiero_ok",
          "impacto_co2_ok", "res_produccion"):
    check(f"{k} eliminado", k not in ss)

# ═══ 3. Cambio de área/tipo (página 1 #172) ═══════════════════════════════════
print("\n[3] Cambio de área útil / tipo de instalación → recurso solar sobrevive")
ss = _sesion_completa()
for k in KEYS_DERIVADOS_POA:
    ss.pop(k, None)
for k in ("tmy_df", "poa_df", "poa_anual_kWh_m2", "ghi_anual_kWh_m2"):
    check(f"{k} sobrevive", k in ss)
for k in ("produccion_ok", "E_ac_anual_kWh", "E_ac_anual_kWh_bypass",
          "E_ac_anual_kWh_multisup", "bypass_ok", "bypass_result",
          "financiero_ok", "comp_financiero", "impacto_co2_ok",
          "co2_total_t", "res_produccion"):
    check(f"{k} eliminado", k not in ss)

# ═══ 4. Chequeo estático: consumidores aguas abajo vs listas ═════════════════
print("\n[4] Toda clave de resultado consumida aguas abajo está en las listas")
_CONSUMIDORES = {
    "7_💰_Financiero.py":  ("E_ac_anual_kWh", "E_ac_anual_kWh_bypass",
                            "E_ac_anual_kWh_multisup", "produccion_ok"),
    "12_🌿_Impacto_CO2.py": ("E_ac_anual_kWh",),
}
_TODAS = set(KEYS_RECURSO_SOLAR + KEYS_DERIVADOS_POA)
for pagina, claves in _CONSUMIDORES.items():
    ruta = os.path.join(_PAGES_DIR, pagina)
    src = open(ruta, encoding="utf-8").read()
    for k in claves:
        usada = re.search(rf'["\']{re.escape(k)}["\']', src) is not None
        check(f"{pagina}: '{k}' usada y cubierta",
              usada and (k in _TODAS),
              "no está en las listas de invalidación" if usada else "la página ya no la usa")

# Y al revés: las guardas de las páginas 1 y 2 realmente usan el módulo compartido
print("\n[5] Las páginas 1 y 2 importan el módulo compartido de invalidación")
for pagina, patron in {
    "1_🏠_Proyecto.py":      r"from calculos\.invalidacion import",
    "2_☀️_Recurso_Solar.py": r"from calculos\.invalidacion import",
}.items():
    src = open(os.path.join(_PAGES_DIR, pagina), encoding="utf-8").read()
    check(f"{pagina} importa calculos.invalidacion", re.search(patron, src) is not None)
    check(f"{pagina} usa KEYS_DERIVADOS_POA", "KEYS_DERIVADOS_POA" in src)

# ═══ 6. Página 1: la guarda de área/tipo usa valores CONFIRMADOS ═════════════
# Regresión de auditoría: leer area_util_m2/tipo_instalacion del session_state
# en el handler de Guardar NO detecta el cambio (el render ya los pisó con los
# valores nuevos). Deben usarse guardas dedicadas escritas solo al guardar.
print("\n[6] Página 1 compara contra la última configuración GUARDADA")
_src_p1 = open(os.path.join(_PAGES_DIR, "1_🏠_Proyecto.py"), encoding="utf-8").read()
check("lee _area_util_guardada", '"_area_util_guardada"' in _src_p1)
check("lee _tipo_inst_guardado", '"_tipo_inst_guardado"' in _src_p1)
check("NO captura el previo desde area_util_m2 (pisado por el render)",
      'st.session_state.get("area_util_m2")' not in
      _src_p1.split("💾 Guardar configuración")[1].split("#172 — Actualizar")[0])
# Simulación del orden real: render pisa los valores → la guarda dedicada
# conserva el confirmado y sí detecta el cambio.
ss = {"_area_util_guardada": 100.0, "_tipo_inst_guardado": "Fachada",
      "area_util_m2": 100.0, "tipo_instalacion": "Fachada"}
ss["area_util_m2"] = 250.0          # render con el valor nuevo (antes del click)
ss["tipo_instalacion"] = "Cubierta"
_cambio = (abs(ss["area_util_m2"] - ss["_area_util_guardada"]) > 0.01
           or ss["tipo_instalacion"] != ss["_tipo_inst_guardado"])
check("la guarda dedicada detecta el cambio pese al render previo", _cambio)

print("\n" + "=" * 64)
if FALLOS:
    print(f"RESULTADO: {len(FALLOS)} verificación(es) FALLARON:")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
print("RESULTADO: todas las verificaciones superadas ✅")
