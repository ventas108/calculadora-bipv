# Ficha de Validación: Sistema de alarma DC/AC vs PVsyst (proyecto Teusaquillo)

**Fecha:** 29-ago-2026
**Origen:** validar que la app se comporte de forma homóloga a PVsyst 8.1.5 frente a un inversor sobredimensionado, usando el proyecto real Teusaquillo (Bogotá, fachada vertical BIPV) como caso de prueba — 128 módulos SOLTECH ASP-ST1-T40 (CdTe semitransparente, 63 Wp), 8,064 kWp, Growatt MID15KTL3-X (15 kW CA, 2 MPPT).

## 1. Hallazgo en PVsyst: el bloqueo es duro, no una advertencia

Con la config real (128 módulos, 8 en serie × 16 cadenas, 2 trackers), PVsyst muestra:

> *"Definición del sistema: La potencia del inversor está muy sobredimensionada."*

El indicador **"Sistema"** queda en 🔴 y el botón **"Ejecutar simulación"** se deshabilita — no es una advertencia cosmética, PVsyst **impide correr la simulación** hasta resolver el sobredimensionamiento. Confirmado con captura real de la ventana principal del proyecto (Resumen de resultados en 0.00 en todos los campos).

**Proporción Pnom real en PVsyst:** 8,064 kWp / 15 kW = **0,538**.

## 2. Trabajo recuperado tras corte de energía

La sesión anterior había implementado `evaluar_relacion_dc_ac(P_dc_stc_kW, P_ac_nom_W)` en `calculos/dimensionamiento.py` — clasifica la relación DC/AC en 5 niveles (🔴 muy sobredimensionado <0,75 · 🟠 sobredimensionado <1,0 · 🟢 óptimo 0,95–1,35 · 🟠 alto ≤1,6 · 🔴 muy alto >1,6), anclada al dato real de PVsyst (0,538 → mismo aviso). Un corte de energía interrumpió el commit/push; el trabajo se recuperó intacto desde el working tree de `C:\Users\Mauricio\bipv\calculadora-bipv` (nunca llegó a `git add`) y se confirmó con la suite completa (726/726 tests) antes de subirlo. Integrada en `pages/6_📊_Producción.py` (alarma antes de simular + aviso de clipping real tras simular) y `pages/4_📐_Dimensionamiento.py` (mismo aviso a nivel de proyecto completo). — commit `e3f702a1`.

**Diferencia de diseño respecto a PVsyst:** la app avisa (🔴/🟠/🟢) pero **no bloquea la simulación** — permite evaluar diseños BIPV con relaciones DC/AC atípicas (habituales en fachadas de baja potencia con inversor reutilizado o sobredimensionado a propósito), en vez de rechazarlos de plano.

## 3. Bugs reales encontrados en el catálogo al intentar reproducir el caso

Verificar la alarma contra el proyecto real expuso tres problemas independientes en `bipv_python/datos/inversores_catalogo.xlsx`, ninguno visible hasta este ejercicio:

### 3.1 El inversor real no estaba en el catálogo Excel
El Growatt MID15KTL3-X solo existía en un catálogo Python viejo (`datos/catalogo_inversores.py`) que el código ya no usa — el dropdown de Producción/Dimensionamiento lee `catalogo_inversores_excel.py`, y ahí no estaba. **Agregado** con specs verificadas contra PVsyst (Vdc_max 1100V, MPPT 140–1000V, 2 trackers, 8 strings/tracker, P_dc máx 22,5kW). — commit `e83dc9e1`.

### 3.2 Columna "Potencia AC nominal (kW)" faltante en TODO el catálogo
El loader busca esa columna para calcular `P_ac_nom_W`; al no existir en el Excel real, **los ~106 inversores del catálogo** calculaban su potencia CA nominal vía el respaldo `P_dc_max_W × 0,96` — nunca con el dato real del fabricante. Para el MID15KTL3-X esa aproximación daba 21.600W en vez de 15.000W reales (este inversor acepta sobrepaneling importante: 22,5kW DC recomendados para solo 15kW CA de salida, ratio muy distinto a 0,96). **Columna agregada** (retrocompatible, al final de la hoja) y valor real (15kW) cargado para este inversor. Los otros 105 inversores siguen con el mismo respaldo hasta que alguien cargue su dato real. — commit `e83dc9e1`.

### 3.3 Corriente máxima por tracker mal derivada
Al mapear compatibilidad eléctrica, la app marcó el Growatt MID15KTL3-X recién agregado como 🔴 **no compatible** ("Isc de strings 8,00 A > límite por tracker 6,40 A"). Causa: el valor inicial (6,4A) se derivó de la corriente que *produce el arreglo* (8 strings × 0,80A del módulo), no de la que *soporta el inversor* — PVsyst no publica ese dato ("N/A" en su ficha). Corregido a **27,5A / 33,5A**, tomando la entrada hermana genérica "MID 15KTL3-X" ya presente en el catálogo (misma familia/clase de potencia, con datos de datasheet más completos). — commit `ac4a87e5`.

### 3.4 Pendiente, no resuelto: duplicado de catálogo
Existe una familia completa **"MID 15/17/20/22/25KTL3-X"** genérica (sin marca, `N_strings/tracker=1` fijo en las 5, `Vmppt_min=200V` en las 5, mismo patrón redondeado) que es casi con certeza el mismo producto que el "Growatt MID15KTL3-X" recién agregado con datos más precisos. La herramienta de "mapeo de inversores compatibles" de Dimensionamiento auto-sugiere la genérica primero, lo que llevó a un cálculo erróneo (16 paneles/inversor, 8 inversores necesarios, ratio DC/AC 0,42) hasta que se seleccionó manualmente la entrada correcta. **No se tocó esta sesión** — fuera de alcance, queda documentado para una limpieza de catálogo futura.

## 4. Verificación final

Con el catálogo corregido, N=8 (el diseño real) pasa limpio en el barrido de compatibilidad de la app:

| Chequeo (N=8, Growatt MID15KTL3-X) | Resultado |
|---|---|
| Voc frío (983,7V) ≤ Vdc máx (1100V) | ✅ OK |
| Vmp realista (652,1V) ≥ Vmppt mín (140V) | ✅ OK |
| Vmp extremo (630,8V) ≥ Vmppt mín | ✅ OK |
| I equiv (8,0A) ≤ I máx tracker (27,5A) | ✅ OK |
| Vmp (652,1V) ≤ Vmppt máx (1000V) | ✅ OK |
| MPPT util. | 65,2% |
| Riesgos | 0 🟢 |

A partir de N=9 en adelante, todo falla por Voc>1100V — confirma que 8 módulos/string es el límite físico correcto, coincidiendo con el diseño real.

**Relación DC/AC de la app:** `evaluar_relacion_dc_ac(8.064, 15000)` → ratio **0,538**, 🔴 muy_sobredimensionado, mensaje cita "capacidad del inversor (15,0 kW CA)" — coincide exactamente con la Proporción Pnom real de PVsyst (0,538, mismo aviso).

## 5. Qué queda abierto

No se obtuvo el número final de energía/PR de PVsyst para este proyecto — el bloqueo de "Sistema" en rojo impide correr la simulación con el inversor real de 15kW. Opciones no ejecutadas todavía: (a) buscar un inversor "de prueba" trifásico de ~7,5–8,5kW con ventana de voltaje alta para destrabar la corrida y comparar solo POA/temperatura/curva del panel, o (b) revisar si PVsyst tiene algún ajuste de tolerancia de diseño no explorado en esta sesión. Sin ese número, la comparación cuantitativa completa (6.017 kWh/año de la app, motor con IAM+soiling+térmico) contra PVsyst sigue pendiente.

## Commits relacionados
- `b79e771f` — recorte (clipping) real al Pnom del inversor en el motor de producción
- `e3f702a1` — alarma de relación DC/AC (`evaluar_relacion_dc_ac`), recuperada tras corte de energía
- `e83dc9e1` — columna "Potencia AC nominal (kW)" + Growatt MID15KTL3-X real en el catálogo
- `ac4a87e5` — corrección de corriente máxima por tracker del Growatt MID15KTL3-X
