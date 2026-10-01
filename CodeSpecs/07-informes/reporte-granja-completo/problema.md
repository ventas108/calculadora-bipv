# Spec — Reporte PDF de Granja FV completo y ficha del inversor

**Estado:** validación

## Alcance de la fase

📄 Reporte PDF de proyectos de granja (gráficas de 🌾 Granja FV), textos y
datos del reporte que no correspondían al proyecto, y revisión de la ficha
del inversor en 📐 Dimensionamiento.

## Problema a resolver

Revisión pedida por el usuario (1-oct-2026) con el reporte real de la Granja
Solar Apartadó (Urabá): «lo que no veo: la gráfica 3D del despliegue de los
paneles, es decir los ítems 8 y 9; ponte en el lugar del cliente y verifica
coherencias y qué puede estar faltando».

- Faltaban la **vista 3D del campo** (sección 9 de 🌾 Granja FV) y el **plano
  eléctrico** (sección 8), además de la luz en el suelo, el mapa de sombra
  mensual, el paso de la maquinaria y las revisiones de coherencia del campo.
- «Factor Mismatch aplicado 100 %» contradecía el diagrama de pérdidas del
  mismo reporte (calidad del módulo 3 % y mismatch 2 % aplicados).
- La altitud salía siempre «—»: el reporte leía `alt_m`, que ninguna página
  guarda.
- Textos de fachada en una granja: «Área de fachada», «90° = fachada
  vertical», «Módulo BIPV», «POA bruta (fachada)», «para fachadas verticales
  POA es menor que GHI» (aquí era mayor), «entregada al edificio», «Bogotá»,
  «módulos CdTe», «un proyecto de 100 m²».
- Sin aviso con la suciedad en 0 %.
- El catálogo traía el Growatt MAX 100KTL3 LV con 1.500 V DC y MPPT
  200–1.300 V; la ficha oficial que envió el usuario dice 1.100 V y
  180–1.000 V. La app daba 🟢 a 28 en serie (Voc en frío 1.386 V).

## Contexto

Continúa las Specs `07/reporte-produccion-completo` (#96) y
`07/reporte-multisuperficie` (#97).
