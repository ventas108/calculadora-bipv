"""
Regresión: default de k_BIPV/montaje por tipo de instalación.

Antes del 30-ago-2026 el default de "Tipo de montaje" en 🔆 Motor Óptico era
binario -- solo "Granja fotovoltaica" recibía k=1.0 (ventilado libre); los
otros 5 tipos, incluidos "Techo plano (con soporte)", "Pérgola / sombreadero"
y "Marquesina / voladizo" (estructuras elevadas y ventiladas, no fachadas
selladas), heredaban k=1.3 (fachada confinada) sin justificación física.

Ver DIAGNOSTICO_MODELO_TERMICO_UC_UV.md.
"""
from calculos.motor_optico import TIPOS_MONTAJE_CONFINADO

# Debe coincidir con LISTA_TIPOS / TIPOS_INSTALACION en pages/1_🏠_Proyecto.py.
# Si se agrega un tipo de instalación nuevo ahí, este set (y su clasificación
# física) debe revisarse también.
TIPOS_INSTALACION_CONOCIDOS = {
    "Fachada BIPV",
    "Techo inclinado (BIPV)",
    "Techo plano (con soporte)",
    "Pérgola / sombreadero",
    "Marquesina / voladizo",
    "Granja fotovoltaica",
}


def test_tipos_montaje_confinado_es_subconjunto_de_tipos_conocidos():
    assert TIPOS_MONTAJE_CONFINADO <= TIPOS_INSTALACION_CONOCIDOS


def test_tipos_confinados_son_solo_fachada_y_techo_bipv():
    # Solo estructuras con cámara de aire restringida detrás del panel.
    assert TIPOS_MONTAJE_CONFINADO == {"Fachada BIPV", "Techo inclinado (BIPV)"}


def test_tipos_elevados_ventilados_no_estan_confinados():
    # Regresión directa del bug: estos 3 tipos son estructuras elevadas con
    # flujo de aire libre en ambas caras -- NO deben heredar el default de
    # fachada sellada (k=1.3).
    tipos_ventilados = {
        "Techo plano (con soporte)",
        "Pérgola / sombreadero",
        "Marquesina / voladizo",
        "Granja fotovoltaica",
    }
    assert tipos_ventilados.isdisjoint(TIPOS_MONTAJE_CONFINADO)


def test_simula_seleccion_de_index_por_tipo():
    # Reproduce la lógica de pages/5b_🔆_Motor_Optico.py:
    #   _es_campo_abierto = tipo not in TIPOS_MONTAJE_CONFINADO
    #   _idx_montaje_default = 0 if _es_campo_abierto else 1
    for tipo in TIPOS_INSTALACION_CONOCIDOS:
        es_campo_abierto = tipo not in TIPOS_MONTAJE_CONFINADO
        idx = 0 if es_campo_abierto else 1
        if tipo in {"Fachada BIPV", "Techo inclinado (BIPV)"}:
            assert idx == 1, f"{tipo} debería defaultear a Fachada confinada (k=1.3)"
        else:
            assert idx == 0, f"{tipo} debería defaultear a Ventilado libre (k=1.0)"
