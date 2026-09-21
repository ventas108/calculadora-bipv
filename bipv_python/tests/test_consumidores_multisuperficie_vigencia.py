"""Contrato de consumo: estado multi-superficie solo vale si esta activo."""
from __future__ import annotations

import ast
from pathlib import Path


_ROOT = Path(__file__).parents[1]
_PAGES = {
    "financiero": "7_💰_Financiero.py",
    "co2": "12_🌿_Impacto_CO2.py",
    "baterias": "11_🔋_Baterias_y_Balance.py",
    "mismatch": "5_🔀_Mismatch.py",
    "reporte": "10_📄_Reporte_PDF.py",
    "unifilar": "20_⚡_Diagrama_Unifilar.py",
    "comparador_inversores": "4b_⚖️_Comparador_Inversores.py",
}


def _source(nombre: str) -> str:
    return (_ROOT / "pages" / _PAGES[nombre]).read_text(encoding="utf-8")


def test_todos_los_consumidores_declaran_guard_multisuperficie():
    for nombre in _PAGES:
        source = _source(nombre)
        assert "multisup_activo" in source, f"{nombre} no declara multisup_activo"


def test_consumidores_de_energia_no_usan_e_ac_multisup_sin_guard():
    for nombre in ("financiero", "co2", "baterias"):
        tree = ast.parse(_source(nombre))
        nombres_guard = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and node.id.startswith("_multisup_ok")
        }
        assert nombres_guard, f"{nombre} no tiene variable de guard multi-superficie"
        assert "E_ac_anual_kWh_multisup" in _source(nombre)
        assert any(
            isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Name) and child.id.startswith("_multisup_ok")
                for child in ast.walk(node.test)
            )
            for node in ast.walk(tree)
        ), f"{nombre} no condiciona el consumo a multisup_activo"


def test_consumidores_de_energia_conservan_fallback_base():
    for nombre in ("financiero", "co2", "baterias"):
        source = _source(nombre)
        assert "_e_ac_base" in source
        assert "else:" in source
        assert "e_ac" in source


def test_consumidores_no_restauran_por_su_cuenta():
    for nombre in _PAGES:
        source = _source(nombre)
        assert "restaurar_multisuperficie" not in source
        assert "cargar_proyecto" not in source
