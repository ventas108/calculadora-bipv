import copy

import numpy as np
import pandas as pd
import pytest
import json
from streamlit import session_state

from calculos.persistencia_multisuperficie import (
    PayloadMultisuperficieError,
    construir_payload_multisuperficie,
    firmar_payload_multisuperficie,
    restaurar_multisuperficie,
    validar_payload_multisuperficie,
)


_HORAS = 8760


def _estado():
    indice = pd.date_range("2025-01-01", periods=_HORAS, freq="h", tz="UTC")
    superficie = {
        "uid": "s1",
        "nombre": "Cubierta",
        "tipo": "Techo plano",
        "activa": True,
        "area_m2": 40.0,
        "tilt_deg": 15.0,
        "azimuth_deg": 180.0,
        "n_serie": 10,
        "n_paralelo": 2,
        "inversor_id": "inv-1",
        "p_shade": np.zeros(_HORAS),
        "firma_sombra": {"geometria": "g1", "tmy_fingerprint": "t1"},
        "firma_poa": "poa-1",
    }
    return {
        "multisup_activo": True,
        "ciudad": "Bogota",
        "lat_proyecto": 4.71,
        "lon_proyecto": -74.07,
        "alt_proyecto": 2600,
        "tmy_df": pd.DataFrame({"T2m": np.full(_HORAS, 20.0)}, index=indice),
        "tmy_provider": "test-tmy",
        "superficies_bipv": [superficie],
        "panel_dict": {"modelo": "P-1", "Pmax": 400},
        "multisup_inversores": [
            {"inversor_id": "inv-1", "tipo": "dedicado", "eta_inversor": 0.97}
        ],
    }


def test_payload_valido_es_determinista_y_se_valida():
    estado = _estado()
    payload_1 = construir_payload_multisuperficie(estado, {"E_ac_total_kWh": 100.0})
    payload_2 = construir_payload_multisuperficie(estado, {"E_ac_total_kWh": 100.0})

    assert payload_1 == payload_2
    resultado = validar_payload_multisuperficie(payload_1, estado)
    assert resultado.ok
    assert resultado.firma_global == payload_1["payload_signature"]


def test_payload_alterado_rechaza_firma_global():
    payload = construir_payload_multisuperficie(_estado(), {"E_ac_total_kWh": 100.0})
    alterado = copy.deepcopy(payload)
    alterado["results"]["E_ac_total_kWh"] = 101.0

    resultado = validar_payload_multisuperficie(alterado)
    assert not resultado.ok
    assert "Firma global" in resultado.errores[0]


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("tilt_deg", 25.0), ("azimuth_deg", 90.0), ("area_m2", 41.0)],
)
def test_geometria_actual_diferente_rechaza_restauracion(campo, valor):
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    actual["superficies_bipv"][0][campo] = valor

    resultado = validar_payload_multisuperficie(payload, actual)
    assert not resultado.ok
    assert any("Geometria diferente" in error for error in resultado.errores)


def test_tmy_diferente_rechaza_restauracion():
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    actual["tmy_df"] = actual["tmy_df"].copy()
    actual["tmy_df"]["T2m"] = 21.0

    resultado = validar_payload_multisuperficie(payload, actual)
    assert not resultado.ok
    assert any("TMY diferente" in error for error in resultado.errores)


@pytest.mark.parametrize(
    "campo", ["firma_sombra", "firma_poa", "inversor_id", "n_serie", "n_paralelo"]
)
def test_firma_o_configuracion_fisica_diferente_rechaza_restauracion(campo):
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    if campo == "firma_poa":
        actual["superficies_bipv"][0][campo] = "poa-distinta"
    elif campo == "firma_sombra":
        actual["superficies_bipv"][0][campo] = {"geometria": "distinta"}
    elif campo == "inversor_id":
        actual["superficies_bipv"][0][campo] = "inv-2"
    else:
        actual["superficies_bipv"][0][campo] = 11

    resultado = validar_payload_multisuperficie(payload, actual)
    assert not resultado.ok
    assert any(campo in error for error in resultado.errores)


def test_panel_diferente_rechaza_restauracion():
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    actual["panel_dict"] = {"modelo": "P-2", "Pmax": 450}

    resultado = validar_payload_multisuperficie(payload, actual)
    assert not resultado.ok
    assert any("Panel diferente" in error for error in resultado.errores)


def test_inversores_diferentes_rechaza_restauracion():
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    actual["multisup_inversores"][0]["eta_inversor"] = 0.5

    resultado = validar_payload_multisuperficie(payload, actual)
    assert not resultado.ok
    assert any("inversores diferente" in error for error in resultado.errores)


def test_superficie_eliminada_del_contexto_rechaza_restauracion():
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {})
    actual = copy.deepcopy(estado)
    actual["superficies_bipv"] = []

    resultado = validar_payload_multisuperficie(payload, actual)
    assert not resultado.ok
    assert any("no coinciden" in error for error in resultado.errores)


def test_inversor_inexistente_en_payload_es_rechazado():
    """Un payload internamente inconsistente (superficie con inversor_id que
    no existe en la lista de inversores propia del payload) debe rechazarse
    aunque no se compare contra ningun contexto actual — protege contra
    fugas producidas antes de guardar (p.ej. borrar un inversor sin
    recalcular) o por una construccion futura defectuosa."""
    estado = _estado()
    estado["superficies_bipv"][0]["inversor_id"] = "inv-fantasma"
    payload = construir_payload_multisuperficie(estado, {})

    resultado = validar_payload_multisuperficie(payload)
    assert not resultado.ok
    assert any("Inversor" in error and "inexistente" in error for error in resultado.errores)


def test_asignaciones_desincronizadas_de_superficies_es_rechazado():
    """Un payload cuyo bloque `asignaciones` no cubre exactamente las
    superficies declaradas se rechaza, incluso con firma global valida."""
    estado = _estado()
    payload = dict(construir_payload_multisuperficie(estado, {}))
    payload["inputs"] = dict(payload["inputs"])
    payload["inputs"]["electrical"] = dict(payload["inputs"]["electrical"])
    payload["inputs"]["electrical"]["asignaciones"] = {"otro-uid": "inv-1"}
    payload["payload_signature"] = firmar_payload_multisuperficie(payload)

    resultado = validar_payload_multisuperficie(payload)
    assert not resultado.ok
    assert any("asignaciones" in error for error in resultado.errores)


@pytest.mark.parametrize(
    ("mutacion", "mensaje"),
    [
        (lambda payload: payload.pop("results"), "results"),
        (lambda payload: payload.update({"schema_version": 999}), "Version de schema"),
        (lambda payload: payload.pop("payload_signature"), "payload_signature"),
    ],
)
def test_payload_incompleto_schema_no_soportado_o_legacy_rechazado(mutacion, mensaje):
    payload = construir_payload_multisuperficie(_estado(), {})
    mutacion(payload)

    resultado = validar_payload_multisuperficie(payload)

    assert not resultado.ok
    assert any(mensaje in error for error in resultado.errores)


def test_superficie_incompleta_no_usa_defaults():
    estado = _estado()
    del estado["superficies_bipv"][0]["uid"]

    with pytest.raises(PayloadMultisuperficieError, match="uid"):
        construir_payload_multisuperficie(estado, {})


def test_restauracion_valida_publica_superficies_y_resultados_permitidos():
    estado = _estado()
    proyecto_fisico = {
        "superficies": {
            "Cubierta": {
                "resultados_dc": {
                    "P_dc_kW": np.array([1.0, 2.0]),
                    "poa_anual_kWh_m2": 1200.0,
                },
                "resultados_ac": {
                    "P_ac_kW": np.array([0.9, 1.8]),
                    "E_ac_anual_kWh": 2.7,
                },
            }
        }
    }
    payload = construir_payload_multisuperficie(
        estado,
        {
            "session_state": {
                "multisup_desglose": [{"nombre": "Cubierta"}],
                "poa_df_multisup": pd.DataFrame(
                    {"poa_global": [1.0, 2.0]},
                    index=pd.date_range("2025-01-01", periods=2, freq="h", tz="UTC"),
                ),
                "proyecto_fisico": proyecto_fisico,
            }
        },
    )
    destino = {"valor_no_tocable": "conservado"}

    resultado = restaurar_multisuperficie(payload, destino)

    assert resultado.ok
    assert destino["multisup_activo"] is True
    assert destino["superficies_bipv"][0]["uid"] == "s1"
    assert isinstance(destino["superficies_bipv"][0]["p_shade"], np.ndarray)
    assert destino["multisup_desglose"] == [{"nombre": "Cubierta"}]
    assert isinstance(destino["poa_df_multisup"], pd.DataFrame)
    restaurado = destino["_multisup_proyecto_fisico"]
    assert isinstance(restaurado["superficies"]["Cubierta"]["resultados_dc"]["P_dc_kW"], np.ndarray)
    assert restaurado["superficies"]["Cubierta"]["resultados_ac"]["E_ac_anual_kWh"] == 2.7
    assert destino["valor_no_tocable"] == "conservado"


def test_restauracion_rechazada_no_escribe_estado_parcial():
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {})
    payload["payload_signature"] = "firma-alterada"
    destino = {
        "multisup_activo": False,
        "E_ac_anual_kWh_multisup": 999.0,
        "multisup_desglose": [{"nombre": "previa"}],
        "marca": "antes",
    }
    antes = copy.deepcopy(destino)

    resultado = restaurar_multisuperficie(payload, destino)

    assert not resultado.ok
    assert destino == antes


def test_restauracion_ignora_resultados_que_no_son_multisup():
    estado = _estado()
    payload = construir_payload_multisuperficie(
        estado,
        {"session_state": {"produccion_ok": True, "multisup_activo": True}},
    )
    destino = {}

    restaurar_multisuperficie(payload, destino)

    assert "produccion_ok" not in destino
    assert destino["multisup_activo"] is True


def test_guardar_y_cargar_difiere_hasta_verificar_tmy(tmp_path, monkeypatch):
    import calculos.proyectos_manager as proyectos_manager

    monkeypatch.setattr(proyectos_manager, "DIR_PROYECTOS", str(tmp_path))
    session_state.clear()
    estado = _estado()
    session_state.update({
        **estado,
        "auth_email": "cliente@example.com",
        "nombre_proyecto": "Persistencia física",
        "E_ac_anual_kWh_multisup": 100.0,
        "area_total_multisup": 40.0,
        "multisup_desglose": [{"nombre": "Cubierta"}],
        # Spec 05/publicacion-energia-multisuperficie: la adopción física
        # publica siempre su origen; sin él, el proyecto físico no se guarda.
        "multisup_origen": "fisico",
        "multisup_perdida_bus_kWh": 0.0,
        "_multisup_proyecto_fisico": {
            "superficies": {
                "Cubierta": {
                    "resultados_dc": {"P_dc_kW": np.array([1.0, 2.0])},
                    "resultados_ac": {"P_ac_kW": np.array([0.9, 1.8])},
                }
            }
        },
        "poa_df_multisup": pd.DataFrame(
            {"poa_global": [1.0, 2.0]},
            index=pd.date_range("2025-01-01", periods=2, freq="h", tz="UTC"),
        ),
    })

    slug = proyectos_manager.guardar_proyecto_actual("Persistencia física")
    ruta = tmp_path / f"{slug}.json"
    with ruta.open(encoding="utf-8") as archivo:
        guardado = json.load(archivo)
    assert "multisuperficie" in guardado
    assert guardado["multisuperficie"]["payload_signature"]
    assert "proyecto_fisico" in guardado["multisuperficie"]["results"]["session_state"]

    session_state.clear()
    session_state["auth_email"] = "cliente@example.com"
    proyectos_manager.cargar_proyecto(slug)
    assert session_state.get("_multisup_payload_pendiente")
    assert "multisup_activo" not in session_state

    pendiente = session_state["_multisup_payload_pendiente"]
    resultado = restaurar_multisuperficie(
        pendiente, session_state, {"tmy_df": estado["tmy_df"]}
    )
    assert resultado.ok
    assert session_state["multisup_activo"] is True
    assert "_multisup_proyecto_fisico" in session_state
    assert session_state["multisup_origen"] == "fisico"
    assert session_state["multisup_perdida_bus_kWh"] == 0.0


def test_cargar_proyecto_sin_multisuperficie_limpia_estado_fisico_previo(
    tmp_path, monkeypatch
):
    """Regresion: cambiar de un proyecto CON modo fisico activo a otro SIN
    payload multi-superficie dejaba vivo `multisup_activo=True` y las
    superficies/resultados del proyecto anterior, que Finanzas/CO2/
    Presupuesto/Baterias/Reporte seguian leyendo como si fueran del proyecto
    recien cargado."""
    import calculos.proyectos_manager as proyectos_manager

    monkeypatch.setattr(proyectos_manager, "DIR_PROYECTOS", str(tmp_path))

    # Proyecto A: multi-superficie activo.
    session_state.clear()
    session_state.update({
        **_estado(),
        "auth_email": "cliente@example.com",
        "nombre_proyecto": "Proyecto A",
        "E_ac_anual_kWh_multisup": 999.0,
    })
    proyectos_manager.guardar_proyecto_actual("Proyecto A")

    # Proyecto B: sin modo fisico.
    session_state.clear()
    session_state.update({
        "auth_email": "cliente@example.com",
        "nombre_proyecto": "Proyecto B",
        "ciudad": "Medellin",
    })
    slug_b = proyectos_manager.guardar_proyecto_actual("Proyecto B")

    # La sesion sigue con el estado fisico del proyecto A cuando se carga B.
    session_state.clear()
    session_state.update({
        "auth_email": "cliente@example.com",
        **_estado(),
        "E_ac_anual_kWh_multisup": 999.0,
    })
    proyectos_manager.cargar_proyecto(slug_b)

    assert session_state.get("multisup_activo") is None
    assert "superficies_bipv" not in session_state
    assert "multisup_inversores" not in session_state
    assert "E_ac_anual_kWh_multisup" not in session_state
    assert "poa_df_multisup" not in session_state
    assert "_multisup_payload_pendiente" not in session_state


def test_cargar_proyecto_limpia_payload_pendiente_no_resuelto_del_anterior(
    tmp_path, monkeypatch
):
    """Si el usuario carga el proyecto A (queda con un payload pendiente sin
    resolver porque no visito Recurso Solar) y luego carga el proyecto B sin
    pasar por alli, el payload pendiente de A no debe sobrevivir para
    restaurarse mas tarde contra el TMY de B."""
    import calculos.proyectos_manager as proyectos_manager

    monkeypatch.setattr(proyectos_manager, "DIR_PROYECTOS", str(tmp_path))

    session_state.clear()
    session_state.update({
        **_estado(),
        "auth_email": "cliente@example.com",
        "nombre_proyecto": "Proyecto A",
    })
    slug_a = proyectos_manager.guardar_proyecto_actual("Proyecto A")

    session_state.clear()
    session_state.update({
        "auth_email": "cliente@example.com",
        "nombre_proyecto": "Proyecto B",
        "ciudad": "Medellin",
    })
    slug_b = proyectos_manager.guardar_proyecto_actual("Proyecto B")

    session_state.clear()
    session_state["auth_email"] = "cliente@example.com"
    proyectos_manager.cargar_proyecto(slug_a)
    assert session_state.get("_multisup_payload_pendiente")

    proyectos_manager.cargar_proyecto(slug_b)
    assert "_multisup_payload_pendiente" not in session_state


# ── Spec 05/publicacion-energia-multisuperficie: origen de la energía ───────
def _restaurar_con_resultados(resultados):
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {"session_state": resultados})
    destino = {}
    return restaurar_multisuperficie(payload, destino, {"tmy_df": estado["tmy_df"]}), destino


def test_restaurar_conserva_el_origen_guardado():
    resultado, destino = _restaurar_con_resultados(
        {"E_ac_anual_kWh_multisup": 100.0, "multisup_origen": "bypass_csv"}
    )
    assert resultado.ok
    assert destino["multisup_origen"] == "bypass_csv"
    assert "_multisup_proyecto_fisico" not in destino


def test_restaurar_proyecto_fisico_antiguo_infiere_origen_fisico():
    resultado, destino = _restaurar_con_resultados(
        {"E_ac_anual_kWh_multisup": 100.0, "proyecto_fisico": {"superficies": {}}}
    )
    assert resultado.ok and destino["multisup_origen"] == "fisico"


def test_restaurar_rechaza_origen_fisico_sin_proyecto():
    resultado, destino = _restaurar_con_resultados(
        {"E_ac_anual_kWh_multisup": 100.0, "multisup_origen": "fisico"}
    )
    assert not resultado.ok and destino == {}


def test_restaurar_rechaza_firma_poa_distinta():
    estado = _estado()
    payload = construir_payload_multisuperficie(estado, {"session_state": {}})
    actuales = copy.deepcopy(estado["superficies_bipv"])
    actuales[0]["firma_poa"] = "poa-otra"
    destino = {}
    resultado = restaurar_multisuperficie(
        payload, destino, {"tmy_df": estado["tmy_df"], "superficies_bipv": actuales}
    )
    assert not resultado.ok
    assert any("firma_poa" in e for e in resultado.errores)
    assert destino == {}
