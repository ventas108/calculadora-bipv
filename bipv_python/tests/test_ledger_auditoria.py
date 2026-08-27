# -*- coding: utf-8 -*-
"""Ledger de Auditoría — cadena de hashes por proyecto (2026-08-25).

Pedido del usuario: un registro local, auditable y tamper-evident de cada
resultado "oficial" (bancable, informativo para cliente, o diagnóstico de
sistema instalado) que sale de la calculadora -- Res. CREG 174/2021 Art. 6
exige trazabilidad de los cálculos. Cada eslabón encadena su hash con el
del eslabón anterior del mismo proyecto; alterar cualquier campo de un
eslabón ya guardado rompe la cadena de forma detectable.

Cada test usa un directorio temporal aislado (monkeypatch de _DIR_LEDGER)
para no tocar datos/ledger_auditoria/ del repo real.
"""
import json

import pytest

import calculos.ledger_auditoria as m


@pytest.fixture(autouse=True)
def _dir_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_DIR_LEDGER", str(tmp_path))


def test_sellar_el_primer_eslabon_encadena_con_genesis():
    e = m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable",
                            {"panel": "X"}, {"tir_pct": 12.0})
    assert e["hash_anterior"] == m.GENESIS
    assert e["id"] == 1
    assert len(e["hash_propio"]) == 64  # SHA-256 hex


def test_sellar_varios_eslabones_encadena_correctamente():
    e1 = m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable", {}, {})
    e2 = m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_informativo", {}, {})
    assert e2["hash_anterior"] == e1["hash_propio"]
    assert e2["id"] == 2


def test_tipo_invalido_lanza_valueerror():
    with pytest.raises(ValueError, match="tipo debe ser uno de"):
        m.sellar_resultado("Proyecto A", "ana@test.com", "tipo_inventado", {}, {})


def test_proyectos_distintos_tienen_cadenas_independientes():
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable", {}, {})
    m.sellar_resultado("Proyecto B", "ana@test.com", "presupuesto_bancable", {}, {})
    assert len(m.listar_eslabones("Proyecto A", "ana@test.com")) == 1
    assert len(m.listar_eslabones("Proyecto B", "ana@test.com")) == 1


def test_mismo_nombre_de_proyecto_usuarios_distintos_no_se_mezclan():
    # Privacidad: dos usuarios con un proyecto del mismo nombre no deben
    # compartir ni ver la cadena del otro (mismo principio que
    # proyectos_manager -- slug con hash del usuario incluido).
    m.sellar_resultado("Mismo Nombre", "ana@test.com", "presupuesto_bancable", {}, {})
    m.sellar_resultado("Mismo Nombre", "beto@test.com", "presupuesto_bancable", {}, {})
    assert len(m.listar_eslabones("Mismo Nombre", "ana@test.com")) == 1
    assert len(m.listar_eslabones("Mismo Nombre", "beto@test.com")) == 1


# ═══════════════════════ Verificación de integridad ═════════════════════════

def test_cadena_recien_sellada_es_integra():
    for _ in range(3):
        m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable",
                            {"x": 1}, {"tir_pct": 10.0})
    r = m.verificar_cadena("Proyecto A", "ana@test.com")
    assert r["integra"] is True
    assert r["eslabones_verificados"] == 3
    assert r["primer_eslabon_roto"] is None


def test_cadena_vacia_es_integra_por_definicion():
    r = m.verificar_cadena("Proyecto Sin Sellar", "ana@test.com")
    assert r["integra"] is True
    assert r["eslabones_verificados"] == 0


def test_alterar_un_campo_de_un_eslabon_rompe_la_cadena(tmp_path):
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable",
                        {"tir_pct": 10.0}, {})
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable",
                        {"tir_pct": 12.0}, {})
    ruta = m._ruta_ledger("Proyecto A", "ana@test.com")
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    # Alteración "silenciosa" fuera de la app: cambia un insumo del PRIMER
    # eslabón directamente en el archivo, sin recalcular su hash.
    datos[0]["insumos"]["tir_pct"] = 99.0
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f)

    r = m.verificar_cadena("Proyecto A", "ana@test.com")
    assert r["integra"] is False
    assert r["primer_eslabon_roto"] == 1


def test_alterar_la_nota_tambien_rompe_la_cadena(tmp_path):
    # La nota es texto libre -- debe estar cubierta por el hash igual que
    # cualquier otro campo, o sería un vector de alteración "silenciosa".
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable",
                        {}, {}, nota="Versión final entregada al cliente")
    ruta = m._ruta_ledger("Proyecto A", "ana@test.com")
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    datos[0]["nota"] = "Versión DEFINITIVA entregada"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f)

    r = m.verificar_cadena("Proyecto A", "ana@test.com")
    assert r["integra"] is False
    assert r["primer_eslabon_roto"] == 1


def test_insertar_un_eslabon_falso_en_medio_de_la_cadena_se_detecta():
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable", {}, {})
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable", {}, {})
    ruta = m._ruta_ledger("Proyecto A", "ana@test.com")
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    falso = dict(datos[0])
    falso["id"] = 99
    falso["resultados"] = {"tir_pct": 999}
    # Insertado con un hash_anterior que no corresponde a ningún eslabón real.
    datos.insert(1, falso)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f)

    r = m.verificar_cadena("Proyecto A", "ana@test.com")
    assert r["integra"] is False


def test_eliminar_un_eslabon_intermedio_rompe_la_cadena():
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable", {}, {})
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable", {}, {})
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable", {}, {})
    ruta = m._ruta_ledger("Proyecto A", "ana@test.com")
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    del datos[1]  # borra el segundo eslabón "por fuera" de la app
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f)

    r = m.verificar_cadena("Proyecto A", "ana@test.com")
    assert r["integra"] is False


# ═══════════════════════════════ Exportación ════════════════════════════════

def test_exportar_json_reproduce_los_eslabones():
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable",
                        {"panel": "X"}, {"tir_pct": 10.0})
    bruto = m.exportar_cadena("Proyecto A", "ana@test.com", formato="json")
    datos = json.loads(bruto)
    assert len(datos) == 1
    assert datos[0]["insumos"]["panel"] == "X"


def test_exportar_markdown_incluye_hash_y_tipo():
    m.sellar_resultado("Proyecto A", "ana@test.com", "presupuesto_bancable", {}, {})
    texto = m.exportar_cadena("Proyecto A", "ana@test.com", formato="markdown").decode("utf-8")
    assert "Eslabón 1" in texto
    assert "Presupuesto bancable" in texto


def test_exportar_formato_no_soportado_da_error_claro():
    with pytest.raises(ValueError, match="Formato no soportado"):
        m.exportar_cadena("Proyecto A", "ana@test.com", formato="xml")


# ══════════════════ Snapshots de insumos/resultados verificados ═════════════

def test_snapshot_insumos_lee_las_claves_reales_de_sesion():
    estado = {
        "tmy_ciudad": "Barranquilla", "tipo_instalacion": "Techo plano (con soporte)",
        "panel_nombre_dim": "ASP-ST1-T40", "inversor_nombre_dim": "Growatt MID25KTL3-X",
        "N_paneles_final": 120, "P_stc_kW_sistema": 55.0,
        "tasa_degradacion_usada": 0.55, "fuente_degradacion": "historial real",
        "tarifa_cop_kwh": 780.0, "tipo_cambio": 4050.0,
        "presupuesto_capex_usd": 42000.0, "presupuesto_fuente": "Presupuesto detallado",
    }
    snap = m.construir_snapshot_insumos(estado)
    assert snap["ciudad"] == "Barranquilla"
    assert snap["panel"] == "ASP-ST1-T40"
    assert snap["capex_usd"] == 42000.0


def test_snapshot_resultados_lee_metricas_financiero_anidado():
    estado = {
        "E_ac_anual_kWh": 91000.0, "PR_sistema": 0.81,
        "metricas_financiero": {"vpn_usd": 15000.0, "tir_pct": 13.2,
                                "payback_simple": 7.4, "lcoe_usd_kWh": 0.081},
    }
    snap = m.construir_snapshot_resultados(estado)
    assert snap["e_ac_anual_kwh"] == 91000.0
    assert snap["tir_pct"] == 13.2
    assert snap["lcoe_usd_kwh"] == 0.081


def test_snapshot_resultados_sin_financiero_no_falla():
    snap = m.construir_snapshot_resultados({})
    assert snap["vpn_usd"] is None
    assert snap["tir_pct"] is None


# ══════════════════════════════════════════════════════════════════════════
# Tipo "diagrama_unifilar" (Diagrama Unifilar Fase 4, 27-ago-2026)
# ══════════════════════════════════════════════════════════════════════════
def test_diagrama_unifilar_es_tipo_valido():
    assert "diagrama_unifilar" in m.TIPOS_VALIDOS
    assert "diagrama_unifilar" in m.TIPO_LABELS


def test_sellar_diagrama_unifilar_encadena_correctamente():
    e = m.sellar_resultado(
        "Proyecto Unifilar", "ana@test.com", "diagrama_unifilar",
        {"generador": {"n_paneles": 306, "p_dc_kWp": 220.32}},
        {"p_dc_total_kWp": 220.32, "p_ac_total_kW": 200.0},
    )
    assert e["tipo"] == "diagrama_unifilar"
    assert e["hash_anterior"] == m.GENESIS
    v = m.verificar_cadena("Proyecto Unifilar", "ana@test.com")
    assert v["integra"] is True
    assert v["eslabones_verificados"] == 1


def test_sellar_diagrama_unifilar_coexiste_con_otros_tipos_mismo_proyecto():
    # Un mismo proyecto puede tener eslabones de distinto tipo encadenados
    # entre si (ej. primero un diagnostico, luego un unifilar) -- la cadena
    # no distingue tipo para el encadenamiento, solo para el filtro visual.
    m.sellar_resultado("Proyecto Mixto", "ana@test.com", "diagnostico_operacion", {}, {})
    e2 = m.sellar_resultado("Proyecto Mixto", "ana@test.com", "diagrama_unifilar", {}, {})
    assert e2["id"] == 2
    v = m.verificar_cadena("Proyecto Mixto", "ana@test.com")
    assert v["integra"] is True
    assert v["eslabones_verificados"] == 2
