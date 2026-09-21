"""Validación pura de inversores/asignaciones por superficie (recreado,
ronda de recuperación 2026-09-21)."""
import pytest

from calculos.inversores_multisuperficie import (
    aplicar_tipos_derivados,
    derivar_tipo_inversor,
    validar_inversores_y_asignaciones,
)


def _sup(nombre, inversor_id=None, n_serie=7, n_paralelo=2, activa=True):
    return {"nombre": nombre, "activa": activa, "inversor_id": inversor_id,
            "n_serie": n_serie, "n_paralelo": n_paralelo}


def _inv(inversor_id, tipo="dedicado", eta=0.97):
    return {"inversor_id": inversor_id, "tipo": tipo, "eta_inversor": eta, "P_ac_nom_W": 5000.0}


def test_deriva_dedicado_con_una_superficie():
    assert derivar_tipo_inversor(1) == "dedicado"


def test_deriva_compartido_con_varias_superficies():
    assert derivar_tipo_inversor(2) == "compartido"
    assert derivar_tipo_inversor(5) == "compartido"


def test_deriva_rechaza_cero_superficies():
    with pytest.raises(ValueError, match="sin superficies"):
        derivar_tipo_inversor(0)


def test_asignacion_valida_deriva_tipos_correctos():
    superficies = [_sup("A", "INV1"), _sup("B", "INV2"), _sup("C", "INV2")]
    inversores = [_inv("INV1"), _inv("INV2")]
    resultado = validar_inversores_y_asignaciones(superficies, inversores)
    assert resultado["ok"] is True
    assert resultado["tipos_derivados"] == {"INV1": "dedicado", "INV2": "compartido"}
    assert resultado["asignaciones"]["INV2"] == ["B", "C"]


def test_superficie_sin_inversor_bloquea_con_mensaje_explicito():
    resultado = validar_inversores_y_asignaciones([_sup("A", None)], [_inv("INV1")])
    assert resultado["ok"] is False
    assert any("'A'" in e and "inversor" in e for e in resultado["errores"])


def test_superficie_referencia_inversor_inexistente():
    resultado = validar_inversores_y_asignaciones([_sup("A", "NO_EXISTE")], [_inv("INV1")])
    assert resultado["ok"] is False
    assert any("NO_EXISTE" in e for e in resultado["errores"])


def test_inversor_sin_superficies_bloquea():
    resultado = validar_inversores_y_asignaciones([_sup("A", "INV1")], [_inv("INV1"), _inv("INV2")])
    assert resultado["ok"] is False
    assert any("INV2" in e and "no tiene ninguna superficie" in e for e in resultado["errores"])
    assert "INV2" not in resultado["tipos_derivados"]


def test_inversor_duplicado_bloquea():
    resultado = validar_inversores_y_asignaciones([_sup("A", "INV1")], [_inv("INV1"), _inv("INV1")])
    assert any("duplicado" in e for e in resultado["errores"])


def test_n_serie_o_n_paralelo_invalidos_bloquean():
    superficies = [_sup("A", "INV1", n_serie=0), _sup("B", "INV1", n_paralelo=None)]
    resultado = validar_inversores_y_asignaciones(superficies, [_inv("INV1")])
    assert resultado["ok"] is False
    assert any("n_serie" in e for e in resultado["errores"])
    assert any("n_paralelo" in e for e in resultado["errores"])


def test_eta_inversor_fuera_de_rango_bloquea():
    resultado = validar_inversores_y_asignaciones([_sup("A", "INV1")], [_inv("INV1", eta=1.5)])
    assert resultado["ok"] is False
    assert any("eta_inversor" in e for e in resultado["errores"])


def test_superficies_inactivas_se_ignoran():
    resultado = validar_inversores_y_asignaciones([_sup("A", None, activa=False)], [_inv("INV1")])
    assert not any("'A'" in e for e in resultado["errores"])
    assert any("INV1" in e and "no tiene ninguna superficie" in e for e in resultado["errores"])


def test_aplicar_tipos_derivados_sobrescribe_tipo_declarado_a_mano():
    nuevos = aplicar_tipos_derivados([_inv("INV1", tipo="compartido")], {"INV1": "dedicado"})
    assert nuevos[0]["tipo"] == "dedicado"


def test_aplicar_tipos_derivados_conserva_tipo_si_no_hay_derivado():
    nuevos = aplicar_tipos_derivados([_inv("INV1", tipo="dedicado")], {})
    assert nuevos[0]["tipo"] == "dedicado"
