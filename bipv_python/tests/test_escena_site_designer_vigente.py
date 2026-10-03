# -*- coding: utf-8 -*-
"""Spec 05-perdidas-y-temperatura/escena-site-designer-vigente (3-oct-2026).

Parches de la auditoría Site Designer del 22-sep que quedaron en el Codespace
sin integrar (rama borrador/validacion-lasalle, c007c0ba), llevados a main:
1. Una escena de Site Designer de otra ubicación solo avisaba y se usaba igual.
2. Si se subía una escena nueva y no se volvía a pulsar «Calcular sombra», la
   sombra de la escena anterior seguía aplicada en silencio.
"""
from pathlib import Path

import numpy as np
import pytest

from calculos.sitedesigner_marsh import cargar_escena_sitedesigner
from calculos.sombras_3d import VERSION_ALGORITMO_FS_POR_SUPERFICIE
from calculos.vinculador_sombra_multisuperficie import (
    construir_y_recalcular_proyecto_fisico, invalidar_sombra_por_cambio_malla,
    invalidar_sombra_por_version_algoritmo,
)
from tests.test_flujo_fisico_multisuperficie_end_to_end import (
    _ALT_M, _LAT, _LON, _session_state_realista, _tmy,
)
from tests.test_sitedesigner_marsh import _escena

_RAIZ = Path(__file__).resolve().parents[1]
_HORAS = 8760


def _sup(malla_horizonte=None, **firma_extra):
    firma = {**({"malla_horizonte": malla_horizonte} if malla_horizonte else {}), **firma_extra}
    return {"nombre": "A", "p_shade": np.ones(_HORAS), "firma_sombra": firma}


# ── Huella de la escena ───────────────────────────────────────────────────
def test_cada_escena_tiene_su_huella():
    _, a = cargar_escena_sitedesigner(_escena(0, [{"min": [0, 0, 0], "max": [1000, 1000, 1000]}]))
    _, b = cargar_escena_sitedesigner(_escena(0, [{"min": [0, 0, 0], "max": [1000, 1000, 2000]}]))
    _, a2 = cargar_escena_sitedesigner(_escena(0, [{"min": [0, 0, 0], "max": [1000, 1000, 1000]}]))
    assert a["malla_fingerprint"].startswith("externa_marsh-")
    assert a["malla_fingerprint"] != b["malla_fingerprint"]
    assert a["malla_fingerprint"] == a2["malla_fingerprint"]
    _, c = cargar_escena_sitedesigner(_escena(15, [{"min": [0, 0, 0], "max": [1000, 1000, 1000]}]))
    assert c["malla_fingerprint"] != a["malla_fingerprint"]          # otro norte, otra sombra


# ── Invalidación por cambio de escena ─────────────────────────────────────
def test_otra_escena_cargada_invalida_la_sombra():
    r = invalidar_sombra_por_cambio_malla([_sup("externa_marsh-aaaa")], "externa_marsh-bbbb")[0]
    assert "p_shade" not in r and "firma_sombra" not in r
    assert "escena" in r["sombra_bloqueo_motivo"].lower()


@pytest.mark.parametrize("sup, actual", [
    (_sup("externa_marsh-aaaa"), "externa_marsh-aaaa"),     # la misma escena
    (_sup("externa_marsh-aaaa"), None),                     # proyecto guardado: la escena no se guarda
    (_sup("box-test-v1"), "externa_marsh-bbbb"),            # otra fuente de malla
    (_sup(None, fuente="sin_mascara"), "externa_marsh-bbbb"),
    ({"nombre": "B", "p_shade": np.ones(_HORAS)}, "externa_marsh-bbbb"),
])
def test_casos_que_conservan_la_sombra(sup, actual):
    r = invalidar_sombra_por_cambio_malla([sup], actual)[0]
    assert np.all(r["p_shade"] == 1.0)


def test_el_proyecto_fisico_rechaza_la_sombra_de_otra_escena():
    tmy = _tmy()
    ss = _session_state_realista(tmy)
    ss["superficies_bipv"][0]["firma_sombra"]["malla_horizonte"] = "externa_marsh-escenavieja"
    ss["multisup_malla_meta"] = {"malla_fingerprint": "externa_marsh-escenanueva"}
    with pytest.raises(ValueError, match="p_shade|firma_sombra"):
        construir_y_recalcular_proyecto_fisico(ss, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)


def test_misma_escena_da_el_mismo_resultado():
    tmy = _tmy()
    base = construir_y_recalcular_proyecto_fisico(_session_state_realista(tmy), tmy,
                                                  lat=_LAT, lon=_LON, alt_m=_ALT_M)
    ss = _session_state_realista(tmy)
    ss["superficies_bipv"][0]["firma_sombra"]["malla_horizonte"] = "externa_marsh-misma"
    ss["multisup_malla_meta"] = {"malla_fingerprint": "externa_marsh-misma"}
    con = construir_y_recalcular_proyecto_fisico(ss, tmy, lat=_LAT, lon=_LON, alt_m=_ALT_M)
    assert con["superficies"]["Este"]["resultados_ac"]["E_ac_anual_kWh"] == pytest.approx(
        base["superficies"]["Este"]["resultados_ac"]["E_ac_anual_kWh"])


def test_la_proteccion_del_algoritmo_viejo_sigue_aplicando():
    # La fuente de la firma sigue siendo sombras_3d aunque la escena venga de
    # Site Designer: si cambiara, una sombra v1 se colaría.
    sup = _sup("externa_marsh-aaaa", fuente="sombras_3d", proveedor="sombras_3d",
               version_algoritmo="sombras_3d.ray_casting_por_superficie.v1")
    assert "p_shade" not in invalidar_sombra_por_version_algoritmo([sup])[0]
    sup_v2 = _sup("externa_marsh-aaaa", fuente="sombras_3d", version_algoritmo=VERSION_ALGORITMO_FS_POR_SUPERFICIE)
    assert "p_shade" in invalidar_sombra_por_version_algoritmo([sup_v2])[0]


# ── Vista 3D ──────────────────────────────────────────────────────────────
def test_vista_3d_bloquea_otra_ubicacion_y_firma_con_la_huella():
    src = (_RAIZ / "pages" / "9_🗺️_Vista_3D.py").read_text(encoding="utf-8")
    assert "No se aplicó la escena Site Designer" in src
    i = src.index("No se aplicó la escena Site Designer")
    assert 'st.session_state.pop("multisup_malla_sombra", None)' in src[i - 400:i]
    assert '"malla_fingerprint", "site_designer")' in src
    assert '.get("fuente", "site_designer")),' not in src          # antes la firma solo decía «externa_marsh»


def test_bypass_documenta_el_alcance_radiativo():
    src = (_RAIZ / "calculos" / "mismatch_bypass.py").read_text(encoding="utf-8")
    assert "Alcance radiativo" in src


def test_manual_del_asistente_seccion_122():
    kb = (_RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
    i = kb.index("## 122.")
    s = kb[i:kb.find("\n## ", i + 5) if kb.find("\n## ", i + 5) > 0 else None]
    for t in ("Site Designer", "otra ubicación", "Calcular sombra", "East2", "La Salle", "provisional"):
        assert t in s, t
    assert i < kb.rindex("Calculadora BIPV — Innovación Química")
    assert "PVsyst" not in s and "pendiente" not in s
