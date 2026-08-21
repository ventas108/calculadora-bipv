# -*- coding: utf-8 -*-
"""Regresión: los SYSTEM_PROMPT de los dos agentes asumían "BIPV integrado
en fachadas de edificios" como la ÚNICA forma de instalación posible. Un
usuario corrió un ejercicio real de "Granja fotovoltaica" (montaje en
suelo, sin nada de fachada) y el Analista Técnico-Financiero narró su
análisis en clave de fachada de edificio -- un sesgo del prompt, no un
error de los datos (los números citados eran reales).

Fix de dos partes: (1) el SYSTEM_PROMPT ya no asume fachada por defecto y
menciona explícitamente que también hay granjas de suelo -- cubierto aquí;
(2) pages/18 le declara el tipo de instalación real como dato explícito en
cada pregunta -- cubierto en tests/test_pagina_analisis_ia.py.

agentes/analista_produccion.py (tercer agente, Fase 5) se diseñó DESDE el
principio con la regla 0 ya incorporada -- no como parche posterior -- pero
se incluye en este mismo test para que un futuro editor no la vuelva a
quitar por accidente.
"""
import agentes.analista_tecnico_financiero as analista
import agentes.asesor_inversion as asesor
import agentes.analista_produccion as analista_prod


def test_prompts_no_asumen_fachada_como_unica_forma_de_instalacion():
    for modulo in (analista, asesor, analista_prod):
        prompt = modulo.SYSTEM_PROMPT
        assert "granja" in prompt.lower(), (
            f"{modulo.__name__}.SYSTEM_PROMPT no menciona granjas fotovoltaicas -- "
            "sigue asumiendo BIPV-en-fachada como la única forma de instalación"
        )
        assert "no asumas fachada" in prompt.lower()


def test_prompts_exigen_usar_el_tipo_de_instalacion_declarado_en_contexto():
    for modulo in (analista, asesor, analista_prod):
        prompt = modulo.SYSTEM_PROMPT.lower()
        assert "tipo de instalación" in prompt
        assert "contexto" in prompt
