# Análisis del Excel CSV para importación en Puntos de Análisis

## Estructura del archivo (11 columnas):
1. **Evento**: Equinoccio de Marzo, Solsticio de Junio, Equinoccio de Septiembre, Solsticio de Diciembre
2. **Mes**: Marzo, Junio, Septiembre, Diciembre
3. **Dia**: 20, 21, 22, 21
4. **Hora**: 07:30, 08:30, 09:30, ... 17:30
5. **Altura Solar (deg)**: float (ej: 19.96, 34.85, etc.)
6. **Acimut Solar (deg)**: float (ej: 92.35, 94.46, etc.)
7. **Obstaculo**: string (ej: "Fachada NE (az.normal=15.0°)")
8. **FS_geometrico**: float (0.0 en todos los datos)
9. **FS_climatico**: float (0.0 - 0.877)
10. **FS**: float (factor de sombreado total = max(FS_geom, FS_clim))
11. **Situacion**: string (Muy nublado, Parcialmente nublado, Cielo despejado / casi claro, Cielo cubierto)

## Total: 88 filas de datos (sin encabezado)
## Eventos: 4 días críticos × múltiples horas × múltiples fachadas

## Estructura actual de la tabla "Puntos de Análisis":
Necesito revisar ShadingCalculator.tsx para ver qué campos tiene actualmente.
