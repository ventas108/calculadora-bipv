"""
Regresión: default de k_BIPV/montaje por tipo de instalación.

Historia (ver DIAGNOSTICO_MODELO_TERMICO_UC_UV.md para el detalle completo):
- Antes del 30-ago-2026 el default era binario -- solo "Granja fotovoltaica"
  recibía k=1.0 (ventilado libre); los otros 5 tipos, incluidos "Techo plano
  (con soporte)", "Pérgola / sombreadero" y "Marquesina / voladizo"
  (estructuras elevadas y ventiladas, no fachadas selladas), heredaban
  k=1.3 (fachada confinada) sin justificación física.
- Primer fix (30-ago-2026): mapeo de 2 grupos, reutilizando solo los 3
  valores ya existentes de K_BIPV_POR_MONTAJE.
- Segundo fix (30-ago-2026, mismo día, tras auto-auditoría pedida por el
  usuario): se agregó un 4to nivel "Semi-ventilado" (k=1.15, sin
  calibración propia -- interpolado) para Pérgola/Marquesina, distinto del
  k=1.0 pleno de Granja fotovoltaica/Techo plano con soporte.
"""
import calculos.motor_optico as motor_optico
from calculos.motor_optico import (
    K_BIPV_POR_MONTAJE,
    TIPOS_MONTAJE_CONFINADO,
    TIPOS_MONTAJE_SEMIVENTILADO,
    indice_montaje_default,
)

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


def test_tipos_montaje_son_subconjuntos_de_tipos_conocidos_y_disjuntos():
    assert TIPOS_MONTAJE_CONFINADO <= TIPOS_INSTALACION_CONOCIDOS
    assert TIPOS_MONTAJE_SEMIVENTILADO <= TIPOS_INSTALACION_CONOCIDOS
    assert TIPOS_MONTAJE_CONFINADO.isdisjoint(TIPOS_MONTAJE_SEMIVENTILADO)


def test_tipos_confinados_son_solo_fachada_y_techo_bipv():
    assert TIPOS_MONTAJE_CONFINADO == {"Fachada BIPV", "Techo inclinado (BIPV)"}


def test_tipos_semiventilados_son_solo_pergola_y_marquesina():
    assert TIPOS_MONTAJE_SEMIVENTILADO == {"Pérgola / sombreadero", "Marquesina / voladizo"}


def test_indice_montaje_default_por_tipo():
    claves = list(K_BIPV_POR_MONTAJE.keys())
    casos = {
        "Fachada BIPV": 1.3,
        "Techo inclinado (BIPV)": 1.3,
        "Pérgola / sombreadero": 1.15,
        "Marquesina / voladizo": 1.15,
        "Techo plano (con soporte)": 1.0,
        "Granja fotovoltaica": 1.0,
    }
    for tipo, k_esperado in casos.items():
        idx = indice_montaje_default(tipo)
        assert K_BIPV_POR_MONTAJE[claves[idx]] == k_esperado, (
            f"{tipo} debería defaultear a k={k_esperado}, dio "
            f"k={K_BIPV_POR_MONTAJE[claves[idx]]}"
        )


def test_indice_montaje_default_no_depende_del_orden_del_dict(monkeypatch):
    # indice_montaje_default() busca por VALOR de k_BIPV, no por posición
    # fija -- reordenar K_BIPV_POR_MONTAJE no debe romper el default.
    orden_alterado = {
        "Sin ventilación (k=1.5) — sellado total": 1.5,
        "Ventilado libre (k=1.0) — espacio > 10 cm": 1.0,
        "Fachada confinada (k=1.3) — montaje típico": 1.3,
        "Semi-ventilado (k=1.15) — un lado parcial. cerrado": 1.15,
    }
    monkeypatch.setattr(motor_optico, "K_BIPV_POR_MONTAJE", orden_alterado)
    claves = list(orden_alterado.keys())
    idx = motor_optico.indice_montaje_default("Fachada BIPV")
    assert orden_alterado[claves[idx]] == 1.3
