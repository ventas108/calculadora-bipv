# Propuesta — Tensión máxima de sistema del módulo en el límite del Voc

**Estado:** validación

## Objetivo

Que ningún string supere la tensión de su módulo ni la del inversor, y que
la app diga cuál de los dos límites manda.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 («si hazlo preparalo asi»).

- `calculos/tension_modulo.py`: `v_sistema_modulo(panel)` y
  `limite_voc(panel, inversor)` = el menor entre el Vdc máximo del inversor y
  la tensión de sistema del módulo, con su origen.
- Usar ese límite en `evaluar_compatibilidad_string`, `optimizar_n_serie`,
  `curva_electrica_temperatura`, el comparador (filtro y mejor N),
  `rango_n_serie` y la validación por grupo de Vista 3D, `margen_voc`, la
  ficha RETIE y el reporte. Los textos dicen «tensión máxima del módulo»
  cuando manda el módulo.
- Catálogo de paneles: columna `VsistemaMaxV` (la crea el guardado), campo
  en el formulario y en la tabla de edición, y lectura desde la ficha PDF.
  Sin el dato en el Excel se usa el de `tecnologias_bipv` (familia
  ASP-ST1: 1.000 V).
- Manual del Asistente: sección de la regla y sección 108 con la corrida de
  Teusaquillo (Spec `07/manual-corrida-teusaquillo`).

## Alternativas descartadas

- Escribir la columna en `paneles_catalogo.xlsx` del repositorio: el `git
  pull` del servidor fallaría porque ese Excel se edita allá.
- Solo un aviso sin cambiar el límite: el optimizador seguiría proponiendo
  8 en serie.

## Fuera de alcance

- Cambiar el NOCT del Excel (se corrige en el servidor desde 📋 Catálogo de
  Paneles; la ficha no lo trae).
- Revisión automática del fusible máximo de string del módulo.
