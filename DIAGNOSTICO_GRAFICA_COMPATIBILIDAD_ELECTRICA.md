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

## Actualización (30 de agosto de 2026, mismo día): visibilizada también en 📊 Producción

El usuario pidió explícitamente que la gráfica "esté visibilizada en el módulo correspondiente y
con las respectivas interpretaciones según el caso del proyecto evaluado" — no solo en el Reporte
PDF. `pages/6_📊_Produccion.py` es ese módulo: ya calculaba `evaluar_compatibilidad_string()` para
el banner de compatibilidad eléctrica que existía antes de este cambio.

**Qué se agregó:**

1. **`calculos/dimensionamiento.py::interpretar_curva_electrica()`** (función pura, nueva). Traduce
   `curva_electrica_temperatura()` a una interpretación en lenguaje natural, punto por punto (Voc
   frío / Vmp real / Vmp extremo), identificando cuál límite del inversor manda en cada uno y con
   qué margen (`nivel`: "ok" / "ajustado" / "critico"). No evalúa nada nuevo — traduce a texto lo
   que `evaluar_compatibilidad_string()` ya calculó, igual que haría un ingeniero leyendo el mismo
   gráfico a mano.

2. En `pages/6_📊_Produccion.py`, la llamada directa a `evaluar_compatibilidad_string()` se
   reemplazó por `curva_electrica_temperatura()` (que internamente sigue llamando a la misma
   función para el veredicto — mismo resultado bit a bit, verificado por
   `test_curva_electrica_no_reimplementa_la_fisica_coincide_con_evaluar_compatibilidad`). El
   banner de compatibilidad (🟢/🔴) queda idéntico a como estaba.

3. Justo debajo del banner, un `st.expander` (expandido automáticamente cuando la configuración es
   incompatible, colapsado cuando es sana) con:
   - El mismo gráfico Voc(T)/Vmp(T) vs. banda MPPT y límite Vdc máximo, ahora interactivo
     (Plotly, en vez de SVG estático — consistente con el patrón ya usado en 🔬 Motor IV de esta
     misma página para la curva I-V).
   - Los 3 puntos de diseño coloreados en verde o rojo según el veredicto real.
   - Las interpretaciones de `interpretar_curva_electrica()`, cada una como `st.error` (crítico),
     `st.warning` (ajustado) o `st.caption` (ok) — adaptadas al caso real del proyecto cargado en
     ese momento, no un texto genérico.

**Verificado con los casos reales de Urabá:**
- N=18: Voc frío 🟢 sano (40.8% de margen bajo Vdc máx), Vmp real 🔴 crítico (687V bajo el piso
  MPPT de 850V), Vmp extremo 🔴 crítico (665V, 185V bajo el piso — pierde MPPT en las horas de
  mayor producción).
- N=28: los 3 puntos 🟢 sanos (Vmp extremo con 21.8% de margen sobre el piso MPPT).

**Cobertura:**
- 3 tests nuevos para `interpretar_curva_electrica()` en `test_compatibilidad_string.py` (críticos
  en N=18, ninguno crítico en N=28, lista vacía sin límites del inversor). Suite completa:
  **797 passed**.
- El bloque Plotly de `pages/6_📊_Produccion.py` no tiene cobertura pytest directa (mismo motivo
  que las funciones SVG del Reporte PDF: el módulo llama `st.set_page_config()` en tiempo de
  import). Se hizo smoke-test real: se instaló Plotly 5.22.0 (la versión fijada en
  `requirements.txt`) en un entorno aislado y se ejecutó el bloque de construcción de la figura
  extraído tal cual, con los datos reales de Urabá para N=18 y N=28 — la figura se construye sin
  excepciones (`fig.to_json()` fuerza la validación completa) y las interpretaciones impresas
  coinciden exactamente con los casos ya documentados arriba.

## Segunda actualización (30 de agosto de 2026, mismo día): visibilizada también en 📐 Dimensionamiento

El usuario pidió "agrégala también en Dimensionamiento" tras verla en Producción. Dimensionamiento
es donde el usuario realmente **elige** el N/string (botón "▶️ Optimizar N paneles/string"), así
que este es el módulo donde más temprano en el flujo conviene ver el comportamiento eléctrico
completo del N óptimo — no solo el semáforo OK/ALERTA/FALLA de la tabla de candidatos.

**Refactor hecho antes de duplicar el código**: como la misma gráfica ahora vive en dos páginas, se
extrajo la construcción de la figura Plotly a `calculos/graficos_compatibilidad.py::figura_compatibilidad_electrica()`
(sin lógica de verificación, solo dibuja lo que `curva_electrica_temperatura()` ya calculó) — evita
el riesgo real de que las dos páginas terminen mostrando el mismo caso de forma distinta si una se
edita y la otra no (la misma clase de bug de coherencia entre módulos que ya se corrigió antes en
esta app, ver `bipv_tipo_instalacion_coherencia` en la memoria del asistente). `pages/6_📊_Produccion.py`
se migró a usar la función compartida en el mismo cambio (comportamiento idéntico, verificado con la
suite completa).

**Dónde quedó en Dimensionamiento**: dentro del bloque `if sin_riesgos:` del botón "▶️ Optimizar N
paneles/string", justo después de fijar `N_serie` en session_state y antes de calcular el
dimensionamiento del sistema — usa exactamente los mismos `T_frio`/`T_real`/`T_extr`/`N_str_tr` que
ya se le pasaron a `optimizar_n_serie()` unas líneas arriba, así que el gráfico corresponde
exactamente al `N óptimo` que la tabla acaba de recomendar. Como `mejor` siempre viene de
`sin_riesgos` (riesgos == 0), el panel queda colapsado por defecto (a diferencia de Producción, que
se auto-expande si la config es incompatible — aquí ese caso no puede darse por construcción).

Suite completa tras el cambio: **797 passed** (sin tests nuevos: `figura_compatibilidad_electrica()`
es un paso a través puramente visual de datos ya cubiertos por los tests de
`curva_electrica_temperatura()`/`interpretar_curva_electrica()`). Smoke-test real del módulo
compartido con Plotly 5.22.0 instalado en un entorno aislado, para N=18 y N=28 de Urabá — la figura
se construye sin excepciones para ambos casos.

## Nota aparte (no corregida, fuera de alcance)

Se detectó que el checkbox "Incluir sección Dimensionamiento" (`key="rep_inc_dim"`) del Reporte PDF
no se referencia en ningún lugar dentro de `generar_html_reporte()` — parece ser un control de UI
sin efecto. La nueva sección de compatibilidad eléctrica se activa independientemente de ese
checkbox, con su propio gate (`N_serie`/`panel_dict`/`inversor_dict_dim`). No se corrigió por estar
fuera del alcance de esta tarea.
