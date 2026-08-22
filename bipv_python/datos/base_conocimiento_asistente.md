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
- Página 4 — Dimensionamiento
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
- Calculadora de Sombreado 3D
- Cadena completa — bypass y multi-superficie
- Interpretación de resultados clave
- Preguntas frecuentes
- Anexo — Sombras desde Site Designer / Andrew Marsh (ruta externa, agosto 2026)  NUEVO
- Anexo — Actualizaciones 6-7 de agosto 2026 (Asistente, cuentas, proyectos y Vista 3D solar)  NUEVO
- Anexo — Actualizaciones del 21 de agosto de 2026 (comparadores, validación Motor IV, consumo y excedentes)  NUEVO
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

Flujo recomendado para proyectos agrivoltaicos  NUEVO (5-ago-2026)

1 Proyecto (tipo Granja fotovoltaica + factor de ocupación) → 2 Recurso Solar (verificar GCR sincronizado → Calcular POA) → 4 Dimensionamiento (área útil) → 9 Vista 3D (verificación visual de filas y cultivo) → 6 Producción → 7 Financiero → 8 Presupuesto → 10 Reporte PDF.

Regla de oro agrivoltaica: factor de ocupación (Proyecto) = GCR (Recurso Solar). Si cambias uno, revisa el otro.

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

## 6. Página 4 — Dimensionamiento

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

Calculadora BIPV — Innovación Química

Repositorio: github.com/ventas108/calculadora-bipv

