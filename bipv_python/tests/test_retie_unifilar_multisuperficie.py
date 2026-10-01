"""Ficha RETIE y Diagrama Unifilar con el sistema multi-superficie real.

Spec 07-informes/unifilar-retie-multisuperficie (caso del cliente en
tests/test_topologia_electrica.py).
"""
import math
from pathlib import Path

import pytest
import schemdraw

from calculos.diagrama_unifilar import construir_config_unifilar, generar_diagrama_unifilar
from calculos.ficha_validacion_retie import (
    calcular_retie_multisuperficie,
    generar_ficha_svg,
    validar_retie_multisuperficie,
)
from tests.test_topologia_electrica import SPR, FICHA_SG5, _cliente, _g, _inv, _topo

ROOT = Path(__file__).resolve().parents[1]
PAG_UNIF = ROOT / "pages" / "20_⚡_Diagrama_Unifilar.py"
PAG_RETIE = ROOT / "pages" / "21_📋_Ficha_Validacion_RETIE.py"


def _etiquetas(d: schemdraw.Drawing) -> str:
    return "\n".join(l.label for e in d.elements for l in getattr(e, "_userlabels", []))


def _ficha(topo, diag, **kw):
    calc = calcular_retie_multisuperficie(topo, tension_salida_v=kw.pop("tension", 220.0))
    checks = validar_retie_multisuperficie(topo, diag, calc, **kw)
    return calc, checks


def _por_titulo(checks, parte):
    return [c for c in checks if parte in c["titulo"]]


# ── Ficha RETIE ──────────────────────────────────────────────────────────────
def test_criterio_1_ficha_valida_cada_grupo_con_los_datos_del_diseno_electrico():
    topo, diag = _topo()
    _, checks = _ficha(topo, diag)
    voc = _por_titulo(checks, "Voc en frío")
    # Spec 03/tension-maxima-modulo: en la fachada (ASP-ST1-T40, 1.000 V)
    # manda el módulo; el techo (sin el dato) sigue con el inversor.
    assert [c["titulo"] for c in voc] == ["Voc en frío ≤ tensión máx. del módulo — Fachada principal · G1",
                                          "Voc en frío ≤ Vdc máximo — Techo 1 · G2"]
    assert all(c["nivel"] == "OK" for c in voc)
    assert "987,6" in voc[0]["detalle"] and "1000" in voc[0]["detalle"]      # igual a ⚡ Diseño eléctrico
    # DC/AC 1,67 (amarillo en Diseño eléctrico) → por revisar, nunca OK
    dcac = _por_titulo(checks, "Relación DC/AC — INV-1")
    assert len(dcac) == 1 and dcac[0]["nivel"] == "PENDIENTE"
    assert not _por_titulo(checks, "Cantidad de módulos")                    # el chequeo de una superficie no aplica


def test_mapeo_de_colores_del_diagnostico():
    sups, invs, paneles = _cliente()
    sups[0]["grupos"] = [_g("G1", "INV-1", 1, 10, 14)]                        # Voc frío > 1100 V
    topo, diag = _topo(sups, invs, paneles)
    _, checks = _ficha(topo, diag)
    voc = _por_titulo(checks, "Voc en frío ≤ tensión máx. del módulo — Fachada principal")[0]
    assert voc["nivel"] == "ERROR"
    assert {c["nivel"] for c in checks} <= {"OK", "PENDIENTE", "ERROR"}


def test_criterio_2_caja_combinadora_pide_fusibles_gpv_con_su_corriente_minima():
    topo, diag = _topo()
    _, checks = _ficha(topo, diag)
    caja = _por_titulo(checks, "Caja combinadora")
    assert len(caja) == 1 and caja[0]["nivel"] == "PENDIENTE"
    assert "INV-1 · MPPT 1" in caja[0]["titulo"]
    assert "14 strings" in caja[0]["detalle"]
    assert "1,25 A" in caja[0]["detalle"]                                     # 1,25 × 1,25 × 0,80 A


def test_criterio_3_corriente_y_breaker_por_inversor_y_general():
    sups, invs, paneles = _cliente()
    sups[1]["grupos"] = [_g("G2", "INV-2", 1, 4, 1)]
    ficha2 = dict(FICHA_SG5, P_ac_nom_W=3000.0)
    topo, diag = _topo(sups, [_inv(), _inv("INV-2", "SG3.0RT", ficha2)], paneles)
    calc, _ = _ficha(topo, diag, tension=220.0)
    i1 = 5000 / (math.sqrt(3) * 220)
    i2 = 3000 / (math.sqrt(3) * 220)
    assert [p["inversor_id"] for p in calc["por_inversor"]] == ["INV-1", "INV-2"]
    assert calc["por_inversor"][0]["corriente_a"] == pytest.approx(round(i1, 1))
    assert calc["por_inversor"][0]["breaker_a"] == 20                        # 1,25 × 13,1 = 16,4 → 20 A
    assert calc["por_inversor"][1]["breaker_a"] == 16                        # 1,25 × 7,9 = 9,8 → 16 A
    assert calc["corriente_total_a"] == pytest.approx(round(i1 + i2, 1))
    assert calc["breaker_general_a"] == 32                                   # 1,25 × 21,0 = 26,2 → 32 A
    assert calc["potencia_ac_kw"] == pytest.approx(8.0)
    assert calc["relacion_dc_ac"] == pytest.approx(round(topo["p_dc_kWp"] / 8.0, 3))


def test_inversor_sin_potencia_ac_no_inventa_corriente():
    sups, invs, paneles = _cliente()
    ficha = {k: v for k, v in FICHA_SG5.items() if k != "P_ac_nom_W"}
    inv = _inv(ficha=dict(FICHA_SG5))
    inv["P_ac_nom_W"] = None
    inv["ficha"] = ficha
    topo, diag = _topo(sups, [inv], paneles)
    calc, _ = _ficha(topo, diag)
    assert calc["por_inversor"][0]["corriente_a"] is None
    assert calc["por_inversor"][0]["breaker_a"] is None and calc["breaker_general_a"] is None


def test_criterio_4_bateria_con_compatibilidad_del_inversor_elegido():
    bat = {"nombre": "ARK 5kWh", "cantidad": 2, "capacidad_kWh_unidad": 5.1, "inversor_id": "INV-1"}
    topo, diag = _topo(bateria=bat)
    _, checks = _ficha(topo, diag, bateria_dict={"capacidad_kWh": 5.1, "voltaje_V": 51.2})
    b = _por_titulo(checks, "Batería")
    assert len(b) == 1 and "INV-1" in b[0]["titulo"]
    # compatibilidad_bateria no reconoce el SG5.0RT: hay que confirmarlo en su ficha
    assert b[0]["nivel"] == "PENDIENTE" and "**" not in b[0]["detalle"]
    sups, _, paneles = _cliente()
    topo, diag = _topo(sups, [_inv(nombre="Growatt MID 5KTL3-X")], paneles, bateria=bat)
    b = _por_titulo(_ficha(topo, diag, bateria_dict={"voltaje_V": 51.2})[1], "Batería")
    assert b[0]["nivel"] == "ERROR"            # inversor de string: sin puerto de batería
    topo, diag = _topo()
    assert not _por_titulo(_ficha(topo, diag)[1], "Batería")


def test_criterio_5_optimizadores_por_revisar_solo_si_se_declaran():
    topo, diag = _topo()
    assert not _por_titulo(_ficha(topo, diag)[1], "Optimizadores")
    topo, diag = _topo(optimizadores=True)
    opt = _por_titulo(_ficha(topo, diag)[1], "Optimizadores")
    assert len(opt) == 1 and opt[0]["nivel"] == "PENDIENTE"
    assert "fabricante" in opt[0]["detalle"]


def test_grupos_sin_asignar_y_temperaturas_por_defecto_se_reportan():
    sups, invs, paneles = _cliente()
    sups[1]["grupos"] = [_g("G2", "INV-9", 2, 4, 1)]
    topo, diag = _topo(sups, invs, paneles)
    diag["temperaturas"]["origen"] = "por_defecto"
    _, checks = _ficha(topo, diag, corriente_cortocircuito_pcc_ka=None, esquema_tierra="")
    assert _por_titulo(checks, "Grupos sin inversor")[0]["nivel"] == "ERROR"
    assert _por_titulo(checks, "Temperaturas de diseño")[0]["nivel"] == "PENDIENTE"
    assert _por_titulo(checks, "Capacidad interruptiva")[0]["nivel"] == "PENDIENTE"
    assert _por_titulo(checks, "Sistema de puesta a tierra")[0]["nivel"] == "PENDIENTE"


def test_svg_multisuperficie_muestra_superficies_inversores_y_caja():
    topo, diag = _topo(optimizadores=True)
    calc, checks = _ficha(topo, diag)
    from calculos.ficha_validacion_retie import construir_config_retie
    svg = generar_ficha_svg(construir_config_retie(nombre_proyecto="Cliente"), calc, checks, topologia=topo)
    for texto in ("Fachada principal", "Techo 1", "INV-1", "SG5.0RT", "Caja combinadora",
                  "Optimizadores", "8,36 kWp"):
        assert texto in svg, texto
    assert "Strings: PENDIENTE" not in svg


# ── Diagrama unifilar ────────────────────────────────────────────────────────
def test_criterio_6_sin_topologia_el_unifilar_no_cambia():
    cfg = construir_config_unifilar(panel={"Pmax_stc": 400.0}, n_paneles=20, n_serie=10,
                                    inversor={"P_ac_nom_W": 8000}, tension_red_V=220)
    assert cfg["topologia"] is None
    texto = _etiquetas(generar_diagrama_unifilar(cfg))
    assert "Caja combinadora" not in texto and "INV-1" not in texto


def test_unifilar_dibuja_la_topologia_del_cliente():
    topo, _ = _topo()
    cfg = construir_config_unifilar(nombre_proyecto="Cliente", topologia=topo, tension_red_V=220)
    texto = _etiquetas(generar_diagrama_unifilar(cfg))
    for parte in ("Fachada principal · G1", "8 × 14", "Techo 1 · G2", "Caja combinadora",
                  "14 strings", "INV-1", "SG5.0RT", "MPPT 1", "MPPT 2", "Medidor", "PCC"):
        assert parte in texto, parte
    assert "Optimizador" not in texto and "Batería" not in texto


def test_unifilar_con_varios_inversores_bateria_y_optimizadores():
    sups, invs, paneles = _cliente()
    sups[1]["grupos"] = [_g("G2", "INV-2", 1, 4, 1)]
    bat = {"nombre": "ARK 5kWh", "cantidad": 2, "capacidad_kWh_unidad": 5.1, "inversor_id": "INV-2"}
    topo, _ = _topo(sups, [_inv(), _inv("INV-2", "SPH 5000TL3 BH-UP")], paneles,
                    bateria=bat, optimizadores=True)
    cfg = construir_config_unifilar(topologia=topo, tension_red_V=220)
    d = generar_diagrama_unifilar(cfg)
    texto = _etiquetas(d)
    for parte in ("INV-1", "INV-2", "Optimizador", "ARK 5kWh", "10,2 kWh", "Protección general"):
        assert parte in texto, parte
    assert d.get_imagedata("png")[:4] == b"\x89PNG"                        # se renderiza de verdad


# ── Páginas ──────────────────────────────────────────────────────────────────
def test_paginas_usan_la_topologia_y_no_piden_modulos_a_mano():
    unif = PAG_UNIF.read_text(encoding="utf-8")
    retie = PAG_RETIE.read_text(encoding="utf-8")
    assert "topologia_desde_estado(" in retie
    assert "no viene de ahí" not in unif
    assert "opciones_sistema_multisuperficie(" in unif and "opciones_sistema_multisuperficie(" in retie
    assert "validar_retie_multisuperficie(" in retie
    assert "No es un documento constructivo" in retie and "No es un documento certificado" in unif


# ── Páginas ejecutadas de verdad (AppTest) ───────────────────────────────────
# La página del unifilar se caía siempre al dibujar: st.image(...,
# use_container_width=False) no existe en Streamlit 1.36 (requirements.txt).
# Las pruebas de texto del código fuente no lo detectaban.
@pytest.fixture
def app_con_login(monkeypatch):
    import calculos.auth as auth
    monkeypatch.setattr(auth, "requerir_login",
                        lambda solo_admin=False: {"email": "t@t", "rol": "admin", "activo": True, "nombre": "T"})
    from streamlit.testing.v1 import AppTest

    def correr(pagina, estado):
        at = AppTest.from_file(str(pagina), default_timeout=120)
        for k, v in estado.items():
            at.session_state[k] = v
        at.run()
        return at
    return correr


@pytest.mark.parametrize("pagina", [PAG_UNIF, PAG_RETIE])
def test_paginas_corren_sin_errores_en_los_dos_modos(app_con_login, pagina):
    from tests.test_topologia_electrica import _estado_cliente
    at = app_con_login(pagina, _estado_cliente())
    assert not at.exception, [e.value for e in at.exception]
    assert at.radio[0].value.startswith("🗺️")
    assert any("116 módulos" in c.value for c in at.caption)
    at.radio[0].set_value(at.radio[0].options[1]).run()                    # modo de una superficie
    assert not at.exception, [e.value for e in at.exception]
    at = app_con_login(pagina, {})                                            # sin proyecto
    assert not at.exception, [e.value for e in at.exception]
    assert not at.radio


def test_ficha_retie_en_la_pagina_valida_el_sistema_del_cliente(app_con_login):
    from tests.test_topologia_electrica import _estado_cliente
    at = app_con_login(PAG_RETIE, _estado_cliente())
    textos = " ".join(m.value for m in at.markdown)
    assert "Voc en frío ≤ tensión máx. del módulo — Fachada principal · G1" in textos
    assert "Caja combinadora — INV-1 · MPPT 1" in textos


# ── Geometría: las cajas quedan donde se dibujan las líneas ──────────────────
# Con schemdraw 0.23, elm.Rect(w=, h=) ignoraba el tamaño y dibujaba un
# cuadrado 1×1 corrido de la línea (también en el diagrama de una superficie);
# ninguna prueba lo detectaba porque solo revisaban que no fallara.
def _cajas(d):
    import schemdraw.elements as elm
    d.draw(show=False)
    salida = {}
    for e in d.elements:
        if isinstance(e, elm.Rect):
            b = e.get_bbox(transform=True, includetext=False)
            nombre = e._userlabels[0].label.split("\n")[0] if e._userlabels else "?"
            salida[nombre] = (round(b.xmin, 3), round(b.xmax, 3), round(b.ymin, 3), round(b.ymax, 3))
    return salida


def test_cajas_del_diagrama_de_una_superficie_centradas_y_con_su_tamano():
    cfg = construir_config_unifilar(panel={"Pmax_stc": 400.0}, n_paneles=20, n_serie=10,
                                    inversor={"P_ac_nom_W": 8000}, tension_red_V=220)
    cajas = _cajas(generar_diagrama_unifilar(cfg))
    assert len(cajas) == 3
    for xmin, xmax, ymin, ymax in cajas.values():
        assert (xmin, xmax) == (-1.4, 1.4)                 # 2,8 de ancho, centrada en la línea x = 0
    alturas = sorted(round(c[3] - c[2], 2) for c in cajas.values())
    assert alturas == [1.1, 1.3, 1.4]


def test_cajas_de_la_topologia_alineadas_con_sus_ramas():
    topo, _ = _topo()
    cajas = _cajas(generar_diagrama_unifilar(construir_config_unifilar(topologia=topo, tension_red_V=220)))
    fachada, techo = cajas["Fachada principal · G1"], cajas["Techo 1 · G2"]
    caja, inv = cajas["Caja combinadora"], cajas["INV-1 · SG5.0RT"]
    centro = lambda c: (c[0] + c[1]) / 2
    assert centro(caja) == pytest.approx(centro(fachada))          # la caja está bajo la fachada
    assert fachada[1] < techo[0]                                    # ramas sin solaparse
    assert inv[0] <= centro(fachada) and centro(techo) <= inv[1]    # las dos entradas llegan al inversor
    assert caja[3] < fachada[2] and inv[3] < caja[2]                # orden vertical: strings → caja → inversor
    medidor = cajas["Medidor Bidireccional"]
    assert medidor[3] < inv[2]


def test_tarjetas_de_la_ficha_no_quedan_debajo_del_pie():
    # Antes el alto no contaba las filas de la tabla: la última fila de
    # tarjetas quedaba tapada por el pie de página.
    import re
    topo, diag = _topo(optimizadores=True, bateria={"nombre": "ARK", "cantidad": 2,
                                                    "capacidad_kWh_unidad": 5.1, "inversor_id": "INV-1"})
    calc, checks = _ficha(topo, diag)
    from calculos.ficha_validacion_retie import construir_config_retie
    svg = generar_ficha_svg(construir_config_retie(nombre_proyecto="Cliente"), calc, checks, topologia=topo)
    alto = float(re.search(r'<svg[^>]* height="([\d.]+)"', svg).group(1))
    tarjetas = [float(y) + 92 for y in re.findall(r'<rect x="[\d.]+" y="([\d.]+)" width="410" height="92"', svg)]
    assert len(tarjetas) == len(checks)
    assert max(tarjetas) < alto - 135                       # borde superior del pie de página
