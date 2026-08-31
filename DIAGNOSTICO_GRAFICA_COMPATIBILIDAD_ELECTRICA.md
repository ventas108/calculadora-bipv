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

## Tercera actualización (30 de agosto de 2026, mismo día): auditoría de coherencia con Motor IV

El usuario pidió "confírmalo en Motor IV también". Motor IV no tiene contexto de string/inversor
(simula UN panel, sin N/string ni inversor en pantalla), así que tras aclarar el alcance con el
usuario, la tarea quedó en: **confirmar que el modelo lineal** que usa `curva_electrica_temperatura()`
(Voc_stc/Vmp_stc escalados por `Tk_beta`) **es coherente con el modelo físico completo que usa el
propio Motor IV** (SDM De Soto 2006, vía `pvlib`).

### Bug real encontrado y corregido (bloqueaba la comprobación)

Intentando correr la comprobación con el panel real de Urabá (JA Solar JAM66D46-720/LB, sin SDM
precalibrado), `preparar_panel_iv()` devolvía `None` sin ningún error visible. Causa raíz:

- `datos/catalogo_paneles_excel.py` fijaba los alias `Voc_stc`/`Vmp_stc`/`Isc_stc` para cada panel
  del catálogo Excel real, pero **nunca fijaba `Imp_stc`** — pese a que el valor (`Imp`) sí estaba
  disponible en la ficha. Una asimetría real de 3-de-4 en un solo archivo.
- `calculos/modelo_iv.py::validar_sdm_vs_ficha()` accedía a `panel["Imp_stc"]` con **subíndice
  directo** (sin `.get()`), a diferencia del resto de esa misma función (`preparar_panel_iv()` sí
  usa `.get()` con respaldo en otros puntos).
- Resultado: **todo panel del catálogo Excel real sin SDM precalibrado** lanzaba `KeyError` dentro
  de `preparar_panel_iv()`, capturado por un `except (KeyError, ...)` genérico y convertido en
  "datos insuficientes" (`None`) — silenciosamente, sin ningún mensaje al usuario, incluso cuando
  el ajuste SDM habría sido válido.

**Corregido en dos capas** (root cause + hardening del patrón frágil que lo permitió):
1. `datos/catalogo_paneles_excel.py`: se agregó el alias `Imp_stc` que faltaba (mismo patrón que
   los otros 3).
2. `calculos/modelo_iv.py::validar_sdm_vs_ficha()`: los 5 campos (`Voc`/`Isc`/`Vmp`/`Imp`/`Pmax`)
   ahora usan `.get(...) or .get(...)` con respaldo a la clave sin sufijo `_stc`, en vez de
   subíndice directo — evita que la misma clase de bug reaparezca si otra fuente de paneles (ficha
   subida por PDF, catálogo futuro) tampoco fija el alias exacto.

### Segundo hallazgo, real y separado (NO corregido, fuera del código de esta app)

Con el bug de `Imp_stc` corregido, se auditaron los 76 paneles reales del catálogo Excel: **ninguno
de los 76** logra activar el ajuste SDM on-demand (`pvlib.ivtools.sdm.fit_desoto()`) — o bien
`fit_desoto()` no converge, o converge a parámetros que no reproducen la ficha STC dentro de 5%
(y el auto-chequeo de `preparar_panel_iv()`, que ya existía, correctamente rechaza mostrar una
curva inválida). Auditando más a fondo con el panel real de Urabá y con un panel "de libro" (60
celdas, valores típicos): **`fit_desoto()` de pvlib 0.15.2 da resultados NO DETERMINISTAS entre una
corrida y otra en este entorno para los MISMOS parámetros de entrada** — a veces converge
correctamente, a veces falla con un `RuntimeError` de Jacobiano, a veces con un `TypeError` interno
de pvlib ("tuple indices must be integers, not str"). Esto apunta a un problema de la propia
librería `pvlib`/`scipy` en este entorno, no a un bug de esta app — no se investigó más a fondo por
ser una desviación grande de alcance frente a lo pedido ("confírmalo"), y porque el mecanismo de
seguridad ya existente (rechazar cualquier SDM que no reproduzca la ficha) ya protege al usuario:
el síntoma es que Motor IV on-demand no está disponible hoy para paneles reales del catálogo sin
SDM precalibrado, no que muestre un resultado incorrecto.

**Impacto real**: el mensaje "🟢 Datos IV obligatorios completos — Motor IV se activará
automáticamente" en 📐 Dimensionamiento (línea ~444) puede aparecer para un panel que luego, en la
práctica, no logra activar la curva real (sin ningún error explicado al usuario, solo la ausencia
silenciosa del expander "📈 Curva I-V real"). Vale la pena revisarlo en una sesión futura si el
usuario lo prioriza.

### Confirmación de coherencia (lo que sí se pudo completar)

Como ningún panel del catálogo Excel llega a tener un SDM válido hoy, la comprobación se hizo con
**ASP-ST1-T40** — el único panel de esta app con SDM ya calibrado y auditado contra el VBA original
(ver docstring de `validar_sdm_vs_ficha`). Comparación real, determinista (sin `fit_desoto`), N=8
en serie, en las 3 temperaturas de diseño (frío/real/extremo):

| Punto | Voc lineal | Voc SDM | dif. | Vmp lineal | Vmp SDM | dif. |
|---|---|---|---|---|---|---|
| T frío (-5°C) | 1017.4 V | 1039.7 V | +2.2% | 757.8 V | 806.5 V | **+6.4%** |
| T real (36.35°C) | 894.2 V | 885.5 V | -1.0% | 666.0 V | 648.3 V | -2.7% |
| T extremo (41.94°C) | 877.5 V | 864.5 V | -1.5% | 653.6 V | 627.3 V | **-4.0%** |

**Conclusión honesta**: Voc es muy coherente (dentro de ~2.2% en los 3 puntos, como se esperaba —
Voc es casi lineal en T incluso en el modelo físico completo). Vmp diverge más (hasta 6.4% en frío,
4.0% en el extremo caliente) porque el modelo lineal reutiliza el coeficiente de Voc (`Tk_beta`)
también para Vmp — una aproximación aceptada explícitamente por el usuario al descartar la Fase 2
(modelo Faiman de 2 parámetros completo) en el plan del modelo térmico. El sesgo tiene dirección:
en el punto más crítico para el gate de compatibilidad (calor extremo, el que decide
compatible/incompatible en casos reales como Urabá), **el modelo lineal SOBREESTIMA Vmp ~4%
respecto al SDM real** — un margen que hoy queda cubierto por el umbral de alerta del 7.5% que ya
usa `evaluar_compatibilidad_string()`, pero es una limitación real y ahora cuantificada, no solo
teórica.

**Cobertura**: nuevo archivo `tests/test_modelo_iv.py` (`calculos/modelo_iv.py` no tenía tests
directos hasta hoy) — 5 tests: 2 anclan el fix de `Imp_stc` (uno contra el catálogo Excel real
completo, uno aislando el `KeyError` sin invocar `fit_desoto`), 3 parametrizados anclan la
coherencia lineal-vs-SDM de ASP-ST1-T40 con los márgenes de arriba. Suite completa: **802/802**
(verificada 3 veces seguidas para confirmar que los tests nuevos son deterministas).

## Cuarta actualización (30 de agosto de 2026, mismo día): investigación de fit_desoto — 2 bugs reales más, corregidos

El usuario pidió "investiga por qué falla fit_desoto para paneles reales", siguiendo el hallazgo
separado de la actualización anterior. Investigación completa, con dos resultados reales:

### 1. Causa raíz de la no-convergencia de `fit_desoto()` (entendida, NO corregible desde esta app)

`pvlib.ivtools.sdm.fit_desoto()` resuelve un sistema de 5 ecuaciones no lineales (I_L, I_o, R_s,
R_sh, a_ref) con `scipy.optimize.root(method='hybr')` — un método tipo Newton (MINPACK hybrd) sin
escalar, con jacobiano por diferencias finitas. Los 5 parámetros del SDM abarcan magnitudes muy
distintas para un panel real moderno de alta potencia (para el panel de Urabá: I_o≈2×10⁻¹⁴,
I_L≈18.6, R_s≈0.09, R_sh≈185, a_ref≈1.8 — **16 órdenes de magnitud entre el más pequeño y el más
grande**). Confirmado experimentalmente: pasando un `init_guess` explícito y fijo, el solver falla
de forma **reproducible y determinista** (mismo `RuntimeError` de "Jacobiano sin progreso" en 4/4
corridas) — no es ruido aleatorio, es un sistema genuinamente mal condicionado para este método en
esta combinación de magnitudes. Esta es una debilidad ya conocida en la comunidad de `pvlib` del
método clásico De Soto con módulos modernos de alta corriente/muchas celdas — no un bug de esta
app, y no corregible sin reimplementar el solver (ej. ajustar en espacio logarítmico para I_o, o
usar un optimizador con escalado explícito) — desproporcionado frente a la alternativa encontrada
abajo.

### 2. Alternativa robusta encontrada y adoptada: `fit_desoto_batzelis()`

El mismo `pvlib` incluye un método **cerrado** (Batzelis 2017, vía Lambert W, sin iteración —
no puede fallar por no-convergencia) en el mismo módulo. Probado contra los 76 paneles reales del
catálogo: reproduce Voc/Vmp/Isc/Imp/Pmax de la ficha STC dentro del margen de validación existente
del 5% en la gran mayoría de los casos. **Implementado como segundo escalón** en
`calculos/modelo_iv.py::estimar_sdm_desde_ficha()`: se intenta `fit_desoto()` primero (si converge,
sin cambios); si falla, se intenta `fit_desoto_batzelis()`; si también falla, cae al heurístico
tosco que ya existía (último recurso).

### 3. Segundo bug real, más grave, encontrado investigando el primero: unidades de `a_ref`

Con el respaldo Batzelis funcionando de forma aislada (confirmado con `pvlib.pvsystem.singlediode`
directamente), el resultado END-TO-END dentro de la app seguía siendo un desastre: Voc calculado
≈1.26 V en vez de 49 V — el MISMO patrón de colapso ~39× que ya se había visto con el heurístico
original y que antes se había atribuido, incorrectamente, solo a que "el heurístico es tosco".
Causa real: **`estimar_sdm_desde_ficha()` devuelve `a_ref` en VOLTIOS** (la convención nativa de
`pvlib` — así lo entregan `fit_desoto()`/`fit_desoto_batzelis()`, y así lo necesita la fórmula
heurística interna `exp(-Voc/a_ref)`), pero **`calculos/modelo_iv.py::trasladar_parametros_gt()` y
`calculos/produccion_iv.py::_pmp_iv_vectorizado()` esperan la convención UNITLESS** (n × Ns) que usa
el único panel precalibrado a mano de esta app (`ASP-ST1-T40` en `datos/tecnologias_bipv.py`,
`a_ref=154.0`) — ambas funciones multiplican por `Vt_ref` (0.0257 V) ellas mismas para convertir a
voltios. Devolver un valor ya-en-voltios lo convertía **dos veces**, encogiendo `nNsVth` ~39×
(≈1/`Vt_ref`) y colapsando Voc.

**Impacto real, más allá de hoy**: este bug afectaba a **cualquier panel estimado on-demand desde
que `estimar_sdm_desde_ficha()` existe** — no solo a los que fallaban por `fit_desoto`/`Imp_stc`.
Ningún test existente lo detectó porque los tests de `test_ns_halfcut_nsa.py` solo comparaban la
**fórmula interna** de `a_ref` contra un valor esperado (que coincidía con el bug, no con lo
correcto), nunca la física reproducida corriente abajo. También afectaba silenciosamente el modo
real de curva IV de 📊 Producción (`calculos/produccion_iv.py::_pmp_iv_vectorizado()`, cero tests
directos) — verificado manualmente tras el fix: para el panel real de Urabá a G=1000 W/m²,
T=45°C, Pmp calculado = 679.2 W, coincide con el derate térmico esperado (720 W × (1 − 0.29%×20°C)
≈ 678.2 W) — antes del fix habría dado un valor colapsado sin sentido físico.

**Corregido**: `estimar_sdm_desde_ficha()` ahora convierte `a_ref` a la convención unitless
(÷ `Vt_ref`) antes de devolverlo, sin tocar `trasladar_parametros_gt()`/`_pmp_iv_vectorizado()`
(ya correctas para esa convención) ni el panel precalibrado `ASP-ST1-T40` (ya en esa convención).

### Resultado final medido

| | Antes de hoy | Después de los 4 fixes de esta sesión |
|---|---|---|
| Paneles reales del catálogo (76) que activan Motor IV | **0** | **62** (55 vía Batzelis + 7 ya precalibrados) |
| Voc reproducido para el panel real de Urabá | colapsado (~1.3–1.6 V) | 48.96 V (ficha: 49.0 V, error 0.09%) |

**Cobertura**: 3 tests nuevos en `test_modelo_iv.py` (unidades de `a_ref` en rango unitless
esperado; panel real de Urabá activa Motor IV end-to-end; ≥50/76 del catálogo real activa Motor
IV — umbral conservador) + 2 tests existentes en `test_ns_halfcut_nsa.py` reescritos (antes
comparaban la fórmula interna de `a_ref`, ahora comparan que `validar_sdm_vs_ficha()` reproduce la
ficha STC — más robusto y es justo el tipo de comprobación que habría atrapado este bug antes).
Suite completa: **805/805**.

## Quinta actualización (31 de agosto de 2026): N_s estimado para la familia Solar First

Siguiendo la auditoría de "qué más del catálogo quedó afectado", el usuario pidió agregar N_s a los
paneles reales que lo necesitaran para activar Motor IV. Antes de escribir nada se encontró un
conflicto real: los 10 paneles Solar First (ST1-16/24/32/40/48/56/64/72, ST2-80/85) ya tenían una
decisión explícita documentada en su propio campo `Notas` de una sesión anterior — *"Ns (celdas en
serie) no especificado en la ficha -- no se infiere"* — la misma política de rigor aplicada ahí para
no cargar coeficientes de temperatura no oficiales de esa misma ficha. Se confirmó de nuevo con el
PDF real (`Ficha_Tecnica_SolarFirst_ST1_ST2_Serie.pdf`) que el fabricante genuinamente no publica
ese dato en ningún lado.

Presentado el conflicto al usuario, decidió explícitamente: **sí estimar un N_s razonable y
guardarlo, claramente marcado como estimado**.

**Método de estimación (real, no arbitrario)**: el propio panel de referencia ya validado de esta
app (SolTech ASP-ST1-T40, usado en Teusaquillo) **tampoco** tiene un campo `N_s` — su SDM se
calibró directamente sin necesitarlo (`a_ref=154.0`, sin depender de un conteo de celdas). Se derivó
N_s para la familia ST1 de ese mismo `a_ref` validado (`154 / n_típico_CdTe(1.09) ≈ 141`), justificado
porque ST1 comparte con ASP-ST1-T40 las mismas dimensiones físicas (1200×600mm) y el mismo Voc
(~116V) — fuerte evidencia de la misma tecnología de escriba láser CdTe. Para ST2 (mismas
dimensiones, pero Voc ~59V, casi exactamente la mitad del de ST1) se usó la mitad: N_s≈72.

**Importante**: esta estimación de N_s en realidad no determina si Motor IV activa o no — el método
que efectivamente termina calibrando estos paneles es `fit_desoto_batzelis()` (agregado en la
actualización anterior), que **no necesita N_s en absoluto**. N_s solo se necesitaba para pasar la
puerta de entrada de `preparar_panel_iv()` (`tiene_ficha and tiene_ns`) y, como último recurso, para
el heurístico tosco si ambos ajustes fallaran — ninguno de los dos casos ocurrió aquí.

**Guardado en el Excel real** (`datos/paneles_catalogo.xlsx`, vía `guardar_panel_excel(...,
merge_conservador=True)` para no tocar ningún otro campo): columnas `Ns (Celdas Serie)` y
`NsA = n × Ns` con los valores estimados; `Confianza` cambiada a `"Estimado -- no confirmado por
fabricante"` (antes vacía); `Fuente NsA` a `"Estimado por analogía con ASP-ST1-T40 (ver Notas)"`;
y la frase de `Notas` que decía "no se infiere" reemplazada por la explicación completa del método,
dejando explícito que es un dato estimado y qué hacer si se consigue el dato real del fabricante.

**Resultado medido**: de 76 paneles reales, **72/76 ahora activan Motor IV** (65 vía
`fit_desoto_batzelis` + 7 precalibrados), subiendo desde 62/76. Los 4 que siguen sin activarlo no
tienen relación con N_s: 2 con ficha electrica genuinamente incompleta (`ASP-LAM3-T0
(1200x1200mm)`, `PERC half Cut Bifacial ESM` — falta Voc/Vmp/Isc/Imp por completo) y 2 con el caso
límite de Rsh negativo de Batzelis ya documentado (`EINNOVA ESM-620M`, `EINNOVA Agri ESM-305HE`).

**Cobertura**: 1 test nuevo (`test_solar_first_activa_motor_iv_con_ns_estimado`) verifica los 10
paneles reales activan Motor IV y reproducen su ficha STC dentro del 5%, y que `confianza` declara
explícitamente que el dato es estimado. Umbral del test de catálogo completo subido de ≥50 a ≥65.
Suite completa: **806/806**.

## Nota aparte (no corregida, fuera de alcance)

Se detectó que el checkbox "Incluir sección Dimensionamiento" (`key="rep_inc_dim"`) del Reporte PDF
no se referencia en ningún lugar dentro de `generar_html_reporte()` — parece ser un control de UI
sin efecto. La nueva sección de compatibilidad eléctrica se activa independientemente de ese
checkbox, con su propio gate (`N_serie`/`panel_dict`/`inversor_dict_dim`). No se corrigió por estar
fuera del alcance de esta tarea.
