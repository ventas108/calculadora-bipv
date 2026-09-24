"""Editor de superficies de Vista 3D: los campos no deben recrearse al editar.

En Streamlit 1.36 la identidad de un widget incluye su ``value=``/``index=``.
El editor pasaba como valor inicial el dato guardado de la superficie, que
cambia justo después de editarlo: en el rerun siguiente el campo era «otro»,
el navegador lo volvía a crear y el usuario veía que el azimuth tardaba en
actualizarse o volvía al valor anterior (reportado en producción 24-sep-2026).
"""
import ast
from pathlib import Path

_PAGINA = Path(__file__).resolve().parents[1] / "pages" / "9_🗺️_Vista_3D.py"
_PREFIJOS = ("snom_", "stipo_", "stilt_", "saz_", "sarea_", "sact_", "smont_")


def _llamadas_editor():
    arbol = ast.parse(_PAGINA.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        clave = next((kw for kw in nodo.keywords if kw.arg == "key"), None)
        if clave is not None and any(p in ast.unparse(clave.value) for p in _PREFIJOS):
            yield nodo


def test_los_siete_campos_del_editor_existen():
    claves = {ast.unparse(next(kw for kw in n.keywords if kw.arg == "key").value)
              for n in _llamadas_editor()}
    for prefijo in _PREFIJOS:
        assert any(prefijo in c for c in claves), prefijo


def test_campos_del_editor_sin_valor_inicial_cambiante():
    culpables = [
        f"línea {n.lineno}: {kw.arg}="
        for n in _llamadas_editor() for kw in n.keywords if kw.arg in ("value", "index")
    ]
    assert not culpables, "; ".join(culpables)


def test_editor_sincroniza_cambios_externos():
    src = _PAGINA.read_text(encoding="utf-8")
    assert "def _valor_campo_superficie(" in src
    assert src.count("_valor_campo_superficie(") >= 8  # definición + 7 campos
