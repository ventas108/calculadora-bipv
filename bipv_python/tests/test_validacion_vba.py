"""
Tests de validación cruzada: Python vs VBA (XLSM auditado).

Ejecutar:  python -m pytest tests/test_validacion_vba.py -v

Todos los valores de referencia provienen de la hoja
FF_vs_Irradiancia del archivo XLSM (De Soto 2006 + Rsh exp CdTe Mermoud 2005).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from calculos.modelo_iv import resolver_curva_iv, validar_sdm_vs_ficha
from calculos.dimensionamiento import optimizar_n_serie, semaforo
from datos.tecnologias_bipv import ASP_ST1_T40
from datos.catalogo_inversores import INVERSORES

GROWATT = INVERSORES["Growatt-MID15KTL3-X"]

# ── Datos de referencia VBA (hoja FF_vs_Irradiancia, T=25°C) ─────────────────
VALIDACION_FF_VBA = [
    (100,  69.75),
    (200,  76.28),  # ← MÁXIMO FF para CdTe (Batzner et al. 2001)
    (300,  75.44),
    (400,  74.51),
    (500,  73.54),
    (600,  72.87),
    (700,  72.19),
    (800,  71.55),
    (900,  70.88),
    (1000, 64.92),  # ← STC
]


@pytest.mark.parametrize("G, FF_vba", VALIDACION_FF_VBA)
def test_ff_vs_irradiancia(G, FF_vba):
    """FF Python debe estar dentro del 0.5% del VBA."""
    res = resolver_curva_iv(G, 25.0, ASP_ST1_T40, n_puntos=0)
    FF_python = res["FF"] * 100
    error = abs(FF_python - FF_vba)
    assert error < 0.5, (
        f"G={G} W/m²: Python={FF_python:.2f}% vs VBA={FF_vba:.2f}% "
        f"— diferencia={error:.3f}% > 0.5%"
    )


def test_maximo_ff_en_bajo_G():
    """FF máximo debe ocurrir entre 150-400 W/m² (característica CdTe)."""
    Gs  = [100, 150, 200, 250, 300, 400, 500, 600]
    FFs = [resolver_curva_iv(G, 25.0, ASP_ST1_T40, n_puntos=0)["FF"] for G in Gs]
    G_max = Gs[FFs.index(max(FFs))]
    assert 150 <= G_max <= 400, f"FF máximo en G={G_max} W/m² — esperado 150-400 W/m²"


def test_validacion_stc_vs_ficha():
    """Parámetros STC calculados deben estar dentro de tolerancia."""
    resultado = validar_sdm_vs_ficha(ASP_ST1_T40, tolerancia_pct=5.0)
    for param, datos in resultado.items():
        if param == "validacion_ok":
            continue
        assert datos["ok"], (
            f"{param}: error={datos['error_pct']:.2f}% > tolerancia"
        )


# ── Validación dimensionamiento string (hoja Optimizacion_String del XLSM) ────
@pytest.mark.parametrize("N, esperado_ok", [
    (6,  False),   # FALLA por Vmp < 580V
    (7,  False),   # ALERTA por margen < 7.5%
    (8,  True),    # OK — seleccionado en proyecto
    (9,  False),   # FALLA por Voc > 1100V
    (10, False),   # FALLA por Voc > 1100V
])
def test_optimizar_n_serie(N, esperado_ok):
    """Reproducir tabla de verificación del XLSM (hoja Optimizacion_String)."""
    resultados = optimizar_n_serie(ASP_ST1_T40, GROWATT,
                                   T_frio=-5, T_real=36.35, T_extremo=41.94,
                                   N_strings_tracker=8, N_min=N, N_max=N)
    r = resultados[0]
    tiene_0_riesgos = (r.riesgos == 0)
    assert tiene_0_riesgos == esperado_ok, (
        f"N={N}: riesgos={r.riesgos}, esperado_ok={esperado_ok} "
        f"v1={r.v1_voc_max} v2={r.v2_vmp_real} v3={r.v3_vmp_extr} v4={r.v4_i_max}"
    )


def test_voc_n8_vs_xlsm():
    """Voc frío con N=8 debe ser 1017.4V ± 2V (hoja Resultado_Dim_String del XLSM)."""
    from calculos.dimensionamiento import calcular_voc_string
    Voc = calcular_voc_string(8, ASP_ST1_T40["Voc_stc"], ASP_ST1_T40["Tk_beta"], -5.0)
    assert abs(Voc - 1017.4) < 2.0, f"Voc={Voc:.1f}V vs VBA=1017.4V"


def test_vmp_n8_vs_xlsm():
    """Vmp realista con N=8 debe ser 666.0V ± 2V (hoja Resultado_Dim_String del XLSM)."""
    from calculos.dimensionamiento import calcular_vmp_string
    Vmp = calcular_vmp_string(8, ASP_ST1_T40["Vmp_stc"], ASP_ST1_T40["Tk_gamma"], 36.35)
    assert abs(Vmp - 666.0) < 2.0, f"Vmp={Vmp:.1f}V vs VBA=666.0V"
