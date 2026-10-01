# Spec — Comparador y Dimensionamiento con el mismo margen de Voc

**Estado:** validación

## Alcance de la fase

Criterio de margen del Voc en frío en ⚖️ Comparador de Inversores
(`mejor_n_por_inversor`) y en el margen del 📄 Reporte PDF.

## Problema a resolver

Con el Growatt MAX 100KTL3 LV corregido a su ficha (1.100 V), 📐
Dimensionamiento daba «N óptimo = 20» (margen del 7,5 %, `UMBRAL_ALERTA_PCT`)
y el comparador proponía 22 en serie (margen del 3 % y reparto exacto
primero): Voc en frío 1.089 V, 11 V de margen. Dos recomendaciones distintas
para el mismo proyecto (captura del usuario, 1-oct-2026).

## Contexto

Continúa la Spec `03/comparador-inversores-completo` (#99).
