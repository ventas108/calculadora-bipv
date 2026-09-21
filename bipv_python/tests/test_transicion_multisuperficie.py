# -*- coding: utf-8 -*-
"""Pruebas de la transición transaccional de configuración multi-superficie."""
import numpy as np
import pandas as pd
import pytest

from calculos.transicion_multisuperficie import (
    calcular_huellas,
    inversor_nuevo,
    proyecto_nuevo,
    recalcular_agregados_proyecto,
    recalcular_etapa_inversor_bus,
    recalcular_fisica_superficie,
    recalcular_financiero_co2,
    superficie_nueva,
    transicion_cambiar_geometria,
    transicion_cambiar_inversor,
)

_HORAS_ANIO = 8760

_PANEL = {
    "nombre": "ASP-ST1-T40",
    "Pmax_stc": 300.0,
    "tecnologia": "Mono-Si",
    "Isc_stc": 9.8,
    "Voc_stc": 40.0,
    "Imp_stc": 9.2,
    "Vmp_stc": 32.6,
    "Tk_alfa": 0.05,
    "Tk_beta": -0.30,
    "NOCT": 45.0,
    "a_ref": 1.6,
    "N_s": 60,
    "gamma_ref": 1.05,
    "I_L_ref": 9.85,
    "I_o_ref": 3.0e-10,
    "R_s": 0.35,
    "R_sh_ref": 400.0,
}

_INVERSOR_FICHA = {
    "Vdc_max": 1000.0,
    "Vmppt_activo_min": 200.0,
    "Vmppt_max": 800.0,
    "Isc_max_tracker": 30.0,
}


def _tmy():
    idx = pd.date_range("2023-01-01", periods=_HORAS_ANIO, freq="h", tz="UTC")
    horas = idx.hour.to_numpy()
    t2m = 20.0 + 5.0 * np.sin((horas - 6) / 24.0 * 2 * np.pi)
    # Perfil diurno sintético simple (no pretende ser un TMY real; solo
    # ejercita calcular_poa/pvlib con datos físicamente plausibles: GHI de
    # dia despejado, DNI/DHI en proporciones típicas).
    dia = (horas >= 6) & (horas <= 18)
    forma = np.where(dia, np.sin((horas - 6) / 12.0 * np.pi), 0.0)
    ghi = 700.0 * forma
    dni = 600.0 * forma
    dhi = 150.0 * forma
    return pd.DataFrame(
        {"T2m": t2m, "G_h": ghi, "Gb_n": dni, "Gd_h": dhi}, index=idx
    )


def _p_shade(valor: float = 0.0) -> np.ndarray:
    return np.full(_HORAS_ANIO, valor, dtype=float)


def _proyecto_dos_superficies(inversor_compartido: bool) -> dict:
    """Fachada Este + Fachada Oeste; comparten inversor si se pide."""
    if inversor_compartido:
        inversores = [inversor_nuevo("INV-1", "compartido", eta_inversor=0.97, P_ac_nom_W=6_000.0, inversor=_INVERSOR_FICHA)]
        inv_este, inv_oeste = "INV-1", "INV-1"
    else:
        inversores = [
            inversor_nuevo("INV-ESTE", "dedicado", eta_inversor=0.97, P_ac_nom_W=4_000.0, inversor=_INVERSOR_FICHA),
            inversor_nuevo("INV-OESTE", "dedicado", eta_inversor=0.96, P_ac_nom_W=4_000.0, inversor=_INVERSOR_FICHA),
        ]
        inv_este, inv_oeste = "INV-ESTE", "INV-OESTE"

    superficies = [
        superficie_nueva(
            "Fachada Este", "Fachada", tilt_deg=90, azimuth_deg=90, area_m2=40.0,
            panel=_PANEL, n_serie=10, n_paralelo=4, inversor_id=inv_este,
            p_shade=_p_shade(0.0),
        ),
        superficie_nueva(
            "Fachada Oeste", "Fachada", tilt_deg=90, azimuth_deg=270, area_m2=40.0,
            panel=_PANEL, n_serie=10, n_paralelo=4, inversor_id=inv_oeste,
            p_shade=_p_shade(0.0),
        ),
    ]
    proyecto = proyecto_nuevo(inversores, superficies)

    tmy = _tmy()
    for nombre in list(proyecto["superficies"]):
        sup = proyecto["superficies"][nombre]
        proyecto["superficies"][nombre] = recalcular_fisica_superficie(sup, tmy, lat=4.65, lon=-74.08, alt_m=2600.0)
    for inv_id in list(proyecto["inversores"]):
        proyecto = recalcular_etapa_inversor_bus(proyecto, inv_id)
    proyecto["agregados"] = recalcular_agregados_proyecto(proyecto)
    return proyecto


# ══════════════════════════════════════════════════════════════════════════
# 1. Cambiar orientación de UNA superficie
# ══════════════════════════════════════════════════════════════════════════
def test_cambiar_orientacion_una_superficie_conserva_las_demas():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    huella_oeste_antes = dict(proyecto["superficies"]["Fachada Oeste"]["huellas"])
    inversor_oeste_antes = dict(proyecto["inversores"]["INV-OESTE"])

    resultado = transicion_cambiar_geometria(
        proyecto, "Fachada Este", {"tilt_deg": 75.0, "azimuth_deg": 100.0},
        _p_shade(0.1), _tmy(), lat=4.65, lon=-74.08, alt_m=2600.0,
    )

    assert resultado["ok"] is True
    nuevo = resultado["proyecto"]
    assert nuevo is not proyecto  # nunca muta el original
    assert nuevo["superficies"]["Fachada Este"]["tilt_deg"] == 75.0
    assert nuevo["superficies"]["Fachada Este"]["azimuth_deg"] == 100.0
    # Panel, strings e inversor de la superficie afectada se conservan.
    assert nuevo["superficies"]["Fachada Este"]["panel"]["nombre"] == "ASP-ST1-T40"
    assert nuevo["superficies"]["Fachada Este"]["n_serie"] == 10
    assert nuevo["superficies"]["Fachada Este"]["inversor_id"] == "INV-ESTE"
    # La otra superficie y su inversor quedan bit a bit idénticos.
    assert nuevo["superficies"]["Fachada Oeste"]["huellas"] == huella_oeste_antes
    assert nuevo["inversores"]["INV-OESTE"] == inversor_oeste_antes
    assert "Fachada Oeste" in resultado["conservado"]
    # Los agregados del proyecto se recalcularon.
    assert nuevo["agregados"] != proyecto["agregados"]


def test_cambiar_orientacion_recalcula_poa_sombra_y_produccion_de_la_afectada():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    huellas_antes = dict(proyecto["superficies"]["Fachada Este"]["huellas"])

    resultado = transicion_cambiar_geometria(
        proyecto, "Fachada Este", {"tilt_deg": 90.0, "azimuth_deg": 90.0},
        _p_shade(0.3),  # sombra distinta de la original (0.0)
        _tmy(), lat=4.65, lon=-74.08, alt_m=2600.0,
    )
    assert resultado["ok"] is True
    huellas_despues = resultado["proyecto"]["superficies"]["Fachada Este"]["huellas"]
    # POA se recalcula (misma geometría pero función corrida de nuevo con
    # p_shade distinto obliga a recomputar resultados_dc igualmente).
    assert huellas_despues["sombra"] != huellas_antes["sombra"]
    assert huellas_despues["resultados_dc"] != huellas_antes["resultados_dc"]


# ══════════════════════════════════════════════════════════════════════════
# 2. Cambiar orientación "global" (todas las superficies, una transición por
#    superficie -- cada una conserva a las demás en su propio paso).
# ══════════════════════════════════════════════════════════════════════════
def test_cambiar_orientacion_global_todas_las_superficies():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    nombres = list(proyecto["superficies"])

    for nombre in nombres:
        resultado = transicion_cambiar_geometria(
            proyecto, nombre, {"tilt_deg": 80.0}, _p_shade(0.05),
            _tmy(), lat=4.65, lon=-74.08, alt_m=2600.0,
        )
        assert resultado["ok"] is True, resultado.get("error")
        proyecto = resultado["proyecto"]

    for nombre in nombres:
        assert proyecto["superficies"][nombre]["tilt_deg"] == 80.0
    assert proyecto["agregados"]["n_superficies"] == 2


# ══════════════════════════════════════════════════════════════════════════
# 3 y 7. Cambiar inversor DEDICADO -- conserva geometria/sombra/POA/panel
# ══════════════════════════════════════════════════════════════════════════
def test_cambiar_inversor_dedicado_conserva_poa_y_sombra():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    huellas_antes = dict(proyecto["superficies"]["Fachada Este"]["huellas"])

    resultado = transicion_cambiar_inversor(proyecto, "INV-ESTE", {"eta_inversor": 0.95})

    assert resultado["ok"] is True
    huellas_despues = resultado["proyecto"]["superficies"]["Fachada Este"]["huellas"]
    for clave in ("geometria", "sombra", "poa", "panel", "resultados_dc"):
        assert huellas_despues[clave] == huellas_antes[clave], clave
    assert huellas_despues["inversor"] == huellas_antes["inversor"]  # es el mismo inversor_id
    assert huellas_despues["resultados_ac"] != huellas_antes["resultados_ac"]
    assert resultado["informes_obsoletos"] is True
    assert resultado["financiero_co2_obsoletos"] is True


def test_cambiar_inversor_compartido_conserva_poa_y_sombra_de_ambas_superficies():
    """Misma verificación que la prueba dedicada, pero con inversor
    COMPARTIDO: cambiar solo el inversor no debe recalcular POA/sombra de
    NINGUNA de las superficies del bus, aunque haya más de una."""
    proyecto = _proyecto_dos_superficies(inversor_compartido=True)
    huellas_antes = {
        nombre: dict(sup["huellas"]) for nombre, sup in proyecto["superficies"].items()
    }

    resultado = transicion_cambiar_inversor(proyecto, "INV-1", {"eta_inversor": 0.94})

    assert resultado["ok"] is True
    for nombre in ("Fachada Este", "Fachada Oeste"):
        huellas_despues = resultado["proyecto"]["superficies"][nombre]["huellas"]
        for clave in ("geometria", "sombra", "poa", "panel", "resultados_dc"):
            assert huellas_despues[clave] == huellas_antes[nombre][clave], (nombre, clave)
        assert huellas_despues["resultados_ac"] != huellas_antes[nombre]["resultados_ac"]


def test_cambiar_inversor_dedicado_calcula_clipping_por_superficie():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    # Inversor deliberadamente pequeño para forzar recorte visible.
    resultado = transicion_cambiar_inversor(proyecto, "INV-ESTE", {"P_ac_nom_W": 500.0})
    assert resultado["ok"] is True
    bus = resultado["proyecto"]["resultados_bus"]["INV-ESTE"]
    assert bus["tipo"] == "dedicado"
    assert bus["superficies"] == ["Fachada Este"]
    assert bus["horas_con_clipping"] > 0
    assert bus["perdida_clipping_kWh"] > 0
    # El otro bus (Fachada Oeste, sin cambios) no se toca.
    assert resultado["proyecto"]["resultados_bus"]["INV-OESTE"] == proyecto["resultados_bus"]["INV-OESTE"]


# ══════════════════════════════════════════════════════════════════════════
# 4 y 5. Cambiar inversor COMPARTIDO -- clipping común hora por hora
# ══════════════════════════════════════════════════════════════════════════
def test_cambiar_inversor_compartido_suma_bus_antes_de_recortar():
    proyecto = _proyecto_dos_superficies(inversor_compartido=True)
    resultado = transicion_cambiar_inversor(proyecto, "INV-1", {"P_ac_nom_W": 3_000.0})
    assert resultado["ok"] is True
    nuevo = resultado["proyecto"]
    bus = nuevo["resultados_bus"]["INV-1"]
    assert set(bus["superficies"]) == {"Fachada Este", "Fachada Oeste"}

    # Verificación hora por hora: el límite se aplica UNA vez sobre la suma,
    # no una vez por superficie (regla 5).
    este = nuevo["superficies"]["Fachada Este"]["resultados_dc"]["P_dc_kW"]
    oeste = nuevo["superficies"]["Fachada Oeste"]["resultados_dc"]["P_dc_kW"]
    eta = nuevo["inversores"]["INV-1"]["eta_inversor"]
    p_ac_sin_recorte_esperado = (este + oeste) * eta
    p_ac_esperado = np.minimum(p_ac_sin_recorte_esperado, 3_000.0 / 1000.0)

    p_ac_este = nuevo["superficies"]["Fachada Este"]["resultados_ac"]["P_ac_kW"]
    p_ac_oeste = nuevo["superficies"]["Fachada Oeste"]["resultados_ac"]["P_ac_kW"]
    np.testing.assert_allclose(p_ac_este + p_ac_oeste, p_ac_esperado, atol=1e-9)

    # Ninguna hora del reparto por superficie excede lo que le corresponde
    # de un recorte aplicado UNA sola vez al bus.
    assert np.all(p_ac_este + p_ac_oeste <= p_ac_sin_recorte_esperado + 1e-9)

    # Falso negativo a vigilar: sumar el clipping de cada superficie
    # calculada INDEPENDIENTEMENTE (mal, regla 5) da un resultado distinto
    # (mayor) al del bus compartido cuando el límite es más ajustado que la
    # suma de límites individuales.
    clip_independiente_este = np.minimum(este * eta, 3_000.0 / 1000.0)
    clip_independiente_oeste = np.minimum(oeste * eta, 3_000.0 / 1000.0)
    suma_independiente = float(np.sum(clip_independiente_este + clip_independiente_oeste))
    assert suma_independiente > bus["E_ac_anual_kWh"]


# ══════════════════════════════════════════════════════════════════════════
# 6. Fallo de una superficie -> rollback completo
# ══════════════════════════════════════════════════════════════════════════
def test_fallo_geometria_hace_rollback_completo():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    p_shade_invalido = np.full(100, 0.5)  # longitud incorrecta -> ValueError interno

    resultado = transicion_cambiar_geometria(
        proyecto, "Fachada Este", {"tilt_deg": 45.0}, p_shade_invalido,
        _tmy(), lat=4.65, lon=-74.08, alt_m=2600.0,
    )

    assert resultado["ok"] is False
    assert resultado["error"]
    assert resultado["proyecto"] is proyecto  # exactamente el original, sin copias parciales
    assert proyecto["superficies"]["Fachada Este"]["tilt_deg"] == 90.0  # sin mutar


def test_fallo_inversor_desconocido_hace_rollback_completo():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    resultado = transicion_cambiar_inversor(proyecto, "INV-FANTASMA", {"eta_inversor": 0.9})
    assert resultado["ok"] is False
    assert resultado["proyecto"] is proyecto


def test_geometria_rechaza_claves_fuera_de_alcance():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    resultado = transicion_cambiar_geometria(
        proyecto, "Fachada Este", {"panel": {"nombre": "otro"}}, _p_shade(0.0),
        _tmy(), lat=4.65, lon=-74.08, alt_m=2600.0,
    )
    assert resultado["ok"] is False
    assert "panel" in resultado["error"]
    assert resultado["proyecto"] is proyecto


# ══════════════════════════════════════════════════════════════════════════
# 8. Producción/Finanzas/CO2/Informes no consumen resultados obsoletos
# ══════════════════════════════════════════════════════════════════════════
def test_cambiar_inversor_no_deja_financiero_co2_obsoleto_en_silencio():
    proyecto = _proyecto_dos_superficies(inversor_compartido=True)
    agregados_antes = dict(proyecto["agregados"])

    parametros_financieros = dict(
        capex_usd=50_000.0, beneficios_1715_usd=0.0, tarifa_cop_kWh=800.0,
        tipo_cambio=4000.0, tasa_escalacion_tarifa=3.0, tasa_degradacion_pct=0.5,
        opex_pct_capex=1.0, n_anos=25, tasa_descuento=0.10,
    )
    parametros_co2 = dict(factor_activo=0.25, factor_promedio=0.30, factor_marginal=0.35)

    resultado_antes = recalcular_financiero_co2(agregados_antes, parametros_financieros, parametros_co2)

    resultado = transicion_cambiar_inversor(proyecto, "INV-1", {"P_ac_nom_W": 2_000.0})
    assert resultado["ok"] is True
    assert resultado["informes_obsoletos"] is True
    assert resultado["financiero_co2_obsoletos"] is True

    agregados_despues = resultado["proyecto"]["agregados"]
    assert agregados_despues["E_ac_total_kWh"] != agregados_antes["E_ac_total_kWh"]

    resultado_despues = recalcular_financiero_co2(agregados_despues, parametros_financieros, parametros_co2)
    # Con un inversor más pequeño (más recorte) la energía y por tanto las
    # métricas financieras/CO2 cambian -- si algo aguas abajo hubiera seguido
    # leyendo el agregado viejo, estos dos resultados serían idénticos.
    assert resultado_despues["E_ac_total_kWh"] < resultado_antes["E_ac_total_kWh"]
    assert resultado_despues["metricas"]["vpn_usd"] != resultado_antes["metricas"]["vpn_usd"]
    assert resultado_despues["co2"]["co2_anual_t"] < resultado_antes["co2"]["co2_anual_t"]


def test_huellas_incluyen_las_seis_dimensiones_requeridas():
    proyecto = _proyecto_dos_superficies(inversor_compartido=False)
    huellas = proyecto["superficies"]["Fachada Este"]["huellas"]
    assert set(huellas) == {"geometria", "sombra", "poa", "panel", "inversor", "resultados_dc", "resultados_ac"}
    assert all(isinstance(v, str) and len(v) == 64 for v in huellas.values())  # sha256 hex
