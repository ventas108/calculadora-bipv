# Brainstorming de Diseño: Calculadora de Factores de Sombreado Solar

## Respuesta 1: Diseño Técnico Minimalista con Énfasis en Datos
**Probabilidad: 0.08**

### Design Movement
Modernismo técnico con influencia de dashboards científicos - inspirado en software de ingeniería profesional como AutoCAD y análisis de energía solar.

### Core Principles
1. **Claridad de datos**: Cada número, cada entrada tiene propósito visible
2. **Eficiencia visual**: Máxima información con mínimo ruido visual
3. **Precisión estética**: Alineación perfecta, tipografía monoespaciada para valores numéricos
4. **Jerarquía funcional**: Las acciones más frecuentes son más prominentes

### Color Philosophy
- Fondo blanco puro (no gris) para máximo contraste
- Azul técnico profundo (#0066CC) para elementos primarios y datos críticos
- Verde suave (#10B981) para valores válidos/sombreado bajo
- Naranja cálido (#F59E0B) para advertencias de sombreado alto
- Gris neutro (#6B7280) para elementos secundarios
- Reasoning: Colores que comunican estado sin necesidad de leyenda

### Layout Paradigm
- Grid de 12 columnas con tabla como elemento central
- Panel de control izquierdo (20% ancho) con parámetros globales
- Área de tabla principal (80% ancho) con scroll horizontal para muchas columnas
- Resumen de resultados en panel derecho flotante (sticky)

### Signature Elements
1. **Tabla editable inline**: Celdas que se transforman en inputs al hacer clic
2. **Indicadores visuales de estado**: Barras de progreso horizontal para FS (0-1)
3. **Gráfico de distribución**: Visualización de FS a lo largo del año

### Interaction Philosophy
- Click-to-edit en celdas de tabla
- Validación en tiempo real con feedback visual inmediato
- Tecla Tab para navegar entre celdas
- Botones de acción flotantes para agregar/eliminar filas

### Animation
- Transiciones suaves (300ms) al cambiar valores
- Fade-in de filas nuevas
- Highlight temporal (amarillo suave) cuando se edita una celda
- Animación de cálculo: números contadores que suben/bajan

### Typography System
- **Display**: IBM Plex Mono Bold para títulos (h1, h2)
- **Body**: IBM Plex Sans Regular para texto
- **Data**: IBM Plex Mono Regular para valores numéricos en tabla
- Jerarquía: 32px (h1) → 24px (h2) → 16px (body) → 12px (data)

---

## Respuesta 2: Diseño Intuitivo Educativo con Visualización Solar
**Probabilidad: 0.07**

### Design Movement
Diseño educativo interactivo inspirado en aplicaciones de ciencia (como Duolingo para ingeniería) - accesible pero profesional.

### Core Principles
1. **Progresión visual**: De conceptos simples a análisis complejos
2. **Retroalimentación inmediata**: El usuario ve el impacto de cada cambio
3. **Contextualización**: Explicaciones breves integradas en la interfaz
4. **Gamificación suave**: Indicadores de progreso y logros

### Color Philosophy
- Fondo gradiente suave: de azul cielo claro (#E0F2FE) a blanco
- Dorado solar (#FCD34D) para elementos relacionados con radiación
- Azul océano (#0369A1) para sombreado/obstáculos
- Verde crecimiento (#16A34A) para eficiencia
- Reasoning: Colores que evocan el contexto solar de forma intuitiva

### Layout Paradigm
- Sección superior: Diagrama interactivo de trayectoria solar (50% altura)
- Sección inferior: Tabla de análisis con vista previa (50% altura)
- Sidebar derecho: Explicaciones y tips contextuales
- Diseño asimétrico con énfasis en visualización

### Signature Elements
1. **Diagrama solar interactivo**: Representación visual de la posición del sol
2. **Tarjetas de información**: Tooltips expandibles con explicaciones
3. **Indicador de impacto**: Visualización de cómo cada obstáculo afecta el FS

### Interaction Philosophy
- Hover en filas de tabla muestra impacto visual en diagrama
- Click en diagrama solar auto-rellena altura y acimut
- Sliders para valores en lugar de inputs numéricos (cuando sea posible)
- Modo "tutorial" para usuarios nuevos

### Animation
- Movimiento suave del sol en diagrama (simulación de trayectoria)
- Transiciones de color al cambiar valores
- Pulso suave en elementos interactivos
- Entrada escalonada de elementos en scroll

### Typography System
- **Display**: Poppins Bold para títulos (h1, h2)
- **Body**: Poppins Regular para texto descriptivo
- **Data**: Roboto Mono para valores numéricos
- Jerarquía: 40px (h1) → 28px (h2) → 16px (body) → 13px (data)

---

## Respuesta 3: Diseño Oscuro Profesional con Énfasis en Rendimiento
**Probabilidad: 0.09**

### Design Movement
Dark mode profesional inspirado en software de análisis financiero y herramientas de trading - sofisticado y moderno.

### Core Principles
1. **Contraste de alto rendimiento**: Fácil lectura en cualquier iluminación
2. **Sofisticación visual**: Detalles sutiles que comunican profesionalismo
3. **Enfoque sin distracciones**: Fondo oscuro minimiza fatiga visual
4. **Densidad de información**: Más datos visibles sin desorden

### Color Philosophy
- Fondo oscuro: Gris carbón (#1F2937)
- Acentos primarios: Cian brillante (#06B6D4) para interactividad
- Verdes de éxito: Verde esmeralda (#10B981) para FS óptimo
- Rojos de alerta: Rojo coral (#EF4444) para FS crítico
- Grises neutros: Escala de grises para jerarquía
- Reasoning: Colores que brillan sobre fondo oscuro, comunican estado claramente

### Layout Paradigm
- Header sticky con logo y controles globales
- Tabla principal con filas alternadas (gris más claro/oscuro)
- Panel de estadísticas derecho con cards flotantes
- Footer con información de cálculos y exportación

### Signature Elements
1. **Tabla con filas alternadas**: Mejora legibilidad en dark mode
2. **Cards de estadísticas flotantes**: Resumen de FS promedio, máximo, mínimo
3. **Gráfico de tendencia**: Visualización de FS a lo largo del año

### Interaction Philosophy
- Hover en filas resalta con fondo más claro
- Doble-click para editar (no click simple)
- Validación con colores de alerta integrados
- Atajos de teclado para usuarios avanzados

### Animation
- Transiciones suaves (200ms) en cambios de estado
- Glow suave en elementos activos
- Fade-in de datos calculados
- Animación de scroll suave

### Typography System
- **Display**: Space Mono Bold para títulos
- **Body**: Inter Regular para texto (default Tailwind)
- **Data**: JetBrains Mono para valores numéricos
- Jerarquía: 36px (h1) → 24px (h2) → 15px (body) → 12px (data)

---

## Decisión Final: Respuesta 1 - Diseño Técnico Minimalista

Se selecciona el **Diseño Técnico Minimalista** por las siguientes razones:

1. **Alineación con propósito**: Una calculadora de ingeniería debe priorizar precisión y claridad sobre estética
2. **Eficiencia de usuario**: Los ingenieros valoran la velocidad de entrada y lectura de datos
3. **Escalabilidad**: Fácil agregar más parámetros sin saturar la interfaz
4. **Profesionalismo**: Comunica confiabilidad y precisión técnica

### Implementación Confirmada:
- **Tipografía**: IBM Plex Mono para datos, IBM Plex Sans para UI
- **Colores**: Azul técnico (#0066CC), Verde (#10B981), Naranja (#F59E0B)
- **Layout**: Grid asimétrico con tabla central y paneles laterales
- **Interacción**: Click-to-edit, validación en tiempo real, navegación con Tab
