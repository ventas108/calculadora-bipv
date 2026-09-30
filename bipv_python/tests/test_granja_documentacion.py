# -*- coding: utf-8 -*-
"""Documentación completa de 🌾 Granja FV (fases 1 a 5) en el Asistente y el director.

Pedido del usuario (30-sep-2026) al cerrar la fase 5: «documenta de forma
completa estas nuevas aplicaciones y conocimientos al asistente y al director».
"""
from pathlib import Path

from calculos.asistente import (
    PROMPT_SISTEMA,
    BaseConocimiento,
    avisos_coherencia,
    avisos_granja,
    contexto_sesion,
    resumen_granja,
)

RAIZ = Path(__file__).resolve().parents[1]
DIRECTOR = RAIZ.parent / "CodeSpecs" / "00-director"
KB = (RAIZ / "datos" / "base_conocimiento_asistente.md").read_text(encoding="utf-8")
JAM = {"nombre": "JA Solar JAM66D46-720/LB", "dimensiones_mm": "2384x1303x33 mm", "area_m2": 3.1064,
       "Pmax_stc": 720.0, "Imp_stc": 17.48, "Vmp_stc": 41.19}
GEO = {"ancho_terreno_m": 80.0, "largo_terreno_m": 30.0, "modulos_pendiente": 2, "orientacion": "horizontal",
       "modulos_por_mesa": 31, "mesas_por_fila": 1, "pasillo_m": 3.0, "pitch_m": 6.60, "altura_libre_m": 2.4}


def _estado(**kw):
    e = {"tipo_instalacion": "Granja fotovoltaica", "granja_fv": GEO, "panel_dict": JAM, "N_serie": 28,
         "N_paneles_final": 308, "reparto_strings_inversores": [6, 5], "tilt_fachada": 10,
         "azimuth_fachada": 180, "inversor_dict_dim": {"P_ac_nom_W": 100_000.0},
         "granja_fv_resultado": {"modulos_colocados": 308, "modulos_proyecto": 308, "filas_usadas": 5,
                                 "gcr": 0.3979, "angulo_limite_deg": 6.5, "corredor_m": 4.01,
                                 "altura_centro_m": 2.628},
         "granja_luz_suelo": {"media_pct": 60.2, "media_kwh_m2": 1158.0, "bajo_mesa_pct": 44.6,
                              "entre_filas_pct": 70.6, "homogeneidad": 0.44},
         "granja_seguidor": {"ganancia_backtracking_pct": 24.7, "ganancia_sin_backtracking_pct": 21.1,
                             "perdida_sombra_electrica_pct": 2.7}}
    e.update(kw)
    return e


# ── Manual: sección 98 ───────────────────────────────────────────────────────
def test_seccion_98_guia_completa():
    s = KB[KB.index("## 98."):]
    for t in ("Las 5 fases", "orden de trabajo", "Usar la geometría del campo en la energía",
              "Calcular la luz en el suelo", "Comparar seguidor y estructura fija",
              "Usar los cables de 🌾 Granja FV", "Cambian la energía", "Solo informan o comparan",
              "glosario", "tabla de alarmas", "Apartadó de punta a punta", "preguntas frecuentes",
              "Límites conocidos", "339.033", "2,626", "0,19 %", "60 %", "6 + 5"):
        assert t in s, t
    assert "PVsyst" not in s


def test_las_cinco_secciones_de_fase_existen():
    for n in ("## 93.", "## 94.", "## 95.", "## 96.", "## 97.", "## 98."):
        assert n in KB


def test_el_asistente_encuentra_la_guia():
    base = BaseConocimiento.cargar()
    for pregunta, esperado in (
        ("en qué orden uso granja FV paso a paso", "Granja FV — orden de trabajo paso a paso"),
        ("qué significa la alarma strings que cruzan filas en granja", "Granja FV — tabla de alarmas y qué hacer"),
        ("qué es el backtracking del seguidor", "Seguidor de un eje"),
        ("luz que llega al cultivo agrivoltaica", "Agrivoltaica"),
    ):
        titulos = [s["titulo"] for s in base.buscar(pregunta, k=4)]
        assert any(esperado in t for t in titulos), (pregunta, titulos)


# ── Contexto de sesión y avisos ──────────────────────────────────────────────
def test_resumen_granja_con_resultados_reales():
    lineas = resumen_granja(_estado())
    texto = "\n".join(lineas)
    assert "GCR 39.8 %" in texto and "ángulo límite 6.5°" in texto
    assert "Luz en el suelo: media 60 %" in texto
    assert "+24.7 % con backtracking" in texto
    assert "11 strings de 28 (6 + 5 por inversor)" in texto
    assert "\n".join(resumen_granja(_estado())) in contexto_sesion(_estado())


def test_resumen_granja_vacio_si_no_es_granja():
    assert resumen_granja(_estado(tipo_instalacion="Fachada BIPV")) == []
    assert avisos_granja(_estado(tipo_instalacion="Fachada BIPV")) == []


def test_avisos_granja():
    sin_campo = avisos_granja({"tipo_instalacion": "Granja fotovoltaica"})
    assert len(sin_campo) == 1 and "🌾 Granja FV" in sin_campo[0]
    av = avisos_granja(_estado(res_produccion={"x": 1}))
    assert any("Usar la geometría del campo en la energía" in a for a in av)
    assert any("Usar los cables de 🌾 Granja FV" in a for a in av)
    ok = avisos_granja(_estado(poa_geometria_filas={"gcr": 0.4, "altura_m": 2.6, "ancho_colector_m": 2.6},
                               res_produccion={"x": 1}, perdida_ohmica_unifilar={"r": 1}))
    assert ok == []
    assert set(avisos_granja(_estado())) <= set(avisos_coherencia(_estado()))


def test_prompt_incluye_granjas():
    assert "granjas solares y agrivoltaicas" in PROMPT_SISTEMA


# ── Director ─────────────────────────────────────────────────────────────────
def test_director_documenta_la_granja():
    mapa = (DIRECTOR / "mapa-dependencias.md").read_text(encoding="utf-8")
    assert "🌾 Granja FV (Streamlit" in mapa and "diseno_desde_estado" in mapa and "calcular_poa(filas=" in mapa
    arq = (DIRECTOR / "arquitectura-global.md").read_text(encoding="utf-8")
    for m in ("granja_fv.py", "agrivoltaica.py", "seguidor.py", "granja_electrico.py"):
        assert m in arq, m
    contratos = (DIRECTOR / "contratos-entre-modulos.md").read_text(encoding="utf-8")
    for clave in ("`granja_luz_suelo`", "`granja_electrico_cfg`", "`filas_energia`", "`poa_geometria_filas`"):
        assert clave in contratos, clave
    registro = (DIRECTOR / "registro-de-decisiones.md").read_text(encoding="utf-8")
    assert "Documentación completa de 🌾 Granja FV" in registro
