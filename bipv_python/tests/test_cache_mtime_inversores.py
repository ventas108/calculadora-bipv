"""#205 — Regresión: la invalidación por mtime del catálogo de inversores.

st.cache_data EXCLUYE del hashing los parámetros cuyo nombre empieza con "_".
Si alguien renombra el parámetro de vuelta a "_mtime", la caché deja de
invalidarse al editar el Excel y el bug vuelve en silencio. Test estructural
vía AST (streamlit no está instalado en el entorno de pruebas).
"""
import ast
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent
_SRC = (_BASE / "datos" / "catalogo_inversores_excel.py").read_text()
_TREE = ast.parse(_SRC)
_FNS = {n.name: n for n in _TREE.body if isinstance(n, ast.FunctionDef)}


def _es_cacheada(fn):
    return any("cache_data" in ast.unparse(d) for d in fn.decorator_list)


def test_loader_cacheado_recibe_mtime_hasheable():
    fn = _FNS["_cargar_catalogo_inversores_cached"]
    assert _es_cacheada(fn)
    args = [a.arg for a in fn.args.args]
    assert args and args[0] == "mtime", (
        f"El parámetro debe llamarse 'mtime' sin guion bajo inicial "
        f"(st.cache_data no hashea args '_x'); encontrado: {args}")


def test_diagnostico_cacheado_recibe_mtime_hasheable():
    fn = _FNS["diagnostico_catalogo_inversores"]
    assert _es_cacheada(fn)
    args = [a.arg for a in fn.args.args]
    assert args and args[0] == "mtime" and not args[0].startswith("_")


def test_wrapper_publico_inyecta_mtime():
    fn = _FNS["cargar_catalogo_inversores"]
    assert not fn.args.args, "la API pública debe seguir sin argumentos"
    assert "_cargar_catalogo_inversores_cached(excel_mtime_inv())" in ast.unparse(fn)


def test_clear_compatibilidad():
    assert ("cargar_catalogo_inversores.clear = "
            "_cargar_catalogo_inversores_cached.clear") in _SRC


def test_nadie_llama_con_mtime_con_guion_bajo():
    for rel in ("pages/4_📐_Dimensionamiento.py",
                "datos/diagnostico_catalogo_inversores.py"):
        src = (_BASE / rel).read_text()
        assert "_mtime=" not in src, f"{rel} pasa _mtime= (kwarg obsoleto)"


if __name__ == "__main__":
    for k, v in sorted(globals().items()):
        if k.startswith("test_"):
            v()
            print(f"✅ {k}")
    print("OK")
