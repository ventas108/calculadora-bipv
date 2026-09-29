# -*- coding: utf-8 -*-
"""Cantidad de inversores elegida por el diseñador (29-sep-2026).

Apartadó: 308 × JAM66D46-720/LB (221,76 kWp, 11 strings de 28) con Growatt
MAX 100KTL3 LV (100 kW AC, 10 MPPT). La referencia estándar internacional
usa 2 inversores (200 kW AC, DC/AC 1,11); la app solo podía derivar 1 por
capacidad de strings (DC/AC 2,22) y recortaba ≈ 49.000 kWh/año. Además
📐 Dimensionamiento redondeaba hacia arriba y 📊 Producción al más cercano.
"""
import pytest

from calculos.dimensionamiento import (
    escalar_p_ac_nom_por_inversores,
    inversores_fijados_vigentes,
    inversores_para_dcac,
    proyecto_completo,
    resolver_inversores,
)

PANEL = {"area_m2": 3.107, "Pmax_stc": 720.0}
P_AC = 100_000.0


def _pc(**kw):
    base = dict(panel=PANEL, area_util_m2=957.0, N_serie=28, N_strings_tracker=2,
                N_mppt=10, N_total_cadenas=11, P_ac_nom_W=P_AC)
    base.update(kw)
    return proyecto_completo(**base)


# ── resolver_inversores ─────────────────────────────────────────────────────
def test_sin_fijar_usa_el_minimo_por_capacidad():
    r = resolver_inversores(strings=11, capacidad=20)
    assert (r["n"], r["minimo"], r["maximo"], r["fuente"]) == (1, 1, 11, "calculado")


def test_fijado_se_respeta():
    r = resolver_inversores(strings=11, capacidad=20, fijado=2)
    assert (r["n"], r["fuente"], r["ajustado"]) == (2, "fijado", False)


def test_fijado_menor_que_el_minimo_sube_al_minimo():
    r = resolver_inversores(strings=11, capacidad=10, fijado=1)
    assert (r["n"], r["ajustado"]) == (2, True)


def test_fijado_mayor_que_los_strings_baja_a_un_string_por_inversor():
    r = resolver_inversores(strings=11, capacidad=20, fijado=15)
    assert (r["n"], r["ajustado"]) == (11, True)


def test_sin_strings_no_hay_inversores():
    assert resolver_inversores(strings=0, capacidad=20, fijado=2)["n"] == 0


# ── inversores_para_dcac ────────────────────────────────────────────────────
def test_apartado_necesita_2_inversores_para_dcac_1_3():
    assert inversores_para_dcac(221.76, P_AC, minimo=1, maximo=11) == 2


def test_dcac_sin_potencia_ac_no_sugiere():
    assert inversores_para_dcac(221.76, None, minimo=1, maximo=11) is None


def test_dcac_respeta_minimo_y_maximo():
    assert inversores_para_dcac(10.0, P_AC, minimo=3, maximo=11) == 3
    assert inversores_para_dcac(5000.0, P_AC, minimo=1, maximo=11) == 11


# ── proyecto_completo ───────────────────────────────────────────────────────
def test_proyecto_completo_apartado_sin_fijar_sugiere_2():
    pc = _pc()
    assert pc["N_inversores"] == 1
    assert pc["fuente_inversores"] == "calculado"
    assert pc["N_inversores_dcac"] == 2
    assert pc["dcac"]["ratio"] == pytest.approx(2.22, abs=0.01)


def test_proyecto_completo_apartado_con_2_fijados():
    pc = _pc(N_inversores_fijado=2)
    assert pc["N_inversores"] == 2
    assert pc["reparto"] == [6, 5]
    assert pc["fuente_inversores"] == "fijado"
    assert pc["dcac"]["ratio"] == pytest.approx(1.11, abs=0.01)
    assert pc["N_paneles"] == 308


def test_proyecto_completo_sin_fijar_igual_que_antes():
    pc = _pc(N_strings_tracker=1)
    assert pc["N_inversores"] == 2 and pc["reparto"] == [6, 5]


# ── escalar_p_ac_nom_por_inversores (📊 Producción) ─────────────────────────
def test_produccion_redondea_hacia_arriba_como_dimensionamiento():
    # 308 paneles, 280 por inversor lleno (28 × 1 × 10): hacen falta 2, no 1.
    r = escalar_p_ac_nom_por_inversores(308, 28, 1, 10, P_AC)
    assert r["n_inversores"] == 2
    assert r["p_ac_nom_w_total"] == pytest.approx(200_000)


def test_produccion_usa_los_inversores_fijados():
    r = escalar_p_ac_nom_por_inversores(308, 28, 2, 10, P_AC, n_inversores_fijado=2)
    assert r["n_inversores"] == 2
    assert r["fuente"] == "fijado"
    assert r["p_ac_nom_w_total"] == pytest.approx(200_000)


def test_produccion_sin_fijar_apartado_con_2_por_mppt_sigue_en_1():
    r = escalar_p_ac_nom_por_inversores(308, 28, 2, 10, P_AC)
    assert r["n_inversores"] == 1
    assert r["fuente"] == "calculado"


def test_produccion_fijado_imposible_se_ajusta():
    r = escalar_p_ac_nom_por_inversores(308, 28, 1, 10, P_AC, n_inversores_fijado=1)
    assert r["n_inversores"] == 2 and r["ajustado"] is True


# ── inversores_fijados_vigentes ─────────────────────────────────────────────
def test_fijado_vale_solo_para_el_mismo_inversor():
    estado = {"N_inversores_proyecto": 2, "N_inversores_proyecto_ref": "MAX 100KTL3 LV"}
    assert inversores_fijados_vigentes(estado, "MAX 100KTL3 LV") == 2
    assert inversores_fijados_vigentes(estado, "Otro") == 0
    assert inversores_fijados_vigentes({}, "MAX 100KTL3 LV") == 0


# ── páginas ──────────────────────────────────────────────────────────────────
def _fuente(nombre):
    from pathlib import Path
    return next((Path(__file__).resolve().parents[1] / "pages").glob(nombre)).read_text(encoding="utf-8")


def test_dimensionamiento_tiene_el_campo_y_lo_pasa():
    src = _fuente("4_*Dimensionamiento.py")
    assert "N_inversores_proyecto" in src
    assert src.count("N_inversores_fijado=") >= 2


def test_produccion_pasa_los_inversores_fijados():
    src = _fuente("6_*Produccion.py")
    assert "inversores_fijados_vigentes" in src
    assert "n_inversores_fijado=" in src


def test_presupuesto_cotiza_todos_los_inversores():
    src = _fuente("8_*Presupuesto.py")
    assert '"INV-CAT", 1.0,' not in src
    assert "N_inv_total" in src


def test_manual_del_asistente_explica_las_alarmas():
    from pathlib import Path
    kb = (Path(__file__).resolve().parents[1] / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    seccion = kb[kb.index("## 90."):]
    for texto in ("guía rápida de alarmas", "0,75", "1,35", "1,60", "💡", "no es posible",
                  "fijados en 📐 Dimensionamiento", "volvió a 0"):
        assert texto in seccion
    assert "PVsyst" not in seccion


# ── Aviso bajo el campo cuando está en 0 (pedido del usuario, 29-sep-2026) ───
def test_aviso_con_cadenas_declaradas_da_la_cuenta_exacta():
    from calculos.dimensionamiento import texto_inversores_automaticos
    t = texto_inversores_automaticos(11, 10, 1)
    assert "**2 inversor(es)**" in t and "11 strings ÷ 10" in t and "otro número" in t
    assert "**1 inversor(es)**" in texto_inversores_automaticos(11, 10, 2)


def test_aviso_sin_cadenas_usa_lo_publicado_o_explica_cuando():
    from calculos.dimensionamiento import texto_inversores_automaticos
    assert "**3 inversor(es)**" in texto_inversores_automaticos(0, 10, 1, publicado=3)
    assert "Optimizar N paneles/string" in texto_inversores_automaticos(0, 10, 1)


def test_dimensionamiento_muestra_el_aviso_en_0():
    src = _fuente("4_*Dimensionamiento.py")
    assert "texto_inversores_automaticos(" in src
    assert "if N_inv_fijado == 0:" in src
