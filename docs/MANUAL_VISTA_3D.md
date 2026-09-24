# Manual de uso — Página 9 🗺️ Vista 3D y Multi-Superficie

Versión: 24-sep-2026 (rev. 4) · Código de referencia: `main` `72326f2f`
(desplegado el 24-sep-2026).

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
   - Ejes: **X = Este, Y = Norte (verdadero), Z = altura.**
   - Coloca cada punto **sobre la superficie de módulos, 20–50 cm por delante
     del muro o cubierta**, nunca dentro del volumen del edificio. Un punto
     dentro de un sólido o a **menos de 10 cm** de la malla deja la superficie
     en estado **error geométrico**.
   - Usa **al menos un punto por fila de módulos** en cada superficie.
   - Si la escena tiene un giro de norte (`northOffset`) distinto de 0, las
     coordenadas que ves en Site Designer están giradas: los puntos deben ir en
     ejes reales (Norte verdadero).
   - Una línea mal escrita (por ejemplo `8,5,0,2`, `8,0` o `8,a,2`) aparece
     en **rojo** con su número de línea y el motivo, y **bloquea el cálculo**
     hasta que la corrijas. Nunca se descarta en silencio.
   - Con la escena cargada, la página avisa **antes de calcular** si un punto
     está dentro del volumen o a menos de 10 cm de la malla.
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
     con aviso. La tabla muestra *Panel usado*, *N serie × paralelo* y
     *Origen strings*.
   - Necesita POA vigente en todas las superficies activas. Si una superficie
     falla, **no publica nada** y muestra la causa.
   - Publica con origen *bypass por superficie*; si la energía vigente es de
     otro origen, pide confirmación (ver paso 5). La tabla dice **✅ Activo en
     Financiero** solo cuando su origen es el vigente.
6. **🔀 Strings de distinta orientación en un mismo MPPT:** es **informativa**
   y no cambia la energía oficial. Usa el mismo panel y los mismos strings por
   defecto que el bypass. Asigna superficies a MPPTs y presiona
   **🔀 Simular curva IV combinada por MPPT**. El resultado indica el **panel
   usado** (y si es distinto al del proyecto) y los strings de cada superficie
   con su origen. Semáforo:
   - 🟢 menos de 0,5 %: compartir el MPPT es aceptable;
   - 🟠 entre 0,5 % y 2 %: evalúa si el ahorro del inversor lo compensa;
   - 🔴 más de 2 %: conviene un MPPT por orientación.

## 7. Sub-pestaña 🌞 Trayectoria Solar

1. **Trayectoria solar** (azimut vs elevación) con el perfil de horizonte de
   🔀 Mismatch.
2. **Horas productivas vs sombreadas** (24 h × 12 meses) por superficie. Cada
   hora se clasifica como productiva, sombreada (por el horizonte), **sin vista
   de la fachada** (sol detrás del plano, AOI ≥ 90°) o nocturna. Si la
   superficie tiene POA **vigente**, el mapa usa su POA; si no, usa la POA
   general de ☀️ Recurso Solar.
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

## 9. Lista de verificación antes de ir a Financiero

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

## 10. Mensajes frecuentes y qué hacer

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
