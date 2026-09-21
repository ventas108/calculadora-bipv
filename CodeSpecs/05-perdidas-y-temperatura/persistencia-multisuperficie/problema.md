# Spec — Persistencia multi-superficie

**Estado:** propuesta para implementación
**Fecha:** 2026-09-21
**Dependencia:** `transicion-multisuperficie`

## Problema

El modo físico multi-superficie ya puede calcular, comparar y adoptar resultados durante una sesión de Streamlit, pero el flujo de Guardar/Cargar proyecto no conserva ni verifica ese estado completo. Un reinicio, una pestaña nueva o una carga posterior puede perder superficies, geometría, sombra, POA, asignaciones eléctricas o resultados físicos.

Restaurar únicamente cifras calculadas es inseguro: una cifra puede corresponder a otro TMY, geometría, inversor, `N_serie`, sombra o configuración eléctrica. El proyecto debe distinguir entradas persistidas, resultados calculados, firmas de vigencia y metadatos del proveedor.

## Objetivo

Definir e implementar un payload canónico para guardar y restaurar el estado físico multi-superficie con verificación completa y comportamiento todo-o-nada. El modelo simplificado continúa siendo el default y no debe cambiar si `multisup_activo` es falso.

## No objetivos

- No convertir el modo físico en default.
- No rediseñar los consumidores downstream.
- No activar Motor Óptico independiente por superficie.
- No restaurar payloads legacy mediante defaults silenciosos.
- No desplegar hasta completar pruebas y revisión.

## Riesgo que se elimina

Una carga parcialmente válida no debe publicar `multisup_*`, resultados físicos ni datos consumibles por Finanzas, CO₂, Presupuesto, Baterías o Reporte. Si una validación falla, se conserva el estado previo y se informa la causa concreta.
