# Proposal: CodeSpec del Módulo Producción

## Objetivo

Formalizar la fuente de verdad energética de `bipv_python/pages/6_📊_Produccion.py` y sus motores para que cada resultado oficial sea reproducible, vigente y coherente entre sus series horaria, mensual y anual.

## Estado actual

Producción integra Recurso Solar, Dimensionamiento, Motor Óptico, Mismatch, Motor IV, bypass, pérdidas óhmicas e inversor. Publica resultados consumidos por Financiero, Balance, Reporte PDF, CO₂ y Asistente. La auditoría estática inicial del 2026-09-17 confirmó dos caminos incoherentes que todavía deben convertirse en pruebas automatizadas rojas:

1. `produccion_ok` permite reutilizar `res_produccion` después de cambiar panel, inversor, número de módulos, eficiencia o modo IV sin una firma completa de vigencia.
2. Con Motor Óptico activo, `poa_sin_termico_df` ya contiene soiling, pero `factor_global_mismatch` lo incluye nuevamente antes del modelo eléctrico.

La misma inspección confirmó dos brechas de bypass: Producción no contrasta su panel/strings/módulos antes de restarlo y una nueva pérdida cero puede dejar viva `E_ac_anual_kWh_bypass`. También deben validarse la igualdad anual/mensual/horaria, la restauración persistente y la prioridad de multi-superficie.

## Fase 1 aprobable

La primera implementación se limita a:

1. impedir que una configuración visible nueva reutilice un resultado anterior;
2. aplicar soiling una sola vez con Motor Óptico activo, preservando la clave histórica para otros consumidores;
3. verificar la vigencia eléctrica del bypass y limpiar su energía corregida cuando la pérdida nueva sea cero;
4. ampliar la huella persistida para rechazar agregados de otra configuración.

El contrato temporal completo y la reclasificación de multi-superficie quedan en fases posteriores para evitar mezclar una corrección de vigencia con una migración de consumidores.

## Alcance

- Selección y trazabilidad de la POA que alimenta el motor eléctrico.
- Vigencia de configuración y publicación atómica de resultados.
- Coherencia entre los motores base, JRC/Huld, SDM PVsyst y Motor IV.
- Aplicación única de pérdidas ópticas, térmicas y eléctricas.
- Contrato oficial base, bypass y multi-superficie.
- Persistencia e invalidación de consumidores downstream.

## Fuera de alcance inicial

- Recalibrar parámetros físicos del catálogo.
- Sustituir NOCT por Faiman.
- Incorporar una curva nueva de eficiencia del inversor.
- Cambiar la geometría o el motor de sombreado.
- Refactorizar frontend React o backend Node.

## Criterio de implementación

Ningún cálculo se modifica hasta que una prueba dirigida reproduzca la brecha. El primer cambio debe cerrar vigencia, doble soiling y bypass obsoleto sin alterar las API públicas de los motores ni los resultados válidos existentes.