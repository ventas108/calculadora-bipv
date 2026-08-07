# -*- coding: utf-8 -*-
"""
Test #120 — Cambio de ciudad borra los datos solares viejos (guarda la #64).

Sin este test, es fácil romper la invalidación en futuros cambios (olvidar una
key nueva en la lista, reordenar código, etc.) y que Producción/Financiero
terminen mezclando el clima de una ciudad con el proyecto de otra.

Estrategia (streamlit no está instalado, las páginas no se pueden importar):
1. Se extraen con `ast` las tuplas de keys REALES del código fuente de las
   páginas (_KEYS_LIMPIAR_CIUDAD de Página 1, _SOLAR_SS_KEYS/_GUARD_KEYS de
   Página 2) — si alguien borra una key crítica de la página, el test falla.
2. Se simula el session_state como dict y se aplica la misma limpieza que hace
   la página, verificando el estado final.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculos.invalidacion import (  # noqa: E402
    KEYS_DERIVADOS_POA,
    KEYS_RECURSO_SOLAR,
)

_DIR_PAGES = os.path.join(os.path.dirname(__file__), "..", "pages")
_PAGINA_1 = os.path.join(_DIR_PAGES, "1_🏠_Proyecto.py")
_PAGINA_2 = os.path.join(_DIR_PAGES, "2_☀️_Recurso_Solar.py")

UMBRAL_COORD = 0.0001  # mismo umbral usado en Página 1 y Página 2


def _extraer_tupla_de_strings(ruta_py, nombre_variable):
    """Devuelve la tupla de strings asignada a `nombre_variable` en el archivo."""
    with open(ruta_py, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Assign):
            for destino in nodo.targets:
                if isinstance(destino, ast.Name) and destino.id == nombre_variable:
                    valor = nodo.value
                    if isinstance(valor, (ast.Tuple, ast.List)):
                        out = []
                        for elt in valor.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                out.append(elt.value)
                        return tuple(out)
    raise AssertionError(f"No se encontró la tupla {nombre_variable} en {ruta_py}")


def _session_con_recurso_solar(lat, lon):
    """session_state simulado con recurso solar YA calculado para (lat, lon)."""
    return {
        "ciudad": "Bogotá",
        "lat_proyecto": lat,
        "lon_proyecto": lon,
        "recurso_solar_ok": True,
        "tmy_df": "TMY_DF_VIEJO",          # sentinelas — basta con que existan
        "poa_df": "POA_DF_VIEJO",
        "poa_efectiva_df": "POA_EFECTIVA_VIEJA",
        "poa_anual_kWh_m2": 1500.0,
        "tmy_ciudad": "Bogotá",
        "E_ac_anual_kWh": 12345.0,
        "produccion_ok": True,
        "financiero_ok": True,
        "_solar_lat_guardada": lat,
        "_solar_lon_guardada": lon,
        "_solar_alt_guardada": 2600,
        # keys que NO deben borrarse al cambiar de ciudad
        "nombre_proyecto": "Proyecto demo",
        "panel_sel": "ASP-ST1-T40",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1) La lista de limpieza de Página 1 contiene todas las keys críticas
# ─────────────────────────────────────────────────────────────────────────────
def test_keys_limpiar_ciudad_completas():
    keys = _extraer_tupla_de_strings(_PAGINA_1, "_KEYS_LIMPIAR_CIUDAD")
    criticas = {
        "lat_proyecto", "lon_proyecto",
        "recurso_solar_ok", "tmy_df", "poa_df", "tmy_ciudad",
        "poa_anual_kWh_m2", "poa_efectiva_df", "poa_sin_termico_df",
        "motor_optico_ok",
        "_solar_lat_guardada", "_solar_lon_guardada", "_solar_alt_guardada",
    }
    faltan = criticas - set(keys)
    assert not faltan, (
        f"_KEYS_LIMPIAR_CIUDAD (Página 1) perdió keys críticas: {sorted(faltan)} "
        "— un cambio de ciudad dejaría datos solares viejos vivos."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2) Simulación: cambio de ciudad limpia el recurso solar del session_state
# ─────────────────────────────────────────────────────────────────────────────
def test_cambio_ciudad_borra_datos_solares():
    ss = _session_con_recurso_solar(lat=4.711, lon=-74.072)          # Bogotá
    keys_limpiar = _extraer_tupla_de_strings(_PAGINA_1, "_KEYS_LIMPIAR_CIUDAD")

    # Página 1: `if ciudad != ciudad_anterior:` → pop de todas las keys
    for k in keys_limpiar:
        ss.pop(k, None)

    assert not ss.get("recurso_solar_ok"), "recurso_solar_ok debe quedar False/ausente"
    assert ss.get("tmy_df") is None, "tmy_df de la ciudad anterior sobrevivió"
    assert ss.get("poa_df") is None, "poa_df de la ciudad anterior sobrevivió"
    assert ss.get("poa_efectiva_df") is None, "poa_efectiva_df vieja sobrevivió"
    assert ss.get("_solar_lat_guardada") is None, "guard de lat viejo sobrevivió"
    # Y lo que NO depende de la ciudad se conserva:
    assert ss["nombre_proyecto"] == "Proyecto demo"
    assert ss["panel_sel"] == "ASP-ST1-T40"


# ─────────────────────────────────────────────────────────────────────────────
# 3) Drift en Página 2: detecta diferencia > 0.0001° y limpia; tolera menos
# ─────────────────────────────────────────────────────────────────────────────
def _hay_drift(ss, lat_actual, lon_actual):
    """Réplica exacta del check de drift de coordenadas de Página 2."""
    s_lat = ss.get("_solar_lat_guardada")
    s_lon = ss.get("_solar_lon_guardada")
    if not ss.get("recurso_solar_ok") or s_lat is None:
        return False
    return (
        abs(lat_actual - float(s_lat)) > UMBRAL_COORD
        or abs(lon_actual - float(s_lon)) > UMBRAL_COORD
    )


def test_drift_coordenadas_detecta_y_limpia():
    keys_p2 = (
        _extraer_tupla_de_strings(_PAGINA_2, "_SOLAR_SS_KEYS")
        + _extraer_tupla_de_strings(_PAGINA_2, "_GUARD_KEYS")
        + KEYS_DERIVADOS_POA
    )
    # Las listas de Página 2 deben seguir cubriendo lo esencial:
    faltan = {"recurso_solar_ok", "tmy_df", "poa_df",
              "_solar_lat_guardada", "_solar_lon_guardada"} - set(keys_p2)
    assert not faltan, f"Página 2 perdió keys de limpieza críticas: {sorted(faltan)}"

    # Caso A: Bogotá → Medellín (drift enorme) → limpia todo
    ss = _session_con_recurso_solar(lat=4.711, lon=-74.072)
    assert _hay_drift(ss, lat_actual=6.244, lon_actual=-75.581)
    for k in keys_p2:
        ss.pop(k, None)
    assert not ss.get("recurso_solar_ok")
    assert ss.get("tmy_df") is None and ss.get("poa_df") is None
    assert ss.get("E_ac_anual_kWh") is None, "producción vieja sobrevivió al drift"

    # Caso B: diferencia mínima (> 0.0001°) también cuenta como drift
    ss2 = _session_con_recurso_solar(lat=4.711, lon=-74.072)
    assert _hay_drift(ss2, lat_actual=4.7112, lon_actual=-74.072)

    # Caso C: misma coordenada (dentro de tolerancia) NO dispara limpieza
    ss3 = _session_con_recurso_solar(lat=4.711, lon=-74.072)
    assert not _hay_drift(ss3, lat_actual=4.71105, lon_actual=-74.07203)


# ─────────────────────────────────────────────────────────────────────────────
# 4) invalidacion.py conserva las keys que las páginas asumen
# ─────────────────────────────────────────────────────────────────────────────
def test_modulo_invalidacion_integro():
    assert "recurso_solar_ok" in KEYS_RECURSO_SOLAR
    assert "tmy_df" in KEYS_RECURSO_SOLAR
    assert "poa_df" in KEYS_RECURSO_SOLAR
    assert "poa_efectiva_df" in KEYS_DERIVADOS_POA
    assert "E_ac_anual_kWh" in KEYS_DERIVADOS_POA
    assert "financiero_ok" in KEYS_DERIVADOS_POA


if __name__ == "__main__":
    fallos = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"✅ {nombre}")
            except AssertionError as e:
                fallos += 1
                print(f"❌ {nombre}: {e}")
    print(f"\n{'✅ TODOS LOS TESTS PASARON' if fallos == 0 else f'❌ {fallos} FALLOS'}")
    sys.exit(1 if fallos else 0)
