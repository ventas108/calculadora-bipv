# Manual de Usuario — Calculadora BIPV (fuente: MANUAL_CALCULADORA_BIPV_v3.4_agosto2026.docx)

## Manual de Usuario — Calculadora BIPV

### Innovación Química

Versión: Agosto 2026 | URL: calc.innovacionquimica.com.co

────────────────────────────────────────────────────────────

## Tabla de contenido

- Descripción general
- Flujo de trabajo recomendado  ACTUALIZADO
- Página 1 — Proyecto  ACTUALIZADO
- Página 2 — Recurso Solar  ACTUALIZADO
- Página 3 — Motor IV  ACTUALIZADO
- Página 4 — Dimensionamiento  ACTUALIZADO
6b. Página 4b — Comparador de Inversores ⚖️  ACTUALIZADO

6c. Página 4c — Comparador de Paneles 🧩  NUEVO

6d. Página 4d — Comparador de Orientación 🧭  NUEVO

6e. Página 18 — 🤖 Análisis IA y los Analistas de Producción  NUEVO

- Página 5b — Motor Óptico
- Página 5 — Mismatch y Bypass Diodes  NUEVO
8a. Página 5a — Sombras desde SketchUp 🌳  NUEVO

8b. Página 9 — Vista 3D y Multi-Superficie  NUEVO

- Página 6 — Producción Anual  ACTUALIZADO
- Página 7 — Análisis Financiero  ACTUALIZADO
- Página 8 — Presupuesto Bancable  ACTUALIZADO
- Página 11 — Baterías y Balance  ACTUALIZADO
- Página 10 — Reporte PDF  ACTUALIZADO
- Página 15 — Catálogo de Inversores PDF  NUEVO
- Catálogo de Baterías — carga robusta del Excel  ACTUALIZADO
13e. Página 19 — 🔒 Ledger de Auditoría  NUEVO
13f. Página 20 — ⚡ Diagrama Unifilar (batería + multi-superficie + sellado Ledger + detalle RETIE)  ACTUALIZADO
13g. Página 21 — 📋 Ficha de Validación RETIE (dashboard + motor de validación, universal N inversores)  NUEVO

- Calculadora de Sombreado 3D
- Cadena completa — bypass y multi-superficie
- Interpretación de resultados clave
- Preguntas frecuentes
- Anexo — Sombras desde Site Designer / Andrew Marsh (ruta externa, agosto 2026)  NUEVO
- Anexo — Actualizaciones 6-7 de agosto 2026 (Asistente, cuentas, proyectos y Vista 3D solar)  NUEVO
- Anexo — Actualizaciones del 21 de agosto de 2026 (comparadores, validación Motor IV, consumo y excedentes)  NUEVO
- Anexo — Actualizaciones del 22 de agosto de 2026 (carga de cotizaciones PDF/Word en Presupuesto)  NUEVO
- Anexo — Actualizaciones del 25 de agosto de 2026 (Ledger de Auditoría, cadena de hashes)  NUEVO
- Anexo — Actualizaciones del 26 de agosto de 2026 (validación cruzada contra PVsyst, corrección de timezone en TMY de PVGIS)  NUEVO
────────────────────────────────────────────────────────────

## 1. Descripción general

La Calculadora BIPV es una herramienta de simulación fotovoltaica especializada en sistemas integrados en edificios (Building-Integrated Photovoltaics). Está diseñada para proyectos en Colombia con paneles SolTech (ASP-ST1-T40) e inversores Growatt.

Tecnologías simuladas:

- Paneles monocristalinos BIPV de fachada (ASP-ST1-T40, 200 Wp)
- Inversores Growatt (catálogo desde Excel con motor de emparejamiento automático)
- Baterías de litio (catálogo configurable)
- Modelo óptico completo: IAM, soiling, efecto térmico confinado BIPV
- Modelo eléctrico completo: bypass diodes bajo sombra parcial
Datos de entrada requeridos:

- Archivo TMY (EPW) de la ubicación del proyecto
- Área y orientación de la fachada
- Perfil de consumo energético del edificio (para balance con batería)
────────────────────────────────────────────────────────────

## 2. Flujo de trabajo recomendado

1 Proyecto → 2 Recurso Solar → (3 Motor IV) → 4 Dimensionamiento
    → (5b Motor Óptico) → 5 Mismatch/Bypass → 6 Producción
    → [9 Vista 3D Multi-Sup ← opcional]
    → 7 Financiero → 8 Presupuesto → 11 Baterías → 10 Reporte PDF

Páginas obligatorias: 1, 2, 4, 6, 7, 10

Páginas opcionales pero recomendadas para BIPV urbano: 3, 5b, 5, 9 (multi-sup), 11

Cuándo usar Página 9 — Vista 3D: Si el proyecto tiene más de una superficie

(ej. fachada sur + techo plano + pérgola), ejecuta la Página 9 para combinar las

producciones y alimentar Financiero con la E_ac total del sistema.

⚠️ Regla de datos: Cada página guarda sus resultados en memoria de sesión

(session_state). Si recargas el navegador, todos los datos se pierden y

debes ejecutar el flujo desde el principio.

────────────────────────────────────────────────────────────

Flujo recomendado para proyectos agrivoltaicos  ACTUALIZADO (26-ago-2026 — ahora incluye Motor Óptico)

1 Proyecto (tipo Granja fotovoltaica + factor de ocupación) → 2 Recurso Solar (verificar GCR sincronizado → Calcular POA) → 4 Dimensionamiento (área útil) → 5b Motor Óptico (IAM — ver nota abajo, montaje "Ventilado libre") → 9 Vista 3D (verificación visual de filas y cultivo) → 6 Producción → 7 Financiero → 8 Presupuesto → 10 Reporte PDF.

Regla de oro agrivoltaica: factor de ocupación (Proyecto) = GCR (Recurso Solar). Si cambias uno, revisa el otro.

Por qué Motor Óptico ahora es obligatorio para Granja FV (26-ago-2026): el flujo anterior lo saltaba, asumiendo que el IAM (pérdida por reflexión angular) era despreciable fuera de fachadas BIPV. Validando el proyecto Agrivoltaico Urabá contra PVsyst se confirmó que NO es despreciable en campo abierto: sin Motor Óptico, la app sobreestimaba producción **+3,1%** frente a PVsyst; corriendo Motor Óptico con IAM, la diferencia bajó a **−0,70%** (mejor incluso que el resto de las validaciones). Detalle completo, cascada de pérdidas de PVsyst y la cuenta que reconcilia el gap en `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md` del repo.

En Página 1 — Proyecto, cuando el tipo de instalación es "Granja fotovoltaica", Página 5b — Motor Óptico ahora preselecciona automáticamente el montaje **"Ventilado libre (k=1,0)"** en vez del default de fachada confinada (k=1,3) — una granja FV con estructura elevada a campo abierto no tiene el confinamiento térmico de una fachada, y usar k=1,3 ahí penalizaría la temperatura de celda sin motivo físico. El resto de los parámetros de Motor Óptico (vidrio, transparencia, soiling) se dejan en sus defaults — solo el montaje cambia automáticamente por tipo de proyecto.

────────────────────────────────────────────────────────────

## 3. Página 1 — Proyecto

Propósito: Registrar los datos básicos del proyecto y configurar el tipo de instalación que determina los parámetros por defecto del sistema.

### Campos obligatorios

- Nombre del proyecto y empresa cliente
- Ciudad (selección desde lista; define las coordenadas y el TMY por defecto)
- Tipo de instalación ← nuevo selector clave (ver tabla más abajo)
### Campos opcionales

- Descripción del sistema BIPV
- Datos del contacto
────────────────────────────────────────────────────────────

### Selector de Tipo de instalación (nuevo)

El selector "Tipo de instalación" reemplaza al anterior campo genérico de área. Su función principal es configurar automáticamente los parámetros físicos correctos para cada tecnología de integración fotovoltaica.

Tipos disponibles y parámetros por defecto

Tipo  │  Densidad recomendada (W/m²)  │  PR típico  │  Tilt por defecto  │  ¿Por qué ese tilt?

🏢 Fachada BIPV  │  80 – 180 W/m²  │  0.65  │  90°  │  Panel vertical integrado en muro

🏠 Techo inclinado BIPV  │  100 – 200 W/m²  │  0.75  │  15°  │  Inclinación mínima típica en Colombia

⛱️ Pérgola BIPV  │  60 – 150 W/m²  │  0.70  │  10°  │  Estructura casi horizontal para generar sombra

Marquesina BIPV  │  70 – 160 W/m²  │  0.68  │  30°  │  Ángulo de voladizo estándar

🏚️ Techo plano  │  120 – 220 W/m²  │  0.78  │  10°  │  Mínimo para garantizar escorrentía

Granja FV  │  130 – 250 W/m²  │  0.80  │  15°  │  Ángulo óptimo para latitud Colombia (≈5°N)

¿Qué ocurre al cambiar el tipo?

Cuando seleccionas un tipo de instalación, la app actualiza en cascada tres parámetros:

- Densidad de potencia (W/m²): el slider en esta misma página se mueve al valor central del rango recomendado para ese tipo.
- Performance Ratio (PR): el campo PR se actualiza al valor típico de la tecnología.
- Inclinación (tilt): el slider de tilt en Página 2 — Recurso Solar se inicializa al ángulo físicamente correcto para ese tipo de instalación.
Importante: Si el usuario ajusta manualmente cualquiera de estos valores después de elegir el tipo, sus ajustes se respetan. El reseteo automático ocurre solo cuando cambias el tipo de instalación.

────────────────────────────────────────────────────────────

### Alertas reactivas de densidad y PR (nuevo)

La app valida en tiempo real que la densidad y el PR ingresados sean coherentes con el tipo de instalación seleccionado. Si algún valor está fuera del rango recomendado, aparece una alerta inmediatamente al mover el slider, sin necesidad de hacer clic en Guardar:

⚠️ La densidad ingresada (50 W/m²) está fuera del rango recomendado
   para Fachada BIPV (80–180 W/m²).
   Un valor por debajo del mínimo puede subestimar la producción del sistema.

⚠️ El PR ingresado (0.90) está por encima del valor típico para
   Fachada BIPV (PR típico: 0.65). Verifica que incluya todas las pérdidas
   reales: ópticas, térmicas, cableado y mismatch.

¿Puedo ignorar la alerta? Sí. Las alertas son informativas y no bloquean el cálculo. Son útiles para detectar errores de entrada (por ejemplo, ingresar la densidad en W en lugar de W/m², o un PR optimista que no incluye pérdidas BIPV).

¿Cuándo no aparece la alerta? Si densidad y PR están dentro del rango del tipo seleccionado, la interfaz está limpia sin ningún mensaje.

────────────────────────────────────────────────────────────

### Panel "Datos del sitio" (actualización en tiempo real)

El panel inferior de la página muestra las coordenadas y altitud del proyecto. Este panel se actualiza en tiempo real cada vez que:

- Cambias la ciudad en el selector
- Modificas manualmente las coordenadas en el expander de ajuste fino
Cuando las coordenadas mostradas corresponden al centroide de la ciudad (no al predio exacto), aparece un indicador ⚠️ Coordenadas del centroide de la ciudad para recordar que se deben ajustar al predio real antes de ejecutar la simulación solar.

Resultado: Al guardar, la app persiste el tipo de instalación, el área, la densidad, el PR y el tilt por defecto en memoria de sesión. Estos valores se usan en Página 2, Página 4, Página 6 y el Reporte PDF.

────────────────────────────────────────────────────────────

Factor de ocupación con paneles — agrivoltaica  NUEVO (5-ago-2026)

Nuevo campo "Factor de ocupación con paneles (%)" (rango 5–100, por defecto 100). Define qué porcentaje del terreno bruto queda cubierto por paneles; el resto queda libre para el cultivo. La app calcula el área útil = área × factor/100 y la usa en Dimensionamiento, Presupuesto y Reporte PDF.

- Ejemplo: terreno de 3 000 m² con factor 30% → 900 m² útiles para paneles (~340 paneles en vez de ~1 040) y 2 100 m² libres para el cultivo.
- El factor se guarda en el proyecto (proyecto_actual.json) y se restaura al recargarlo.
⚠️ Para no cometer errores: si tu proyecto es una granja con cultivo, ajusta el factor ANTES de pasar a Dimensionamiento. Si lo dejas en 100%, el conteo de paneles, el presupuesto y el USD/m² se calcularán como si todo el terreno llevara paneles.

────────────────────────────────────────────────────────────

## 4. Página 2 — Recurso Solar

Propósito: Cargar el archivo climático TMY y calcular la irradiancia sobre el plano de instalación (POA).

### Pasos

- Cargar archivo EPW:
- Descarga el EPW de https://energyplus.net/weather

- Busca la ciudad más cercana al proyecto

- Arrastra el archivo .epw al uploader

- Configurar la geometría de instalación:
- Orientación (azimuth): 0° = Norte, 90° = Este, 180° = Sur, 270° = Oeste

- Inclinación (tilt): ver sección "Tilt por defecto según tipo" más abajo

- Área de instalación (m²): área total donde van los paneles

- Ejecutar cálculo:
- Clic en "Calcular POA"

- La app calcula la irradiancia en el plano de instalación hora a hora (8 760 horas)

Resultados:

- POA bruta anual (kWh/m²/año)
- Heatmap de irradiancia horaria (meses × horas del día)
- Diagrama solar con la trayectoria del sol sobre el plano
Nota timezone: El diagrama solar usa UTC. Para Colombia (UTC-5), la hora solar

de mediodía aparece a las 17:00 UTC en el diagrama.

────────────────────────────────────────────────────────────

### Tilt por defecto según tipo de instalación (nuevo)

Cuando llegas a esta página después de configurar el tipo de instalación en Página 1, el slider de inclinación (tilt) ya está pre-cargado con el ángulo físicamente correcto para tu tipo:

Tipo de instalación  │  Tilt pre-cargado  │  Referencia física

🏢 Fachada BIPV  │  90°  │  Panel integrado verticalmente en muro

🏠 Techo inclinado BIPV  │  15°  │  Inclinación mínima típica en edificios Colombia

⛱️ Pérgola BIPV  │  10°  │  Estructura de cobertura casi horizontal

Marquesina BIPV  │  30°  │  Voladizo en ángulo estándar de marquesina

🏚️ Techo plano  │  10°  │  Mínimo para escorrentía en techos planos

Granja FV  │  15°  │  Óptimo para latitud Colombia (~5° N)

Un banner informativo en la parte superior de la página muestra el tipo activo y el ángulo sugerido, por ejemplo:

ℹ️ Tipo de instalación: Fachada BIPV
   Tilt sugerido: 90° (panel vertical integrado en muro).
   Puedes ajustar el slider si el diseño específico requiere otro ángulo.

¿Puedo cambiar el tilt manualmente? Sí. El valor pre-cargado es una sugerencia. Si tu diseño requiere un ángulo diferente (por ejemplo, una fachada inclinada a 75°), mueve el slider libremente. La app guardará tu selección manual para esa sesión.

¿Qué pasa si vuelvo a cambiar el tipo en Página 1? El tilt se resetea al valor correspondiente al nuevo tipo. Esto evita que el ángulo de una fachada quede accidentalmente en un proyecto de granja FV.

Impacto en el cálculo: El tilt es el parámetro geométrico más sensible en el cálculo de POA. Una fachada vertical (90°) capta principalmente irradiancia difusa y directa de bajo ángulo solar; un techo plano (10°) capta mucho más irradiancia directa anual. Usar el tilt incorrecto puede llevar a errores de ±20–30% en la POA anual.

────────────────────────────────────────────────────────────

Rendimiento (nuevo — agosto 2026): el heatmap de irradiancia carga ahora en la mitad del tiempo. Se eliminó una llamada duplicada al servicio PVWatts, sin ningún cambio en los resultados numéricos.

────────────────────────────────────────────────────────────

### Simulación bifacial 🔄  NUEVO

Si el panel del proyecto es bifacial (capta luz también por la cara trasera), la página 2 muestra el expander «🔄 Simulación bifacial». Se activa automáticamente cuando el panel elegido tiene el dato de bifacialidad en el catálogo (columna BifacialidadPct); si no lo tiene, puedes activarlo manualmente e ingresar el valor de la ficha técnica.

Controles disponibles:

- Bifacialidad (%): cuánto rinde la cara trasera respecto a la frontal (típico 70–85 % en paneles vidrio-vidrio). Sale de la ficha técnica del panel.
- Altura de montaje (m): distancia del borde inferior del panel al suelo. A mayor altura, más luz reflejada llega a la cara trasera.
- Albedo trasero: reflectividad de la superficie bajo/detrás del panel (0.20 pasto/concreto gris, 0.50 membrana blanca, 0.80 pintura reflectiva).
- GCR (Ground Coverage Ratio): qué tan juntas están las filas de paneles. Filas muy juntas (GCR alto) se sombrean entre sí y reducen la ganancia.
El cálculo usa el modelo infinite_sheds de pvlib: la POA global incluye la cara frontal (con sombreado fila a fila) más la trasera ponderada por la bifacialidad. La métrica «Ganancia bifacial» muestra el % de energía extra anual, y ese valor viaja automáticamente a Producción, Financiero y Reporte PDF.

⚠️ IMPORTANTE: la ganancia bifacial solo es real si la cara trasera efectivamente recibe luz. No actives bifacial en paneles vidrio-backsheet (opacos) ni esperes ganancias grandes con albedo bajo.

Fachadas verticales: adosada vs ventilada  NUEVO

Cuando la inclinación es ≥ 80° (fachada vertical), aparece el selector «Montaje de la fachada» con dos opciones:

- Adosada al muro (sellada) — opción por defecto: el panel va pegado al muro y la cara trasera no recibe luz. La app anula automáticamente la ganancia trasera (factor de vista 0) y bloquea el slider de albedo trasero. Es el caso típico BIPV.
- Separación ventilada con superficie reflejante: hay cámara de aire y una superficie clara detrás (muro pintado de blanco, por ejemplo). La ganancia trasera sí aplica y puedes ajustar el albedo trasero.
🚨 ALERTA PARA EVITAR ERRORES: si tu fachada va pegada al muro, deja la opción «Adosada» (la que viene por defecto). Elegir «ventilada» sin que exista la cámara de aire real infla la producción estimada y el proyecto financiero quedará sobreestimado.

Nota: el slider de Albedo del suelo (parte superior de la página) ahora sí afecta el cálculo de POA. El valor por defecto 0.20 es adecuado para la mayoría de los sitios urbanos.

────────────────────────────────────────────────────────────

GCR sincronizado con el factor de ocupación  NUEVO (5-ago-2026)

El control "GCR (cobertura del suelo)" del modelo bifacial ahora arranca con el mismo valor que el factor de ocupación definido en Proyecto (factor 30% → GCR 0.30), porque ambos representan la misma fracción de suelo cubierta por paneles. La sincronización solo aplica la primera vez; después se respeta el valor que guardes aquí.

- Si el GCR y el factor difieren en más de 15 puntos, aparece una alerta con el valor sugerido — el sombreado entre filas y el conteo de paneles estarían usando supuestos distintos.
⚠️ Para no cometer errores: no subas el GCR "para producir más" sin cambiar también el factor de ocupación en Proyecto. Un GCR alto junta las filas (más sombra mutua y menos luz al cultivo); mantén ambos valores alineados.

────────────────────────────────────────────────────────────

### Chequeo QCRad automático — cierre físico del TMY  NUEVO (27-ago-2026)

`calculos/solar.py::calcular_poa()` ahora valida automáticamente, en cada llamada, que el TMY sea físicamente consistente: GHI ≈ DNI·cos(zenit) + DHI (algoritmo QCRad, Long & Shi 2008 — el estándar BSRN de control de calidad de radiación solar). Si más del 2% de las horas de día se salen de esa consistencia por más de 50 W/m², la app emite un `UserWarning` automático.

**Por qué se agregó**: auditando un motor BIPV aparte que aportó el usuario, su propio chequeo de este tipo detectó que el script tenía un bug real de 30 minutos de desfase entre el TMY y la posición solar — misma familia que el bug de 5 horas de `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md` (26-ago-2026). Antes de este cambio, la app no tenía ninguna validación automática equivalente — ese tipo de bug solo se detectaba a mano, con scripts de diagnóstico sueltos.

**De dónde viene el algoritmo**: pvlib no trae este chequeo. Existe en el paquete hermano oficial `pvanalytics` (mismo equipo de NREL/pvlib) como `quality.irradiance.check_irradiance_consistency_qcrad()` — se verificó leyendo su código fuente real antes de decidir. Se portó solo la fórmula central del algoritmo (cierre físico) directamente a `calculos/solar.py`, **sin agregar `pvanalytics` como dependencia** — esa librería arrastra `statsmodels` y `scikit-image`, pesados y no usados para nada más que esta única función.

**Cómo funciona**: el resultado (`horas_evaluadas`, `horas_inconsistentes`, `pct_inconsistente`, `diferencia_media_wm2`, `diferencia_maxima_wm2`) queda disponible en `poa.attrs["qcrad"]` — no cambia las columnas ni el contrato del DataFrame que devuelve `calcular_poa()`, así que no rompe ningún código existente que ya lo llama. Corre una sola vez por llamada (no depende de tilt/azimuth/bifacial), y sobrevive al `.copy()` de la rama bifacial.

**Verificado con datos reales antes de integrar**: TMY real de PVGIS para Bogotá (proyecto Teusaquillo, coordenadas reales de `datos/ciudades_colombia.py`) → 0% de horas inconsistentes, diferencia media 0,3 W/m², máxima 2,8 W/m². El mismo TMY desfasado artificialmente 30 minutos → 20,2% de horas inconsistentes, dispara el warning correctamente. 7 tests nuevos en `tests/test_solar_qcrad.py`, incluyendo un caso mínimo calculado a mano (3 "horas" con el resultado esperado derivado manualmente, no solo verificado con `isinstance`).

## 5. Página 3 — Motor IV

Propósito: Modelar la curva corriente-voltaje (I-V) del panel usando el modelo de 5 parámetros (SDM).

¿Cuándo usar?

- Cuando tienes la ficha técnica completa del panel (Voc, Isc, Vmpp, Impp, α, β, γ)
- Para verificar que los parámetros del catálogo son coherentes
¿Cuándo no es necesario?

- Si usas los paneles ASP-ST1-T40 del catálogo estándar (ya tienen SDM calibrado)
- Para una estimación rápida sin análisis eléctrico detallado
El Motor IV se activa automáticamente cuando el panel tiene ficha técnica completa

en el catálogo. No requiere intervención manual.

────────────────────────────────────────────────────────────

Activación automática y defensa Ns half-cut  NUEVO (5-ago-2026)

Si el panel seleccionado tiene su ficha técnica completa (Voc, Isc, Vmp, Imp, Ns y coeficientes térmicos), el Motor IV se activa automáticamente sin configuración manual.

- Nueva defensa para paneles half-cut: el extractor de fichas infiere el número de celdas en serie (Ns) desde el conteo de semiceldas y lo verifica contra el Voc (regla práctica: Ns ≈ Voc / 0.74 en paneles HJT).
- Si el Ns auto-extraído es inconsistente, el Motor IV lo corrige al vuelo y el validador físico lo marca en el diagnóstico.
⚠️ Para no cometer errores: en paneles half-cut la ficha suele reportar el TOTAL de semiceldas (p. ej. 144); el Ns eléctrico es la mitad (72) porque hay dos strings en paralelo. Si cargas un panel a mano, verifica el Ns con la regla Voc/0.74.

────────────────────────────────────────────────────────────

### Validación automática SDM vs ficha técnica — alarma y texto técnico  NUEVO (21-ago-2026)

El Motor IV (modelo De Soto/pvlib de 5 parámetros) es el motor de cálculo detrás de las curvas de Página 3, y también se reutiliza internamente en Producción (Modo IV), Mismatch/Bypass y Vista 3D (MPPT combinado). Para saber si ese modelo reproduce fielmente la ficha del panel, la app ahora valida automáticamente 5 métricas en condiciones STC (1000 W/m², 25 °C): Voc, Isc, Vmp, Imp y Pmax, cada una con tolerancia de 5% de error frente al valor de la ficha.

- La validación corre SOLA (sin apretar ningún botón) al entrar a 📐 Dimensionamiento, siempre que el panel tenga ficha calibrada (no aplica a paneles "estimados", que no tienen ficha completa).
- Si las 5 métricas están dentro de tolerancia, verás un mensaje corto: "✅ Motor IV: SDM validado (Voc/Isc/Vmp/Imp/Pmax dentro de 5% de error)".
- Si alguna métrica falla, aparece una alarma 🔴 con un texto técnico específico: cuáles métricas fallaron, el valor calculado, el valor de ficha, el % de error exacto de cada una, y una causa técnica probable por métrica (por ejemplo: Rs mal ajustada afecta Vmp/Imp; Rsh afecta la pendiente cerca de Isc; a_ref/I_o_ref afectan Voc). Es un texto determinístico igual que todo el resto del Manual — no requiere clave de IA ni gasta ninguna llamada al agente.
- Puedes además correr la validación manualmente en 🔬 Motor IV con el botón "Ejecutar validación", que muestra el mismo texto técnico.

¿Dónde más aparece esta alarma? Si el SDM no valida, 📊 Producción, 🔀 Mismatch y 🗺️ Vista 3D muestran el mismo aviso 🔴 apenas abres la página (mientras sigas con el mismo panel) — porque las tres reutilizan el SDM del panel para sus propios cálculos (curva IV completa en Producción/Modo IV, bypass diodes en Mismatch, MPPT combinado multi-superficie en Vista 3D).

⚠️ Para no cometer errores: un SDM que no valida NO bloquea el cálculo — la app sigue funcionando con esos parámetros, pero los resultados de energía, mismatch o MPPT combinado pueden tener más error del esperado. Si ves la alarma 🔴, revisa primero los datos de la ficha técnica del panel (Voc, Isc, Vmp, Imp, Ns y coeficientes térmicos) antes de confiar en los resultados aguas abajo.

────────────────────────────────────────────────────────────

## 6. Página 4 — Dimensionamiento  ACTUALIZADO

Propósito: Calcular cuántos paneles caben en la fachada y seleccionar el inversor óptimo.

### Pasos

- Revisar los datos de la fachada:
- Área disponible (viene de Página 2)

- Dimensiones del panel (0.98 m × 1.76 m para ASP-ST1-T40)

- Configurar el layout:
- Orientación de los módulos (portrait / landscape)

- Espaciado entre paneles (si aplica)

- Selección de inversor:
- La app propone el inversor más adecuado del catálogo Growatt

- Verifica que Vdc_máx del string ≤ Vdc_máx del inversor

- Verifica que P_pico_array ≤ 1.3 × P_nominal_inversor

Resultados:

- N° de paneles instalables
- Potencia instalada (kWp)
- Inversor recomendado con alertas de compatibilidad

### N_strings/tracker: autocálculo del catálogo + mecanismo total estilo PVsyst, y ⚠️ advertencia sobre inversores duplicados en el catálogo  NUEVO/ACTUALIZADO (29-ago-2026)

El usuario pidió validar el proyecto real Teusaquillo (128 módulos SOLTECH ASP-ST1-T40, Growatt MID15KTL3-X) contra PVsyst 8.1.5. Al reproducirlo en la app, el campo **"N_strings por tracker (vía combinadoras)"** (arriba, junto a las temperaturas de diseño) quedaba fijo en su default duro (**1**) sin importar el inversor elegido — el Growatt MID15KTL3-X real soporta **8** strings/tracker. Con el default en 1, la app calculaba "Paneles/inversor = 8×1×2 = 16" en vez de 128, y de ahí "necesitas 8 inversores" para cubrir el área, en vez de 1 — un error de dimensionamiento real, no cosmético.

**Primer fix**: autocalcular `N_str_tr` desde `inversor["n_strings_tracker"]` del catálogo (la capacidad MÁXIMA del inversor) cada vez que cambia el inversor seleccionado. Suficiente para destrabar Teusaquillo, pero el usuario preguntó, con honestidad, si esto ya operaba igual que PVsyst — la respuesta correcta fue **no**: PVsyst nunca pide este dato aparte porque parte de lo que el usuario **QUIERE instalar** (el total de cadenas del generador, campo "Núm. cadenas"), y reparte ese total entre los MPPT; el autocálculo del catálogo, en cambio, parte de lo que el **equipo soporta** como máximo — coinciden en Teusaquillo porque el diseño real usa la capacidad máxima del inversor, pero no coincidirían en un proyecto donde se use menos capacidad de la que el inversor permite.

**Corregido de raíz**: `calculos/dimensionamiento.py::resolver_n_strings_tracker()` (reemplaza a la función anterior, `resolver_n_strings_tracker_autocalculado`) ahora soporta DOS mecanismos, elegibles por el usuario: (1) **"total" — mecanismo real de PVsyst**: si se declara un `N_total_cadenas` > 0 en el nuevo campo *"N total de cadenas para el proyecto (opcional — estilo PVsyst)"*, se reparte `ceil(N_total_cadenas / n_trackers)` — igual que PVsyst; (2) **"catálogo"** (default, `N_total_cadenas=0`): el autocálculo original, apropiado para cuando el usuario todavía está explorando cuánto cabe, no verificando un diseño ya decidido. Ambos respetan un ajuste manual del usuario mientras la fuente activa no cambie (mismo inversor+total, o mismo inversor sin total); cambiar de mecanismo, de inversor, o de total declarado siempre resetea al valor recién calculado. 8 tests en `tests/test_compatibilidad_string.py` (incluye el reparto no exacto — `ceil(17/2)=9` — y que volver el total a 0 regresa al mecanismo de catálogo, no se queda pegado en el último total).

⚠️ **Advertencia real, no resuelta — verificar SIEMPRE qué inversor exacto quedó cargado**: el catálogo tiene una familia genérica **"MID 15KTL3-X" / "MID 17KTL3-X" / "MID 20KTL3-X" / "MID 22KTL3-X" / "MID 25KTL3-X"** (sin marca, specs redondeadas — `N_strings/tracker=1` fijo en las 5, `Vmppt_min=200V` en las 5) que es casi con certeza el MISMO producto físico que **"Growatt MID15KTL3-X"** (con datos reales verificados contra PVsyst: `N_strings/tracker=8`, `Vmppt_min=140V`). La herramienta de "🧭 Mapeo de inversores compatibles" de esta página **auto-sugiere la entrada genérica primero** (aparece antes alfabéticamente / en el orden del Excel) — seguirla sin revisar llevó exactamente al error descrito arriba (16 paneles/inversor, 8 inversores, ratio DC/AC 0,42 en vez de 0,538) hasta notar y corregir la selección manualmente. **Antes de confiar en un match de "compatible" del mapeo, confirma el nombre EXACTO del inversor cargado** (mostrado en "✅ *nombre* cargado desde el mapeo") contra la ficha real del fabricante — no asumas que dos nombres parecidos son el mismo dato. Esta familia genérica NO se corrigió esta sesión (fuera de alcance); queda pendiente para una limpieza de catálogo futura.

**Otros 2 bugs de catálogo encontrados y corregidos en la misma auditoría**: (1) faltaba la columna **"Potencia AC nominal (kW)"** en TODO `datos/inversores_catalogo.xlsx` — sin ella, los ~106 inversores del catálogo calculaban su potencia CA nominal vía un respaldo `P_dc_max_W × 0,96` en vez del dato real del fabricante (para el Growatt MID15KTL3-X eso daba 21.600W en vez de 15.000W reales); columna agregada (retrocompatible, al final de la hoja) y valor real cargado para este inversor — los otros 105 siguen con el respaldo hasta que se cargue su dato real. (2) La corriente máxima por tracker del Growatt MID15KTL3-X se había derivado mal en un primer intento (de lo que produce el arreglo — 8 strings × 0,80A del módulo — no de lo que soporta el inversor), lo que marcaba el inversor como "no compatible" pese a que PVsyst no reporta ningún problema eléctrico con ese mismo diseño; corregido a 27,5A/33,5A tomando el dato real de la entrada genérica hermana.

### `alerta_margen`: el "Mapeo de inversores" y "▶️ Optimizar N paneles/string" podían recomendar N distintos para el MISMO inversor  NUEVO (29-ago-2026)

Probando otro inversor real (TriP 6K-HV, 2 strings/tracker) con el mismo panel, el usuario notó que **"Por inversor (1 unidad)"** (resultado del botón "▶️ Optimizar N paneles/string") mostraba 28 paneles/inversor, mientras que **"Prorrateo preliminar del inversor cargado"** (resultado del "🧭 Mapeo de inversores compatibles") mostraba 32 — para el mismo inversor, mismo panel, mismo `N_strings/tracker`. Investigado y confirmado con datos reales: **no era un problema del autocálculo de N_strings/tracker** (ambos paneles usaban correctamente 2, el valor real del catálogo) — era una inconsistencia de fondo, pre-existente, entre dos funciones de evaluación eléctrica:

- `optimizar_n_serie()` (usa `semaforo()`, que aplica un **margen de seguridad del 7,5%** — `UMBRAL_ALERTA_PCT`, heredado literalmente de la hoja Excel original `Optimizacion_String` celda L14) — descartaba N=8 como "🟡 ALERTA" porque su Voc en frío (987,6V) queda a solo 1,24% del Vdc_max del inversor (1000V), y elegía N=7 como el óptimo seguro.
- `evaluar_compatibilidad_string()` (usada por `mapear_inversores_catalogo()`/"🧭 Mapeo de inversores" y por el banner "🟢 Compatibilidad eléctrica preliminar" de 📊 Producción) **no aplicaba ningún margen** — solo miraba si el límite se excedía o no, así que N=8 salía "✅ Compatible" sin más, y el mapeo lo recomendaba en vez de N=7.

**Corregido, con cuidado de no romper proyectos ya validados**: se agregó un campo nuevo, puramente informativo, `alerta_margen` al resultado de `evaluar_compatibilidad_string()` — usa exactamente el mismo `semaforo()` con el mismo 7,5% de margen, pero **NO cambia el significado de `compatible`** (sigue siendo el mismo booleano de siempre, sin margen) para no alterar en silencio el estado de compatibilidad de proyectos reales ya entregados (ej. Urabá). `mapear_inversores_catalogo()` ahora prioriza, al elegir el "N recomendado", primero los N sin `alerta_margen` antes que la máxima utilización MPPT — con eso el mapeo recomienda N=7 para el TriP 6K-HV, coincidiendo con `optimizar_n_serie()`. N=8 sigue apareciendo como "viable" en la columna `N_viables` (no desaparece), solo deja de ser el recomendado.

**Visible en la UI**: nueva columna "⚠️ Margen ajustado" en la tabla del mapeo, marca "⚠️ margen ajustado" en el desplegable "Inversor compatible", y una advertencia nueva bajo "⚡ Prorrateo preliminar del inversor cargado" cuando el N cargado tiene el margen justo. 3 tests nuevos en `tests/test_compatibilidad_string.py`, anclados al caso real TriP 6K-HV. Suite completa: **737/737**.

⚠️ **Segundo bug real, distinto, encontrado probando el fix de arriba**: repitiendo el mismo TriP 6K-HV pero además declarando `N_total_cadenas=16` (mecanismo estilo PVsyst), "Por inversor" e "⚡ Prorrateo preliminar" volvieron a discrepar (112 vs 128 paneles/inversor) — pero esta vez NO era la inconsistencia de arriba (ambas herramientas, verificado con los datos reales, ya coincidían en recomendar N=7). La causa: **"Prorrateo preliminar" guarda el N recomendado en `session_state` en el momento del clic del botón "⚡ Cargar y recalcular", y nunca se invalidaba si el usuario cambiaba después "N total de cadenas" o ajustaba `N_strings/tracker`** — solo se invalidaba al cambiar de inversor o panel. El resultado combinaba un N=8 viejo (recomendado ANTES de declarar el total) con el `N_str_tr=8` nuevo (derivado del total recién declarado), dando 128 paneles/inversor que no correspondía a ninguna recomendación real vigente. **Corregido**: nueva clave `prorrateo_preliminar_n_str_tr` (separada de `N_str_tr_usado`, que ya escribe también el botón "Optimizar N paneles/string" con otro propósito, para no cruzarse) que invalida el prorrateo preliminar cada vez que `N_strings/tracker` cambia desde el último cálculo, igual que ya invalidaba al cambiar de inversor/panel.

Ficha de auditoría completa, con capturas reales de PVsyst y la verificación paso a paso: `DIAGNOSTICO_VALIDACION_TEUSAQUILLO_PVSYST.md` (raíz del repo). Suite completa: **730/730 passed**.
────────────────────────────────────────────────────────────

## 6b. Página 4b — Comparador de Inversores ⚖️  NUEVO

Nueva página (agosto 2026) ubicada entre Dimensionamiento y Mismatch. Compara varias configuraciones de inversor (modelo × unidades) usando la simulación horaria REAL ya corrida en 📊 Producción, aplicando el recorte de potencia (clipping) que cada límite AC produciría, y entrega los indicadores financieros a 25 años de cada opción.

### Prerrequisitos

- Panel seleccionado en 📐 Dimensionamiento (con Voc, Vmp, Isc y coeficientes térmicos completos).
- Simulación horaria corrida en 📊 Producción EN LA MISMA SESIÓN (la serie horaria no se guarda en el proyecto).
- Si el proyecto usa multi-superficie, la página se bloquea: dimensiona los inversores por superficie desde la Página 9.
- Si hay corrección por diodos de bypass, la página la aplica automáticamente y lo avisa en pantalla.
### Las 3 secciones de la página

- 1️⃣ Compatibilidad: evalúa TODO el catálogo contra tu string (Voc en frío ≤ V máx., ventana MPPT, corriente Isc×1,25 por tracker). La columna "modo" indica cómo conectar: normal, o "1 string/tracker" cuando el panel tiene tanta corriente que solo cabe un string por entrada MPPT (típico con paneles de 700+ W). La columna "motivo" explica cada rechazo.
- 2️⃣ Comparativa: eliges 2–4 modelos; la app calcula sola las unidades necesarias según las entradas de cada equipo y muestra E_ac con clipping, CAPEX, TIR, VPN, Payback y LCOE. Exportable a CSV. Incluye el botón "✅ Adoptar esta configuración".
- 3️⃣ Barrido DC/AC: curva completa de ratio DC/AC (1,0 a 2,2) con el óptimo por LCOE marcado con ⭐. Te dice cuántos kW AC realmente necesita tu campo solar.
### Pautas para elegir bien antes de oprimir "Adoptar"

Aplícalas en este orden — primero descartar, luego comparar, luego desempatar:

- ① Descarta por clipping y ratio: solo considera configuraciones con clipping ≤ 2% (0,5–2% es la zona sana; 0% suele significar inversor sobredimensionado). El ratio DC/AC recomendable en Colombia es 1,2–1,4: debajo de 1,1 pagas capacidad AC de más; arriba de 1,5 regalas energía.
- ② Elige por LCOE, no por TIR: el LCOE (COP/kWh) es cuánto cuesta producir cada kWh en 25 años — la configuración de menor LCOE es casi siempre la mejor. TIR y VPN son desempates. Ojo: si un modelo no tiene costo en el catálogo, la app lo avisa y su LCOE NO es comparable (compáralo solo por E_ac y clipping).
- ③ Diferencias pequeñas son empates: menos de ~2% en E_ac o ~3% en LCOE es empate numérico. Desempata con criterios prácticos: redundancia (2 equipos medianos superan a 1 grande — si uno falla sigues produciendo), y disponibilidad real en Colombia (repuestos, garantía y soporte local de la marca).
- ④ Revisa el modo de conexión: si dice "1 str/MPPT", confirma que las unidades calculadas no te obliguen a comprar un equipo extra casi vacío solo por falta de entradas.
- ⑤ Corrige las advertencias ANTES de adoptar: si aparece el aviso de string parcial (módulos no múltiplo del N en serie), ajusta N o el número de módulos — un string incompleto es eléctricamente inválido.
- ⑥ Contrasta con el barrido: la potencia AC total de tu elección debería quedar cerca de los kW AC del punto ⭐ de la sección 3. Si queda lejos, revisa por qué.
### Qué pasa al oprimir "✅ Adoptar esta configuración"

- Se fija el inversor, el número de unidades y el N en serie como configuración oficial del proyecto.
- Se INVALIDAN automáticamente los resultados guardados de Producción, Bypass, Financiero y CO₂ (estaban calculados con el inversor anterior) — es la misma invalidación en cadena del resto de la app.
- Paso obligatorio después de adoptar: vuelve a correr 📊 Producción y 💰 Financiero. Sin eso el proyecto queda sin energía oficial.
- El CAPEX y el costo USD/kW del comparador son supuestos editables: cuando tengas cotizaciones reales de los finalistas, actualízalos y confirma que el ganador sigue ganando.

────────────────────────────────────────────────────────────

### 🔍 Comparar TODOS los inversores compatibles + Analista de Producción  NUEVO (21-ago-2026)

Además de comparar 2-4 modelos elegidos a mano (sección 2️⃣), la página tiene una sección adicional que evalúa TODO el catálogo de inversores compatibles de una sola vez, ordenados por LCOE (los incompatibles se listan al final, marcados ❌ con el motivo del rechazo). Si un inversor compatible no tiene costo cargado en el catálogo, la fila se marca con una advertencia y su LCOE no es comparable, en vez de romper el cálculo o mostrar un número falso.

- Botón "🤖 Analista de Producción": envía la tabla completa al agente de IA, que redacta una recomendación técnica en lenguaje natural (razona sobre E_ac con clipping, %clipping y compatibilidad eléctrica — NO usa Performance Ratio para inversores, esa métrica es de paneles/orientación).
- El agente conoce el tipo de instalación REAL del proyecto (Fachada BIPV, Techo, Pérgola, Granja FV, etc. — el que elegiste en 🏠 Proyecto), no un perfil de costos genérico, así que sus razones citan correctamente el contexto BIPV/fachada/pérgola o campo abierto según corresponda.
⚠️ Para no cometer errores: la comparación de TODOS los inversores usa la simulación horaria ya corrida en 📊 Producción, igual que la comparación manual de 2-4 — si cambiaste el panel o el string después de correr Producción, vuelve a correrla antes de comparar.

────────────────────────────────────────────────────────────

## 6c. Página 4c — Comparador de Paneles 🧩  NUEVO

Propósito: Comparar varios modelos de panel del catálogo (o combinaciones panel×orientación) usando la misma simulación horaria del proyecto, con E_ac, Performance Ratio (PR) y compatibilidad eléctrica de cada opción, más un botón de Analista de Producción que redacta la recomendación técnica.

- Compatibilidad eléctrica: ✅/❌ (dos estados, igual que Inversores) — evalúa la ventana de voltaje/corriente del panel contra el string y el inversor ya configurados.
- E_ac y PR: para paneles se calculan ambos (a diferencia de Inversores, donde el PR no aplica).
- Botón "🤖 Analista de Producción": redacta la recomendación citando E_ac, PR y compatibilidad eléctrica de cada panel comparado.

### Perfil de costos CAPEX (referencia) — no confundir con el tipo de instalación real  ACTUALIZADO (21-ago-2026)

La página tiene un selector "Perfil de costos CAPEX (referencia)" que solo sirve para mostrar un benchmark de costo por m² (Granja FV campo / Techo industrial / BIPV fachada-pérgola) — es una referencia de comparación de costos, NO el tipo de instalación del proyecto. Este selector ahora se preselecciona automáticamente según el tipo de instalación real que elegiste en 🏠 Proyecto (Fachada BIPV, Techo, Pérgola, Marquesina y Granja FV se agrupan al perfil CAPEX correspondiente), pero puedes cambiarlo manualmente si solo quieres comparar costos contra otro perfil.

⚠️ Para no cometer errores: el texto que redacta el Analista de Producción SIEMPRE describe el tipo de instalación REAL del proyecto (el de 🏠 Proyecto), nunca el perfil de costos CAPEX que hayas elegido para comparar — así que si cambias el perfil CAPEX para ver otro benchmark de costos, la recomendación del agente no cambia de tipo de proyecto por eso. (Antes del 21 de agosto de 2026 esto no era así: la recomendación citaba el perfil CAPEX en vez del tipo real, por ejemplo diciendo "esta granja FV en campo" en una simulación de fachada — ya está corregido.)

────────────────────────────────────────────────────────────

## 6d. Página 4d — Comparador de Orientación 🧭  NUEVO

Propósito: Comparar varias orientaciones/tilts candidatos (por ejemplo distintas fachadas o distintos ángulos de una misma fachada) usando la misma simulación horaria del proyecto, con E_ac y PR de cada orientación, más el botón de Analista de Producción.

- Solo evalúa E_ac y PR (no aplica compatibilidad eléctrica — la orientación no cambia el string ni el inversor).
- Botón "🤖 Analista de Producción": redacta la recomendación técnica citando E_ac y PR de cada orientación comparada, y cuál conviene según el objetivo del proyecto (más energía total vs. mejor aprovechamiento del área disponible).
- Útil para decidir ENTRE fachadas candidatas de un mismo edificio, o para justificar ante el cliente por qué se eligió una orientación sobre otra.

────────────────────────────────────────────────────────────

## 6e. Página 18 — 🤖 Análisis IA: los 4 Analistas de Producción  NUEVO (ACTUALIZADO 21-ago-2026)

Página central que reúne los accesos directos a los 4 Analistas de Producción de la app: 🧩 Comparador de Paneles, 🧭 Comparador de Orientación, 🔋 Baterías y Balance, y ⚖️ Comparador de Inversores. Desde aquí puedes leer qué evalúa cada uno y saltar directamente a la página correspondiente con un clic.

- Los 4 accesos están organizados en una cuadrícula 2×2 con etiquetas cortas ("Comparador de Paneles →", "Comparador de Orientación →", "Baterías y Balance →", "Comparador de Inversores →") para que no se encimen visualmente.
- Cada uno de los 4 agentes tiene un alcance distinto y no debe confundirse con los otros: paneles y orientación evalúan E_ac/PR/compatibilidad eléctrica (orientación sin compatibilidad); baterías evalúa autonomía, profundidad de descarga (DoD), vida útil y compatibilidad de voltaje; inversores evalúa E_ac con clipping/%clipping y compatibilidad eléctrica, explícitamente SIN Performance Ratio.
- Todos son llamadas de IA bajo demanda (requieren clave configurada en el servidor y se activan solo al oprimir su botón) — no corren automáticamente ni tienen costo si no los usas.
⚠️ Para no cometer errores: cada Analista de Producción solo conoce los resultados de SU propia página de comparación (la tabla que ves en pantalla en ese momento) — no tiene memoria de comparaciones anteriores ni de otras páginas. Si cambias algo (panel, string, inversor), vuelve a generar la comparación antes de volver a pedirle la recomendación.

## 7. Página 5b — Motor Óptico

Propósito: Aplicar las correcciones ópticas específicas de BIPV sobre la POA bruta.

Cascada de correcciones:

POA bruta
  × IAM (Incidence Angle Modifier)    → pérdida por reflexión a ángulos oblicuos
  × Soiling                           → pérdida por suciedad acumulada en vidrio
  × Factor térmico BIPV (k_BIPV)      → penalización por cámara trasera confinada
  = POA efectiva

¿Cuándo usar?

- Siempre en proyectos BIPV de fachada para un cálculo más preciso
- El k_BIPV para fachada ventilada es ~0.93–0.97; para fachada sellada es ~0.88–0.92
¿Cuándo omitir?

- En estudios de prefactibilidad donde una estimación ±10% es suficiente
Resultado: POA efectiva (kWh/m²/año) que la Página 6 usa en lugar de la POA bruta.

────────────────────────────────────────────────────────────

### Transparencia τ — solo informativa (sin doble conteo)  ACTUALIZADO

Desde agosto de 2026 el slider de transparencia τ del Motor Óptico es solo informativo. La reducción real de energía por la transparencia del vidrio NO se resta de la POA: entra al cálculo a través del Isc_stc del catálogo, porque el fabricante mide la corriente del panel ya con el vidrio semitransparente instalado.

¿Por qué este cambio? En versiones anteriores existía el riesgo de contar la pérdida por τ dos veces (una en la óptica y otra en los parámetros eléctricos), subestimando la producción. Ahora τ se aplica exactamente una vez, y una guardia de regresión automática verifica en cada versión que la POA efectiva sea idéntica con τ = 0% y τ = 40%.

En pantalla: la 'pérdida por transparencia' aparece como dato informativo (POA que llega a la celda), pero no forma parte de la pérdida total de la cascada óptica.

### Verificación automática: ¿el Isc/Pmax del panel realmente incluye τ?  NUEVO

Al detectar el panel del proyecto, el Motor Óptico verifica ahora que la ficha del panel sea físicamente coherente con su transparencia declarada. El chequeo calcula la eficiencia implícita del área activa: η módulo = Pmax ÷ (área × 1000 W/m²), y η activa = η módulo ÷ (1 − τ). Ese valor se compara contra el máximo plausible de cada tecnología (CdTe ≈ 19%, CIGS ≈ 20%, Mono-Si ≈ 24,5%, Poli-Si ≈ 21%).

🚨 Alerta roja: si la eficiencia implícita supera el techo de la tecnología, el Pmax/Isc de la ficha parecen ser 'de celda pura' (sin descontar τ). De usarse así, la producción quedaría sobreestimada en silencio. Corrige la ficha antes de confiar en la energía calculada.

⚠️ Alerta amarilla: si la eficiencia implícita es anormalmente baja, es posible que τ se haya descontado dos veces en los datos (producción subestimada) o que el Pmax/área sean incorrectos.

✅ Nota verde: la ficha es coherente. Ejemplo: ASP-ST1-T40 (63 W, 0,72 m², τ = 40%) → η módulo 8,75% → η activa 14,6%, dentro del rango CdTe.

Si la ficha no trae Pmax o área, la app lo indica en lugar de emitir un veredicto. El chequeo reconoce variantes de nombre de tecnología ('MonoSi', 'N-Type', 'TOPCon', etc.) y no bloquea ningún cálculo: es una alerta de calidad de datos.

────────────────────────────────────────────────────────────

## 8. Página 5 — Mismatch y Bypass Diodes

Esta página es nueva y clave para proyectos BIPV en entornos urbanos con obstáculos.

Propósito: Calcular las pérdidas eléctricas reales por sombra parcial en strings,

modelando la activación de los bypass diodes integrados en cada panel.

### ¿Por qué importa?

Cuando un obstáculo (edificio vecino, voladizo, antena) sombrea parte de un string,

los módulos sombreados reducen su Isc. Los bypass diodes se activan para proteger el

circuito, pero al hacerlo eliminan toda la tensión de esos módulos. La pérdida real

es mucho mayor que la reducción proporcional de irradiancia.

Ejemplo: sombra en 2 de 8 módulos en serie → pérdida NO es 25%, sino puede ser 40-60%

de la producción de ese string en esas horas.

────────────────────────────────────────────────────────────

### Sección 1 — Cargar el CSV de Factor de Sombreado

El CSV debe provenir de la Calculadora de Sombreado 3D (bipv.innovacionquimica.com.co).

Formato del CSV esperado:

Hora,Mes,Dia,FS_geometrico,FS_climatico,FS_combinado,Fachada,...
8,3,21,0.00,0.05,0.04,Fachada_Sur,...
9,3,21,0.12,0.15,0.24,Fachada_Sur,...

- FS_geometrico: factor de sombreado solo por obstáculos físicos (recomendado)
- FS_climatico: incluye nubes → sobreestima el bypass
- FS_combinado: combinación de ambos
- Convención: 0 = sin sombra, 1 = sombra total (p_shade directo)
- Fachada: nombre de la fachada del análisis
Pasos:

- Arrastra el CSV al uploader
- La app detecta automáticamente qué columna de FS usar (prioridad: FS_geometrico)
- Revisa el banner de color:
- 🟩 Verde: FS_geometrico detectado — resultados más precisos

- 🟨 Amarillo: solo FS combinado disponible — puede sobreestimar bypass

────────────────────────────────────────────────────────────

### Detección automática de CSV con FS invertido

Importante para CSVs generados por herramientas externas

Algunas herramientas exportan el Factor de Sombreado con la convención invertida:

- Convención estándar (calculadora BIPV): 0 = sin sombra, 1 = sombra total
- Convención invertida (puntos manuales): 1 = sin sombra, 0 = sombra total (transmitancia)
La app detecta automáticamente si el CSV parece estar invertido (>55% de valores > 0.90

y sin columna FS_geometrico explícita) y muestra:

🔴 POSIBLE CSV INVERTIDO: el 87% de los valores FS están entre 0.90 y 1.00,
lo que sugiere transmitancia (1=sin sombra), no Factor de Sombreado (1=sombra total).

Acción: Abre "Opciones avanzadas" y activa "Invertir FS (1 − FS)".

────────────────────────────────────────────────────────────

### Selector de Fachada

Si el CSV contiene datos de múltiples fachadas o fachadas con múltiples orientaciones,

aparece un selector " Seleccionar fachada del array" con las fachadas detectadas.

Selecciona solo la fachada donde está instalado el array antes de simular.

Esto evita que obstáculos de otras fachadas contaminen el cálculo de bypass.

────────────────────────────────────────────────────────────

### Sección 5 — Configuración de strings y cobertura temporal

Configuración de strings

Parámetro  │  Descripción  │  Ejemplo Ruta N

Panel fotovoltaico  │  Debe coincidir con el de Producción  │  ASP-ST1-T40

Módulos en serie (N_series)  │  Módulos en un string  │  8

Strings en paralelo (N_parallel)  │  Número de strings  │  55

La app infiere N_series automáticamente buscando que Voc_array ≈ 400 V DC.

Cobertura temporal del CSV

El CSV de días críticos típicamente cubre solo 4–6 días del año (~60 horas).

La app muestra:

Métrica  │  Descripción

Días críticos  │  Cuántos días con datos hay en el CSV

Cobertura modo exacto  │  Horas TMY con coincidencia exacta (mes/día/hora)

Cobertura modo mensual  │  Horas cubiertas al replicar el patrón a todo el mes

Modos de cobertura:

- 📅 Modo mensual (recomendado): El patrón horario de cada día crítico
(ej. 21 de marzo) se replica a todos los días de ese mes. La geometría solar

varía <3° dentro de un mes, así que el día crítico es representativo del mes.

Cobertura típica: 25–40% del año.

- 📌 Modo exacto: Solo usa los días del CSV. El 98%+ del año tiene FS=0.
Útil para verificación pero subestima enormemente las pérdidas anuales.

Recomendación: Usa el modo mensual siempre para el diseño. Usa el modo exacto

para comparar con mediciones puntuales o para auditorías.

────────────────────────────────────────────────────────────

### Sección 5 — Ejecutar la simulación

Clic en " Calcular pérdida real por bypass diodes".

La simulación:

- Alinea el CSV con el TMY según el modo seleccionado
- Para cada hora del año (8 760 iteraciones): si FS > 5%, resuelve el circuito IV
con los módulos sombreados activos y calcula la potencia real del array

- Compara con la producción sin sombra (baseline) → calcula pérdida horaria
Resultados mostrados:

- Pérdida bypass (kWh DC/año): energía DC perdida por la activación de bypass
- % sobre E_dc: fracción de la producción DC base
- Horas con bypass activo / año: magnitud del problema
- E_dc_base vs E_dc_bypass: curva mensual comparativa
- Tabla mensual: desglose de pérdidas mes a mes
Interpretación del % de pérdida bypass:

- < 2%: Bajo — sombras leves, bypass no es un problema crítico
- 2–5%: Moderado — considerar redibujo de layout o modificar strings
- 5–10%: Alto — evaluar cambio de orientación o supresores de sombra
- > 10%: Muy alto — el sistema BIPV tiene un problema de sombreado serio
────────────────────────────────────────────────────────────

### Alarma de validación SDM (Motor IV)  NUEVO (21-ago-2026)

El modelo de bypass diodes de esta página resuelve el circuito IV panel por panel usando el mismo SDM (De Soto) que 🔬 Motor IV. Si ese panel no validó contra su ficha técnica (error > 5% en Voc/Isc/Vmp/Imp/Pmax), verás la misma alarma 🔴 con el texto técnico de causa probable apenas abras esta página — porque la pérdida por bypass que calculas aquí depende directamente de esos mismos parámetros del modelo. Ver la sección "Validación automática SDM vs ficha técnica" en Página 3 — Motor IV para el detalle completo.

────────────────────────────────────────────────────────────

## 8a. Página 5a — Sombras desde SketchUp 🌳  NUEVO

Nueva página (agosto 2026) que calcula el Factor de Sombreado horario automáticamente a partir de un modelo 3D del sitio hecho en SketchUp. Es la segunda puerta de entrada al modelo de bypass diodes: la Calculadora de Sombreado web (sección 14) sigue funcionando igual — las dos rutas conviven y producen el mismo CSV. Esta funcionalidad cierra la brecha frente a PVsyst en escenas 3D de sombras cercanas, con un modelador mejor.

### Cómo preparar el modelo en SketchUp

- Modela en METROS y con el norte real en el eje verde (Y). Si el modelo quedó girado, la página tiene un campo de corrección de norte (° horario).
- Incluye SOLO los obstáculos que producen sombra: edificios vecinos, árboles, tanques, la propia edificación si sombrea la fachada. NO incluyas los paneles (se sombrearían a sí mismos).
- Árboles: modélalos como volúmenes simples (cilindro + esfera). En la página hay un deslizador de transparencia (0,3–0,6 típico de follaje). Si mezclas edificios y árboles, calcula en dos pasadas.
- Exporta con Archivo → Exportar → Modelo 3D en formato OBJ o STL (también acepta DAE, PLY, GLB).
- Modelos muy pesados: la página rechaza mallas de más de 300.000 triángulos — borra mobiliario y detalle, deja solo los volúmenes que dan sombra.
### Flujo en la página (3 pasos)

- 1️⃣ Modelo 3D: sube el archivo, elige las unidades y la corrección de norte. La página muestra triángulos y dimensiones — si mide más de 2 km, las unidades no son metros.
- 2️⃣ Puntos de análisis: una fila de módulos = un punto, con coordenadas (x=Este, y=Norte, z=altura) tomadas del propio SketchUp con la herramienta de medición. La columna Fachada permite filtrar después en la Página 5.
- 3️⃣ Calcular: la app lanza un rayo hacia el sol por cada punto y cada hora del año usando el MISMO TMY del proyecto. Muestra % de horas con sombra, FS medio y una gráfica de verificación (FS a mediodía por mes).
### Requisito obligatorio: el TMY del proyecto

La página se bloquea si no has corrido antes ☀️ Recurso Solar. No es un capricho: el TMY de PVGIS viene en hora UTC y el CSV se alinea con Producción por (mes, día, hora) — sin el mismo TMY, la sombra quedaría corrida unas 5 horas. Con el TMY cargado, la coincidencia con 📊 Producción es hora a hora, 1:1.

### Conexión con el resto de la calculadora

- Botón «📤 Enviar a la Página 5»: deja el CSV listo en la sesión. Al abrir 🔀 Mismatch aparece el botón «🌳 Usar el CSV generado en Sombras SketchUp» — de ahí en adelante la cadena es la de siempre: bypass → E_ac corregida → Producción → Financiero → Reporte.
- También puedes descargar el CSV y guardarlo: tiene el mismo formato de la Calculadora web (Mes, Dia, Hora, FS_geometrico, FS, Fachada), con FS_geometrico = sombra física pura (convención 0 = sin sombra, 1 = sombra total — sin riesgo de FS invertido).
- Si cambias el modelo, las unidades, el norte, los puntos o la transparencia, el resultado anterior se invalida automáticamente — no puedes enviar por error un cálculo viejo.
### Avisos y validaciones automáticas

- Punto DENTRO de un edificio: la página lo detecta y avisa (daría sombra total falsa).
- Punto pegado al obstáculo (menos de ~10 cm): aviso de resultado ambiguo.
- Modelo sin ninguna sombra sobre los puntos: aviso para revisar unidades, norte y coordenadas.
- La Página 5 promedia los puntos de cada hora con IGUAL peso: usa un punto por fila de módulos y procura que las filas tengan un número similar de módulos.
### Requisito de instalación (una sola vez en el servidor)

La página usa la librería trimesh (ya incluida en requirements.txt). Si el servidor no la tiene, la propia página muestra el comando: venv/bin/pip install trimesh.

## 8b. Página 9 — Vista 3D y Multi-Superficie  NUEVO

Propósito: Modelar proyectos BIPV con más de una superficie (fachada + techo + pérgola + marquesina), combinando sus POA y producciones en un único valor de E_ac total que alimenta Financiero, Baterías y CO₂.

### Alarma de validación SDM (Motor IV)  NUEVO (21-ago-2026)

El MPPT combinado multi-superficie (mezcla módulo → string → grupo) también resuelve el circuito IV con el mismo SDM (De Soto) de cada panel. Si el panel usado no validó contra su ficha técnica (error > 5% en Voc/Isc/Vmp/Imp/Pmax), esta página muestra la misma alarma 🔴 con el texto técnico de causa probable, porque el reparto de mismatch entre superficies depende de esos mismos parámetros. Ver la sección "Validación automática SDM vs ficha técnica" en Página 3 — Motor IV.

Cuándo usarla: Solo si el proyecto tiene múltiples superficies con distintas orientaciones. Para una sola superficie (techo plano, fachada única), Página 9 no es necesaria.

### Sub-tabs de la Página 9

Sub-tab  │  Función

⚙️ Superficies BIPV  │  Crear y configurar cada superficie (tilt, azimuth, área, tipo)

🗺️ Vista 3D  │  Visualización 3D del edificio con mapa de POA o FS por mes

Producción por Superficie  │  Barras apiladas, recurso solar, tabla resumen, bypass por superficie

Diagrama Solar  │  Trayectoria solar con perfil de obstáculos (sin cambios)

### ⚙️ Sub-tab 1 — Superficies BIPV

Tipos de superficie disponibles:

Tipo  │  Tilt por defecto  │  Azimuth sugerido  │  Corrección T°

Fachada BIPV  │  90°  │  0° / 90° / 180° / 270°  │  Confinada (k=1.3)

Techo plano  │  10°  │  0°  │  Ventilada (k=1.0)

Techo inclinado  │  30°  │  180° (sur)  │  Ventilada (k=1.0)

Pérgola BIPV  │  15°  │  180° (sur)  │  Semi-ventilada (k=1.1)

Marquesina  │  20°  │  180° (sur)  │  Semi-ventilada (k=1.1)

Pasos:

- Pulsar "➕ Agregar superficie" para cada plano activo del edificio
- Configurar nombre, tipo, área, tilt y azimuth para cada superficie
- Pulsar " Calcular POA para todas las superficies"
- La app calcula el perfil TMY para cada orientación
### Sub-tab 3 — Producción y Bypass Multi-Superficie

Secciones 1–4 (producción base)

- 1. Barras apiladas de E_ac mensual por superficie
- 2. POA anual por orientación (gráfica horizontal)
- 3. Tabla resumen con área, POA, E_ac y % del total
- 4. FS mensual por superficie desde el CSV (requiere columna Fachada)
Sección 5 — Bypass diodes por superficie (#46)

Ejecuta el modelo de bypass individualmente para cada superficie usando su propio perfil POA y su propio perfil FS del CSV:

- Seleccionar el panel fotovoltaico y N_series (compartido para todas las superficies)
- El N_parallel de cada superficie se calcula automáticamente: N_parallel = área_m² / área_panel / N_series
- Pulsar " Calcular bypass por superficie"
Resultado — tabla por superficie:

Columna  │  Significado

Fachada CSV  │  Qué filas del CSV se usaron para esta superficie

E_ac base (kWh/año)  │  E_ac sin corrección bypass

Pérdida bypass (%)  │  % de la E_ac perdida por activación de bypass diodes

Horas bypass/año  │  Horas al año con bypass activo en esa superficie

E_ac bypass (kWh/año)  │  E_ac real corregida por bypass

Clave: E_ac_anual_kWh_multisup se actualiza con la suma de E_ac_bypass de todas las superficies. Esta clave tiene prioridad máxima en Financiero, Baterías y CO₂.

Sección 6 — Strings de distinta orientación en un mismo MPPT  NUEVO

Cuando dos superficies con orientaciones distintas (p. ej. fachada Este y fachada Oeste) se conectan en paralelo a la MISMA entrada MPPT del inversor, éste impone un solo voltaje de operación para todas. La app resuelve hora a hora la curva IV combinada (suma de las corrientes de los strings) y la compara contra el caso ideal de un MPPT por orientación, para cuantificar cuánta energía se pierde por compartir el MPPT.

- Panel fotovoltaico: solo aparecen paneles con ficha SDM completa (Motor IV).
- Módulos en serie por string: igual para todas las superficies; los strings en paralelo se calculan por área.
- Nº de MPPTs del inversor: se toma automáticamente de la ficha del inversor del Dimensionamiento si existe.
- Asignación superficie → MPPT: dos o más superficies en el mismo MPPT = strings en paralelo compartiendo voltaje.
- Resultados: E_dc ideal vs E_dc con MPPT compartido, pérdida por mismatch total y por MPPT, y gráfica de la curva IV combinada de la peor hora del año.
Semáforo de decisión: 🟢 pérdida < 0.5% = compartir MPPT es aceptable · 🟠 0.5–2% = evaluar si el ahorro del inversor compensa · 🔴 > 2% = se recomienda un MPPT por orientación o un inversor con más MPPTs.

⚠️ IMPORTANTE: esta sección es INFORMATIVA — no modifica la E_ac oficial que usan Financiero, Baterías y CO₂. Úsala para decidir el diseño eléctrico antes de comprar el inversor.

✅ Regla: si cada superficie tiene su propio MPPT, la pérdida es 0 y no necesitas esta simulación; ejecútala solo cuando el inversor tiene menos MPPTs que orientaciones.

### Botón "Integrar al Financiero"

Después de calcular la POA (o el bypass), el botón " Integrar al Financiero" escribe las claves exclusivas del sistema multi-superficie en la sesión:

Clave  │  Contenido  │  Nunca sobreescribe

E_ac_anual_kWh_multisup  │  E_ac total del sistema  │  E_ac_anual_kWh (superficie única)

poa_df_multisup  │  POA combinada ponderada por área  │  poa_df (POA bruta original)

area_total_multisup  │  Suma de áreas activas  │  area_fachada_m2

multisup_desglose  │  Lista con detalle por superficie  │  —

multisup_activo  │  Flag booleano  │  —

### Prioridad en las páginas aguas abajo

Cuando multisup_activo = True, Financiero, Baterías y CO₂ usan la E_ac multi-superficie:

💰 Financiero / 🔋 Baterías / 🌿 CO₂ leen en este orden:
  1. E_ac_anual_kWh_multisup  ← si multi-superficie activo  ★ prioridad máxima
  2. E_ac_anual_kWh_bypass    ← si bypass (superficie única) ejecutado
  3. E_ac_anual_kWh           ← simulación estándar base

Un banner en cada página indica qué modo está activo.

────────────────────────────────────────────────────────────

### Bifacial en multi-superficie  NUEVO

Al calcular la POA de varias superficies, un checkbox permite heredar la configuración bifacial definida en Recurso Solar (bifacialidad, altura, albedo trasero, GCR) para todas las superficies.

✅ Regla automática: si en Recurso Solar elegiste «fachada adosada», ese bloqueo de la cara trasera aplica SOLO a las superficies verticales (tilt ≥ 80°). Los techos y pérgolas del mismo proyecto conservan su ganancia bifacial normal — no tienes que configurar nada extra.

Montaje adosado/ventilado por cada fachada  NUEVO

En el editor de superficies (⚙️ Superficies BIPV), cada superficie con inclinación ≥ 80° muestra ahora su propio selector «🔄 Montaje de la fachada (modelo bifacial)» con tres opciones:

- Heredar de ☀️ Recurso Solar — opción por defecto: usa el montaje (adosada o ventilada) que elegiste en la página 2. Si no necesitas diferenciar fachadas, no toques nada.
- Adosada al muro (sellada): la cara trasera de ESTA fachada no recibe luz — su ganancia bifacial se anula automáticamente, sin afectar a las demás superficies.
- Ventilada con superficie reflejante: ESTA fachada tiene cámara de aire con superficie clara detrás — su ganancia bifacial sí aplica.
Esto permite modelar proyectos reales mixtos: por ejemplo, una fachada sur adosada al muro (ganancia 0), una fachada oriente ventilada con muro blanco (ganancia normal) y un techo bifacial — cada una con su cálculo correcto en la misma corrida.

🚨 ALERTA PARA EVITAR ERRORES: marca «Ventilada» solo si la cámara de aire y la superficie reflejante existen físicamente en ESA fachada. Marcarla sin serlo infla la producción de esa superficie y contamina el total del proyecto que llega al Financiero.

⚠️ IMPORTANTE: los techos y pérgolas (inclinación < 80°) no muestran este selector y nunca se ven afectados por el montaje de las fachadas — conservan siempre su ganancia bifacial normal.

Nota: al eliminar una superficie de la lista, las demás conservan sus valores (nombre, montaje, tilt, área). Puedes agregar y quitar superficies con confianza.

────────────────────────────────────────────────────────────

Modo Granja agrivoltaica  NUEVO (5-ago-2026)

Cuando el tipo de instalación es "Granja fotovoltaica", la Vista 3D ya no dibuja un edificio: muestra el terreno completo en verde (el cultivo) con las filas de paneles inclinadas y elevadas a 3 m cuando el factor de ocupación es menor a 100%.

- La separación entre filas se calcula como ancho del colector ÷ GCR (con 30% de ocupación, ~3.7 m entre ejes de filas).
- Un resumen indica número de filas, separación, altura de montaje y porcentaje de suelo libre para el cultivo.
Nota: la vista muestra las filas como bandas continuas, no módulos individuales. El conteo oficial de paneles sigue siendo el de la Página 4 — Dimensionamiento.

## 9. Página 6 — Producción Anual  ACTUALIZADO

Propósito: Calcular la producción AC anual del sistema completo.

### Pasos

- Revisa los datos de entrada (tomados automáticamente de páginas anteriores)
- Verifica que el inversor esté correctamente seleccionado
- Si ejecutaste el Motor Óptico (5b), la POA efectiva se usa automáticamente
- Clic en "Calcular producción"
Balance energético mostrado:

POA bruta → Motor Óptico (IAM + Soiling + Térmico) → POA efectiva
  → Pérdida mismatch → E_dc → Pérdida bypass ← (si Página 5 fue ejecutada)
  → Pérdida inversor → E_ac anual

Si ejecutaste el modelo de bypass en Página 5, el balance incluye automáticamente

una barra "Bypass diodes" mostrando los kWh DC perdidos.

### Auditoría del pipeline de cálculo (27-ago-2026) — bug real en el gate de compatibilidad eléctrica

A pedido explícito del usuario ("audita cada sección de cálculo... basado en cálculos reales como el de Urabá"), se corrió el pipeline real de la app (no solo scripts sueltos) con los datos reales del proyecto Agrivoltaico Urabá (18 módulos JA Solar JAM66D46-720/LB en serie, Growatt MAX 100KTL3 LV — ficha oficial: Voc_stc=49,00 V, Vmp_stc=41,19 V, Isc_stc=18,59 A; inversor: Vdc_max=1500 V, Vmppt_min=200 V, **Vmppt_activo_min=850 V**, Vmppt_max=1300 V).

**Bug real encontrado**: `calculos/dimensionamiento.py::evaluar_compatibilidad_string()` — la función que produce el banner 🟢/🔴 de esta página (Producción) — usaba `Vmppt_min` (piso de arranque, 200 V) en vez de `Vmppt_activo_min` (piso MPPT recomendado, 850 V) como umbral, con la prioridad del `or` invertida respecto a las OTRAS 2 funciones de compatibilidad de la app (`optimizar_n_serie()`, validada contra el Excel VBA original, y `comparador_inversores.filtrar_inversores_compatibles()`), que sí usan `Vmppt_activo_min` primero. El propio docstring de `evaluar_compatibilidad_string()` afirmaba usar "exactamente los mismos límites" que el resto de la app — no era cierto.

**Impacto real, verificado ejecutando las 3 funciones con los datos de Urabá**: con 18 en serie, Vmp string = 720 V. `optimizar_n_serie()` y `comparador_inversores.py` ya lo marcaban como incompatible/FALLA; `evaluar_compatibilidad_string()` decía "compatible", así que Página 6 mostraba el banner 🟢 verde para una configuración que el resto de la app ya rechazaba. Además, en Página 4 — Dimensionamiento, el cálculo del "N mínimo eléctrico" para el barrido de `optimizar_n_serie()` usaba el mismo umbral equivocado: con Vmppt_min dio N≥5 (dejaba entrar 18 sin más), con el umbral correcto es **N≥21** (a temperatura real/extrema, el mínimo verdadero es N=22).

**Corregido**: las 3 apariciones del patrón invertido (`calculos/dimensionamiento.py` líneas ~124 y ~310, `pages/4_📐_Dimensionamiento.py` línea ~233) ahora priorizan `Vmppt_activo_min`. 4 tests de regresión nuevos en `tests/test_compatibilidad_string.py` con los datos reales de Urabá, incluyendo uno que verifica que `evaluar_compatibilidad_string()` y `filtrar_inversores_compatibles()` ya coinciden. 2 tests preexistentes de `tests/test_optimization_fase4.py` necesitaron subir su presupuesto de reintentos (`max_intentos_por_candidato`) porque el espacio eléctrico válido del catálogo real es más angosto con el umbral correcto — comportamiento esperado, no una regresión (el propio docstring de `generar_candidatos()` ya documentaba este trade-off). Suite completa: 701/701 passed.

⚠️ **Implicación real para el proyecto Urabá, no solo de código**: el diseño físico documentado en esta sesión (18 módulos JA Solar por string con el Growatt MAX 100KTL3 LV) opera con Vmp por debajo del piso MPPT recomendado del fabricante (720 V vs 850 V). Esto **NO afecta** los kWh/año ya validados contra PVsyst (esa simulación no pasa por este gate), pero sí es una alerta de diseño eléctrico real que vale la pena que el ingeniero responsable revise — posiblemente aumentando N en serie (≥22) o confirmando con Growatt si operar por debajo de Vmppt_activo_min es aceptable para este modelo específico.

**Hallazgo aparte, NO corregido** (riesgo, no confirmado como bug activo): si un usuario corre 🔀 Página 5 — Mismatch ADEMÁS de 🔆 Motor Óptico (el flujo agrivoltaico recomendado, sección 2, NO incluye Página 5 — así que esto no afecta la validación ya hecha de Urabá), el slider `pct_soiling` de Mismatch (default 2%) podría contar el soiling dos veces junto con el modelo de soiling propio de Motor Óptico, ya que no existe una advertencia explícita como la que sí existe para el confinamiento térmico ("k_bipv → única fuente de corrección térmica"). Pendiente de decidir si se agrega un guard similar.

La E_ac guardada en memoria:

- E_ac_anual_kWh — producción base (sin corrección bypass)
- E_ac_anual_kWh_bypass — producción real (con corrección bypass) ← usada por Páginas 7, 11
### Tasa de degradación anual desde historial PR (#28)

Al final de la Página 6 hay una nueva sección " Tasa de degradación anual del sistema". Permite calcular la degradación real de los módulos a partir del PR corregido por temperatura de varios años operativos.

Pasos:

- Ingresar el número de años con datos (mínimo 2)
- Para cada año: el año calendario y el PR_corr_T promedio anual (tomado de la tabla de diagnóstico)
- La app ajusta una regresión lineal sobre los puntos e informa:
Métrica  │  Descripción

Pendiente PR (pp/año)  │  Cambio absoluto en puntos porcentuales por año

Tasa de degradación  │  % de pérdida relativa al PR inicial por año

Vida útil (PR > 70%)  │  Años estimados hasta degradación severa

El resultado se guarda como tasa_degradacion_calculada y queda disponible en Página 7 como alternativa al slider paramétrico.

Ejemplo: Si PR_corr_T fue 82% en 2022, 81.3% en 2023 y 80.6% en 2024, la regresión da −0.7 pp/año → tasa = 0.70%/año (ligeramente superior al 0.5% de catálogo CdTe).

────────────────────────────────────────────────────────────

### Aporte de la cara trasera (bifacial)  NUEVO

Si la POA vino de una simulación bifacial, aparece la sección «🔆 Aporte de la cara trasera» con tres métricas:

- Cara frontal (POA): irradiación anual sobre la cara frontal, en kWh/m²·año.
- Aporte trasero efectivo: la energía que la cara trasera realmente suma a la simulación, ya ponderada por la bifacialidad del panel (y por el montaje de fachada, si aplica).
- Aporte trasero (%): qué fracción de la POA global proviene de la cara trasera.
⚠️ IMPORTANTE: la E_ac anual YA incluye la ganancia bifacial. No sumes el aporte trasero aparte — hacerlo duplicaría la energía y distorsionaría el análisis financiero.

### Modo curva IV real del panel (Motor IV)  NUEVO

Además del modelo hora a hora estándar, la página 6 puede calcular la producción usando la curva I-V real del panel (modelo de un diodo De Soto calibrado con la ficha técnica). El toggle «🔬 Usar curva IV real» aparece SOLO si el panel tiene ficha SDM completa (I_L_ref, I_o_ref, R_s, R_sh_ref, a_ref, coeficientes térmicos).

- Con el toggle apagado (por defecto) todo funciona exactamente igual que antes.
- Con el toggle encendido se corren AMBOS modelos y se muestra la comparación: E_ac de cada uno y % de diferencia.
- Si ambos coinciden dentro de ±10%, la E_ac oficial aguas abajo pasa a ser la del modelo de curva IV.
- El cálculo es vectorizado: las 8.760 horas del año se resuelven en menos de un segundo.
🚨 ALERTA PARA EVITAR ERRORES: si la diferencia entre los dos modelos supera ±10%, la app muestra alerta roja — es señal de datos de ficha inconsistentes (Voc/Isc/Vmp/Imp, N_s half-cut o parámetros SDM mal calibrados). Revisa la ficha en 🔬 Motor IV antes de usar ese resultado en el análisis financiero.

✅ Regla: usa el modo curva IV cuando el panel tenga ficha completa verificada — es más preciso en horas de baja irradiancia y en climas fríos, donde el modelo lineal subestima o sobreestima.

### Bug real corregido: la producción nunca se recortaba (clipping) al Pnom del inversor  NUEVO (29-ago-2026)

El usuario reportó un error de PVsyst ("inversor sobredimensionado") en el proyecto Teusaquillo y preguntó, honestamente, si esa misma restricción existía en la app. Se investigó y la respuesta fue: no existía ningún filtro — pero al preguntarse si eso era un riesgo real, se encontró algo más serio que una advertencia faltante.

**Root-caused verificando el código real**: `calculos/produccion.py` calculaba `P_ac_W = P_dc_W * eta_inversor` **sin ningún tope** — la función ni siquiera recibía la potencia AC nominal del inversor como parámetro. Cualquier proyecto con relación DC/AC > 1 (el diseño ESTÁNDAR de la industria, típicamente 1.1-1.3, no un caso raro) hacía que la app sobreestimara producción sin límite, exactamente lo que PVsyst SÍ modela con su recorte ("Pnom") siempre activo.

**Cuantificado con un caso real** (inversor 100 kW AC, array 130 kWp DC, ratio 1.3): un solo día despejado — la app reportaría 967,7 kWh cuando lo real con clipping sería 873,5 kWh, **10,8% de sobreestimación**, 5 de 24 horas realmente recortadas. Impacto en cascada: E_ac, PR, Y_f inflados → TIR/VPN/Payback optimistas en cualquier proyecto financiero con ese tipo de diseño.

**Por qué nunca apareció en las 2 validaciones contra PVsyst ya hechas esta sesión**: Urabá (220,32 kWp / 249,6 kW CA = ratio 0,88) y Teusaquillo (8,064 kWp / 15 kW CA = ratio 0,54) — **ambos por debajo de 1,0**, así que el DC nunca se acercó a superar al inversor. El hueco estuvo presente todo este tiempo sin que ninguna validación lo expusiera.

**Corregido, con el mismo rigor que PVsyst**: `calculos/produccion.py::simular_produccion_anual()` y `calculos/produccion_iv.py::simular_produccion_iv()` (ambos motores, modelo simplificado y curva IV real) reciben ahora `P_ac_nom_W` opcional y aplican `P_ac = min(P_dc × η, Pnom)` hora a hora. Nuevos campos en el resultado: `perdida_clipping_kWh`, `horas_con_clipping`, `E_ac_sin_recorte_kWh`. La cascada de pérdidas (`perdidas_desglosadas()`) ahora tiene una fila nueva "④b Recorte inversor (Pnom, clipping)" separada de "④ Pérdida inversor (eficiencia)" — igual que PVsyst separa ambas causas en su propio diagrama de pérdidas.

`simulation/bipv_simulator.py::run_bipv_simulation()` extrae `P_ac_nom_W` de `config.inversor` automáticamente (ya existía ese campo en el contrato, simplemente nunca se usaba para esto) y lo escala por `N_inversores` para proyectos multi-inversor — verificado matemáticamente y con ejecución real que el atajo de escalar N_paneles/P_dc_stc_kW por N_inversores **sigue siendo exacto** con recorte activo (PR y horas_con_clipping idénticos entre 1 y 7 inversores, porque `N×min(a,b) = min(N×a, N×b)`). `pages/6_📊_Producción.py` pasa el mismo dato desde el inversor seleccionado en pantalla. Retrocompatible: si no se pasa `P_ac_nom_W` (o el inversor no lo trae), el comportamiento es idéntico al de antes — ningún proyecto ya validado (Urabá, Teusaquillo) cambia de resultado.

⚠️ **Limitación real, declarada, NO resuelta**: en proyectos multi-superficie donde varias superficies comparten el MISMO inversor físico (bus horizontal común, Fase 3), el recorte se sigue aplicando por superficie — cada una "vería" la capacidad completa del Pnom compartido en vez del recorte agregado real del bus. Modelarlo bien requiere sumar la potencia pre-recorte de todas las superficies activas hora a hora y recortar una sola vez a nivel de sistema — un rediseño de `run_bipv_simulation_multisuperficie()` fuera de alcance de este fix puntual. Documentado en su docstring.

Regresión: 3 tests nuevos en `tests/test_simulation_pipeline.py` (recorte real con inversor pequeño, sin recorte cuando no se pasa `P_ac_nom_W` — verifica retrocompatibilidad total —, y exactitud matemática del atajo multi-inversor con recorte activo). Suite pytest completa: **721/721 passed**.

### Nueva alarma: relación DC/AC (Proporción Pnom, homóloga al aviso real de PVsyst)  NUEVO (29-ago-2026)

Verificando el proyecto real Teusaquillo contra PVsyst 8.1.5 se confirmó algo importante: con la config real (128 módulos, 8,064 kWp, Growatt MID15KTL3-X 15 kW CA), PVsyst muestra *"La potencia del inversor está muy sobredimensionada"* y el indicador **"Sistema"** queda en 🔴 — el botón **"Ejecutar simulación"** se deshabilita. **No es una advertencia cosmética: PVsyst bloquea la simulación por completo** hasta resolver el sobredimensionamiento. Proporción Pnom real de PVsyst para este caso: 8,064/15 = **0,538**.

**Nueva función** `calculos/dimensionamiento.py::evaluar_relacion_dc_ac(P_dc_stc_kW, P_ac_nom_W)`: clasifica la relación DC/AC en 5 niveles — 🔴 muy sobredimensionado (<0,75) · 🟠 sobredimensionado (<1,0) · 🟢 óptimo (0,95–1,35) · 🟠 alto (≤1,6) · 🔴 muy alto (>1,6), anclada al dato real de PVsyst (0,538 → mismo aviso "muy sobredimensionado", verificado idéntico). Se muestra en **📊 Producción** (antes de simular, junto a la compatibilidad eléctrica) y en **📐 Dimensionamiento** (tras presionar "▶️ Optimizar N paneles/string", a nivel de proyecto completo).

**Diferencia deliberada respecto a PVsyst**: la app **avisa pero NO bloquea** la simulación — permite evaluar diseños BIPV con relaciones DC/AC atípicas (habituales en fachadas de baja potencia con inversor reutilizado o sobredimensionado a propósito por el cliente) en vez de rechazarlos de plano como hace PVsyst.

5 tests nuevos en `tests/test_compatibilidad_string.py`, incluyendo uno anclado al pantallazo real de PVsyst (Teusaquillo, ratio 0,538 exacto) y otro con el proyecto Urabá ya validado (0,883). Ver también la subsección de "N_strings/tracker" en la sección 6 (Dimensionamiento) — **incluye una advertencia importante sobre inversores duplicados en el catálogo** encontrada al validar este mismo caso. Ficha de auditoría completa: `DIAGNOSTICO_VALIDACION_TEUSAQUILLO_PVSYST.md` (raíz del repo).

## 10. Página 7 — Análisis Financiero  ACTUALIZADO

Propósito: Calcular TIR, VPN, Payback y LCOE del proyecto bajo la Ley 1715/2014.

### Prioridad de E_ac: multi-superficie > bypass > base

La Página 7 selecciona automáticamente la estimación de producción más precisa disponible:

Prioridad alta    → E_ac_anual_kWh_multisup   (Página 9 integrada)
Prioridad media   → E_ac_anual_kWh_bypass     (Página 5 bypass ejecutado)
Prioridad baja    → E_ac_anual_kWh            (simulación estándar)

Un banner muestra qué fuente está activa y permite desactivar el modo multi-superficie con un botón "Desactivar".

### Toggle de degradación desde historial real (#28)

Si ejecutaste la sección " Degradación anual" de Página 6 con al menos 2 años de PR histórico, aparece un interruptor junto al slider de degradación:

🔘 Usar degradación del historial real — 0.62%/año
   (calculada en 📊 Producción › Degradación anual)

Al activarlo, el slider paramétrico se reemplaza por la tasa calculada por regresión lineal. La TIR y el VPN quedan calculados con la degradación real medida del sistema, no el valor genérico de catálogo.

### Pasos

- Sección 1 — CAPEX: Ingresa costos de módulos, inversor, estructura, instalación
- Sección 2 — Parámetros financieros:
- Tarifa energía (COP/kWh)

- TRM (COP/USD)

- Tasa de descuento (%)

- Horizonte de análisis (años)

- Degradación anual del sistema (% — o usar historial real con toggle)

- Sección 3 — Beneficios Ley 1715: Revisa los ahorros tributarios calculados
- Clic " Calcular TIR, VPN, Payback y LCOE"
### Beneficios Ley 1715/2014

Artículo  │  Beneficio  │  Cálculo

Art. 11  │  Deducción renta  │  50% × CAPEX × tasa_renta (35%)

Art. 12  │  Exclusión IVA equipos  │  19% × CAPEX_equipos

Art. 14  │  Depreciación acelerada  │  VPN del diferencial 5yr vs 10yr

Requiere certificación UPME previa al inicio del proyecto.

### Indicadores de viabilidad

Indicador  │  Proyecto viable  │  Proyecto marginal  │  Proyecto no viable

TIR  │  > 12%  │  8–12%  │  < 8%

VPN  │  > 0 USD  │  Cercano a 0  │  < 0 USD

Payback simple  │  < 10 años  │  10–15 años  │  > 15 años

LCOE  │  < tarifa red  │  ≈ tarifa red  │  > tarifa red

────────────────────────────────────────────────────────────

Precio real del inversor del catálogo  NUEVO (5-ago-2026)

El precio del inversor seleccionado en el catálogo fluye automáticamente al análisis financiero, en lugar de usar un estimado genérico por kW.

⚠️ Para no cometer errores: verifica que la ficha del inversor en el catálogo tenga precio cargado. Si el campo está vacío, revisa el valor que aparece en Financiero antes de generar el presupuesto.

────────────────────────────────────────────────────────────

### Autoconsumo vs. excedente exportado: tarifa diferenciada  NUEVO (21-ago-2026)

Cuando en 🔋 Baterías y Balance tienes un balance energético activo, el análisis financiero ahora separa la energía en dos partes con su propia tarifa:

- Energía autoconsumida: se valora a la tarifa de energía normal (COP/kWh) — es el ahorro por NO comprarle esa energía a la red.
- Energía exportada como excedente: se valora a una tarifa de excedentes propia, editable, que aparece como el campo "Tarifa de excedentes exportados (COP/kWh)" (referencia: Res. CREG 174 de 2021 — medición neta). Por defecto empieza igual a la tarifa de compra (sin descontar ningún porcentaje inventado) hasta que ajustes el valor real de tu contrato o comercializador.
Antes de este cambio, si había un balance de baterías activo, el excedente exportado NO generaba ningún ingreso en el modelo financiero — quedaba completamente excluido del cálculo. Ahora se incluye siempre, a la tarifa que definas.

⚠️ Para no cometer errores: si tu proyecto es 100% autoconsumo (sin excedente, o sin balance de baterías corrido), este widget ni siquiera aparece — toda la energía se sigue valorando a la tarifa normal, igual que antes. El widget solo aparece cuando 🔋 Baterías y Balance reporta una fracción de exportación real (E_exportacion_anual_kWh > 0).

────────────────────────────────────────────────────────────

### Auditoría del pipeline financiero/CO2/TRM (27-ago-2026) — módulo financiero validado, bug real de TRM corregido

Continuación de la auditoría del pipeline de cálculo con datos reales de Urabá (ver sección 9, Página 6 Producción, para el bug del gate de compatibilidad eléctrica encontrado antes).

**`calculos/financiero.py` — validado, sin bugs encontrados**: se reprodujeron INDEPENDIENTEMENTE, ejecutando el módulo real con los insumos declarados en `entregables/generar_informe_final_evaluador_uraba.py` (CAPEX≈USD 177.200, tarifa 950 COP/kWh EPM, TRM 3.118,24, degradación 0,4%/año, OPEX 10 USD/kWp/año, sin beneficios Ley 1715), las cifras oficiales YA entregadas a un evaluador externo — coinciden casi exactamente en ambos escenarios (caso base bifacial: TIR 55,91%≈55,9%, VPN USD 701.692≈701.820, LCOE 208,4≈208 COP/kWh; piso conservador monofacial: TIR 51,65%≈51,7%, VPN USD 635.184≈635.213, LCOE 225,1≈225 COP/kWh). El motor financiero es correcto y consistente con lo entregado. 3 tests de regresión nuevos (`tests/test_financiero_uraba.py`) anclados a estas cifras del informe real.

**Cabo suelto real, sin corregir (decisión pendiente del usuario, ya documentada desde el 26-ago)**: el informe entregado usa E_ac=334.805 kWh/año (supuesto "+8% bifacial fijo", sin el ajuste fino de Motor Óptico/IAM), no los 336.662 kWh/año ya validados como más precisos con el motor real de la app. Diferencia pequeña y no material (TIR 55,9%→56,2%, +0,32 pp; VPN +USD ~5.000) pero real — sigue sin decidirse si se regeneran los entregables oficiales con el número más preciso.

**`calculos/co2.py` — validado, sin bugs**: fórmulas de equivalencias (árboles, hogares, km, vuelos, barriles, cilindros GLP) verificadas contra las etiquetas de `pages/12_🌿_Impacto_CO2.py` — todas consistentes en unidades (ej. `km_vehiculo` está en MILES de km a propósito, coincide con el label "mil km"). El uso de `factor_activo` (metodología elegida por el usuario) vs `factor_marginal` (0,300 kg/kWh, CDM) para bonos de carbono es una elección de diseño transparente y bien etiquetada, no un bug — la página muestra explícitamente ambos y recomienda el marginal para bonos reales.

**Bug real encontrado y corregido, verificado en vivo**: `calculos/trm_utils.py` — el umbral `_ALERTA_BAJA` (3.800) y el mensaje de referencia ("ref. 2025-2026: ~4.000–4.500") estaban desactualizados frente al mercado real: la TRM oficial del 27-ago-2026, **verificada en vivo contra la API real de datos.gov.co durante esta auditoría** (no un supuesto), es 3.118,24 — por debajo del umbral, así que el widget de TRM en 💰 Financiero / 💼 Presupuesto mostraba una advertencia FALSA de "TRM parece baja" para la tasa oficial correcta. `TRM_DEFAULT` (respaldo si ambas APIs fallan) también bajó de 4.200 a 3.900 por la misma razón. Nuevos valores: `TRM_DEFAULT=3.900`, `_ALERTA_BAJA=2.600` (con margen para no quedar obsoleto de nuevo con una fluctuación normal del peso). 4 tests de regresión nuevos (`tests/test_trm_utils.py`), anclados al valor real verificado en vivo ese día. **Nota explícita**: a diferencia de los demás bugs de esta auditoría (lógica invertida, redondeo doble), este es un valor de referencia de mercado que se desactualiza con el tiempo por diseño — si vuelve a quedar desalineado en el futuro, es una fluctuación normal del peso que hay que resubir, no un error de lógica.

Suite completa tras estos cambios: **708/708 passed**.

────────────────────────────────────────────────────────────

### Advertencia nueva: umbral de 1 MW para Ley 1715 "autoconsumo a pequeña escala"  NUEVO (28-ago-2026)

Verificando si la calculadora está lista para mega-proyectos (varios MW, zona desértica tipo La Guajira, inversor central como el Woodward IDS SOLO 500), se encontró un hallazgo real: `datos/ciudades_colombia.py::LEY_1715["potencia_maxima_autoconsumo_kW"]` (1.000 kW) ya existía en el repo, pero **ningún cálculo lo usaba** — un proyecto de varios MW podía mostrar los beneficios fiscales de Ley 1715 calculados con el mismo modelo de "autoconsumo a pequeña escala" sin ninguna advertencia de que el régimen real para generación a gran escala puede ser distinto.

**Corregido**: `run_financial_simulation()` (`simulation/financial_simulator.py`) ahora compara `P_dc_stc_kW` contra ese umbral cuando `aplicar_ley_1715=True`, y si lo supera, deja el mensaje en el nuevo campo `FinancialResult.advertencia_ley_1715` (`None` si no aplica). **No bloquea ni recalcula** los beneficios con otro régimen — esta app no lo modela — solo advierte, para que el proyecto se revise con un asesor tributario/regulatorio antes de presentar esas cifras como definitivas. La misma advertencia se agregó directamente en 💰 Página 7 — Financiero (que calcula los beneficios con su propio llamado directo a `calcular_beneficios_ley_1715()`, no a través de `run_financial_simulation()`) usando la potencia ya disponible en sesión (`p_stc`).

Verificado con 4 casos reales: Urabá (220 kWp) → sin advertencia; exactamente 1.000 kW → sin advertencia (el umbral es estrictamente "supera", no "alcanza"); un mega-proyecto sintético de ~1,2 MWp (mismo patrón de `N_inversores` ya validado) → advertencia con la cifra exacta del proyecto; `aplicar_ley_1715=False` → ni beneficios ni advertencia. Test de regresión nuevo en `tests/test_simulation_pipeline.py`. Suite completa: **718/718 passed**.

────────────────────────────────────────────────────────────

## 11. Página 8 — Presupuesto Bancable

Propósito: Construir el presupuesto completo del proyecto con estructura

financiera exigida para bancabilidad: CAPEX directo, costos blandos, contingencias

diferenciadas y OPEX anual proyectado a 25 años.

¿Por qué "bancable"? Un banco o fondo de inversión no financia proyectos

con un estimado de obra simple. Exige un presupuesto que demuestre que todos

los costos están identificados, cuantificados y respaldados por fuentes.

Esta estructura cumple ese estándar.

────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────

🧮 Estimación Rápida — Escalamiento Paramétrico de Rentabilidad  NUEVO

Propósito: Obtener un CAPEX y OPEX de referencia en menos de dos minutos, con benchmarks del mercado colombiano calibrados por tipo de instalación, escenario económico y zona geográfica. El resultado alimenta directamente el Análisis Financiero (Página 7) para calcular TIR, VPN y Payback sin necesidad de ingresar cotizaciones reales.

¿Cuándo usar la Estimación Rápida?

Usa esta pestaña en las etapas tempranas del proyecto, antes de disponer de cotizaciones formales de equipos y mano de obra:

Etapa de prefactibilidad (Día 1–7): el promotor necesita responder ¿vale la pena desarrollar este proyecto? antes de invertir en estudios formales.

Tamizaje de oportunidades: cuando tienes 5–10 oportunidades simultáneas y necesitas identificar cuáles 2–3 ameritan un estudio completo.

Reunión inicial con el cliente: para presentar un rango de inversión orientativo con Ley 1715 ya aplicada, sin esperar 2–4 semanas de cotizaciones EPC.

Sensibilidad por escenario: para comparar optimista vs. conservador antes de comprometer recursos en ingeniería de detalle.

¿Cuándo NO usar la Estimación Rápida?

Para estructurar un crédito bancario o presentar ante inversionistas formales. En esos casos, completa las pestañas de cotización real (Perfilería, Mano de Obra, Sistema FV, etc.) con precios respaldados por fuente. Al hacerlo, la app desactiva automáticamente la Estimación Rápida y usa los costos reales.

────────────────────────────────────────────────────────────

Paso a paso — Cómo usar la Estimación Rápida

Paso 1 — Auto-detección de parámetros del proyecto

Al abrir la pestaña 🧮 Estimación Rápida, la app lee automáticamente tres parámetros de la sesión:

kWp del sistema: tomado de Página 4 — Dimensionamiento (P_stc_kW_sistema). Si el Dimensionamiento no se ha ejecutado, ingresa el kWp manualmente en el campo correspondiente.

Ciudad / Zona geográfica: detectada desde Página 1 — Proyecto. Si la ciudad pertenece a Urabá o Chocó, el factor de zona (×1.17) se aplica automáticamente.

Tipo de instalación: inferido desde la densidad W/m² configurada en Página 1. Si la densidad está por debajo de 120 W/m² se asume BIPV; por encima de 130 W/m² con tilt ≤15° se asume Granja FV campo.

Un banner de confirmación muestra los valores auto-detectados. Puedes sobrescribir cualquiera de los tres antes de calcular.

Paso 2 — Seleccionar tipo, escenario y zona

Tipo de instalación: define los benchmarks de costo USD/Wp

Tipo  │  Rango CAPEX referencia  │  Contexto típico

🏚️ Granja FV campo  │  0.70–1.10 USD/Wp  │  Parques solares en suelo, acceso vehicular, obra civil limitada

🏢 Techo industrial  │  0.90–1.45 USD/Wp  │  Cubiertas planas o inclinadas, estructura metálica, sin obra civil pesada

🏢 BIPV fachada / pérgola  │  1.60–3.20 USD/Wp  │  Integración arquitectónica, mano de obra especializada, estructura a medida

Escenario económico: ajusta los benchmarks dentro de cada tipo

Escenario  │  Significado  │  Cuándo usarlo

Optimista  │  Precios mínimos del rango: proveedores negociados, volumen, zona de fácil acceso  │  Verificar si hay margen en el mejor caso posible

Base  │  Valor central del mercado colombiano (julio 2026)  │  Presentación estándar al cliente o inversionista

Conservador  │  Precios máximos: zona remota, lote pequeño, contratista nuevo  │  Evaluar riesgo antes de comprometerse

Factor de zona geográfica: multiplica los costos de obra civil, logística y estructura

Zona  │  Factor  │  Por qué

Bogotá / Sabana  │  ×1.00  │  Referencia base — mejor acceso a proveedores

Medellín / Antioquia  │  ×1.05  │  Logística desde Valle de Aburrá

Cali / Valle  │  ×1.07  │  Distancia a puertos y distribuidoras

Barranquilla / Costa  │  ×1.08  │  Calor, corrosión salina, fletes costeros

Urabá / Chocó (tropical)  │  ×1.17  │  Acceso difícil, humedad extrema, flete terrestre y fluvial, mano de obra escasa

Llanos Orientales  │  ×1.12  │  Transporte en temporada de lluvias, acceso limitado

Otra zona remota  │  ×1.15  │  Aplica a cualquier zona sin vía pavimentada o con acceso estacional

Paso 3 — Ejecutar y leer el desglose

Clic en " Calcular Estimación Rápida". La app produce un desglose en cuatro categorías:

Categoría  │  Componentes incluidos  │  % típico del CAPEX total

🔩 Equipos / Duros  │  Módulos FV, inversores, estructura, cableado DC/AC, protecciones, transformador MT (si kWp ≥ 100), SCADA, logística  │  55–65%

🏗️ Construcción / EPC  │  Obra civil y cimentación, montaje estructural, instalación eléctrica, puesta en marcha  │  20–28%

🧾 Costos Blandos  │  Ingeniería + diseño, gestión de proyecto (PM), permisos / RETIE / UPME, conexión a la red  │  8–14%

⚙️ Contingencias  │  Reserva sobre el CAPEX base para imprevistos de ejecución  │  8–16%

La tabla muestra tres columnas por fila:

USD: valor en dólares

% CAPEX: participación de esa línea sobre el CAPEX total

COP (M): equivalente en millones de pesos colombianos a la TRM actual

Las filas de encabezado de categoría aparecen con fondo azul. Los subtotales aparecen en negrita. El renglón ✅ CAPEX TOTAL es el valor final que se envía a Financiero.

Paso 4 — Comparativo de tres escenarios

Debajo de la tabla principal aparece automáticamente un comparativo horizontal con los tres escenarios (Optimista / Base / Conservador) para la misma combinación de tipo de instalación y zona:

Métrica  │  Optimista  │  Base  │  Conservador

CAPEX total (USD)  │  Valor mínimo  │  Valor central  │  Valor máximo

CAPEX por Wp (USD/Wp)  │  ───  │  ───  │  ───

OPEX anual (USD/año)  │  ───  │  ───  │  ───

OPEX por kWp (USD/kWp·año)  │  ───  │  ───  │  ───

Este comparativo permite al promotor comunicar la incertidumbre al cliente de forma honesta: 'el proyecto cuesta entre USD X (optimista) y USD Z (conservador), con escenario base de USD Y.'

Paso 5 — Revisar el OPEX anual

La sección de OPEX muestra cinco componentes con sus valores anuales:

O&M preventivo (visitas técnicas): USD/kWp·año × kWp

Limpieza de módulos: USD/kWp·año × kWp (mayor en Urabá por la lluvia y vegetación)

Fondo de reposición de inversor: USD/kWp·año provisionado desde el año 1 para reemplazo al año 12–15

Monitoreo remoto (SCADA/Growatt): USD/kWp·año

Seguro operativo todo riesgo: % del CAPEX total por año

Referencia rápida de OPEX Colombia:

Tipo  │  OPEX/kWp·año (Base)  │  Rango típico

Granja FV campo  │  USD 10/kWp·año  │  USD 8–12

Techo industrial  │  USD 9/kWp·año  │  USD 6–12

BIPV fachada / pérgola  │  USD 13/kWp·año  │  USD 10–16

Paso 6 — Aplicar o limpiar

✅ Aplicar al Financiero: escribe los resultados en la memoria de sesión para que Página 7 — Análisis Financiero los use automáticamente. Guarda los siguientes valores:

presupuesto_capex_usd → CAPEX total en USD

presupuesto_opex_anual_usd → OPEX anual en USD

presupuesto_fraccion_equipos → fracción de equipos duros (para calcular Art. 12 Ley 1715 — exclusión de IVA)

presupuesto_capex_directo → usado internamente en Financiero

presupuesto_capex_blando → costos blandos del proyecto

Un banner verde confirma que los valores fueron aplicados. Desde ese momento, Página 7 muestra ✅ CAPEX desde Estimación Rápida en lugar del campo de entrada manual.

🔄 Limpiar: borra los valores paramétricos de la sesión y devuelve Financiero al modo de entrada manual. Úsalo si decides reemplazar la estimación con cotizaciones reales.

────────────────────────────────────────────────────────────

Interacción con las pestañas de cotización real

La Estimación Rápida y las pestañas de cotización real (Perfilería, Mano de Obra, Sistema FV, Inversor, Catálogo, Costos Blandos, OPEX) coexisten en la misma página con la siguiente lógica de prioridad:

Modo  │  Condición  │  ¿Qué usa Financiero?

Estimación Rápida activa  │  Botón Aplicar presionado y todas las pestañas de cotización vacías  │  CAPEX y OPEX paramétricos

Cotización real activa  │  Al menos una pestaña de cotización tiene datos ingresados  │  CAPEX calculado desde sub-totales reales; flag paramétrico se desactiva automáticamente

Sin datos  │  Estimación no aplicada y pestañas vacías  │  Financiero usa el campo de entrada manual de CAPEX

Importante: la cotización real SIEMPRE tiene prioridad sobre la paramétrica. No necesitas borrar la Estimación Rápida antes de ingresar cotizaciones reales — la app lo detecta sola.

────────────────────────────────────────────────────────────

Precisión y limitaciones

Precisión esperada: ±25–35% del CAPEX real.

Esto equivale a:

Proyecto de USD 650 000 (Base): rango de incertidumbre de ±USD 160 000–230 000

Proyecto de USD 50 000 (Techo 50 kWp): rango de ±USD 12 500–17 500

Esta precisión es:

Inaceptable para bancabilidad formal o estructuración de crédito

Perfectamente suficiente para decidir si contratar un estudio de factibilidad (etapa 1 → etapa 2)

Mejor que la hoja de Excel improvisada que la mayoría de promotores usan en prefactibilidad

Factores que la Estimación Rápida NO cubre:

Precios spot de equipos (los benchmarks son de julio 2026 y no se actualizan automáticamente)

Costos de acceso a sitio fuera de los factores de zona (helicóptero, barcaza, mula)

Obras civiles atípicas (refuerzo estructural de fachada existente, adecuación de cubierta)

Costos de interconexión en alta tensión (>500 kWp)

Financiamiento (intereses, costos de estructuración)

Para estos casos, completa las pestañas de cotización real o consulta directamente con un EPC calificado.

### Encabezado del presupuesto

Antes de comenzar, completa el bloque superior (expandible):

Campo  │  Qué es  │  Por qué importa

Nombre del proyecto  │  Identificador único  │  Traza el presupuesto a un proyecto específico

Vigencia  │  Fecha hasta la que los precios son válidos  │  Los bancos exigen presupuestos vigentes; precios de hace >90 días se consideran desactualizados

Elaboró  │  Nombre de la empresa o profesional  │  Da trazabilidad y responsabilidad técnica al documento

────────────────────────────────────────────────────────────

### Estructura de 8 pestañas (incluyendo Estimación Rápida)

Pestaña  │  Contenido  │  Categoría financiera

🧮 Estimación Rápida  │  CAPEX y OPEX paramétrico por benchmarks Colombia  │  Prefactibilidad / Escalamiento

🔩 Perfilería y Estructura  │  Rieles, soportes, fijaciones BIPV  │  CAPEX Directo

👷 Mano de Obra  │  Instalación, certificación RETIE, transporte  │  CAPEX Directo

Sistema FV  │  Cables, protecciones, cajas, puesta a tierra, monitoreo  │  CAPEX Directo

🔌 Inversor y Equipos Eléctricos  │  Tableros, breakers, comunicaciones  │  CAPEX Directo

📦 Equipos del Catálogo  │  Módulos + inversor + baterías (auto desde Dimensionamiento)  │  CAPEX Directo

🧾 Costos Blandos  │  Ingeniería, trámites, legal, PM, ITA, póliza CAR  │  CAPEX Blando (soft costs)

📅 OPEX Anual  │  O&M, limpieza, seguro operativo, monitoreo, fondos reposición  │  Gasto operativo anual

────────────────────────────────────────────────────────────

### Columna "✔ Activo" — incluir o excluir ítems

Cada fila tiene un checkbox al inicio:

- ✅ Marcado: el ítem suma al subtotal y al CAPEX total.
- ☐ Desmarcado: queda visible como referencia pero no suma. Útil
para ítems opcionales o que cubre otra partida del contrato.

Agregar una fila nueva: botón ➕ al pie de la tabla → fila en blanco → escribe directamente.

Eliminar una fila: selecciona la fila → tecla Supr / Delete.

Resetear: botón ↺ en la parte superior de cada pestaña vuelve a la plantilla base del Excel.

────────────────────────────────────────────────────────────

### Fuente de precios — campo de trazabilidad

Cada pestaña tiene un campo de texto "Fuente / cotización". Escribe aquí el

origen de los precios ingresados (ej.: "Cotización Acesco julio 2026",

"Lista de precios Schneider distribuidora Medellín").

Impacto bancario: El auditor técnico independiente (ITA) y el banco

verifican que los precios sean de mercado y tengan respaldo documental.

Sin fuente, los precios se consideran estimados, no cotizaciones.

────────────────────────────────────────────────────────────

### 📄 Carga automática de cotizaciones (PDF/Word) — extractor genérico + clasificador  NUEVO (22-ago-2026)

Un único punto de carga, visible en la parte de arriba de la página (arriba de las 8 pestañas, dentro del expansor "📄 Cargar cotización de proveedor"), permite subir la cotización REAL de un proveedor (PDF o Word .docx) y que sus valores lleguen a la pestaña correcta sin transcribirlos a mano. No está atado a un proveedor ni a una plantilla específica — funciona con cualquier layout, en español o inglés.

¿Cómo funciona? (3 pasos automáticos + 1 de confirmación)

- 1️⃣ Extracción: la app lee el texto y las tablas del documento (por encabezado de columna, no por posición fija — reconoce "Capacidad"/"Potencia"/"Install Capacity" o "Precio Unitario"/"Price/Watt" sin importar el orden de las columnas) y saca: proveedor, número de cotización, fecha, descripción del ítem, capacidad (W), precio unitario (USD/W), flete, total FOB, total CIF, incoterm y condiciones de pago.
- 2️⃣ Respaldo por IA (solo si algo no se encontró): si el servidor tiene una clave de IA configurada (🧭 Asistente usa la misma), se le pide el campo faltante — pero el modelo debe CITAR el fragmento exacto del documento de donde lo sacó; si ese fragmento no existe literalmente en el texto, el campo se descarta. Es una salvaguarda anti-invención: ningún valor de IA se acepta "porque sí".
- 3️⃣ Clasificación de sección: un contador de palabras clave por categoría (p. ej. "estructura/montaje" → Perfilería; "instalación/RETIE" → Mano de Obra; "cable/monitoreo" → Sistema FV; "tablero/breaker" → Inversor y Equipos Eléctricos; "panel/módulo/batería" → Catálogo; "ingeniería/legal/seguro" → Costos Blandos) SUGIERE a qué de las 6 pestañas de cotización pertenece el documento. Aparece un selector con la sugerencia preseleccionada y el detalle de cuántas coincidencias tuvo cada sección — puedes cambiarla si no es la correcta.
- 4️⃣ Confirmación (obligatoria): antes de aplicar nada, la app muestra una tabla con cada campo, su valor propuesto, el método (🔤 patrón o 🤖 IA) y el fragmento de evidencia citado del documento. **Nada se aplica a Presupuesto sin que lo confirmes con el botón "✅ Aplicar".**

¿A qué 6 secciones puede dirigir una cotización? Las mismas del listado de pestañas de esta página, EXCEPTO Estimación Rápida (que es paramétrica, no basada en cotizaciones reales): 🔩 Perfilería y Estructura, 👷 Mano de Obra, ⚡ Sistema FV, 🔌 Inversor y Equipos Eléctricos, 📦 Equipos del Catálogo, 🧾 Costos Blandos.

Dos formas de armar la fila de costo (automático según lo que trae el documento):

- Cotización por Watt (típico de estructura o paneles): si el documento trae capacidad (W) Y precio unitario (USD/W), la fila queda como Cantidad = capacidad en W, Unidad = "W", USD/un = precio por watt.
- Monto global (típico de mano de obra, ingeniería, seguros — casi nunca se cotizan por Watt): si no hay capacidad/precio unitario pero sí un Total, la fila queda como Cantidad = 1, Unidad = "glb", USD/un = el total detectado.
- Si el documento trae flete marítimo, se agrega una segunda fila aparte ("Flete marítimo — {proveedor}") en la misma sección.

⚠️ Para no cometer errores — verificación cruzada: si el documento trae capacidad, precio unitario Y un total, la app compara Capacidad × Precio unitario contra ese total. Si difieren más de 2%, muestra una advertencia — revisa los valores extraídos antes de aplicar, puede ser un campo mal leído.

Reemplazar o quitar una cotización ya aplicada:

- Volver a cargar la MISMA cotización (mismo número) actualizada: la app reemplaza la fila anterior automáticamente en vez de duplicarla.
- Quitarla del todo: usa los mecanismos que ya existían en cada tabla — desmarca el checkbox ✔ Activo (la excluye sin borrar), bórrala con Supr, o usa "↺ Resetear" para volver a la plantilla en blanco de esa sección.
- "🗑️ Descartar cotización cargada": borra la extracción pendiente ANTES de aplicarla, sin tocar ninguna tabla.

¿Se guarda a disco? Solo si la sección destino es una de las persistibles: 🔩 Perfilería, 👷 Mano de Obra, ⚡ Sistema FV, 🔌 Inversor y Equipos Eléctricos. 📦 Equipos del Catálogo y 🧾 Costos Blandos NO se guardan en disco entre sesiones (mismo comportamiento que ya tenían esas dos pestañas antes de esta función) — la app lo avisa en pantalla al aplicar. El campo "Fuente / cotización" de la pestaña destino se autocompleta con "Cotización {proveedor} {número} ({fecha})" para trazabilidad bancaria.

⚠️ Para no cometer errores — moneda: Presupuesto solo trabaja en USD. Si la app detecta que la cotización está en otra moneda (COP, EUR, CNY), lo avisa y NO convierte automáticamente — ajusta los valores a mano antes de aplicar.

────────────────────────────────────────────────────────────

### 🧾 Pestaña Costos Blandos — soft costs

Los costos blandos son todos los gastos del proyecto que no son materiales

ni mano de obra de instalación física. Representan entre el **8–18% del CAPEX

directo** en proyectos BIPV en Colombia.

Ítem  │  Qué incluye  │  Referencia Colombia

Ingeniería, diseño y memorias  │  Planos eléctricos y mecánicos, cálculos estructurales, estudio de producción  │  1.5–3% CAPEX directo

Estudio de sombreado y simulación BIPV  │  Modelo 3D, análisis horario, curvas IV, informe técnico  │  USD 800–2.500 (proyecto pequeño)

Registro UPME y trámites Ley 1715  │  Solicitud calificación UPME, resolución de calificación  │  USD 500–1.200 (incluye honorarios gestor)

Concepto de conexión — operador de red  │  Solicitud al operador local (EPM, ENEL, etc.) para conexión en paralelo  │  USD 200–800

Certificación RETIE / RITEL  │  Inspección por organismo certificador acreditado. Obligatorio en Colombia  │  USD 300–900 según potencia

Gestión del proyecto (PM)  │  Director de proyecto, coordinación, informes de avance, actas de entrega  │  3–5% CAPEX directo

Asesoría legal y estructuración financiera  │  Contratos EPC, contrato O&M, asesoría financiera, estructuración crédito  │  USD 1.500–5.000

Auditoría técnica independiente (ITA)  │  Revisión por firma especializada externa. Obligatorio para financiamiento > USD 200k  │  USD 2.000–8.000

Póliza CAR — construcción todo riesgo  │  Seguro durante la ejecución del proyecto (daños, robo, responsabilidad civil)  │  0.4–0.6% CAPEX directo

Gastos notariales, registros y licencias  │  Escrituras de servidumbre, permisos municipales, otros  │  USD 300–1.000

Impacto: Si omites los costos blandos, el CAPEX está subvalorado en

un 8–18%. Esto hace que la TIR calculada sea artificialmente alta y el

VPN sobreestimado — el proyecto parecerá más rentable de lo que es.

Un banco detecta esto inmediatamente y lo considera una señal de riesgo.

────────────────────────────────────────────────────────────

### 📅 Pestaña OPEX Anual — costos de operación

El OPEX (Operating Expenditure) es el costo anual de mantener el sistema

funcionando durante su vida útil (25–30 años). Es la diferencia entre los

ingresos brutos por energía y el flujo de caja neto que recibe el inversionista.

Los valores en esta pestaña representan USD por año (no por unidad física).

El total anual se envía automáticamente a  Financiero para construir el

flujo de caja a 25 años.

Ítem  │  Qué incluye  │  Referencia Colombia

O&M preventivo — visitas técnicas  │  Revisión anual de módulos, strings, inversor, cableado, torqueo de conexiones  │  USD 5–10/kWp·año

Limpieza de módulos  │  Lavado manual o con agua a presión. En Urabá: alta frecuencia por humedad y vegetación  │  USD 1–3/kWp·año (4 veces/año aprox.)

Seguro operativo — todo riesgo  │  Cubre daños por granizo, viento, cortocircuito, robo de módulos o inversor  │  0.3–0.5% CAPEX/año

Monitoreo remoto (Growatt/SCADA)  │  Plataforma de telemetría en tiempo real, alertas de falla, informes de producción  │  USD 200–600/año

Revisión anual inversor  │  Actualización firmware, limpieza ventiladores, verificación protecciones  │  USD 150–400/año

Fondo de reposición inversor  │  Provisión anual para reemplazar el inversor al año 12–15 de vida  │  Costo inversor ÷ 12 años

Fondo de reposición módulos  │  Provisión para módulos dañados fuera de garantía, degradación acelerada  │  0.1–0.2% CAPEX/año

Administración y costos fijos  │  Contabilidad, reportes a UPME, administración de contratos O&M  │  USD 300–800/año

Referencia consolidada Colombia BIPV:

KPI OPEX  │  Valor de referencia

OPEX total / kWp · año  │  USD 8–15

OPEX / CAPEX anual  │  1.0–2.5%

Fondo reposición inversor  │  ~0.8–1.2% CAPEX/año

Impacto financiero: Si el OPEX es USD 0 en el modelo, la TIR y el VPN

están sobreestimados. Un modelo sin OPEX no es financieramente evaluable.

El banco proyecta el OPEX incluso si el solicitante no lo incluye, y usa

sus propios estimados (conservadores) si no hay datos del proyecto.

────────────────────────────────────────────────────────────

### Cálculo del CAPEX Total — tres niveles de contingencia

El CAPEX total se construye en cascada:

CAPEX Directo     = Perfilería + Mano de Obra + Sistema FV + Inversor + Catálogo
CAPEX Base        = CAPEX Directo + Costos Blandos
─────────────────────────────────────────────────────────
+ Costos indirectos (%)   → AUI: Administración, Imprevistos, Utilidad del contratista
+ Contingencia técnica (%) → Reserva por riesgo específico de instalación BIPV en fachada
+ Contingencia de precios (%) → Reserva por volatilidad de TRM y materiales importados
═════════════════════════════════════════════════════════
= CAPEX TOTAL     → va a Financiero, Ley 1715 y Reporte PDF

Significado de cada contingencia

Costos indirectos — AUI (Administración, Imprevistos, Utilidad)

El AUI es el porcentaje que aplica el contratista EPC sobre el costo

directo para cubrir sus propios gastos de administración, los imprevistos

de ejecución y su utilidad neta.

- Referencia Colombia: 10–18% del CAPEX directo.
- En proyectos BIPV con acceso difícil o trabajo en altura: extremo alto del rango.
- No confundir con la utilidad del inversionista (dueño del proyecto).
Contingencia técnica

Reserva específica para riesgos de ejecución que son más altos en BIPV

que en una instalación convencional en suelo:

- Integración con la fachada existente (interferencias no previstas en planos)
- Trabajos en altura con andamios o grúas
- Adaptaciones estructurales del edificio
- Pruebas de compatibilidad electromagnética con la fachada
- Referencia: 8–15% para BIPV de fachada. Instalación en suelo: 4–8%.
Contingencia de precios

Reserva para absorber el impacto de variaciones en el tipo de cambio

(TRM) y en los precios de materiales importados (módulos, inversor,

cables de cobre) entre la fecha del presupuesto y la ejecución.

- Referencia: 3–7% según horizonte de ejecución.
- Para proyectos con ejecución > 6 meses desde la cotización: usar extremo alto.
────────────────────────────────────────────────────────────

### KPIs de bancabilidad — semáforo automático

La calculadora evalúa cuatro indicadores y muestra alertas si están

fuera del rango de referencia para proyectos BIPV en Colombia:

KPI  │  Cálculo  │  Rango sano  │  Alerta si...

USD / Wp  │  CAPEX total ÷ potencia instalada (W)  │  USD 1.8–4.0/Wp  │  > 5.0/Wp (precio en COP?) · > 3.5/Wp (rango alto)

USD / m²  │  CAPEX total ÷ área de fachada (m²)  │  USD 180–350/m²  │  > 400/m²

OPEX / CAPEX  │  OPEX anual ÷ CAPEX total  │  1.0–2.5%/año  │  > 3.0%

OPEX / kWp·año  │  OPEX anual ÷ potencia instalada  │  USD 8–15/kWp  │  indicativo

USD/Wp es el indicador más universal. Un banco lo compara contra

proyectos financiados en la región. Si está fuera de rango, el banco

pide justificación técnica o rechaza el presupuesto.

USD/m² es clave para BIPV porque relaciona el costo con el área

de fachada aprovechada, no solo con la potencia. Un edificio en zona

de alto costo de construcción puede tener un USD/m² alto pero un

USD/Wp razonable — es importante mostrar ambos.

────────────────────────────────────────────────────────────

### Fracción de equipos — base para Ley 1715

La calculadora determina automáticamente qué proporción del CAPEX total

corresponde a equipos calificables (módulos, inversor, sistema FV):

Fracción equipos = (Sistema FV + Inversor + Catálogo) ÷ CAPEX total

Esta fracción es la base del Art. 12 — Exclusión IVA y del

Art. 11 — Deducción renta de la Ley 1715. Si es incorrecta, los

beneficios tributarios en Financiero quedan mal calculados.

────────────────────────────────────────────────────────────

### Conexión automática con otras páginas

Dato exportado  │  Lo usa  │  Para qué

CAPEX TOTAL  │  Financiero  │  TIR, VPN, Payback, LCOE, Ley 1715

OPEX Anual  │  Financiero  │  Flujo de caja anual a 25 años (reemplaza el slider paramétrico)

Fracción equipos  │  Financiero  │  Art. 11 y Art. 12 Ley 1715

CAPEX TOTAL  │  Reporte PDF  │  Sección de costos y resumen ejecutivo

En  Financiero aparece un toggle que permite elegir entre:

- OPEX del presupuesto detallado (recomendado, valores reales ingresados aquí)
- OPEX paramétrico (slider % del CAPEX, para estimaciones rápidas)
────────────────────────────────────────────────────────────

### TRM y precios en USD

Todos los precios se ingresan en USD. La conversión a pesos colombianos

(millones de COP) se muestra automáticamente usando la TRM del campo superior.

⚠️ Error frecuente: ingresar precios en COP en lugar de USD. La alerta

de USD/Wp > 5.0 es el primer síntoma. Si ocurre, divide todos los

precios de esa sección por la TRM vigente.

────────────────────────────────────────────────────────────

### 📤 Exportar cotización para el cliente (Excel / PDF)  NUEVO

Al final de la página 8 — Presupuesto está la sección «📤 Exportar cotización»: genera un documento limpio para entregar al cliente, con los ítems activos agrupados por categoría, subtotal (CAPEX directo), costos blandos, indirectos, contingencia y TOTAL en pesos colombianos (formato $ 12.345.678), más el equivalente en USD con la TRM del proyecto.

- Campos editables: nombre del cliente/destinatario, validez de la oferta (15 días por defecto) y notas/condiciones del pie.
- Dos botones de descarga: Cotizacion_<proyecto>_<fecha>.xlsx y .pdf.
- Solo se exportan ítems con la casilla «✔ Activo» marcada y con cantidad y precio mayores que cero.
- El documento NO incluye la columna de fuente de precios ni los KPIs bancarios — es apto para entregar al cliente final.
⚠️ IMPORTANTE: el total de la cotización se calcula SIEMPRE desde los mismos ítems que se exportan (subtotal + blandos + indirectos + contingencia). Si difiere más de 1% del CAPEX del Resumen, la app lo avisa — suele pasar cuando la Estimación Rápida sigue aplicada o hay ítems desactivados; recalcula el Resumen si quieres que coincidan.

🚨 ALERTA PARA EVITAR ERRORES: si los botones de descarga aparecen deshabilitados es porque no hay ítems activos con valor. Completa al menos una pestaña de cotización (o aplica la 🧮 Estimación Rápida y luego ingresa cotizaciones reales).

## 12. Página 11 — Baterías y Balance

Propósito: Dimensionar el sistema de almacenamiento y calcular el balance energético

(autogeneración, autosuficiencia, excedentes a red).

### E_ac corregida por bypass (nuevo)

Si bypass fue ejecutado en Página 5, la E_ac usada para el balance es la corregida.

Verás el banner:

⚡ Corrección bypass activa:
E_ac base = 91.000 kWh/año → pérdida bypass = 2.850 kWh/año → E_ac usada en el balance = 88.150 kWh/año (3.1% menos)
La autogeneración y el dimensionamiento de la batería se calculan con la producción real.

Esto evita sobredimensionar la batería basándose en una producción solar inexistente.

### Pasos

- Seleccionar la batería del catálogo (o ingresar manualmente)
- Ingresar el perfil de consumo del edificio (kWh/día o perfil horario)
- Ejecutar el balance energético
Resultados:

- Tasa de autogeneración (%) — fracción del consumo cubierta por solar
- Tasa de autosuficiencia (%) — fracción de la producción solar autoconsumida
- Excedentes a red (kWh/año)
- Dimensionamiento recomendado de la batería (kWh y ciclos/año)
────────────────────────────────────────────────────────────

### Consumo sincronizado con la factura real de 🏠 Proyecto  NUEVO (21-ago-2026)

Si en 🏠 Proyecto elegiste el modo "Conozco mi consumo/factura" (en vez de "Tengo un área disponible"), ese valor de consumo real ahora es el punto de partida por defecto en los 3 modos de consumo de esta página (consumo diario, perfil típico anual, resolución horaria y 12 valores manuales) — en vez de estimarlo siempre desde la producción solar (E_ac/365 o E_ac × 1.2). Verás un aviso "📄 Sugerido desde tu factura/consumo declarado en Proyecto: ..." cuando aplique.

- Puedes seguir ajustando el valor manualmente en cualquier momento — el valor de Proyecto solo fija el default inicial, no un valor forzado.
- Si en Proyecto elegiste "Tengo un área disponible" (sin factura), el comportamiento no cambia: se sigue estimando desde la producción, como antes.
⚠️ Para no cometer errores: si tienes la factura real, complétala en 🏠 Proyecto ANTES de entrar a Baterías — así los 3 modos de consumo parten de la misma cifra real en vez de 3 estimaciones distintas entre sí.

────────────────────────────────────────────────────────────

### ⚖️ Comparador de Baterías + Analista de Producción  NUEVO

Sección para comparar varios modelos de batería del catálogo (o configuraciones de capacidad) bajo el mismo balance energético del proyecto, con autonomía, profundidad de descarga (DoD) y vida útil estimada de cada opción.

- Columna Compatible con 3 estados (a diferencia de paneles/inversores, que solo tienen 2): ✅ compatible confirmado, ⚠️ el catálogo no tiene datos suficientes para confirmar la compatibilidad de voltaje (NO tratar como un "sí"), ❌ incompatible confirmado.
- Botón "🤖 Analista de Producción": redacta la recomendación citando autonomía, DoD, vida útil y compatibilidad de voltaje de cada batería comparada.
⚠️ Para no cometer errores: una batería marcada ⚠️ no es una batería aprobada — significa que falta información en su ficha de catálogo para confirmar la compatibilidad de voltaje. Verifica manualmente contra la ficha del fabricante antes de adoptarla.

────────────────────────────────────────────────────────────

## 13. Página 10 — Reporte PDF

Propósito: Generar el reporte técnico descargable del proyecto.

### Secciones del reporte

Sección  │  Contenido  │  Disponible si  │  Checkbox

1. Proyecto  │  Datos generales, ubicación, sistema  │  Siempre  │  —

2. Recurso Solar  │  POA anual, GHI, temperatura  │  Página 2 ejecutada  │  —

3. Motor Óptico  │  Cascada IAM + Soiling + Térmico  │  Página 5b ejecutada  │  ✅ Motor Óptico

4. Producción  │  E_ac, PR, Factor de Planta  │  Página 6 ejecutada  │  ✅ Producción

4b. Diagnóstico  │  PR real vs esperado mes a mes  │  Datos reales ingresados  │  —

4c. Bypass Diodes  │  Pérdidas bypass, tabla mensual  │  Página 5 ejecutada  │  ✅ Bypass Diodes

4d. Multi-Superficie  │  Desglose E_ac + bypass por superficie  │  Página 9 integrada  │  ✅ Multi-Superficie

5. Financiero  │  TIR, VPN, Payback + fuente E_ac  │  Página 7 ejecutada  │  ✅ Financiero

5b. Costos Presupuesto  │  CAPEX, OPEX, KPIs de bancabilidad  │  Página 8 completada  │  ✅ Costos Presupuesto

6. Balance  │  Autogeneración, batería  │  Página 11 ejecutada  │  ✅ Balance

7. CO₂  │  Emisiones evitadas, equivalencias  │  Página 12 ejecutada  │  ✅ CO₂

### Sección 4c — Bypass Diodes (superficie única)

Cuando el modelo de bypass fue ejecutado en Página 5, el reporte incluye:

- Tabla con pérdida anual, % E_dc, horas bypass, E_ac corregida
- Fuente del FS (geométrico o combinado) y modo de cobertura temporal
- Semáforo de impacto: 🟢 < 2% · 🟡 2–5% · 🔴 > 5%
- Tabla mensual con pérdidas coloreadas (rojo si > 20 kWh ese mes)
- Referencia técnica: Deline et al. 2013
### Sección 4d — Multi-Superficie (nueva, #45)

Cuando Página 9 fue integrada, el reporte incluye una tabla por superficie con:

- E_ac base, pérdida bypass (%), horas bypass/año, E_ac con bypass
- Fila TOTAL SISTEMA con área total y E_ac total
- Nota con densidad del sistema (kWh/m²·año)
Activar con checkbox " Incluir desglose Multi-Superficie" en opciones del reporte.

### Sección 5b — Costos del Presupuesto (nueva, #8)

Cuando Página 8 fue completada, el reporte incluye:

- CAPEX directo (equipos + obra) y costos blandos en USD y M COP
- CAPEX total y KPIs: USD/m², USD/kWp, OPEX/CAPEX
- Fracción de equipos (base para beneficios Ley 1715)
Activar con checkbox " Incluir Resumen de Costos del Presupuesto".

### Sección 5 — Trazabilidad de E_ac (actualizado, #38)

La sección Financiero del reporte muestra qué fuente de E_ac se usó (en orden de prioridad):

# Caso 1: Sistema multi-superficie con bypass
E_ac usada: 33.929 kWh/año (multi-superficie — 2 superficies + bypass)

# Caso 2: Superficie única con bypass
E_ac usada: 88.150 kWh/año (corregida por bypass diodes)
Pérdida bypass descontada: 2.850 kWh/año (3.1% de E_ac base)

# Caso 3: Simulación estándar
E_ac usada: 91.000 kWh/año (simulación estándar superficie única)

Esto permite al cliente o a la UPME verificar que los números de TIR y Payback son conservadores y realistas (no optimistas).

### Cómo generar el PDF

- Completa los campos "Nombre de la empresa" y "Nombre del proyecto"
- Selecciona qué secciones incluir (checkboxes)
- Clic en "⬇️ Descargar reporte (.html → imprimir como PDF)"
- El archivo .html se abre en el navegador
- Usa Ctrl+P → Guardar como PDF (escala recomendada: 85%, márgenes: mínimos)
────────────────────────────────────────────────────────────

### Datos bifaciales en el reporte  NUEVO

Si la simulación bifacial está activa, la sección «Recurso Solar y POA del Sitio» del PDF incluye una tabla adicional con: modelo usado (pvlib infinite_sheds), bifacialidad (%), altura de montaje, albedo trasero y la ganancia bifacial anual (%). Así el cliente y el banco ven de dónde sale la energía extra. Si la simulación bifacial está apagada, el reporte no cambia.

────────────────────────────────────────────────────────────

### 🔒 Sellar el reporte en el Ledger de Auditoría  NUEVO (25-ago-2026)

Justo antes del botón "📄 Generar Reporte" aparece el checkbox **"🔒 Sellar este resultado en el Ledger de Auditoría"**, marcado por defecto (se puede desmarcar). Junto a él hay un selector de tipo — **🏦 Presupuesto bancable (banco/ITA)** o **📋 Verificación presupuestal informativa** — y un campo de nota opcional (ej. "Versión final entregada al cliente").

Si el checkbox está marcado y presionas "Generar Reporte":

- La app sella un eslabón nuevo en la cadena de hashes de este proyecto (ver la sección completa del "🔒 Ledger de Auditoría" más abajo en este manual para el detalle técnico).
- El propio archivo HTML/PDF entregado queda con un pie de página impreso: **"🔒 ID de verificación del Ledger de Auditoría: `<hash corto>` — sellado `<fecha>` — verificable en la página 🔒 Ledger de Auditoría del proyecto."** Esto significa que el documento que le entregas al cliente o al banco lleva su propia huella digital verificable — no es solo un PDF suelto, es un PDF con una prueba de integridad que se puede cotejar contra tu base local.
- Si por algún motivo no se pudo sellar (sin sesión activa, o falla de disco), la app avisa con un mensaje explícito y genera el reporte igual, sin ID de verificación — nunca falla en silencio ni bloquea la entrega del reporte.

⚠️ Para no cometer errores: el tipo de sello que elijas aquí (bancable vs. informativo) queda registrado dentro del eslabón — úsalo con criterio, porque de eso depende cómo se etiqueta ese resultado en el historial del Ledger.

## 13b. Página 15 — Catálogo de Inversores PDF  NUEVO

Propósito: Agregar inversores al catálogo subiendo directamente la ficha técnica del fabricante en PDF. La app extrae automáticamente los parámetros eléctricos y los deja listos para revisar y guardar en el Excel del catálogo, sin transcripción manual.

Cómo usarla

1. Arrastra el PDF del datasheet al cargador. Se reconocen fichas de Growatt, Solis, Deye, MUST, SolaX, LuxPower, POWEST, Huawei, SMA, Fronius, GoodWe, Sofar, Sungrow, Victron, SolarEdge, Delta, Chint, Kstar, Voltronic y compatibles — en inglés y en español.

2. La app muestra un banner de estado: ✅ PDF digital procesado · 📷 PDF escaneado con OCR aplicado (verifica los valores) · ❌ escaneado sin OCR disponible (completa el formulario a mano).

3. Revisa el formulario pre-llenado (potencias, tensiones MPPT, corrientes por tracker, número de MPPT y strings) y guarda el modelo en el catálogo.

Fichas multi-modelo (una tabla, varios inversores)

Muchos fabricantes publican una sola tabla con varias potencias (ej. SNA2-EU-LT 10K / 12K / 14K, o series Deye '9R–280R'). La app ahora separa cada columna en un modelo individual, con su propia potencia FV máxima, corriente máxima y corriente de cortocircuito por tracker. Las celdas combinadas del PDF (un valor que cubre varios modelos) se asignan al grupo correcto según la posición real de la columna.

Formatos difíciles que ya se procesan correctamente

· Fichas en español con unidades entre corchetes ([V], [A], [Wp]@STC) — SAJ, Huawei SUN2000, Growatt MAX/XMV/MID.

· Nombres de modelo partidos en dos líneas (TriP2-LB-3P 5-20K) y filas combinadas tipo 'trackers / strings per MPPT 3 / 2'.

· Folletos con varias tablas MODEL en un mismo PDF (Voltronic / InfiniSolar).

· Fichas escaneadas (imagen) mediante OCR — Felicity Solar, SolTech flexible. El banner 📷 recuerda verificar los valores extraídos.

· Si la ficha no publica la potencia FV máxima recomendada, la app la estima con ratio DC/AC 1,5 y lo advierte para que la ajustes si el fabricante indica otro límite.

Detección de fallos silenciosos (nuevo)

Si el extractor no logra leer campos importantes de un PDF nuevo, la app lo dice explícitamente en pantalla en lugar de dejar los campos en cero sin aviso. Así un formato de fabricante desconocido nunca entra al catálogo con datos incompletos sin que te des cuenta.

Verificación interna: existe además una página de pruebas del extractor (Página 16) que corre 26 casos de fichas reales para asegurar que los formatos ya soportados no se dañen al agregar soporte para nuevos fabricantes.

────────────────────────────────────────────────────────────

### Fichas con varios modelos: selección obligatoria  NUEVO

Muchas fichas técnicas (SolaX, Deye, Growatt…) traen una tabla con varios modelos de la misma familia (ej. 75K, 100K, 110K, 125K). Al detectarlo, la app muestra el selector «— Elige un modelo —» y el botón Guardar queda deshabilitado hasta que elijas uno.

Al elegir el modelo, el formulario se llena con los valores de ESA columna (Vdc máx, corrientes, número de MPPT, potencia FV máx) y el nombre del modelo queda fijado — así el catálogo no se contamina con datos mezclados de otra variante.

🚨 ALERTA PARA EVITAR ERRORES: nunca guardes «la familia» completa. Cada variante tiene corrientes y potencias distintas; guardar la equivocada hace que el emparejamiento de strings en Dimensionamiento dé resultados inválidos.

### Alerta de extracción incompleta (campos vacíos)  NUEVO

Tras procesar el PDF, la app cuenta cuántos campos críticos (voltajes MPPT, trackers, corrientes, potencia FV) quedaron vacíos:

- 🚨 Error rojo (más de 3 vacíos): el extractor probablemente no reconoció el formato del PDF. Revisa el texto crudo y completa el formulario a mano antes de guardar.
- ⚠️ Aviso amarillo (1 a 3 vacíos): faltan algunos datos puntuales — verifícalos contra la ficha antes de guardar.
Esta alerta evita el error silencioso más peligroso: guardar un inversor con campos en blanco que luego rompe el dimensionamiento sin aviso. En PDFs escaneados sin OCR la app muestra su propio mensaje y no duplica esta alerta.

### 3 alias reales agregados + 1 hallazgo NO corregido a propósito (28-ago-2026)

El usuario reportó (con ayuda de un tercero que diagnosticó "problema de mapeo de etiquetas") que una ficha en formato INNOVAQ en español (Woodward IDS SOLO 500, inversor central de 500-600 kW) no extraía 5 de 9 campos críticos. Verificado con ejecución real contra el texto exacto de la ficha (no solo teoría) antes de tocar código:

**3 campos SÍ eran un problema real de etiquetas** (agregados sin ambigüedad con marcas ya soportadas — cada patrón nuevo exige el texto exacto de la ficha en español, verificado que no colisiona con Growatt/SolaX/Huawei/SAJ):

- `Vdc_max`: la ficha dice «Voltaje FV máximo absoluto» — orden de palabras distinto a cualquier alias existente («máxima de entrada», «Máxima FV»).
- `Vmppt_min`/`Vmppt_max`: se publican en **filas separadas** («Voltaje MPP mínimo» / «Voltaje MPP máximo»), no como un rango combinado «X ~ Y V» en una sola línea — el motor de rangos (`_find_range()`) nunca los veía. Se agregó como un tercer fallback junto a los ya existentes de SMA/Fronius (`_INNOVAQ_MPPMIN_RE`/`_INNOVAQ_MPPMAX_RE`).
- `P_dc_max_W`: la ficha dice «Potencia FV máxima 600 kW» (kW, no Wp) — el patrón español existente solo aceptaba «W» pegado al número, no «kW».

**1 hallazgo real, NO corregido a propósito — no es un problema de etiquetas, es conceptual**: `I_max_tracker`/`Isc_max_tracker` («I máx (A)» / «Isc máx (A)») siguieron en blanco. El "diagnóstico" recibido sugería agregar un alias más para «Corriente de entrada máxima» → estos campos. **Eso habría sido un bug real y silencioso, no una mejora**: este inversor es central/utility-scale, sin trackers MPPT discretos (la propia ficha lo confirma: "N trackers no visible... puede que este modelo no exponga ese dato"). Su "Corriente de entrada máxima" (1140 A) es la corriente TOTAL del equipo, no una corriente POR tracker/string. `calculos/dimensionamiento.py` compara `I_max_tracker`/`Isc_max_tracker` directamente contra la corriente de UN string (`I_equiv`) en el gate de compatibilidad eléctrica — si se hubiera poblado con 1140 A, ese chequeo habría quedado falsamente permisivo para CUALQUIER configuración de strings, con cualquier inversor central que reporte así su corriente total (1140 A nunca lo supera un string real). El guard de plausibilidad existente (1-200 A) rechaza correctamente ese valor por ser implausible como corriente por tracker — es un comportamiento correcto del extractor, no un bug.

⚠️ Para futuros hallazgos similares: antes de agregar un alias nuevo, verificar que el campo de destino signifique lo mismo en la ficha nueva que en las fichas que ya lo alimentan — un nombre de columna igual no garantiza la misma semántica física.

Regresión: nuevo caso "Woodward IDS SOLO 500" en `scripts/casos_test_inversores.py` (Vdc_max/Vmppt_min/Vmppt_max/P_dc_max_W resueltos; V_arranque/n_trackers/n_strings_tracker/I_max_tracker/Isc_max_tracker esperados en `None` a propósito). Harness: **48/48 passed** (antes 47/47). Suite pytest completa: **717/717 passed**.

### Bug real encontrado al intentar guardar el inversor: ruta del Excel hardcodeada solo al servidor (28-ago-2026, mismo día)

Al intentar ingresar el Woodward IDS SOLO 500 al catálogo real con `guardar_inversor_excel()` (la función real de la app, mismo criterio que se usó para paneles), se encontró que `datos/catalogo_inversores_excel.py` tenía `_EXCEL` hardcodeado solo a `/var/www/bipv/calculadora-bipv/bipv_python/datos/inversores_catalogo.xlsx` — sin el mismo fallback relativo-primero-servidor-después que ya tenía `catalogo_paneles_excel.py`. En cualquier entorno de desarrollo local esto hacía que `cargar_catalogo_inversores()`/`guardar_inversor_excel()` reventaran con `FileNotFoundError`, y que `optimization.variables._catalogo_inversores_real()` cayera **en silencio** al catálogo Python chico de 7 inversores en vez del Excel real de 105 — sin ningún error visible, durante toda la sesión hasta este punto. Corregido con el mismo patrón de ruta relativa que ya usa el catálogo de paneles.

**3 tests dejaron de pasar tras el fix** (esperado: ahora usan el catálogo Excel real de 105 en vez del fallback Python de 7) y se corrigieron para reflejar el comportamiento real en vez de un accidente de entorno: `test_optimization_fase4.py::test_generar_candidatos_con_panel_e_inversor_varia_ambos` y `::test_generar_candidatos_sincroniza_eta_inversor_con_el_inversor_sorteado` (resuelven contra `_catalogo_inversores_real()`, no contra `INVERSORES` a secas), y `test_catalogo_inversores_real.py::test_resolver_sincroniza_eta_inversor_cuando_si_hay_dato_real` (el catálogo Excel real no trae `eficiencia_max` para ninguno de sus 105 modelos — el caso "sí hay dato real" ahora se prueba con un catálogo controlado vía `monkeypatch`, mismo patrón que el resto del archivo, no dependiendo de que el entorno local "accidentalmente" cayera al catálogo chico).

**Inversor ingresado al catálogo real** (`datos/inversores_catalogo.xlsx`, hoja `Catalogo_Inversores`): Woodward IDS SOLO 500, con los valores de la ficha verificados por el usuario (Vdc_max=1200 V, Vmppt_min=500 V, Vmppt_max=1100 V, V_mppt_activo=500 V — de "Voltaje mínimo para Pnom" —, P_dc_max_W=600.000 W). Insertado con `guardar_inversor_excel()` y verificado leyendo de vuelta con `cargar_catalogo_inversores()`. **`Datos completos (Si/No)` = "No" a propósito** — primer registro del catálogo marcado así (los 105 anteriores están completos) — porque V_arranque, N Trackers, N Strings/Tracker, Corriente Máxima/Cortocircuito por Tracker genuinamente no aplican/no se publican para este inversor central sin trackers discretos (ver hallazgo de arriba). La página 📐 Dimensionamiento ya tiene el mecanismo correcto para esto: al cargar un inversor con `datos_completos=False` muestra "🟡 Inversor incompleto — faltan: ..." listando exactamente los campos vacíos, en vez de fingir que está completo.

⚠️ **Imprecisión conocida, declarada, no resuelta**: el catálogo Excel no tiene columna "Potencia AC nominal (kW)" (otro campo que el loader referencia pero que no existe en el schema real — mismo tipo de gap que `CoefIsc_C` en paneles). Por eso `P_ac_nom_W` para este inversor queda **derivado** por el fallback `P_dc_max_W × 0.96` = 576.000 W, en vez del valor real de la ficha ("Potencia de CA nominal 500 kW" = 500.000 W) — una diferencia de 15%. No hay dónde escribir el dato real en el schema actual sin agregar una columna nueva (fuera de alcance de esta tarea).

## 13c. Catálogo de Baterías — carga robusta del Excel  ACTUALIZADO

El cargador del catálogo de baterías (hoja del Excel del servidor) se endureció para evitar errores silenciosos:

· Detección automática de la fila de encabezados: ya no importa si la hoja tiene títulos o filas vacías arriba de la tabla.

· Encabezados con saltos de línea ('Capacidad\n(kWh)') se normalizan automáticamente antes de mapear las columnas.

· Columnas faltantes: si una columna esperada no existe, la app la reporta con sugerencias de nombres compatibles, en lugar de cargar la batería con valores vacíos.

· Modelos duplicados (nuevo): si un mismo modelo aparece dos veces en el Excel (exacto o con espacios de más), solo la última fila sobreviviría y el resto se perdería en silencio. Ahora la app lista los duplicados con su número de fila en el Excel para que los corrijas.

· Valores por defecto seguros cuando un dato opcional falta, con aviso en pantalla.

────────────────────────────────────────────────────────────

## 13d. Página 14 — Catálogo de Paneles PDF: bifacialidad  NUEVO

Al subir la ficha técnica de un panel, el extractor ahora también detecta la bifacialidad (patrones como «Bifaciality 80 % ± 5 %», «Bifacial factor 0.85»). El campo «Bifacialidad (%)» aparece pre-llenado en el formulario y se guarda en el catálogo (columna BifacialidadPct).

Con ese dato guardado, la página 2 activa automáticamente la simulación bifacial al seleccionar el panel — sin ingresar nada a mano.

⚠️ IMPORTANTE: si el panel es monofacial (vidrio-backsheet), deja el campo vacío o en 0. Poner una bifacialidad inventada infla la producción estimada.

### Bug real corregido: falso "multi-modelo" en fichas con auto-verificación cruzada  NUEVO (28-ago-2026)

El usuario reportó que al subir una ficha de un **solo** panel (Suntech STP-410-A72-Pnh-Bifacial) el extractor mostraba «Ficha técnica multi-modelo — se detectan 2 modelos: 410.18Wp, 410Wp». Root-caused reproduciendo el texto real contra `calculos.pdf_panel_extractor._extract_multimodel_panel()` antes de tocar código: la ficha trae, en la MISMA línea del valor de Pmax, una nota de auto-verificación cruzada que re-cita el mismo valor redondeado — «Potencia máxima calculada (Vmpp × Impp) 410.18 W **✓ coincide con 410.0 Wp**». El heurístico de respaldo (cuando no hay tabla estructurada ni códigos de modelo detectables) toma TODOS los números de la línea que sigue a la etiqueta "Pmax" como si fueran columnas de modelos distintos — y la nota de verificación aporta un segundo número "plausible" que en realidad es el MISMO panel.

**Corregido** en `_extract_row_numbers()`: corta el segmento de línea en el primer carácter `✓` antes de buscar números, así la nota de verificación queda fuera del barrido. No afecta la detección multi-modelo legítima (varias columnas reales de potencia en la misma fila, sin ✓) — se agregó un caso de control para eso en el banco de regresión.

**El mismo bug también corrompía Isc, no solo Pmax** — descubierto en una segunda vuelta, con el PDF real que el usuario aportó después de guardar el panel manualmente y notar el semáforo en rojo ("Imp debe ser menor que Isc", con Isc=0.05 A e Imp=9.98 A). La MISMA línea de la ficha que causaba el falso multi-modelo en Pmax («Coeficiente de temperatura µIsc 5.2 mA/°C (+0.050 %/°C)») coincide también con el patrón de detección de Isc — el heurístico de respaldo extraía 5.2 y 0.050 como si fueran los valores de Isc (en A, no mA/°C) de las 2 columnas falsas: `valores_por_modelo = {'410.18Wp': {'Pmax': 410.18, 'Isc': 5.2}, '410Wp': {'Pmax': 410.0, 'Isc': 0.05}}`. Al elegir "410Wp" en el selector de la UI, el merge de la página (líneas ~120-124) sobrescribía el Isc YA correctamente extraído de la base (10.49 A) con ese 0.05 A falso. Verificado con el PDF real (no solo texto sintético) que el MISMO fix de `_extract_row_numbers()` resuelve todo el cascade (Pmax, Isc y cualquier otro campo variable), no solo Pmax — la corrección era genérica desde el principio, no hacía falta un segundo fix.

**Generalización pedida explícitamente por el usuario** ("revisa la lógica del extractor para que no confunda coeficientes de temperatura con valores absolutos... es un error que se puede repetir con cualquier otra ficha"): el fix del `✓` solo cubría ESTA ficha exacta. Se auditó primero el camino base de un solo valor (`_apply_patterns()`/`_find_first()`, el que usa CUALQUIER ficha) con casos adversariales — está bien protegido por diseño, exige que el número aparezca casi pegado a la etiqueta, sin poder saltar sobre texto como "temperature coefficient:". El riesgo real está solo en el heurístico multi-modelo, que toma "todos los números plausibles de la línea" de forma más laxa. Se agregó una segunda capa, independiente del `✓`: `_COEF_UNIT_AHEAD_RE` descarta cualquier número seguido de una unidad de coeficiente por grado (`/°C`, `/℃` — glifo único visto en fichas SolTech reales —, `/K`, con o sin unidad corta antepuesta: mA, mV, %). Verificado con un caso SIN checkmark (tabla multi-modelo real de 2 códigos, con una fila de coeficiente en `mA/°C` intercalada antes de la fila real de Isc) que la fila de coeficiente ya no le roba la asignación a la fila correcta.

**Limitación residual, declarada honestamente, no corregida**: el algoritmo de asignación por campo (`_extract_multimodel_panel`, Paso 2) toma la PRIMERA línea que matchea la etiqueta del campo Y tiene ≥2 números plausibles, y deja de buscar — no seguiría intentando si esa primera línea resultara ser la incorrecta por una razón distinta a un coeficiente de temperatura (p.ej. una nota con exactamente 2 números coincidentes que no sea ni `✓` ni un coeficiente por grado). El filtro de esta sesión cierra la clase de bug real que se reportó (coeficientes de temperatura y notas de auto-verificación); no es una garantía de robustez universal contra cualquier anotación futura no vista todavía.

Banco de regresión (`scripts/test_pdf_panel_extractor.py`, "Ficha 8"): caso sintético Suntech (0 modelos detectados) + caso e2e con el PDF real del usuario (`scripts/fixtures_fichas/panel_suntech_stp410_bifacial.pdf`: 0 modelos falsos, Pmax/Voc/Isc/Vmp/Imp los 5 correctos) + caso de coeficiente SIN `✓` en una tabla multi-modelo real de 2 códigos + caso de control multi-modelo real de 4 variantes (debe seguir detectando las 4). **85/85 checks propios del banco pasan** (2 fallos restantes, preexistentes y no relacionados: dependen de OCR — pytesseract/pdf2image — no instalado en este entorno de desarrollo). Nota aparte: `pdfplumber` (declarado en `requirements.txt`) faltaba en el venv local usado para verificar — se instaló para poder correr el banco completo; no es un cambio de código.

**Panel ingresado al catálogo real** (`datos/paneles_catalogo.xlsx`, hoja `Catalogo_Paneles_FV`): Suntech STP-410-A72-Pnh-Bifacial, con los valores de la ficha oficial (Pmax=410.0 Wp, Voc=48.90 V, Isc=10.490 A, Vmp=41.10 V, Imp=9.980 A, Ns=72, β Voc=-0.304 %/°C, γ Pmax=-0.37 %/°C, Bifacialidad=70%, dimensiones 2028×1002×35 mm). Insertado con `guardar_panel_excel()` (la función real de la app, no edición directa del Excel) y verificado leyendo de vuelta con `cargar_catalogo_paneles()`. **Hallazgo aparte, no corregido**: el schema del Excel no tiene columna para el coeficiente de temperatura de Isc (α Isc) — `guardar_panel_excel()` descarta ese campo en silencio para CUALQUIER panel guardado desde la UI de 📋 Catálogo de Paneles, no solo este. Se documentó el valor (+0.050 %/°C) en el campo `Notas` de este panel como respaldo, ya que no hay dónde más guardarlo hoy.

### 2 bugs reales más: tabla multi-modelo "por fila" no reconocida + falso positivo de marca "LG"  NUEVO (28-ago-2026, mismo día)

El usuario subió una ficha de familia (Solar First, serie ST1/ST2, 10 variantes: 8 transparentes + 2 opacas) y reportó, con el CSV de verificación de la UI adjunto, que el extractor no identificó NINGÚN parámetro (los 5 campos obligatorios en rojo). Pidió "el diagnóstico honesto" antes de continuar.

**Root-caused verificando con `_dump_tables_pdfplumber()` antes de tocar código**: pdfplumber parseaba la tabla PERFECTO (11 filas limpias: encabezado "Modelo | Transp. | Pmax | Voc | Vmpp | Isc | Impp | Dimensiones" + 10 filas de datos) — el problema no era la lectura del PDF, era que **ningún criterio existente reconocía esa tabla como multi-modelo**:

1. El detector de tablas multi-modelo (`_extract_multimodel_from_tables()`, Paso 1) exige códigos de modelo "largos" vía `_MODEL_CODE_RE` (≥3 caracteres tras el guion, pensado para nombres tipo "CS6R-400MS") — los códigos de esta ficha ("ST1-72", solo 2 caracteres tras el guion) no califican.
2. El heurístico de texto plano (`_extract_multimodel_panel()`) exige que la etiqueta "Pmax" y los valores estén en la MISMA línea — en esta ficha la etiqueta vive en la fila de encabezado, separada de los valores por N filas (estructura de tabla normal, no el problema que ese heurístico fue diseñado para cubrir).

Ambos criterios estaban diseñados para la orientación "modelos en columnas, campos en filas" (SolaX, Growatt, familias con 3-6 variantes en una tabla ancha) — esta ficha tiene la orientación TRANSPUESTA: modelos en filas, campos en columnas (tabla vertical clásica, más común cuantas más variantes tiene una familia — 10 en este caso).

**Corregido**: nueva función `_detectar_tabla_modelos_por_fila()` — detecta un encabezado cuya primera celda sea literalmente "Modelo"/"Model", mapea las columnas restantes a campos vía `_TABLE_LABEL_RE` (el mismo diccionario ya usado en otras partes del archivo), y lee cada fila siguiente como un modelo independiente hasta la primera fila vacía. Se prueba como fallback dentro de `_extract_multimodel_from_tables()` cuando la orientación "por columna" no encuentra nada. Se extendió además `_TABLE_LABEL_RE["Transparencia"]` para reconocer el encabezado abreviado "Transp." (antes solo "transparencia" completo).

**Segundo bug real, encontrado verificando el resultado completo, no solo Pmax**: la marca se detectó como **"LG"** — falso positivo. `_extract_brand()` buscaba cada marca de `BRANDS` como substring SIN límites de palabra (`re.search(re.escape(marca), texto)`), y la ficha dice "película delgada" (CdTe, thin-film) — "de**lg**ada" contiene literalmente "lg". Corregido agregando `\b...\b` a la búsqueda. Riesgo real, no solo teórico: `BRANDS` tiene otras marcas cortas (REC, NCL) con el mismo riesgo de substring dentro de palabras en español — el fix es general, no un parche solo para "LG". Se agregaron "Solar First", "Suntech" e "Hiitio" a `BRANDS` (marcas ya vistas en fichas reales de la sesión, ausentes de la lista).

Banco de regresión (`scripts/test_pdf_panel_extractor.py`, "Ficha 9"): caso unitario de `_detectar_tabla_modelos_por_fila()` con tabla sintética de 3 filas, caso del falso positivo "LG" + su control positivo ("Panel LG NeON" sí debe detectar LG), y caso e2e completo con el PDF real (`scripts/fixtures_fichas/panel_solarfirst_st1_st2.pdf`): 10 modelos, marca correcta, valores eléctricos de 2 variantes verificados exactos (incluida la variante opaca ST2-85, sin campo Transparencia — correcto, su celda dice "No (opaco)", no un número). **93/93 checks propios del banco pasan** (2 fallos preexistentes de entorno OCR, sin relación, documentados arriba). Suite pytest completa: **717/717 passed**.

### Los 10 paneles Solar First ingresados al catálogo real + un tercer bug real (`_f()` no manejaba NaN)  NUEVO (28-ago-2026, mismo día)

Con el extractor ya corregido, se ingresaron los 10 modelos de la serie (Solar First ST1-72/64/56/48/40/32/24/16, ST2-80/85) a `datos/paneles_catalogo.xlsx` con `guardar_panel_excel()`, siguiendo la ficha exacta (Pmax/Voc/Vmp/Isc/Imp por variante, dimensiones comunes 1200×600×6.8mm). **Coeficientes de temperatura y NOCT quedaron en blanco a propósito** — la ficha misma dice explícitamente en su sección 5 ("Recomendación para el Motor Óptico"): *"antes de cargar estos coeficientes de referencia al catálogo como si fueran datos oficiales del fabricante... si se usan los valores de referencia CdTe, marcarlos explícitamente... como valor estimado — no verificado"*. Como el schema del Excel no tiene un flag de confianza por campo, se optó por dejar los campos numéricos vacíos (honesto) y documentar la referencia típica CdTe (γ=-0.32, β=-0.28, α=+0.04 %/°C, **NO CONFIRMADO**) solo en `Notas`, siguiendo literalmente la recomendación de la propia ficha.

**Tercer bug real, encontrado verificando la simulación de los paneles recién insertados (no solo `validar_panel()`)**: `run_bipv_simulation()` reventaba con `ValueError: resultado_horario.P_dc_kW contiene valores no finitos` para los 10 paneles nuevos. Root-caused: `datos/catalogo_paneles_excel.py::_f()` no manejaba `NaN` — `float(val)` no lanza excepción para NaN, así que una celda genuinamente vacía en una columna numérica (que pandas lee como `NaN`, no `None`) pasaba de largo como `NaN` en vez de aplicar el `default`. El fix de esta mañana en `calculos/produccion.py` (`panel.get("Tk_gamma") or -0.45`) NO cubre este caso: `NaN` es *truthy* en Python, así que `nan or -0.45` da `nan`, no `-0.45`. Confirmado comparando: un panel arreglado esta mañana (`HW-MQSB-V2`) sí devolvía `None` limpio (su celda original era una cadena vacía, no una celda en blanco — casos distintos), mientras que los paneles recién insertados vía `guardar_panel_excel()` con campos `None` sí producían `NaN` al releerlos. **Corregido en la raíz**: `_f()` ahora valida `math.isfinite()`, exactamente el mismo patrón que YA usa correctamente `datos/catalogo_inversores_excel.py::_f()` — aplicado también aquí. Efecto colateral positivo: también corrige el aviso espurio "Bifacialidad nan%" que aparecía en `validar_panel()` para cualquier panel con esa celda vacía (no solo los nuevos).

Verificado tras el fix: los 10 paneles simulan sin `NaN`/`Inf` (`_calcular_pmax_vectorizado()` probado directamente), `validar_panel()` sin avisos espurios, suite pytest completa **717/717 passed**. Catálogo real: 66 → 76 paneles.

## 13e. Página 19 — 🔒 Ledger de Auditoría  NUEVO (25-ago-2026)

### Por qué existe esta página — el diferenciador real

Res. CREG 174 de 2021, Artículo 6, exige explícitamente que **"los cálculos tengan trazabilidad para determinar si son reales o actualizados"**. Hasta esta versión, la calculadora cumplía ese requisito de forma *declarativa* (campos de "Fuente de precios", banners de trazabilidad de E_ac, fecha de vigencia del presupuesto...), pero nada impedía correr Financiero dos veces con supuestos distintos y quedarte con la versión más favorable, sin que quedara ningún rastro de que existió una corrida anterior diferente.

**Con el Ledger de Auditoría, la calculadora deja de ser solo una herramienta de cálculo y pasa a cumplir ese artículo de forma *verificable*, no solo declarativa** — cada resultado oficial queda sellado con una cadena de hashes que cualquiera puede recorrer y confirmar matemáticamente que no fue alterado después de generarse. Esto es un diferenciador **concreto y citable frente a un banco o un ITA**, no una "buena práctica" genérica: hoy, ningún competidor de esta calculadora ofrece de forma verificable esa trazabilidad exigida por el Art. 6 de la Res. CREG 174/2021. Puedes citar textualmente este artículo al presentar un proyecto ante un banco como respaldo normativo de por qué tu presupuesto trae un Ledger sellado y el de la competencia no.

### Qué es un "eslabón" y cómo funciona la cadena de hashes

Cada vez que sellas un resultado, la app crea un **eslabón**: un registro que contiene los insumos (panel, inversor, degradación, tarifa, TRM, CAPEX y su fuente), los resultados (E_ac, PR, TIR, VPN, LCOE, Payback, o las métricas de un diagnóstico), la fecha, el usuario que lo selló, una nota opcional, y dos hashes SHA-256: el de este mismo eslabón (`hash_propio`) y el del eslabón **anterior** de ese mismo proyecto (`hash_anterior`).

Esa referencia al hash anterior es lo que forma la "cadena": el hash de cada eslabón se calcula incluyendo el hash del que vino antes, así que **alterar cualquier campo de un eslabón ya guardado — incluso un solo carácter de la nota — cambia su hash, y ese cambio se propaga y rompe la cadena de todos los eslabones que le siguen.** No hace falta un sistema externo para detectarlo: basta con recorrer la cadena y recalcular cada hash para ver si sigue coincidiendo con el guardado.

En términos auditables, esto significa concretamente:

- **Detecta alteración retroactiva**: si alguien edita un registro directamente en el archivo del servidor (sin pasar por la app), su hash deja de coincidir con el que usó el siguiente eslabón como referencia — la ruptura es matemáticamente evidente, sin necesitar comparar contra un backup externo.
- **Prueba de secuencia honesta**: un banco o ITA puede revisar el HISTORIAL completo de corridas de un proyecto, no solo el resultado final. Si el TIR subió de 11% a 14% entre dos sellos, el Ledger muestra exactamente qué insumo cambió y cuándo — no un número final que "apareció así".
- **Límite honesto (no se oculta)**: el hash-chain protege contra editar UN eslabón sin que se note. No evita que alguien borre el archivo completo del ledger y empiece de cero — eso requeriría un ancla externa (por ejemplo, publicar el hash raíz en otro sistema independiente), decidido explícitamente FUERA de alcance por ahora para no perder el principio de "todo local, sin depender de servicios externos".

### Los 5 tipos de resultado que se pueden sellar  ACTUALIZADO (27-ago-2026 — se agregó Ficha de Validación RETIE)

El Ledger no es solo para bancabilidad — cubre 5 escenarios reales, cada uno con su propia etiqueta dentro del eslabón:

Tipo  │  Cuándo se usa  │  Dónde se sella

🏦 Presupuesto bancable  │  El resultado va a un banco o a un Auditor Técnico Independiente (ITA) para financiamiento  │  Checkbox en 📄 Reporte PDF, o manual en esta página

📋 Verificación presupuestal informativa  │  Le entregas un resultado a un cliente SIN fines de financiamiento — igual queda protegido: si en 6 meses el cliente dice "usted me había dicho que esto rendía X", tienes la prueba exacta de qué le mostraste y con qué insumos  │  Checkbox en 📄 Reporte PDF, o manual en esta página

🔍 Diagnóstico de sistema en operación  │  Diagnosticas un sistema YA instalado (🔍 Página 13 — Diagnóstico) — protege la conclusión de un diagnóstico puntual, útil ante una reclamación de garantía al instalador o fabricante  │  Botón "🔒 Sellar en el Ledger de Auditoría" en la propia página 13, independiente del botón de histórico de tendencia que ya existía ahí

⚡ Diagrama unifilar (diseño eléctrico)  │  Congelas la configuración eléctrica exacta (generador, inversor(es), batería, superficies, protecciones) que le entregaste al cliente o al instalador como diagrama unifilar — protege contra "eso no fue lo que usted diseñó" si el diseño cambia después  │  Botón "🔒 Sellar en el Ledger de Auditoría" en ⚡ Página 20 — Diagrama Unifilar, único tipo ofrecido ahí (no un selector, a diferencia de Reporte PDF que sí ofrece varios)

📋 Ficha de validación RETIE (dashboard + checklist)  │  Congelas el dashboard ejecutivo y el checklist de validaciones (Voc frío, ventana MPPT, balance de inversores, breaker) que le mostraste al cliente o al revisor — protege contra "el sistema no marcaba ese error/pendiente cuando me lo entregó"  │  Botón "🔒 Sellar en el Ledger de Auditoría" en 📋 Página 21 — Ficha de Validación RETIE, único tipo ofrecido ahí

### Por qué el sellado es siempre manual, nunca automático

El Ledger NO registra cada cálculo de prueba mientras ajustas un slider — eso llenaría la cadena de ruido y le restaría valor a lo que sí es un resultado oficial. Se sella únicamente cuando presionas un botón explícito ("🔒 Sellar" en esta página, en Diagnóstico, o el checkbox al generar el Reporte PDF). Esto significa que la disciplina de cuándo sellar es tuya: sella cuando el resultado sea el que realmente vas a entregar o defender, no cada intento.

### Qué puedes hacer en esta página

- **🔒 Sellar el resultado actual**: toma un snapshot de los insumos y resultados vigentes en la sesión (panel, inversor, degradación, tarifa, CAPEX, E_ac, PR, TIR, VPN, LCOE) y lo sella como un eslabón nuevo — útil para una verificación presupuestal informativa que no pasa por el Reporte PDF.
- **✅ Verificar integridad de la cadena**: recorre TODOS los eslabones del proyecto recalculando cada hash. Muestra 🟢 "cadena íntegra" o 🔴 "cadena rota en el eslabón #N" si detecta cualquier alteración — corre esto antes de entregar el historial como evidencia a un banco.
- **📜 Historial completo**: tabla con fecha, tipo, usuario y nota de cada eslabón, más el detalle completo (insumos y resultados congelados, y ambos hashes) de cualquiera que selecciones.
- **📤 Exportar para banco/ITA**: descarga el historial completo en JSON o Markdown, para entregárselo a un tercero sin darle acceso directo al servidor de la calculadora.

⚠️ Para no cometer errores: el Ledger es por proyecto Y por cuenta — dos usuarios distintos con un proyecto del mismo nombre tienen cadenas completamente separadas, igual que el resto de los datos privados por cuenta de esta app.

## 13f. Página 20 — ⚡ Diagrama Unifilar  ACTUALIZADO (27-ago-2026 — plan de 4 fases completo)

Generador universal de diagrama unifilar (esquema eléctrico simplificado en una línea) — sirve para cualquier proyecto FV o BIPV, no está atado a un caso particular. Auto-llena módulo, número de paneles, N en serie, inversor y unidades desde lo que ya configuraste en 📐 Dimensionamiento / ⚖️ Comparador de Inversores, batería desde 🔋 Baterías y Balance, y superficies desde 🗺️ Vista 3D (Página 9) si hay multi-superficie activa; lo que no esté disponible se completa a mano.

Si el número de módulos no es múltiplo de los módulos en serie, la página avisa de string incompleto antes de generar el diagrama. La protección AC se estima automáticamente (NEC, factor de seguridad 1,25) si no se ingresa a mano.

Exporta PNG, SVG (editable) y PDF.

### 🔋 Batería (Fase 2, 27-ago-2026)

El checkbox "Incluir batería en el diagrama" se preselecciona solo si ya hay una batería configurada en 🔋 Baterías y Balance (`bateria_ok`). En esta app la batería se conecta al **mismo inversor híbrido** que el generador FV — la compatibilidad se verifica por rango de voltaje en `calculos/compatibilidad_bateria.py`, no hay un inversor separado para la batería. Por eso el diagrama la dibuja como una segunda entrada DC que se une al bus del generador justo antes del inversor (con su propia protección), en vez de un circuito aparte. Si el inversor configurado no tiene "híbrido" en el nombre, la etiqueta del inversor en el diagrama agrega "Híbrido" automáticamente cuando hay batería activa, para dejar explícito ese requisito.

### 🗺️ Multi-superficie (Fase 3, 27-ago-2026)

El checkbox "Incluir varias superficies" se preselecciona si `multisup_activo` está activo (Página 9). Con 2 o más superficies, cada una se dibuja como su propio bloque generador con su propia protección DC, todas convergiendo en un **bus horizontal común** antes de la protección DC compartida y el inversor — no como ramas que se repiten literalmente el resto del circuito, sino como fuentes que confluyen. `multisup_desglose` (Página 9) trae nombre/tipo/área por superficie pero NO número de módulos (esa página trabaja con áreas y POA, no con conteo de paneles) — la página pide el número de módulos por superficie a mano, con nombre/área ya auto-llenados como contexto. Si no hay multi-superficie detectada, se puede definir manualmente con una superficie por línea (`nombre, número de módulos`).

Con menos de 2 superficies con módulos ingresados, el diagrama cae automáticamente al generador único (Fase 1/2) — sin romper ni mostrar una rama vacía.

### 🔒 Sellado en el Ledger (Fase 4, 27-ago-2026)

Botón "🔒 Sellar en el Ledger de Auditoría" al final de la página — mismo patrón que 🔍 Diagnóstico: un botón dedicado con un solo tipo (`diagrama_unifilar`, ver sección 13e), no un selector de varios tipos como en 📄 Reporte PDF. Congela el diseño eléctrico completo (generador, inversor(es), batería, superficies, protecciones) que se muestra en pantalla, con un hash encadenado al eslabón anterior del proyecto — protege contra "eso no fue lo que usted diseñó" si el layout cambia después de entregado. Con esto se completa el plan original de 4 fases del Diagrama Unifilar (MVP → batería → multi-superficie → sellado).

### Auditoría posterior a las 4 fases (27-ago-2026) — 3 correcciones reales

Tras completar el plan de 4 fases, se auditó el sistema completo probando escenarios más allá de los casos de prueba originales (nombres de proyecto/superficie realistas, superficies con nombres duplicados). Se encontraron y corrigieron 3 problemas reales, no cosméticos:

1. **Nombres de descarga sin sanitizar**: el nombre de archivo de las descargas (PNG/SVG/PDF) solo reemplazaba espacios — un nombre de proyecto con `/`, `:`, `*`, etc. (caracteres inválidos en nombres de archivo de Windows) pasaba sin filtrar. Corregido con un sanitizador que preserva letras/números/acentos/ñ y reemplaza el resto por `_`.
2. **`DuplicateWidgetID` con superficies del mismo nombre**: el campo de "número de módulos" por superficie usaba el nombre de la superficie como key del widget — si el usuario nombró dos superficies igual en 🗺️ Vista 3D (no hay validación de unicidad ahí), la página completa reventaba. Corregido agregando el índice a la key.
3. **Etiquetas de superficies vecinas se solapaban con nombres largos**: el espaciado horizontal entre bloques de superficie era un número fijo, calibrado (sin darse cuenta) solo con nombres de prueba cortos ("Sup0"). Con nombres reales como "Marquesina Estacionamiento" (26 caracteres) las etiquetas de dos superficies vecinas se solapaban visualmente. Corregido calibrando el ancho real del texto en `schemdraw` y escalando el espaciado según el nombre más largo presente.

Los 3 casos ya tienen test de regresión. Lección para las próximas fases (Fase 3 de multi-superficie ya cerrada, pero aplica a cualquier extensión futura de esta página): probar con datos de prueba REALISTAS (nombres largos, duplicados, casos límite), no solo con los datos cortos que son cómodos de escribir a mano en un test.

### Detalle RETIE (27-ago-2026)

El usuario aportó un script Python aparte (SVG crudo, sin schemdraw, codificado a mano para el proyecto Urabá con 2 inversores fijos) con anotaciones típicas de una revisión RETIE. Se decidió **no adoptar ese motor de dibujo** — habría duplicado arquitectura y descartado la geometría de batería/multi-superficie ya probada — y en cambio se **extrajo su contenido** como campos opcionales sobre el sistema universal existente:

- `equipotencialidad` (bool): agrega una línea al bloque generador ("Equipotencialidad: estructura y marcos → PE").
- `detalle_proteccion_dc` / `detalle_proteccion_ac` (listas de texto libre): ítems de protección (fusibles gPV, seccionador DC, DPS, cable solar, interruptor AC, etc.) que el usuario elige de una lista sugerida (multiselect) en la página, o cualquier texto propio.
- `notas_retie` / `pendientes_retie` (listas de texto libre): NO se dibujan dentro del esquema — se muestran como listas debajo de la imagen en la página (`st.markdown`), igual que el resto del contenido de documento de esta app.
- Etiqueta del punto de conexión ahora dice "Red / Punto de Conexión Común — PCC" (antes "Red / Punto de conexión"), siempre, con o sin detalle RETIE.

Todos los campos son opcionales y por defecto inactivos — un proyecto que no los usa produce exactamente el mismo diagrama que antes (verificado renderizando ambos casos lado a lado, no solo con `isinstance(d, Drawing)`).

**3 bugs reales encontrados renderizando de verdad** (no solo corriendo tests, que no detectan overlaps visuales):
1. El símbolo `⏚` (earth ground, U+23DA) para equipotencialidad no existe en la fuente por defecto de matplotlib (DejaVu Sans) — se veía como un cuadro vacío. Corregido: texto plano sin símbolo.
2. Primer intento: agregar el detalle como líneas extra dentro de la MISMA etiqueta del Fuse/Breaker (`.label(texto, loc="right")`). Con una etiqueta corta de 1 línea eso ya funcionaba bien (caso base, sin cambios), pero con 2-4 líneas de detalle schemdraw centraba el bloque sobre el propio símbolo en vez de desplazarlo — el texto quedaba encima del fusible/breaker. Intentar arreglarlo con `halign="left"` + `ofst` no dio un desplazamiento horizontal predecible (probado con varios valores) y además rompía el caso base al aplicarse siempre.
3. Fix final: el detalle se dibuja como un `elm.Label()` **aparte**, con coordenadas explícitas (mismo criterio que `_caja`/`_gap` desde Fase 2) a la derecha del símbolo, separado de la etiqueta corta del Fuse/Breaker (que queda intacta, sin cambios respecto al caso base). El gap que sigue a la protección se agranda solo cuando hay detalle (`_holgura_por_detalle`, ~0,32 unidades por ítem) para que el bloque no invada la caja siguiente.

**Hallazgo aparte, NO corregido en esta sesión** (fuera de alcance de esta tarea): al renderizar el caso combinado multi-superficie + batería + inversor con nombre largo ("Huawei SUN2000-50KTL Hibrido"), la etiqueta del inversor se solapa visualmente con "Protección Bat." — confirmado que este bug **ya existía antes** de este cambio (aparece igual sin ningún dato RETIE), es de la geometría de la rama de batería (Fase 2) con nombres de inversor largos, no algo introducido por el detalle RETIE. Pendiente de una futura sesión si el usuario lo prioriza.

⚠️ Para no cometer errores: **no es un documento certificado**. Es un borrador técnico auto-poblado — el diagrama unifilar para trámite RETIE formal requiere firma de un ingeniero electricista matriculado. La página lo advierte explícitamente arriba del todo. Con más de 1 inversor, se muestran como un solo bloque con multiplicador ("2 × Growatt...") en vez de ramas paralelas dibujadas — simplificación deliberada, no un error. Multi-superficie asume que todas las superficies alimentan el/los mismo(s) inversor(es) — no modela strings de distinta orientación compartiendo un mismo MPPT (eso ya lo resuelve Página 9, sección 6, como cálculo aparte).

## 13g. Página 21 — 📋 Ficha de Validación RETIE  NUEVO (27-ago-2026)

Segundo aporte del usuario en la misma sesión: un script aparte con dataclasses `frozen` fijas al proyecto Urabá (2 inversores exactos), motor SVG propio sin dependencias, y un TIPO de documento que la app no tenía todavía: no un esquema eléctrico de línea única (eso es ⚡ Diagrama Unifilar, Página 20), sino una **ficha ejecutiva de una sola página** — tarjetas KPI, un flujo simplificado de 5 bloques, una tabla de cargas/protecciones, y sobre todo un **motor de validación eléctrica** que antes no existía en la app: Voc del string en frío vs Vdc máxima del inversor, ventana MPPT, balance DC/AC entre inversores, selección de breaker por calibre comercial, y banderas OK/PENDIENTE/ERROR cuando falta un dato de ficha técnica (nunca inventa el valor).

Presentadas 3 opciones al usuario (página nueva + motor reutilizable / solo motor sin página / no integrar), eligió la primera. El usuario también alertó explícitamente a mitad de la construcción: *"que no quede unicamente harcodeado al proyecto de uraba, verifica que sea universal e iterativo para multiples proyecto FV y BIPV"* — antes de seguir, se generalizó `strings_por_inversor` de 2 campos fijos (`strings_inversor_1`/`strings_inversor_2`) a una **lista de N elementos**, y se verificó ejecutando (no solo leyendo) 2 proyectos completamente distintos a Urabá: una fachada BIPV residencial de 1 solo inversor y una planta comercial de 3 inversores, ambos renderizados y revisados visualmente en el navegador antes de dar por buena la generalización.

`calculos/ficha_validacion_retie.py`, mismo patrón de 3 capas que `diagrama_unifilar.py`: `construir_config_retie()` (datos) → `calcular_retie()`/`validar_retie()` (cálculos y checklist puros) → `generar_ficha_svg()` (dibujo, motor SVG propio sin schemdraw ni dependencias nuevas — no hace falta para una ficha de tarjetas/tabla). Reutiliza `calcular_voc_string()`/`calcular_vmp_string()` de `calculos/dimensionamiento.py` en vez de reimplementar la fórmula (ese módulo ya documenta un bug real de confundir el coeficiente de Voc con el de potencia en este mismo cálculo — reusar la función evita repetirlo). Auto-llena Voc/Vmp/Isc/coeficiente de temperatura del panel y Vdc máx/ventana MPPT del inversor desde los mismos campos que ya usa ⚖️ Comparador de Inversores (`Voc_stc`, `Vmp_stc`, `Isc_stc`, `Tk_beta`, `Vdc_max`, `Vmppt_min`, `Vmppt_max`) — no son campos nuevos inventados para esta página.

`pages/21_📋_Ficha_Validacion_RETIE.py`: auto-llena proyecto/panel/inversor igual que Página 20; pide la distribución de strings por inversor como texto libre separado por comas (ej. `9,8` o `15,15,15`) — opcional, sin eso el balance entre inversores queda sin calcular en vez de asumir una repartición pareja. Exporta SVG siempre (sin dependencias); PNG solo si el servidor tiene CairoSVG instalado (dependencia OPCIONAL, **no** agregada a `requirements.txt` — si falta, la página lo dice y ofrece igual el SVG en vez de fallar). Sellado en el Ledger con tipo propio `ficha_validacion_retie` (ver TIPOS_VALIDOS en `calculos/ledger_auditoria.py`, ahora 5 tipos).

Verificado end-to-end: 696/696 tests (23 nuevos: 14 en `test_ficha_validacion_retie.py`, 2 en `test_ledger_auditoria.py`, 7 en `test_pagina_ficha_validacion_retie.py`), servidor Streamlit local levantado y la página confirmada respondiendo 200 con el título correcto (sin traceback) antes de dar la tarea por terminada.

### Auditoría de la muestra entregada (27-ago-2026) — 2 bugs reales corregidos

El usuario pidió auditar la imagen de muestra ya entregada. Se encontraron y corrigieron 2 bugs reales:

1. **Título incorrecto dentro del SVG**: decía literalmente "DIAGRAMA UNIFILAR FOTOVOLTAICO" (heredado sin cambiar del script original del usuario) aunque este documento NO es el esquema de línea única (eso es Página 20) — confundía cuál documento era cuál si se archivaban los dos juntos para el mismo proyecto. Corregido a "FICHA DE VALIDACIÓN RETIE".
2. **Doble redondeo en la corriente de diseño**: `corriente_diseno_total_a` se calculaba multiplicando el factor de continuidad (1,25) por `corriente_total_a` YA REDONDEADA a 1 decimal, en vez de por el valor crudo. Para el proyecto Urabá esto daba **360,9 A**, un número DISTINTO al que muestra Página 20 (`diagrama_unifilar.py`) para el mismo proyecto físico: **360,8 A** (redondeado directo, sin redondeo intermedio). Verificado ejecutando ambas rutas de cálculo antes de corregir. Corregido guardando primero el valor crudo (`i_total_crudo`) y derivando de ahí tanto la cifra a mostrar como la corriente de diseño y el breaker por inversor (mismo tipo de doble redondeo también afectaba a `breaker_inversor_a`, corregido igual aunque sin un documento externo con el que comparar). 2 tests de regresión nuevos (698/698 en la suite completa).

⚠️ Para no cometer errores: mismo criterio que Página 20 — **no es un documento constructivo**, no sustituye memorias de cálculo, estudio de cortocircuito, coordinación de protecciones, declaración de cumplimiento, inspección ni firma de ingeniero electricista matriculado. Es un tipo de documento DISTINTO al diagrama unifilar (dashboard + checklist, no un esquema de símbolos eléctricos) — no reemplaza a Página 20, la complementa.

## 14. Calculadora de Sombreado 3D

URL: bipv.innovacionquimica.com.co

Propósito: Generar el CSV de Factor de Sombreado para usar en Página 5 de la calculadora BIPV.

### Pasos en la Calculadora de Sombreado 3D

- Cargar el archivo EPW del proyecto (el mismo que en Página 2)
- Dibujar los obstáculos en el mapa 3D:
- Edificios vecinos (altura, distancia, ancho)

- Voladizos, antenas, tanques

- Configurar los puntos de análisis:
- Ubicar puntos sobre la fachada fotovoltaica

- Asignar nombre de fachada (campo "Fachada")

- Seleccionar días críticos:
- Mínimo recomendado: solsticios (21 jun, 21 dic) + equinoccios (21 mar, 21 sep)

- Para mayor precisión: un día representativo por mes (12 días)

- Cruzar máscara de sombras con el EPW:
- Botón "Cruzar Máscara + EPW"

- Genera: FS_geometrico (obstáculos), FS_climatico (nubes), FS_combinado

- Exportar CSV:
- Botón "Exportar CSV"

- El CSV incluye columnas: Hora, Mes, Dia, FS_geometrico, FS_climatico, FS_combinado, Fachada ← columna nueva

### Convención del CSV exportado

Valor FS  │  Significado

0.00  │  Sin sombra en esa hora

0.50  │  50% de la fachada sombreada

1.00  │  Sombra total (100%)

Esta es la convención p_shade: 0 = libre, 1 = sombreado.

Es la convención correcta para cargar en Página 5.

────────────────────────────────────────────────────────────

## 15. Cadena completa — bypass y multi-superficie

### Flujo A — Superficie única con bypass diodes

bipv.innovacionquimica.com.co (Calculadora Sombreado 3D)
  └── Exportar CSV (con columna Fachada)
           │
           ↓
Página 5 — Mismatch
  ├── Cargar CSV · Detectar FS_geometrico / invertido / multi-fachada
  ├── [Si multi-fachada] → Seleccionar fachada del array
  ├── Cobertura temporal: Modo mensual (recomendado) o exacto
  ├── Configurar strings (N_series, N_parallel)
  └── ⚡ Calcular → kWh_bypass_anual, pct_bypass, horas_bypass
           │
           ↓
Página 6 — Producción
  └── Guarda: E_ac_anual_kWh_bypass ← usada aguas abajo
           │
    ┌──────┼──────┬──────────┐
    ↓      ↓      ↓          ↓
Pág.7   Pág.11  Pág.12     Pág.10
Financ. Baterías CO₂        PDF
TIR/VPN  Balance  Emisiones  §4c bypass
                             §5 E_ac label

### Flujo B — Multi-superficie (Página 9)

Página 9 — Vista 3D
  ├── ⚙️ Superficies BIPV: crear fachada, techo, pérgola, marquesina
  ├── ☀️ Calcular POA para cada superficie
  ├── [Opcional] Cargar CSV → FS por fachada en sub-tab FS
  ├── [Opcional] ⚡ Bypass por superficie (Sección 5)
  │      Para cada superficie:
  │        · POA propia × FS propio del CSV (filtrado por Fachada)
  │        · N_parallel = área / área_panel / N_series
  │        · simular_bypass_horario() → pérdida% por superficie
  │        · E_ac_bypass_i = E_ac_base_i × (1 - pérdida%)
  └── 🔗 Integrar al Financiero
       Escribe claves exclusivas (nunca sobreescriben las de Pág. 1):
         E_ac_anual_kWh_multisup ← suma E_ac por superficie
         poa_df_multisup         ← POA combinada ponderada
         area_total_multisup     ← suma de áreas
         multisup_desglose       ← lista por superficie
         multisup_activo = True
           │
    ┌──────┼──────┬──────────┐
    ↓      ↓      ↓          ↓
Pág.7   Pág.11  Pág.12     Pág.10
Financ. Baterías CO₂        PDF §4d
★ prioridad máxima en todas     multi-sup

### Prioridad global de E_ac

Página 7 / 11 / 12 / 10 leen:
  1. E_ac_anual_kWh_multisup  ← Página 9 integrada  ★ MÁX
  2. E_ac_anual_kWh_bypass    ← Página 5 ejecutada
  3. E_ac_anual_kWh           ← Página 6 base

────────────────────────────────────────────────────────────

## 16. Interpretación de resultados clave

### Performance Ratio (PR)

PR = Y_f / Y_r = (E_ac / P_STC) / (H_POA / G_STC)

- PR > 100%: Posible en Bogotá/Medellín (altitud, temperatura baja) — físicamente correcto
- PR 80–100%: Rango normal para fachadas BIPV bien diseñadas
- PR 60–80%: Revisar pérdidas ópticas, mismatch o sombreado
- PR < 60%: Problema real — inspección de campo recomendada
### E_ac según escenario del proyecto

Escenario  │  E_ac usada  │  Para qué

Superficie única, sin sombras significativas  │  E_ac base  │  Proyectos con obstrucción < 5%

Superficie única, con sombras urbanas  │  E_ac_bypass  │  Fachadas en centros urbanos

Multi-superficie (techo + fachada + pérgola)  │  E_ac_multisup  │  Proyectos con orientaciones mixtas

Multi-superficie + bypass por superficie  │  E_ac_multisup (corregida)  │  Máxima precisión — BIPV urbano complejo

Certificación UPME / bancos  │  E_ac más conservadora disponible  │  Exigencia de estimación realista

### Horas con bypass activo

- < 200 h/año: Sombra estacional leve (ej. solo invierno solar)
- 200–500 h/año: Sombra moderada — bypass tiene impacto real
- > 500 h/año: Sombra severa — reconsiderar el layout del array
────────────────────────────────────────────────────────────

## 17. Preguntas frecuentes

P: ¿El CSV de la Calculadora de Sombreado cubre las 8 760 horas del año?

R: No. El CSV cubre solo los días críticos (~60–150 horas). El modo "mensual" replica

el patrón de cada día a todo el mes (cobertura ~25–40%). Para máxima precisión,

incluye un día representativo por cada mes (12 días en total), de modo que cada mes

tenga su propio perfil de sombra real.

P: ¿Por qué mi TIR es diferente antes y después de ejecutar bypass?

R: Con bypass activo, la Página 7 usa E_ac_bypass (menor que E_ac base). Menos

energía generada = menos ahorro = TIR levemente menor. La diferencia es proporcional

al % de pérdida bypass. Para proyectos con < 2% de pérdida, el impacto en TIR

es < 0.3 puntos porcentuales.

P: El banner de "FS invertido" apareció. ¿Qué hago?

R: Si el CSV viene de la Calculadora de Sombreado 3D de esta suite, NO está invertido

— el banner puede ser un falso positivo si el FS promedio real es muy alto (fachada

muy poco sombreada). Si el CSV viene de otra herramienta, activa el checkbox

"Invertir FS (1 − FS)" y verifica que la gráfica mensual tenga sentido.

P: ¿Por qué hay meses sin dato de bypass?

R: Si el CSV no tiene ningún día crítico de ese mes, la app asume FS=0 en todo el mes.

Solución: en la Calculadora de Sombreado, agrega al menos un día representativo

de los meses faltantes antes de exportar el CSV.

P: ¿El PR puede ser mayor de 100%?

R: Sí. En ciudades de alta altitud como Bogotá (2 600 m) o Medellín (1 500 m), la

temperatura ambiente baja hace que los módulos operen por debajo de 25°C muchas horas,

ganando eficiencia. Esto es físicamente correcto según IEC 61724.

P: ¿Qué es el modo "Motor Óptico vs sin Motor Óptico"?

R: El Motor Óptico aplica correcciones de IAM (reflexión angular), soiling (suciedad)

y temperatura confinada BIPV. Sin él, la app usa la POA bruta × factor de mismatch

global. El Motor Óptico da resultados más precisos para fachadas BIPV (diferencia

típica: 5–12% en la producción final).

P: Cambié el tipo de instalación a "Granja FV" pero el tilt sigue en 90°. ¿Por qué?

R: El tilt se resetea al valor del nuevo tipo solo si aún no has ajustado manualmente

el slider en Página 2 en esta sesión. Si ya lo moviste antes del cambio de tipo, la

app respeta tu selección manual para no sobreescribir trabajo hecho. Solución: ve a

Página 2 y ajusta el slider manualmente al valor deseado (15° para Granja FV).

P: Aparece la alerta de densidad fuera de rango pero estoy seguro de que mi valor es correcto. ¿Puedo continuar?

R: Sí, la alerta es informativa y no bloquea ningún cálculo. En instalaciones especiales

(fachadas con módulos de alta densidad > 200 W/m² o pérgolas de baja densidad < 60 W/m²)

los rangos pueden diferir de los típicos. La alerta te pide verificar — si el valor

es intencional, simplemente ignórala y continúa.

P: ¿Qué pasa si selecciono "Fachada BIPV" pero mi edificio tiene la fachada inclinada a 75°?

R: El tilt pre-cargado es 90° (fachada vertical estándar), pero puedes moverlo a 75°

libremente en Página 2. El slider acepta cualquier valor entre 0° y 90°. La app

calculará la POA correctamente para el ángulo que ingreses, independientemente del

tipo de instalación seleccionado.

P: ¿La alerta de PR considera las pérdidas del Motor Óptico?

R: No. La alerta de PR en Página 1 compara tu entrada con el rango típico global del

tipo de instalación, que ya incorpora las pérdidas ópticas promedio (IAM, soiling,

temperatura confinada). El PR que ingresas en Página 1 es el PR total del sistema

(incluyendo todas las pérdidas). Si ejecutas el Motor Óptico en Página 5b, las

correcciones ópticas se aplican sobre la POA y el PR resultante se recalcula en

Página 6 con mayor precisión.

P: ¿Cómo funciona la Página 9 (Vista 3D) con un proyecto de una sola superficie?

R: Para proyectos de una sola superficie (ej. solo fachada sur), la Página 9 no es

necesaria. El flujo normal (Páginas 1→2→4→5→6→7) es suficiente. La Página 9 agrega

valor cuando hay 2 o más superficies con distintas orientaciones que deben combinarse

en un solo sistema.

P: Si activo multi-superficie en Página 9, ¿se pierden los resultados de la Página 6?

R: No. Las claves de multi-superficie (E_ac_anual_kWh_multisup, poa_df_multisup)

son exclusivas y nunca sobreescriben E_ac_anual_kWh ni poa_df. Al desactivar

el modo multi-superficie con el botón "Desactivar", Financiero vuelve a usar la E_ac

de Página 6 automáticamente.

P: ¿Cómo calcula el N_parallel para cada superficie en el bypass por superficie?

R: La app divide el número estimado de módulos de cada superficie

(N_panels = área_m² / área_panel) por el N_series configurado:

N_parallel = max(1, round(N_panels / N_series)). El N_series es el mismo

para todas las superficies (se asume un único tipo de string); el N_parallel

varía proporcionalmente al área de cada superficie.

P: Tengo datos de PR de 3 años. ¿Por qué la degradación calculada es negativa (mejora)?

R: Una pendiente positiva (PR creciente) puede reflejar mejora real en limpieza o

mantenimiento entre años, no que los módulos "mejoren". Si ves PR_corr_T subiendo,

revisa si cambió el protocolo de limpieza. La app indica "PR estable o en mejora" y

no actualiza la tasa de degradación en Financiero si la pendiente es positiva.

P: ¿Puedo usar el bypass por superficie si el CSV no tiene columna "Fachada"?

R: Sí. Si el CSV no tiene columna Fachada, la app usa el promedio de todos los

puntos del CSV como FS para cada superficie. Esto es menos preciso que tener una

columna Fachada, pero es funcional. Para mayor precisión, asigna un nombre de

fachada a cada punto de análisis en la Calculadora de Sombreado 3D antes de exportar.

────────────────────────────────────────────────────────────

P: Subí un PDF de inversor y varios campos quedaron en cero. ¿Qué hago?

R: Revisa el banner de estado. Si dice 📷 escaneado sin OCR, la ficha es una imagen y debes completar el formulario manualmente (o pedir que instalen Tesseract en el servidor). Si el PDF es digital y aun así faltan campos, la app lo advierte explícitamente: es un formato de fabricante nuevo — completa a mano los campos faltantes y repórtalo para que se agregue soporte.

P: La tabla del PDF trae 3 modelos (10K/12K/14K). ¿Cuál se guarda?

R: Los tres. La app separa cada columna en un modelo independiente con sus propios valores de potencia y corrientes por tracker. Elige en el selector cuál revisar y guarda cada uno por separado en el catálogo.

P: Apareció una alerta roja 'τ sin efecto real' en el Motor Óptico. ¿Bloquea el cálculo?

R: No bloquea nada, pero no la ignores: significa que el Pmax/Isc de la ficha del panel parecen no descontar la transparencia (la eficiencia implícita del área activa supera el máximo físico de la tecnología). Si simulas así, la producción quedará sobreestimada. Corrige la ficha del panel en el catálogo (usa los valores del panel semitransparente real) o verifica el área y la τ declaradas.

P: ¿Por qué el slider de transparencia τ ya no cambia la energía producida?

R: Porque la reducción por transparencia ya viene incluida en el Isc_stc del panel del catálogo (el fabricante lo mide con el vidrio instalado). Si el slider también la restara, se contaría dos veces. El slider es informativo: muestra cuánta luz llega a la celda, pero la energía se calcula con los parámetros eléctricos reales del panel.

P: La app dice que hay modelos de batería duplicados en el Excel. ¿Es grave?

R: Sí, conviene corregirlo: cuando un modelo se repite, solo la última fila del Excel se carga y las demás se pierden sin aviso. La alerta indica el nombre y las filas exactas del Excel donde está el duplicado — elimina o renombra las filas sobrantes y recarga el catálogo.

────────────────────────────────────────────────────────────

## 18. Anexo — Actualizaciones del 6 y 7 de agosto de 2026

Esta entrega convierte la calculadora en una aplicación multiusuario: cada persona entra con su cuenta, guarda varios proyectos privados y no pierde el trabajo al cerrar la pestaña. Además se suma el Asistente 🧭 que guía el flujo paso a paso, un tab de análisis solar en la Vista 3D para elegir la mejor orientación, y mejoras de robustez en catálogos, presupuesto, financiero y reporte PDF.

────────────────────────────────────────────────────────────

18.1 Acceso con cuenta: login, planes y panel de administración  NUEVO

La app ahora pide iniciar sesión con correo y contraseña antes de usar cualquier página. Cada cuenta tiene un plan con fecha de vencimiento (por ejemplo, prueba de 14 días, mensual o anual); al vencer, la app muestra la pantalla de renovación.

- El administrador gestiona todo desde la página 17 — Administración: crear usuarios, asignar plan y vigencia, extender o revocar accesos y cerrar sesiones activas.
- En la pantalla de renovación aparecen los botones de pago configurados por el administrador: link de pago Wompi (mensual o anual) y/o datos de transferencia bancaria. Solo se aceptan links de dominios oficiales de Wompi, como protección contra suplantación.
- La primera vez que se instala en un servidor nuevo, el primer administrador se crea con un código de configuración de un solo uso (no viaja en el repositorio).
⚠️ Para no cometer errores: cada persona debe usar su propia cuenta. Los proyectos y resultados guardados son privados por usuario — si dos personas comparten una cuenta, se pisarán los datos entre sí.

────────────────────────────────────────────────────────────

18.2 Página 0 — 🧭 Asistente: guía paso a paso y chat con el manual  NUEVO

Nueva primera página del menú. Tiene dos partes:

- Guía del flujo: un checklist en vivo que detecta qué pasos ya completaste en esta sesión (proyecto definido, recurso solar descargado, dimensionamiento, producción, financiero, presupuesto, reporte) y te dice cuál es el siguiente paso y en qué página está.
- Chat del manual: puedes preguntar en lenguaje natural ("¿cómo cargo el CSV de sombras?", "¿qué significa el PR?") y el asistente responde usando este mismo Manual de Usuario como fuente. Requiere que el administrador haya configurado una clave de IA en el servidor; si no hay clave, la guía paso a paso funciona igual.
Consejo: si te pierdes en el flujo, abre el Asistente — el checklist te muestra exactamente qué falta y en qué orden.

────────────────────────────────────────────────────────────

18.3 Página 1 — Proyecto: varios proyectos guardados, privados por usuario  NUEVO

Ahora puedes guardar varios proyectos con nombre y alternar entre ellos sin perder nada. En la parte superior de la Página 1 está el selector: Guardar proyecto actual, Cargar y Eliminar.

- El proyecto activo se muestra en la barra lateral de todas las páginas, para que siempre sepas sobre qué proyecto estás trabajando.
- Privacidad: cada proyecto queda amarrado a la cuenta que lo guardó. Otros usuarios no pueden verlo, cargarlo ni borrarlo. Los proyectos guardados antes de esta versión solo los ve el administrador; al volver a guardarlos quedan asociados a su dueño.
- Al cargar un proyecto, la app pide re-ejecutar Recurso Solar (banner de pasos pendientes). Si la ciudad y las coordenadas no cambiaron, la descarga se revalida sola desde el caché en segundos.
⚠️ Para no cometer errores: cargar un proyecto NO revive simulaciones viejas — es a propósito, para que Producción y Financiero nunca muestren números de otra corrida. Sigue el banner de pasos pendientes en orden.

────────────────────────────────────────────────────────────

18.4 Tu trabajo sobrevive recargas y pestañas nuevas  NUEVO

Los resultados importantes ya no viven solo en la pestaña del navegador: se guardan en el servidor, en archivos privados de tu cuenta, y se restauran al volver a entrar.

- Producción Anual y Análisis Financiero: al abrir la página en una sesión nueva, si hay resultados guardados aparece un banner "restaurado de la sesión anterior" con la fecha. Antes de restaurar, la app verifica que la ciudad y las coordenadas coincidan con las guardadas.
- Consumo energético: el perfil de consumo y el modo de entrada que usaste se recuerdan automáticamente.
- Presupuesto: las tablas editadas (ítems, precios, activos/inactivos, costos blandos, OPEX) se guardan en disco por proyecto y por usuario, y vuelven al recargar.
Consejo: igual conviene oprimir los botones de guardar del Presupuesto después de ediciones grandes — el guardado explícito es inmediato.

────────────────────────────────────────────────────────────

18.5 Página 11 — Baterías: perfil de carga horario real  NUEVO

El balance energético con batería ahora puede usar un perfil de consumo hora a hora (8 760 valores) en lugar de un promedio plano. Esto cambia mucho el resultado en edificios con consumo concentrado en el día o en la noche: el autoconsumo, los ciclos de la batería y el ahorro se calculan contra el consumo real de cada hora.

- Puedes elegir entre perfiles típicos (residencial, comercial, industrial) o subir tu propio CSV horario.
⚠️ Para no cometer errores: si tienes la curva real de tu operador de red, úsala — el perfil típico es una aproximación y puede sobrestimar el autoconsumo.

────────────────────────────────────────────────────────────

18.6 Motor Óptico: efecto térmico BIPV integrado sin doble conteo  ACTUALIZADO

El sobrecalentamiento típico de los paneles integrados a fachada (k_bipv) ahora entra directamente al modelo de temperatura de celda y al modelo eléctrico del panel, en un solo lugar. Antes existía el riesgo de descontar el efecto térmico dos veces.

- Además, la POA corregida por el Motor Óptico (IAM + soiling) fluye automáticamente a Dimensionamiento y a Producción — ya no hay que activar nada manualmente.
────────────────────────────────────────────────────────────

18.7 Página 7 — Financiero: CAPEX del Presupuesto y ahorro de batería  ACTUALIZADO

- CAPEX como fuente única: el análisis financiero toma automáticamente el CAPEX Total del Presupuesto (con su nivel de contingencia), y muestra la fuente y la fecha de última actualización. Un toggle permite desvincularlo si quieres probar un CAPEX manual.
- El OPEX anual del Presupuesto entra como valor absoluto coherente en el VPN y la TIR.
- El ahorro que genera la batería (autoconsumo nocturno) ahora sí se incluye en la TIR y el Payback, no solo en la gráfica de balance.
⚠️ Para no cometer errores: si cambias precios en el Presupuesto, vuelve a abrir Financiero para que el CAPEX vinculado se refresque, y revisa la fecha de última actualización que aparece junto al valor.

────────────────────────────────────────────────────────────

18.8 Página 8 — Cotización exportada: cifras coherentes y celdas seguras  ACTUALIZADO

- El total en USD de la cotización (Excel y PDF) ahora se deriva exactamente del mismo total en COP de los ítems, con la TRM vigente — ya no pueden salir dos cifras de bases distintas en el mismo documento.
- El Excel exportado neutraliza textos que empiecen con símbolos de fórmula (=, +, -, @): protección estándar contra archivos maliciosos al compartir cotizaciones.
────────────────────────────────────────────────────────────

18.9 Página 10 — Reporte PDF: gráficas, logo y trazabilidad  ACTUALIZADO

- Nueva gráfica de producción mensual (barras) y nueva curva de flujo de caja acumulado con el año de payback marcado.
- Encabezado con el logo y los datos de contacto de tu empresa (se configuran una vez en el Presupuesto y se reutilizan).
- El reporte indica qué tasa de degradación se usó (historial PR real vs slider manual) y la zona horaria del análisis.
────────────────────────────────────────────────────────────

18.10 Catálogo de Inversores: diagnóstico, confianza y recarga automática  ACTUALIZADO

- Dimensionamiento muestra un semáforo de salud del catálogo de inversores (filas válidas, campos críticos vacíos, duplicados) con botón de recarga.
- Al extraer una ficha PDF, cada campo queda marcado con su nivel de confianza; antes de sobrescribir un inversor existente la app muestra un diff campo por campo y pide confirmación.
- Si reemplazas el Excel del catálogo en el servidor, la app lo detecta y recarga sola — ya no hay que esperar una hora ni reiniciar.
- En Dimensionamiento también aparece un banner cuando el panel elegido del catálogo tiene confianza distinta de Alta: sus dimensiones son estimadas y conviene confirmarlas con el fabricante antes de cerrar el diseño.
────────────────────────────────────────────────────────────

18.11 Página 9 — Vista 3D: nuevo análisis solar y de orientación  NUEVO

El tab solar de la Vista 3D ahora responde la pregunta clave: ¿está bien orientada mi fachada, y cuánto ganaría si la girara?

- Diagrama solar con líneas iso-hora: sobre las curvas del recorrido del sol se dibujan líneas punteadas de 07:00 a 17:00 hora local, para leer de un vistazo a qué hora el sol pasa por cada posición.
- Comparación de AOI mensual entre superficies: un multiselect permite poner lado a lado el ángulo de incidencia promedio de varias fachadas, con colores semáforo (verde < 40°, naranja < 60°, rojo ≥ 60°). Menor AOI = luz más perpendicular = más energía.
- 🧭 Orientación de mejor incidencia (geométrica): barrido de azimuth cada 5° que sugiere hacia dónde girar la superficie para mejorar el ángulo de incidencia, comparando solo orientaciones con horas de sol equiparables e indicando las horas de sol directo al año.
- ⚡ Orientación de máxima energía real (con TMY): barrido de 72 orientaciones que calcula la irradiación anual real (kWh/m²) de cada azimuth usando el clima del TMY y el horizonte de obstáculos del proyecto, y muestra el azimuth óptimo, la mejora porcentual y cuántos grados habría que girar. Incluye gráfica POA vs azimuth con la orientación actual y la óptima marcadas.
Consejo: usa primero la métrica de energía real (⚡) para decidir — es la que manda, porque incluye nubes y horizonte. La geométrica (🧭) sirve para entender el porqué.

⚠️ Para no cometer errores: estos barridos evalúan la orientación manteniendo la misma inclinación. En BIPV de fachada muchas veces la orientación viene dada por el edificio; usa el resultado como criterio para elegir ENTRE fachadas candidatas.

────────────────────────────────────────────────────────────

18.12 Página 5 — Mismatch: el CSV acepta meses en texto  ACTUALIZADO

El CSV de Factor de Sombreado ahora puede traer los meses escritos (Ene, Feb, Mar… o January, February…) además de números — es el formato que exporta la Calculadora de Sombreado 3D web. La app los reconoce automáticamente.

────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────

## 20. Anexo — Sombras desde Site Designer (Andrew Marsh): la ruta externa

Además de SketchUp y de la Calculadora de Sombreado 3D web, la app acepta escenas dibujadas en Site Designer, la herramienta gratuita de Andrew Marsh que corre en el navegador (buscar «Andrew Marsh Site Designer» o «3D Site Designer drajmarsh»). Es la opción más rápida para modelar los edificios vecinos como cajas simples: se dibujan los volúmenes, se exporta un archivo JSON y la calculadora hace el resto con su propio motor solar — el mismo ray-casting oficial de la ruta SketchUp. Site Designer solo aporta la geometría; los números de sombra los calcula siempre la calculadora, por eso ambas rutas dan resultados idénticos para la misma escena.

────────────────────────────────────────────────────────────

20.1 Qué dibujar en Site Designer  NUEVO

- Primero fija la ubicación del proyecto en Site Designer (latitud/longitud o buscando la ciudad): esa ubicación viaja dentro del JSON y la calculadora la compara contra el proyecto activo — si no coincide, avisa.
- Dibuja SOLO los obstáculos que producen sombra: edificios vecinos, muros, volúmenes de la propia edificación si sombrean la fachada. Cada obstáculo es un bloque (caja) con su posición y altura reales.
- NO dibujes los paneles ni la fachada de estudio: los puntos de análisis se definen después, dentro de la calculadora (igual que en la ruta SketchUp).
- Si Site Designer muestra el norte girado (northOffset), déjalo tal cual: el archivo lo registra y la calculadora aplica la corrección automáticamente.
────────────────────────────────────────────────────────────

20.2 Exportar el JSON  NUEVO

- En Site Designer usa la opción de guardar/exportar el proyecto: descarga un archivo con nombre tipo «site-designer-AAAA-MM-DD-HHMM-SS.json».
- No edites el JSON a mano. Si le falta información (por ejemplo el norte), la calculadora lo rechaza con un mensaje claro en vez de asumir valores.
El archivo contiene la ubicación (latitud, longitud, zona horaria, elevación, corrección de norte) y los obstáculos como cajas en milímetros. La conversión a metros es automática y fija — no hay selector de unidades que configurar.

────────────────────────────────────────────────────────────

20.3 Cargarlo en la calculadora  NUEVO

- Corre primero ☀️ Recurso Solar (el TMY del proyecto es obligatorio para alinear las horas de sombra con Producción).
- Abre 🌳 Sombras y sube el archivo .json en el mismo cargador donde va el modelo de SketchUp. La app confirma cuántos obstáculos leyó, sus dimensiones en metros, el norte corregido y la ubicación del archivo.
- Define los puntos de análisis (una fila de módulos = un punto, con sus coordenadas x, y, z en metros en el mismo sistema de la escena) y pulsa ▶️ Calcular sombras.
- Envía el resultado a la Página 5 con «📤 Enviar a Mismatch»: de ahí en adelante la cadena es la de siempre — bypass → E_ac corregida → Producción → Financiero.
Si la app avisa que la ubicación del archivo no coincide con la del proyecto, verifica que la escena sea del sitio correcto antes de continuar: una escena de otro proyecto produce sombras sin sentido físico.

────────────────────────────────────────────────────────────

20.4 Trazabilidad: el informe dice de dónde salieron las sombras  NUEVO

La fuente del sombreado queda registrada y visible en toda la cadena: en el resumen del modelo bypass (Página 5), en Producción y en el Reporte PDF aparece «Fuente del sombreado: SketchUp (interno)», «Site Designer + TMY (externo)» o «CSV externo». Es un dato informativo — no cambia ningún cálculo — pero le da credibilidad al informe que se entrega al cliente.

¿Cuándo usar cada ruta? Site Designer: escenas rápidas de cajas (edificios vecinos) sin instalar nada. SketchUp: geometrías detalladas, aleros, árboles con transparencia. Calculadora web: cuando ya existe el análisis punto a punto. Las tres desembocan en el mismo CSV de FS horario y el mismo modelo bypass.

────────────────────────────────────────────────────────────

## 21. Anexo — Actualizaciones del 21 de agosto de 2026

Esta entrega completa el comparador exhaustivo de inversores, cierra la validación técnica del Motor IV con una alarma explicativa que se propaga a Producción/Mismatch/Vista 3D, y corrige la desconexión entre el consumo real (factura) y el motor financiero, incluyendo por primera vez una tarifa diferenciada para el excedente exportado.

────────────────────────────────────────────────────────────

21.1 ⚖️ Comparador de Inversores: comparar TODO el catálogo compatible  NUEVO

Antes solo se podían comparar 2-4 modelos elegidos a mano. Ahora una sección adicional evalúa TODOS los inversores compatibles del catálogo de una sola vez, ordenados por LCOE, con los incompatibles listados aparte y motivo de rechazo. Incluye botón de Analista de Producción. Ver sección 6b.

────────────────────────────────────────────────────────────

21.2 🤖 Análisis IA: corrección del layout de accesos y del tipo de instalación citado  ACTUALIZADO

Los 4 accesos a los Analistas de Producción (Paneles/Orientación/Baterías/Inversores) se reorganizaron en cuadrícula 2×2 para que las etiquetas no se encimen. Además, se corrigió un error donde 🧩 Comparador de Paneles enviaba al agente el perfil de costos CAPEX de referencia en vez del tipo de instalación real del proyecto — el síntoma reportado era que la recomendación citaba "esta granja FV en campo" en una simulación de fachada. Ver secciones 6c y 6e.

────────────────────────────────────────────────────────────

21.3 🔬 Motor IV: alarma de validación SDM vs ficha técnica  NUEVO

La validación de Voc/Isc/Vmp/Imp/Pmax contra la ficha técnica (antes solo informativa en Motor IV) ahora corre automáticamente al entrar a Dimensionamiento y, si falla (error > 5%), muestra un texto técnico explicando exactamente qué métricas fallan y por qué — el mismo aviso se propaga a Producción, Mismatch y Vista 3D porque los cuatro reutilizan el mismo modelo SDM del panel. Ver sección 5 y las notas en secciones 8 y 8b.

────────────────────────────────────────────────────────────

21.4 🔋 Baterías y Balance: consumo sincronizado con la factura real  ACTUALIZADO

Los 3 modos de consumo de esta página (diario, anual con perfil típico/horario/12 valores) ahora usan como default el consumo real declarado en 🏠 Proyecto (modo "Conozco mi consumo/factura") en vez de estimarlo siempre desde la producción solar. Ver sección 12.

────────────────────────────────────────────────────────────

21.5 💰 Financiero: tarifa diferenciada para el excedente exportado  NUEVO

El motor financiero distinguía toda la energía a una sola tarifa; cuando había batería con excedente exportado, ese excedente ni siquiera generaba ingreso. Ahora la energía autoconsumida y la exportada se valoran cada una con su propia tarifa (la de excedentes es editable, con referencia a Res. CREG 174/2021, y por defecto igual a la tarifa de compra hasta que la ajustes). Ver sección 10.

⚠️ Para no cometer errores: revisa el nuevo campo "Tarifa de excedentes exportados" en Financiero si tu proyecto exporta energía a la red — antes de este cambio, esa energía no aportaba nada a la TIR/VPN aunque físicamente se estuviera exportando.

────────────────────────────────────────────────────────────

Manual actualizado el 21 de agosto de 2026

Novedades de esta versión: comparador exhaustivo de TODOS los inversores compatibles, corrección del layout y del tipo de instalación citado en 🤖 Análisis IA, alarma de validación SDM vs ficha técnica propagada a Motor IV/Producción/Mismatch/Vista 3D, sincronización del consumo real (factura) en Baterías y Balance, y tarifa diferenciada de excedentes exportados en Financiero.

────────────────────────────────────────────────────────────

## 22. Anexo — Actualizaciones del 22 de agosto de 2026

22.1 💼 Presupuesto: carga automática de cotizaciones de proveedor (PDF/Word)  NUEVO

Nuevo punto único de carga en 💼 Presupuesto (arriba de las 8 pestañas) que lee la cotización real de un proveedor (PDF o Word), extrae sus valores con evidencia citada del documento, sugiere a cuál de las 6 secciones de cotización pertenece (Perfilería, Mano de Obra, Sistema FV, Inversor y Equipos Eléctricos, Equipos del Catálogo o Costos Blandos) y solo aplica los valores cuando el usuario los confirma. Funciona con cualquier proveedor o layout, no con una plantilla específica. Ver el detalle completo en la sección 11, subsección "📄 Carga automática de cotizaciones (PDF/Word)".

⚠️ Para no cometer errores: la app nunca aplica un valor sin mostrarlo primero junto al fragmento del documento del que salió — si vas a usar esta función para un presupuesto bancable, de todas formas revisa la tabla de campos detectados antes de oprimir "Aplicar", igual que revisarías una cotización transcrita a mano.

────────────────────────────────────────────────────────────

Manual actualizado el 22 de agosto de 2026

Novedades de esta versión: carga automática de cotizaciones de proveedor (PDF/Word) en 💼 Presupuesto, con extracción genérica por patrones + respaldo por IA verificado y clasificador automático de sección destino.

────────────────────────────────────────────────────────────

## 23. Anexo — Actualizaciones del 25 de agosto de 2026

23.1 🔒 Ledger de Auditoría: cadena de hashes verificable por proyecto  NUEVO

Nueva página (🔒 Página 19) que sella resultados oficiales del proyecto — bancables, informativos para un cliente, o diagnósticos de un sistema ya instalado — en una cadena de hashes SHA-256 encadenados: alterar cualquier campo de un eslabón ya sellado, aunque sea un carácter de la nota, rompe la cadena de forma matemáticamente detectable. Implementa de forma **verificable** (no solo declarativa) el requisito de trazabilidad de cálculos del Art. 6 de la Res. CREG 174 de 2021 — un diferenciador concreto y citable frente a un banco, no una "buena práctica" genérica. Ver el detalle técnico completo en la sección 13e.

- 📄 Reporte PDF ahora ofrece un checkbox para sellar al generar (marcado por defecto), con el ID de verificación impreso en el propio documento entregado.
- 🔍 Diagnóstico ahora tiene un botón de sellado independiente del histórico de tendencia que ya existía, para proteger la conclusión de un diagnóstico puntual.
- El sellado es siempre manual y explícito — nunca automático en cada cálculo de prueba.

Actualización (27-ago-2026): se sumó un 4º tipo, ⚡ diagrama unifilar (diseño eléctrico) — sellable desde ⚡ Página 20. Ver el listado completo y siempre actualizado de los 4 tipos en la sección 13e, no en este anexo (este anexo queda fijo como registro histórico del 25-ago).

⚠️ Para no cometer errores: el Ledger protege contra la edición silenciosa de un eslabón ya guardado; NO protege contra borrar el archivo completo del ledger (eso requeriría un ancla externa, fuera de alcance por decisión explícita para mantener el principio de "todo local").

────────────────────────────────────────────────────────────

Manual actualizado el 25 de agosto de 2026

Novedades de esta versión: 🔒 Ledger de Auditoría — cadena de hashes verificable por proyecto, integrado en 📄 Reporte PDF y 🔍 Diagnóstico, implementando de forma verificable el requisito de trazabilidad del Art. 6 de la Res. CREG 174/2021.

## 24. Anexo — Actualizaciones del 26 de agosto de 2026

24.1 Validación cruzada contra PVsyst + corrección de bug de timezone en TMY (proyecto Agrivoltaico Urabá)  NUEVO

Los scripts de análisis del proyecto Agrivoltaico Urabá (220,32 kWp, `bipv_python/scripts/barrido_dcac_uraba.py` y `comparar_alt_b_uraba.py`) descargan su TMY directo de PVGIS con `pvlib.iotools.get_pvgis_tmy()`. Ese TMY viene indexado en UTC. El código re-etiquetaba las filas como si la posición N ya fuera la hora local N, sin convertir — un desfase de 5 horas (Colombia es UTC−5) entre la irradiancia y la posición solar de cada hora. Se detectó con una verificación de cierre físico (GHI = DNI·cosθ + DHI hora por hora: con el bug no cerraba, con el fix sí) y se corrigió con `tz_convert("America/Bogotá")` en vez de reetiquetar. El bug subestimaba la producción anual del script en ~20-25%.

De paso se agregó la pérdida IAM (reflexión angular, ASHRAE + factor difusa IEC 61853-3) a esos mismos scripts, reutilizando `iam_ashrae()` que ya existía en `calculos/motor_optico.py` — antes no la modelaban.

Con ambos fixes, se corrió una validación cruzada real contra PVsyst para el mismo proyecto (mismo TMY de PVGIS, mismo módulo JA Solar JAM66D46-720/LB, mismo inversor Growatt MAX 100KTL3 LV): la calculadora quedó a solo 1,6% de PVsyst en el caso monofacial, y a 1,2% en el caso bifacial (PVsyst con altura de montaje 3,0 m, pitch 6,6 m, GCR≈0,39, albedo 0,20 de pasto verde). Esto también validó el supuesto de ganancia bifacial +8% que usan esos scripts: PVsyst midió +7,6% real con la geometría física del proyecto, muy cerca del supuesto plano.

⚠️ Para no cometer errores: este bug estaba confinado a los 2 scripts de `bipv_python/scripts/` que llaman `get_pvgis_tmy()` directamente — **no afecta** el motor de producción real de la app. `calculos/solar.py::obtener_tmy_pvgis()` también usa PVGIS (corrección: no es Open-Meteo como se dijo en una nota anterior de este mismo anexo), pero maneja el tiempo correctamente — parsea en UTC y solo cambia el año, sin reetiquetar horas — así que irradiancia y posición solar quedan siempre bien emparejadas. Sí es la misma clase de riesgo que ya advierten la "Nota timezone" de Página 2 y el "Requisito obligatorio: el TMY del proyecto" de Página 5a — cualquier código nuevo que use una fuente de TMY indexada en UTC debe convertir con `tz_convert()`, nunca reetiquetar el índice a mano.

Entregables generados con las cifras corregidas: `entregables/Ficha_Tecnica_Preliminar_Agrivoltaico_Uraba_v2.docx` (v2.1) e `entregables/Informe_Final_Evaluador_Agrivoltaico_Uraba.pdf`. Detalle técnico completo del hallazgo, la verificación y ambas validaciones (mono y bifacial) en `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md` (raíz del repo).

────────────────────────────────────────────────────────────

24.2 Motor Óptico (IAM) ahora obligatorio en el flujo de Granja fotovoltaica/agrivoltaica + default de montaje corregido  NUEVO

Corriendo el motor REAL de la app (no solo los scripts) para el proyecto Agrivoltaico Urabá y comparando contra PVsyst, se confirmó que saltar 🔆 Motor Óptico en proyectos de campo abierto (como recomendaba el flujo agrivoltaico hasta ahora) deja fuera la pérdida IAM y sobreestima producción **+3,1%** frente a PVsyst. Corriendo Motor Óptico, la diferencia baja a **−0,70%**. Ver sección 2 ("Flujo recomendado para proyectos agrivoltaicos", ya actualizada) y el detalle numérico completo en `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md`.

Cambio de código que acompaña esto: en 🔆 Motor Óptico, el selector "Tipo de montaje" tenía como default fijo **"Fachada confinada (k=1,3)"** para todos los proyectos — correcto para el caso BIPV típico, pero físicamente incorrecto para una Granja fotovoltaica (estructura elevada a campo abierto, sin confinamiento térmico). Ahora, cuando el tipo de instalación del proyecto (🏠 Proyecto) es **"Granja fotovoltaica"**, Motor Óptico preselecciona automáticamente **"Ventilado libre (k=1,0)"** en su lugar — el usuario puede cambiarlo manualmente si su caso particular es distinto.

⚠️ Para no cometer errores: esto es un default automático, no un bloqueo — sigue siendo editable. Si tu granja FV tiene alguna condición de montaje más confinada (poco común, pero posible en diseños atípicos), ajusta el selector manualmente. El resto de los parámetros de Motor Óptico (tipo de vidrio/b₀, transparencia, soiling) no cambian automáticamente por tipo de proyecto — solo el montaje/k_BIPV.

────────────────────────────────────────────────────────────

24.3 optimization/variable_panel() conectado al catálogo Excel real de paneles (65)  NUEVO

Hasta ahora `optimization/variables.py::variable_panel()` (Fase 3, el vocabulario de variables que consume el optimizador de Fase 4) solo sorteaba entre los 7 paneles de `datos.tecnologias_bipv.MODULOS_BIPV` (familia ASP-ST1) — nunca se conectó al catálogo Excel real de 65 paneles (`datos.catalogo_paneles_excel`, el que usa 📐 Dimensionamiento y 📋 Catálogo Paneles), a diferencia de `variable_inversor()`, que sí prioriza su catálogo Excel de 105 inversores desde antes. Esto limitaba a 7 opciones cualquier barrido de optimización (📊 comparación panel/geometría/inversor para mejorar TIR) que un agente o la página de optimización quisiera correr.

**Qué se conectó**: nueva función `optimization.variables._catalogo_paneles_real()` — a diferencia de `_catalogo_inversores_real()` (que solo PREFIERE el catálogo grande), aquí se hace una **unión** con prioridad explícita: para las 7 claves que existen en ambas fuentes (`ASP-ST1-T10`..`T70`), gana siempre `MODULOS_BIPV` porque trae los 5 parámetros SDM De Soto calibrados por curve-fit contra el XLSM auditado (I_L_ref/I_o_ref/R_s/R_sh_ref/a_ref); la versión del Excel de esas mismas 7 claves solo trae un NsA/n_idealidad **estimado** (no calibrado), inferior. Los 58 paneles restantes del Excel (sin equivalente en MODULOS_BIPV) se agregan tal cual — se simulan con el modelo lineal simplificado, no con SDM (ver `calculos.produccion.panel_tiene_sdm_completo()`). El catálogo real resultante tiene **65** paneles totales (no 72: los 7 ASP-ST1 están *dentro* de los 65 del Excel, no se suman aparte).

`variable_panel()` sigue excluyendo por defecto los paneles sin `Pmax_stc` (ninguno de los 65 lo tiene hoy, así que no se excluye nada en la práctica) — ese filtro solo se aplica cuando se usa el catálogo por defecto, no cuando se pasa un `catalogo` explícito (contrato preexistente, ver docstring de la función).

**4 bugs reales encontrados y corregidos en la misma auditoría** (rigor pedido explícitamente por el usuario — verificar con ejecución real, correr la suite completa, no asumir):

1. `optimization.scenario_generator._resolver_categoricas_de_catalogo()` resolvía la clave sorteada de "panel" contra `MODULOS_BIPV` a secas — cualquier clave del Excel sorteada (58 de las 65 opciones) reventaba con `KeyError`. Mismo patrón que ya se había evitado para "inversor" en la misma función. Corregido: ahora resuelve contra `_catalogo_paneles_real()`.
2. `calculos.comparador_paneles.comparar_paneles()` tenía el mismo bug — tercera aparición del mismo patrón, encontrada corriendo la suite completa tras el fix de (1) (`KeyError: 'ASP-LAM3-T0 (1200x1200mm)'`). Corregido igual.
3. `calculos.comparador_paneles.paneles_excluidos_por_ficha_incompleta()` seguía usando `MODULOS_BIPV` como catálogo por defecto — inconsistente con lo que el usuario realmente ve comparado en 🧩 Comparador Paneles tras el fix de (2). Sin impacto práctico hoy (los 65 del Excel sí traen `Pmax_stc`), pero subreportaría en silencio el día que el Excel gane una ficha incompleta. Corregido para usar `_catalogo_paneles_real()`.
4. **El más serio**: `calculos.produccion._calcular_pmax_vectorizado()`, en su rama de fallback para paneles sin SDM completo, leía `panel.get("Tk_gamma", -0.45)` — ese patrón de `.get(clave, default)` solo aplica el default si la clave *falta*, no si existe con valor `None`. Un panel real del catálogo Excel (`HW-MQSB-V2 Teja Curva CIGS (Black)`) trae `Tk_gamma=None` explícito (clave presente, sin dato) → `float(None)` reventaba con `TypeError`. Bug preexistente en el código, nunca alcanzable hasta ahora porque `variable_panel()` nunca había expuesto un panel del Excel sin SDM en un flujo real. Corregido con el mismo idiom `or` que ya usan `NOCT`/`Tk_alfa` en el mismo archivo para el mismo problema.

⚠️ **Auto-corrección durante la propia auditoría**: la primera versión de este fix aplicaba el filtro de `Pmax_stc` incondicionalmente en `variable_panel()`, incluso cuando se pasaba un `catalogo` explícito — rompía el contrato del que depende `paneles_excluidos_por_ficha_incompleta()` (necesita ver las entradas *sin* `Pmax_stc`, no que ya vengan filtradas). Se encontró releyendo esa función antes de darla por no afectada, y se corrigió en el mismo commit, no en uno posterior.

Tests: se actualizaron 2 aserciones que asumían el catálogo viejo de 7 paneles como techo exacto (`test_optimization_contract.py::test_variable_panel_opciones_coincide_con_catalogo_real_simulable`, `test_optimization_fase4.py::test_variable_panel_incluye_toda_la_familia_asp_st1_completa` — de igualdad exacta a subconjunto/unión real), se ajustaron 2 tests de `test_comparador_paneles.py` que asumían que la mejor LCOE (`df.iloc[0]`) era siempre eléctricamente compatible con la config base (ya no es cierto con 65 paneles de Voc/Vmp muy distintos comparados con N_serie fijo), y se agregaron 2 tests de regresión nuevos para el comportamiento de unión (`test_catalogo_paneles_real_prioriza_sdm_calibrado_sobre_excel_para_asp_st1`, `test_catalogo_paneles_real_incluye_paneles_exclusivos_del_excel`, este último verificando resolución end-to-end vía `generar_candidatos()` sin `KeyError`). Suite completa: **717/717 passed**.

────────────────────────────────────────────────────────────

Manual actualizado el 29 de agosto de 2026

Novedades de esta versión: 📐 Dimensionamiento — el panel "⚡ Prorrateo preliminar del inversor cargado" guardaba el N recomendado en el momento del clic y nunca se invalidaba si después el usuario cambiaba "N total de cadenas para el proyecto" o `N_strings/tracker` -- solo se invalidaba al cambiar de inversor/panel. Combinaba un N viejo con un `N_str_tr` nuevo, dando un "Paneles/inversor" que no correspondía a ninguna recomendación real (caso real: TriP 6K-HV, 128 paneles/inversor con N=8 viejo × N_str_tr=8 nuevo, cuando el N recomendado real para ese N_str_tr es 7). Corregido con una clave dedicada (`prorrateo_preliminar_n_str_tr`, separada de `N_str_tr_usado` que ya usa otro botón para otro fin) que invalida el prorrateo cada vez que cambia N_strings/tracker. Ver sección 6.

Versión anterior (29 de agosto de 2026): 📐 Dimensionamiento — nuevo campo `alerta_margen` en `evaluar_compatibilidad_string()`: armoniza esa función (usada por "🧭 Mapeo de inversores"/"Prorrateo preliminar" y por el banner de compatibilidad de 📊 Producción) con el margen de seguridad del 7,5% que `optimizar_n_serie()` (botón "▶️ Optimizar N paneles/string") ya aplicaba y la otra no. Antes esto podía dar recomendaciones de N/string DISTINTAS para el mismo inversor real (caso encontrado: TriP 6K-HV, N=8 recomendado por el mapeo pero descartado por el optimizador por pasar el Vdc_max con solo 1,24% de margen). `compatible` no cambia de significado en ningún caso (retrocompatible con proyectos ya validados, ej. Urabá) — `alerta_margen` es un dato nuevo y aparte; `mapear_inversores_catalogo()` ahora prioriza N sin alerta al recomendar, y la UI muestra "⚠️ Margen ajustado" cuando aplica. 3 tests nuevos. Suite completa: **737/737**. Ver sección 6.

Versión anterior (29 de agosto de 2026): 📐 Dimensionamiento — `N_strings/tracker` ahora soporta el mismo mecanismo que PVsyst, no solo el autocálculo del catálogo. Nuevo campo opcional *"N total de cadenas para el proyecto (estilo PVsyst)"*: si se declara un total, `calculos/dimensionamiento.py::resolver_n_strings_tracker()` lo reparte entre los trackers del inversor (`ceil(N_total/n_trackers)`) — el mecanismo REAL de PVsyst (parte de lo que el usuario quiere instalar). Si se deja en 0 (default), sigue autocalculando desde la capacidad máxima del inversor en el catálogo — mejor para explorar cuánto cabe sin haber decidido un total todavía. Reemplaza a `resolver_n_strings_tracker_autocalculado()` con la misma protección: un ajuste manual del usuario se respeta mientras no cambie la fuente activa (inversor, o inversor+total). 4 tests nuevos (8 en total para esta función). Ver sección 6.

Versión anterior (29 de agosto de 2026): 📐 Dimensionamiento/📊 Producción — nueva alarma `evaluar_relacion_dc_ac()` homóloga al aviso real de PVsyst 8.1.5 ("La potencia del inversor está muy sobredimensionada", Proporción Pnom) para el proyecto real Teusaquillo (ratio 0,538 verificado idéntico contra una captura real de PVsyst, que además reveló que PVsyst bloquea DURO la simulación en ese caso — no es solo advertencia; la app avisa pero no bloquea, a propósito). Al intentar reproducir el caso real se encontraron y corrigieron 3 bugs reales de catálogo: el Growatt MID15KTL3-X ni siquiera estaba en el catálogo Excel real (solo en un catálogo Python viejo sin uso); faltaba la columna "Potencia AC nominal (kW)" en TODO el catálogo (~106 inversores calculaban su potencia CA vía un respaldo `P_dc_max×0,96` en vez del dato real del fabricante — para este inversor daba 21.600W en vez de 15.000W reales); y la corriente máxima por tracker se había derivado mal (de lo que produce el arreglo, no de lo que soporta el inversor). Además, `N_strings/tracker` (Dimensionamiento) autocalculaba desde `inversor["n_strings_tracker"]` del catálogo en vez de quedar fijo en 1 por defecto — ese default duro había hecho que el mismo proyecto Teusaquillo se calculara como "128 módulos → 8 inversores necesarios" en vez de 1 (función desde entonces reemplazada, ver arriba). ⚠️ **Pendiente sin resolver, léelo antes de tocar el catálogo de inversores**: existe una familia genérica "MID 15/17/20/22/25KTL3-X" (sin marca) casi con certeza duplicada del "Growatt MID15KTL3-X" real, con specs distintas (N_strings/tracker=1 vs 8 real) — el "mapeo de inversores compatibles" tiende a sugerir la genérica primero; ver detalle y advertencia completa en la sección 6. Ficha completa en `DIAGNOSTICO_VALIDACION_TEUSAQUILLO_PVSYST.md`. Ver secciones 6 y 9.

Versión anterior (29 de agosto de 2026): 📊 Producción — corregido bug real donde la app NUNCA recortaba (clipping) la producción al Pnom del inversor: `P_ac = P_dc × η` sin ningún tope, así que cualquier proyecto con relación DC/AC > 1 (el diseño estándar de la industria) sobreestimaba producción sin límite (cuantificado: +10,8% en un caso típico DC/AC=1.3). Nunca apareció en las validaciones contra PVsyst ya hechas (Urabá y Teusaquillo tienen DC/AC < 1). Corregido en ambos motores (modelo simplificado y curva IV real), con nueva fila "Recorte inversor" en la cascada de pérdidas, igual que hace PVsyst. Limitación real declarada: multi-superficie con inversor compartido entre superficies no modela el recorte agregado del bus todavía. Ver sección 9.

Versión anterior (28 de agosto de 2026): 💰 Financiero — nueva advertencia cuando un proyecto supera el umbral de 1 MW de "autoconsumo a pequeña escala" (Ley 1715): el dato ya existía en `datos/ciudades_colombia.py` pero ningún cálculo lo usaba, así que un mega-proyecto podía mostrar beneficios fiscales sin avisar que el régimen real a esa escala puede ser distinto. No bloquea ni recalcula, solo advierte (`FinancialResult.advertencia_ley_1715` + banner en Página 7). Verificado con un caso sintético de ~1,2 MWp y con Urabá (220 kWp, sin advertencia). Suite completa: 718/718. Ver sección 10.

Versión anterior (28 de agosto de 2026, más temprano): 📋 Catálogo de Paneles — 3 bugs reales más encontrados con la ficha de familia Solar First (10 variantes, serie ST1/ST2): (1) la tabla multi-modelo "por fila" (modelos en filas, no en columnas) no se reconocía por códigos de modelo cortos («ST1-72») — nueva `_detectar_tabla_modelos_por_fila()` la resuelve; (2) falso positivo real de marca: "película delgada" se detectaba como marca "LG" (substring sin límite de palabra) — corregido con `\b...\b`, riesgo genérico para cualquier marca corta; (3) `datos/catalogo_paneles_excel.py::_f()` no manejaba `NaN` de celdas vacías (pandas), causando `ValueError: P_dc_kW contiene valores no finitos` al simular paneles con campos opcionales vacíos — corregido con el mismo patrón `isfinite()` que ya usaba correctamente el `_f()` de inversores. 10 modelos Solar First ingresados al catálogo real (66→76), coeficientes de temperatura dejados en blanco a propósito por instrucción explícita de la propia ficha ("no confirmado, no cargar como dato oficial"). Ver sección 13d.

Versión anterior (28 de agosto de 2026, más temprano): 🔌 Catálogo de Inversores PDF — 3 alias reales agregados para fichas en formato INNOVAQ en español (Vdc_max: «Voltaje FV máximo absoluto»; Vmppt_min/max en filas separadas; P_dc_max_W en kW) tras reportar el usuario una ficha Woodward IDS SOLO 500 sin extraer. **1 hallazgo NO corregido a propósito**: I_max/Isc_max_tracker no es un problema de etiquetas para inversores centrales sin trackers discretos — poblarlo habría vuelto falsamente permisivo el gate de compatibilidad eléctrica para cualquier config de strings. Al intentar guardar el inversor se encontró y corrigió además un bug real de infraestructura: `datos/catalogo_inversores_excel.py` tenía la ruta del Excel hardcodeada solo al servidor (sin el fallback local que sí tenía el de paneles) — en cualquier entorno de desarrollo el catálogo real de 105 inversores nunca cargaba, cayendo en silencio al catálogo Python de 7. Inversor Woodward IDS SOLO 500 ingresado al catálogo real (marcado `Datos completos = No`, primer caso del catálogo, por los campos que genuinamente no aplican a este inversor central). Ver sección 13b.

Versión anterior (28 de agosto de 2026, más temprano): 📋 Catálogo de Paneles — corregido falso "multi-modelo" (una ficha de un solo panel real, Suntech STP-410-A72-Pnh-Bifacial, se detectaba como 2 modelos) causado por una nota de auto-verificación cruzada en la misma línea del valor de Pmax (`"410.18 W ✓ coincide con 410.0 Wp"`); el mismo bug también corrompía Isc (0.05 A en vez de 10.49 A) por la misma causa en la línea del coeficiente de temperatura µIsc — confirmado con el PDF real que un solo fix resuelve ambos. Reportado por el usuario, root-caused reproduciendo el texto y luego el PDF real antes de tocar/confirmar el fix. Panel Suntech STP-410-A72-Pnh-Bifacial ingresado al catálogo real. Ver sección 13d.

Versión anterior (27 de agosto de 2026): `optimization.variable_panel()` conectado al catálogo Excel real de 65 paneles (antes solo 7) para que el optimizador de Fase 4 y cualquier agente puedan barrer panel real × geometría × inversor al buscar mejor TIR — 4 bugs reales encontrados y corregidos en la misma auditoría (3 apariciones del mismo patrón de `KeyError` por resolver contra el catálogo viejo, 1 `TypeError` real en el modelo simplificado de producción). Ver sección 24.3.

Versión anterior (27 de agosto de 2026, más temprano): nueva página 📋 Ficha de Validación RETIE (Página 21) — dashboard ejecutivo + motor de validación eléctrica (Voc frío, ventana MPPT, balance de inversores, breaker por calibre) generalizado a N inversores, verificado con 2 proyectos distintos a Urabá (1 y 3 inversores) tras alerta explícita del usuario sobre no dejarlo hardcodeado. Ver sección 13g.

Versión anterior (27 de agosto de 2026, más temprano): ⚡ Diagrama Unifilar (Página 20) suma **Detalle RETIE** — contenido extraído de un script aparte que aportó el usuario (protecciones detalladas, equipotencialidad, notas/pendientes), sobre la arquitectura universal existente, sin adoptar su motor de dibujo. Ver sección 13f, subsección "Detalle RETIE" para el detalle completo (incluye 3 bugs de renderizado encontrados y corregidos, y 1 bug preexistente encontrado pero no corregido por estar fuera de alcance).

Versión anterior (27 de agosto de 2026, más temprano): ⚡ Diagrama Unifilar (Página 20) completa su plan de 4 fases con el sellado en el Ledger de Auditoría (Fase 4, nuevo tipo `diagrama_unifilar`) — se suma a multi-superficie (Fase 3, misma sesión) y batería (Fase 2, sesión anterior). Ver sección 13f (diagrama) y 13e (Ledger, ahora 4 tipos) para el detalle completo.

Versión anterior (27 de agosto de 2026, más temprano): multi-superficie (Fase 3) — N superficies convergiendo en un bus horizontal común, auto-llenado desde 🗺️ Vista 3D.

Versión anterior a esa (26 de agosto de 2026): corrección de bug de timezone en TMY de PVGIS + pérdida IAM en los scripts de análisis del proyecto Urabá, primera validación cruzada documentada de la calculadora (scripts y motor real) contra PVsyst (monofacial y bifacial), y Motor Óptico ahora obligatorio en el flujo de Granja fotovoltaica/agrivoltaica con default de montaje "Ventilado libre" corregido para ese tipo de proyecto.

Calculadora BIPV — Innovación Química

Repositorio: github.com/ventas108/calculadora-bipv

