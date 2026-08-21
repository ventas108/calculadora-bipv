# -*- coding: utf-8 -*-
"""Validación de la alarma automática de validación SDM (2026-08-21).

Hallazgo del usuario: hasta ahora, si validar_sdm_vs_ficha() fallaba
(>5% de error contra la ficha técnica), la ÚNICA forma de enterarse era
entrar manualmente a 🔬 Motor IV y presionar el botón "Ejecutar validación"
-- ninguna otra página de la app lo mostraba, y ni siquiera un fallo
bloqueaba nada.

Esta suite cubre dos partes:
1. calculos.modelo_iv.explicar_fallo_validacion_sdm() -- texto técnico
   determinista (NO es un agente de IA) que explica en qué métricas falla
   y por qué, con datos reales (ASP-ST1-T40, que sí valida) y un caso
   sintético que deliberadamente no valida.
2. Auditoría AST/regex de que 📐 Dimensionamiento corre la validación SOLA
   (no detrás de un botón) y persiste el resultado en session_state, y que
   📊 Producción y 🔬 Motor IV lo leen/escriben con las mismas claves.
"""
import ast
import os

from datos.tecnologias_bipv import ASP_ST1_T40
from calculos.modelo_iv import validar_sdm_vs_ficha, explicar_fallo_validacion_sdm

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ── explicar_fallo_validacion_sdm() -- datos reales + un caso sintético ──────

def test_panel_real_calibrado_valida_y_da_texto_de_ok():
    val = validar_sdm_vs_ficha(ASP_ST1_T40)
    assert val["validacion_ok"] is True
    texto = explicar_fallo_validacion_sdm("ASP-ST1-T40", val)
    assert texto.startswith("✅")
    assert "SDM validado" in texto


def test_panel_con_voc_de_ficha_incorrecto_no_valida_y_explica_la_causa():
    # Ficha deliberadamente incoherente con el SDM calibrado real (Voc_stc
    # muy distinto del que el modelo realmente calcula) -- fuerza el fallo
    # para verificar el texto explicativo, no un caso hipotético inventado.
    panel_malo = {**ASP_ST1_T40, "Voc_stc": 90.0}
    val = validar_sdm_vs_ficha(panel_malo)
    assert val["validacion_ok"] is False
    assert val["Voc"]["ok"] is False

    texto = explicar_fallo_validacion_sdm("Panel-Prueba", val)
    assert texto.startswith("🔴")
    assert "Panel-Prueba" in texto
    assert "Voc" in texto
    assert f"{val['Voc']['error_pct']}%" in texto
    assert "Ns (Celdas Serie)" in texto  # causa técnica específica de Voc
    assert "📊 Producción" in texto and "💰 Financiero" in texto  # explica el impacto aguas abajo


def test_solo_menciona_las_metricas_que_realmente_fallan():
    # Si Isc SÍ valida pero Voc no, el texto no debe citar la causa técnica
    # de Isc -- solo la de la métrica que realmente falló.
    panel_malo = {**ASP_ST1_T40, "Voc_stc": 90.0}
    val = validar_sdm_vs_ficha(panel_malo)
    texto = explicar_fallo_validacion_sdm("Panel-Prueba", val)
    assert val["Isc"]["ok"] is True
    assert "fotocorriente calibrada (I_L_ref)" not in texto  # causa técnica de Isc, no debe aparecer


def test_valida_tambien_vmp_e_imp_no_solo_voc_isc_pmax():
    # 2026-08-21: Vmp/Imp se agregaron porque resolver_curva_iv() ya los
    # calculaba pero no se comparaban contra la ficha -- un punto ciego real,
    # ya que Vmp es el valor que usan los chequeos de compatibilidad
    # eléctrica (ventana MPPT), no Voc.
    val = validar_sdm_vs_ficha(ASP_ST1_T40)
    assert "Vmp" in val and "Imp" in val
    assert val["Vmp"]["ok"] is True
    assert val["Imp"]["ok"] is True


def test_vmp_mal_calibrado_falla_y_explica_causa_especifica_de_vmp():
    panel_malo = {**ASP_ST1_T40, "Vmp_stc": 70.0}   # ficha incoherente con el SDM real
    val = validar_sdm_vs_ficha(panel_malo)
    assert val["Vmp"]["ok"] is False
    assert val["Voc"]["ok"] is True   # Voc no depende de Vmp_stc, sigue validando

    texto = explicar_fallo_validacion_sdm("Panel-Prueba", val)
    assert "Vmp" in texto
    assert "ventana MPPT" in texto  # causa técnica específica de Vmp
    assert "fotocorriente calibrada (I_L_ref)" not in texto  # causa de Isc no debe aparecer


def test_cuenta_correctamente_cuantas_metricas_fallan_de_cuantas_totales():
    panel_malo = {**ASP_ST1_T40, "Voc_stc": 90.0}
    val = validar_sdm_vs_ficha(panel_malo)
    texto = explicar_fallo_validacion_sdm("Panel-Prueba", val)
    n_fallos = sum(1 for k, v in val.items() if k != "validacion_ok" and not v["ok"])
    n_total = len(val) - 1
    assert f"{n_fallos} de {n_total} métricas" in texto


# ── Auditoría AST/regex de las páginas (streamlit no instalado en este entorno) ──

def test_dimensionamiento_corre_la_validacion_sin_boton_explicito():
    # A diferencia de los agentes de IA (que SÍ deben estar detrás de un
    # botón por su costo real de API), esta validación es una comparación
    # numérica gratuita e instantánea -- debe correr sola, no hay razón
    # para exigirle un clic al usuario.
    src = _leer(os.path.join(_ROOT, "pages", "4_📐_Dimensionamiento.py"))
    assert "validar_sdm_vs_ficha(_panel_iv)" in src
    assert "explicar_fallo_validacion_sdm(panel_nombre, _val_sdm_dim)" in src
    # No debe estar envuelta en "if st.button(...)"
    idx_llamada = src.index("validar_sdm_vs_ficha(_panel_iv)")
    fragmento_previo = src[:idx_llamada]
    # El último "if" antes de la llamada no debe ser un st.button de la
    # validación misma (comprobación superficial: no aparece "st.button"
    # entre el bloque "_panel_iv is not None" y la llamada).
    idx_bloque = fragmento_previo.rindex("if _panel_iv is not None:")
    assert "st.button" not in fragmento_previo[idx_bloque:]


def test_dimensionamiento_persiste_el_resultado_en_session_state():
    src = _leer(os.path.join(_ROOT, "pages", "4_📐_Dimensionamiento.py"))
    for clave in ("motor_iv_validacion_ok", "motor_iv_validacion_detalle", "motor_iv_validacion_panel"):
        assert f'st.session_state["{clave}"]' in src


def test_dimensionamiento_no_valida_si_el_sdm_es_estimado():
    # Si el panel usa parámetros estimados (no calibrados), la validación
    # formal contra ficha no aplica -- mismo criterio que 🔬 Motor IV.
    src = _leer(os.path.join(_ROOT, "pages", "4_📐_Dimensionamiento.py"))
    idx = src.index('if _panel_iv.get("_estimado"):')
    assert idx > -1


def test_produccion_lee_la_alarma_y_verifica_que_sea_del_panel_activo():
    src = _leer(os.path.join(_ROOT, "pages", "6_📊_Produccion.py"))
    assert 'st.session_state.get("motor_iv_validacion_ok") is False' in src
    # Debe comparar contra el panel activo -- no mostrar una alarma vieja de
    # OTRO panel que ya no está en uso.
    assert (
        'st.session_state.get("motor_iv_validacion_panel") == '
        'st.session_state.get("panel_nombre_dim")'
    ) in src
    assert "explicar_fallo_validacion_sdm(" in src


def test_motor_iv_tambien_persiste_las_mismas_claves():
    # El botón manual de Motor IV sigue existiendo (útil para explorar
    # cualquier panel del catálogo, no solo el activo) -- pero debe escribir
    # las MISMAS claves que Dimensionamiento, para que ambas páginas queden
    # consistentes sin importar cuál corrió la validación por última vez.
    src = _leer(os.path.join(_ROOT, "pages", "3_🔬_Motor_IV.py"))
    for clave in ("motor_iv_validacion_ok", "motor_iv_validacion_detalle", "motor_iv_validacion_panel"):
        assert f'st.session_state["{clave}"]' in src
    assert "explicar_fallo_validacion_sdm(_panel_nom_ss, val)" in src
