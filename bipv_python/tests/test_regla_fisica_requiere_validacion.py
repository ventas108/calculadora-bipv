# -*- coding: utf-8 -*-
"""Regla "fórmula física nueva = test de validación obligatorio" (2026-08-25).

Prueba la lógica de scripts/verificar_fisica_tiene_test.py -- el guard que
la CI corre en cada PR para bloquear un cambio a una fórmula/constante
física del SDM que no traiga, en el MISMO PR, al menos uno de sus tests de
validación contra una referencia real.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verificar_fisica_tiene_test as guard  # noqa: E402


def test_bloquea_si_toca_fisica_sin_tocar_ningun_test_de_validacion(monkeypatch, capsys):
    monkeypatch.setattr(guard, "_archivos_modificados",
                        lambda base, head="HEAD": ["bipv_python/calculos/modelo_iv.py"])
    codigo = _run(guard, ["--base", "origin/main"])
    assert codigo == 1
    assert "no toca ninguno de sus tests" in capsys.readouterr().out


def test_aprueba_si_toca_fisica_y_un_test_de_validacion(monkeypatch, capsys):
    monkeypatch.setattr(guard, "_archivos_modificados", lambda base, head="HEAD": [
        "bipv_python/calculos/modelo_iv.py",
        "bipv_python/tests/test_validacion_vba.py",
    ])
    codigo = _run(guard, ["--base", "origin/main"])
    assert codigo == 0
    assert "también su test de validación" in capsys.readouterr().out


def test_aprueba_si_no_toca_ninguna_formula_fisica(monkeypatch, capsys):
    monkeypatch.setattr(guard, "_archivos_modificados",
                        lambda base, head="HEAD": ["bipv_python/pages/8_💼_Presupuesto.py"])
    codigo = _run(guard, ["--base", "origin/main"])
    assert codigo == 0
    assert "No se modificó ninguna fórmula" in capsys.readouterr().out


def test_aprueba_si_toca_fisica_y_el_test_de_consistencia_cruzada(monkeypatch, capsys):
    # Cualquiera de los 3 tests de validación cuenta, no solo test_validacion_vba.py.
    monkeypatch.setattr(guard, "_archivos_modificados", lambda base, head="HEAD": [
        "bipv_python/calculos/mppt_combinado.py",
        "bipv_python/tests/test_consistencia_sdm_entre_modulos.py",
    ])
    codigo = _run(guard, ["--base", "origin/main"])
    assert codigo == 0


def test_bloquea_aunque_solo_uno_de_varios_archivos_fisicos_carezca_de_contexto(monkeypatch, capsys):
    # Varios archivos físicos tocados, cero tests -- sigue bloqueando.
    monkeypatch.setattr(guard, "_archivos_modificados", lambda base, head="HEAD": [
        "bipv_python/calculos/modelo_iv.py",
        "bipv_python/calculos/produccion.py",
        "bipv_python/datos/tecnologias_bipv.py",
    ])
    codigo = _run(guard, ["--base", "origin/main"])
    assert codigo == 1


def _run(guard_module, argv):
    old_argv = sys.argv
    sys.argv = ["verificar_fisica_tiene_test.py", *argv]
    try:
        return guard_module.main()
    finally:
        sys.argv = old_argv
