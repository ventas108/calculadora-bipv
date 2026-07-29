# 📘 MANUAL DE OPERACIÓN — CALCULADORA BIPV COLOMBIA
### Versión 2026 · Innovación Química · calc.innovacionquimica.com.co

---

> **Cómo usar este manual**
> Cada proyecto sigue un flujo de páginas en orden. Las páginas están numeradas 1 → 8 en la barra lateral.
> **No salte páginas.** Cada página alimenta a la siguiente. Si salta una, los cálculos posteriores quedarán incompletos o con valores por defecto incorrectos.

---

## ⚡ PUNTOS DE PARTIDA — ¿Cuál es su caso?

| Situación | Modo | Sección de este manual |
|---|---|---|
| Sé cuántos m² de fachada/techo hay disponibles | 📐 **Modo Área** | Ver Parte A |
| Tengo la factura eléctrica o sé el consumo kWh/mes | 🔌 **Modo Consumo** | Ver Parte B |

---
---

# PARTE A — 📐 Modo ÁREA DISPONIBLE
## "Sé cuántos metros cuadrados tengo para instalar paneles"

---

## PASO 1 — Página 1: Datos del Proyecto

### Qué hacer
1. Abrir **`1 🏠 Proyecto`** en la barra lateral.
2. En **"Modo de cálculo"** seleccionar: **`Área disponible`**.
3. Llenar los campos:

| Campo | Descripción | Ejemplo |
|---|---|---|
| **Nombre del proyecto** | Identificador del proyecto (solo texto) | `Edificio Chapinero` |
| **Ciudad** | Seleccionar de la lista desplegable | `Bogotá` |
| **Área de fachada / techo (m²)** | Metros cuadrados REALES disponibles para paneles | `50` |
| **Tarifa eléctrica (COP/kWh)** | Valor del kWh según su factura | `650` |
| **Performance Ratio — PR (%)** | Eficiencia real del sistema (dejar en 80% si no sabe) | `80` |
| **Densidad de potencia (W/m²)** | Potencia por m² del panel elegido (ver ficha técnica) | `200` |

4. Hacer clic en **`💾 Guardar configuración`**.

### ✅ Señal de éxito
La página muestra un bloque verde con: ciudad, coordenadas, GHI, temperatura media y una **estimación preliminar** de energía anual en kWh.

### ⚠️ ALERTAS — No cometer estos errores

> 🔴 **NO ingrese el área del lote completo.** Solo ingrese el área NETA disponible para paneles (sin pasillos de mantenimiento, sin sombras de paredes, sin zonas de exclusión).

> 🔴 **NO deje la tarifa en 0.** Si la tarifa es 0 el análisis financiero calculará ahorro = $0 y la TIR saldrá incorrecta.

> 🔴 **NO cambie la ciudad después de haber calculado el Recurso Solar.** Si cambia la ciudad debe repetir todos los pasos desde el Paso 2.

> 🟡 **El PR por defecto (80%) es conservador.** Para sistemas BIPV en fachada vertical con sombras, use 70–75%. Para techos sin sombras, puede usar 82–85%.

---

## PASO 2 — Página 2: Recurso Solar

### Qué hacer
1. Abrir **`2 ☀️ Recurso Solar`**.
2. Ingresar la orientación de la instalación:

| Campo | Descripción | Valores típicos |
|---|---|---|
| **Azimuth fachada (°)** | Dirección a la que mira la fachada (Norte=0°, Sur=180°, Este=90°, Oeste=270°) | Fachada sur → `180` |
| **Inclinación — Tilt (°)** | Ángulo de inclinación del panel respecto al horizonte | Fachada vertical → `90` · Techo plano → `10` |
| **Albedo del suelo** | Reflectividad del suelo frente a la fachada (0.2 = concreto, 0.8 = nieve) | `0.20` |

3. Hacer clic en **`⚡ Calcular Recurso Solar`**.
4. Esperar el heatmap horario (puede tardar 30–90 segundos la primera vez — descarga datos de PVGIS/NASA).

### ✅ Señal de éxito
Aparece el mensaje `✅ Recurso solar calculado` y se muestran:
- Gráfica de irradiancia mensual POA
- Heatmap horario
- POA anual en kWh/m²

### ⚠️ ALERTAS — No cometer estos errores

> 🔴 **NO continúe si aparece error de PVGIS.** El error indica que no hay datos satelitales para esa ciudad. Revisar la conexión a internet del servidor. Sin este paso el resto del flujo no tiene datos climáticos.

> 🔴 **NO use Tilt = 0°.** Tilt cero significa panel horizontal mirando al cielo. Para fachadas use 90°. Para techos inclinados use el ángulo real.

> 🟡 **El azimuth afecta drásticamente la producción.** Una fachada norte (azimuth 0°) en Colombia puede producir 40–60% menos que una fachada sur. La calculadora lo mostrará en el POA resultante.

> 🟡 **Si el cálculo tarda más de 3 minutos**, refrescar la página y repetir. El tiempo normal es 30–90 seg.

---

## PASO 3 — Página 4: Dimensionamiento de Strings

> ⚠️ **Salte la Página 3 (Motor IV) por ahora.** El Motor IV es una herramienta técnica de validación. No es obligatoria para completar el flujo de cálculo.

### Qué hacer
1. Abrir **`4 📐 Dimensionamiento`**.
2. Seleccionar equipos:

| Selector | Descripción |
|---|---|
| **Panel solar** | Elegir del catálogo. Usar panel con ficha técnica completa (marcado 🟢). |
| **Inversor** | Elegir el inversor que corresponde a la potencia del sistema. |

3. Revisar o ajustar los parámetros de temperatura:

| Campo | Descripción | Defecto |
|---|---|---|
| **T mínima de diseño (°C)** | Temperatura nocturna más fría del sitio | Viene de Página 1 |
| **T celda realista (°C)** | Temperatura de operación normal (50–60 °C típico) | `50` |
| **T celda extremo (°C)** | Temperatura máxima posible en verano (65–75 °C) | `70` |
| **N° strings por tracker** | Número de strings en paralelo por entrada MPPT | `1` |

4. Hacer clic en **`⚡ Calcular Dimensionamiento`**.

### ✅ Señal de éxito
La calculadora muestra:
- Número de paneles en serie por string (N_serie)
- Verificación ✅ de tensiones (Voc ≤ Vmax inversor, Vmpp dentro del rango MPPT)
- Potencia DC total del sistema (kWp)

### ⚠️ ALERTAS — No cometer estos errores

> 🔴 **NO elija un panel marcado 🔴 (ficha incompleta).** El motor de simulación no podrá calcular la curva I-V y la producción será estimada con menor precisión.

> 🔴 **NO ignore las advertencias de tensión.** Si aparece ⚠️ "Voc supera Vmax del inversor" el sistema eléctrico es inseguro y no debe instalarse así. Reducir paneles en serie o cambiar inversor.

> 🟡 **Si el sistema tiene múltiples orientaciones** (por ejemplo fachada sur + techo), use el toggle "Múltiples orientaciones" y distribuya el porcentaje de paneles por orientación. Las fracciones DEBEN sumar exactamente 1.00 (100%).

---

## PASO 4 — Página 5: Mismatch y Pérdidas

### Qué hacer
1. Abrir **`5 🔀 Mismatch`**.
2. Definir el perfil de horizonte (obstáculos que generan sombra):
   - Si NO hay sombras cercanas: dejar el perfil de horizonte vacío (elevación = 0° para todos los azimuth).
   - Si hay edificios, árboles u obstáculos: ingresar los puntos de azimuth y elevación del obstáculo.
3. Ajustar pérdidas por factores del sistema:

| Parámetro | Descripción | Valor típico |
|---|---|---|
| **Mismatch fabricación (%)** | Diferencia de parámetros entre paneles del mismo lote | `2` |
| **Soiling / suciedad (%)** | Pérdida por polvo y suciedad acumulada | `3` |
| **Cableado DC (%)** | Pérdidas resistivas en el cableado | `2` |

4. Hacer clic en **`⚡ Calcular Mismatch`**.

### ✅ Señal de éxito
Aparece el gráfico "cascada de pérdidas" (waterfall) con el **Factor Global de Mismatch** y la **POA efectiva final** en kWh/m².

### ⚠️ ALERTAS — No cometer estos errores

> 🟡 **Esta página es opcional pero recomendada.** Si la omite, la Producción usará el POA sin descuentos de sombra ni mismatch. Esto sobreestima la energía producida.

> 🟡 **Si usa múltiples orientaciones**, activar el toggle correspondiente para que el cálculo de mismatch por orientación sea correcto.

> 🟡 **Las pérdidas totales** (soiling + mismatch + cableado) no deben ser menores al 3% ni mayores al 25% en condiciones normales. Valores extremos indican un error de entrada.

---

## PASO 5 — Página 6: Producción Anual

### Qué hacer
1. Abrir **`6 📊 Producción`**.
2. Verificar o ajustar:

| Campo | Descripción |
|---|---|
| **N° paneles** | Viene del Dimensionamiento (editable si necesita ajustar) |
| **Eficiencia del inversor (%)** | Eficiencia CEC o Euro del inversor (96–98% típico) |

3. Hacer clic en **`⚡ Calcular Producción`**.
4. Revisar los resultados: E_ac anual (kWh), PR del sistema, Yields.

### ✅ Señal de éxito
Aparece el mensaje `✅ Producción calculada` con:
- Energía AC anual (kWh/año)
- Performance Ratio real del sistema
- Gráficas mensuales y heatmap de producción horaria

### ⚠️ ALERTAS — No cometer estos errores

> 🔴 **NO continúe al Financiero sin completar este paso.** Sin producción calculada, el análisis financiero no tiene el dato de energía anual y usará 0 kWh.

> 🟡 **PR > 100% es posible en climas fríos** (Bogotá, Manizales). No es un error. El modelo SDM captura la ganancia de los paneles por bajas temperaturas. Es un resultado válido.

> 🟡 **Si E_ac sale muy alta** (>1.800 kWh/kWp·año para Colombia) verifique que el tilt y azimuth del Paso 2 son correctos para su instalación.

---

## PASO 6 — Página 8: Presupuesto (opcional pero recomendado)

> 💡 **¿Por qué hacerlo antes del Financiero?** El Presupuesto con costos reales da un CAPEX más preciso que el modelo paramétrico del Financiero.

### Qué hacer
1. Abrir **`8 💼 Presupuesto`**.
2. Verificar la **TRM (COP/USD)** en la parte superior. Ajustar a la tasa actual si difiere.
3. Revisar las pestañas de costos:

| Pestaña | Qué contiene |
|---|---|
| **Materiales** | Estructura, cableado, protecciones, mano de obra civil |
| **Mano de Obra** | Instalación eléctrica, puesta en marcha |
| **Sistema FV** | Paneles (cantidad y precio/unidad) |
| **Inversor** | Inversor (cantidad y precio/unidad) |
| **Catálogo** | Líneas de costo personalizadas adicionales |

4. Ajustar cantidades y precios según cotizaciones reales.
5. Revisar el **costo total (USD)** y el **costo por Wp (USD/Wp)**.

### ✅ Señal de éxito
El CAPEX total en USD queda visible al final de la página. Este valor se transferirá automáticamente al Financiero.

### ⚠️ ALERTAS — No cometer estos errores

> 🔴 **ALERTA CRÍTICA — Costo/Wp > USD 5.0:** Si aparece la advertencia amarilla "⚠️ Costo por Wp parece alto", hay un error de unidades en alguna fila. Las columnas de precio son en **USD**. Si ingresó un valor en COP (ej: $18.000.000) en lugar de USD (ej: $5.000), el total queda inflado por un factor ~3.600. Revisar fila por fila.

> 🔴 **NO mezcle COP y USD en la misma tabla.** Todos los valores del Presupuesto deben estar en **USD**. Usar la TRM para convertir los valores que tenga en COP antes de ingresarlos.

> 🟡 **Los valores de Mano de Obra son los más propensos al error COP/USD.** Verifique que el total de MO no supere el 20–30% del costo total del sistema.

> 🟡 **Rango de referencia saludable:** Un sistema fotovoltaico instalado en Colombia cuesta entre **USD 1.50 y USD 4.00 por Wp**. Valores fuera de este rango indican error en la entrada de datos.

---

## PASO 7 — Página 7: Análisis Financiero

### Qué hacer
1. Abrir **`7 💰 Financiero`**.
2. **Activar el toggle de Presupuesto** (si completó el Paso 6):
   - Activar: `🔗 Usar CAPEX del Presupuesto`
   - El CAPEX real reemplaza al modelo paramétrico.
3. Si NO usó el Presupuesto, llenar manualmente el CAPEX paramétrico:

| Campo | Descripción | Rango típico Colombia |
|---|---|---|
| Costo módulos (USD/kWp) | Precio de paneles por kWp instalado | 300–500 |
| Costo inversor (USD/kWp) | Precio de inversor por kWp | 100–200 |
| Estructura e instalación (USD/kWp) | Civil + eléctrico | 200–400 |
| Imprevistos (%) | Contingencia sobre CAPEX | 5–10 |

4. Verificar o ajustar los parámetros financieros:

| Campo | Descripción | Valor típico |
|---|---|---|
| **TRM (COP/USD)** | Tasa de cambio actual | `4.200` (ajustar al día) |
| **Escalación tarifa (%/año)** | Aumento anual esperado del kWh | `5` |
| **Degradación módulos (%/año)** | Pérdida anual de producción del panel | `0.5` |
| **OPEX (% del CAPEX/año)** | Mantenimiento anual | `1.0` |
| **Tasa de descuento (%)** | Costo de oportunidad del capital | `10–12` |
| **Horizonte (años)** | Vida útil del proyecto | `25` |
| **Tasa renta corporativa (%)** | Para calcular beneficio Art. 11 Ley 1715 | `35` |

5. Hacer clic en **`⚡ Calcular Análisis Financiero`**.

### ✅ Señal de éxito
La página muestra:
- TIR (%) — Tasa Interna de Retorno
- VPN (USD) — Valor Presente Neto
- Payback simple y descontado (años)
- LCOE (USD/kWh)
- Beneficios Ley 1715 (Art. 11, 12, 14)
- Gráfica de flujo de caja acumulado

### ⚠️ ALERTAS — No cometer estos errores

> 🔴 **Si aparece el banner "🔄 El CAPEX cambió — Recalcula"**: significa que modificó el Presupuesto después de calcular el Financiero. **Siempre volver a hacer clic en `⚡ Calcular`** después de cualquier cambio en Presupuesto o en los parámetros financieros.

> 🔴 **NO active el toggle de Presupuesto si el Presupuesto tiene el costo/Wp inflado.** El error de datos se propagará a todos los indicadores financieros (TIR, VPN, Payback).

> 🔴 **TIR muestra "M COP" en lugar de "%"**: si ve este error, actualice la página (F5) y recalcule. Es un bug de visualización ya corregido en la versión actual.

> 🟡 **La Ley 1715 aplica solo para personas jurídicas** (empresas). Para proyectos residenciales, los beneficios del Art. 11 (deducción renta) y Art. 12 (IVA) no aplican. En ese caso dejar tasa renta = 0%.

> 🟡 **TIR negativa o payback > 20 años** casi siempre indica uno de estos problemas: (1) CAPEX inflado por error de unidades, (2) tarifa eléctrica ingresada demasiado baja, (3) producción cercana a 0 por falta del cálculo de Producción.

---

## PASO 8 — Página 3: Motor IV (opcional / técnico)

> 💡 Este paso es para validación técnica del panel elegido. NO afecta los cálculos de producción ni financieros.

### Qué hacer
1. Abrir **`3 🔬 Motor IV`**.
2. Seleccionar el mismo panel elegido en Dimensionamiento.
3. El motor calcula la curva I-V y P-V y valida contra la ficha técnica.

### ✅ Señal de éxito
Errores de validación < 5% en Voc, Isc, Vmp y Pmax. Aparece mensaje `✅ Parámetros validados`.

### ⚠️ ALERTAS

> 🟡 **Si el error es > 5%**, la ficha técnica del panel puede estar incompleta o los coeficientes de temperatura son incorrectos. Notificar al administrador del catálogo.

---
---

# PARTE B — 🔌 Modo CONSUMO / FACTURA
## "Tengo la factura eléctrica o sé cuántos kWh/mes consumo"

---

## PASO 1 — Página 1: Datos del Proyecto

### Qué hacer
1. Abrir **`1 🏠 Proyecto`** en la barra lateral.
2. En **"Modo de cálculo"** seleccionar: **`Consumo / Factura`**.
3. Llenar los campos:

| Campo | Descripción | Ejemplo |
|---|---|---|
| **Nombre del proyecto** | Identificador del proyecto | `Fábrica Norte` |
| **Ciudad** | Seleccionar de la lista | `Medellín` |
| **Tarifa eléctrica (COP/kWh)** | Valor del kWh según su factura | `580` |
| **Factura mensual (COP)** | Valor total de la última factura | `1.500.000` |
| **— O bien — Consumo (kWh/mes)** | Si conoce el consumo directo | `2.500` |
| **% Cobertura solar deseada** | Qué porcentaje del consumo quiere cubrir con solar | `80` |
| **Densidad de potencia (W/m²)** | Del panel elegido (ver ficha técnica) | `200` |
| **Performance Ratio — PR (%)** | Dejar en 80% si no sabe | `80` |

4. Hacer clic en **`💾 Guardar configuración`**.

### ✅ Señal de éxito
La calculadora muestra:
- Consumo mensual estimado (si ingresó factura, lo convierte usando la tarifa)
- **Área necesaria** para alcanzar la cobertura deseada
- Semáforo: 🟢 si el área necesaria es razonable / 🔴 si es muy grande

### ⚠️ ALERTAS — No cometer estos errores

> 🔴 **NO ingrese factura Y consumo al mismo tiempo.** Use uno de los dos. Si ingresa ambos, la calculadora usará la factura y el consumo quedará como referencia secundaria.

> 🔴 **Si la tarifa está en 0 o es incorrecta**, el cálculo de consumo desde factura será erróneo. Verifique la tarifa exacta en su factura de energía (columna "costo kWh" o "valor unitario").

> 🔴 **El área calculada es la mínima necesaria.** Si no tiene ese espacio disponible, baje el % de cobertura hasta que el área sea factible. Por ejemplo: si necesita 80 m² pero solo tiene 50 m², ajuste la cobertura al 50%.

> 🟡 **En modo consumo, el Área Fachada se calcula automáticamente.** No la ingrese manualmente. Este campo se pre-llena con el área mínima necesaria para la cobertura solicitada.

---

## PASOS 2 al 8 — Idénticos al Modo Área

> Una vez configurado el Proyecto en Modo Consumo, **el resto del flujo es exactamente igual al Modo Área** (Pasos 2 al 8 de la Parte A). La única diferencia es el punto de partida: en Modo Área usted define el espacio disponible; en Modo Consumo la calculadora determina el espacio necesario.

Continúe desde el **[Paso 2 — Recurso Solar](#paso-2--página-2-recurso-solar)** de la Parte A.

---
---

# 🗂️ RESUMEN DE DEPENDENCIAS — Orden obligatorio de páginas

```
[1 🏠 Proyecto]  ←── SIEMPRE PRIMERO
       │
       ▼
[2 ☀️ Recurso Solar]  ←── OBLIGATORIO antes de Mismatch y Producción
       │
       ▼
[4 📐 Dimensionamiento]  ←── Seleccionar panel + inversor
       │
       ▼
[5 🔀 Mismatch]  ←── Opcional pero recomendado (sombras y pérdidas)
       │
       ▼
[6 📊 Producción]  ←── OBLIGATORIO antes del Financiero
       │
       ├──────────────────────┐
       ▼                      ▼
[7 💰 Financiero]  ←──  [8 💼 Presupuesto]
   (usa CAPEX real            (alimenta CAPEX
    si toggle activo)          al Financiero)


[3 🔬 Motor IV]  ←── Independiente. Herramienta técnica de validación.
                      Puede usarse en cualquier momento.
```

---

# 🚫 ERRORES FRECUENTES — Resumen rápido

| Error | Causa | Solución |
|---|---|---|
| Financiero muestra TIR = 0% o negativa | Producción no calculada o CAPEX inflado | Completar Pág. 6 antes de Pág. 7 |
| Costo/Wp = USD 12 o más | Valores de MO o materiales ingresados en COP en lugar de USD | Dividir esos valores por la TRM actual |
| Presupuesto muestra inversor a $0/unidad | Columna "Costo Inversor" vacía en el Excel del catálogo | Ingresar precio manualmente en la pestaña Catálogo del Presupuesto |
| Recurso Solar da error de PVGIS | Sin conexión a internet o servidor caído | Verificar conexión y reintentar |
| Producción parece muy alta | Azimuth o Tilt incorrectos en Recurso Solar | Corregir orientación en Pág. 2 y recalcular todo desde ahí |
| Mismatch no calcula | Falta Recurso Solar | Completar Pág. 2 primero |
| Dimensionamiento da ⚠️ de tensión | Demasiados paneles en serie para ese inversor | Reducir N_serie o elegir otro inversor |
| "Recalcula" banner en Financiero | CAPEX cambió después de calcular | Clic en ⚡ Calcular nuevamente |
| Sidebar muestra dos entradas "Presupuesto" | Archivo duplicado en el servidor | Eliminar `8_📦_Presupuesto.py` del servidor (conservar `8_💼_Presupuesto.py`) |

---

# 📋 CHECKLIST DE PROYECTO COMPLETO

Antes de entregar resultados a un cliente, verifique:

- [ ] Pág. 1 — Ciudad correcta, tarifa real, área o consumo ingresado
- [ ] Pág. 2 — Azimuth y tilt correctos para la instalación real
- [ ] Pág. 4 — Panel con ficha 🟢, inversor compatible, tensiones ✅
- [ ] Pág. 5 — Mismatch calculado (aunque sea con pérdidas = 0)
- [ ] Pág. 6 — Producción calculada (E_ac > 0 kWh/año)
- [ ] Pág. 8 — Presupuesto revisado, costo/Wp entre USD 1.5 y 4.0
- [ ] Pág. 7 — TRM actualizada, toggle de Presupuesto activo, recalculado
- [ ] Pág. 7 — TIR, VPN y Payback tienen sentido económico
- [ ] Exportar PDF del reporte técnico (disponible en Pág. 6 o Pág. 7)

---

*Manual generado para uso interno · Innovación Química · Calculadora BIPV Colombia v2026*
