# Manual de uso — Página 9 🗺️ Vista 3D y Multi-Superficie

Versión: 24-sep-2026 (rev. 2) · Código de referencia: rama `claude/mejoras-bipv`
(incluye la corrección de sombra con el sol detrás del módulo, algoritmo v2, la
corrección del mapa de calor POA, la vigencia de la POA por superficie y la
publicación única de la energía multi-superficie).

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
   uno por línea, con el formato `x,y,z` en metros:
   ```
   8,0,2
   8,0,3.5
   8,0,5
   ```
   - Ejes: **X = Este, Y = Norte (verdadero), Z = altura.**
   - Coloca cada punto **sobre la superficie de módulos, 20–50 cm por delante
     del muro o cubierta**, nunca dentro del volumen del edificio. Un punto
     dentro de un sólido o a **menos de 10 cm** de la malla deja la superficie
     en estado **error geométrico**.
   - Usa **al menos un punto por fila de módulos** en cada superficie.
   - Si la escena tiene un giro de norte (`northOffset`) distinto de 0, las
     coordenadas que ves en Site Designer están giradas: los puntos deben ir en
     ejes reales (Norte verdadero).
   - ⚠️ Una línea mal escrita (por ejemplo, con 2 números o con letras) **se
     descarta en silencio**. Revisa que el número de líneas coincida con el de
     puntos que querías.
3. Presiona **🌳 Calcular sombra de todas las superficies**. El botón solo se
   habilita con malla, TMY y al menos un punto en cada superficie activa.
4. Resultado: cada superficie válida queda con un factor de sombra horario
   (`p_shade`, 8.760 valores) y su **firma de sombra**. Internamente cada
   superficie recibe un estado:

| Estado interno | Significado | ¿Se conserva la sombra? |
|---|---|---|
| calculado_completo | Sombra calculada en todas las horas con sol | ✅ |
| sombra_cero_calculada | Calculada y sin ninguna sombra | ✅ |
| calculo_incompleto | Faltaron horas con sol por calcular | ❌ se descarta |
| error_geometrico | Punto dentro o a menos de 10 cm de la malla | ❌ se descarta |

> ⚠️ **La página todavía no muestra ese estado por superficie.** Para
> comprobar que la sombra quedó bien, marca **🧪 Preparar comparación con
> modelo físico** (paso 6). Si una superficie aparece con
> *falta `p_shade`* o *falta `firma_sombra`*, su sombra se descartó: revisa
> sus puntos (fuera del volumen, a 20–50 cm) y vuelve a calcular la sombra.

> ℹ️ **Desde el 24-sep-2026 (algoritmo v2)**, las horas en que el sol está
> **detrás** del plano del módulo ya no cuentan como sombra: en esas horas no
> hay haz directo que sombrear. Las sombras guardadas con el algoritmo
> anterior (v1) no se usan en el modo físico: aparecen como *falta `p_shade`*
> y hay que recalcularlas con **🌳 Calcular sombra**.

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
   adopción y te dice por qué.
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

## 6. Sub-pestaña 📊 Producción por Superficie

Requiere la POA del paso 4.

1. **Producción mensual** en barras apiladas por superficie.
2. **Recurso solar anual** por orientación.
3. **Resumen anual:** superficies activas, área total, E_ac total y densidad.
4. **Factor de sombreado por superficie (CSV):** si el CSV de 🔀 Mismatch
   tiene columna *Fachada*, asigna qué fachada del CSV corresponde a cada
   superficie.
5. **⚡ Bypass diodes por superficie:** requiere el CSV de 🔀 Mismatch
   (sección 5).
   - ⚠️ El selector **Panel fotovoltaico** trae por defecto *ASP-ST1-T40*, que
     **no es necesariamente el panel de tu proyecto**: elige el correcto.
   - **N_series** es uno solo para todas las superficies y es independiente
     del "N serie" del paso 3. Pon el mismo valor.
   - Necesita POA vigente en todas las superficies activas. Si una superficie
     falla, **no publica nada** y muestra la causa.
   - Publica con origen *bypass por superficie*; si la energía vigente es de
     otro origen, pide confirmación (ver paso 5). La tabla dice **✅ Activo en
     Financiero** solo cuando su origen es el vigente.
6. **🔀 Strings de distinta orientación en un mismo MPPT:** es **informativa**
   y no cambia la energía oficial. Asigna superficies a MPPTs y presiona
   **🔀 Simular curva IV combinada por MPPT**. Semáforo:
   - 🟢 menos de 0,5 %: compartir el MPPT es aceptable;
   - 🟠 entre 0,5 % y 2 %: evalúa si el ahorro del inversor lo compensa;
   - 🔴 más de 2 %: conviene un MPPT por orientación.

## 7. Sub-pestaña 🌞 Trayectoria Solar

1. **Trayectoria solar** (azimut vs elevación) con el perfil de horizonte de
   🔀 Mismatch.
2. **Horas productivas vs sombreadas** (24 h × 12 meses) por superficie. Cada
   hora se clasifica como productiva, sombreada (por el horizonte), **sin vista
   de la fachada** (sol detrás del plano, AOI ≥ 90°) o nocturna. Con POA por
   superficie calculada, el mapa usa la POA de esa superficie.
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

## 8. Lista de verificación antes de ir a Financiero

- [ ] Recurso Solar ✅ y TMY vigente.
- [ ] Todas las superficies reales creadas, con tilt, azimut y área correctos,
      y las que no existen desactivadas.
- [ ] Montaje "Ventilada" solo donde existe físicamente.
- [ ] Ningún aviso **⚠️ Estas superficies no tienen POA vigente…**.
- [ ] Si usas sombra 3D: escena del sitio correcto, puntos fuera del volumen
      (20–50 cm) y, en 🧪 Preparar comparación con modelo físico, ninguna
      superficie con *falta `p_shade`*.
- [ ] Inversores: ✅ Asignaciones válidas.
- [ ] El banner ✅ Modo multi-superficie activo muestra el **origen** que
      elegiste (simplificado, bypass con CSV o físico) y la E_ac que esperas.

## 9. Mensajes frecuentes y qué hacer

| Mensaje | Causa | Solución |
|---|---|---|
| ⚠️ Primero configura el proyecto en 🏠 Proyecto… | No hay ciudad | Completa 🏠 Proyecto |
| ℹ️ Primero calcula el Recurso Solar en ☀️ | No hay TMY | Calcula ☀️ Recurso Solar |
| Completa la malla, el TMY y al menos un punto por superficie activa | Falta la escena, el TMY o puntos | Carga el `.json` y escribe puntos en cada superficie activa |
| La ubicación del archivo … NO coincide | La escena es de otro sitio | Exporta la escena correcta |
| ⚠️ Configuración eléctrica incompleta | Falta ID, eficiencia, asignación o N serie/paralelo | Corrige lo que indica el mensaje |
| … no puede entrar al modo físico: falta 'p_shade' (o 'firma_sombra') | Sombra no calculada, descartada por error geométrico, o guardada con el algoritmo v1 | Revisa los puntos (20–50 cm fuera del volumen) y recalcula con 🌳 Calcular sombra |
| … falta 'n_serie' / 'n_paralelo' / 'inversor_id' | Configuración eléctrica de la superficie incompleta | Completa el paso 3 |
| ❌ No se puede calcular el modo físico: … | Otro dato faltante o inválido | Completa lo indicado; no inventes valores |
| ❌ El candidato ya no es válido… | Algo cambió después de comparar | Vuelve a calcular la comparación |
| 🔴 Alarma de validación SDM | El panel no valida contra su ficha | Revisa 📐 Dimensionamiento / Motor IV |
| ⚠️ Estas superficies no tienen POA vigente… | Cambió la geometría, el montaje, el albedo, el bifacial, el TMY o la ubicación, o el cálculo falló | Presiona ⚡ Calcular POA para todas las superficies |
| ⚠️ Financiero, Baterías y CO₂ ya usan energía … ¿Reemplazarla por…? | Hay energía publicada de otro origen | ✅ Sí, reemplazar o ✖ Cancelar |
| ❌ Bypass no publicado; falló en: … | Una superficie no pudo simular el bypass | Corrige la causa y vuelve a calcular |
