# Diagnóstico Honesto: Brechas entre Análisis POA y Simulador de Energía

## Estado Actual — Lo que realmente pasa

### El Análisis POA (botón "Análisis POA") calcula:
1. **POA horario real** con modelo Liu-Jordan completo (o Perez mejorado)
2. **Componentes separadas**: directa, difusa, reflejada — mes a mes
3. **Temperatura mensual real** del EPW
4. **Parámetros configurables**: inclinación, azimut, albedo, modelo (Liu-Jordan vs Perez)
5. Usa `calculateHourlyPOA()` con ángulos solares reales, DNI, DHI, GHI del EPW

### El Simulador de Energía recibe `poaData` de Home.tsx, que calcula:
1. **POA simplificado**: `directComponent = avgDirect × cos(tiltRad)` — un promedio mensual plano
2. **Sin ángulos solares horarios**: no usa posición solar real, solo cos(latitud)
3. **Inclinación fija**: siempre usa latitud como tilt, ignora el tilt del Análisis POA
4. **Azimut ignorado**: siempre asume 0° (Sur), ignora el azimut del Análisis POA
5. **Albedo fijo**: siempre 0.2, ignora el albedo del Análisis POA
6. **Modelo fijo**: siempre Liu-Jordan simplificado, ignora opción Perez
7. **Wind speed = 1 m/s**: hardcodeado, ignora viento real del EPW
8. **NOCT genérico**: `calculateCellTemperature` usa eta=0.15 fijo, no la eficiencia real del panel

## Las 7 Brechas Críticas

| # | Brecha | Impacto |
|---|--------|---------|
| 1 | **POA del Simulador NO usa el cálculo horario del Análisis POA** — recalcula con fórmula simplificada | Subestima/sobreestima POA hasta 15-20% |
| 2 | **Inclinación/Azimut desconectados** — el usuario ajusta en POA pero el Simulador ignora esos valores | Producción calculada no refleja la orientación real |
| 3 | **Albedo ignorado** — siempre 0.2, pero POA permite ajustarlo | Error en componente reflejada |
| 4 | **Modelo Perez ignorado** — POA ofrece Perez pero Simulador siempre usa Liu-Jordan simplificado | Pierde precisión en difusa circunsolar/horizonte |
| 5 | **Viento real ignorado** — EPW tiene windSpeed mensual, Simulador usa 1 m/s fijo | T_cell sobreestimada (viento enfría paneles) |
| 6 | **T_cell usa eficiencia genérica** — eta=0.15 fijo en vez de la eficiencia real del panel seleccionado | Error en cálculo de temperatura de celda |
| 7 | **Componentes directa/difusa/reflejada se pierden** — el Simulador solo usa totalPOA | No permite análisis de sensibilidad por componente |

## Plan de Corrección

### Corrección 1: Conectar POA real al Simulador
- Reemplazar el cálculo simplificado de `poaData` en Home.tsx por el cálculo horario real del POAAnalyzer
- Usar los mismos parámetros (tilt, azimut, albedo, modelo) del POA en el Simulador

### Corrección 2: Pasar windSpeed real del EPW
- Extraer windSpeed mensual promedio del EPW
- Pasarlo al motor de producción para calcular T_cell con viento real

### Corrección 3: Usar eficiencia real del panel en T_cell
- Pasar la eficiencia del panel seleccionado a calculateCellTemperature
- En vez de eta=0.15 fijo, usar panelSpecs.efficiency

### Corrección 4: Sincronizar parámetros POA ↔ Simulador
- Elevar tilt, azimut, albedo, usePerez a estado compartido en Home.tsx
- Cuando el usuario ajusta en POA, el Simulador se actualiza automáticamente

### Corrección 5: Mostrar desglose de componentes en el Simulador
- Agregar tarjetas de directa/difusa/reflejada en el resumen del Simulador
- Permitir ver qué porcentaje de la producción viene de cada componente
