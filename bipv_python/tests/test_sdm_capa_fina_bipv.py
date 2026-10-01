# -*- coding: utf-8 -*-
"""Spec 04-produccion-energia/sdm-capa-fina-bipv (1-oct-2026).

Ficha real: MiaSolé FLEX-03 90N 1,7 m (CIGS flexible). Trae STC, NOCT 48 °C y
coeficientes (Pmax −0,38, Voc −0,28, Isc +0,008 %/°C), pero no el número de
celdas ni el rendimiento a 200 W/m². Antes se estimaba como silicio y, sin
N_s, no se estimaba.
"""
from pathlib import Path

import pytest

from calculos.modelo_iv import (
    calcular_pmax_vectorizado,
    estimar_sdm_desde_ficha,
    normalizar_tecnologia,
    validar_sdm_vs_ficha,
)
from datos.tecnologias_bipv import MODULOS_BIPV

_RAIZ = Path(__file__).resolve().parents[1]
MIASOLE_90N = {
    "nombre": "MiaSolé FLEX-03 90N", "tecnologia": "CIS",
    "Voc_stc": 26.3, "Isc_stc": 4.41, "Vmp_stc": 21.8, "Imp_stc": 4.14, "Pmax_stc": 90.0,
    "Tk_beta": -0.28, "Tk_gamma": -0.38, "Tk_alfa": 0.008, "NOCT": 48.0,
}


def _rel_200(panel_sdm):
    import numpy as np
    p200, p1000 = calcular_pmax_vectorizado(np.array([200.0, 1000.0]), np.array([25.0, 25.0]), panel_sdm)
    return 100.0 * (p200 / 200.0) / (p1000 / 1000.0)


@pytest.mark.parametrize("texto, esperado, supuesta", [
    ("CIS", "CIGS", False), ("CIGS", "CIGS", False), ("Copper Indium Gallium Diselenide", "CIGS", False),
    ("CdTe", "CdTe", False), ("Mono-Si", "Mono-Si", False), ("HJT", "Mono-Si", False),
    ("TOPCon", "Mono-Si", False), ("Poly-Si", "Poli-Si", False),
    ("a-Si", "Mono-Si", True), ("Thin Film", "Mono-Si", True), ("Otro", "Mono-Si", True), ("", "Mono-Si", True),
])
def test_normalizar_tecnologia(texto, esperado, supuesta):
    assert normalizar_tecnologia(texto) == (esperado, supuesta)


def test_miasole_se_estima_como_cigs_sin_numero_de_celdas():
    est = estimar_sdm_desde_ficha(MIASOLE_90N)
    assert est is not None
    assert est["tecnologia"] == "CIGS" and est["_tecnologia_supuesta"] is False
    assert est["_ns_estimado"] is True and 36 <= est["N_s"] <= 44          # 26,3 V ÷ ~0,66 V/celda
    val = validar_sdm_vs_ficha({**MIASOLE_90N, **est})
    assert val["validacion_ok"]


def test_sin_el_dato_capa_fina_usa_el_menos_3_por_ciento_por_defecto():
    # Con el factor de idealidad típico de CIGS (1,35) daba ~91,6 % a 200 W/m²;
    # sin dato la referencia estándar internacional usa −3 % (97 %).
    est = estimar_sdm_desde_ficha(MIASOLE_90N)
    assert est["_ajuste_200"] == "defecto" and est["_metodo"] == "pvsyst_v6_calibrado_200"
    assert _rel_200({**MIASOLE_90N, **est}) == pytest.approx(97.0, abs=0.3)


def test_ajuste_con_el_dato_de_200_w_m2():
    for objetivo in (94.0, 97.0, 99.0):
        est = estimar_sdm_desde_ficha({**MIASOLE_90N, "eficiencia_rel_200": objetivo})
        sdm = {**MIASOLE_90N, **est}
        assert est["_ajuste_200"] == "ficha" and est["_metodo"] == "pvsyst_v6_calibrado_200"
        assert _rel_200(sdm) == pytest.approx(objetivo, abs=0.3)
        assert est["_rel_200_modelo"] == pytest.approx(objetivo, abs=0.3)
        assert validar_sdm_vs_ficha(sdm)["validacion_ok"]                 # STC sigue anclado


def test_silicio_queda_igual():
    jam = {"nombre": "JAM", "tecnologia": "Mono-Si", "Voc_stc": 49.0, "Isc_stc": 18.59, "Vmp_stc": 41.19,
           "Imp_stc": 17.48, "N_s": 66, "Tk_beta": -0.25, "Tk_gamma": -0.29}
    est = estimar_sdm_desde_ficha(jam)
    assert est["tecnologia"] == "Mono-Si" and est["_tecnologia_supuesta"] is False
    assert est["_ns_estimado"] is False and est["N_s"] == 66
    assert est["gamma_ref"] == pytest.approx(1.0, abs=0.01)                 # igual que antes de esta Spec
    assert est["_ajuste_200"] is None and est["_metodo"] == "pvsyst_v6_defaults"   # silicio sin cambios


def test_tecnologia_desconocida_queda_marcada():
    est = estimar_sdm_desde_ficha({**MIASOLE_90N, "tecnologia": "Thin Film", "N_s": 40})
    assert est["tecnologia"] == "Mono-Si" and est["_tecnologia_supuesta"] is True


def test_asp_calibrado_no_cambia():
    assert MODULOS_BIPV["ASP-ST1-T40"]["tecnologia"] == "CdTe"
    assert normalizar_tecnologia("CdTe") == ("CdTe", False)


def test_catalogo_y_motor_iv():
    from datos.catalogo_paneles_excel import cargar_catalogo_paneles  # noqa: F401
    src_cat = (_RAIZ / "datos" / "catalogo_paneles_excel.py").read_text(encoding="utf-8")
    assert '"eficiencia_rel_200"' in src_cat and "EficRel200Pct" in src_cat
    pag = (_RAIZ / "pages" / "14_📋_Catálogo_Paneles.py").read_text(encoding="utf-8")
    assert '"η rel. 200 W/m² (%)":' in pag and '"EficRel200Pct":' in pag
    iv = (_RAIZ / "pages" / "3_🔬_Motor_IV.py").read_text(encoding="utf-8")
    assert "_tecnologia_supuesta" in iv and "_ns_estimado" in iv and "_ajuste_200" in iv


def test_manual_del_asistente():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 112.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("CIGS", "200 W/m²", "MiaSolé", "η rel. 200 W/m² (%)", "Vista 3D", "a-Si"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
