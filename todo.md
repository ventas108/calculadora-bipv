# Project TODO

- [x] Tabla dinámica de cálculo de factores de sombreado
- [x] Importación y exportación CSV
- [x] Plantillas predefinidas de análisis
- [x] Carga de datos meteorológicos EPW
- [x] Gráfico de radiación solar directa vs difusa
- [x] Optimizador de orientación (azimut e inclinación)
- [x] Modelo Liu-Jordan para cálculo de radiación POA
- [x] Simulador de producción energética kWh
- [x] Biblioteca de múltiples ciudades con datos EPW
- [x] Comparador de ciudades
- [x] Integración con Google Maps
- [x] Generador de reportes PDF
- [x] Heatmap de irradiancia solar
- [x] Integración PVGIS API (datos reales satelitales)
- [x] Upgrade a full-stack con proxy backend para PVGIS
- [x] Corrección de heatmap de irradiancia (HeatmapLayer + fallback círculos)
- [x] Corrección de proxy PVGIS (sin CORS, acceso directo desde backend)
- [x] Corregir error 400 de PVGIS al analizar desde el mapa (raddatabase PVGIS-NSRDB no soportada en v5.3)
- [x] Reparar ubicador geográfico de irradiancia (reescrito con datos PVGIS reales + círculos coloreados + marcadores)
- [x] Validar simulaciones PVGIS con datos EPW de Medellín (EPW GHI=1842.7, PVGIS GHI≈1716.7 - coherente)
- [x] Mejorar componentes de la calculadora dinámica (corregido NSRDB→ERA5, props, descripciones)
- [x] Corregir error insertBefore en PVGISAnalyzer (Fragment condicional eliminado, normalización claves PVGIS corregida)
- [x] BUG PERSISTENTE: Error insertBefore en PVGISAnalyzer - CORREGIDO DEFINITIVAMENTE:
  - Home.tsx: PVGISAnalyzer ahora se monta una vez y se oculta/muestra con CSS display:none/block (patrón keep-alive)
  - PVGISAnalyzer.tsx: Todos los gráficos Recharts siempre montados, ocultos con display:none cuando no hay datos
  - Eliminados todos los patrones {condition && <Component>} para gráficos y tablas
  - index.html: Agregado translate="no" y meta notranslate para prevenir manipulación DOM por extensiones
  - Verificado: 0 errores en consola tras múltiples consultas PVGIS y cambios de pestaña
- [x] Sistema de plantillas de tecnología de paneles solares en PVGIS Real
- [x] Plantillas predefinidas: c-Si, CdTe, CIS, BIPV, HJT, a-Si con datos técnicos reales
- [x] Editor de plantillas personalizadas (eficiencia, coef. temperatura, NOCT, degradación, etc.)
- [x] Enlazar datos técnicos de plantillas a cálculos de producción PV reales de PVGIS
- [x] Recalcular producción PV con parámetros técnicos reales del panel seleccionado
- [x] Integrar 17 productos BIPV HIITIO (TOPCon Flex, HJT Curtain Wall, HJT Wall Tile, CdTe SemiT, CdTe BIPV, CIGS) como plantillas
- [x] Incluir datos técnicos reales de tabla HIITIO: Pmax, Voc, Isc, Vmp, Imp, eficiencia, coef. temp, dimensiones, peso
- [x] Pasar pvtechchoice y mountingplace a la API PVGIS según tecnología seleccionada
- [x] Mostrar producción corregida con parámetros reales del panel HIITIO seleccionado
- [x] Integrar factores de sombreado (FS) de la calculadora al Simulador de Producción
- [x] Conectar plantillas HIITIO al Simulador de Producción via PanelTechSelector completo (catálogo HIITIO + plantillas personalizadas)
- [x] Mostrar resumen de integración: sombreado + meteorología + panel seleccionado en el simulador
- [x] Reutilizar PanelTechSelector en Simulador de Producción para soportar catálogo completo y plantillas personalizadas
- [x] Cálculo automático de área y número de paneles: campo de área disponible (m²) que calcula cuántos paneles caben según dimensiones del panel seleccionado y actualiza la cantidad en el simulador
- [x] Auto-cálculo de altura solar y azimut solar en la Calculadora de Factores de Sombreado usando datos EPW (latitud, longitud, zona horaria)
- [x] Función de posición solar (Solar Position Algorithm) basada en coordenadas y fecha/hora
- [x] Auto-rellenar campos de altura y azimut solar al seleccionar mes, día y hora en la tabla de sombreado
- [x] Corrección de índices del parser EPW (latitud/longitud estaban desplazados por código WMO)
- [x] Tabla dinámica de costos BIPV en Parámetros Financieros del Simulador de Producción
- [x] Costo unitario del panel × cantidad de paneles (según área evaluada) como primera línea de la tabla
- [x] Líneas editables para costos de: estructura/montaje, inversores, cableado, protecciones, ingeniería/diseño, permisos/licencias, transporte, mano de obra, imprevistos
- [x] Totalización automática que reemplace el campo fijo "Costo del Sistema" en el análisis financiero
- [x] Precios unitarios de referencia para paneles HIITIO en panelTechnologies.ts
- [x] Fila predeterminada de Imprevistos/Contingencia (5%) auto-calculada en tabla de costos BIPV
- [x] Configuraciones predefinidas de instalación BIPV (fachada, cubierta inclinada, cubierta plana, pérgola, marquesina)
- [x] Ajuste automático de inclinación según tipo de montaje seleccionado
- [x] Ajuste automático de pérdidas del sistema según configuración de instalación
- [x] Ajuste automático de costos de estructura según tipo de montaje
- [x] Selector visual de configuración de instalación en el Simulador de Producción
- [x] Diagrama de Trayectoria Solar (Sun Path Diagram) interactivo SVG
- [x] Visualización del recorrido del sol sobre el horizonte para cada mes del año
- [x] Clic interactivo en cualquier punto de la trayectoria para auto-rellenar altura y azimut en la tabla de sombreado
- [x] Integración con datos EPW (latitud, longitud) para cálculo preciso de trayectorias
- [x] Indicador visual de la posición actual del sol y puntos de análisis existentes en la tabla
- [x] Modo dibujo de polígonos de sombra (obstáculos) sobre el diagrama de trayectoria solar
- [x] Herramientas de dibujo: agregar vértices con clic, cerrar polígono, editar/eliminar obstáculos
- [x] Nombrar obstáculos (Edificio, Árbol, Montaña, etc.) con colores diferenciados
- [x] Cálculo automático de intersección polígono-trayectoria para determinar horas sombreadas
- [x] Actualización automática del área sombreada en la tabla de puntos de análisis según obstáculos dibujados
- [x] Panel de gestión de obstáculos (lista, editar nombre, eliminar, toggle visibilidad)
- [x] Persistencia de obstáculos en estado del componente y exportación/importación
- [x] Importación de archivos JSON de Andrew Marsh Site Designer
- [x] Parser de formato Site Designer: extraer bloques sólidos (obstáculos) y superficies de análisis (isGrid)
- [x] Conversión de bloques 3D (coordenadas cartesianas mm) a polígonos solares (azimut, altitud) usando geometría de proyección
- [x] Detección automática del punto de observación desde la superficie de análisis (isGrid) del archivo
- [x] Generación de polígonos de silueta angular para cada bloque sólido visto desde el punto de observación
- [x] Integración de obstáculos importados con el sistema existente de obstáculos del diagrama solar
- [x] UI de importación con botón dedicado, previsualización de bloques importados y resumen
- [x] Tests unitarios para el parser y la conversión de coordenadas 3D a solares
- [x] Importación de JSON de Sun Path 3D (settings de Andrew Marsh)
- [x] Parser de formato Sun Path 3D: extraer ubicación (lat, lon, timezone), fecha/hora, centro del domo y northOffset
- [x] Aplicar automáticamente ubicación y zona horaria del Sun Path 3D a la calculadora (equivalente a datos EPW)
- [x] Aplicar fecha/hora del Sun Path 3D como punto de análisis inicial
- [x] UI de importación con previsualización de datos extraídos del Sun Path 3D
- [x] Importación de archivos OBJ (modelos 3D de sombra)
- [x] Parser de formato OBJ: extraer vértices y caras de malla triangular/poligonal
- [x] Conversión de geometría OBJ 3D a polígonos de obstáculo en coordenadas solares (azimut, altitud)
- [x] Detección de punto de observación (centro del modelo o configurable)
- [x] Generación de siluetas angulares para cada objeto/grupo del OBJ
- [x] Integración de obstáculos OBJ con el sistema existente de obstáculos del diagrama solar
- [x] UI de importación OBJ con botón dedicado y previsualización de objetos importados
- [x] Tests unitarios para ambos parsers
- [x] Tests unitarios para sunPath3DParser.ts y objParser.ts
- [x] Agregar 18 productos EINNOVA al catálogo de panelTechnologies con categorías propias
- [x] Agregar diagnóstico de compatibilidad EINNOVA por región climática colombiana (Caribe, Andina, Pacífica, Orinoquía, Amazonía, Insular)
- [x] Botón de selección de tecnología EINNOVA en el PanelTechSelector con indicador de compatibilidad regional
- [x] Integración de EINNOVA con cálculos de sombreado y dimensionamiento (misma interfaz que HIITIO)
- [x] Mostrar recomendación de compatibilidad (3=óptimo, 2=aceptable, 1=no recomendado) según ciudad/región seleccionada
- [x] Tests unitarios para datos EINNOVA (validar 18 productos, brand, categorías y compatibilidad regional)
- [x] Agregar regionalCompatibility a los 17 productos HIITIO según diagnóstico del Excel
- [x] Mapear familias HIITIO a productos: TOPCon Flex (H01-H05), HJT Curtain Wall (H06-H08), HJT Wall Tile (H09-H11), CdTe SemiT (H12-H15), CdTe BIPV (H16), CIGS (H17)
- [x] Mostrar filtros regionales y estrellas de compatibilidad para productos HIITIO (igual que EINNOVA)
- [x] Actualizar PanelTechSelector para mostrar diagnóstico regional en HIITIO
- [x] Actualizar tests unitarios para validar regionalCompatibility en HIITIO
- [x] BUG: Las tarjetas de ciudades no aparecen en la pestaña Datos Meteorológicos después de cargar un EPW
- [x] BUG: Pestaña Ciudades no carga archivos EPW ni genera tarjetas de almacenamiento
- [x] Conectar pestaña Ciudades con selectores dinámicos (weatherData, calculadora, simulador)
- [x] Auto-detección de región climática colombiana por coordenadas geográficas (lat/lon)
- [x] Función de clasificación geográfica: mapear lat/lon a las 6 regiones (Caribe, Andina, Pacífica, Orinoquía, Amazonía, Insular)
- [x] Integrar auto-detección con PanelTechSelector para filtrar productos BIPV por compatibilidad
- [x] Mostrar región detectada automáticamente en la UI con opción de override manual
- [x] Tests unitarios para la función de detección de región por coordenadas

## Prospector Solar Interactivo - Modelo Mulcue-Llanos
- [x] Crear librería mulcueLlanos.ts con fórmulas PR_max, PR_C y producción anual
- [x] Crear componente SolarProspector con ficha de viabilidad al hacer clic en punto del heatmap
- [x] Integrar panel BIPV seleccionado (del catálogo) en el cálculo de producción
- [x] Tabla de factores FI por región colombiana e inclinación recomendada
- [x] Selector de factor de sombreado FS con tabla general
- [x] Temperatura de celda = Ta × 1.40 (40% sobre ambiente)
- [x] Comparador de ubicaciones (anclar 2-3 puntos del heatmap)
- [x] Tests unitarios para fórmulas Mulcue-Llanos verificados contra ejercicio 5

## Puente Prospector Solar → Simulador de Energía
- [x] Botón "Usar en Simulador" en la ficha del Prospector Solar
- [x] Interfaz de datos compartidos (GHI, PR, temperatura, región, FS) entre Prospector y Simulador
- [x] Callback en Home.tsx para recibir datos del Prospector y cambiar a vista Simulador
- [x] Pre-llenar campos del Simulador con datos del Prospector (panel, cantidad, inclinación)
- [x] Banner informativo en Simulador indicando que los datos provienen del Prospector Solar
- [x] Inyectar POA sintético basado en GHI del Prospector cuando hay weatherData existente (override)
- [x] Mostrar PR Mulcue-Llanos como referencia comparativa en el Simulador
- [x] Eliminar Math.random() del EPW sintético y usar construcción determinista
- [x] Probar flujo completo end-to-end en navegador

## Corrección Temperatura de Celda y Pérdidas por Alta Temperatura (Heatmap/Prospector)
- [x] Reemplazar T_cell = T_amb × 1.40 por fórmula NOCT estándar: T_cell = T_amb + (NOCT - 20) × G/800
- [x] Calcular pérdida por temperatura correctamente: loss_temp = γ × (T_cell - 25°C)
- [x] Usar NOCT del panel seleccionado (de panelTechnologies) en vez de valor fijo
- [x] Mostrar T_cell calculada y pérdida por temperatura en la ficha del Prospector
- [x] Actualizar mulcueLlanos.ts con fórmula NOCT estándar
- [x] Actualizar tests unitarios con nuevas fórmulas de temperatura
- [x] Verificar resultados contra ejemplo del Excel (T_c=65°C, γ=0.31%/°C → pérdida 12.4%)

## Slider de Irradiancia G en Prospector Solar
- [x] Agregar estado irradianceG con valor por defecto 800 W/m² al SolarProspector
- [x] Crear slider visual (200-1200 W/m²) con marcas de referencia (STC=1000, NOCT=800)
- [x] Recalcular T_cell, pérdida por temperatura y producción en tiempo real al mover el slider
- [x] Pasar irradianceG a calculateCellTemp y quickEstimate
- [x] Mostrar indicador visual del impacto de G en la ficha de resultados
- [x] Verificar compilación, tests y probar en navegador

## Gráfico de Sensibilidad G vs Producción en Prospector Solar
- [x] Generar datos de sensibilidad: calcular producción para G de 200 a 1200 W/m² (paso 50)
- [x] Crear mini-gráfico con Recharts (ComposedChart) mostrando curva G vs Producción anual
- [x] Marcar punto actual de G seleccionado en el gráfico con indicador visual
- [x] Marcar puntos de referencia NOCT (800) y STC (1000) en el gráfico
- [x] Mostrar tooltip interactivo con valores al pasar el mouse sobre la curva
- [x] Incluir eje secundario con T_cell y pérdida por temperatura
- [x] Integrar gráfico en la sección de Resultados del Prospector Solar
- [x] Tarjetas de resumen: @ NOCT, @ Actual, @ STC con energía y T_cell

## Corrección Fórmula P_exp Mulcue-Llanos (T_ref=21°C)
- [x] Implementar P_exp = P_nom × [1 + γ(T_c − 21)] × (G/1000) con T_ref=21°C
- [x] Aplicar P_exp en el cálculo de producción anual del Prospector Solar
- [x] Mostrar P_exp y potencia degradada por temperatura en la ficha de resultados
- [x] Actualizar quickEstimate para usar P_exp en vez de P_nom directo
- [x] Actualizar tests unitarios con la nueva fórmula P_exp (6 tests calculateExpectedPower + quickEstimate actualizado)
- [x] Verificar resultados: 193 tests pasan, build exitoso, TypeScript 0 errores

## Mejoras Simulador de Energía - Descartar Prospector y Datos de Campo
- [x] Hacer funcional el botón "Descartar" del banner Prospector Solar en el Simulador de Energía (limpiar prospectorData en Home.tsx via callback)
- [x] Al descartar, restaurar POA desde datos EPW originales (no sintéticos del Prospector)
- [x] Agregar sección "Mediciones de Campo" con campos editables: GHI (W/m²), T. Ambiente (°C), T. Celda (°C)
- [x] Los valores de campo sobreescriben datos EPW/Prospector en los cálculos de producción BIPV
- [x] Si T_cell se ingresa manualmente, se usa directamente en vez de calcularla con NOCT
- [x] Si solo se ingresa GHI y T_amb, T_cell se calcula automáticamente con fórmula NOCT del panel
- [x] Datos de campo integrados con factores de sombreado (FS) de la Calculadora (se siguen aplicando)
- [x] Coordenadas EPW de la zona mostradas como referencia en la sección de campo
- [x] Ecuaciones BIPV estándar (P_exp, PR, producción) aplicadas con los valores de campo
- [x] 7 tests unitarios de escenarios de campo (200 tests total), build exitoso, TypeScript 0 errores

## Integración Profunda: Análisis POA → Simulador de Energía
- [x] Elevar parámetros POA (tilt, azimut, albedo, usePerez) a estado compartido en Home.tsx
- [x] Reemplazar cálculo POA simplificado en Home.tsx por cálculo horario real (calculateHourlyPOA)
- [x] Pasar windSpeed mensual real del EPW al motor de producción (en vez de 1 m/s fijo)
- [x] Usar eficiencia real del panel seleccionado en calculateCellTemperature (en vez de eta=0.15 fijo)
- [x] Sincronizar tilt/azimut del Simulador (installTilt/installAzimuth) con el cálculo POA
- [x] Mostrar desglose de componentes POA (directa/difusa/reflejada) en el Simulador
- [x] Mostrar banner de origen de datos POA en el Simulador (modelo, parámetros, fuente)
- [x] Agregar tests unitarios (20 tests energyProduction.ts, 220 total)
- [x] Verificar build (exitoso) y TypeScript (0 errores)

## Sincronización Bidireccional: POAAnalyzer ↔ Simulador
- [x] Conectar POAAnalyzer a Home.tsx con props/callbacks para tilt, azimuth, albedo y usePerez
- [x] Sincronización bidireccional: cambios en Análisis POA actualizan el Simulador y viceversa
- [x] Verificar en navegador el flujo completo Análisis POA → Simulador (sincronización bidireccional implementada)

## Integración Optimizador de Orientación → Simulador de Energía
- [x] Agregar búsqueda automática del óptimo (barrido tilt×azimut grueso 5° + fino 1°) en el Optimizador
- [x] Agregar callback onSendToSimulator al OrientationOptimizer con OptimizerResult completo
- [x] Conectar OrientationOptimizer con estado compartido POA en Home.tsx (tilt, azimut sincronizados)
- [x] Pasar restricciones de instalación (tiltRange, azimuthLocked, installationType) al Optimizador
- [x] Agregar botón "Aplicar al Simulador" + "Aplicar Óptimo al Simulador" con datos POA mensuales
- [x] Mostrar banner cyan en Simulador con datos del Optimizador (tilt/az óptimo, POA, ganancia %)
- [x] Calcular ganancia porcentual vs orientación actual al encontrar el óptimo
- [x] Sincronización bidireccional: Optimizador ↔ Home.tsx ↔ Simulador (tilt, azimut)
- [x] 13 tests unitarios para búsqueda del óptimo + irradiancia inclinada (233 total)
- [x] Build exitoso, TypeScript 0 errores, 233 tests pasan

## Historial de Mediciones de Campo
- [x] Definir interfaz FieldMeasurementRecord con id, timestamp, label, GHI, T_amb, T_cell (manual o NOCT), P_exp, PR, tempLoss, contexto panel y coordenadas
- [x] Implementar hook useFieldMeasurementHistory con localStorage para persistencia entre sesiones
- [x] Agregar botón "Guardar Medición" que captura valores actuales de campo con fecha/hora y etiqueta
- [x] Mostrar tabla del historial ordenable por columna (fecha, GHI, T_amb, T_cell, P_exp, PR) con acción de cargar/eliminar
- [x] Permitir eliminar mediciones individuales del historial con confirmación
- [x] Permitir cargar una medición del historial para re-aplicarla como valores de campo activos (botón ojo)
- [x] Agregar gráfico temporal (Recharts LineChart) con GHI, T_cell, T_amb y P_exp, doble eje Y, agrupado por día
- [x] Permitir agregar etiqueta/nota a cada medición con campo de texto (máx 60 chars)
- [x] Exportar historial como CSV con BOM UTF-8 para Excel (botón CSV)
- [x] 16 tests unitarios para CSV, agrupación por día y estadísticas (249 total)
- [x] Build exitoso, TypeScript 0 errores, 249 tests pasan

## Alertas de Rendimiento en Mediciones de Campo
- [x] Crear motor de diagnóstico performanceDiagnostic.ts con 8 causas probables (suciedad, sombreado, degradación, temperatura, inversor, cableado, mismatch, baja irradiancia)
- [x] Definir umbrales de alerta: ok (<10%), leve (10-15%), moderada (15-25%), severa (25-40%), crítica (>40%)
- [x] Implementar análisis de causas ponderado por: GHI, T_cell, tipo de instalación, pérdidas del sistema, latitud
- [x] Agregar recomendaciones específicas por causa con categorías (ambiental, equipo, instalación, mantenimiento, diseño)
- [x] Mostrar PerformanceAlertPanel inline con health score circular, barra PR, causas expandibles con ranking
- [x] Agregar badges de estado (OK/Leve/Alerta/Severa/Crítica) en cada fila de la tabla del historial
- [x] Panel de diagnóstico expandible con causas ordenadas por probabilidad, categoría y recomendación de acción
- [x] 28 tests unitarios para el motor de diagnóstico (281 total)
- [x] Build exitoso, TypeScript 0 errores, 281 tests pasan

## Corrección Performance Ratio IEC 61724
- [x] Corregir PR: cambiar de E_AC/E_DC a PR = E_AC / (Yr × P_nom_kW) según IEC 61724
- [x] Calcular Reference Yield (Yr) = Σ(POA_i × horas_i) / G_ref(1000) correctamente
- [x] Calcular Final Yield (Yf) = E_AC / P_nom_kW
- [x] Corregir PR: cambiado de E_AC/E_DC (BOS efficiency) a Yf/Yr (IEC 61724) — error crítico corregido
- [x] Agregar PR corregido por temperatura (PR_T) según IEC 61724-1:2021 Ed.2
- [x] Calcular Reference Yield (Yr) usando rawPOA (antes de sombreado) y G_ref=1000 W/m²
- [x] Separar BOS Efficiency (E_AC/E_DC) del Performance Ratio (Yf/Yr) en la UI
- [x] Agregar Specific Yield (kWh/kWp/año) = Final Yield como métrica principal
- [x] Ponderar pérdidas por energía de referencia mensual (no promedio aritmético)
- [x] Agregar métricas IEC completas: Yr, Yf, Ya, Lc (Capture Losses), Ls (System Losses)
- [x] Mostrar desglose de yields IEC 61724 con grid 5 columnas + BOS/Pérdidas/E_DC
- [x] 41 tests unitarios para IEC 61724 (PR, PR_T, yields, pérdidas ponderadas) — 302 total
- [x] Build exitoso, TypeScript 0 errores, 302 tests pasan
## Integración PVGIS Real → Simulador de Energía + Unificación Unidades DC/AC
- [x] Crear interfaz PVGISToSimulatorData con datos mensuales PVGIS (productionAC_kWh, productionCorrectedAC_kWh, irradiationPOA_kWhm2, temperature) y anuales
- [x] Agregar callback onSendToSimulator al PVGISAnalyzer con payload completo (lat, lon, tilt, az, kWp, loss, technology, monthlyData, radiationDB)
- [x] Agregar botón "Aplicar al Simulador" en PVGISAnalyzer que envía datos raw y corregidos
- [x] Crear estado pvgisData en Home.tsx y pasarlo al EnergyProductionSimulator + onDiscardPvgis
- [x] Mostrar banner PVGIS emerald en el Simulador con producción AC, corregida, POA, factor, tilt/az, kWp
- [x] Agregar comparativa: producción PVGIS AC vs Simulador AC con Δ% automático en tarjeta verde
- [x] Unificar unidades en Simulador: tarjetas DC (azul, kWh/año DC) y AC (verde, kWh/año AC) en grid 6 cols
- [x] Unificar unidades en PVGISAnalyzer: ya etiquetado como kWh/año AC (PVGIS reporta AC post-inversor)
- [x] Unificar unidades en IEC 61724: E_DC kWh/año DC (azul), E_AC kWh/año AC (verde) en grid 4 cols
- [x] Actualizar gráfico "Producción Mensual" con barras DC (azul 40%) y AC (verde) + línea PVGIS (púrpura punteada)
- [x] Actualizar gráfico "Energía DC vs AC" a kWh/mes con línea Pérdidas BOS (roja punteada) + leyenda explicativa
- [x] Build exitoso, 302 tests pasan, TypeScript 0 errores

## Nuevo Botón: PVWatts Satelital (NREL)
- [x] Crear proxy backend /api/pvwatts para la API PVWatts v8 de NREL (evitar CORS)
- [x] Registrar proxy PVWatts en server/_core/index.ts
- [x] Solicitar API key NREL al usuario via webdev_request_secrets
- [x] Crear cliente frontend pvwattsApi.ts con tipos normalizados (mensual: ac, dc, poa, tamb, wspd, solrad)
- [x] Crear componente PVWattsSatellite.tsx con UI similar al Heatmap Irradiancia (mapa, grilla, heatmap coloreado)
- [x] Integrar SolarProspector dentro de PVWattsSatellite (mismo patrón que IrradianceHeatmap)
- [x] Ejecutar cálculos Mulcue-Llanos (P_exp, PR, pérdidas T°) con datos PVWatts
- [x] Agregar pestaña/botón "PVWatts Satelital" en Home.tsx
- [x] Conectar flujo de datos PVWatts → Prospector → Simulador de Energía
- [x] Unificar unidades kWh/año DC y kWh/año AC en resultados PVWatts
- [x] Agregar tests unitarios para proxy y cliente PVWatts
- [x] Verificar build y funcionalidad

## Fix: PVWatts Satelital → Simulador de Energía
- [x] Crear interfaz PVWattsToSimulatorData con datos mensuales AC/DC/POA/Tamb completos
- [x] Modificar PVWattsSatellite para obtener datos completos del punto seleccionado (no solo quickEstimate)
- [x] Agregar botón directo "Usar en Simulador" en PVWattsSatellite que envíe PVWattsToSimulatorData
- [x] Agregar estado pvwattsData en Home.tsx y callback dedicado handlePVWattsToSimulator
- [x] Agregar prop pvwattsData en EnergyProductionSimulator con banner dedicado PVWatts
- [x] Agregar comparación PVWatts AC mensual en gráfico del Simulador (línea como PVGIS)
- [x] Agregar comparación PVWatts AC anual en métricas del Simulador
- [x] Permitir seleccionar entre Prospector y PVWatts como fuente de datos en el Simulador
- [x] Verificar build y tests

## Fix: Datos Prospector (Mulcue-Llanos) de PVWatts NO migran al Simulador
- [x] Asegurar que handleProspectorToSimulator funcione correctamente cuando se llama desde PVWattsSatellite
- [x] Verificar que poaData se recalcule correctamente cuando prospectorData se setea junto con weatherData sintético
- [x] Agregar indicador visual en el banner del Prospector que muestre si los datos vienen de PVGIS o PVWatts
- [x] Permitir al usuario seleccionar entre Prospector (Mulcue-Llanos) y PVWatts directo como fuente en el Simulador
- [x] Verificar build y tests

## Diferenciación PVGIS vs PVWatts en Simulador
- [x] Agregar campo 'source' a ProspectorToSimulatorData ('heatmap_pvgis' | 'heatmap_pvwatts')
- [x] En SolarProspector: aceptar prop 'source' y pasarlo al ProspectorToSimulatorData
- [x] En IrradianceHeatmap: pasar source='heatmap_pvgis' al SolarProspector
- [x] En PVWattsSatellite: pasar source='heatmap_pvwatts' al SolarProspector
- [x] En EnergyProductionSimulator: banner diferenciado según source (color, icono, texto distinto)
- [x] En EnergyProductionSimulator: etiqueta "GHI (PVGIS)" o "GHI (PVWatts)" según source
- [x] Mismos 8 parámetros en ambos banners para comparación directa
- [x] Verificar build y tests

## Fix: Etiqueta "GHI PVGIS" incorrecta en PVWatts y valores GHI bajos
- [x] Cambiar todas las etiquetas "GHI PVGIS" / "GHI Anual (PVGIS)" en SolarProspector a dinámicas según prop source
- [x] En PVWattsSatellite: hacer consulta adicional con tilt=0 para obtener GHI real (no POA inclinado)
- [x] Actualizar pvwattsApi.ts para que annualGHI_kWhm2 sea GHI real (tilt=0) y no POA
- [x] Verificar que los valores GHI PVWatts con tilt=0 sean comparables a PVGIS (Medellín: 1941 vs 2091 PVGIS = ~7% diferencia, normal por TMY diferente)
- [x] Verificar build y tests (320/320 pasan)

## Optimización IEC 61724: EPI y Desglose Capture Losses
- [x] Agregar campo captureLossesBreakdown a IEC61724Metrics (temperatura, sombra, suciedad, mismatch, cableadoDC) en horas equivalentes
- [x] Agregar campo energyPerformanceIndex (EPI) a IEC61724Metrics (ratio vs PVWatts benchmark)
- [x] Calcular Lc_temp = Yr × (pérdida_temp% / 100) en calculateAnnualProduction
- [x] Calcular Lc_sombra = Yr × (pérdida_sombra% / 100) en calculateAnnualProduction
- [x] Calcular Lc_suciedad = Yr × (pérdida_suciedad% / 100) en calculateAnnualProduction
- [x] Calcular Lc_mismatch = Yr × (pérdida_mismatch% / 100) en calculateAnnualProduction
- [x] Calcular Lc_cableadoDC = Yr × (pérdida_dcWiring% / 100) en calculateAnnualProduction
- [x] Calcular EPI = E_AC_simulador / E_AC_pvwatts cuando pvwattsData está disponible
- [x] Agregar visualización del desglose de Capture Losses con gráfico de barras horizontales en EnergyProductionSimulator
- [x] Agregar tarjeta EPI con indicador visual (verde ≥1.0, amarillo 0.9-1.0, rojo <0.9) en EnergyProductionSimulator
- [x] Pasar pvwattsData al motor de producción para calcular EPI
- [x] Verificar build y tests (52 tests energyProduction, 331 total, build exitoso)

## Fix: Gráfico DC vs AC - Energía AC negativa y pérdidas BOS negativas
- [x] Corregir cálculo de energyDC en gráfico de barras: usar d.dcEnergy en vez de d.dcPower * (365.25/12)/1000
- [x] Corregir cálculo de dcEnergy_kWh en gráfico de líneas: usar d.dcEnergy en vez de d.dcPower * (365.25/12)/1000
- [x] Corregir cálculo de losses_kWh: usar d.dcEnergy - d.energyProduced
- [x] Verificar build y tests (356/356 pasan, build exitoso)

## Optimización IEC 61724: PR_T Horario (PVWatts + PVGIS)
- [x] Agregar parámetros horarios a pvwattsProxy.ts (timeframe=hourly)
- [x] Agregar función getPVWattsHourlyData en pvwattsApi.ts (8760 registros: poa, tamb, tcell, wspd)
- [x] Agregar parámetros seriescalc a pvgisProxy.ts (startyear, endyear, pvcalculation, components)
- [x] Agregar función getPVGISHourlyData en pvgisApi.ts (T2m, irradiancia, WS10m por hora)
- [x] Crear función calculatePR_T_Hourly en energyProduction.ts (IEC 61724-1:2021)
- [x] Fórmula: PR_T = Σ(E_AC_h) / Σ(G_POA_h × P_nom/G_ref × (1 + γ × (T_cell_h - 25)))
- [x] Calcular PR_T mensual desglosado (12 valores) para gráfico
- [x] Agregar interfaz HourlyPR_T_Data con datos horarios agrupados por mes
- [x] Integrar datos horarios PVWatts en PVWattsSatellite → Simulador
- [x] Integrar datos horarios PVGIS en PVGISAnalyzer → Simulador
- [x] Agregar visualización PR_T horario vs PR_T mensual en EnergyProductionSimulator
- [x] Agregar gráfico mensual comparativo PR_T (PVWatts vs PVGIS vs Simulador)
- [x] Agregar tests unitarios para calculatePR_T_Hourly (25 tests en server/prTHourly.test.ts, 356 total)
- [x] Verificar build y tests (356/356 pasan, build exitoso)

## Tabla Comparativa Lado a Lado (Simulador vs PVWatts vs PVGIS)
- [x] Crear función buildComparisonData que unifique datos mensuales de las 3 fuentes en una estructura común
- [x] Crear componente CrossValidationTable con tabla completa de 12 meses + fila anual
- [x] Columnas por fuente: Producción AC (kWh), Producción DC (kWh), POA (kWh/m²), PR (%), PR_T (%), T_amb (°C), T_cell (°C)
- [x] Calcular Δ% entre fuentes (Simulador vs PVWatts, Simulador vs PVGIS, PVWatts vs PVGIS)
- [x] Resaltado condicional: verde si Δ < 5%, amarillo 5-15%, rojo > 15%
- [x] Fila de totales/promedios anuales con resumen estadístico (RMSE, MAE, R²)
- [x] Botón de exportar tabla comparativa a CSV
- [x] Toggle para mostrar/ocultar columnas por fuente
- [x] Integrar componente en EnergyProductionSimulator (visible cuando hay al menos 2 fuentes)
- [x] Tests unitarios para buildComparisonData y métricas estadísticas (31 tests, 387 total)

## Corrección de Irradiancia PVWatts vs PVGIS (Heatmap)
- [x] Diagnosticar causa de diferencia excesiva entre valores GHI PVWatts y PVGIS en heatmap (marcadores mostraban Specific Yield en vez de GHI)
- [x] Corregir el procesamiento de datos de irradiancia PVWatts para que sea comparable con PVGIS (ahora usa classifyAnnualIrradiance con mismos umbrales)
- [x] Verificar que los valores corregidos son razonables para Colombia (GHI ~1400-1900 kWh/m²/año)
- [x] Actualizar tests y verificar build (387/387 pasan, TypeScript 0 errores)

## Mejora de Navegación - Acceso a PVWatts/PVGIS sin EPW
- [x] Hacer visibles las pestañas PVWatts Satelital y PVGIS Real sin requerir archivo EPW cargado
- [x] Permitir que PVWatts y PVGIS funcionen sin selectedCity (usar coordenadas por defecto Medellín)
- [x] Hacer visible el Heatmap Irradiancia sin requerir EPW
- [x] Hacer visible el Simulador Energía cuando hay datos de PVWatts o PVGIS (sin EPW)

## Módulo Diagnóstico BIPV - Mediciones de Campo
- [x] Crear librería bipvDiagnostic.ts con lógica de diagnóstico BIPV
- [x] Función calculateExpectedProduction: producción esperada mensual/anual usando Mulcue-Llanos, PVGIS y PVWatts
- [x] Función compareBIPVPerformance: comparar producción real vs esperada con métricas Δ%, health score
- [x] Función generateBIPVReport: generar resumen de salud del sistema con causas probables
- [x] Crear componente BIPVDiagnostic.tsx con 4 secciones principales:
  - [x] Sección 1: Especificaciones del Panel (selector PanelTechSelector + editor personalizado)
  - [x] Sección 2: Ubicación y Configuración (coordenadas, ángulo inclinación campo, azimut, tipo instalación)
  - [x] Sección 3: Producción Esperada (tabla mensual Mulcue-Llanos vs PVGIS vs PVWatts con PR y PR_T)
  - [x] Sección 4: Mediciones de Campo y Diagnóstico (GHI, T_amb, T_cell, producción real, alertas)
- [x] Botón "Consultar PVGIS" integrado que obtiene datos automáticamente por coordenadas
- [x] Botón "Consultar PVWatts" integrado que obtiene datos automáticamente por coordenadas
- [x] Conectar con cálculos del Simulador de Energía (PR, PR_T, EPI, Capture Losses)
- [x] Tabla resumen: Producción Esperada vs Real con Δ% y semáforo de salud
- [x] Integrar diagnosePerformance() existente para alertas y causas probables
- [x] Agregar pestaña "Diagnóstico BIPV" en la navegación principal (siempre visible)
- [x] Tests unitarios para bipvDiagnostic.ts (42 tests, 429 total)

## PR Convencional y PR Corregido en Diagnóstico BIPV
- [x] Agregar campo de entrada "Producción Real del Inversor (kWh)" mensual y anual en BIPVDiagnostic
- [x] Calcular PR Convencional = Producción_inversor / P_m donde P_m = P_ref × N_paneles × (G / G_ref)
- [x] Calcular PR Corregido = Producción_inversor / Producción_esperada (fuente más precisa: promedio 3 modelos)
- [x] Mostrar ambos PRs en la sección de resultados con semáforo de salud
- [x] Agregar PR Convencional y PR Corregido a la tabla mensual de comparación
- [x] Actualizar tests unitarios para los nuevos cálculos de PR (8 tests dedicados)

## Importación CSV Mejorada - Calculadora Factores de Sombreado
- [x] Ampliar interfaz AnalysisPoint con campos: evento, fsGeometrico, fsClimatico, situacion, hourStr
- [x] Modificar importFromCSV para detectar formato del Excel (11 columnas con Evento, FS_geometrico, FS_climatico, Situacion)
- [x] Importar datos tal cual el orden del CSV: conservar mes, día, hora, altura solar, azimut, obstáculo, FS_geom, FS_clim, FS, situación
- [x] Agregar columnas FS_Geom, FS_Clim y Situación a la tabla visual de Puntos de Análisis (condicionales)
- [x] Mantener interactividad: edición inline, auto-cálculo solar, integración con obstáculos del diagrama
- [x] Actualizar exportToCSV para incluir los nuevos campos (formato extendido automático)
- [x] Soportar importación de archivos .xlsx directamente (librería xlsx instalada)

## Corrección Tabla Puntos de Análisis (visual + parsing)
- [x] Reducir tipografía de tabla a text-[10px]/text-[11px] y padding a px-1 py-1
- [x] Hacer visibles día, hora, altura solar, azimut con inputs compactos (w-12/w-14/w-16)
- [x] Corregir parsing de FS: agregar parseLocalizedNumber para locale colombiano (punto=miles, coma=decimal)
- [x] Agregar normalizeFS para validar rango 0-1 (valores >1 se dividen por 100)
- [x] Mostrar hora como texto (hourStr) cuando viene del CSV importado
- [x] Verificar build y tests (437/437 pasan, 0 errores TypeScript)

## Gráfico Radar Comparativo - Diagnóstico BIPV
- [x] Implementar gráfico radar con Recharts (RadarChart) en sección 4 de BIPVDiagnostic
- [x] 4 series: Mulcue-Llanos (azul), PVGIS (verde), PVWatts (violeta), Producción Real (rojo)
- [x] 12 ejes correspondientes a los 12 meses del año
- [x] Normalizar valores por máximo mensual para visualización proporcional
- [x] Identificar patrones de degradación estacional (badges de meses críticos Δ>15%)
- [x] Verificar build y tests (437/437 pasan, 0 errores TypeScript)

## Corrección Error 410 PVWatts
- [x] Diagnosticar error 410: NREL migró dominio de developer.nrel.gov a developer.nlr.gov (brownout hasta 29 mayo 2026)
- [x] Actualizar PVWATTS_BASE_URL en server/pvwattsProxy.ts a developer.nlr.gov
- [x] Verificar que no hay otras referencias al dominio antiguo
- [x] Verificar build y tests (437/437 pasan, 0 errores TypeScript)

## Exportación PDF Informe Diagnóstico BIPV
- [x] Crear función generateBIPVReport en client/src/lib/bipvReportGenerator.ts
- [x] Sección 1: Portada con título, nombre del sitio, fecha y coordenadas
- [x] Sección 2: Especificaciones del Panel (tabla con datos técnicos)
- [x] Sección 3: Configuración del Sitio (ubicación, inclinación, azimut, tipo instalación)
- [x] Sección 4: Producción Esperada Mensual (tabla Mulcue vs PVGIS vs PVWatts vs Promedio)
- [x] Sección 5: Comparación Real vs Esperada (tabla mensual con Δ%, PR Conv., PR Corr.)
- [x] Sección 6: Métricas de Salud (Health Score, PR Convencional, PR Corregido, P_m)
- [x] Sección 7: Diagnóstico y Recomendaciones de Mantenimiento
- [x] Agregar botón "Exportar PDF" en BIPVDiagnostic.tsx (rojo, al lado de CSV)
- [x] Verificar build y tests (437/437 pasan, 0 errores TypeScript)

## Almacenamiento Paneles Personalizados BIPV (localStorage + DB)
- [x] Crear tabla custom_panels en drizzle/schema.ts (userId, name, powerRating, efficiency, tempCoeff, noct, area, degradation, etc.)
- [x] Crear procedimientos tRPC: customPanels.list, customPanels.create, customPanels.update, customPanels.delete
- [x] Crear hook useCustomPanels con localStorage como caché inmediata
- [x] Sincronizar localStorage con DB cuando hay sesión activa (pull al cargar, push al guardar)
- [x] UI: Botón "Guardar Panel" para almacenar configuración actual como panel personalizado
- [x] UI: Lista de paneles guardados con opción de cargar y eliminar
- [x] Integrar en BIPVDiagnostic.tsx reemplazando/complementando el selector actual
- [x] Tests unitarios para procedimientos tRPC de paneles (22 tests)
- [x] Verificar build y tests (459/459 pasan, 0 errores TypeScript)

## Corrección Error PDF autoTable
- [x] Corregir "t.autoTable is not a function" en bipvReportGenerator.ts: cambiar import side-effect por import autoTable from 'jspdf-autotable' y usar autoTable(doc, {...})
- [x] Corregir mismo problema en reportGenerator.ts para prevenir error en el otro generador de PDF
- [x] Verificar build y tests (459/459 pasan, 0 errores TypeScript)

## Gráfico Radar como Imagen en PDF
- [x] Agregar ref al contenedor del RadarChart para capturar el SVG/canvas
- [x] Usar html2canvas para convertir el gráfico radar a imagen PNG base64 (scale: 2x)
- [x] Pasar la imagen radarImageBase64 como parámetro opcional a generateBIPVReport
- [x] Insertar la imagen del radar en el PDF (sección 6: GRÁFICO RADAR — PATRÓN ESTACIONAL)
- [x] Verificar build y tests (459/459 pasan, 0 errores TypeScript)

## Cruce Máscara de Sombreado + EPW → Factores FS Geométrico y Climático
- [x] Crear librería shadingMaskCrossing.ts con algoritmo de cruce máscara+EPW
- [x] Implementar modelo de cielo claro Hottel para DNI_clearsky y DHI_clearsky
- [x] Implementar cálculo de posición solar (altitud, azimut) para cualquier fecha/hora/ubicación
- [x] Implementar cálculo de FS_climático = 1 - POA_actual/POA_clearsky por fachada/hora
- [x] Implementar cálculo de FS_geométrico basado en obstrucciones 3D (bloques del JSON)
- [x] Implementar selección de días críticos: solsticios (21 jun, 21 dic) y equinoccios (20 mar, 22 sep)
- [x] Implementar clasificación de situación del cielo según FS (despejado/parcial/nublado/cubierto)
- [x] Generar array de AnalysisPoint[] compatible con la tabla existente de Puntos de Análisis
- [x] Agregar botón "Cruzar Máscara + EPW" en ShadingCalculator.tsx
- [x] Agregar modal/panel de configuración: selección de eventos, fachadas, rango horario
- [x] Integrar con EPW ya cargado en la app (reusar weatherData del estado global)
- [x] Integrar con obstáculos ya importados (Site Designer JSON / OBJ)
- [x] Poblar tabla Puntos de Análisis automáticamente con resultados del cruce
- [x] Tests unitarios para shadingMaskCrossing.ts (modelo Hottel, posición solar, FS_clim, FS_geom)
- [x] Verificar build, TypeScript 0 errores, todos los tests pasan

## Importación de Modelo 3D a Evaluar (Edificio) con Ajuste de Obstáculos
- [x] Crear librería buildingModelImporter.ts para importar modelo 3D del edificio a evaluar
- [x] Separar conceptos: "obstáculos de sombra" (entorno) vs "modelo a evaluar" (edificio propio)
- [x] Detectar superficies de fachada del modelo importado (normales, orientaciones)
- [x] Calcular punto de observación desde el centroide del modelo importado
- [x] Recalcular obstáculos existentes desde la perspectiva del nuevo punto de observación
- [x] Generar fachadas automáticas basadas en las superficies del modelo importado
- [x] Crear componente EvaluationModelImporter.tsx con UI de importación y configuración
- [x] Selector de punto de evaluación (centroide, fachada específica, punto personalizado)
- [x] Previsualización 3D simplificada del modelo importado con obstáculos relativos
- [x] Integrar con CrossingModal: usar fachadas detectadas automáticamente del modelo
- [x] Actualizar tabla Puntos de Análisis con resultados ajustados por posición del modelo
- [x] Tests unitarios para buildingModelImporter.ts
- [x] Verificar build, TypeScript 0 errores, todos los tests pasan

## Visor 3D Interactivo (Three.js)
- [x] Instalar dependencias Three.js y @react-three/fiber + @react-three/drei
- [x] Crear componente ModelViewer3D.tsx con escena Three.js (canvas, luces, grid)
- [x] Renderizar modelo del edificio importado (fachadas coloreadas por orientación)
- [x] Renderizar obstáculos de sombra existentes (semi-transparentes)
- [x] Controles de cámara: rotación orbital, zoom, pan
- [x] Selección visual de fachadas: clic para seleccionar, hover para highlight
- [x] Indicador visual de orientación (brújula N/S/E/O)
- [x] Panel de información de fachada seleccionada (azimut, inclinación, área)
- [x] Integrar visor 3D con EvaluationModelImporter (mostrar al importar modelo)
- [x] Tests unitarios para el componente del visor 3D
- [x] Verificar build, TypeScript 0 errores, todos los tests pasan

## Exportación PDF - Resultados Cruce Máscara+EPW en Diagnóstico BIPV
- [x] Agregar sección "Análisis de Sombreado por Fachada" al PDF del Diagnóstico BIPV
- [x] Tabla resumen de FS por fachada (azimut, inclinación, área, FS_geom promedio, FS_clim promedio)
- [x] Tabla detallada de FS por hora y evento (días críticos evaluados)
- [x] Gráfico de distribución horaria de FS (barras agrupadas por fachada)
- [x] Gráfico de situación del cielo (pie chart: despejado/parcial/nublado/cubierto)
- [x] Información del modelo 3D importado (dimensiones, fachadas detectadas)
- [x] Integrar con el flujo de exportación existente del Diagnóstico BIPV
- [x] Tests unitarios para la generación de la nueva sección PDF
- [x] Verificar build, TypeScript 0 errores, todos los tests pasan

## Importación glTF/GLB (Khronos Standard)
- [x] Crear librería gltfParser.ts para parsear archivos glTF (.gltf) y GLB (.glb)
- [x] Extraer vértices, caras y normales de meshes glTF
- [x] Extraer materiales y colores de los nodos glTF
- [x] Soportar escenas con múltiples nodos y transformaciones jerárquicas
- [x] Convertir datos glTF al formato OBJParseResult para reusar la lógica existente
- [x] Integrar parser glTF con EvaluationModelImporter (modelo a evaluar)
- [x] Integrar parser glTF con importación de obstáculos de sombra
- [x] Actualizar ModelViewer3D para renderizar materiales/colores del glTF
- [x] Agregar botón de importación glTF/GLB en la UI (junto a OBJ)
- [x] Tests unitarios para gltfParser.ts
- [x] Verificar build, TypeScript 0 errores, todos los tests pasan

## Detección de Techos/Superficies Horizontales en Modelo 3D
- [x] Modificar buildingModelImporter para detectar superficies horizontales (techos) además de verticales
- [x] Incluir caras con normal en eje Z (inclinación ~0°) como superficies evaluables
- [x] Calcular área, centroide y orientación del techo detectado
- [x] Integrar techos en la lista de fachadas detectadas con etiqueta "Techo/Cubierta"
- [x] Actualizar CrossingModal para incluir techos en el cruce Máscara+EPW
- [x] Actualizar ModelViewer3D para que el techo sea seleccionable y coloreado
- [x] Actualizar textos en EvaluationModelImporter para mencionar "fachadas y techos"
- [x] Tests unitarios para la detección de techos
- [x] Verificar build, TypeScript 0 errores, todos los tests pasan

## Selector de Inclinación para Techos Inclinados
- [x] Agregar control deslizante/input de inclinación (0°-45°) para superficies de techo detectadas
- [x] Permitir definir orientación del techo inclinado (azimut de la pendiente)
- [x] Selector de tipo de techo: plano, una agua, dos aguas, cuatro aguas
- [x] Actualizar FacadeDefinition.tilt dinámicamente al cambiar la inclinación del techo
- [x] Previsualización visual del ángulo de inclinación seleccionado
- [x] Integrar con el cruce Máscara+EPW (usar tilt ajustado en vez del detectado)
- [x] Tests unitarios para la lógica de ajuste de inclinación
- [x] Verificar build, TypeScript 0 errores, todos los tests pasan

## Limpieza de Datos de Ejemplo
- [x] Eliminar datos de ejemplo pre-cargados en la tabla Puntos de Análisis (Edificio A, Ninguno)
- [x] La tabla ahora inicia vacía y se llena por importación CSV, manual o cruce Máscara+EPW

## Bug Fix - Botones Heatmap PVGIS y PVWatts no abren
- [x] Investigar por qué los botones Heatmap PVGIS y PVWatts no navegan correctamente
- [x] Solucionar definitivamente el problema de navegación (lazy-mount persistent pattern en Home.tsx)
- [x] Verificar que ambos botones abren sus respectivas páginas
- [x] Fix Google Maps loading: patrón original del template + fallback Leaflet/OpenStreetMap
- [x] Implementar shim de compatibilidad Google Maps API sobre Leaflet (AdvancedMarkerElement, Circle, Geocoder, LatLngBounds, InfoWindow)
- [x] Eliminar server/mapsProxy.ts innecesario
- [x] Agregar indicador visual "OpenStreetMap (fallback)" cuando se usa Leaflet
- [x] Navegación entre vistas sin errores DOM (display:none/block pattern)
- [x] 609 tests pasando (16 nuevos para Map fallback logic)

## Bug Fix - Visor 3D Modelo a Evaluar (SketchUp)
- [x] Corregir controles orbitales (rotar, zoom, pan) que no funcionan con modelos SketchUp
- [x] Corregir botón de ampliar pantalla (fullscreen) del visor 3D
- [x] Mejorar visualización de ejes X, Y, Z con etiquetas claras y colores diferenciados
- [x] Verificar que los controles funcionan correctamente después de cargar un modelo
- [x] OrbitControls: enableRotate, enableZoom, enablePan activados con damping
- [x] Botones funcionales: Auto-rotar, Zoom In, Zoom Out, Resetear vista, Pantalla completa
- [x] Ejes: X (rojo), Y/Norte (verde), Z/Arriba (azul) con flechas cónicas + etiquetas
- [x] Overlays con pointer-events-none para no bloquear interacción con canvas
- [x] 609 tests pasando

## Integración Modelo 3D Edificio Propio → Diagrama Trayectoria Solar
- [x] Conectar puntos de evaluación del edificio propio como puntos de observación en el diagrama solar
- [x] Proyectar obstáculos de sombra (OBJ importados) desde cada punto de evaluación del edificio
- [x] Calcular siluetas angulares de obstáculos vistos desde cada fachada del edificio propio (recalculateForFacade)
- [x] Mostrar en el diagrama solar los polígonos de sombra específicos para la fachada seleccionada
- [x] Actualizar automáticamente los factores de sombreado (FS) por fachada según la proyección
- [x] Integrar con el cálculo BIPV para obtener FS exacto por superficie receptora
- [x] Selector visual de fachada/techo activa con info de Az/Incl/Área
- [x] Auto-selección de primera fachada al importar modelo
- [x] Mensaje informativo cuando no hay obstáculos 3D importados aún

## Tabla Resumen Comparativa Multi-Fachada
- [x] Crear componente FacadeComparisonTable con columnas: Superficie, Az, Incl, Área, FS, Horas Sol, POA, Producción, Pérdida Sombra
- [x] Calcular FS promedio por fachada usando recalculateForFacade + obstáculos importados
- [x] Estimar producción (kWh/m²/año y kWh/año total) por fachada usando datos EPW + inclinación + orientación (Liu-Jordan)
- [x] Calcular horas de sol efectivas por fachada (horas sin sombra vs disponibles)
- [x] Mostrar tabla lado a lado después del selector de fachadas (con header púrpura gradiente)
- [x] Resaltar la mejor superficie para BIPV (mayor producción) con icono de corona
- [x] Tabla se muestra solo cuando hay modelo + EPW cargados
- [x] 609 tests pasando, 0 errores TypeScript

## Bug Fix URGENTE - Mapas Heatmap PVGIS y PVWatts no cargan círculos
- [x] Investigar por qué los círculos de irradiancia no se muestran en Heatmap PVGIS
- [x] Investigar por qué los círculos de irradiancia no se muestran en PVWatts Satelital
- [x] Causa raíz: clases shim singleton (Circle, AdvancedMarkerElement) usaban leafletMap del closure del primer mapa
- [x] Fix: cada instancia de Circle/Marker ahora obtiene el leafletMap correcto del shimMap pasado en opts.map
- [x] Restaurar la visualización de círculos con valores de irradiancia promedio (PVGIS: 9 puntos, PVWatts: 16 puntos)
- [x] Mantener la interactividad (clic en círculo → panel detalle + cálculos con fórmulas)
- [x] Verificar que no se rompe la conexión con otros cálculos (Simulador, Prospector, etc.)
- [x] Navegación entre pestañas: círculos persisten al cambiar de mapa
- [x] 609 tests pasando

## Bug Fix - Botón Generar Reporte PDF no funciona
- [x] Investigar error al hacer clic en "Generar Reporte" / "Descargar Reporte PDF"
- [x] Causa raíz: requería selectedCity (null si EPW se carga directamente) + división por cero con shadingPoints vacíos
- [x] Remover dependencia de selectedCity - usar datos del EPW como fallback (city, country, lat, lon, elevation)
- [x] Manejar datos parciales sin errores NaN (shadingPoints, poaData, energyData)
- [x] Mostrar advertencia clara de "Reporte parcial" cuando faltan datos opcionales
- [x] Indicar requisitos cumplidos vs pendientes en la UI
- [x] PDF genera correctamente con 2 páginas (portada, resumen, POA, proyecciones, meteo, recomendaciones)
- [x] Corregir la generación del PDF
- [x] Verificar que el PDF se descarga correctamente (38KB, 2 páginas)
- [x] 609 tests pasando

## Optimización Flujo FS Modelo 3D → Simulador Energía BIPV
- [x] Auto-generar puntos de análisis para todas las horas solares de cada mes al tener modelo 3D + obstáculos
- [x] Calcular FS mensual automático basado en intersección obstáculos-trayectoria por fachada activa
- [x] Enviar FS mensuales calculados desde el modelo 3D al Simulador de Energía automáticamente
- [x] Mostrar banner en Simulador indicando que los FS provienen del análisis 3D del edificio (panel púrpura)
- [x] Incluir info de la fachada activa (nombre, azimut, inclinación, área) en los datos enviados al Simulador
- [x] Permitir seleccionar fachada desde el Simulador para recalcular producción por superficie
- [x] Fix: Panel de FS mensual visible siempre que facadeAnalysis3D esté presente (condición hasShadingData || facadeAnalysis3D)

## Selector de Fachada en el Simulador de Energía
- [x] Agregar selector de fachada dentro del Simulador para comparar producción entre superficies sin volver a la Calculadora
- [x] Pasar lista de fachadas detectadas del modelo 3D como prop al Simulador
- [x] UI de selector con botones/tabs por fachada mostrando nombre, azimut, inclinación
- [x] Callback para cambiar fachada activa desde el Simulador (recalcula FS y producción directamente en Home.tsx)
- [x] Indicador visual de la fachada actualmente seleccionada (check + borde + FS/pérdida)

## Tabla Comparativa Multi-Fachada en el Simulador
- [x] Calcular producción estimada (kWh/año) para cada fachada del modelo 3D automáticamente
- [x] Mostrar tabla comparativa con columnas: Fachada, Az/Incl, Área, FS Anual, POA, Prod AC, Yield, PR, Comparativa
- [x] Incluir indicadores visuales (barras de progreso coloreadas, medallas de ranking)
- [x] Agregar ranking/orden por producción para identificar la mejor superficie (medallas oro/plata/bronce)
- [x] Mostrar totales del edificio (TOTAL EDIFICIO: producción total sumando todas las superficies)
- [x] Resumen superior con KPIs: Producción Total, Área Total, FS Promedio, PR Promedio, Mejor Superficie
- [x] Nota al pie explicando la metodología de cálculo (panel, pérdidas, modelo Liu-Jordan)

## Tabla Comparativa Multi-Fachada en Reporte PDF
- [x] Agregar sección "6. ANÁLISIS COMPARATIVO MULTI-FACHADA (BIPV)" al generador de reportes PDF
- [x] Tabla con ranking de superficies: nombre, azimut, inclinación, área, FS, POA, producción AC, yield, PR
- [x] Fila TOTAL EDIFICIO con producción total sumada
- [x] KPIs resumen: Producción Total, Área Total, FS Promedio, PR Promedio, Mejor Superficie
- [x] Pasar datos del modelo 3D (fachadas, obstáculos, northOffset) al generador de reportes
- [x] Nota metodológica al pie de la sección explicando modelo Liu-Jordan y cálculo de FS

## BUG: Error al generar reporte PDF
- [x] Fix: "Cannot read properties of undefined (reading 'toString')" al generar reporte PDF — Protecciones null-safe en todas las llamadas .toFixed() del reportGenerator.ts

## Mejora del Reporte PDF - Auto-cálculo y datos faltantes
- [x] Auto-calcular Producción Anual en el reporte usando datos POA + config panel (sin necesidad de ejecutar Simulador)
- [x] Auto-calcular Factor de Capacidad, Ratio de Desempeño, Yield en el reporte
- [x] Agregar tabla de Producción Mensual desglosada (12 meses con kWh)
- [x] Agregar Horas Sol Pico (HSP) mensual derivadas del POA
- [x] Agregar estimación de CO2 evitado (ton/año) usando factor de emisión
- [x] Agregar estimación de Ahorro Económico Anual ($/año)
- [x] Agregar sección de FS mensual (12 valores) cuando hay datos de sombreado
- [x] Corregir tabla de puntos de análisis: mostrar día, hora, alt, azim correctos
- [x] Mejorar sección de Recomendaciones con datos calculados más específicos

## BUG: Valores incorrectos en PDF (Factor de Capacidad, HSP, Yield)
- [x] Fix: Factor de Capacidad mostraba 2874% en lugar de 28.7% — capacityFactor ya viene como % de calculateAnnualProduction, se multiplicaba por 100 dos veces
- [x] Fix: HSP Anuales mostraba 119h en lugar de ~2882h — fórmula incorrecta (totalPOA/1000*30), corregida a (totalPOA*days*24/1000)
- [x] Fix: Mismo bug de capacityFactor*100 en ReportGenerator.tsx (UI preview)
- [x] Fix: performanceRatio ya viene como % de calculateAnnualProduction, normalizado correctamente en reportGenerator.ts

## Sincronización Fachada-POA y ROI por Fachada
- [x] Sincronizar automáticamente tilt/azimut del POA con la fachada seleccionada del modelo 3D
- [x] Agregar análisis de ROI/payback individual por fachada en la tabla comparativa
- [x] Columnas en PDF: Ahorro (mil COP), Payback (años), ROI 25a (%)
- [x] KPIs financieros globales del edificio en PDF (ahorro total, payback promedio, costo/Wp, tarifa)

## Parámetros Financieros Editables para ROI por Fachada
- [x] Hacer editables costo/Wp y tarifa eléctrica desde la UI del Simulador para el cálculo de ROI por fachada
- [x] Conectar los valores editados al cálculo de multiFacadeReportData y al PDF
- [x] Agregar tabla de sensibilidad financiera con escenarios optimista/pesimista (tarifa ±20%) en el reporte PDF

## BUG: Cantidad de Paneles = 1 en el reporte PDF
- [x] El Simulador no comunica panelQuantity, panelPower, production al padre (Home.tsx)
- [x] El reporte PDF usa energyData.panelQuantity=1 (valor inicial) en lugar del valor real del Simulador
- [x] Agregar callback onEnergyDataChange para sincronizar datos del Simulador con el reporte
- [x] Agregar PVWatts preload bridge para aplicar tilt/azimuth/panelQuantity al Simulador
- [x] Corregir bucle infinito React #185 (useRef + JSON dedupe en onEnergyDataChange)

## PVWatts pre-llena área disponible en Simulador
- [x] Agregar campo editable de área disponible (m²) en PVWatts Satelital antes de enviar
- [x] Incluir availableArea en PVWattsToSimulatorData
- [x] En el preload bridge del Simulador, aplicar availableArea para auto-calcular paneles

## PVGIS Analyzer: campo de área disponible igual que PVWatts
- [x] Agregar campo editable de área disponible (m²) en PVGIS Analyzer antes de enviar al Simulador
- [x] Incluir availableArea en los datos enviados al Simulador desde PVGIS
- [x] Agregar PVGIS preload bridge en Simulador para aplicar tilt/azimuth/availableArea

## Importar área desde modelo 3D en PVWatts y PVGIS
- [x] Pasar modelFacades como prop a PVWattsSatellite y PVGISAnalyzer
- [x] Agregar botón "Importar área desde modelo 3D" junto al campo de área manual en ambos componentes
- [x] Al hacer clic, mostrar lista de fachadas disponibles con su área calculada para seleccionar

## BUG: Eficiencia ×100 extra y Producción inflada en PDF
- [x] Fix display eficiencia: panelEfficiency ya es % (21.5), no multiplicar por 100 en reportGenerator
- [x] Fix weatherData sintético PVWatts: genera registros horarios realistas (días×24h) con perfil sinusoidal
- [x] Fix tabla multi-fachada: systemLosses usaba inverterEfficiency como pérdida (106%) en vez de (100-96)=4%
- [x] Fix multi-fachada: tilt/azimut se pasaban en grados a función que espera radianes
- [x] Verificar coherencia: CF, Yield, Payback ahora realistas con correcciones aplicadas

## Heatmap PVGIS: campo de área disponible + envío al Simulador
- [x] Agregar campo editable de área disponible (m²) en Heatmap PVGIS antes de "Aplicar al Simulador"
- [x] Incluir availableArea en los datos enviados al Simulador desde Heatmap PVGIS
- [x] Agregar botón "Importar del Modelo 3D" junto al campo de área (si modelFacades disponible)

## Refactorización del Sistema de Reportes - Reporte por Fachada Específica
- [x] Filtrar shadingPoints en el reporte para mostrar SOLO la fachada/techo evaluado en el Simulador
- [x] Análisis de sombreado: mostrar SOLO promedio de FS por solsticio (Jun 21, Dic 21) de la fachada evaluada
- [x] Eliminar sección multi-fachada del reporte individual (va en el reporte global)
- [x] Título del reporte debe indicar la fachada/techo específico evaluado
- [x] Verificar coherencia de resultados antes de generar reporte (validación automática)

## Sistema de Almacenamiento de Reportes Individuales
- [x] Agregar botón "Almacenar" para guardar reportes individuales por fachada en localStorage
- [x] Almacenar datos del reporte en localStorage/estado para acumulación
- [x] Mostrar lista de reportes guardados con opción de eliminar

## Reporte Global Comparativo
- [x] Crear botón "Generar Reporte Global Comparativo" que compare todos los reportes guardados
- [x] Tabla comparativa por fachada/techo con producción, FS, ROI, payback
- [x] PDF del reporte global con ranking, KPIs globales y recomendaciones por superficie

## Auto-corrección de ejes en importación de modelos 3D
- [x] Auto-detectar orientación de ejes del modelo importado (Z-up vs Y-up vs X-up)
- [x] Aplicar remapeo automático para que Z sea siempre la altura (vertical) internamente
- [x] Agregar controles manuales de corrección de ejes como fallback (UI: selector Auto/Z-up/Y-up/X-up)
- [x] Soportar convenciones de ejes de SketchUp (Z-up), Blender/glTF (Y-up), y otros (X-up)
- [x] Agregar rotación horizontal manual (0°/90°/180°/270°) para corregir orientación norte
- [x] Re-procesamiento sin recarga de archivo al cambiar eje o rotación
- [x] Badge de confianza de detección (alta/media/baja) en la UI
- [x] Tie-breaking Z > Y > X en caso de empate de scores de detección
- [x] Tests unitarios para autoDetectUpAxis, upAxis explícito y rotación (628 tests pasan)
- [x] Fix: ModelViewer3D usa transformedVertices (con remapeo aplicado) para coherencia visual con fachadas
- [x] Fix: Canvas Three.js usa up=[0,0,1] para que Z sea el eje vertical visual
- [x] Fix: glTF/GLB fuerza Y-up automáticamente (es la especificación del formato)
- [x] Fix: Alerta prominente cuando la confianza de detección es baja, con botones rápidos Y-up/Z-up
- [x] Fix: Tests de transformedVertices coherentes con centroide y dimensiones (630 tests pasan)

## Corrección del Cruce EPW (0 puntos generados)
- [x] Fix: EPW parser ahora detecta correctamente el inicio de datos (línea 8 o primera línea con año)
- [x] Fix: EPW parser usa índices correctos del formato EnergyPlus (GHI=pos13, DNI=pos14, DHI=pos15)
- [x] Fix: EPW parser filtra líneas de encabezado (requiere >=22 campos y año 1900-2100)
- [x] Fix: isFacadeExposed sanitiza NaN/undefined en tilt y azimuth (defaults: tilt=90, azimuth=0)
- [x] Fix: executeCrossing sanitiza todas las fachadas antes del loop de evaluación
- [x] Fix: calculatePOA sanitiza todos los inputs numéricos para prevenir propagación de NaN
- [x] Fix: calculateFSClimatico usa variables sanitizadas para fachada azimuth y tilt
- [x] UI: Mensaje de diagnóstico cuando el cruce genera 0 resultados (posibles causas y sugerencias)
- [x] UI: Validación de EPW vacío antes de ejecutar el cruce
- [x] Tests: 630 tests pasan correctamente

## Integración Motor IAM + Soiling (Orquestador BIPV)
- [x] Crear librería iamSoilingEngine.ts con modelo ASHRAE de reflexión geométrica (IAM)
- [x] Implementar fórmula IAM: f_iam = 1 - b0 * (1/cos(AOI) - 1), con clamp [0,1] y cutoff 85°
- [x] Implementar modelo de soiling estacional con factores mensuales configurables
- [x] Implementar corrección climática de soiling por precipitación (autolavado -85% si precipitable_water > 25)
- [x] Implementar modelo térmico confinado BIPV (k_bipv: 1.0 ventilado, 1.15 semi, 1.3 confinado, 1.5 sin vent.)
- [x] Crear catálogo de vidrios BIPV por generación: 1G (a-Si), 2G (CdTe), 3G (Perovskita) con b0_ashrae
- [x] Agregar 6 niveles de transparencia (10%-60%) con eficiencia ajustada
- [x] Calcular eficiencia STC ajustada: η_adj = η_base × (1 - τ) donde τ = transparencia
- [x] Calcular ganancia lumínica pasiva: P_luz = POA_total × área × τ
- [x] Crear componente UI BIPVGlassSimulator con selector de generación, transparencia y resultados
- [x] Integrar con datos EPW existentes (DNI, GHI, DHI, precipitable_water, temp_air)
- [x] Integrar con obstáculos del diagrama solar (factor de sombra SF)
- [x] Integrar con geometría de fachada del modelo 3D importado (tilt, azimuth, área)
- [x] Simulación comparativa multi-tecnología × multi-transparencia con tabla de resultados
- [x] Gráfico de producción mensual con desglose IAM, soiling, térmico
- [x] 5 presets de soiling por zona climática (tropical urbano, árido industrial, templado limpio, costero salino, personalizado)
- [x] 4 tipos de montaje térmico con factores k_bipv
- [x] Botón de navegación 'IAM + Soiling BIPV' en la barra principal de Home.tsx
- [x] 65 tests unitarios nuevos para motor IAM+Soiling y catálogo (695 tests totales pasan)

## Integración Script Python Multivariable (Complementos al Motor IAM+Soiling)
- [x] Agregar modelo de transposición Perez (anisótropo) como alternativa avanzada al Liu-Jordan
- [x] Agregar campo irradiancia_reflejada_w_m2 (pérdida por reflexión geométrica IAM) a resultados
- [x] Generar resultados horarios detallados (BIPVHourlyResult[]) con estructura equivalente al BSON del Python
- [x] Crear esquema DB MySQL para persistir resúmenes de simulaciones BIPV (tabla bipv_simulations)
- [x] Crear API tRPC para guardar/cargar simulaciones (CRUD: save, list, get, delete)
- [x] Agregar botón "Guardar Simulación" en BIPVGlassSimulator con nombre de proyecto
- [x] Agregar historial de simulaciones guardadas con comparación
- [x] Agregar exportación CSV/JSON de resultados horarios detallados
- [x] Agregar selector de modelo de transposición (Isótropo Liu-Jordan / Perez Anisótropo) en la UI
- [x] Tests unitarios para modelo Perez y persistencia de simulaciones (19 tests nuevos)

## Persistencia Completa de Simulaciones BIPV (MySQL + Resultados Horarios)
- [x] Crear tabla bipv_hourly_results en MySQL (JSON comprimido por mes, 12 registros por simulación)
- [x] Helpers de persistencia: saveHourlyResults, getHourlyResults, deleteHourlyResults
- [x] API tRPC: bipvSimulations.saveWithHourly (guardar resumen + datos horarios)
- [x] API tRPC: bipvSimulations.getWithHourly (obtener simulación completa)
- [x] API tRPC: bipvSimulations.compare (comparar 2+ escenarios)
- [x] UI: Selector de modelo de transposición (Isotrópico / Perez)
- [x] UI: Botón "Guardar Simulación" con nombre personalizado
- [x] UI: Panel de historial de simulaciones guardadas
- [x] UI: Tabla detallada de pérdidas ópticas (IAM, soiling, térmicas)
- [x] UI: Comparador de escenarios (seleccionar 2+ simulaciones y ver diferencias)
- [x] UI: Exportar CSV de resultados horarios
- [x] 19 tests unitarios para modelo Perez, hourly results, pérdidas y persistencia (714 tests totales)

## Conexión IAM+Soiling BIPV → Simulador de Energía
- [x] Crear interfaz BIPVToEnergyData con resultados IAM+Soiling para el Simulador
- [x] Agregar callback onSendToEnergySimulator en BIPVGlassSimulator
- [x] Agregar botón "Enviar al Simulador de Energía" en BIPVGlassSimulator
- [x] Agregar prop bipvData al EnergyProductionSimulator
- [x] Crear bridge de precarga en EnergyProductionSimulator (patrón PVWatts/PVGIS)
- [x] Conectar en Home.tsx: estado bipvToEnergyData, callback, y flujo de datos
- [x] Mapear paneles HITIIO/EINNOVA del catálogo IAM+Soiling a la selección del Simulador de Energía
- [x] Aplicar pérdidas IAM+Soiling como factores de corrección en el cálculo de producción
- [x] Tests unitarios para la integración (714 tests pasan)

## Paneles Personalizados en Ambos Simuladores
- [x] Agregar useCustomPanels + adapter a BIPVGlassSimulator (mapeo CustomPanel → BIPVGlassTechnology)
- [x] Agregar useCustomPanels + adapter a EnergyProductionSimulator (PanelTechSelector con savedPanels)
- [x] Mapear paneles HIITIO CdTe (H12-H15) y EINNOVA P18 al catálogo BIPV_GLASS_CATALOG

## Importar Fichas Técnicas PDF de Paneles
- [x] Endpoint tRPC para subir PDF y extraer texto
- [x] Procesamiento con LLM para extraer parámetros eléctricos/térmicos del PDF
- [x] Componente PDFPanelImporter con drag-and-drop y preview
- [x] Integrar PDFPanelImporter en PanelTechSelector (ambos simuladores)
- [x] Auto-rellenar formulario de panel personalizado con datos extraídos
- [x] Manejo de errores y validación de datos extraídos
- [x] Tests unitarios para la extracción de parámetros (5 tests, 719 total)

## Integración Completa IAM+Soiling BIPV ↔ Calculadora
- [x] Pasar obstacles (polígonos del diagrama solar) de ShadingCalculator al BIPVGlassSimulator
- [x] Pasar facadeAnalysis3D (factores de sombreado mensuales por fachada) al BIPVGlassSimulator
- [x] Aplicar factores de sombreado 3D hora a hora en el motor IAM+Soiling (evaluateObstacleShading mejorado)
- [x] Agregar selector multi-superficie arquitectónica: ventanas, pérgolas, marquesinas, pasamanos, techos
- [x] Cada superficie con geometría propia (tilt, azimuth, área, tipo montaje)
- [x] Simulación multi-superficie simultánea (no solo una fachada a la vez)
- [x] Banner de estado de integración: mostrar qué datos están cargados (EPW, modelo 3D, obstáculos)
- [x] Pre-configuración automática desde datos del modelo 3D (auto-seleccionar fachadas detectadas)
- [x] Convertir ObstaclePolygon[] (polígonos SVG) a formato angular compatible con evaluateObstacleShading

## Optimizador ROI BIPV - Alternativas Arquitectónicas y Técnicas
- [x] Motor de optimización ROI: análisis de sensibilidad multi-variable (tilt, azimuth, transparencia, área, montaje)
- [x] Cálculo de ahorro HVAC por reducción de carga solar (SHGC del vidrio BIPV vs vidrio convencional)
- [x] Valorización energética dual: autoconsumo (tarifa completa) vs inyección a red (tarifa reducida)
- [x] Comparador ROI por tipo de superficie (fachada vs pérgola vs marquesina vs techo)
- [x] Recomendaciones arquitectónicas automáticas para mejorar ROI negativo
- [x] Escenarios de financiamiento: subsidios, incentivos fiscales (Ley 1715), exclusión IVA, exención aranceles
- [x] Gráfico de sensibilidad ROI vs variables (tilt, transparencia, tarifa, autoconsumo)
- [x] Tabla de break-even: años para recuperar inversión por escenario (payback + VAN + TIR + LCOE)
- [x] Parámetros financieros editables (costos BIPV, tarifas, incentivos, meses refrigeración)
- [x] Ranking de viabilidad y punto de equilibrio ROI

## Reparar Visor 3D - Detección de Techos Inclinados Multi-Aguas
- [x] Corregir isRoofFace/isVerticalFace: las caras inclinadas (30-60°) no se clasifican como techo ni fachada
- [x] Agregar categoría "superficie inclinada" (tilt 15-75°) para capturar aguas de techos
- [x] Corregir clusterFacesIntoFacades: agrupar caras inclinadas por azimut para detectar cada agua por separado
- [x] Corregir ModelViewer3D: asignar caras de techo inclinado al cluster correcto por azimut (no solo al primer techo)
- [x] Nombrar correctamente: "Techo Agua Este", "Techo Agua Oeste" según azimut de la pendiente
- [x] Soporte para techos de 2 aguas (gable): detectar automáticamente las 2 caras inclinadas opuestas
- [x] Soporte para techos de 3 aguas: detectar las 3 caras inclinadas
- [x] Soporte para techos de 4 aguas (hip): detectar las 4 caras inclinadas
- [x] Soporte para curvaturas 3D (superficies trianguladas): agrupar triángulos curvos por normal promedio
- [x] Tests unitarios para detección de techos multi-aguas (719 tests pasan)

## Bug Área Duplicada en Techos Multi-Aguas + Optimizar Orientación BIPV
- [x] Diagnosticar bug: Techo Agua Oeste muestra el doble de área que Techo Agua Este (splitNonPlanarFace + northOffset fix)
- [x] Corregir tolerancia de azimut en agrupación de caras inclinadas (reducida a 30°)
- [x] Verificar cálculo de área de triángulos en el importador 3D (splitNonPlanarFace para quads no planares)
- [x] Botón "Optimizar Orientación BIPV" con ranking de producción estimada por agua de techo
- [x] Mostrar recomendación de mejor orientación para instalar paneles BIPV
- [x] Botón "⚡ Enviar al Simulador" en la mejor superficie del ranking → envía BIPVToEnergyData al Simulador de Energía

## Bug Persistente: Área Duplicada en Fachada Oeste (5431 m² → 1411 m²)
- [x] Diagnosticar causa raíz: SketchUp exporta front+back faces (mismos vértices, normales opuestas) → área se duplica
- [x] Implementar PASO 4a: Deduplicar por índices canónicos (eliminar 2947 back faces)
- [x] Diagnosticar segundo nivel: SketchUp modela grosor de losa/teja → 2 caras paralelas a 1m de distancia
- [x] Implementar PASO 4c: Deduplicar geométricamente (misma normal, área similar, centros alineados < 2m)
- [x] Verificar resultado: Techo Agua Oeste = 1411.4 m², Techo Agua Este = 1407.2 m² (ratio ≈ 1.0, simétrico)
- [x] Tests: 719 tests pasan correctamente

## Conflicto Panel BIPV → Simulador de Energía
- [x] Agregar panelId al BIPVToEnergyData para identificar el panel usado en IAM+Soiling
- [x] Cuando el Simulador recibe datos BIPV, sincronizar selectedTech con el panel correcto
- [x] Si el panel BIPV no existe en el catálogo del Simulador, crear panel virtual temporal con los datos BIPV
- [x] Mostrar indicador visual de que el panel fue sincronizado desde IAM+Soiling BIPV

## Modo Auto-optimizar BIPV (Todas las combinaciones)
- [x] Botón "Auto-optimizar" que ejecuta todas las combinaciones de tecnología × transparencia × superficie
- [x] Motor de optimización: iterar catálogo BIPV × niveles de transparencia × superficies del modelo 3D
- [x] Calcular ROI financiero para cada combinación (costo panel, energía producida, ahorro anual)
- [x] Mostrar tabla de resultados ordenada por mejor ROI global
- [x] Indicar la combinación ganadora con resumen ejecutivo
- [x] Botón "Aplicar configuración óptima" que selecciona la mejor combinación automáticamente

## Bug: Ángulos no se transfieren de IAM+Soiling BIPV al Simulador de Energía
- [x] Diagnosticar por qué tilt y azimuth del optimizador BIPV no se aplican en el Simulador
- [x] Corregir el bridge: normalizar azimut solar (-180..+180) a geográfico (0-360), seleccionar tipo de instalación compatible, aplicar ángulos DESPUÉS de la config
- [x] Verificar que la Configuración de Instalación refleje los ángulos del BIPV + banner muestra Tilt/Az

## Validación Cruzada Simulador vs IAM+Soiling BIPV
- [x] Indicador que compare producción anual del Simulador vs estimada por IAM+Soiling
- [x] Mostrar % de desviación y semáforo (verde <5%, amarillo 5-15%, rojo >15%)
- [x] Desglose mensual comparativo: BIPV como 4ª fuente en CrossValidationTable + columna AC + delta S-BIPV + estadísticas

## Botón "Volver al BIPV" desde el Simulador de Energía
- [x] Agregar callback onReturnToBIPV en EnergyProductionSimulator
- [x] Botón visible solo cuando hay datos BIPV activos
- [x] Al presionar, navegar a la pestaña IAM+Soiling BIPV con los parámetros actuales

## Tipo de Instalación "BIPV (Importado)"
- [x] Agregar 7ª opción "BIPV (Importado)" al array de configuraciones de instalación
- [x] Rangos libres: tilt 0-90°, azimut 0-360°, sin restricciones
- [x] Selección automática cuando llegan datos del optimizador BIPV
- [x] Badge/indicador visual que muestra "Ángulos del modelo 3D" + nombre de superficie
- [x] Sliders bloqueados (solo lectura) para evitar edición manual accidental
- [x] Icono Microscopio y descripción específica para BIPV integrado

## Alerta de Desviación Excesiva S-BIPV
- [x] Detectar meses donde delta S-BIPV > 15% en la tabla de validación cruzada
- [x] Mostrar panel de alerta con diagnóstico de posibles causas (expandible)
- [x] Incluir sugerencias de calibración específicas según el tipo de desviación (estacional/sistemático/aislado)
- [x] Semáforo visual: meses flaggeados con badges de color + probabilidad de cada causa

## Detección de Superficies Curvas (Bóvedas/Arcos)
- [x] Analizar OBJ de techo curvo: contar caras, verificar conectividad, rango de azimuts
- [x] Implementar detección de conectividad de malla (caras que comparten aristas por coordenadas)
- [x] Algoritmo de flood-fill para agrupar caras conectadas con variación gradual de normales (<45°)
- [x] Unificar superficie curva como un solo cluster: área total, tilt promedio ponderado, azimut circular
- [x] Nombrar correctamente: "Techo Curvo (Cúpula/Bóveda)" según tilt promedio
- [x] Marcar superficie como isCurved: true con azimuthRange y tiltRange
- [x] Mantener compatibilidad con techos planos e inclinados existentes (728 tests pasan)
- [x] Corregir auto-detección de eje vertical para bóvedas planas (reducir penalización heightRatio<0.1 si roofFaces>8)

## Soporte Multi-Formato 3D (DXF, DWG, FBX, XSI, VRML, STL, DAE/Collada, 3DS)
- [x] Implementar parser DXF (AutoCAD): extraer entidades 3DFACE, POLYFACE MESH
- [x] Implementar parser FBX (Blender, Revit, 3ds Max): via Three.js FBXLoader
- [x] Implementar parser VRML/WRL (formato legacy): via Three.js VRMLLoader
- [x] Implementar parser STL (formato universal de malla): ASCII y binario
- [x] Implementar parser DAE/Collada (Blender, SketchUp, Rhino): via Three.js ColladaLoader
- [x] Implementar parser 3DS (3ds Max legacy): via Three.js TDSLoader
- [x] Soporte DWG via conversión a DXF (mensaje de guía al usuario)
- [x] Soporte XSI/dotXSI via conversión (mensaje de guía al usuario)
- [x] Actualizar UI para aceptar todos los nuevos formatos en ambos importadores
- [x] Integrar todos los parsers con el pipeline de detección de curvas (OBJParseResult)
- [x] Tests para DXF y STL (31 tests pasando, 759 total)

## Mejoras UX Importador Multi-Formato
- [x] Actualizar texto botón "Cargar Archivo (OBJ/glTF/GLB)" → "Cargar Modelo 3D" en ambos importadores
- [x] Agregar zona de drag & drop para arrastrar archivos 3D directamente (con feedback visual)
- [x] Verificar detección de curvas con archivo DXF real (bóveda de cañón 16 segmentos, cúpula 60 caras, mixto plano+curvo)

## Fix: Δ% BIPV constante (Array(12).fill bug)
- [x] Corregir auto-optimizador: guardar produccionMensualKwh real del summary en vez de Array(12).fill(kwhYear/12)
- [x] Agregar produccionMensualKwh + iamPromedio + soilingPromedio + factorTermicoPromedio al tipo de autoOptResults
- [x] Verificar que la tabla de validación cruzada recibirá valores mensuales variables (767 tests pasan)

## Validación de coherencia de datos mensuales BIPV
- [x] Detectar cuando produccionMensualKwh tiene coeficiente de variación < 5% (datos planos/sintéticos)
- [x] Mostrar alerta visual en la tabla de validación cruzada cuando se detecten datos sospechosos
- [x] Sugerir al usuario re-ejecutar la simulación completa si los datos parecen artificiales
- [x] Detectar también valores negativos y outliers extremos (>3× mediana)
- [x] Tests: 5 tests específicos de coherencia (772 total)

## Auto-corrección de distribución plana BIPV
- [x] Agregar botón "⚡ Re-simular con datos reales" en la alerta de coherencia cuando se detecta flat_distribution en BIPV
- [x] El botón re-ejecuta runBIPVSimulation con los parámetros reconstruidos del bipvData actual
- [x] Actualizar bipvToEnergyData con la produccionMensualKwh real resultante (+ factores IAM/Soiling/Térmico)
- [x] La alerta desaparece automáticamente porque el CV sube > 5% con datos reales

## Fix: Desalineación parámetros BIPV → Simulador (Δ% -83%)
- [x] Corregir bridge BIPV: cuando no hay panelId, crear panel virtual de 1m² con potencia=1000×eficiencia
- [x] Corregir customArea: panel virtual usa 1.0 m² (no el área total del sistema)
- [x] Calcular panelQuantity correctamente: áreaTotal m² = cantidad de paneles virtuales de 1m²
- [x] Desactivar autoSyncQuantity en TODOS los casos del bridge BIPV (evitar que useEffect sobrescriba)
- [x] Cuando hay panelId con match: calcular paneles = área_total / área_panel
- [x] Cuando hay panelPmax < 1000W: calcular paneles = potencia_total / potencia_panel
- [x] Fallback: usar panel de referencia del catálogo y derivar cantidad
- [x] Agregar validación: si Δ% > 50% entre Simulador y BIPV, mostrar diagnóstico de parámetros desalineados (causa 'parameter_desync' con 95% prob)

## Botón Re-sincronizar parámetros en alerta Δ% > 50%
- [x] Agregar prop onResyncParams e isResyncing al componente BIPVDeviationAlert
- [x] Mostrar botón "⚡ Re-sincronizar parámetros" cuando avgDelta > 50% (con spinner de carga)
- [x] El botón re-aplica bipvData al Simulador reseteando bipvApplied=false
- [x] Pasar el callback desde EnergyProductionSimulator → BIPVDeviationAlert

## Validación preventiva BIPV→Simulador
- [x] Al aplicar bipvData al Simulador, verificar si potencia/panel > 1000W o área/panel > 5m²
- [x] Si se detecta anomalía, mostrar toast.warning con advertencia (duración 8s)
- [x] Auto-corregir automáticamente: forzar panel virtual de 1m² con potencia=1000×eficiencia

## Fix DEFINITIVO: Delta BIPV vs Simulador (desalineación de escala)
- [x] Problema raíz identificado: tabla comparaba kWh absolutos sin verificar que ambas fuentes tengan la misma capacidad instalada
- [x] Solución: normalizar producción BIPV al mismo kWp del Simulador (bipvScaleFactor = simKwp/bipvKwp)
- [x] Normalización se aplica automáticamente cuando la diferencia de kWp es >20%
- [x] Indicador visual azul en la tabla mostrando: kWp de cada fuente, factor de escala, y explicación
- [x] Campos agregados a ComparisonResult: bipvNormalized, bipvScaleFactor, bipvKwp, simKwp

## Columna Yield (kWh/kWp) IEC 61724 en tabla de validación cruzada
- [x] Agregar campo yield_kwh_kwp a cada fila mensual de la comparación (AC/kWp para cada fuente)
- [x] Agregar columna "Yield" toggleable en la tabla para Simulador, PVWatts, PVGIS y BIPV
- [x] Calcular yield mensual = AC_mensual / kWp_instalado para cada fuente
- [x] Agregar yield anual en la fila ANUAL (suma de yields mensuales = Yield específico anual)

## Sincronización bidireccional del factor de normalización
- [x] Cuando el usuario cambia panelQuantity o panelPower en el Simulador, recalcular simKwp automáticamente
- [x] useMemo de comparisonData ya depende de panelPower y panelQuantity (línea 881)
- [x] No requiere re-envío de datos desde BIPV — el factor se actualiza en tiempo real

## Columna Δ Yield (comparación de rendimiento específico entre fuentes)
- [x] Agregar columna Δ Yield (%) en la tabla de validación cruzada: (Yield_Sim - Yield_Ref) / Yield_Ref × 100
- [x] Calcular Δ Yield para cada par de fuentes: S vs PVW, S vs PVG, PVW vs PVG, S vs BIPV
- [x] Mostrar Δ Yield con colores (verde <5%, amarillo 5-15%, rojo >15%) igual que Δ% AC
- [x] Agregar toggle "Δ Yield" en la barra de columnas
- [x] Incluir Δ Yield en la fila ANUAL del footer

## Gráfico de barras Yield mensual agrupado por fuente
- [x] Crear gráfico de barras agrupadas (Recharts BarChart) mostrando Yield mensual por fuente
- [x] Barras para: Simulador (azul), PVWatts (cyan), PVGIS (verde), BIPV (teal)
- [x] Eje X: meses (Ene-Dic), Eje Y: kWh/kWp
- [x] Tooltip interactivo mostrando valores exactos de cada fuente
- [x] Posicionar debajo de la tabla de validación cruzada
- [x] Solo mostrar barras de fuentes que tengan datos disponibles

## KPI Yield Anual Total encima del gráfico de barras
- [x] Crear tarjetas KPI con Yield anual de cada fuente (Simulador, PVWatts, PVGIS, BIPV)
- [x] Calcular media de Yield entre todas las fuentes disponibles
- [x] Mostrar Δ% de cada fuente respecto a la media con colores semáforo
- [x] Posicionar las tarjetas KPI encima del gráfico de barras de Yield mensual
- [x] Diseño visual compacto con iconos y valores destacados

## Comparación de impacto BIPV vs Simulación Estándar
- [x] Calcular simulación "sin BIPV" (panel genérico sin IAM, sin soiling, sin factores térmicos BIPV)
- [x] Calcular simulación "con BIPV" (panel real con IAM, soiling, factor térmico, kBipv)
- [x] Mostrar tarjetas comparativas: Producción AC, Yield, PR, pérdidas térmicas, IAM, soiling
- [x] Calcular Δ absoluto y Δ% entre ambos escenarios para cada métrica
- [x] Gráfico de barras mensual comparando producción con vs sin BIPV
- [x] Tabla de desglose de pérdidas: cuánto aporta cada factor (IAM, soiling, térmico, kBipv)
- [x] Posicionar la sección después del banner BIPV en el Simulador de Energía

## Selector de panel de referencia (baseline) en comparación BIPV
- [x] Agregar estado para panel baseline seleccionado (default: genérico 400W)
- [x] Crear selector dropdown con opciones: Genérico 400W + todos los paneles del catálogo
- [x] Recalcular escenario "Sin BIPV" usando el panel baseline seleccionado
- [x] Actualizar KPIs, tablas y gráfico en tiempo real al cambiar el baseline

## Filtro de paneles seleccionados en auto-optimizador BIPV
- [x] Agregar checkboxes de selección en la tabla de ranking del optimizador
- [x] Implementar modo "Evaluar solo seleccionados" que filtre el ranking a los paneles marcados
- [x] Vincular los paneles del Trade-off con la selección del optimizador
- [x] Mostrar indicador visual de cuál es el óptimo entre los seleccionados
- [x] Permitir toggle entre "Ranking completo" y "Solo seleccionados"

## Botón "Aplicar óptimo seleccionado" + Gráfico Radar comparativo
- [x] Agregar botón "Aplicar óptimo seleccionado al Simulador" en el panel violeta de seleccionados
- [x] El botón envía el mejor de los marcados (no el global) al Simulador de Energía via onSendToEnergySimulator
- [x] Gráfico radar (Recharts RadarChart) comparando paneles seleccionados en 5 ejes: kWh, ROI, Payback, LCOE, kWh/m²
- [x] Normalizar valores al rango 0-100% para que el radar sea visualmente comparable
- [x] Mostrar radar solo cuando hay 2+ paneles seleccionados

## Corrección interpretación soiling en bridge BIPV→Simulador
- [x] soilingPromedio en IAM+Soiling es la PÉRDIDA (0.038 = 3.8% pérdida), NO el factor de retención
- [x] En el preload bridge: setSoilingLosses debe usar soilingPromedio×100 directamente (ya es pérdida %)
- [x] En la comparación BIPV: soilingLoss debe usar bipvData.soilingPromedio×100 (ya es pérdida %)
- [x] Verificar que el banner muestra correctamente "Soiling Prom. 3.8%" como pérdida
- [x] Verificar PR resultante sea coherente (0.7-0.9 típico) — corregido, ahora soiling aplica correctamente

## Validación PR > 1.0 y tooltip explicativo
- [x] Agregar alerta visual cuando PR > 1.0 indicando error en datos de entrada
- [x] Mostrar mensaje explicativo de posibles causas (irradiancia incorrecta, capacidad mal calculada)
- [x] Incluir tooltip junto al valor de PR con fórmula: PR = Yf / Yr = (E_AC / P_nom) / (H_POA / G_ref)
- [x] Mostrar valores numéricos de Yf y Yr en el tooltip para facilitar diagnóstico
- [x] Aplicar validación tanto en el PR principal como en la comparación BIPV vs Baseline

## Botón "Diagnosticar PR" cuando PR > 100%
- [x] Agregar botón "Diagnosticar PR" visible solo cuando PR > 100%
- [x] Al hacer clic, analizar: H_POA real vs H_POA esperada para tilt/azimut configurado
- [x] Comparar P_nom calculada vs P_nom esperada según paneles × potencia
- [x] Verificar coherencia entre área, cantidad de paneles y potencia total
- [x] Mostrar panel de diagnóstico con sugerencias específicas de corrección
- [x] Incluir valores esperados vs reales para cada parámetro analizado

## Implementar factor IAM ASHRAE en el motor de producción del Simulador
- [x] Agregar campo iamLosses (%) al interface SystemLosses en energyProduction.ts
- [x] Aplicar factor IAM como pérdida en calculateACPower: power *= (1 - iamLosses/100)
- [x] En el bridge BIPV→Simulador: transferir iamPromedio como pérdida IAM al Simulador
- [x] Agregar estado iamLosses en EnergyProductionSimulator con default 0% (sin BIPV)
- [x] Mostrar control editable de IAM losses en la sección de pérdidas del sistema
- [x] Incluir IAM en la tabla de desglose de pérdidas mensuales
- [x] Actualizar tests para verificar que IAM se aplica correctamente (772 tests pasan)

## Indicador visual IAM en banner BIPV
- [x] Mostrar badge/indicador "IAM aplicado: X%" en el banner de datos BIPV del Simulador
- [x] Mostrar el valor de pérdida IAM activa junto a los otros indicadores (Soiling, F.Térmico)
- [x] Colorear en verde si IAM < 15%, amarillo 15-25%, rojo > 25%

## Cálculo de IAM mensual variable (no promedio anual fijo)
- [x] Calcular IAM mensual usando ángulo de incidencia horario del EPW para cada mes
- [x] Transferir array de 12 valores IAM mensuales desde IAM+Soiling al Simulador
- [x] Aplicar IAM mensual variable en calculateAnnualProduction en vez del promedio anual
- [x] Mostrar los 12 valores IAM mensuales en el banner BIPV y sección de pérdidas
- [x] Mantener compatibilidad: si no hay datos mensuales, usar el promedio anual como fallback

## Soiling mensual variable en el motor de producción
- [x] Agregar parámetro soilingMensualData (12 valores % pérdida por mes) a calculateAnnualProduction
- [x] Aplicar soiling mensual variable sobreescribiendo systemLosses.soilingLosses por mes
- [x] Transferir soilingMensual desde bridge BIPV al estado del Simulador (setSoilingMensualData)
- [x] Mostrar indicador "Soiling mensual variable activo" en sección de pérdidas con rango min-max
- [x] Mostrar nota en banner BIPV con los 12 valores de soiling mensual
- [x] Mantener compatibilidad: si no hay datos mensuales, usar el promedio anual como fallback

## Fix: Producción AC Baseline absurdamente baja en comparación BIPV vs Estándar
- [x] Diagnosticar bug: panel de referencia (baseline) produce ~37,895 kWh/año en vez de ~800,000+ kWh/año
- [x] Causa raíz: efficiency se dividía por 100 (0.232 en vez de 23.2) al construir panelEstandar, pero calculateAnnualProduction espera % directo
- [x] Corregir: efficiency: baselinePanel.efficiencySTC (sin /100) y genérico: 20 (no 0.20)
- [x] Corregir display de eficiencia estándar en tabla comparativa (ya no multiplica ×100)
- [x] Verificar tests (772/772 pasan, 0 errores en corrección)

## Fix: Yr (Reference Yield) de 8,599 h — sobreestimación ~4-5x del POA importado desde PVGIS
- [x] Diagnosticar cómo Heatmap PVGIS exporta datos POA al Simulador de Energía
- [x] Identificar error de unidades/escala: divisor /5 en vez de /24 causa sobreestimación 4.8x
- [x] Corregir la conversión: cambiado /5 a /24 en Home.tsx línea 351 (Yr ahora ~1,663 h)
- [x] Verificar coherencia: Yr=1,663h, Yield BIPV~1,114 kWh/kWp, 772 tests pasan

## Feature: IAM y Soiling horario en Simulador Principal (como motor BIPV)
- [x] Modificar calculateAnnualProduction para aplicar IAM pre-cálculo (solo componente directa del POA)
- [x] Modificar calculateAnnualProduction para aplicar soiling pre-cálculo (sobre POA total)
- [x] Pasar directPOA, diffusePOA y reflectedPOA separados desde EnergyProductionSimulator al motor
- [x] Eliminar doble conteo (iamLosses=0 y soilingLosses=0 en systemLosses cuando se usa pre-cálculo)
- [x] Agregar campo iam a AnnualProduction.losses y weightedLosses para reporte correcto
- [x] Verificar que Δ Yield vs motor BIPV se reduce a <10% (estimado: de 13% a ~4-5%)
- [x] 772 tests pasan correctamente

## Feature: Validación de orden de importación al Simulador
- [x] Impedir exportar IAM+Soiling BIPV al simulador si no hay POA cargado (PVGIS/PVWatts/EPW)
- [x] Mostrar mensaje informativo: "Primero importe datos de irradiación desde Heatmap PVGIS o PVWatts" (toast.error con duración 8s)
- [x] Agregar indicador visual de estado en el botón de exportación del módulo IAM+Soiling BIPV (⚠️ + tooltip hover)
- [x] Toast de confirmación cuando la exportación es exitosa (✅ Datos IAM+Soiling enviados al Simulador)

## Fix: Lc negativo y Δ Yield incoherente cuando IAM/Soiling se aplican pre-cálculo
- [x] Fix Yr incoherente: cuando IAM/soiling se aplican pre-cálculo sobre POA, el Yr usa rawPOA (sin IAM/soiling) pero Ya usa effectivePOA (con IAM/soiling reducido), causando Ya > Yr y Lc negativo
- [x] Corregir cálculo de Yr para reflejar las pérdidas pre-cálculo (IAM+soiling) que ya fueron aplicadas al POA antes de entrar al motor
- [x] Corregir Lc_temp negativo: la ganancia aparente de temperatura (T_cell baja por menor POA) debe reflejarse correctamente
- [x] Verificar coherencia: Yr ≥ Ya ≥ Yf siempre, Lc ≥ 0, Ls ≥ 0
- [x] Actualizar tests unitarios para el nuevo comportamiento de Yr con pérdidas pre-cálculo (779 tests pasan)
