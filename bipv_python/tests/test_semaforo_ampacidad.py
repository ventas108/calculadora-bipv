# -*- coding: utf-8 -*-
"""
Semáforo de ampacidad (7-sep-2026) -- calculos/diagrama_unifilar.py::
calcular_semaforo_ampacidad(), integrada en calcular_perdida_ohmica().

Contexto: el usuario pidió verificar si era seguro auto-sugerir el calibre
por ampacidad. La respuesta fue NO en la forma de un semáforo único
"✅ seguro / ❌ inseguro" -- la ampacidad real depende del método de
instalación, del agrupamiento de circuitos y de la temperatura ambiente
real, ninguno de los cuales esta app le pregunta hoy al usuario. Dar una luz
verde única fingiría un juicio de ingeniería sin la información para
hacerlo.

En cambio, se implementó un RANKING de escenarios NOMBRADOS y citables:
  - DC: ficha técnica real del fabricante Eland Cables para el cable solar
    H1Z2Z2-K (EN 50618) -- 3 condiciones de instalación reales publicadas.
  - AC: NTC 2050 / NEC Tabla 310-16 -- 3 tipos de aislamiento (60/75/90°C).
Cada escenario tiene su propio semáforo (verde ≤70% de margen, amarillo
70-100%, rojo >100%) -- nunca uno solo "certificado" para el proyecto.

Casos cubiertos:
  - Verificación a mano de la física (corriente/ampacidad) en ambas tablas.
  - Ranking ordenado de mayor a menor ampacidad.
  - Umbrales del semáforo (verde/amarillo/rojo) en los bordes exactos.
  - Nunca inventa: sin corriente, sin calibre, calibre sin dato en la tabla,
    o tabla desconocida -- todos devuelven escenarios vacíos, no un
    semáforo falso.
  - Integración con calcular_perdida_ohmica(): cada tramo DC recibe su
    propio semáforo con la corriente ESCALADA por su fracción de paneles
    (no la corriente total del proyecto), y el tramo AC recibe el suyo.
"""
import pytest

from calculos.diagrama_unifilar import (
    calcular_perdida_ohmica,
    calcular_semaforo_ampacidad,
    AMPACIDAD_H1Z2Z2K_A,
    AMPACIDAD_NTC2050_A,
)

PANEL = {"Isc_stc": 10.0}
INVERSOR = {"P_ac_nom_W": 15_000.0}


def test_h1z2z2k_margen_calculado_a_mano():
    # 6 mm2, ampacidad publicada por el fabricante: 70/67/57 A.
    r = calcular_semaforo_ampacidad(6.0, 25.0, "h1z2z2k")
    assert len(r["escenarios"]) == 3
    esc = {e["nombre"]: e for e in r["escenarios"]}
    assert esc["Cable único, al aire libre"]["ampacidad_A"] == 70
    assert esc["Cable único, al aire libre"]["margen_pct"] == pytest.approx(25.0 / 70 * 100, abs=0.1)
    assert esc["2 cables juntos, sobre superficie"]["ampacidad_A"] == 57


def test_ntc2050_margen_calculado_a_mano():
    # 16 mm2, ampacidad NTC2050: 55/65/75 A (60/75/90°C).
    r = calcular_semaforo_ampacidad(16.0, 40.0, "ntc2050")
    esc = {e["nombre"]: e for e in r["escenarios"]}
    assert esc["Aislamiento 60°C (ej. TW)"]["ampacidad_A"] == 55
    assert esc["Aislamiento 90°C (ej. THHN/THWN-2)"]["ampacidad_A"] == 75
    assert esc["Aislamiento 90°C (ej. THHN/THWN-2)"]["margen_pct"] == pytest.approx(40.0 / 75 * 100, abs=0.1)


def test_ranking_ordenado_de_mayor_a_menor_ampacidad():
    r = calcular_semaforo_ampacidad(10.0, 30.0, "h1z2z2k")
    ampacidades = [e["ampacidad_A"] for e in r["escenarios"]]
    assert ampacidades == sorted(ampacidades, reverse=True)


@pytest.mark.parametrize("margen_pct_objetivo, semaforo_esperado", [
    (50.0, "verde"),
    (70.0, "verde"),      # borde inclusive
    (70.1, "amarillo"),
    (100.0, "amarillo"),  # borde inclusive
    (100.1, "rojo"),
    (250.0, "rojo"),
])
def test_umbrales_del_semaforo_en_los_bordes_exactos(margen_pct_objetivo, semaforo_esperado):
    # calibre 25mm2, ampacidad "aire libre" = 176 A -- se elige la corriente
    # de diseño para dar exactamente el margen_pct_objetivo en ESE escenario.
    ampacidad_aire_libre = AMPACIDAD_H1Z2Z2K_A[25.0][0]
    corriente = ampacidad_aire_libre * margen_pct_objetivo / 100.0
    r = calcular_semaforo_ampacidad(25.0, corriente, "h1z2z2k")
    fila_aire_libre = next(e for e in r["escenarios"] if e["nombre"] == "Cable único, al aire libre")
    assert fila_aire_libre["semaforo"] == semaforo_esperado


def test_nunca_inventa_sin_corriente_sin_calibre_o_tabla_desconocida():
    assert calcular_semaforo_ampacidad(6.0, None, "h1z2z2k")["escenarios"] == []
    assert calcular_semaforo_ampacidad(6.0, 0.0, "h1z2z2k")["escenarios"] == []
    assert calcular_semaforo_ampacidad(None, 25.0, "h1z2z2k")["escenarios"] == []
    assert calcular_semaforo_ampacidad(6.0, 25.0, "tabla_inexistente")["escenarios"] == []


def test_calibre_sin_dato_en_la_tabla_no_inventa():
    # NTC2050 no tiene dato verificado arriba de 120 mm2 -- a propósito.
    r = calcular_semaforo_ampacidad(150.0, 300.0, "ntc2050")
    assert r["escenarios"] == []
    assert r["sin_dato_calibre"] is True
    assert r["fuente"] is not None  # la fuente se informa aunque no haya dato de ESTE calibre


def test_todos_los_calibres_comerciales_dc_tienen_dato_h1z2z2k():
    # El calibre AC (NTC2050) declara explícitamente que solo llega a 120mm2 --
    # pero el DC (H1Z2Z2-K) debe cubrir los 15 calibres comerciales completos,
    # porque la ficha del fabricante sí los trae todos.
    from calculos.diagrama_unifilar import CALIBRES_COMERCIALES_MM2
    for calibre in CALIBRES_COMERCIALES_MM2:
        assert calibre in AMPACIDAD_H1Z2Z2K_A, f"falta dato H1Z2Z2-K para {calibre} mm2"


# ── Integración con calcular_perdida_ohmica() ────────────────────────────────
def test_tramo_unico_recibe_semaforo_con_la_corriente_total():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[{"nombre": "Techo", "longitud_m": 20.0, "calibre_mm2": 6.0, "n_paneles": 40}],
        longitud_ac_m=15.0, calibre_ac_mm2=16.0,
    )
    tramo = r["tramos"][0]
    assert tramo["fraccion_paneles"] == 1.0
    assert tramo["corriente_diseno_A"] == pytest.approx(r["corriente_dc_diseno_A"])
    assert len(tramo["semaforo_ampacidad"]["escenarios"]) == 3
    assert len(r["semaforo_ampacidad_ac"]["escenarios"]) == 3


def test_multi_tramo_escala_la_corriente_por_fraccion_no_usa_la_total():
    # Bug que este diseño evita a propósito: si el semáforo comparara la
    # corriente TOTAL del proyecto contra CADA tramo (en vez de la fracción
    # de ese tramo), un proyecto multi-superficie mostraría un riesgo de
    # ampacidad muchísimo mayor al real para cada tramo individual.
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[
            {"nombre": "Sur", "longitud_m": 10.0, "calibre_mm2": 6.0, "n_paneles": 30},
            {"nombre": "Norte", "longitud_m": 10.0, "calibre_mm2": 6.0, "n_paneles": 10},
        ],
        n_paneles_total=40,
    )
    tramo_sur = next(t for t in r["tramos"] if t["nombre"] == "Sur")
    tramo_norte = next(t for t in r["tramos"] if t["nombre"] == "Norte")
    assert tramo_sur["corriente_diseno_A"] == pytest.approx(r["corriente_dc_diseno_A"] * 0.75)
    assert tramo_norte["corriente_diseno_A"] == pytest.approx(r["corriente_dc_diseno_A"] * 0.25)
    # La corriente del tramo Sur (75% del total) debe ser mayor que la de
    # Norte (25%) -- y por tanto su margen de ampacidad más ajustado.
    margen_sur = tramo_sur["semaforo_ampacidad"]["escenarios"][0]["margen_pct"]
    margen_norte = tramo_norte["semaforo_ampacidad"]["escenarios"][0]["margen_pct"]
    assert margen_sur > margen_norte


def test_tramo_sin_calibre_no_tiene_semaforo():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=400.0,
        tramos_dc=[{"nombre": "Techo", "n_paneles": 40}],  # sin longitud/calibre
    )
    assert r["tramos"][0]["semaforo_ampacidad"]["escenarios"] == []


def test_sin_tension_red_v_el_semaforo_ac_no_inventa():
    r = calcular_perdida_ohmica(
        panel=PANEL, inversor=INVERSOR, N_strings_tracker=2, n_inversores=1,
        tension_red_V=None,
        longitud_ac_m=15.0, calibre_ac_mm2=16.0,
    )
    assert r["semaforo_ampacidad_ac"]["escenarios"] == []
