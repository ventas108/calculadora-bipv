# Propuesta — Reporte PDF de proyectos multi-superficie (🗺️ Vista 3D)

**Estado:** validación

## Objetivo

Una sola energía del proyecto en el reporte y todo el diseño de 🗺️ Vista 3D
explicado para el cliente.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 («Prepara la Spec del reporte
multi-superficie (Vista 3D)»).

- `cadena_perdidas_multisup.registro_publicacion` guarda también
  `desglose` (la misma `tabla_desglose` de la página).
- `calculos/reporte_multisuperficie.py` (sin Streamlit, solo lee lo
  publicado): `activo`, `resumen`, `tabla_superficies`, `filas_por_panel`,
  `tabla_inversores`, `cadena_por_superficie`, `cruces`, `mensual`.
- 📄 Reporte PDF: con energía multi-superficie publicada, «Producción Anual
  del Proyecto — Multi-Superficie» (resumen y gráfica mensual) reemplaza a las
  secciones de superficie única (producción, diagrama de pérdidas, sistema
  eléctrico y compatibilidad de Dimensionamiento); la sección multi-superficie
  suma superficies completas, paneles, inversores, pérdidas por superficie y
  cruces.
- Manual del Asistente, sección 102.

## Alternativas descartadas

- Mostrar las dos energías con una nota: el cliente seguiría viendo dos
  cifras.
- Recalcular la cadena en el reporte: la POA por superficie no se guarda con
  el proyecto y serían dos cálculos de lo mismo.

## Fuera de alcance

- Recorte en kWh por inversor (se ve en % por superficie en la cadena).
- Vista 3D en imagen dentro del PDF.
