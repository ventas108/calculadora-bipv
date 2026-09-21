"""Regresiones estáticas del modo físico opt-in de Vista 3D (recreado, ronda
de recuperación 2026-09-21, tras el borrado accidental de este archivo)."""
from pathlib import Path

PAGINA = Path(__file__).parents[1] / "pages" / "9_🗺️_Vista_3D.py"


def _fuente() -> str:
    return PAGINA.read_text(encoding="utf-8")


def test_modo_fisico_es_opt_in_y_apagado_por_defecto():
    src = _fuente()
    assert 'key="multisup_usar_fisico"' in src
    assert 'bool(st.session_state.get("multisup_usar_fisico", False))' in src


def test_comparacion_no_publica_multisup_hasta_adopcion():
    src = _fuente()
    inicio = src.index("if _usar_fisico:")
    adopcion = src.index("aplicar_proyecto_a_session_state(", inicio)
    comparacion = src.index('"btn_comparar_multisup_fisico"', inicio)
    assert comparacion < adopcion
    assert src.index('"btn_adoptar_multisup_fisico"', inicio) < adopcion


def test_vista_3d_usa_construir_y_recalcular_proyecto_fisico():
    src = _fuente()
    assert "construir_y_recalcular_proyecto_fisico" in src
    assert "aplicar_proyecto_a_session_state" in src
    assert "multisup_proyecto_fisico_candidato" in src


def test_adopcion_revalida_en_vez_de_confiar_en_el_candidato_guardado():
    """El botón "Adoptar" debe volver a llamar
    construir_y_recalcular_proyecto_fisico (revalidación real) ANTES de
    aplicar_proyecto_a_session_state -- nunca debe publicar directamente el
    candidato guardado de un rerun anterior."""
    src = _fuente()
    inicio_boton = src.index('"btn_adoptar_multisup_fisico"')
    ocurrencias = [
        i for i in range(len(src))
        if src.startswith("construir_y_recalcular_proyecto_fisico(", i)
    ]
    assert len(ocurrencias) >= 2, (
        "Debe haber al menos dos llamadas: una en 'calcular comparación' y "
        "otra en 'adoptar' (revalidación)."
    )
    segunda_llamada = ocurrencias[1]
    assert inicio_boton < segunda_llamada
    adopcion = src.index("aplicar_proyecto_a_session_state(", segunda_llamada)
    assert segunda_llamada < adopcion


def test_adopcion_no_publica_si_la_revalidacion_falla():
    src = _fuente()
    inicio_boton = src.index('"btn_adoptar_multisup_fisico"')
    bloque = src[inicio_boton:inicio_boton + 2200]
    assert "except" in bloque
    assert "else:" in bloque


def test_editor_de_geometria_preserva_campos_fisicos_en_vez_de_perderlos():
    """El bucle que reconstruye superficies_bipv en cada rerun debe pasar
    por preservar_o_invalidar_campos_fisicos -- de lo contrario cualquier
    p_shade/firma_sombra/n_serie/n_paralelo/inversor_id que se llegue a
    escribir en una superficie se perdería en silencio."""
    src = _fuente()
    assert "preservar_o_invalidar_campos_fisicos" in src
    assert "preservar_o_invalidar_campos_fisicos(_sup, {" in src


def test_modo_fisico_muestra_estado_por_superficie_antes_de_calcular():
    src = _fuente()
    assert "resumen_estado_fisico_superficies" in src
    inicio = src.index("if _usar_fisico:")
    resumen = src.index("resumen_estado_fisico_superficies(", inicio)
    boton = src.index('"btn_comparar_multisup_fisico"', inicio)
    assert resumen < boton


def test_ui_expone_inversores_y_asignacion_por_superficie():
    src = _fuente()
    assert 'key="btn_add_multisup_inversor"' in src
    assert 'key=f"ms_sup_inv_' in src
    assert "validar_inversores_y_asignaciones(" in src
    assert 'st.session_state["multisup_inversores"]' in src


def test_ui_no_permite_declarar_tipo_de_inversor_manualmente():
    src = _fuente()
    inicio = src.index('st.markdown("##### 🔌 Inversores por superficie")')
    fin = src.index("# Calcular POA para todas", inicio)
    bloque = src[inicio:fin]
    assert "se deriva" in bloque
    assert 'selectbox("Tipo"' not in bloque
    assert 'text_input("Tipo"' not in bloque


def test_ui_conecta_site_designer_y_puntos_por_superficie():
    src = _fuente()
    assert "cargar_escena_sitedesigner" in src
    assert 'key="multisup_site_designer_json"' in src
    assert "calcular_fs_horario_por_superficie(" in src
    assert "aplicar_sombra_a_superficies(" in src


def test_ui_bloquea_sombra_hasta_tener_malla_tmy_y_puntos():
    src = _fuente()
    assert "_sombra_lista" in src
    assert "disabled=not _sombra_lista" in src
