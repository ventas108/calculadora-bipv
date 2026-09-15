# -*- coding: utf-8 -*-
"""CodeSpecs/01-datos-proyecto — recorte defensivo de factor_ocupacion_pct.

diseno.md: "JSON de proyecto guardado corrupto o con factor_ocupacion_pct
fuera de [5, 100]: se recorta defensivamente (min(max(...))) al cargar."

pages/1_🏠_Proyecto.py es una página Streamlit completa (st.set_page_config,
requerir_login(), etc. a nivel de módulo) -- no se puede importar sin
levantar toda la app. Igual que tests/test_carga_proyecto_127.py hace para
proyectos_manager.py, se extrae y evalúa vía AST solo la expresión del
recorte defensivo (línea `_f_ocup_def = ...`), en vez de reimplementar la
fórmula a mano (lo que no detectaría una regresión en el código real).
"""
import ast
import os

RUTA = os.path.join(os.path.dirname(__file__), "..", "pages", "1_🏠_Proyecto.py")


def _expr_clamp() -> ast.Expression:
    tree = ast.parse(open(RUTA, encoding="utf-8").read())
    for n in ast.walk(tree):
        if (isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "_f_ocup_def" for t in n.targets)):
            return ast.fix_missing_locations(ast.Expression(body=n.value))
    raise AssertionError("No se encontró la asignación de _f_ocup_def en la página de Proyecto")


class _SessionStateStub(dict):
    def get(self, key, default=None):
        return dict.get(self, key, default)


class _StStub:
    def __init__(self, valor_guardado):
        self.session_state = _SessionStateStub()
        if valor_guardado is not None:
            self.session_state["factor_ocupacion_pct"] = valor_guardado


def _clamp(valor_guardado):
    """Evalúa la expresión real de recorte defensivo del código de la página."""
    codigo = compile(_expr_clamp(), RUTA, "eval")
    return eval(codigo, {"st": _StStub(valor_guardado), "float": float})


def test_valor_dentro_de_rango_no_se_altera():
    assert _clamp(35.0) == 35.0


def test_valor_por_encima_de_100_se_recorta_a_100():
    assert _clamp(500.0) == 100.0


def test_valor_por_debajo_de_5_se_recorta_a_5():
    assert _clamp(-20.0) == 5.0


def test_valor_cero_cae_al_default_100_por_el_or():
    # 0.0 es falsy en Python: el `or 100.0` del código real lo trata como
    # "sin valor" y lo reemplaza por el default (100.0) ANTES del clamp
    # min/max -- documentando este comportamiento real, no uno asumido.
    assert _clamp(0.0) == 100.0


def test_sin_valor_guardado_usa_default_100():
    assert _clamp(None) == 100.0
