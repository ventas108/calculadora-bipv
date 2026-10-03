# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.path.insert(0, "/workspaces/calculadora-bipv/bipv_python")

import numpy as np
import pandas as pd
from pvlib.iotools import epw as pvlib_epw

from calculos.sitedesigner_marsh import cargar_escena_sitedesigner
from calculos.sombras_3d import calcular_fs_horario_por_superficie, validar_puntos, ESTADOS_SOMBRA_ACEPTABLES
from calculos.modelo_iv import estimar_sdm_desde_ficha
from calculos.transicion_multisuperficie import superficie_nueva
from calculos.vinculador_sombra_multisuperficie import (
    construir_y_recalcular_proyecto_fisico, aplicar_sombra_a_superficies,
)
from calculos.adaptador_multisuperficie import aplicar_proyecto_a_session_state

LAT, LON, ALT_M = 4.634, -74.148, 2550.0
INVERSOR_ID = "Fronius-Primo-15"
ETA_INVERSOR = 0.986
N_SERIE, N_PARALELO = 10, 7
_HORAS_ANIO = 8760
G = Path("/tmp/claude-1000/-workspaces-calculadora-bipv/a911aa20-79cb-4c25-9d11-10e46335b71c/scratchpad/geom")
_EPW = Path("/workspaces/calculadora-bipv/references/bogota-eldorado-iwec.epw")

def _tmy_epw_real():
    data, meta = pvlib_epw.read_epw(str(_EPW))
    return pd.DataFrame({
        "G_h": data["ghi"].to_numpy(dtype=float), "Gb_n": data["dni"].to_numpy(dtype=float),
        "Gd_h": data["dhi"].to_numpy(dtype=float), "T2m": data["temp_air"].to_numpy(dtype=float),
    }, index=data.index)

def _ficha_sunpower_max3_400():
    return {
        "nombre": "SPR-MAX3-400", "fabricante": "SunPower (Maxeon Solar Technologies)",
        "tecnologia": "Mono-Si", "transparencia_pct": 0,
        "sdm_estimado": True,
        "Voc_stc": 75.6, "Vmp_stc": 65.8, "Isc_stc": 6.58, "Imp_stc": 6.08,
        "Pmax_stc": 65.8 * 6.08,
        "Tk_beta": -0.236, "Tk_alfa": 0.058, "Tk_gamma": -0.27,
        "N_s": 104, "NOCT": 45.0,
        "largo_mm": 1690, "ancho_mm": 1046, "area_m2": 1.690 * 1.046,
    }

def _panel():
    ficha = _ficha_sunpower_max3_400()
    return {**ficha, **estimar_sdm_desde_ficha(ficha)}

def correr_escenario(nombre_json, etiqueta, puntos_archivo):
    with open(G / nombre_json, "rb") as f:
        malla, meta_escena = cargar_escena_sitedesigner(f.read())

    with open(G / puntos_archivo) as f:
        pts = json.load(f)
    puntos_por_superficie = {
        "Fachada-Sureste": pts["puntos_Fachada-Sureste"],
        "Fachada-Suroeste": pts["puntos_Fachada-Suroeste"],
    }
    for nombre_sup, lista in puntos_por_superficie.items():
        avisos = validar_puntos(malla, lista)
        if avisos:
            print(f"  [{etiqueta}] AVISOS puntos {nombre_sup}:", avisos)

    tmy = _tmy_epw_real()
    geometrias = {
        "Fachada-Sureste": {"tilt_deg": 90.0, "azimuth_deg": 162.0},
        "Fachada-Suroeste": {"tilt_deg": 90.0, "azimuth_deg": 249.0},
    }
    resultados_sombra = calcular_fs_horario_por_superficie(
        malla, puntos_por_superficie, LAT, LON, tmy, geometrias,
        malla_horizonte=meta_escena["malla_fingerprint"],
        fuente="externa_marsh",
    )

    panel = _panel()
    superficies = []
    for nombre_sup, tilt, az in (
        ("Fachada-Sureste", 90.0, 162.0), ("Fachada-Suroeste", 90.0, 249.0),
    ):
        area = panel["area_m2"] * N_SERIE * N_PARALELO
        sup = superficie_nueva(
            nombre=nombre_sup, tipo="Fachada", tilt_deg=tilt, azimuth_deg=az,
            area_m2=area, panel=panel, n_serie=N_SERIE, n_paralelo=N_PARALELO,
            inversor_id=INVERSOR_ID, p_shade=np.zeros(_HORAS_ANIO), albedo=0.20,
        )
        superficies.append(sup)

    superficies_con_sombra = aplicar_sombra_a_superficies(superficies, resultados_sombra)

    session_state = {
        "panel_dict": panel,
        "superficies_bipv": superficies_con_sombra,
        "multisup_inversores": [
            {"inversor_id": INVERSOR_ID, "tipo": "compartido",
             "eta_inversor": ETA_INVERSOR, "P_ac_nom_W": None, "ficha": {}},
        ],
        "multisup_malla_meta": meta_escena,
    }

    proyecto = construir_y_recalcular_proyecto_fisico(session_state, tmy, lat=LAT, lon=LON, alt_m=ALT_M)

    resumen = {}
    for nombre_sup in ("Fachada-Sureste", "Fachada-Suroeste"):
        sup_res = proyecto["superficies"][nombre_sup]
        dc, ac = sup_res["resultados_dc"], sup_res["resultados_ac"]
        cobertura = superficies_con_sombra[
            0 if nombre_sup == "Fachada-Sureste" else 1
        ].get("cobertura_sombra", {})
        p_shade_arr = superficies_con_sombra[
            0 if nombre_sup == "Fachada-Sureste" else 1
        ].get("p_shade")
        horas_sombreadas_pct = float(np.mean(p_shade_arr > 0.01) * 100.0) if p_shade_arr is not None else None
        perdida_sombra_pct = float(np.mean(p_shade_arr) * 100.0) if p_shade_arr is not None else None
        estado = superficies_con_sombra[
            0 if nombre_sup == "Fachada-Sureste" else 1
        ].get("estado_sombra")
        resumen[nombre_sup] = {
            "estado_sombra": estado,
            "poa_anual_kWh_m2": round(dc["poa_anual_kWh_m2"], 2),
            "E_dc_anual_kWh": round(dc["E_dc_anual_kWh"], 1),
            "E_ac_anual_kWh": round(ac["E_ac_anual_kWh"], 1),
            "rendimiento_esp_kWh_kWp": round(ac["E_ac_anual_kWh"] / ac["P_dc_stc_kW"], 2),
            "PR": round((ac["E_ac_anual_kWh"] / ac["P_dc_stc_kW"]) / dc["poa_anual_kWh_m2"], 4),
            "horas_shade_gt_1pct_pct": round(horas_sombreadas_pct, 3) if horas_sombreadas_pct is not None else None,
            "perdida_sombra_media_pct": round(perdida_sombra_pct, 3) if perdida_sombra_pct is not None else None,
            "cobertura": cobertura,
        }
    return resumen, meta_escena["malla_fingerprint"]

RESULTADOS = {}
for nombre_json, etiqueta, puntos_archivo in [
    ("torre_central.json", "TORRE central (SO=SE=17.29m)", "puntos_analisis_central.json"),
    ("torre_so_estrecha_12m.json", "sensibilidad SO=12m", "puntos_analisis_estrecha_12m.json"),
    ("torre_so_ancha_25m.json", "sensibilidad SO=25m", "puntos_analisis_ancha_25m.json"),
    ("torre_mas_arboles_central.json", "TORRE + arboles (central)", "puntos_analisis_central.json"),
]:
    print(f"\n=== {etiqueta} ({nombre_json}) ===")
    resumen, fp = correr_escenario(nombre_json, etiqueta, puntos_archivo)
    RESULTADOS[etiqueta] = resumen
    print("fingerprint:", fp)
    print(json.dumps(resumen, indent=2, default=str))


import json as _json
with open(str(G) + "/RESULTADOS_FINALES.json", "w", encoding="utf-8") as f:
    _json.dump(RESULTADOS, f, indent=2, default=str, ensure_ascii=False)
print("\nGuardado RESULTADOS_FINALES.json")
