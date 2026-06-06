# Diagnóstico Honesto: Optimizador de Orientación → Simulador de Energía

## Estado Actual: DESCONECTADOS

El Optimizador de Orientación y el Simulador de Energía **NO están conectados interactivamente**.
Son módulos completamente independientes que no comparten datos entre sí.

## Datos que calcula el Optimizador (y NO se usan en el Simulador)

| Dato del Optimizador | Disponible | Usado en Simulador | Impacto |
|---|---|---|---|
| Tilt óptimo para máxima irradiancia | Sí (slider) | NO — Simulador usa su propio installTilt | CRÍTICO |
| Azimut óptimo | Sí (slider) | NO — Simulador usa su propio installAzimuth | CRÍTICO |
| Irradiancia mensual en plano inclinado | Sí (monthlyProduction) | NO — Simulador recalcula POA desde Home.tsx | ALTO |
| Componentes directa/difusa por mes | Sí (direct/diffuse) | NO | MEDIO |
| Variación estacional (%) | Sí (stats.variance) | NO | BAJO |
| Promedio mensual W/m² | Sí (stats.avgMonthly) | NO | MEDIO |

## Datos INDISPENSABLES del Optimizador para mejorar el Simulador

### 1. Tilt y Azimut Óptimos (CRÍTICO)
- El Optimizador calcula la irradiancia para cualquier combinación tilt/azimut
- El Simulador tiene su propio tilt/azimut que NO se sincroniza
- **Solución**: Botón "Aplicar orientación óptima al Simulador" + sincronización bidireccional

### 2. Irradiancia Mensual Optimizada en Plano Inclinado (CRÍTICO)
- El Optimizador calcula irradiancia horaria real con modelo de ángulo de incidencia
- El Simulador recalcula POA en Home.tsx con calculateHourlyPOA (duplicación)
- **Solución**: Compartir los datos POA mensuales del Optimizador directamente

### 3. Búsqueda Automática del Óptimo (NUEVO - MUY ALTO IMPACTO)
- Actualmente el Optimizador solo tiene sliders manuales
- **Solución**: Implementar barrido automático tilt×azimut para encontrar el máximo global
- Resultado: tilt_opt, azimut_opt, POA_max, ganancia vs horizontal

### 4. Factor de Producción Real vs Óptimo (ALTO)
- estimateProductionFactor() usa cos(diff) simplificado
- **Solución**: Calcular factor real = POA(actual) / POA(óptimo) con datos horarios

### 5. Restricciones de Instalación (ALTO)
- El tipo de instalación (fachada, cubierta, pérgola) limita tilt/azimut
- El Optimizador no conoce estas restricciones
- **Solución**: Pasar tiltRange del InstallationConfig al Optimizador para optimizar DENTRO de las restricciones reales

### 6. Temperatura Mensual Real para cada Orientación (MEDIO)
- El Optimizador no calcula T_cell por orientación
- Diferentes orientaciones reciben diferente irradiancia → diferente T_cell → diferente P_exp
- **Solución**: Calcular T_cell mensual para la orientación seleccionada

## Plan de Implementación

1. Agregar callback onOptimalFound al OrientationOptimizer
2. Implementar búsqueda automática del óptimo (barrido tilt×azimut)
3. Agregar botón "Enviar al Simulador" con datos completos
4. Sincronizar bidireccional: Optimizador ↔ Home.tsx ↔ Simulador
5. Pasar restricciones de instalación al Optimizador
6. Mostrar banner en Simulador con datos del Optimizador aplicados
