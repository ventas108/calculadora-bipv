"""
Regresión: validador de coherencia física de inversores.

Antes de esta sesión no había ningún test directo de
calculos/validador_inversor.py. Ver DIAGNOSTICO_EXTRACCION_INVERSORES_MUST.md
para el contexto completo de "estructura lógica para evitar errores"
pedida por el usuario (30-ago-2026).
"""
from calculos.validador_inversor import validar_inversor, validar_coherencia_familia


def test_techo_p_dc_usa_vmppt_min_no_vdc_max():
    # Bug real corregido: el techo físico usaba Vdc_max (el límite MÁS
    # generoso posible), no Vmppt_min (el peor caso real de mayor
    # corriente, P=V×I). Caso real PV35-12048 TLV: Vdc_max=145V,
    # Vmppt_min=64V, I_max=100A, n_trackers no publicado (híbrido de un
    # solo cargador -> se asume 1). Techo real = 64×100×1 = 6400W.
    campos = {
        "Vdc_max": 145.0, "Vmppt_min": 64.0, "Vmppt_max": 145.0,
        "I_max_tracker": 100.0, "P_dc_max_W": 6500.0,  # supera el techo real (6400W)
        "es_hibrido": True,
    }
    r = validar_inversor(campos)
    assert r["campos"]["P_dc_max_W"]["estado"] == "warn"
    assert "6,400" in r["campos"]["P_dc_max_W"]["detalle"] or "6400" in r["campos"]["P_dc_max_W"]["detalle"]


def test_techo_p_dc_no_se_salta_por_n_trackers_ausente_en_hibrido():
    # Bug real: antes, si n_trackers era None (común en híbridos MUST, que
    # nunca lo publican), el chequeo se saltaba por completo -- ahora se
    # asume 1 tracker para híbridos en vez de quedar ciego.
    campos = {
        "Vdc_max": 145.0, "Vmppt_min": 64.0, "Vmppt_max": 145.0,
        "I_max_tracker": 100.0, "P_dc_max_W": 10000.0,  # supera 6400W con margen
        "n_trackers": None, "es_hibrido": True,
    }
    r = validar_inversor(campos)
    assert r["campos"]["P_dc_max_W"]["estado"] == "warn"


def test_techo_p_dc_dentro_del_limite_real_no_avisa():
    # Caso real PV35-12048 TLV con su P_dc_max_W real (5000W) -- dentro del
    # techo real (6400W) -- no debe avisar.
    campos = {
        "Vdc_max": 145.0, "Vmppt_min": 64.0, "Vmppt_max": 145.0,
        "I_max_tracker": 100.0, "P_dc_max_W": 5000.0,
        "es_hibrido": True,
    }
    r = validar_inversor(campos)
    assert r["campos"]["P_dc_max_W"]["estado"] == "ok"


def test_bat_corriente_carga_max_ausente_en_hibrido_avisa():
    campos = {"Vdc_max": 145.0, "es_hibrido": True, "bat_corriente_carga_max": None}
    r = validar_inversor(campos)
    assert r["campos"]["bat_corriente_carga_max"]["estado"] == "warn"


def test_bat_corriente_carga_max_presente_marca_ok():
    campos = {"Vdc_max": 145.0, "es_hibrido": True, "bat_corriente_carga_max": 80.0}
    r = validar_inversor(campos)
    assert r["campos"]["bat_corriente_carga_max"]["estado"] == "ok"


def test_bat_corriente_carga_max_no_aplica_a_no_hibridos():
    campos = {"Vdc_max": 1100.0, "es_hibrido": False}
    r = validar_inversor(campos)
    assert "bat_corriente_carga_max" not in r["campos"]


# ── validar_coherencia_familia() ──────────────────────────────────────────────

def test_familia_monotona_no_avisa():
    # Caso real PV35: 8048 < 10048 < 12048, todo sube o se mantiene igual.
    modelos = ["PV35-8048", "PV35-10048", "PV35-12048"]
    valores = {
        "PV35-8048":  {"P_dc_max_W": 5000.0, "bat_corriente_carga_max": 60.0},
        "PV35-10048": {"P_dc_max_W": 5000.0, "bat_corriente_carga_max": 70.0},
        "PV35-12048": {"P_dc_max_W": 5000.0, "bat_corriente_carga_max": 80.0},
    }
    r = validar_coherencia_familia(modelos, valores)
    assert r["ok"] is True
    assert r["avisos"] == []


def test_familia_no_monotona_avisa_columna_mal_alineada():
    # Simula el mismo tipo de bug real ya encontrado y corregido esta
    # sesión (columnas fusionadas/mal alineadas en un multi-modelo): el
    # modelo de MAYOR potencia (12048) queda con MENOS corriente que el de
    # potencia media (10048) -- inconsistente, el fabricante lista de menor
    # a mayor potencia.
    modelos = ["PV35-8048", "PV35-10048", "PV35-12048"]
    valores = {
        "PV35-8048":  {"bat_corriente_carga_max": 60.0},
        "PV35-10048": {"bat_corriente_carga_max": 80.0},
        "PV35-12048": {"bat_corriente_carga_max": 70.0},  # baja -- incoherente
    }
    r = validar_coherencia_familia(modelos, valores)
    assert r["ok"] is False
    assert any("PV35-12048" in a and "PV35-10048" in a for a in r["avisos"])


def test_familia_de_un_solo_modelo_no_avisa():
    r = validar_coherencia_familia(["PV35-8048"], {"PV35-8048": {"P_dc_max_W": 5000.0}})
    assert r["ok"] is True
