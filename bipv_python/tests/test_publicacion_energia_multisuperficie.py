"""Spec 05-perdidas-y-temperatura/publicacion-energia-multisuperficie.

Tres botones de Vista 3D (Integrar, bypass por superficie y Adoptar físico)
escribían las claves de energía multi-superficie cada uno a su manera: el
bypass cambiaba el total sin tocar desglose, área ni POA ponderada, y un
proyecto físico adoptado sobrevivía a una publicación posterior de otro
origen. Ahora una sola función publica todo junto, con origen explícito.
"""
import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from calculos.adaptador_multisuperficie import aplicar_proyecto_a_session_state
from calculos.invalidacion import KEYS_DERIVADOS_POA, KEYS_MULTISUP_ESTADO
from calculos.publicacion_multisuperficie import (
    CLAVES_PUBLICACION,
    ETIQUETA_ORIGEN,
    ORIGEN_DESCONOCIDO,
    ORIGENES,
    origen_vigente,
    publicar_energia_multisuperficie,
    resultados_multisuperficie_a_guardar,
    retirar_energia_multisuperficie,
)

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
_INDICE = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")


def _poa(valor=500.0):
    return pd.DataFrame({"poa_global": np.full(8760, valor)}, index=_INDICE)


def _desglose():
    return [
        {"nombre": "Sur", "tipo": "Fachada", "area_m2": 20.0, "e_ac_kWh": 1500.0, "poa_kWh_m2": 800.0},
        {"nombre": "Techo", "tipo": "Techo", "area_m2": 30.0, "e_ac_kWh": 4500.0, "poa_kWh_m2": 1600.0},
    ]


def _datos(**cambios):
    datos = {"e_ac_total": 6000.0, "desglose": _desglose(), "poa_ponderada": _poa(),
             "area_total": 50.0}
    datos.update(cambios)
    return datos


def _proyecto():
    return {
        "superficies": {
            "Sur": {"nombre": "Sur", "tipo": "Fachada", "area_m2": 20.0, "poa_df": _poa(400.0),
                    "resultados_dc": {"poa_anual_kWh_m2": 800.0},
                    "resultados_ac": {"E_ac_anual_kWh": 1500.0}},
            "Techo": {"nombre": "Techo", "tipo": "Techo", "area_m2": 30.0, "poa_df": _poa(600.0),
                      "resultados_dc": {"poa_anual_kWh_m2": 1600.0},
                      "resultados_ac": {"E_ac_anual_kWh": 4500.0}},
        },
        # El bus compartido recorta 120 kWh: el total NO es la suma del desglose.
        "agregados": {"E_ac_total_kWh": 5880.0, "area_total_m2": 50.0},
    }


# ── Publicación por origen ───────────────────────────────────────────────────
@pytest.mark.parametrize("origen", ["simplificado", "bypass_csv"])
def test_publica_todas_las_claves_coherentes(origen):
    estado = {}
    r = publicar_energia_multisuperficie(estado, origen=origen, **_datos())
    assert r["publicado"] and not r["requiere_confirmacion"]
    assert estado["multisup_activo"] is True and estado["multisup_origen"] == origen
    assert estado["E_ac_anual_kWh_multisup"] == 6000.0
    assert sum(d["e_ac_kWh"] for d in estado["multisup_desglose"]) == pytest.approx(6000.0)
    assert sum(d["area_m2"] for d in estado["multisup_desglose"]) == estado["area_total_multisup"]
    assert len(estado["poa_df_multisup"]) == 8760
    assert "_multisup_proyecto_fisico" not in estado
    assert "multisup_perdida_bus_kWh" not in estado


def test_publicacion_fisica_registra_la_perdida_de_bus():
    estado = {}
    aplicar_proyecto_a_session_state(_proyecto(), estado)
    assert estado["multisup_origen"] == "fisico"
    assert estado["E_ac_anual_kWh_multisup"] == 5880.0
    assert estado["multisup_perdida_bus_kWh"] == pytest.approx(120.0)
    assert estado["_multisup_proyecto_fisico"]["agregados"]["E_ac_total_kWh"] == 5880.0
    np.testing.assert_allclose(estado["poa_df_multisup"]["poa_global"], 520.0)


def test_origen_fisico_exige_proyecto():
    with pytest.raises(ValueError, match="proyecto"):
        publicar_energia_multisuperficie({}, origen="fisico", **_datos())


def test_proyecto_fisico_con_otro_origen_se_rechaza():
    with pytest.raises(ValueError, match="fisico"):
        publicar_energia_multisuperficie(
            {}, origen="simplificado", proyecto_fisico=_proyecto(), **_datos())


# ── Atomicidad ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cambio, patron", [
    ({"e_ac_total": 6100.0}, "desglose"),
    ({"area_total": 55.0}, "[áa]rea"),
    ({"desglose": []}, "desglose"),
    ({"poa_ponderada": pd.DataFrame()}, "POA"),
    ({"poa_ponderada": None}, "POA"),
    ({"poa_ponderada": _poa().iloc[:100]}, "8760"),
    ({"e_ac_total": float("nan")}, "E_ac"),
])
def test_publicacion_incoherente_no_escribe_nada(cambio, patron):
    estado = {"multisup_activo": False, "otra": 1}
    antes = dict(estado)
    with pytest.raises(ValueError, match=patron):
        publicar_energia_multisuperficie(estado, origen="simplificado", **_datos(**cambio))
    assert estado == antes


def test_origen_fuera_del_conjunto_cerrado():
    assert set(ORIGENES) == {"simplificado", "bypass_csv", "fisico"}
    with pytest.raises(ValueError, match="origen"):
        publicar_energia_multisuperficie({}, origen="manual", **_datos())


def test_proyecto_incompleto_no_toca_una_publicacion_anterior():
    estado = {}
    publicar_energia_multisuperficie(estado, origen="simplificado", **_datos())
    antes = dict(estado)
    roto = _proyecto()
    del roto["superficies"]["Techo"]["resultados_ac"]
    with pytest.raises(ValueError):
        aplicar_proyecto_a_session_state(roto, estado)
    assert estado == antes


# ── Reemplazo de origen ──────────────────────────────────────────────────────
def test_reemplazar_otro_origen_exige_confirmacion():
    estado = {}
    aplicar_proyecto_a_session_state(_proyecto(), estado)
    antes = {k: estado[k] for k in estado}
    r = publicar_energia_multisuperficie(estado, origen="simplificado", **_datos())
    assert r == {"publicado": False, "requiere_confirmacion": True, "origen_vigente": "fisico"}
    assert estado.keys() == antes.keys() and estado["multisup_origen"] == "fisico"

    r = publicar_energia_multisuperficie(
        estado, origen="simplificado", confirmar_reemplazo=True, **_datos())
    assert r["publicado"] and estado["multisup_origen"] == "simplificado"
    assert "_multisup_proyecto_fisico" not in estado
    assert "multisup_perdida_bus_kWh" not in estado


def test_mismo_origen_reemplaza_sin_confirmar():
    estado = {}
    publicar_energia_multisuperficie(estado, origen="bypass_csv", **_datos())
    r = publicar_energia_multisuperficie(
        estado, origen="bypass_csv", **_datos(e_ac_total=5000.0, desglose=[
            {**_desglose()[0], "e_ac_kWh": 1000.0}, {**_desglose()[1], "e_ac_kWh": 4000.0}]))
    assert r["publicado"] and estado["E_ac_anual_kWh_multisup"] == 5000.0


def test_adoptar_fisico_sobre_simplificado_puede_pedir_confirmacion():
    estado = {}
    publicar_energia_multisuperficie(estado, origen="simplificado", **_datos())
    r = aplicar_proyecto_a_session_state(_proyecto(), estado, confirmar_reemplazo=False)
    assert r["requiere_confirmacion"] and estado["multisup_origen"] == "simplificado"
    r = aplicar_proyecto_a_session_state(_proyecto(), estado)  # confirmado por el usuario
    assert r["publicado"] and estado["multisup_origen"] == "fisico"


def test_origen_vigente_y_sesion_antigua():
    assert origen_vigente({}) is None
    assert origen_vigente({"multisup_activo": False, "multisup_origen": "fisico"}) is None
    legado = {"multisup_activo": True, "E_ac_anual_kWh_multisup": 1.0}
    assert origen_vigente(legado) == ORIGEN_DESCONOCIDO
    assert set(ETIQUETA_ORIGEN) == set(ORIGENES) | {ORIGEN_DESCONOCIDO}
    r = publicar_energia_multisuperficie(legado, origen="simplificado", **_datos())
    assert r["requiere_confirmacion"] and r["origen_vigente"] == ORIGEN_DESCONOCIDO


# ── Retirar ──────────────────────────────────────────────────────────────────
def test_retirar_borra_todas_las_claves_de_la_publicacion():
    estado = {"bypass_multisup_resultados": [1]}
    aplicar_proyecto_a_session_state(_proyecto(), estado)
    retiradas = retirar_energia_multisuperficie(estado)
    assert set(retiradas) == set(CLAVES_PUBLICACION)
    assert estado == {"bypass_multisup_resultados": [1]}
    assert retirar_energia_multisuperficie(estado) == []


# ── Estado: invalidación y guardado ──────────────────────────────────────────
def test_invalidacion_incluye_las_claves_nuevas():
    for clave in ("multisup_origen", "multisup_perdida_bus_kWh", "_multisup_proyecto_fisico"):
        assert clave in KEYS_DERIVADOS_POA
        assert clave in KEYS_MULTISUP_ESTADO
    assert set(CLAVES_PUBLICACION) <= set(KEYS_MULTISUP_ESTADO)


def test_proyectos_manager_excluye_y_resetea_las_claves_nuevas():
    src = (Path(__file__).resolve().parents[1] / "calculos" / "proyectos_manager.py").read_text(
        encoding="utf-8")
    for clave in ("multisup_origen", "multisup_perdida_bus_kWh", "poa_superficies",
                  "poa_superficies_errores", "poa_superficies_ok"):
        assert src.count(f'"{clave}"') >= 2, clave  # _CLAVES_EXCLUIR y reset al cargar


def test_guardado_tras_reemplazar_fisico_no_lleva_proyecto_fisico():
    estado = {}
    aplicar_proyecto_a_session_state(_proyecto(), estado)
    publicar_energia_multisuperficie(
        estado, origen="simplificado", confirmar_reemplazo=True, **_datos())
    resultados = resultados_multisuperficie_a_guardar(estado)
    assert "proyecto_fisico" not in resultados
    assert resultados["multisup_origen"] == "simplificado"
    aplicar_proyecto_a_session_state(_proyecto(), estado)
    resultados = resultados_multisuperficie_a_guardar(estado)
    assert "proyecto_fisico" in resultados
    assert resultados["multisup_perdida_bus_kWh"] == pytest.approx(120.0)


# ── Página: los botones solo publican a través de la función central ─────────
_CLAVES_ENERGIA = {
    "E_ac_anual_kWh_multisup", "multisup_desglose", "poa_df_multisup",
    "area_total_multisup", "multisup_activo", "multisup_origen",
    "multisup_perdida_bus_kWh", "_multisup_proyecto_fisico",
}


def test_pagina_no_escribe_ni_borra_claves_de_energia_directamente():
    arbol = ast.parse(_PAGINA.read_text(encoding="utf-8"))
    culpables = []
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Subscript) and isinstance(nodo.ctx, (ast.Store, ast.Del))
                and isinstance(nodo.slice, ast.Constant) and nodo.slice.value in _CLAVES_ENERGIA):
            culpables.append(f"línea {nodo.lineno}: {ast.unparse(nodo)}")
        if (isinstance(nodo, ast.Call) and ast.unparse(nodo.func).endswith("session_state.pop")
                and nodo.args and isinstance(nodo.args[0], ast.Constant)
                and nodo.args[0].value in _CLAVES_ENERGIA):
            culpables.append(f"línea {nodo.lineno}: {ast.unparse(nodo)}")
        if isinstance(nodo, ast.For) and isinstance(nodo.iter, (ast.Tuple, ast.List)):
            literales = {e.value for e in nodo.iter.elts if isinstance(e, ast.Constant)}
            if literales & _CLAVES_ENERGIA:
                culpables.append(f"línea {nodo.lineno}: bucle sobre claves de energía")
    assert not culpables, "; ".join(culpables)


def test_pagina_usa_publicacion_central_en_los_tres_origenes():
    src = _PAGINA.read_text(encoding="utf-8")
    assert 'origen="simplificado"' in src
    assert 'origen="bypass_csv"' in src
    assert "aplicar_proyecto_a_session_state(" in src
    assert "retirar_energia_multisuperficie(st.session_state)" in src
    assert "_multisup_publicacion_pendiente" in src
    assert "ETIQUETA_ORIGEN" in src


def test_bypass_muestra_origen_y_permite_desactivar_en_su_seccion():
    """El usuario no veía el banner del origen (está en ⚙️ Superficies BIPV)
    desde la sección del bypass: ahí mismo se muestra el origen vigente y un
    «✖ Desactivar» que usa la misma retirada central."""
    src = _PAGINA.read_text(encoding="utf-8")
    inicio = src.index('key="btn_bypass_multisup"')
    fin = src.index("# ── 🔀 6. Strings de distinta orientación", inicio)
    bloque = src[inicio:fin]
    assert 'key="btn_desactivar_multisup_bypass"' in bloque
    assert "retirar_energia_multisuperficie(st.session_state)" in bloque
    assert "ETIQUETA_ORIGEN[_origen_bp]" in bloque
    assert "Activo en Financiero" in bloque and "origen" in bloque
