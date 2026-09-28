"""Rótulo de módulos y mensaje final de 💰 Financiero; ficha RETIE al ancho.

Proyecto cliente (28-sep-2026, 112 ASP-ST1-T40 + 4 SPR-E20-327):
- El mensaje final decía «116 módulos ASP-ST1-T40» (el panel de 📐
  Dimensionamiento) y terminaba en «TIR: 16.8% |»: el `if/else` de la
  f-string se tragaba VPN, Payback y LCOE cuando había TIR.
- La ficha RETIE (SVG de 1800 px) se veía con barra horizontal.
"""
from pathlib import Path

from calculos.lectura_financiera import mensaje_resumen_financiero, rotulo_modulos

ROOT = Path(__file__).resolve().parents[1]
FIN = ROOT / "pages" / "7_💰_Financiero.py"
RETIE = ROOT / "pages" / "21_📋_Ficha_Validacion_RETIE.py"
SPR = "SPR-E20-327 (E20-327NE-WHT-D)"
SISTEMA = {"n_modulos": 116, "por_panel": [{"panel": "ASP-ST1-T40", "modulos": 112},
                                           {"panel": SPR, "modulos": 4}]}
M_CON = {"tir_pct": 16.8, "vpn_usd": 10756.0, "payback_simple": 6.7, "lcoe_cop_kWh": 1620.0}


def test_rotulo_con_varios_paneles_del_sistema_multisuperficie():
    assert rotulo_modulos(SISTEMA, 116, "ASP-ST1-T40") == f"112 ASP-ST1-T40 + 4 {SPR}"


def test_rotulo_con_un_panel_o_sin_sistema():
    uno = {"por_panel": [{"panel": "ASP-ST1-T40", "modulos": 116}]}
    assert rotulo_modulos(uno, 116, "otro") == "116 módulos ASP-ST1-T40"
    assert rotulo_modulos(None, 20, "P-400") == "20 módulos P-400"
    assert rotulo_modulos(None, 20, "") == "20 módulos —"
    assert rotulo_modulos({"por_panel": []}, 20, "P-400") == "20 módulos P-400"


def test_mensaje_final_trae_vpn_payback_y_lcoe_con_tir():
    texto = mensaje_resumen_financiero("Bogotá", rotulo_modulos(SISTEMA, 116, ""), 14745.0,
                                       3307.0, M_CON, 1732.0, vpn_positivo=True)
    assert f"112 ASP-ST1-T40 + 4 {SPR}" in texto
    for parte in ("TIR: **16.8%**", "VPN: **USD 10,756**", "Payback: **6.7 años**",
                  "LCOE: **1620 COP/kWh**", "< valor nivelado", "1732"):
        assert parte in texto, parte
    assert texto.startswith("✅ **Bogotá**")


def test_mensaje_final_sin_tir_ni_payback():
    m = dict(M_CON, tir_pct=None, payback_simple=None)
    texto = mensaje_resumen_financiero("Cali", "20 módulos P", 1000.0, 4000.0, m, None, vpn_positivo=False)
    assert texto.startswith("⚠️") and "TIR: **N/A**" in texto
    assert "Payback: **> horizonte**" in texto and "VPN: **USD" in texto and "LCOE:" in texto
    assert "valor nivelado" not in texto


def test_paginas_usan_rotulo_mensaje_y_ficha_al_ancho():
    fin = FIN.read_text(encoding="utf-8")
    assert "mensaje_resumen_financiero(" in fin and "rotulo_modulos(" in fin
    assert 'f"{color_vpn} **{ciudad}** — {n_pan} módulos "' not in fin
    retie = RETIE.read_text(encoding="utf-8")
    assert "st.image(svg, use_column_width=True)" in retie
    assert "st.components.v1.html(svg" not in retie
