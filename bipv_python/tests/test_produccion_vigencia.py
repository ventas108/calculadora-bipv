# -*- coding: utf-8 -*-
"""
Fase 1 del CodeSpec de Producción (.openspec/proposals/produccion-codespec) —
pruebas TDD para las piezas puras de vigencia:

1. produccion_run_signature_v1 — normalización canónica, serialización,
   huellas horarias y digest final (calculos.produccion_vigencia).
2. factor_mismatch_sin_soiling — fórmula exacta de soiling único
   (calculos.mismatch).
3. bypass_run_signature_v1 — firma de los argumentos efectivos de
   simular_bypass_horario() (calculos.produccion_vigencia).
4. Persistencia con firma — calculos.persistencia_resultados rechaza
   legacy sin firma y restauraciones sin coincidencia exacta.

Estas pruebas se escribieron ANTES de calculos/produccion_vigencia.py: la
primera corrida debe fallar por ImportError/AttributeError (rojo), no por
aserciones -- ver el informe de esta ronda para la evidencia exacta.
"""
import os

import numpy as np
import pandas as pd
import pytest

IDX_8760 = pd.date_range("2001-01-01", periods=8760, freq="h", tz="UTC")
IDX_5 = pd.date_range("2001-01-01", periods=5, freq="h", tz="UTC")


# ══════════════════════════════════════════════════════════════════════════
# 1) calcular_factor_mismatch_sin_soiling (calculos.mismatch)
# ══════════════════════════════════════════════════════════════════════════

def test_factor_mismatch_sin_soiling_formula_exacta():
    from calculos.mismatch import calcular_factor_mismatch_sin_soiling

    # (1 - 0.10) * (1 - 5/100) = 0.9 * 0.95 = 0.855
    resultado = calcular_factor_mismatch_sin_soiling(
        factor_sombra_anual=0.10, factor_mismatch_or_pct=5.0,
    )
    assert resultado == pytest.approx(0.855, abs=1e-6)


def test_factor_mismatch_sin_soiling_entradas_ausentes_equivalen_a_cero():
    from calculos.mismatch import calcular_factor_mismatch_sin_soiling

    assert calcular_factor_mismatch_sin_soiling(None, None) == pytest.approx(1.0)
    assert calcular_factor_mismatch_sin_soiling(None, 10.0) == pytest.approx(0.9)
    assert calcular_factor_mismatch_sin_soiling(0.2, None) == pytest.approx(0.8)


def test_factor_mismatch_sin_soiling_limitado_a_0_1():
    from calculos.mismatch import calcular_factor_mismatch_sin_soiling

    # Sombra > 100% (dato corrupto) no debe dar factor negativo.
    assert calcular_factor_mismatch_sin_soiling(1.5, 0.0) == pytest.approx(0.0)
    # Mismatch negativo (dato corrupto) no debe dar factor > 1.
    assert calcular_factor_mismatch_sin_soiling(0.0, -50.0) <= 1.0
    assert calcular_factor_mismatch_sin_soiling(0.0, -50.0) >= 0.0


# ══════════════════════════════════════════════════════════════════════════
# 2) Normalización canónica y serialización (calculos.produccion_vigencia)
# ══════════════════════════════════════════════════════════════════════════

def test_fingerprint_mapping_mismo_dict_mismo_digest():
    from calculos.produccion_vigencia import fingerprint_mapping

    panel = {"nombre": "ASP-ST1-T40", "Pmax_stc": 63.0, "NOCT": 45.0, "N_s": 141}
    d1 = fingerprint_mapping(panel)
    d2 = fingerprint_mapping(dict(panel))  # copia distinta, mismo contenido
    assert d1 == d2
    assert isinstance(d1, str) and len(d1) == 64  # hex SHA-256


def test_fingerprint_mapping_orden_de_claves_no_importa():
    from calculos.produccion_vigencia import fingerprint_mapping

    a = {"z": 1, "a": 2.5, "m": "x"}
    b = {"a": 2.5, "m": "x", "z": 1}
    assert fingerprint_mapping(a) == fingerprint_mapping(b)


def test_fingerprint_mapping_cambio_de_valor_cambia_digest():
    from calculos.produccion_vigencia import fingerprint_mapping

    base = {"Pmax_stc": 63.0, "NOCT": 45.0}
    distinto = {"Pmax_stc": 63.0, "NOCT": 46.0}
    assert fingerprint_mapping(base) != fingerprint_mapping(distinto)


def test_fingerprint_mapping_none_retorna_none():
    from calculos.produccion_vigencia import fingerprint_mapping
    assert fingerprint_mapping(None) is None


def test_fingerprint_mapping_rechaza_nan_e_infinito():
    from calculos.produccion_vigencia import fingerprint_mapping

    with pytest.raises(ValueError):
        fingerprint_mapping({"x": float("nan")})
    with pytest.raises(ValueError):
        fingerprint_mapping({"x": float("inf")})


def test_fingerprint_mapping_rechaza_tipo_no_soportado():
    from calculos.produccion_vigencia import fingerprint_mapping

    class NoSoportado:
        pass

    with pytest.raises(TypeError):
        fingerprint_mapping({"x": NoSoportado()})


def test_fingerprint_mapping_numpy_scalars_coherente_con_python_nativo():
    """Los catálogos Excel entregan a veces np.float64/np.int64 -- deben
    fingerprintear IGUAL que el equivalente Python nativo (mismo valor
    físico, misma huella), no un tipo distinto que rompa la comparación."""
    from calculos.produccion_vigencia import fingerprint_mapping

    nativo = {"Pmax_stc": 63.0, "N_s": 141}
    numpy_vals = {"Pmax_stc": np.float64(63.0), "N_s": np.int64(141)}
    assert fingerprint_mapping(nativo) == fingerprint_mapping(numpy_vals)


# ══════════════════════════════════════════════════════════════════════════
# 3) Huellas horarias
# ══════════════════════════════════════════════════════════════════════════

def test_huella_horaria_mismos_datos_mismo_digest():
    from calculos.produccion_vigencia import huella_horaria

    valores = np.linspace(0, 900, len(IDX_8760))
    h1 = huella_horaria(IDX_8760, valores)
    h2 = huella_horaria(IDX_8760, valores.copy())
    assert h1 == h2
    assert len(h1) == 64


def test_huella_horaria_cambia_un_solo_valor_cambia_el_digest():
    from calculos.produccion_vigencia import huella_horaria

    valores = np.linspace(0, 900, len(IDX_8760))
    h1 = huella_horaria(IDX_8760, valores)
    valores2 = valores.copy()
    valores2[4000] += 0.0001
    h2 = huella_horaria(IDX_8760, valores2)
    assert h1 != h2


def test_huella_horaria_distinta_zona_horaria_en_el_objeto_cambia_el_digest():
    """El diseño firma la cadena de zona horaria TAL COMO viene en el
    índice (además de los valores ya convertidos a UTC) -- dos índices con
    los MISMOS instantes físicos pero zona horaria distinta en el objeto
    (p.ej. "UTC" vs "America/Bogota") deben producir digests DISTINTOS: la
    zona es parte explícita de lo firmado, no se descarta tras convertir."""
    from calculos.produccion_vigencia import huella_horaria

    idx_utc = pd.date_range("2001-01-01", periods=5, freq="h", tz="UTC")
    idx_bogota = idx_utc.tz_convert("America/Bogota")
    valores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert huella_horaria(idx_utc, valores) != huella_horaria(idx_bogota, valores)


def test_huella_horaria_mismo_tz_mismos_instantes_mismo_digest():
    """Control positivo del test anterior: SIN cambiar la zona, la misma
    serie produce el mismo digest de forma reproducible."""
    from calculos.produccion_vigencia import huella_horaria

    idx_utc = pd.date_range("2001-01-01", periods=5, freq="h", tz="UTC")
    valores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert huella_horaria(idx_utc, valores) == huella_horaria(idx_utc, valores.copy())


def test_huella_horaria_indice_naive_usa_cadena_vacia_de_zona():
    from calculos.produccion_vigencia import huella_horaria

    idx_naive = pd.date_range("2001-01-01", periods=5, freq="h")
    valores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    # No debe lanzar, y debe ser determinista.
    h1 = huella_horaria(idx_naive, valores)
    h2 = huella_horaria(idx_naive, valores.copy())
    assert h1 == h2


def test_huella_horaria_rechaza_valores_no_finitos():
    from calculos.produccion_vigencia import huella_horaria

    valores = np.array([1.0, 2.0, float("nan"), 4.0, 5.0])
    with pytest.raises(ValueError):
        huella_horaria(IDX_5, valores)

    valores_inf = np.array([1.0, 2.0, float("inf"), 4.0, 5.0])
    with pytest.raises(ValueError):
        huella_horaria(IDX_5, valores_inf)


def test_huella_horaria_rechaza_longitud_distinta_indice_valores():
    from calculos.produccion_vigencia import huella_horaria

    valores = np.array([1.0, 2.0, 3.0])  # longitud 3 vs índice de longitud 5
    with pytest.raises(ValueError):
        huella_horaria(IDX_5, valores)


def test_huella_horaria_rechaza_indice_con_timestamps_duplicados():
    from calculos.produccion_vigencia import huella_horaria

    idx_dup = pd.DatetimeIndex(
        ["2001-01-01 00:00", "2001-01-01 00:00", "2001-01-01 02:00"], tz="UTC"
    )
    valores = np.array([1.0, 2.0, 3.0])
    with pytest.raises(ValueError):
        huella_horaria(idx_dup, valores)


def test_huella_horaria_opcional_none_retorna_none():
    from calculos.produccion_vigencia import huella_horaria_opcional
    assert huella_horaria_opcional(IDX_5, None) is None


# ══════════════════════════════════════════════════════════════════════════
# 4) produccion_run_signature_v1 — determinismo, sensibilidad y digest final
# ══════════════════════════════════════════════════════════════════════════

def _tmy_poa_sinteticos():
    poa = np.clip(np.sin(np.linspace(0, 8760 / 24 * 2 * np.pi, 8760)) * 500 + 400, 0, None)
    t2m = 20.0 + 5.0 * np.sin(np.linspace(0, 8760 / 24 * 2 * np.pi, 8760))
    return poa, t2m


def _kwargs_firma_base(**overrides) -> dict:
    poa, t2m = _tmy_poa_sinteticos()
    base = dict(
        panel={"nombre": "ASP-ST1-T40", "Pmax_stc": 63.0, "NOCT": 45.0},
        panel_nombre="ASP-ST1-T40",
        inversor={"modelo": "MID15KTL3-X", "P_ac_nom_W": 15000},
        inversor_nombre="MID15KTL3-X",
        N_paneles=64,
        N_serie=8,
        N_strings_tracker=2,
        n_inversores=1,
        P_dc_stc_kW=4.032,
        eta_inversor=0.975,
        P_ac_nom_W_total=15000.0,
        NOCT=45.0,
        k_bipv=1.3,
        produccion_usar_iv=False,
        source_mode="sdm_pvsyst",
        tmy_index=IDX_8760,
        tmy_T2m=t2m,
        poa_source="poa_sin_termico_df",
        poa_index=IDX_8760,
        poa_global=poa,
        factor_mismatch_aplicado=0.92,
        factor_espectral=None,
        pct_mismatch_fab=1.0,
        pct_cableado_dc=1.5,
        pct_cableado_ac=0.0,
        perdida_ohmica_unifilar=None,
    )
    base.update(overrides)
    return base


def test_produccion_run_signature_mismos_datos_mismo_digest():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    kwargs = _kwargs_firma_base()
    d1 = calcular_produccion_run_signature_v1(**kwargs)
    d2 = calcular_produccion_run_signature_v1(**_kwargs_firma_base())
    assert d1 == d2
    assert isinstance(d1, str) and len(d1) == 64


@pytest.mark.parametrize("campo,valor_nuevo", [
    ("panel_nombre", "OTRO-PANEL"),
    ("inversor_nombre", "OTRO-INVERSOR"),
    ("N_paneles", 65),
    ("N_serie", 9),
    ("eta_inversor", 0.96),
    ("produccion_usar_iv", True),
    ("source_mode", "motor_iv"),
    ("poa_source", "poa_df"),
    ("factor_mismatch_aplicado", 0.80),
    ("NOCT", 50.0),
    ("k_bipv", 1.0),
    ("pct_mismatch_fab", 2.0),
    ("pct_cableado_dc", 3.0),
    ("pct_cableado_ac", 1.0),
])
def test_produccion_run_signature_cambia_con_cada_campo(campo, valor_nuevo):
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    base = calcular_produccion_run_signature_v1(**_kwargs_firma_base())
    modificado = calcular_produccion_run_signature_v1(**_kwargs_firma_base(**{campo: valor_nuevo}))
    assert base != modificado, f"Cambiar '{campo}' debió cambiar la firma"


def test_produccion_run_signature_cambia_con_panel_distinto():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    base = calcular_produccion_run_signature_v1(**_kwargs_firma_base())
    otro_panel = calcular_produccion_run_signature_v1(
        **_kwargs_firma_base(panel={"nombre": "ASP-ST1-T40", "Pmax_stc": 70.0, "NOCT": 45.0})
    )
    assert base != otro_panel


def test_produccion_run_signature_cambia_con_poa_horaria_distinta():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    kwargs = _kwargs_firma_base()
    base = calcular_produccion_run_signature_v1(**kwargs)
    poa_modificada = kwargs["poa_global"].copy()
    poa_modificada[100] += 50.0
    modificado = calcular_produccion_run_signature_v1(**{**kwargs, "poa_global": poa_modificada})
    assert base != modificado


def test_produccion_run_signature_cambia_con_tmy_distinto():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    kwargs = _kwargs_firma_base()
    base = calcular_produccion_run_signature_v1(**kwargs)
    t2m_modificado = kwargs["tmy_T2m"].copy()
    t2m_modificado[200] += 1.0
    modificado = calcular_produccion_run_signature_v1(**{**kwargs, "tmy_T2m": t2m_modificado})
    assert base != modificado


def test_produccion_run_signature_source_mode_invalido_rechaza():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    with pytest.raises(ValueError):
        calcular_produccion_run_signature_v1(**_kwargs_firma_base(source_mode="otro_modo"))


def test_produccion_run_signature_poa_source_invalido_rechaza():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    with pytest.raises(ValueError):
        calcular_produccion_run_signature_v1(**_kwargs_firma_base(poa_source="poa_efectiva_df"))


def test_produccion_run_signature_ausencias_dan_null_no_defaults_inventados():
    """N_paneles/N_serie/etc ausentes (None) deben producir un digest
    DISTINTO al de un valor concreto -- nunca se infiere un default."""
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    con_valor = calcular_produccion_run_signature_v1(**_kwargs_firma_base(N_strings_tracker=2))
    sin_valor = calcular_produccion_run_signature_v1(**_kwargs_firma_base(N_strings_tracker=None))
    assert con_valor != sin_valor


def test_produccion_run_signature_perdida_ohmica_afecta_la_firma():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    sin_ohmica = calcular_produccion_run_signature_v1(**_kwargs_firma_base())
    con_ohmica = calcular_produccion_run_signature_v1(
        **_kwargs_firma_base(perdida_ohmica_unifilar={"resistencia_dc_ohm": 0.05})
    )
    assert sin_ohmica != con_ohmica


def test_produccion_run_signature_factor_espectral_afecta_la_firma():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    kwargs = _kwargs_firma_base()
    sin_espectral = calcular_produccion_run_signature_v1(**kwargs)
    espectral = np.full(len(IDX_8760), 0.98)
    con_espectral = calcular_produccion_run_signature_v1(**{**kwargs, "factor_espectral": espectral})
    assert sin_espectral != con_espectral


def test_produccion_run_signature_rechaza_nan_en_poa():
    from calculos.produccion_vigencia import calcular_produccion_run_signature_v1

    kwargs = _kwargs_firma_base()
    poa_nan = kwargs["poa_global"].copy()
    poa_nan[50] = float("nan")
    with pytest.raises(ValueError):
        calcular_produccion_run_signature_v1(**{**kwargs, "poa_global": poa_nan})


def test_produccion_run_signature_proceso_distinto_mismo_digest():
    """Réplica de 'procesos distintos' vía subprocess con un intérprete
    fresco -- confirma reproducibilidad fuera de la caché de módulos de
    este proceso de pruebas."""
    import subprocess
    import sys

    codigo = (
        "import numpy as np, pandas as pd, sys, os; "
        "sys.path.insert(0, os.getcwd()); "
        "from calculos.produccion_vigencia import calcular_produccion_run_signature_v1; "
        "idx = pd.date_range('2001-01-01', periods=5, freq='h', tz='UTC'); "
        "print(calcular_produccion_run_signature_v1("
        "panel={'a':1.0}, panel_nombre='P', inversor={'b':2.0}, inversor_nombre='I', "
        "N_paneles=10, N_serie=5, N_strings_tracker=1, n_inversores=1, "
        "P_dc_stc_kW=3.0, eta_inversor=0.97, P_ac_nom_W_total=3000.0, "
        "NOCT=45.0, k_bipv=1.3, produccion_usar_iv=False, source_mode='lineal', "
        "tmy_index=idx, tmy_T2m=np.array([1.0,2.0,3.0,4.0,5.0]), "
        "poa_source='poa_df', poa_index=idx, poa_global=np.array([100.0,200.0,300.0,400.0,500.0]), "
        "factor_mismatch_aplicado=0.9))"
    )
    root = os.path.join(os.path.dirname(__file__), "..")
    r1 = subprocess.run([sys.executable, "-c", codigo], cwd=root, capture_output=True, text=True, timeout=60)
    r2 = subprocess.run([sys.executable, "-c", codigo], cwd=root, capture_output=True, text=True, timeout=60)
    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr
    assert r1.stdout.strip() == r2.stdout.strip()
    assert len(r1.stdout.strip()) == 64


# ══════════════════════════════════════════════════════════════════════════
# 5) bypass_run_signature_v1
# ══════════════════════════════════════════════════════════════════════════

def _kwargs_firma_bypass(**overrides) -> dict:
    idx = IDX_5
    base = dict(
        panel={"nombre": "ASP-ST1-T40", "Pmax_stc": 63.0, "NOCT": 45.0},
        N_series=8,
        N_parallel=4,
        total_modules=32,
        tmy_index=idx,
        G_eff=np.array([100.0, 300.0, 500.0, 700.0, 200.0]),
        T_amb=np.array([20.0, 22.0, 25.0, 27.0, 21.0]),
        p_shade_final=np.array([0.0, 0.1, 0.3, 0.2, 0.0]),
        NOCT=45.0,
        k_bipv=1.3,
        umbral_shade=0.05,
    )
    base.update(overrides)
    return base


def test_bypass_run_signature_mismos_datos_mismo_digest():
    from calculos.produccion_vigencia import calcular_bypass_run_signature_v1

    d1 = calcular_bypass_run_signature_v1(**_kwargs_firma_bypass())
    d2 = calcular_bypass_run_signature_v1(**_kwargs_firma_bypass())
    assert d1 == d2
    assert len(d1) == 64


@pytest.mark.parametrize("campo,valor_nuevo", [
    ("N_series", 9),
    ("N_parallel", 5),
    ("total_modules", 40),
    ("NOCT", 50.0),
    ("k_bipv", 1.0),
    ("umbral_shade", 0.10),
])
def test_bypass_run_signature_cambia_con_cada_campo(campo, valor_nuevo):
    from calculos.produccion_vigencia import calcular_bypass_run_signature_v1

    base = calcular_bypass_run_signature_v1(**_kwargs_firma_bypass())
    modificado = calcular_bypass_run_signature_v1(**_kwargs_firma_bypass(**{campo: valor_nuevo}))
    assert base != modificado


def test_bypass_run_signature_cambia_con_panel_distinto():
    from calculos.produccion_vigencia import calcular_bypass_run_signature_v1

    base = calcular_bypass_run_signature_v1(**_kwargs_firma_bypass())
    otro = calcular_bypass_run_signature_v1(
        **_kwargs_firma_bypass(panel={"nombre": "OTRO", "Pmax_stc": 70.0, "NOCT": 45.0})
    )
    assert base != otro


def test_bypass_run_signature_cambia_con_g_eff_distinto():
    from calculos.produccion_vigencia import calcular_bypass_run_signature_v1

    kwargs = _kwargs_firma_bypass()
    base = calcular_bypass_run_signature_v1(**kwargs)
    g_eff2 = kwargs["G_eff"].copy()
    g_eff2[2] += 10.0
    modificado = calcular_bypass_run_signature_v1(**{**kwargs, "G_eff": g_eff2})
    assert base != modificado


def test_bypass_run_signature_cambia_con_t_amb_distinto():
    from calculos.produccion_vigencia import calcular_bypass_run_signature_v1

    kwargs = _kwargs_firma_bypass()
    base = calcular_bypass_run_signature_v1(**kwargs)
    t_amb2 = kwargs["T_amb"].copy()
    t_amb2[1] += 1.0
    modificado = calcular_bypass_run_signature_v1(**{**kwargs, "T_amb": t_amb2})
    assert base != modificado


def test_bypass_run_signature_cambia_con_p_shade_final_distinto():
    """p_shade final captura fachada, inversión, modo, agregación y
    horizonte en un solo array -- cualquier cambio en esas fuentes cambia
    este array y por lo tanto la firma, sin duplicar metadata causal."""
    from calculos.produccion_vigencia import calcular_bypass_run_signature_v1

    kwargs = _kwargs_firma_bypass()
    base = calcular_bypass_run_signature_v1(**kwargs)
    p_shade2 = kwargs["p_shade_final"].copy()
    p_shade2[3] = 0.9  # p.ej. horizonte ahora también bloquea esa hora
    modificado = calcular_bypass_run_signature_v1(**{**kwargs, "p_shade_final": p_shade2})
    assert base != modificado


def test_bypass_run_signature_no_incluye_factor_mismatch_sin_soiling():
    """El contrato de bypass_run_signature_v1 (spec.yaml bypass_signature.
    includes) NO tiene ningún campo de factor_mismatch -- bypass nunca debe
    mezclar factor_mismatch_sin_soiling dentro de su G_eff/firma; eso
    pertenece a la corrida BASE de Producción."""
    import inspect
    from calculos.produccion_vigencia import calcular_bypass_run_signature_v1

    parametros = set(inspect.signature(calcular_bypass_run_signature_v1).parameters)
    assert not any("mismatch" in p.lower() for p in parametros), parametros


# ══════════════════════════════════════════════════════════════════════════
# 6) determinar_source_mode (calculos.produccion)
# ══════════════════════════════════════════════════════════════════════════

def test_determinar_source_mode_cdte_es_jrc_huld():
    from calculos.produccion import determinar_source_mode

    panel_cdte = {"tecnologia": "CdTe"}
    assert determinar_source_mode(panel_cdte, produccion_modo_iv=False) == "jrc_huld"


def test_determinar_source_mode_iv_activo_es_motor_iv_incluso_para_cdte():
    from calculos.produccion import determinar_source_mode

    panel_cdte = {"tecnologia": "CdTe"}
    assert determinar_source_mode(panel_cdte, produccion_modo_iv=True) == "motor_iv"


def test_determinar_source_mode_sdm_completo_es_sdm_pvsyst():
    from calculos.produccion import determinar_source_mode

    panel_sdm = {
        "tecnologia": "Silicio cristalino",
        "I_L_ref": 5.0, "I_o_ref": 1e-10, "R_s": 0.3, "R_sh_ref": 200.0, "a_ref": 1.8,
    }
    assert determinar_source_mode(panel_sdm, produccion_modo_iv=False) == "sdm_pvsyst"


def test_determinar_source_mode_sin_sdm_completo_es_lineal():
    from calculos.produccion import determinar_source_mode

    panel_incompleto = {"tecnologia": "Silicio cristalino", "Pmax_stc": 60.0}
    assert determinar_source_mode(panel_incompleto, produccion_modo_iv=False) == "lineal"


# ══════════════════════════════════════════════════════════════════════════
# 7) Persistencia con verificación de integridad (calculos.persistencia_
#    resultados) -- objetivo 5. tmp_path/monkeypatch aíslan el directorio --
#    nunca tocan datos reales.
#
#    Diseño (CodeSpecs/06-analisis-financiero/diseno.md): Financiero y
#    Presupuesto restauran en una pestaña que NUNCA tuvo tmy_df/panel/POA en
#    session_state, así que no pueden reconstruir produccion_run_signature_v1
#    desde cero para compararla contra la persistida (a diferencia de
#    Producción, que sí revalida así su propio res_produccion). En su lugar,
#    guardar_resultados_produccion() persiste TAMBIÉN el payload canónico
#    (pre-hash) que produjo la firma, y restaurar_resultados_produccion()
#    recalcula su SHA-256 con calculos.produccion_vigencia.firma_desde_
#    payload() exigiendo que coincida EXACTAMENTE con la firma persistida --
#    ni payload ausente (legacy) ni alterado restauran.
# ══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def _pr_aislado(tmp_path, monkeypatch):
    import calculos.persistencia_resultados as pr
    monkeypatch.setattr(pr, "DIR_PERSISTENCIA", str(tmp_path))
    return pr


_SESION_GUARDAR_BASE = {
    "E_ac_anual_kWh": 12345.6, "E_dc_anual_kWh": 13000.0,
    "PR_sistema": 0.81, "Y_f_kWh_kWp": 1500.0,
    "P_stc_kW_sistema": 10.0, "N_paneles_final": 20,
    "panel_nombre_final": "ASP-ST1-T40", "eta_inversor": 0.96,
    "ciudad": "Bogotá", "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
}


def _sesion_con_payload_real(**overrides_firma) -> tuple[dict, str, dict]:
    """Sesión de Producción con firma + payload canónico REALES y
    mutuamente consistentes (el mismo par que pages/6_📊_Produccion.py deja
    en session_state antes de llamar guardar_resultados_produccion())."""
    from calculos.produccion_vigencia import (
        construir_payload_produccion_run_signature_v1, firma_desde_payload,
    )
    import calculos.persistencia_resultados as pr

    payload = construir_payload_produccion_run_signature_v1(**_kwargs_firma_base(**overrides_firma))
    firma = firma_desde_payload(payload)
    sesion = dict(_SESION_GUARDAR_BASE, produccion_run_signature_v1=firma)
    sesion[pr.CLAVE_PAYLOAD_FIRMA] = payload
    return sesion, firma, payload


def test_guardar_resultados_produccion_persiste_la_firma(_pr_aislado):
    pr = _pr_aislado
    usuario = "vigencia-test-1@example.com"
    sesion = dict(_SESION_GUARDAR_BASE, produccion_run_signature_v1="a" * 64)

    assert pr.guardar_resultados_produccion(sesion, usuario) is True

    ruta = pr._ruta_resultados(usuario)
    with open(ruta, "r", encoding="utf-8") as f:
        import json
        data = json.load(f)
    assert data["resultados"].get("produccion_run_signature_v1") == "a" * 64


def test_guardar_resultados_produccion_persiste_el_payload_canonico(_pr_aislado):
    pr = _pr_aislado
    usuario = "vigencia-test-payload@example.com"
    sesion, _firma, payload = _sesion_con_payload_real()

    assert pr.guardar_resultados_produccion(sesion, usuario) is True

    ruta = pr._ruta_resultados(usuario)
    with open(ruta, "r", encoding="utf-8") as f:
        import json
        data = json.load(f)
    assert data.get("payload_firma") == payload


def test_restaurar_rechaza_archivo_legacy_sin_firma_ni_payload(_pr_aislado):
    """Un archivo guardado ANTES de esta ronda (sin produccion_run_signature_v1
    ni payload canónico) debe rechazarse -- nunca se asume que sigue vigente."""
    pr = _pr_aislado
    usuario = "vigencia-test-2@example.com"
    sesion_legacy = dict(_SESION_GUARDAR_BASE)  # SIN firma NI payload
    assert pr.guardar_resultados_produccion(sesion_legacy, usuario) is True

    estado_nuevo = {
        "auth_email": usuario, "ciudad": "Bogotá",
        "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
    }
    assert pr.restaurar_resultados_produccion(estado_nuevo, usuario) is False
    assert "E_ac_anual_kWh" not in estado_nuevo


def test_restaurar_rechaza_si_falta_payload_persistido(_pr_aislado):
    """La firma SÍ quedó persistida, pero sin el payload canónico no hay
    forma de re-verificar su SHA-256 -- se rechaza igual que legacy, nunca
    se confía en la firma sola (caso: guardado con una ronda anterior a
    esta, que ya escribía la firma pero no el payload)."""
    pr = _pr_aislado
    usuario = "vigencia-test-3@example.com"
    sesion_sin_payload = dict(_SESION_GUARDAR_BASE, produccion_run_signature_v1="c" * 64)
    assert pr.guardar_resultados_produccion(sesion_sin_payload, usuario) is True

    estado_nuevo = {
        "auth_email": usuario, "ciudad": "Bogotá",
        "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
    }
    assert pr.restaurar_resultados_produccion(estado_nuevo, usuario) is False
    assert "E_ac_anual_kWh" not in estado_nuevo


def test_restaurar_rechaza_si_payload_alterado_no_coincide_con_la_firma(_pr_aislado):
    """Payload persistido pero MODIFICADO respecto al que produjo la firma
    (archivo editado a mano, corrupción parcial, etc.) -- el SHA-256
    recalculado no coincide, no se restaura."""
    pr = _pr_aislado
    usuario = "vigencia-test-4@example.com"
    sesion, _firma, _payload = _sesion_con_payload_real()
    assert pr.guardar_resultados_produccion(sesion, usuario) is True

    import json
    ruta = pr._ruta_resultados(usuario)
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["payload_firma"]["N_paneles"] = (data["payload_firma"].get("N_paneles") or 0) + 1
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f)

    estado_nuevo = {
        "auth_email": usuario, "ciudad": "Bogotá",
        "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
    }
    assert pr.restaurar_resultados_produccion(estado_nuevo, usuario) is False
    assert "E_ac_anual_kWh" not in estado_nuevo


def test_restaurar_rechaza_si_payload_persistido_tiene_tipo_no_soportado(_pr_aislado):
    """Payload corrupto con un tipo que firma_desde_payload() no puede
    normalizar (p.ej. edición manual del JSON) -- la excepción se trata
    como "no verifica", nunca como crash ni como "restaurar igual"."""
    pr = _pr_aislado
    usuario = "vigencia-test-tipo-invalido@example.com"
    sesion, _firma, _payload = _sesion_con_payload_real()
    assert pr.guardar_resultados_produccion(sesion, usuario) is True

    import json
    ruta = pr._ruta_resultados(usuario)
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["payload_firma"]["N_paneles"] = {"objeto": "no soportado en la firma"}
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f)

    estado_nuevo = {
        "auth_email": usuario, "ciudad": "Bogotá",
        "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
    }
    assert pr.restaurar_resultados_produccion(estado_nuevo, usuario) is False
    assert "E_ac_anual_kWh" not in estado_nuevo


def test_restaurar_acepta_si_payload_persistido_verifica_la_firma(_pr_aislado):
    """Caso feliz: pestaña NUEVA de Financiero/Presupuesto, sin tmy_df/panel
    en sesión -- restaurar NO depende de que el llamador reconstruya la
    firma, solo del payload canónico ya persistido junto a ella."""
    pr = _pr_aislado
    usuario = "vigencia-test-5@example.com"
    sesion, _firma, _payload = _sesion_con_payload_real()
    assert pr.guardar_resultados_produccion(sesion, usuario) is True

    estado_nuevo = {
        "auth_email": usuario, "ciudad": "Bogotá",
        "lat_proyecto": 4.7110, "lon_proyecto": -74.0721,
        # SIN produccion_run_signature_v1 ni tmy_df/panel -- pestaña nueva real.
    }
    assert pr.restaurar_resultados_produccion(estado_nuevo, usuario) is True
    assert estado_nuevo["E_ac_anual_kWh"] == 12345.6
    assert estado_nuevo["E_dc_anual_kWh"] == 13000.0


def test_restaurar_bloquea_por_huella_de_ciudad_antes_de_evaluar_el_payload(_pr_aislado):
    """La huella de ciudad/coordenadas se evalúa ANTES del payload -- otra
    ciudad u otras coordenadas bloquean aunque el payload sea perfectamente
    válido (datos de otro proyecto, no una corrida desactualizada)."""
    pr = _pr_aislado
    usuario = "vigencia-test-6@example.com"
    sesion, _firma, _payload = _sesion_con_payload_real()
    assert pr.guardar_resultados_produccion(sesion, usuario) is True

    estado_otra_ciudad = {"auth_email": usuario, "ciudad": "Medellín"}
    assert pr.restaurar_resultados_produccion(estado_otra_ciudad, usuario) is False
    assert "E_ac_anual_kWh" not in estado_otra_ciudad

    estado_otras_coord = {
        "auth_email": usuario, "ciudad": "Bogotá",
        "lat_proyecto": 4.9, "lon_proyecto": -74.0721,
    }
    assert pr.restaurar_resultados_produccion(estado_otras_coord, usuario) is False
    assert "E_ac_anual_kWh" not in estado_otras_coord


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
