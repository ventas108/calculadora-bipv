# Spec — Parámetros de Financiero que se conservan y se guardan con el proyecto

**Estado:** validación

## Alcance de la fase

App Streamlit (`bipv_python/`): campos de entrada de `pages/7_💰_Financiero.py`
y su guardado con `calculos/proyectos_manager.py`. Sin cambios de cálculo.
Evidencia del 27-sep-2026 con el proyecto de un cliente en Bogotá.

## Problema a resolver

1. **La tarifa de excedentes se perdía.** El campo usaba una `key` de widget:
   Streamlit borra ese valor al abrir otra página. Al ir a 🏠 Proyecto a
   guardar, el 800 escrito no llegaba al archivo; al cargar el proyecto (y al
   volver a Financiero en la misma sesión) el campo mostraba la tarifa de
   compra, 1.200. Reproducido con AppTest: 800 → otra página → 1.200.
2. **Otros parámetros volvían a su valor por defecto.** Estructura (USD/kWp),
   instalación (%), imprevistos (%), escalación de tarifa y de O&M, O&M
   (%CAPEX), WACC, horizonte y tasa de renta eran campos sin `key` con un
   `value=` fijo: cada visita a la página los devolvía al valor por defecto y
   no se guardaban con el proyecto.

## Contexto

- La tarifa de compra ya se conserva con una clave de datos global
  (`calculos/tarifa_utils.tarifa_widget`).
- `calculos/campos_editor.sincronizar_campo` ya resuelve el mismo problema en
  los editores de 🗺️ Vista 3D.
- `proyectos_manager.guardar_proyecto_actual` guarda las claves de
  `session_state` salvo las excluidas y las que empiezan por `_`.
