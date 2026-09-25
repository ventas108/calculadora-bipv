# Manual de uso — Página 9 🗺️ Vista 3D y Multi-Superficie

Versión: 25-sep-2026 (rev. 5) · Código de referencia: `main` con los PR #45 a
#48 (desplegados el 24 y 25-sep-2026).

> 💡 **Cómo leer este manual:** los recuadros amarillos **«💡 Explicación»**
> aclaran dudas reales que surgieron al probar la página en producción. Si algo
> no se comporta como esperas, busca primero el recuadro de ese paso. El
> **Anexo A** trae un ejercicio completo, con valores, para verificar la página
> de principio a fin.

---

## 0. Novedades de esta versión (24-sep-2026)

| Cambio | Qué ves ahora | Antes |
|---|---|---|
| **Vigencia de la POA** | Si cambias la geometría, el montaje, el albedo, el bifacial, el TMY o la ubicación, la superficie sale en **⚠️ Estas superficies no tienen POA vigente…** y no se usa hasta recalcular | Se seguía usando la POA de la geometría anterior sin aviso |
| **Publicación única de la energía** | Los tres botones publican juntos total, desglose, área y POA con su **origen**; reemplazar otro origen pide **confirmación** | «Ganaba el último botón» y el bypass cambiaba solo el total |
| **Puntos 3D** | Acepta `x,y,z` y `x;y;z` (coma decimal); una línea mal escrita sale en rojo y bloquea el cálculo; aviso de punto dentro del volumen antes de calcular | Las líneas mal escritas se perdían en silencio |
| **Estado de la sombra** | Tabla **Estado de la sombra por superficie** con 🟢/🔴/⚪, motivo y qué hacer | No se veía; además el resultado de «🌳 Calcular sombra» **se perdía** al calcular |
| **Panel y strings del proyecto** | Bypass y MPPT arrancan con **Panel del proyecto (…)** y el N serie × N paralelo de cada superficie | Arrancaban con *ASP-ST1-T40* y 8 módulos en serie |
| **Mapa de calor POA** | Funciona con POA por superficie | Se caía con «The truth value of a DataFrame is ambiguous» |
| **Sombra v2** | Las horas con el sol detrás del módulo no cuentan como sombra | Se contaba sombra total en esas horas |
| **Formato de strings** | Leyendas y tablas del bypass y del MPPT dicen siempre «8 serie × 17 paralelo» | La leyenda decía «17×8s» y la tabla «8 × 17» |
| **Editor de superficies** | Tilt, azimuth, área, nombre, tipo, montaje y «Activa» conservan el valor escrito y el encabezado de la superficie se actualiza al instante | El campo se recreaba al editar: el valor tardaba en aparecer o volvía al anterior, y el encabezado mostraba el valor previo |

🚩 **Después de esta actualización, en tus proyectos:**

1. Presiona **⚡ Calcular POA para todas las superficies**.
2. Presiona **🌳 Calcular sombra de todas las superficies** (antes no quedaba
   guardada).
3. Si usabas el bypass por superficie, vuelve a calcularlo: ahora usa el
   panel y los strings del proyecto.
4. Vuelve a publicar la energía con el botón que elijas: si el banner dice
   **origen desconocido**, es energía de la versión anterior.

---

## 1. Para qué sirve y cuándo usarla

| Situación | ¿Usar Vista 3D? |
|---|---|
| Proyecto con **una sola superficie** (una fachada o un techo) | Solo para visualizar. El cálculo oficial va por Dimensionamiento → Producción |
| Proyecto con **varias superficies** de distinta orientación (fachada + techo + pérgola + marquesina) | **Sí.** Aquí se calcula la POA de cada una y la energía combinada que llega a Financiero, Baterías y CO₂ |
| Sombra 3D real de edificios u objetos cercanos por superficie | Sí, con una escena de Site Designer |
| Decidir cuántos MPPT necesita el inversor | Sí, en la sección 6 de Producción por Superficie (informativa) |

## 2. Requisitos previos (en este orden)

1. **🏠 Proyecto:** ciudad y coordenadas del predio. Sin ciudad, la página se
   detiene con un aviso.
2. **☀️ Recurso Solar:** calcula el recurso para tener el **TMY** (8.760 horas).
   Sin TMY no puedes calcular la POA por superficie, la sombra 3D, el bypass
   ni el modo físico.
3. **📐 Dimensionamiento:** panel e inversor. Si el panel no pasó la
   validación del modelo SDM (Motor IV), Vista 3D muestra una alarma roja 🔴
   al abrir: corrígela antes, porque bypass y MPPT usan ese mismo modelo.
4. **🔀 Mismatch (opcional):** el perfil de horizonte y el CSV de sombreado.
   Se usan en el bypass por superficie (sección 5) y en la Trayectoria Solar.

El panel superior de la página confirma ciudad, coordenadas, orientación y si
el Recurso Solar está ✅ calculado o ⚠️ pendiente.

## 3. Cómo está organizada la página

**Geometría del edificio** (arriba): ancho, profundidad, pisos y altura.
⚠️ Son **solo visuales**: no afectan producción ni finanzas.

Debajo hay **3 pestañas principales**:

| Pestaña | Contenido |
|---|---|
| 🗺️ Mapa del Sitio | Mapa 3D geolocalizado del edificio, la fachada activa y su orientación |
| 🏗️ Modelo 3D con Paneles | Modelo de la fachada principal con paneles, rayo solar por mes y POA mensual. En tipo *Granja fotovoltaica* muestra la granja agrivoltaica |
| 🌞 Diagrama Solar | **Aquí está todo el sistema Multi-Superficie** (4 sub-pestañas) |

> 🚩 **Error común:** buscar las superficies múltiples en las dos primeras
> pestañas. Están dentro de **🌞 Diagrama Solar**, en sus 4 sub-pestañas:
> **⚙️ Superficies BIPV · 🎨 Vista 3D Multi-Superficie ·
> 📊 Producción por Superficie · 🌞 Trayectoria Solar.**

---

## 4. Flujo recomendado paso a paso (multi-superficie)

### Paso 1 · Definir superficies (⚙️ Superficies BIPV)

- Agrega con los botones rápidos **🏢 Fachada · 🏠 Techo · 🌿 Pérgola ·
  🏪 Marquesina**. La primera vez aparece la "Fachada principal" con el azimut
  y el área del proyecto.
- En cada superficie ajusta **Nombre, Tipo, Tilt, Azimuth, Área y Activa**.

| Tipo | Tilt por defecto | Rango de tilt permitido |
|---|---|---|
| 🏢 Fachada | 90° | 70–90° |
| 🏠 Techo | 10° | 0–45° |
| 🌿 Pérgola | 5° | 0–20° |
| 🏪 Marquesina | 20° | 5–45° |

- **Azimuth:** 0 = Norte · 90 = Este · 180 = Sur · 270 = Oeste.
- **Superficies con tilt ≥ 80° (fachadas):** aparece el selector
  **🔄 Montaje de la fachada** (Heredar / Adosada / Ventilada). Marca
  *Ventilada* **solo** si existen de verdad la cámara de aire y la superficie
  reflejante detrás; si no, inflas la producción.
- **Desactivar vs eliminar:** desmarca *Activa* para excluir temporalmente una
  superficie sin perder sus datos; 🗑️ la elimina.

### Paso 2 · Sombra 3D por superficie (opcional, necesaria para el modo físico)

1. En Site Designer usa **File → Save Model File** y carga el `.json` en
   **Escena Site Designer**. Revisa el mensaje verde con el número de bloques y
   las dimensiones.
   - ⚠️ Si aparece *"La ubicación del archivo … NO coincide con la del
     proyecto"*, es la escena de otro sitio: no continúes.
2. Para **cada superficie activa**, escribe los **puntos 3D** en su recuadro,
   uno por línea, en metros. Dos formatos válidos:
   ```
   8.5,0,2      ← coma entre valores, punto decimal
   8,5;0;2      ← punto y coma entre valores, coma decimal
   ```
   Los puntos quedan ligados a la superficie aunque la renombres.

> 💡 **Explicación — el texto gris no son puntos.** Cuando el recuadro está
> vacío muestra en gris un **ejemplo de formato** («8,0,2 / 8,0,3.5 /
> 8;0;5,5»). No son puntos reales: por eso la tabla de estado dice
> «Puntos: 0». Haz clic dentro, escribe tus propios puntos y **haz clic fuera
> del recuadro (o pulsa Ctrl+Enter)**: Streamlit solo aplica el texto cuando
> sales del recuadro.

> 💡 **Explicación — por qué «8,5,0,2» es un error.** Con comas, la app lee
> cuatro números (8 / 5 / 0 / 2) y no puede adivinar cuál es el decimal. Si
> usas coma decimal, separa los valores con punto y coma: **8,5;0;2**. Si usas
> punto decimal, separa con comas: **8.5,0,2**. La línea con error se queda
> escrita y marcada en rojo hasta que la corrijas.
   - Ejes: **X = Este, Y = Norte (verdadero), Z = altura.**
   - Coloca cada punto **sobre la superficie de módulos, 20–50 cm por delante
     del muro o cubierta**, nunca dentro del volumen del edificio. Un punto
     dentro de un sólido o a **menos de 10 cm** de la malla deja la superficie
     en estado **error geométrico**.
   - Usa **al menos un punto por fila de módulos** en cada superficie.
   - Si la escena tiene un giro de norte (`northOffset`) distinto de 0, las
     coordenadas que ves en Site Designer están giradas: los puntos deben ir en
     ejes reales (Norte verdadero).

> 💡 **Explicación — cómo saber dónde está cada obstáculo.** El mensaje verde
> («Malla Site Designer cargada: 1 bloque(s), 4.56 × 3.69 × 10.0 m») da el
> **tamaño** de la escena, no su **ubicación**. Para ubicar un bloque abre el
> `.json` con el Bloc de notas y busca `"Blocks"`: cada bloque trae `"min"` y
> `"max"` en **milímetros** (divide entre 1000 para pasar a metros). La app
> además gira la escena el ángulo `"northOffset"` para llevarla a Norte
> verdadero, así que las coordenadas finales cambian un poco. El **Anexo A**
> muestra un ejemplo resuelto.
   - Una línea mal escrita (por ejemplo `8,5,0,2`, `8,0` o `8,a,2`) aparece
     en **rojo** con su número de línea y el motivo, y **bloquea el cálculo**
     hasta que la corrijas. Nunca se descarta en silencio.
   - Con la escena cargada, la página avisa **antes de calcular** si un punto
     está dentro del volumen o a menos de 10 cm de la malla.

> 💡 **Explicación — los avisos amarillos no bloquean el botón.** «El punto …
> está DENTRO del modelo» o «…está a 3 cm de la malla» son advertencias
> previas: puedes calcular igual, pero esa superficie saldrá en 🔴
> *error_geometrico* y la tabla dirá qué punto está mal. Las **líneas en rojo**
> (mal escritas) sí bloquean el botón.
3. Presiona **🌳 Calcular sombra de todas las superficies**. El botón solo se
   habilita con malla, TMY, sin líneas con error y al menos un punto en cada
   superficie activa; si no, un aviso dice qué falta.
4. Revisa la tabla **Estado de la sombra por superficie** (siempre visible).
   Usa las mismas reglas que el modo físico: una superficie 🟢 no fallará por
   sombra en el modo físico.

| Estado | Significado | Semáforo |
|---|---|---|
| calculado_completo | Sombra calculada en todas las horas con sol | 🟢 |
| sombra_cero_calculada | Calculada y sin ninguna sombra | 🟢 |
| calculo_incompleto | Faltaron horas con sol por calcular | 🔴 |
| error_geometrico | Punto dentro o a menos de 10 cm de la malla (dice cuál) | 🔴 |
| invalidada_tmy | Calculada con otro TMY o ubicación | 🔴 |
| invalidada_version | Calculada con el algoritmo anterior (v1) | 🔴 |
| invalidada_geometria | Cambiaste tilt, azimuth o área (dice cuál) | 🔴 |
| sin_calcular | Todavía no se calculó | ⚪ |

   La columna **Qué hacer** indica la corrección de cada caso.

> 💡 **Explicación — «mi superficie desapareció de la tabla».** La tabla (y el
> recuadro de puntos) solo muestran superficies **activas**. Si una superficie
> desaparece, abre su recuadro en ⚙️ Superficies BIPV y revisa la casilla
> **Activa**: está justo debajo de Tilt, Azimuth y Área y es fácil desmarcarla
> sin querer.

> ℹ️ **Desde el 24-sep-2026 (algoritmo v2)**, las horas en que el sol está
> **detrás** del plano del módulo ya no cuentan como sombra: en esas horas no
> hay haz directo que sombrear. Las sombras guardadas con el algoritmo
> anterior (v1) no se usan en el modo físico: la tabla las muestra como
> *invalidada_version* y hay que recalcularlas con **🌳 Calcular sombra**.
>
> *(Corregido el 24-sep-2026: antes el resultado del cálculo de sombra se
> perdía en el mismo momento de calcular, y el modo físico decía «falta
> p_shade».)*

### Paso 3 · Inversores por superficie

1. **➕ Agregar inversor**: se crea `INV-1`, `INV-2`, etc. Completa **Eficiencia
   (0–1)**, por ejemplo `0.97`, y **Potencia AC (W)**.
2. Para cada superficie activa elige su **Inversor** y escribe **N serie** y
   **N paralelo** (números enteros).
3. El tipo **dedicado** (1 superficie) o **compartido** (2 o más) se calcula
   solo; no se puede escribir a mano.
4. Debe aparecer **✅ Asignaciones válidas**. Si sale
   **⚠️ Configuración eléctrica incompleta**, el mensaje dice qué falta:
   - un inversor sin ID o con el ID repetido;
   - eficiencia vacía, no numérica o fuera de (0, 1];
   - una superficie sin inversor o con un inversor que no existe;
   - N serie o N paralelo inválidos;
   - un inversor sin ninguna superficie asignada.

> ℹ️ El **N serie** y el **N paralelo** de cada superficie se escriben **solo
> aquí**: los usan también el bypass por superficie, el MPPT combinado y el
> modo físico.

### Paso 4 · Calcular la POA de todas las superficies

- Presiona **⚡ Calcular POA para todas las superficies** (requiere TMY).
- Si el proyecto es bifacial, marca o desmarca **🔄 Aplicar modelo bifacial**.
  Techos y pérgolas (tilt < 80°) siempre conservan su ganancia; las fachadas
  siguen su selector de montaje.
- Verás el **📊 Resumen POA por superficie** y la **⚡ Producción total del
  sistema** (con η del panel y PR del sistema).

> 🚩 **La POA vigila su vigencia:** cada POA queda firmada con la geometría
> (tipo, tilt, azimuth, área, montaje), el albedo, el bifacial, el TMY y la
> ubicación. Si cambias algo de eso, la app muestra **⚠️ Estas superficies no
> tienen POA vigente…** con el motivo, omite esa superficie en el resumen, la
> vista 3D, la producción, el bypass y el mapa de calor, y deshabilita
> **🔗 Usar sistema multi-superficie en Financiero** hasta que vuelvas a
> presionar **⚡ Calcular POA**. Renombrar una superficie no invalida su POA.
> Si el cálculo de una superficie falla, el aviso muestra la causa.

### Paso 5 · Llevar la energía a Financiero, Baterías y CO₂

Tres botones publican la energía multi-superficie que usan Financiero,
Baterías y CO₂. Los tres pasan por **una sola publicación** que escribe juntos
el total, el desglose por superficie, el área y la POA ponderada, y registra
el **origen**:

| Botón | Dónde | Origen que publica |
|---|---|---|
| 🔗 **Usar sistema multi-superficie en Financiero** | ⚙️ Superficies BIPV | Simplificado: POA × área × η × PR |
| ⚡ **Calcular bypass por superficie** | 📊 Producción por Superficie › 5 | Bypass por superficie con el CSV de 🔀 Mismatch |
| ✅ **Adoptar cálculo físico** | ⚙️ Superficies BIPV › modo físico | Modelo físico SDM + bypass + inversores |

- El banner **✅ Modo multi-superficie activo** muestra el **origen**, la E_ac
  y el área. En origen físico muestra también el **recorte en buses de
  inversor** (suma del desglose por superficie − total de los buses).
- Si ya hay energía de **otro origen**, el botón no la reemplaza en silencio:
  pregunta *¿Reemplazarla por…?* con **✅ Sí, reemplazar** o **✖ Cancelar**.
  Al confirmar, la app vuelve a calcular con los datos actuales (el físico se
  revalida completo).
- Si el banner dice **origen desconocido**, la energía viene de una sesión
  anterior a esta versión: vuelve a publicarla antes de guardar el proyecto.
- **✖ Desactivar modo multi-superficie** retira toda la publicación y devuelve
  Financiero, Baterías y CO₂ a la energía de superficie única. Publicar un
  origen no físico también retira el proyecto físico: un proyecto guardado
  nunca mezcla el proyecto físico con energía de otro origen.

> 💡 **Explicación — dónde está el banner del origen.** El banner verde
> «✅ Modo multi-superficie activo — origen: …» está en **⚙️ Superficies BIPV ›
> 🔗 Integrar al análisis financiero**, a la derecha del botón «Usar sistema
> multi-superficie en Financiero». La sección del bypass (📊 Producción por
> Superficie › 5) repite el origen y el botón «✖ Desactivar» para que no
> tengas que cambiar de sub-pestaña.

> 💡 **Explicación — «no veo el botón Calcular bypass por superficie».** El
> bypass necesita el **CSV de sombreado** cargado en **🔀 Mismatch › Sección 5**.
> Sin él, la sección 5 solo muestra el aviso «Carga el CSV de sombreado…». Si
> el CSV no tiene columna *Fachada*, el bypass usa el promedio del CSV para
> todas las superficies («— promedio —» en la tabla).

### Paso 6 · Modo físico (opcional, recomendado para validar)

1. Marca **🧪 Preparar comparación con modelo físico SDM + bypass**.
2. Revisa el aviso **"X/Y superficies activas listas"**. Cada superficie activa
   necesita **N serie, N paralelo, inversor, p_shade y firma de sombra**
   (pasos 2 y 3).
3. Presiona **🧪 Calcular comparación física (sin adoptar)**. Si todo está
   vigente, verás *"simplificado … · físico … · diferencia …%"*. Esto **no**
   cambia nada todavía.
4. Si la comparación te convence, presiona **✅ Adoptar cálculo físico**. La app
   **revalida todo de nuevo**; si algo cambió desde la comparación, rechaza la
   adopción y te dice por qué. Si ya hay energía publicada de otro origen,
   primero pregunta *¿Reemplazarla por…?*; al confirmar vuelve a revalidar.
   El banner queda con origen **físico** y muestra el recorte en buses de
   inversor.
5. Nunca completes datos faltantes con valores inventados (por ejemplo,
   `p_shade = 0` "para que pase"): el bloqueo existe para impedir resultados
   falsos.

---

## 5. Sub-pestaña 🎨 Vista 3D Multi-Superficie

- Visualiza todas las superficies activas sobre el edificio.
- **Colorear por:** *POA mensual* (azul → rojo) o *FS del CSV* (verde libre
  < 10 % · naranja parcial 10–35 % · rojo bypass > 35 %). Sin CSV cargado usa
  la POA.
- Controles: Mes, Vista (Perspectiva / Fachada / Planta / Lateral), Opacidad,
  Cuadrícula de paneles y Etiquetas.
- Solo usa POA **vigentes**. Una superficie sin POA vigente aparece en el
  aviso ⚠️ y se colorea con una estimación desde la irradiancia global (no con
  su POA anterior); en la tabla del mes figura con 0.

## 6. Sub-pestaña 📊 Producción por Superficie

Requiere la POA del paso 4. Solo usa POA **vigentes**: las superficies sin
POA vigente aparecen en el aviso ⚠️ y se omiten de las gráficas; el bypass no
calcula hasta que todas las superficies activas tengan POA vigente.

1. **Producción mensual** en barras apiladas por superficie.
2. **Recurso solar anual** por orientación.
3. **Resumen anual:** superficies activas, área total, E_ac total y densidad.
4. **Factor de sombreado por superficie (CSV):** si el CSV de 🔀 Mismatch
   tiene columna *Fachada*, asigna qué fachada del CSV corresponde a cada
   superficie.
5. **⚡ Bypass diodes por superficie:** requiere el CSV de 🔀 Mismatch
   (sección 5).
   - **Panel fotovoltaico:** por defecto *Panel del proyecto (…)* de
     📐 Dimensionamiento, aunque no esté en el catálogo, si tiene ficha SDM
     completa. Si no hay panel del proyecto o no tiene SDM, elige uno del
     catálogo (el botón queda deshabilitado hasta elegirlo). Otro panel queda
     marcado en los resultados.
   - **Strings:** cada superficie usa su N serie × N paralelo del paso 3. Si
     faltan, usa el N serie de Dimensionamiento y estima el paralelo por área,
     con aviso. Los strings se muestran siempre como «8 serie × 17
     paralelo». La tabla muestra *Panel usado*, *N serie × paralelo* y
     *Origen strings*.
   - Necesita POA vigente en todas las superficies activas. Si una superficie
     falla, **no publica nada** y muestra la causa.
   - Publica con origen *bypass por superficie*; si la energía vigente es de
     otro origen, pide confirmación (ver paso 5).
   - Bajo la tabla, cuando su origen es el vigente, dice **✅ Activo en
     Financiero · Baterías · CO₂ — origen: bypass por superficie con CSV de
     sombreado** y trae el botón **✖ Desactivar modo multi-superficie**, el
     mismo del banner de ⚙️ Superficies BIPV. Si la energía vigente es de otro
     origen, dice *Resultado calculado, no publicado* y el origen vigente.
6. **🔀 Strings de distinta orientación en un mismo MPPT:** es **informativa**
   y no cambia la energía oficial. Usa el mismo panel y los mismos strings por
   defecto que el bypass. Asigna superficies a MPPTs y presiona
   **🔀 Simular curva IV combinada por MPPT**. El resultado indica el **panel
   usado** (y si es distinto al del proyecto) y los strings de cada superficie
   con su origen. Semáforo:
   - 🟢 menos de 0,5 %: compartir el MPPT es aceptable;
   - 🟠 entre 0,5 % y 2 %: evalúa si el ahorro del inversor lo compensa;
   - 🔴 más de 2 %: conviene un MPPT por orientación.

> 💡 **Explicación — cómo leer «8 serie × 17 paralelo».** Significa **8
> módulos en serie por string** y **17 strings en paralelo** (8 × 17 = 136
> módulos). Si el origen dice «N serie de Dimensionamiento, paralelo por
> área», es una **estimación**: la superficie todavía no tiene N serie y N
> paralelo propios. Escríbelos en ⚙️ Superficies BIPV › Inversores por
> superficie y el origen cambiará a «configurado en la superficie».

## 7. Sub-pestaña 🌞 Trayectoria Solar

1. **Trayectoria solar** (azimut vs elevación) con el perfil de horizonte de
   🔀 Mismatch.
2. **Horas productivas vs sombreadas** (24 h × 12 meses) por superficie. Cada
   hora se clasifica como productiva, sombreada (por el horizonte), **sin vista
   de la fachada** (sol detrás del plano, AOI ≥ 90°) o nocturna. Las horas
   productivas siempre son las de la superficie elegida; los **colores** dicen
   de dónde salen:
   - con POA **vigente** de la superficie: nota «Valores: POA vigente de esta
     superficie»;
   - sin POA vigente: aviso ⚠️ con el motivo, y los colores usan la POA
     general de ☀️ Recurso Solar (orientación del proyecto);
   - sin ninguna POA: aviso ⚠️ de estimación fija de 300 W/m².
   Recalcula con **⚡ Calcular POA** para ver la POA real de la superficie.
   *(Corregido el 24-sep-2026: antes esta sección se caía con "The truth value
   of a DataFrame is ambiguous".)*
3. **Métricas de sombras:** compara el % de horas sombreadas (trayectoria
   solar) con el % de energía perdida (🔀 Mismatch). Una diferencia menor de
   2 pp es normal, porque miden cosas distintas.
4. **AOI promedio mensual** con semáforo (< 40° excelente, < 60° aceptable) y
   dos recomendaciones de orientación:
   - 🧭 **Mejor incidencia:** es geométrica, solo como guía.
   - ⚡ **Máxima energía real con TMY:** es la recomendación de captación que
     vale.

> Esta sección usa el **horizonte de 🔀 Mismatch**, no la escena de Site
> Designer. Son dos fuentes de sombra distintas; que no coincidan no
> significa un error.

> 💡 **Explicación — «el mapa sale vacío de mayo a julio».** Es correcto en
> Colombia. A la latitud de Bogotá (4,7° N) el sol pasa **al norte** a mitad de
> año, así que una fachada mirando al **sur** (azimuth 180°) no lo ve de mayo a
> julio: esas horas son «sin vista de la fachada». El gráfico de AOI lo
> confirma con «–» en esos meses. Una fachada norte tendría el patrón opuesto,
> y un techo casi horizontal produce todo el año.

> 💡 **Explicación — de dónde salen los colores del mapa.** Las **horas**
> productivas siempre son las de la superficie elegida. Los **colores** solo
> son su POA real si la superficie tiene POA vigente (nota «Valores: POA
> vigente de esta superficie»). Si cambiaste el tilt, el azimuth o el área sin
> recalcular, sale un aviso ⚠️ y los colores usan la POA general del proyecto:
> pulsa **⚡ Calcular POA** para verla bien.

---

## 8. Guardar y cargar un proyecto con varias superficies

- El estado multi-superficie (superficies, inversores, energía publicada y su
  origen) se guarda con el proyecto **solo si hay energía publicada** (banner
  ✅ activo). Publica antes de guardar si quieres conservar las superficies.
- El **proyecto físico** solo se guarda si el origen vigente es **físico**.
- Al cargar el proyecto, el estado multi-superficie se restaura cuando pasas
  por **☀️ Recurso Solar** con el TMY: verás *📂 Estado multi-superficie
  restaurado…* o, si el TMY o las firmas no coinciden, *…rechazado* con el
  motivo.
- La **POA por superficie no se guarda**: al abrir el proyecto aparece como
  «POA sin calcular»; presiona **⚡ Calcular POA**.
- Los **puntos 3D** se conservan y siguen ligados a su superficie.
- Proyectos guardados antes del 24-sep-2026: si traían proyecto físico se
  restauran con origen **físico**; los demás muestran **origen desconocido**
  hasta que vuelvas a publicar.

## 9. Después de actualizar o reiniciar la app

Cada despliegue (`pm2 restart streamlit-bipv`) **reinicia Streamlit** y borra
lo que tenías abierto en el navegador: superficies, POA, sombra y bypass que
no estén guardados en un proyecto.

1. Antes de un despliegue, **guarda el proyecto** si estás trabajando en algo.
2. Después, recarga la página con **Ctrl+F5** e inicia sesión si te lo pide.
3. **Carga el proyecto** y pasa por **☀️ Recurso Solar** (ahí se restaura el
   estado multi-superficie).
4. En Vista 3D pulsa **⚡ Calcular POA**: la POA por superficie no se guarda con
   el proyecto.

> 💡 **Explicación — los campos del editor.** Desde el 25-sep-2026, Nombre,
> Tipo, Tilt, Azimuth, Área, Activa y Montaje conservan lo que escribes y el
> encabezado de la superficie («… · Az 170° · …») se actualiza al instante.
> Si cambias el tipo a uno con otro rango de tilt (por ejemplo Fachada 90° →
> Techo), el tilt se ajusta solo al máximo permitido (45°).

## 10. Lista de verificación antes de ir a Financiero

- [ ] Recurso Solar ✅ y TMY vigente.
- [ ] Todas las superficies reales creadas, con tilt, azimut y área correctos,
      y las que no existen desactivadas.
- [ ] Montaje "Ventilada" solo donde existe físicamente.
- [ ] Ningún aviso **⚠️ Estas superficies no tienen POA vigente…**.
- [ ] Si usas sombra 3D: escena del sitio correcto, puntos fuera del volumen
      (20–50 cm) y todas las superficies en 🟢 en *Estado de la sombra por
      superficie*.
- [ ] Inversores: ✅ Asignaciones válidas, con N serie y N paralelo en cada
      superficie.
- [ ] Bypass y MPPT con **Panel del proyecto (…)** y strings «configurado en
      la superficie» (o una diferencia que elegiste a propósito).
- [ ] El banner ✅ Modo multi-superficie activo muestra el **origen** que
      elegiste (simplificado, bypass con CSV o físico) y la E_ac que esperas.

## 11. Mensajes frecuentes y qué hacer

| Mensaje | Causa | Solución |
|---|---|---|
| ⚠️ Primero configura el proyecto en 🏠 Proyecto… | No hay ciudad | Completa 🏠 Proyecto |
| ℹ️ Primero calcula el Recurso Solar en ☀️ | No hay TMY | Calcula ☀️ Recurso Solar |
| Completa la malla, el TMY y al menos un punto por superficie activa | Falta la escena, el TMY o puntos | Carga el `.json` y escribe puntos en cada superficie activa |
| La ubicación del archivo … NO coincide | La escena es de otro sitio | Exporta la escena correcta |
| ⚠️ Configuración eléctrica incompleta | Falta ID, eficiencia, asignación o N serie/paralelo | Corrige lo que indica el mensaje |
| … no puede entrar al modo físico: falta 'p_shade' (o 'firma_sombra') | La superficie no está en 🟢 en *Estado de la sombra por superficie* | Sigue la columna *Qué hacer* y recalcula con 🌳 Calcular sombra |
| ❌ Líneas con error en … | Un punto 3D mal escrito | Corrige la línea indicada (`x,y,z` o `x;y;z`) |
| ⚠️ El punto … está DENTRO del modelo / a N cm de la malla | Punto dentro del volumen o pegado a la malla | Muévelo 20–50 cm por delante de la superficie |
| ⚠️ El panel del proyecto … no tiene ficha SDM completa | El bypass y el MPPT necesitan el SDM | Elige un panel del catálogo o completa la ficha en 📐 Dimensionamiento |
| … falta 'n_serie' / 'n_paralelo' / 'inversor_id' | Configuración eléctrica de la superficie incompleta | Completa el paso 3 |
| ❌ No se puede calcular el modo físico: … | Otro dato faltante o inválido | Completa lo indicado; no inventes valores |
| ❌ El candidato ya no es válido… | Algo cambió después de comparar | Vuelve a calcular la comparación |
| 🔴 Alarma de validación SDM | El panel no valida contra su ficha | Revisa 📐 Dimensionamiento / Motor IV |
| ⚠️ Estas superficies no tienen POA vigente… | Cambió la geometría, el montaje, el albedo, el bifacial, el TMY o la ubicación, o el cálculo falló | Presiona ⚡ Calcular POA para todas las superficies |
| ⚠️ Financiero, Baterías y CO₂ ya usan energía … ¿Reemplazarla por…? | Hay energía publicada de otro origen | ✅ Sí, reemplazar o ✖ Cancelar |
| ❌ Bypass no publicado; falló en: … | Una superficie no pudo simular el bypass | Corrige la causa y vuelve a calcular |
| ❌ No se publicó / No se calculó: hay superficies activas sin POA vigente | Falta recalcular la POA | Presiona ⚡ Calcular POA para todas las superficies |
| ❌ No se calculó: elige el panel y corrige los strings indicados arriba | Sin panel utilizable o strings sin N serie | Elige un panel y completa N serie/N paralelo en el paso 3 |
| ❌ La superficie … no tiene N serie válido y tampoco hay N serie en 📐 Dimensionamiento | No hay de dónde tomar el N serie | Escribe N serie y N paralelo de esa superficie en el paso 3 |
| ⚠️ '…': strings por estimación | La superficie no tiene N serie o N paralelo propios | Complétalos en el paso 3 para usar los reales |
| ⚠️ Esta energía se publicó con una versión anterior… (origen desconocido) | Energía de antes del 24-sep-2026 | Vuelve a publicarla antes de guardar |
| ⚠️ Se descartaron los puntos de «…»: esa superficie ya no existe | Puntos de una superficie eliminada | Ninguna acción; escribe los puntos de las superficies actuales |
| Para calcular la sombra: … | Falta escena, TMY, corregir líneas o puntos | Haz lo que indica el aviso |
| 📂 Estado multi-superficie rechazado… | El TMY o las firmas del proyecto guardado no coinciden | Recalcula POA, sombra y vuelve a publicar |

---

## Anexo A. Ejercicio completo de verificación (con valores)

Este ejercicio es el que se usó el 24 y 25-sep-2026 para validar la página en
producción. Sirve para comprobar que todo funciona después de una
actualización. Tarda unos 30 minutos.

### A.1 Preparación
1. Carga un proyecto con **🏠 Proyecto**, **☀️ Recurso Solar** (TMY) y
   **📐 Dimensionamiento** (panel) calculados.
2. En **⚙️ Superficies BIPV** deja **2 superficies activas**:

| Superficie | Tipo | Tilt | Azimuth | Área |
|---|---|---|---|---|
| Fachada principal | Fachada | 90° | 180° | 97,3 m² |
| Techo 1 | Techo | 10° | 180° | 97,3 m² |

### A.2 Prueba 1 · POA vigente
1. Pulsa **⚡ Calcular POA** → «POA calculada para 2 superficie(s)».
2. Cambia el tilt de la fachada (90 → 75) **sin recalcular** → aviso «⚠️ Estas
   superficies no tienen POA vigente… Fachada principal: cambió la geometría…»,
   el resumen muestra solo el techo y «🔗 Usar sistema multi-superficie» queda
   en gris.
3. Pulsa **⚡ Calcular POA** → vuelven las 2 superficies y el botón se habilita.

> 💡 **Valores de referencia (Bogotá):** fachada sur a 75° ≈ 1.004
> kWh/m²·año; techo a 10° ≈ 1.675 kWh/m²·año. La fachada recibe bastante menos
> porque a esta latitud el sol pasa casi por encima.

### A.3 Prueba 2 · Origen de la energía y confirmación
Requiere el CSV de sombreado en 🔀 Mismatch › Sección 5.
1. **🔗 Usar sistema multi-superficie** → banner con origen **simplificado**.
2. **5. Bypass › ⚡ Calcular bypass por superficie** → pregunta «¿Reemplazarla
   por bypass por superficie con CSV de sombreado?».
3. **✖ Cancelar** → «Resultado calculado, no publicado: Financiero usa energía
   de origen simplificado».
4. Repite y pulsa **✅ Sí, reemplazar** → «✅ Activo en Financiero… — origen:
   bypass por superficie con CSV de sombreado» y el botón **✖ Desactivar**.
5. **✖ Desactivar** → «Resultado calculado, no publicado en Financiero».

### A.4 Prueba 3 · Puntos 3D (con escena de Site Designer)
Escena de ejemplo: un **árbol** modelado como bloque sólido.

```
"northOffset": 7
"Blocks": [ { "min": [900, 200, 0], "max": [5100, 3400, 10000], "isTree": true } ]
```

| Paso | Cálculo | Resultado |
|---|---|---|
| Pasar mm a m | min ÷ 1000, max ÷ 1000 | X 0,9–5,1 m · Y 0,2–3,4 m · Z 0–10 m |
| Girar 7° al Norte verdadero | lo hace la app | X ≈ 0,9–5,5 m · Y ≈ −0,4–3,3 m · Z 0–10 m |

Escribe en los recuadros y haz clic fuera:

| Recuadro | Texto | Resultado esperado |
|---|---|---|
| Fachada principal | `3,6,2` y en otra línea `8,5,0,2` | Línea 2 en rojo; «Calcular sombra» en gris |
| Fachada principal | cambia la línea 2 por `8,5;0;2` | Sin error; 2 puntos |
| Techo 1 | `3.2,1.4,5` | ⚠️ «está DENTRO del modelo» |
| Techo 1 | `3;-0,2;5` | ⚠️ «está a 3 cm de la malla» |

### A.5 Prueba 4 · Estado de la sombra
1. Reemplaza los puntos por posiciones válidas:

| Recuadro | Puntos | Por qué |
|---|---|---|
| Fachada principal | `3,6,2` · `3,6,4` · `3,6,6` | ~2,7 m al norte del árbol, mirando al sur: el árbol le da sombra |
| Techo 1 | `12,12,3` · `14,12,3` | Lejos del árbol |

2. **🌳 Calcular sombra** → tabla: Fachada 🟢 *calculado_completo* (el árbol la
   sombrea ~240 h/año) y Techo 🟢 *sombra_cero_calculada*, con 4.407 horas con
   sol calculadas y calidad alta.
3. Cambia el azimuth del techo (180 → 170) → Techo 🔴 *invalidada_geometria*
   «Se retiró la sombra porque cambió azimuth»; la fachada sigue 🟢.

### A.6 Prueba 5 · Panel y strings del proyecto
En **5. Bypass** y **6. MPPT**:
- El panel por defecto es **«Panel del proyecto (…)»**.
- Los strings dicen **«8 serie × 17 paralelo»** en la leyenda y en las tablas.
- Con 97,3 m² y un módulo de 0,72 m² caben ~135 módulos; con 8 en serie
  salen 17 strings en paralelo.

### A.7 Prueba 6 · Mapa de calor
En **🌞 Trayectoria Solar › 2. Horas productivas vs sombreadas**:
1. **Techo 1** → mapa productivo todo el año (hasta ~800 W/m²) y nota
   «Valores: POA vigente de esta superficie».
2. **Fachada principal** → mayo a julio vacíos (sol al norte) y máximos en
   diciembre y enero.
3. Cambia el tilt de la fachada sin recalcular → aviso ⚠️ «…no tiene POA
   vigente…: los colores usan la POA general de ☀️ Recurso Solar».

### A.8 Cierre
En el servidor:
```
pm2 logs streamlit-bipv --err --lines 20 --nostream
```
Debe salir **vacío**: ninguna prueba produjo errores.
