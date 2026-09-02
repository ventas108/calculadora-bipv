# -*- coding: utf-8 -*-
"""
Ancla real: el inversor INVT MG750TL (2-sep-2026) debe estar disponible en el
catálogo real de la app, con los valores reales verificados contra 2 fuentes
(ficha oficial INVT 2020.07 V1.0 + pantalla real de PVsyst 8.1.5 usada en la
validación del motor CdTe). Ver datos/agregar_inversor_invt_mg750tl.py y
DIAGNOSTICO_JRC_HULD_PRIMARIO_CDTE.md / DIAGNOSTICO_RECOMBINACION_CDTE.md
(el mismo inversor de esas corridas reales).

Bug real encontrado y corregido el mismo día: sin `I_max_tracker`/
`Isc_max_tracker` (ninguna fuente lo publica directamente -- PVsyst mostró
"N/A"), `evaluar_compatibilidad_string()` devolvía `evaluable=False` para
CUALQUIER configuración con este inversor, incluida la config real ya
validada (3 en serie x 4 strings) -- no fallaba por incompatibilidad, sino
por "ficha incompleta". Corregido con un valor DERIVADO (no inventado): 900W
(potencia DC máxima real) / 60V (Vmppt mínimo real) = 15A, el peor caso
físico real de corriente a máxima potencia en el extremo inferior de la
ventana MPPT.
"""
import pytest

from datos.catalogo_inversores_excel import cargar_catalogo_inversores
from calculos.dimensionamiento import evaluar_compatibilidad_string, evaluar_relacion_dc_ac
from datos.tecnologias_bipv import ASP_ST1_T40


def test_mg750tl_esta_en_el_catalogo_real():
    cat = cargar_catalogo_inversores()
    assert "MG750TL" in cat, (
        "MG750TL no está en inversores_catalogo.xlsx -- "
        "correr datos/agregar_inversor_invt_mg750tl.py"
    )


def test_mg750tl_valores_reales_verificados():
    cat = cargar_catalogo_inversores()
    inv = cat["MG750TL"]

    # Coinciden EXACTO en la ficha oficial INVT y la pantalla real de PVsyst.
    assert inv["Vdc_max"] == 400.0
    assert inv["P_ac_nom_W"] == 750.0
    assert inv["P_ac_nom_kW"] == 0.75

    # Ventana MPPT: la de la pantalla real de PVsyst (la corrida validada),
    # no la más amplia de la ficha oficial 2020 (50-400V) -- ver docstring
    # de agregar_inversor_invt_mg750tl.py.
    assert inv["Vmppt_min"] == 60.0
    assert inv["Vmppt_max"] == 350.0

    # Real, de la ficha oficial ("Max. DC input power").
    assert inv["P_dc_max_W"] == 900.0

    assert inv["n_trackers"] == 1.0
    assert inv["es_hibrido"] is False
    assert inv["marca"] == "INVT Solar Technology"

    # Corriente máxima derivada (900W/60V) -- ver docstring del módulo.
    assert inv["I_max_tracker"] == pytest.approx(15.0)
    assert inv["Isc_max_tracker"] == pytest.approx(15.0)


def test_mg750tl_evalua_compatible_en_la_config_real_ya_validada():
    # Ancla directa al caso real (ver DIAGNOSTICO_RECOMBINACION_CDTE.md /
    # DIAGNOSTICO_JRC_HULD_PRIMARIO_CDTE.md): 12 módulos ASP-ST1-T40, 3 en
    # serie x 4 strings, con este inversor -- debe evaluar como compatible,
    # no "ficha incompleta".
    cat = cargar_catalogo_inversores()
    inv = cat["MG750TL"]

    r = evaluar_compatibilidad_string(ASP_ST1_T40, inv, N_serie=3, N_strings_tracker=4)
    assert r["evaluable"] is True, r["mensajes"]
    assert r["compatible"] is True, r["mensajes"]

    r_dcac = evaluar_relacion_dc_ac(12 * ASP_ST1_T40["Pmax_stc"] / 1000.0, inv["P_ac_nom_W"])
    assert r_dcac["evaluable"] is True
    assert r_dcac["ratio"] == pytest.approx(1.008, abs=0.01)
    assert r_dcac["nivel"] == "🟢"
