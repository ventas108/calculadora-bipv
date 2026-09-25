"""Spec 03-dimensionamiento/diseno-electrico-multisuperficie — fase A2.

Modo físico por grupos de strings, asignaciones por grupo, temperaturas de
diseño del proyecto y regla hacia Financiero (🔴 no publica el físico).
"""
import copy

import pytest

from calculos.adaptador_multisuperficie import (
    aplicar_proyecto_a_session_state,
    construir_proyecto_desde_session_state,
)
from calculos.inversores_multisuperficie import validar_inversores_y_asignaciones
from calculos.vinculador_sombra_multisuperficie import construir_y_recalcular_proyecto_fisico
from tests.test_flujo_fisico_multisuperficie_end_to_end import (
    _ALT_M, _INVERSOR_FICHA, _LAT, _LON, _PANEL, _superficie, _tmy,
)


def _inv(inv_id, p_ac=6000.0):
    return {"inversor_id": inv_id, "tipo": "", "eta_inversor": 0.97, "P_ac_nom_W": p_ac,
            "ficha": dict(_INVERSOR_FICHA), "origen_ficha": "catalogo", "nombre": "Ficha e2e"}


def _grupo(gid, inv, n_serie, n_par, mppt=1):
    return {"gid": gid, "topologia": "string", "inversor_id": inv, "mppt": mppt,
            "n_serie": n_serie, "n_paralelo": n_par}


def _estado_dos_grupos(tmy):
    sup = _superficie("Sur", tilt=30.0, azimuth=180.0, inversor_id=None, p_shade_valor=0.1, tmy=tmy)
    sup.update(inversor_id=None, n_serie=None, n_paralelo=None,
               grupos=[_grupo("G1", "INV-1", 7, 2), _grupo("G2", "INV-2", 7, 1)])
    return {"panel_dict": _PANEL, "superficies_bipv": [sup],
            "multisup_inversores": [_inv("INV-1"), _inv("INV-2")],
            "T_min_diseno": 5.0, "T_cel_realista": 36.35, "T_cel_extremo": 41.94}


def _estado_dos_superficies(tmy):
    a = _superficie("Sur", tilt=30.0, azimuth=180.0, inversor_id="INV-1", p_shade_valor=0.1, tmy=tmy)
    b = _superficie("Sur-b", tilt=30.0, azimuth=180.0, inversor_id="INV-2", p_shade_valor=0.1, tmy=tmy)
    a.update(n_serie=7, n_paralelo=2)
    b.update(n_serie=7, n_paralelo=1, uid=a["uid"] + 1)
    return {"panel_dict": _PANEL, "superficies_bipv": [a, b],
            "multisup_inversores": [_inv("INV-1"), _inv("INV-2")],
            "T_min_diseno": 5.0, "T_cel_realista": 36.35, "T_cel_extremo": 41.94}


@pytest.fixture(scope="module")
def tmy():
    return _tmy()


# ── Asignaciones por grupo ───────────────────────────────────────────────────
def test_asignaciones_y_tipos_por_grupo(tmy):
    estado = _estado_dos_grupos(tmy)
    estado["superficies_bipv"][0]["grupos"][1]["inversor_id"] = "INV-1"
    v = validar_inversores_y_asignaciones(estado["superficies_bipv"], [_inv("INV-1")])
    assert v["ok"] and v["asignaciones"]["INV-1"] == ["Sur · G1", "Sur · G2"]
    assert v["tipos_derivados"]["INV-1"] == "compartido"


def test_errores_por_grupo_nombran_el_grupo(tmy):
    estado = _estado_dos_grupos(tmy)
    estado["superficies_bipv"][0]["grupos"][1].update(inversor_id=None, n_serie=0)
    v = validar_inversores_y_asignaciones(estado["superficies_bipv"], estado["multisup_inversores"])
    assert "La superficie 'Sur' (G2) no tiene inversor asignado." in v["errores"]
    assert "La superficie 'Sur' (G2) tiene n_serie invalido." in v["errores"]


def test_superficie_antigua_sigue_validando_igual(tmy):
    estado = _estado_dos_superficies(tmy)
    v = validar_inversores_y_asignaciones(estado["superficies_bipv"], estado["multisup_inversores"])
    assert v["ok"] and v["asignaciones"] == {"INV-1": ["Sur"], "INV-2": ["Sur-b"]}


# ── Modo físico por grupos ───────────────────────────────────────────────────
def test_una_unidad_fisica_por_grupo(tmy):
    proy = construir_proyecto_desde_session_state(_estado_dos_grupos(tmy))
    assert set(proy["superficies"]) == {"Sur · G1", "Sur · G2"}
    g1, g2 = proy["superficies"]["Sur · G1"], proy["superficies"]["Sur · G2"]
    assert (g1["n_serie"], g1["n_paralelo"], g1["inversor_id"]) == (7, 2, "INV-1")
    assert (g2["n_serie"], g2["n_paralelo"], g2["inversor_id"]) == (7, 1, "INV-2")
    assert g1["superficie_origen"] == g2["superficie_origen"] == "Sur"
    # Sin área del módulo en la ficha, el área se reparte por módulos.
    assert g1["area_m2"] + g2["area_m2"] == pytest.approx(20.0)
    assert g1["area_m2"] == pytest.approx(20.0 * 14 / 21)
    assert proy["temperaturas_diseno"]["origen"] == "proyecto"


def test_criterio_a2_dos_grupos_equivalen_a_dos_superficies(tmy):
    grupos = construir_y_recalcular_proyecto_fisico(_estado_dos_grupos(tmy), tmy, _LAT, _LON, _ALT_M)
    superficies = construir_y_recalcular_proyecto_fisico(_estado_dos_superficies(tmy), tmy, _LAT, _LON, _ALT_M)
    assert grupos["agregados"]["E_ac_total_kWh"] == pytest.approx(
        superficies["agregados"]["E_ac_total_kWh"], abs=0.5)
    estado = _estado_dos_grupos(tmy)
    aplicar_proyecto_a_session_state(grupos, estado)
    assert [f["nombre"] for f in estado["multisup_desglose"]] == ["Sur"]
    fila = estado["multisup_desglose"][0]
    assert fila["e_ac_kWh"] == pytest.approx(sum(
        s["resultados_ac"]["E_ac_anual_kWh"] for s in grupos["superficies"].values()), abs=0.2)
    assert estado["area_total_multisup"] == pytest.approx(20.0, abs=0.01)


def test_compatibilidad_fisica_con_temperaturas_del_proyecto(tmy):
    frio = _estado_dos_superficies(tmy)
    frio["T_min_diseno"] = -20.0
    proy_frio = construir_y_recalcular_proyecto_fisico(frio, tmy, _LAT, _LON, _ALT_M)
    proy_base = construir_y_recalcular_proyecto_fisico(_estado_dos_superficies(tmy), tmy, _LAT, _LON, _ALT_M)
    voc_frio = proy_frio["superficies"]["Sur"]["resultados_ac"]["compatibilidad_electrica"]["Voc_frio"]
    voc_base = proy_base["superficies"]["Sur"]["resultados_ac"]["compatibilidad_electrica"]["Voc_frio"]
    assert voc_frio > voc_base


# ── Regla hacia Financiero ───────────────────────────────────────────────────
def test_fisico_con_diseno_rojo_no_se_publica(tmy):
    estado = _estado_dos_superficies(tmy)
    proy = construir_y_recalcular_proyecto_fisico(estado, tmy, _LAT, _LON, _ALT_M)
    rojo = copy.deepcopy(estado)
    rojo["superficies_bipv"][0]["n_serie"] = 30   # Voc en frío ≈ 1.290 V > 1.000 V
    with pytest.raises(ValueError, match="no se publica"):
        aplicar_proyecto_a_session_state(proy, rojo)
    assert "multisup_activo" not in rojo


def test_fisico_publica_su_estado_electrico(tmy):
    estado = _estado_dos_superficies(tmy)
    proy = construir_y_recalcular_proyecto_fisico(estado, tmy, _LAT, _LON, _ALT_M)
    aplicar_proyecto_a_session_state(proy, estado)
    assert estado["multisup_estado_electrico"]["estado"] in ("verde", "amarillo")
    assert estado["multisup_estado_electrico"]["texto"]


# ── Persistencia de grupos ───────────────────────────────────────────────────
def _estado_guardable(tmy):
    estado = _estado_dos_grupos(tmy)
    estado["superficies_bipv"][0]["grupos"][1]["mppt"] = 2
    estado.update({"multisup_activo": True, "ciudad": "Bogota", "lat_proyecto": _LAT,
                   "lon_proyecto": _LON, "alt_proyecto": _ALT_M, "tmy_df": tmy,
                   "tmy_provider": "test"})
    return estado


def test_guardar_y_cargar_conserva_grupos_y_fichas(tmy):
    from calculos.persistencia_multisuperficie import (
        construir_payload_multisuperficie, restaurar_multisuperficie, validar_payload_multisuperficie,
    )
    estado = _estado_guardable(tmy)
    payload = construir_payload_multisuperficie(estado, {})
    assert payload["inputs"]["electrical"]["asignaciones"] == {
        str(estado["superficies_bipv"][0]["uid"]): ["INV-1", "INV-2"]}
    assert validar_payload_multisuperficie(payload, estado).ok
    destino = {}
    assert restaurar_multisuperficie(payload, destino).ok
    grupos = destino["superficies_bipv"][0]["grupos"]
    assert [(g["gid"], g["inversor_id"], g["mppt"]) for g in grupos] == [("G1", "INV-1", 1), ("G2", "INV-2", 2)]
    assert destino["multisup_inversores"][0]["ficha"]["Vdc_max"] == 1000.0


def test_grupos_distintos_rechazan_la_carga(tmy):
    from calculos.persistencia_multisuperficie import (
        construir_payload_multisuperficie, validar_payload_multisuperficie,
    )
    estado = _estado_guardable(tmy)
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    actual["superficies_bipv"][0]["grupos"][1]["n_serie"] = 6
    r = validar_payload_multisuperficie(payload, actual)
    assert not r.ok and any("Grupos de strings diferentes" in e for e in r.errores)


@pytest.mark.parametrize("grupos, fragmento", [
    ("no-lista", "no es una lista"),
    ([{"gid": "G1"}, {"gid": "G1"}], "repetido"),
    ([{"gid": "G1", "topologia": "solar-magico"}], "Topología desconocida"),
])
def test_grupos_invalidos_se_rechazan(tmy, grupos, fragmento):
    from calculos.persistencia_multisuperficie import (
        PayloadMultisuperficieError, construir_payload_multisuperficie,
    )
    estado = _estado_guardable(tmy)
    estado["superficies_bipv"][0]["grupos"] = grupos
    with pytest.raises(PayloadMultisuperficieError, match=fragmento):
        construir_payload_multisuperficie(estado, {})


# ── Bypass por grupo y sección 6 (fase A2) ───────────────────────────────────
from pathlib import Path

from calculos.publicacion_multisuperficie import aviso_estado_electrico
from calculos.strings_superficie import (
    perdida_ponderada_por_modulos, strings_grupos_superficie, strings_superficie,
)

_PAGINAS = Path(__file__).resolve().parents[1] / "pages"


def _sup_grupos(*grupos):
    return {"nombre": "Techo", "area_m2": 40.0, "grupos": list(grupos)}


def test_strings_por_grupo_usa_los_de_cada_grupo():
    r = strings_grupos_superficie(
        _sup_grupos(_grupo("G1", "INV-1", 8, 2), _grupo("G2", "INV-1", 6, 1)), 10, _PANEL)
    assert [(g["gid"], g["n_serie"], g["n_paralelo"], g["modulos"]) for g in r] == [
        ("G1", 8, 2, 16), ("G2", 6, 1, 6)]
    assert all(g["aviso"] is None for g in r)


def test_strings_por_grupo_sin_datos_nombra_el_grupo_y_no_estima():
    with pytest.raises(ValueError, match=r"'Techo' \(G2\)"):
        strings_grupos_superficie(
            _sup_grupos(_grupo("G1", "INV-1", 8, 2), _grupo("G2", "INV-1", None, 1)), 10, _PANEL)


def test_strings_un_grupo_equivale_a_la_superficie_antigua():
    antigua = {"nombre": "Sur", "area_m2": 20.0, "n_serie": 7, "n_paralelo": 2}
    r = strings_grupos_superficie(antigua, 10, _PANEL)
    base = strings_superficie(antigua, 10, _PANEL)
    assert r == [{"gid": "G1", **base, "modulos": 14}]
    r1 = strings_grupos_superficie(_sup_grupos(_grupo("G1", "INV-1", 7, 2)), 10, _PANEL)
    assert (r1[0]["n_serie"], r1[0]["n_paralelo"], r1[0]["origen"]) == (7, 2, "superficie")


def test_strings_superficie_rechaza_varios_grupos():
    # Estimar por área una superficie con varios grupos inventaría el diseño.
    with pytest.raises(ValueError, match="2 grupos"):
        strings_superficie(
            _sup_grupos(_grupo("G1", "INV-1", 8, 2), _grupo("G2", "INV-1", 6, 1)), 10, _PANEL)


def test_perdida_de_la_superficie_ponderada_por_modulos():
    pct = perdida_ponderada_por_modulos([{"pct": 3.0, "modulos": 16}, {"pct": 9.0, "modulos": 8}])
    assert pct == pytest.approx((3 * 16 + 9 * 8) / 24)
    assert perdida_ponderada_por_modulos([{"pct": 4.2, "modulos": 5}]) == pytest.approx(4.2)
    with pytest.raises(ValueError):
        perdida_ponderada_por_modulos([])


@pytest.mark.parametrize("estado, nivel", [
    ("rojo", "error"), ("amarillo", "warning"), ("verde", "caption"),
])
def test_aviso_estado_electrico_por_color(estado, nivel):
    ss = {"multisup_activo": True,
          "multisup_estado_electrico": {"estado": estado, "texto": f"x {estado}"}}
    assert aviso_estado_electrico(ss) == (nivel, f"Energía publicada con x {estado}")


def test_aviso_estado_electrico_sin_publicacion_o_sin_estado():
    assert aviso_estado_electrico({}) is None
    assert aviso_estado_electrico({"multisup_activo": True}) is None
    assert aviso_estado_electrico({"multisup_estado_electrico": {"estado": "rojo", "texto": "x"}}) is None


@pytest.mark.parametrize("pagina", [
    "7_💰_Financiero.py", "11_🔋_Baterias_y_Balance.py", "12_🌿_Impacto_CO2.py", "9_🗺️_Vista_3D.py",
])
def test_paginas_consumidoras_muestran_el_estado_electrico(pagina):
    src = (_PAGINAS / pagina).read_text(encoding="utf-8")
    assert "aviso_estado_electrico" in src
    assert "_ee(st.session_state)" in src or "aviso_estado_electrico(st.session_state)" in src


def test_pagina_bypass_por_grupo_y_seccion6_explicita():
    src = (_PAGINAS / "9_🗺️_Vista_3D.py").read_text(encoding="utf-8")
    assert "strings_grupos_superficie(" in src and "perdida_ponderada_por_modulos(" in src
    assert '"Pérdida por grupo"' in src
    assert "no la(s) incluye" in src and "for _sp_str in _sups_mp:" in src
    assert "no se puede adoptar" in src


def test_editor_conserva_los_grupos_al_reconstruir_la_superficie():
    # Hallado en la prueba de humo A2: el editor reconstruye cada superficie en
    # cada rerun y perdía los grupos (➕ Agregar grupo no tenía efecto).
    from calculos.vinculador_sombra_multisuperficie import preservar_o_invalidar_campos_fisicos
    grupos = [_grupo("G1", "INV-1", 8, 1), _grupo("G2", "INV-1", 8, 2, mppt=2)]
    anterior = {"uid": 2, "nombre": "Techo", "tilt_deg": 10.0, "azimuth_deg": 180.0,
                "area_m2": 30.0, "grupos": grupos, "p_shade": [0.1], "firma_sombra": {"x": 1}}
    editada = {k: anterior[k] for k in ("uid", "nombre", "tilt_deg", "azimuth_deg", "area_m2")}
    nueva = preservar_o_invalidar_campos_fisicos(anterior, editada)
    assert nueva["grupos"] == grupos and nueva["grupos"] is not grupos
    assert nueva["firma_sombra"] == {"x": 1}
    # Cambiar el N serie de un grupo invalida la sombra, como con el campo antiguo.
    otra = copy.deepcopy(anterior)
    otra["grupos"][1]["n_serie"] = 9
    nueva2 = preservar_o_invalidar_campos_fisicos(anterior, {**editada, "grupos": otra["grupos"]})
    assert "firma_sombra" not in nueva2 and nueva2["sombra_invalidada_motivo"] == "cambió N serie"


def test_fisico_no_publica_con_strings_de_distinto_largo_en_un_mppt(tmy):
    estado = _estado_dos_grupos(tmy)
    proy = construir_y_recalcular_proyecto_fisico(estado, tmy, _LAT, _LON, _ALT_M)
    distinto = copy.deepcopy(estado)
    distinto["superficies_bipv"][0]["grupos"] = [_grupo("G1", "INV-1", 7, 1), _grupo("G2", "INV-1", 6, 1)]
    with pytest.raises(ValueError, match="distinto largo"):
        aplicar_proyecto_a_session_state(proy, distinto)
    assert "multisup_activo" not in distinto
