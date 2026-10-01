# Spec — Comparador de Inversores completo: mejor N por inversor, precios y adopción

**Estado:** validación

## Alcance de la fase

⚖️ Comparador de Inversores: filtro de compatibilidad, configuración por
inversor, precios y botón de adopción.

## Problema a resolver

Revisión pedida por el usuario (1-oct-2026): «¿continuamos con ese inversor?
Si hay dudas podemos encontrar otro… hay un módulo que se llama Comparador
de Inversores, ¿cómo le sacamos el máximo provecho? Revísalo». Con la Granja
Apartadó (308 × JAM66D46-720/LB) se encontró:

1. El filtro revisaba el Vmp solo a la temperatura de trabajo; 📐
   Dimensionamiento también lo revisa a la extrema.
2. No usaba la revisión de la ficha del inversor (Spec
   `07/reporte-granja-completo`).
3. Comparaba todos los inversores con el mismo N en serie.
4. No mostraba el margen de Voc ni si los módulos se repartían exactos.
5. Sin precio en el catálogo (ningún inversor lo tiene) daba TIR y LCOE no
   comparables.
6. «Adoptar» solo guardaba inversor, N y unidades: en modo «1 string por
   MPPT» Dimensionamiento volvía a 2 strings por MPPT (46,5 A > 40 A).

## Contexto

Continúa la corrección del Growatt MAX 100KTL3 LV a su ficha oficial
(1.100 V, MPPT 180–1.000 V, 40 A) y el rediseño a 22 en serie.
