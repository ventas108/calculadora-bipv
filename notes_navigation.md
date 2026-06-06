# Análisis del Problema de Navegación

## Problema Principal:
Las pestañas de PVWatts Satelital, PVGIS Real, Heatmap Irradiancia, Simulador Energía, Reporte, 
Radiación Solar, Optimizador, y Análisis POA están **OCULTAS** detrás de la condición:
```
{weatherData && ( ... )}
```

Esto significa que el usuario SOLO ve estas pestañas si primero carga un archivo EPW 
en "Datos Meteorológicos". Sin archivo EPW, no ve PVWatts, PVGIS, ni nada.

## Pestañas siempre visibles (sin EPW):
1. Calculadora
2. Plantillas
3. Ciudades
4. Mapa
5. Datos Meteorológicos

## Pestañas ocultas (requieren EPW):
6. Radiación Solar
7. Optimizador
8. Análisis POA
9. Simulador Energía
10. Generar Reporte
11. Heatmap Irradiancia
12. PVGIS Real
13. PVWatts Satelital

## Además:
- PVWatts y PVGIS también requieren `selectedCity` para renderizarse (líneas 521, 531)
- Heatmap también requiere `selectedCity`

## Solución:
PVWatts Satelital y PVGIS Real NO deberían requerir weatherData (archivo EPW) para ser visibles.
Son fuentes de datos independientes que pueden funcionar sin EPW.
Deberían ser siempre visibles, o al menos visibles cuando hay selectedCity.
