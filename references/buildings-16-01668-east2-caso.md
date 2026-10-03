# Caso externo East2 — validación del Motor Óptico

## Fuente

- Artículo: *Dealing with Shadows When Modelling BIPV Façades with Conventional PV Tools*.
- DOI: `10.3390/buildings16091668`.
- PDF local: `buildings-16-01668-v2.pdf`.
- SHA-256 del PDF: `39683bfdaecc085a3c9e75308350d528cead1e6303f51b7bfae450e899f41e1d`.
- Caso de referencia: East2, Building 42, campus CIEMAT, Madrid.

## Objetivo

Usar East2 como validación externa del componente óptico, separando:

1. POA geométrica sin sombreado.
2. Factor de sombreado por azimut y elevación.
3. POA efectiva después del sombreado.
4. Producción eléctrica como comparación posterior, no como criterio exclusivo del Motor Óptico.

El caso no debe usarse para calibrar parámetros hasta disponer de los insumos
originales y de una comparación reproducible.

## Datos confirmados

| Campo | Valor | Estado |
|---|---|---|
| Latitud | `40.45° N` | Publicado |
| Longitud | `-3.74°` | Publicado |
| Orientación del edificio | `7.35°` hacia el sureste | Publicado |
| Superficie | East2 | Publicado |
| Módulo | SunPower E20-327 | Publicado |
| Potencia del módulo | `327 W` | Publicado |
| Eficiencia del módulo | `20.1%` | Publicado |
| Módulos del arreglo | `14` | Publicado |
| Configuración | `7S x 2P` | Publicado |
| Azimut del arreglo | `82.65°` | Publicado |
| Inclinación | `90°` | Inferido por fachada vertical; confirmar con los autores |
| Inversor | Fronius IG Plus 50 V-1 | Publicado |
| Albedo | `0.2` | Publicado |
| Periodo de medición | `2017-2023` | Publicado |
| Resolución temporal | Horaria | Publicado |
| Fuente de irradiancia | CAMS: GHI, DNI y DHI | Publicado |
| Temperatura y viento | PVGIS/ERA5 | Publicado |
| DSM | LiDAR, resolución `1 m` | Publicado; archivo ausente |

## Sombreado

El artículo publica para East2 una tabla de factor de sombreado con azimut de
`-180°` a `180°` en pasos de `20°` y elevación de `0°` a `90°` en pasos de
`10°`. El factor está definido entre `0` (sin sombra) y `1` (sombra total).

La matriz completa debe transcribirse desde la Tabla 4 antes de crear un
fixture automatizado. No se deben completar celdas ausentes por interpolación
sin registrar esa decisión y su impacto.

## Resultados de referencia

El artículo no publica una energía anual agregada de East2 en las tablas
principales. Sí publica métricas de comparación:

- SAM 3D: nRMSE anual `26.6%`.
- SAM DSM: nRMSE anual `6.8%`.
- PVsyst 3D: nRMSE anual `7.5%`.
- PVsyst DSM: nRMSE anual `11.6%`.

Estos valores son referencias del error de producción de las herramientas frente
a mediciones, no tolerancias universales para la aplicación.

## Bloqueos de reproducibilidad

No convertir este caso en una prueba de homologación completa hasta obtener o
reconstruir con trazabilidad:

- matriz completa de East2 en formato estructurado;
- serie meteorológica horaria exacta;
- geometría o DSM usado en el artículo;
- parámetros eléctricos completos de módulo e inversor;
- datos horarios medidos de producción;
- definición exacta de la conversión de factor de sombra a pérdida.

## Secuencia de validación

1. Ejecutar una prueba óptica determinista con la matriz East2 transcrita.
2. Comparar POA sin sombra y POA sombreada por intervalo temporal.
3. Reportar pérdida óptica absoluta y relativa.
4. Solo después ejecutar la cadena térmica y eléctrica.
5. Reportar por separado error óptico, térmico, eléctrico y total.
6. Comparar MBE, RMSE, nRMSE y `R^2` con las Tablas 5–7 del artículo.

## Estado

`Preparado — pendiente de transcripción verificada de Tabla 4 e insumos
meteorológicos.`