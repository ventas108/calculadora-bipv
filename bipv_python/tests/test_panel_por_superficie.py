"""Spec 05-perdidas-y-temperatura/panel-por-superficie.

Vista 3D usaba una sola referencia de panel para todas las superficies y la
energía simplificada leía ``eta_panel``, clave que ninguna página escribe:
siempre 16 %. Con el panel del proyecto ``ASP-ST1-T40`` (η 8,75 %) la fachada
de la prueba en producción del 24-sep-2026 daba 12.191 kWh/año en vez de 6.667.
"""
import ast
import copy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from calculos.adaptador_multisuperficie import construir_proyecto_desde_session_state
from calculos.multi_superficie import e_ac_total_multisup, produccion_superficie
from calculos.panel_superficie import (
    CLAVE_FIRMA_PANELES,
    KEYS_RESULTADOS_PANEL,
    ORIGEN_PANEL_CATALOGO,
    PanelSuperficieError,
    area_modulo,
    eficiencia_panel,
    eficiencias_superficies,
    firma_panel_superficie,
    invalidar_por_cambio_panel,
    opcion_panel_actual,
    panel_de_superficie,
    seleccion_panel,
)
from calculos.persistencia_multisuperficie import (
    PayloadMultisuperficieError,
    construir_payload_multisuperficie,
    restaurar_multisuperficie,
    validar_payload_multisuperficie,
)
from calculos.strings_superficie import strings_superficie
from calculos.transicion_multisuperficie import calcular_huellas
from datos.tecnologias_bipv import MODULOS_BIPV

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
_PROYECTO = "ASP-ST1-T40"
_OTRO = "SPR-E20-327 (E20-327NE-WHT-D)"
_IDX = pd.date_range("2025-01-01", periods=8760, freq="h", tz="UTC")


def _poa_anual(kwh_m2: float) -> pd.DataFrame:
    return pd.DataFrame({"poa_global": np.full(8760, kwh_m2 * 1000.0 / 8760)}, index=_IDX)


def _catalogo(nombre: str) -> dict:
    return {"panel_origen": ORIGEN_PANEL_CATALOGO, "panel_nombre": nombre,
            "panel_ficha": dict(MODULOS_BIPV[nombre])}


def _sup(nombre="Fachada principal", uid=1, **cambios):
    base = {"uid": uid, "nombre": nombre, "tipo": "Fachada", "tilt_deg": 90.0,
            "azimuth_deg": 180.0, "area_m2": 97.3, "activa": True}
    base.update(cambios)
    return base


# ── Eficiencia del panel ─────────────────────────────────────────────────────
def test_eficiencia_del_panel_del_proyecto():
    assert eficiencia_panel(MODULOS_BIPV[_PROYECTO]) == pytest.approx(63.0 / 720.0)
    assert eficiencia_panel(MODULOS_BIPV[_PROYECTO]) == pytest.approx(0.0875)


def test_area_del_modulo_por_dimensiones_si_falta_area():
    panel = {k: v for k, v in MODULOS_BIPV[_PROYECTO].items() if k != "area_m2"}
    assert area_modulo(panel) == pytest.approx(0.72)
    assert eficiencia_panel(panel) == pytest.approx(0.0875)


@pytest.mark.parametrize("panel", [
    {"Pmax_stc": 400.0},                               # sin área
    {"area_m2": 2.0},                                  # sin potencia
    {"Pmax_stc": "n/d", "area_m2": 2.0},
    {"Pmax_stc": 3000.0, "area_m2": 2.0},              # η > 100 %
])
def test_panel_sin_datos_no_usa_un_valor_fijo(panel):
    with pytest.raises(PanelSuperficieError):
        eficiencia_panel(panel, "P-X")


# ── Panel de cada superficie ─────────────────────────────────────────────────
def test_por_defecto_la_superficie_sigue_al_panel_del_proyecto():
    datos = panel_de_superficie(_sup(), MODULOS_BIPV[_PROYECTO], _PROYECTO)
    assert datos["origen"] == "proyecto" and datos["es_proyecto"]
    assert datos["nombre"] == _PROYECTO and datos["panel"] == MODULOS_BIPV[_PROYECTO]


def test_superficie_con_panel_del_catalogo():
    datos = panel_de_superficie(_sup(**_catalogo(_OTRO)), MODULOS_BIPV[_PROYECTO], _PROYECTO)
    assert datos["origen"] == "catalogo" and not datos["es_proyecto"]
    assert datos["panel"] == MODULOS_BIPV[_OTRO]
    # El mismo modelo del proyecto elegido desde el catálogo cuenta como del proyecto.
    mismo = panel_de_superficie(_sup(**_catalogo(_PROYECTO)), MODULOS_BIPV[_PROYECTO], _PROYECTO)
    assert mismo["es_proyecto"]


@pytest.mark.parametrize("sup, panel_dict, fragmento", [
    (_sup(), None, "Dimensionamiento"),
    (_sup(panel_origen="excel"), MODULOS_BIPV[_PROYECTO], "desconocido"),
    (_sup(panel_origen="catalogo", panel_nombre=_OTRO), MODULOS_BIPV[_PROYECTO], "ficha"),
])
def test_panel_no_utilizable_explica_el_motivo(sup, panel_dict, fragmento):
    with pytest.raises(PanelSuperficieError, match=fragmento):
        panel_de_superficie(sup, panel_dict, _PROYECTO)


def test_eficiencias_por_superficie_con_errores_separados():
    sups = [_sup(), _sup("Techo 1", 2, **_catalogo(_OTRO)),
            _sup("Sin panel", 3, panel_origen="catalogo"),
            _sup("Apagada", 4, activa=False)]
    etas, paneles, errores = eficiencias_superficies(sups, MODULOS_BIPV[_PROYECTO], _PROYECTO)
    assert etas["Fachada principal"] == pytest.approx(0.0875)
    assert etas["Techo 1"] == pytest.approx(eficiencia_panel(MODULOS_BIPV[_OTRO]))
    assert paneles["Techo 1"]["nombre"] == _OTRO
    assert set(errores) == {"Sin panel"} and "Apagada" not in etas


def test_seleccion_del_editor():
    etq = f"Panel del proyecto ({_PROYECTO})"
    assert seleccion_panel(etq, etq, MODULOS_BIPV, _sup()) == {"panel_origen": "proyecto"}
    elegido = seleccion_panel(_OTRO, etq, MODULOS_BIPV, _sup())
    assert elegido == _catalogo(_OTRO)
    assert opcion_panel_actual(_sup(**elegido), etq) == _OTRO
    assert opcion_panel_actual(_sup(), etq) == etq
    # Si el modelo no cambió se conserva la ficha guardada, aunque el catálogo cambie.
    guardada = _sup(**_catalogo(_OTRO))
    guardada["panel_ficha"]["Pmax_stc"] = 999.0
    catalogo_nuevo = copy.deepcopy(MODULOS_BIPV)
    assert seleccion_panel(_OTRO, etq, catalogo_nuevo, guardada)["panel_ficha"]["Pmax_stc"] == 999.0
    with pytest.raises(PanelSuperficieError):
        seleccion_panel("No existe", etq, MODULOS_BIPV, _sup())


# ── Energía simplificada ─────────────────────────────────────────────────────
def test_criterio_de_aceptacion_fachada_de_la_prueba():
    prod = produccion_superficie(_poa_anual(1004.0), 97.3, eficiencia_panel(MODULOS_BIPV[_PROYECTO]), 0.78)
    assert prod["e_ac_anual_kWh"] == pytest.approx(6667.3, abs=0.2)
    # Con el 16 % fijo de antes daba 12.191 kWh/año.
    assert produccion_superficie(_poa_anual(1004.0), 97.3, 0.16, 0.78)["e_ac_anual_kWh"] == pytest.approx(12191.6, abs=0.2)


def test_energia_con_panel_distinto_por_superficie():
    sups = [_sup(), _sup("Techo 1", 2, tipo="Techo inclinado", tilt_deg=10.0, **_catalogo(_OTRO))]
    etas, _, _ = eficiencias_superficies(sups, MODULOS_BIPV[_PROYECTO], _PROYECTO)
    poas = {"Fachada principal": _poa_anual(1004.0), "Techo 1": _poa_anual(1675.0)}
    res = e_ac_total_multisup(poas, sups, etas, 0.78)
    por_nombre = {d["nombre"]: d for d in res["desglose"]}
    assert por_nombre["Fachada principal"]["e_ac_kWh"] == pytest.approx(97.3 * 1004 * 0.0875 * 0.78, abs=0.2)
    assert por_nombre["Techo 1"]["e_ac_kWh"] == pytest.approx(
        97.3 * 1675 * etas["Techo 1"] * 0.78, abs=0.2)
    assert por_nombre["Techo 1"]["eta_panel"] == pytest.approx(etas["Techo 1"], abs=1e-5)
    assert res["e_ac_total_kWh"] == pytest.approx(sum(d["e_ac_kWh"] for d in res["desglose"]), abs=0.2)


def test_superficie_activa_sin_eficiencia_es_error():
    with pytest.raises(ValueError, match="eficiencia"):
        e_ac_total_multisup({"Fachada principal": _poa_anual(1000.0)}, [_sup()], {}, 0.78)


# ── Strings ──────────────────────────────────────────────────────────────────
def test_strings_estimados_con_el_modulo_de_la_superficie():
    grande = {**MODULOS_BIPV[_OTRO]}
    r = strings_superficie(_sup(n_serie=8), 8, grande, panel_es_del_proyecto=False)
    modulos = int(97.3 / area_modulo(grande))
    assert r["n_paralelo"] == max(1, round(modulos / 8))


def test_panel_distinto_sin_n_serie_no_toma_el_de_dimensionamiento():
    with pytest.raises(ValueError, match="N serie propio"):
        strings_superficie(_sup(), 8, MODULOS_BIPV[_OTRO], panel_es_del_proyecto=False)
    # Con el panel del proyecto sí se usa el de Dimensionamiento.
    assert strings_superficie(_sup(), 8, MODULOS_BIPV[_PROYECTO])["n_serie"] == 8


# ── Modo físico ──────────────────────────────────────────────────────────────
def _sup_fisica(nombre, uid, **cambios):
    base = _sup(nombre, uid, n_serie=8, n_paralelo=2, inversor_id="INV-1",
                p_shade=np.zeros(8760), firma_sombra={"f": uid},
                estado_sombra="calculado_completo")
    base.update(cambios)
    return base


def _estado_fisico(techo_panel=None):
    techo = _sup_fisica("Techo 1", 2, **(techo_panel or {}))
    return {
        "superficies_bipv": [_sup_fisica("Fachada principal", 1), techo],
        "panel_dict": dict(MODULOS_BIPV[_PROYECTO]), "panel_nombre_dim": _PROYECTO,
        "multisup_inversores": [{"inversor_id": "INV-1", "tipo": "dedicado", "eta_inversor": 0.97}],
    }


def test_modo_fisico_usa_el_panel_de_cada_superficie():
    proy = construir_proyecto_desde_session_state(_estado_fisico(_catalogo(_OTRO)))
    assert proy["superficies"]["Fachada principal"]["panel"] == MODULOS_BIPV[_PROYECTO]
    assert proy["superficies"]["Techo 1"]["panel"] == MODULOS_BIPV[_OTRO]
    base = construir_proyecto_desde_session_state(_estado_fisico())
    h_base = {n: calcular_huellas(s)["panel"] for n, s in base["superficies"].items()}
    h_nuevo = {n: calcular_huellas(s)["panel"] for n, s in proy["superficies"].items()}
    assert h_base["Fachada principal"] == h_nuevo["Fachada principal"]
    assert h_base["Techo 1"] != h_nuevo["Techo 1"]


def test_modo_fisico_sin_panel_del_proyecto_si_todas_eligen_catalogo():
    estado = _estado_fisico(_catalogo(_OTRO))
    estado["superficies_bipv"][0].update(_catalogo(_PROYECTO))
    estado.pop("panel_dict")
    proy = construir_proyecto_desde_session_state(estado)
    assert proy["superficies"]["Techo 1"]["panel"] == MODULOS_BIPV[_OTRO]
    estado["superficies_bipv"][0] = _sup_fisica("Fachada principal", 1)
    with pytest.raises(ValueError, match="Dimensionamiento"):
        construir_proyecto_desde_session_state(estado)


# ── Invalidación ─────────────────────────────────────────────────────────────
def _estado_publicado():
    sups = [_sup(firma_poa="poa-1", p_shade=np.zeros(8760), firma_sombra={"f": 1}),
            _sup("Techo 1", 2, firma_poa="poa-2")]
    estado = {
        "superficies_bipv": sups,
        "panel_dict": dict(MODULOS_BIPV[_PROYECTO]), "panel_nombre_dim": _PROYECTO,
        "poa_superficies": {1: "poa", 2: "poa"},
        "E_ac_anual_kWh_multisup": 100.0, "multisup_desglose": [{}], "multisup_activo": True,
        "multisup_origen": "simplificado", "area_total_multisup": 194.6,
        "poa_df_multisup": _poa_anual(1.0),
    }
    for clave in KEYS_RESULTADOS_PANEL:
        estado[clave] = "x"
    return estado


def test_primera_vez_solo_registra_la_firma():
    estado = _estado_publicado()
    assert invalidar_por_cambio_panel(estado) == []
    assert CLAVE_FIRMA_PANELES in estado and estado["multisup_activo"]
    assert invalidar_por_cambio_panel(estado) == []


@pytest.mark.parametrize("cambio", ["superficie", "proyecto"])
def test_cambio_de_panel_retira_energia_y_resultados_y_conserva_poa_y_sombra(cambio):
    estado = _estado_publicado()
    invalidar_por_cambio_panel(estado)
    if cambio == "superficie":
        estado["superficies_bipv"][1].update(_catalogo(_OTRO))
    else:
        estado["panel_dict"] = dict(MODULOS_BIPV["ASP-ST1-T10"])
        estado["panel_nombre_dim"] = "ASP-ST1-T10"
    retiradas = invalidar_por_cambio_panel(estado)
    for clave in ("E_ac_anual_kWh_multisup", "multisup_activo", "multisup_origen") + KEYS_RESULTADOS_PANEL:
        assert clave in retiradas and clave not in estado
    assert estado["poa_superficies"] == {1: "poa", 2: "poa"}
    assert estado["superficies_bipv"][0]["firma_poa"] == "poa-1"
    assert estado["superficies_bipv"][0]["firma_sombra"] == {"f": 1}


def test_panel_del_proyecto_no_afecta_a_superficies_con_panel_propio():
    estado = _estado_publicado()
    for s in estado["superficies_bipv"]:
        s.update(_catalogo(_OTRO))
    invalidar_por_cambio_panel(estado)
    estado["panel_dict"] = dict(MODULOS_BIPV["ASP-ST1-T10"])
    assert invalidar_por_cambio_panel(estado) == []
    assert estado["multisup_activo"]


def test_firma_estable_del_panel_calibrado():
    from calculos.modelo_iv import resolver_panel_calibrado

    a = _sup(**{**_catalogo(_OTRO), "panel_ficha": resolver_panel_calibrado(dict(MODULOS_BIPV[_OTRO]))})
    b = _sup(**{**_catalogo(_OTRO), "panel_ficha": resolver_panel_calibrado(dict(MODULOS_BIPV[_OTRO]))})
    assert firma_panel_superficie(a, None, None) == firma_panel_superficie(b, None, None)


# ── Persistencia ─────────────────────────────────────────────────────────────
def _estado_persistencia():
    estado = _estado_fisico(_catalogo(_OTRO))
    for s in estado["superficies_bipv"]:
        s["firma_poa"] = f"poa-{s['uid']}"
    estado.update({
        "multisup_activo": True, "ciudad": "Bogota", "lat_proyecto": 4.71,
        "lon_proyecto": -74.07, "alt_proyecto": 2600,
        "tmy_df": pd.DataFrame({"T2m": np.full(8760, 20.0)}, index=_IDX),
        "tmy_provider": "test-tmy",
    })
    return estado


def test_guardar_y_cargar_conserva_el_panel_de_cada_superficie():
    estado = _estado_persistencia()
    payload = construir_payload_multisuperficie(estado, {})
    assert validar_payload_multisuperficie(payload, estado).ok
    destino = {}
    assert restaurar_multisuperficie(payload, destino).ok
    techo = next(s for s in destino["superficies_bipv"] if s["nombre"] == "Techo 1")
    fachada = next(s for s in destino["superficies_bipv"] if s["nombre"] == "Fachada principal")
    assert techo["panel_origen"] == "catalogo" and techo["panel_nombre"] == _OTRO
    assert techo["panel_ficha"]["Pmax_stc"] == MODULOS_BIPV[_OTRO]["Pmax_stc"]
    assert "panel_origen" not in fachada
    assert panel_de_superficie(fachada, estado["panel_dict"], _PROYECTO)["es_proyecto"]


def test_proyecto_guardado_antes_del_cambio_carga_con_panel_del_proyecto():
    estado = _estado_persistencia()
    for s in estado["superficies_bipv"]:
        for campo in ("panel_origen", "panel_nombre", "panel_ficha"):
            s.pop(campo, None)
    payload = construir_payload_multisuperficie(estado, {})
    destino = {}
    assert restaurar_multisuperficie(payload, destino).ok
    for s in destino["superficies_bipv"]:
        assert panel_de_superficie(s, estado["panel_dict"], _PROYECTO)["origen"] == "proyecto"


def test_panel_de_superficie_distinto_rechaza_la_carga():
    estado = _estado_persistencia()
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    actual["superficies_bipv"][1].update(_catalogo("ASP-ST1-T10"))
    resultado = validar_payload_multisuperficie(payload, actual)
    assert not resultado.ok and any("Panel diferente en superficie" in e for e in resultado.errores)


def test_panel_del_proyecto_distinto_no_bloquea_si_ninguna_superficie_lo_sigue():
    estado = _estado_persistencia()
    estado["superficies_bipv"][0].update(_catalogo(_PROYECTO))
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    actual["panel_dict"] = dict(MODULOS_BIPV["ASP-ST1-T10"])
    assert validar_payload_multisuperficie(payload, actual).ok


def test_origen_de_panel_desconocido_en_payload_se_rechaza():
    estado = _estado_persistencia()
    estado["superficies_bipv"][1]["panel_origen"] = "excel"
    with pytest.raises(PayloadMultisuperficieError, match="Origen de panel"):
        construir_payload_multisuperficie(estado, {})


# ── Página ───────────────────────────────────────────────────────────────────
def test_pagina_sin_eficiencia_fija_ni_selector_comun_de_panel():
    src = _PAGINA.read_text(encoding="utf-8")
    assert 'get("eta_panel"' not in src and "get('eta_panel'" not in src
    for clave in ("ms_bp_panel_sel", "ms_mppt_panel_sel"):
        assert clave not in src
    assert 'key=f"spanel_{_uid}"' in src
    assert src.count("eficiencias_superficies_estado(") >= 4
    assert "invalidar_por_cambio_panel(" in src
    arbol = ast.parse(src)
    llamadas = [n for n in ast.walk(arbol) if isinstance(n, ast.Call)
                and ast.unparse(n.func) in ("strings_superficie", "strings_grupos_superficie")]
    assert len(llamadas) >= 2 and all(len(n.args) == 4 for n in llamadas)


def test_dimensionamiento_retira_energia_si_cambia_el_panel():
    src = (_PAGINA.parent / "4_📐_Dimensionamiento.py").read_text(encoding="utf-8")
    assert src.index('st.session_state["panel_dict"]        = panel') < src.index("invalidar_por_cambio_panel")


# ── Auditoría posterior al merge (25-sep-2026) ───────────────────────────────
@pytest.mark.parametrize("cambio", ["agregar", "eliminar", "desactivar", "renombrar"])
def test_cambios_que_no_son_de_panel_no_retiran_nada(cambio):
    # H1: agregar, eliminar o desactivar una superficie no es «cambió el panel».
    estado = _estado_publicado()
    invalidar_por_cambio_panel(estado)
    sups = estado["superficies_bipv"]
    if cambio == "agregar":
        sups.append(_sup("Pérgola", 3))
    elif cambio == "eliminar":
        sups.pop()
    elif cambio == "desactivar":
        sups[1]["activa"] = False
    else:
        sups[1]["nombre"] = "Cubierta"
    assert invalidar_por_cambio_panel(estado) == []
    assert estado["multisup_activo"]
    # Y un cambio real de panel después sí se detecta.
    sups[0].update(_catalogo(_OTRO))
    assert "multisup_activo" in invalidar_por_cambio_panel(estado)


def test_calibracion_fallida_no_tumba_el_editor():
    # H2: resolver_panel_calibrado lanza ValueError con un SDM manual inválido.
    def calibrar_falla(_ficha):
        raise ValueError("El SDM manual guardado ya no reproduce la ficha dentro del 6%.")

    with pytest.raises(PanelSuperficieError, match="6%"):
        seleccion_panel(_OTRO, "Panel del proyecto (X)", MODULOS_BIPV, _sup(), calibrar=calibrar_falla)


def test_cambio_de_panel_retira_la_comparacion_fisica():
    # H3: la comparación del modo físico se calculó con el panel anterior.
    assert "multisup_proyecto_fisico_candidato" in KEYS_RESULTADOS_PANEL


def test_resumen_no_dice_total_del_sistema_si_falta_una_superficie():
    # H4: con una superficie fuera por su panel, el total no es del sistema.
    src = _PAGINA.read_text(encoding="utf-8")
    assert "if _motivos_poa or _err_panel_g else" in src
