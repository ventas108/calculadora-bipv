"""Frontera pura sombras_3d -> superficies_bipv -> adaptador_multisuperficie
(recreado, ronda de recuperación 2026-09-21). Cubre el bloqueo de sombra no
aceptable, la invalidación geométrica ampliada y la invalidación por cambio
de TMY (restaurada -- había quedado como no-op tras la reconstrucción
posterior al borrado accidental)."""
import numpy as np
import pandas as pd
import pytest

from calculos.sombras_3d import ESTADOS_SOMBRA_ACEPTABLES
from calculos.produccion_vigencia import huella_horaria
from calculos.vinculador_sombra_multisuperficie import (
    aplicar_sombra_a_superficies,
    invalidar_sombra_por_cambio_tmy,
    preservar_o_invalidar_campos_fisicos,
    resumen_estado_fisico_superficies,
)

_HORAS_ANIO = 8760


def _sup(nombre="Fachada 1", tilt=90.0, az=180.0, **extra):
    base = {"uid": 1, "nombre": nombre, "tipo": "Fachada", "tilt_deg": tilt,
            "azimuth_deg": az, "area_m2": 20.0, "activa": True}
    base.update(extra)
    return base


def _resultado_sombra(estado="calculado_completo", tmy_fingerprint="tmy-abc", **extra):
    base = {
        "p_shade": np.zeros(_HORAS_ANIO, dtype=float),
        "firma_sombra": {"geometria": {"tilt_deg": 90.0, "azimuth_deg": 180.0}, "tmy_fingerprint": tmy_fingerprint},
        "cobertura": {"horas_totales": _HORAS_ANIO},
        "advertencias": [],
        "calidad_confianza": "alta",
        "estado_sombra": estado,
    }
    base.update(extra)
    return base


def _tmy(t2m_base=20.0):
    idx = pd.date_range("2023-01-01", periods=_HORAS_ANIO, freq="h", tz="UTC")
    t2m = t2m_base + 5.0 * np.sin((idx.hour.to_numpy() - 6) / 24.0 * 2 * np.pi)
    return pd.DataFrame({"T2m": t2m}, index=idx)


# ── aplicar_sombra_a_superficies: publicación y bloqueo ──────────────────
def test_publica_p_shade_cuando_estado_aceptable():
    resultado = aplicar_sombra_a_superficies([_sup("A")], {"A": _resultado_sombra()})
    assert resultado[0]["p_shade"].shape == (_HORAS_ANIO,)
    assert resultado[0]["estado_sombra"] == "calculado_completo"


def test_rechaza_resultado_de_superficie_inexistente():
    with pytest.raises(ValueError, match="inexistentes"):
        aplicar_sombra_a_superficies([_sup("A")], {"Z": _resultado_sombra()})


@pytest.mark.parametrize("estado", ["calculo_incompleto", "error_geometrico", "resolucion_insuficiente"])
def test_estado_no_aceptable_bloquea_publicacion(estado):
    resultado = aplicar_sombra_a_superficies([_sup("A")], {"A": _resultado_sombra(estado=estado)})
    assert "p_shade" not in resultado[0]
    assert "firma_sombra" not in resultado[0]
    assert resultado[0]["estado_sombra"] == estado
    assert estado not in ESTADOS_SOMBRA_ACEPTABLES


def test_bloqueo_retira_p_shade_previo_de_un_calculo_anterior():
    sup_con_sombra_vieja = _sup("A", p_shade=np.ones(_HORAS_ANIO), firma_sombra={"vieja": True})
    resultado = aplicar_sombra_a_superficies(
        [sup_con_sombra_vieja], {"A": _resultado_sombra(estado="error_geometrico")},
    )
    assert "p_shade" not in resultado[0]
    assert "firma_sombra" not in resultado[0]


def test_superficie_sin_resultado_conserva_lo_que_ya_tenia():
    resultado = aplicar_sombra_a_superficies(
        [_sup("A", p_shade=np.ones(_HORAS_ANIO), firma_sombra={"x": 1})], {},
    )
    assert np.all(resultado[0]["p_shade"] == 1.0)


# ── invalidar_sombra_por_cambio_tmy (restaurada) ──────────────────────────
def test_tmy_distinto_invalida_sombra():
    tmy = _tmy()
    fp_real = huella_horaria(tmy.index, tmy["T2m"].to_numpy(dtype=float))
    sup = _sup("A", p_shade=np.ones(_HORAS_ANIO), firma_sombra={"tmy_fingerprint": "tmy-viejo-distinto"})
    resultado = invalidar_sombra_por_cambio_tmy([sup], tmy)
    assert "p_shade" not in resultado[0]
    assert "firma_sombra" not in resultado[0]
    assert "tmy" in resultado[0]["sombra_bloqueo_motivo"].lower()
    assert fp_real != "tmy-viejo-distinto"


def test_tmy_igual_conserva_sombra():
    tmy = _tmy()
    fp_real = huella_horaria(tmy.index, tmy["T2m"].to_numpy(dtype=float))
    sup = _sup("A", p_shade=np.ones(_HORAS_ANIO), firma_sombra={"tmy_fingerprint": fp_real})
    resultado = invalidar_sombra_por_cambio_tmy([sup], tmy)
    assert np.all(resultado[0]["p_shade"] == 1.0)


def test_superficie_sin_firma_sombra_no_falla_con_cambio_tmy():
    resultado = invalidar_sombra_por_cambio_tmy([_sup("A")], _tmy())
    assert "p_shade" not in resultado[0]


def test_invalidar_sombra_por_tmy_rechaza_tmy_invalido():
    with pytest.raises(ValueError, match="T2m"):
        invalidar_sombra_por_cambio_tmy([_sup("A")], pd.DataFrame({"x": [1, 2, 3]}))


# ── preservar_o_invalidar_campos_fisicos ──────────────────────────────────
def test_conserva_sombra_si_ninguna_entrada_cambio():
    anterior = _sup(tilt=90.0, az=180.0, p_shade=np.ones(_HORAS_ANIO), firma_sombra={"x": 1},
                     n_serie=7, n_paralelo=2, inversor_id="INV1")
    editada = _sup(tilt=90.0, az=180.0, n_serie=7, nombre="Fachada 1 (renombrada)")
    fusion = preservar_o_invalidar_campos_fisicos(anterior, editada)
    assert np.all(fusion["p_shade"] == 1.0)
    assert fusion["n_serie"] == 7
    assert fusion["inversor_id"] == "INV1"


@pytest.mark.parametrize("campo,antes,despues", [
    ("tilt_deg", 90.0, 30.0), ("azimuth_deg", 180.0, 90.0), ("area_m2", 20.0, 35.0),
    ("n_serie", 7, 10), ("malla_horizonte", "v1", "v2"), ("transparencia", 0.0, 0.3),
])
def test_cambiar_entrada_de_sombra_invalida_p_shade(campo, antes, despues):
    anterior = _sup(p_shade=np.ones(_HORAS_ANIO), firma_sombra={"x": 1},
                     n_serie=7, n_paralelo=2, inversor_id="INV1")
    anterior[campo] = antes
    editada = dict(anterior)
    editada.pop("p_shade", None)
    editada.pop("firma_sombra", None)
    editada[campo] = despues
    fusion = preservar_o_invalidar_campos_fisicos(anterior, editada)
    assert "p_shade" not in fusion
    assert "firma_sombra" not in fusion
    assert fusion["inversor_id"] == "INV1"


def test_superficie_nueva_sin_anterior_no_falla():
    editada = _sup()
    fusion = preservar_o_invalidar_campos_fisicos(None, editada)
    assert fusion == editada
    assert "p_shade" not in fusion


# ── resumen_estado_fisico_superficies ─────────────────────────────────────
def test_resumen_marca_campos_faltantes_sin_inventarlos():
    superficies = [
        _sup("Lista", p_shade=np.zeros(_HORAS_ANIO), firma_sombra={}, n_serie=7, n_paralelo=2, inversor_id="INV1"),
        _sup("Incompleta"),
        _sup("Inactiva", activa=False),
    ]
    resumen = resumen_estado_fisico_superficies(superficies)
    assert len(resumen) == 2
    listo = next(r for r in resumen if r["nombre"] == "Lista")
    incompleta = next(r for r in resumen if r["nombre"] == "Incompleta")
    assert listo["lista"] is True
    assert incompleta["lista"] is False
    assert set(incompleta["campos_faltantes"]) == {"n_serie", "n_paralelo", "inversor_id", "p_shade", "firma_sombra"}
