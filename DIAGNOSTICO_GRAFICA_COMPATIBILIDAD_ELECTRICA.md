# Gráfica de compatibilidad eléctrica string–inversor en el Reporte PDF

**Fecha**: 30 de agosto de 2026
**Disparador**: el usuario preguntó qué ventaja tendría integrar, para cada inversor, un gráfico de
compatibilidad eléctrica como el que muestra una referencia estándar internacional (Voc/Vmp del
string vs. temperatura, contrastado con la ventana MPPT y el límite Vdc máximo del inversor).
Tras confirmar honestamente que la app ya verifica esto con certeza matemática (Voc y Vmp son
funciones lineales de la temperatura, así que los 3 puntos de diseño ya cubren toda la curva
continua) y que el valor real de un gráfico así es solo visual/comunicación, el usuario respondió:
**"sí, sirve para el reporte — agrégalo"**.

## Qué se agregó

1. **`calculos/dimensionamiento.py::curva_electrica_temperatura()`** (función pura, nueva).
   Muestrea Voc(T) y Vmp(T) del string entre la temperatura de diseño mínima y la máxima
   (por defecto `n_puntos=40`), y llama internamente a `evaluar_compatibilidad_string()` para el
   veredicto real — **no reimplementa la física de verificación**. Devuelve además los límites
   del inversor (`vdc_max`, `vmppt_min`, `vmppt_max`) que `evaluar_compatibilidad_string()` ya
   calcula pero no expone en su valor de retorno.

2. **`pages/10_📄_Reporte_PDF.py::_curva_electrica_svg()`** (nueva función de dibujo).
   Sigue el mismo patrón hand-built-SVG que las gráficas ya existentes del reporte
   (`_barras_mensuales_svg`, `_flujo_caja_svg`, `_waterfall_cascada_svg`): sin librerías externas,
   `viewBox` + coordenadas calculadas a mano. Dibuja:
   - Banda verde clara = ventana MPPT activa del inversor.
   - Línea roja punteada = límite absoluto Vdc máximo.
   - Curva azul = Voc(T), curva naranja = Vmp(T).
   - 3 puntos marcados (color verde si compatible, rojo si no) en las temperaturas de diseño real
     del proyecto (frío / real / extremo).

3. Nueva sección del reporte **"⚡ Compatibilidad Eléctrica String–Inversor"**, insertada después
   de "Recurso Solar", gated en `N_serie` + `panel_dict` + `inversor_dict_dim` presentes en
   `session_state`. Incluye el gráfico, una tabla resumen (Voc frío / Vmp real / Vmp extremo /
   estado) y una nota explícita al usuario final:

   > "Voc y Vmp son funciones lineales de la temperatura de celda: verificar los 3 puntos de
   > diseño (frío, real, extremo) cubre con certeza matemática toda la curva continua entre
   > ellos — el gráfico es para verificación visual, no agrega precisión sobre el cálculo ya
   > validado."

## Por qué esto NO es una nueva verificación (framing honesto)

`evaluar_compatibilidad_string()` ya es la fuente de verdad usada por el gate de Dimensionamiento
y el banner de Producción. La curva nueva llama a esa misma función sin modificarla y solo
interpola linealmente los mismos coeficientes de temperatura (`Tk_beta`) entre los 3 puntos que
ya se evalúan. No hay ningún escenario físico entre esos 3 puntos que la curva pueda revelar y que
los 3 puntos discretos no cubrieran ya — Voc y Vmp son afines en T, así que el mínimo/máximo de la
curva siempre cae en uno de los extremos ya evaluados.

## Verificación realizada

- **5 tests nuevos** en `tests/test_compatibilidad_string.py`, anclados a los casos reales de
  Urabá ya validados en esta base de conocimiento:
  - La curva coincide bit-a-bit con `evaluar_compatibilidad_string()` llamada directamente.
  - N=18 en serie: incompatible (`Vmp extremo < Vmppt_min = 850V`).
  - N=28 en serie: compatible.
  - Temperaturas ordenadas de menor a mayor, extremos coinciden con los parámetros de entrada.
  - Sin límites del inversor (`{}`) → `vdc_max`/`vmppt_min`/`vmppt_max` son `None`, no `0`
    (evita que un gráfico vacío se dibuje como si el límite fuera cero).
- **Geometría del SVG verificada a mano**: se recalcularon independientemente las coordenadas
  píxel esperadas para el caso N=18 (Voc frío ≈888V, Vmp extremo ≈665V, banda MPPT 850–1300V,
  Vdc máx 1500V) y se contrastaron contra la salida real de `_curva_electrica_svg()` — coinciden
  exactamente (ej. y=207.6px para la línea MPPT mín=850V, y=198.2px para el primer punto de
  Voc(T)). El punto rojo de Vmp extremo cae visualmente por debajo de la banda verde, tal como
  corresponde a la incompatibilidad real conocida de ese caso.
- **Suite completa**: `PYTHONUTF8=1 python -m pytest tests/ -q` → **794 passed**, sin regresiones.
- Limitación conocida (consistente con el resto del reporte): las funciones SVG de
  `pages/10_📄_Reporte_PDF.py` no tienen cobertura pytest directa porque el módulo llama a
  `st.set_page_config()` en tiempo de import y no puede importarse fuera de una sesión Streamlit
  — mismo patrón ya existente para sus funciones hermanas. Se verificó por extracción de AST +
  `exec` en un namespace aislado, sin excepciones, para N=18 y N=28.

## Nota aparte (no corregida, fuera de alcance)

Se detectó que el checkbox "Incluir sección Dimensionamiento" (`key="rep_inc_dim"`) del Reporte PDF
no se referencia en ningún lugar dentro de `generar_html_reporte()` — parece ser un control de UI
sin efecto. La nueva sección de compatibilidad eléctrica se activa independientemente de ese
checkbox, con su propio gate (`N_serie`/`panel_dict`/`inversor_dict_dim`). No se corrigió por estar
fuera del alcance de esta tarea.
