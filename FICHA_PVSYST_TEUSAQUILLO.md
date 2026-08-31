# Ficha de datos para PVsyst — Proyecto Teusaquillo, Bogotá (fachada BIPV vertical)

**Fecha:** 27-ago-2026
**Origen:** el usuario pidió los datos concretos de un corrido real de la app para replicarlo en PVsyst y corroborar resultados, usando el proyecto "Teusaquillo, Bogotá" — el único proyecto de fachada vertical ya auditado contra el XLSM original en este repo (panel ASP-ST1-T40, inversor Growatt-MID15KTL3-X, 128 paneles). Verificado antes de escribir esto que "GEN-LB-US-6K" y "97 m²" (mencionados inicialmente por el usuario) no existen en ningún archivo del repo — se usan los datos reales confirmados.

**Estado:** pendiente el resultado de PVsyst — este archivo se actualizará con la comparación cuando el usuario lo corra. Ver sección "Pendiente" al final.

## 1. Sitio

| Parámetro | Valor | Fuente |
|---|---|---|
| Ubicación | Bogotá (Teusaquillo) | `datos/ciudades_colombia.py` |
| Latitud | 4,711° N | ídem |
| Longitud | -74,072° (74,072° O) | ídem |
| Altitud | 2.600 m | ídem |
| Albedo | 0,20 | default de la app |

## 2. Orientación — conversión de convención de azimut

La app usa convención **pvlib** (0°=Norte, 90°=Este, **180°=Sur**, 270°=Oeste). **PVsyst usa 0°=Sur** por defecto en el hemisferio norte.

| | Convención pvlib (app) | Convención PVsyst |
|---|---|---|
| Inclinación (tilt) | 90° (fachada vertical) | 90° — igual |
| Azimut | 180° (Sur) | **0°** — NO 180° |

⚠️ Meter 180° directamente en PVsyst orientaría la fachada al Norte (error de 180°) e invalidaría toda la comparación.

## 3. Módulo FV — ASP-ST1-T40 (SolTech Energy LaTam, CdTe semitransparente 40%)

No está en la base de datos de PVsyst — requiere módulo personalizado con modelo de un diodo (De Soto 2006). Fuente: `datos/tecnologias_bipv.py`, calibrado contra la hoja `FF_vs_Irradiancia` del XLSM auditado, validado contra Batzner et al. 2001.

### Parámetros STC (1000 W/m², 25°C)

| Parámetro | Valor |
|---|---|
| Voc | 116,0 V |
| Vmp | 86,4 V |
| Isc | 0,80 A |
| Imp | 0,70 A |
| Pmax | 63,0 W |
| FF | 67,9% |
| NOCT | 45,0 °C |
| Dimensiones | 1200×600 mm (0,72 m²) |

### Coeficientes de temperatura

| Coeficiente | Valor |
|---|---|
| β (Voc) | -0,321 %/°C |
| α (Isc) | +0,060 %/°C |
| γ (Pmax) | -0,214 %/°C |

### Parámetros del modelo de diodo único (SDM, De Soto)

| Parámetro | Valor |
|---|---|
| I_L_ref (fotocorriente) | 0,8152 A |
| I_o_ref (corriente de saturación) | 1,35×10⁻¹³ A |
| R_s (resistencia serie) | 25,509 Ω |
| R_sh_ref (resistencia paralelo en STC) | 1.340,6 Ω |
| a_ref (n×Ns) | 154,0 (Ns=141) |

⚠️ **Nota real, relevante para la comparación**: este panel tiene una curva de eficiencia calibrada donde el Fill Factor **sube** a irradiancias bajas (FF=76,3% a G=200 W/m² vs FF=67,9% en STC). Es un comportamiento documentado de este CdTe específico (validado contra Batzner et al. 2001), pero PVsyst probablemente no lo replique igual si el módulo se define solo con los parámetros SDM estándar de arriba — puede ser una fuente real de diferencia con PVsyst, no necesariamente un error de ninguno de los dos lados.

### Configuración del arreglo

128 módulos = **8,064 kWp DC** · 8 en serie × 8 strings/tracker × 2 trackers MPPT · 92,16 m² de área total.

## 4. Inversor — Growatt MID15KTL3-X

Fuente: `datos/catalogo_inversores.py`, ficha `Ficha_Tecnica_Inversores_GROWATT_MID15_25KTL3X.docx`.

| Parámetro | Valor |
|---|---|
| Vdc máx | 1.100 V |
| Ventana MPPT (rango absoluto) | 200–1.000 V |
| Tensión mínima MPPT activo (crítica) | 580 V |
| N° entradas MPPT | 2 (2 strings nativos c/u) |
| Corriente máx. por tracker | 27 A |
| Isc máx. por tracker | 33,8 A |
| Potencia DC máx. recomendada | 22.500 W |
| Potencia AC nominal | 15.000 W |
| Eficiencia máxima | 98,5% |

**Relación DC/AC** = 8.064 / 15.000 = **0,54** (muy conservador).

## 5. Temperaturas de diseño (Bogotá)

Fuente: `datos/ciudades_colombia.py`.

| Temperatura | Valor |
|---|---|
| Mínima de diseño | 5,0 °C |
| Celda realista | 36,35 °C |
| Celda extremo | 41,94 °C |
| Ambiente media | 14,0 °C |

## 6. Modelo de transposición y pérdidas (para replicar el criterio de la app)

- **Transposición**: Hay-Davies (verificado formula a formula contra `pvlib.irradiance.haydavies()` en la auditoría del 27-ago-2026). PVsyst por defecto suele usar Perez — correr ambos modelos en PVsyst permite ver la sensibilidad, igual que se hizo para el proyecto Urabá.
- **IAM**: ASHRAE, b₀=0,05 (vidrio estándar liso).
- **Soiling**: modelo mensual Colombia con factor de auto-limpieza vertical k=0,65 (fachadas se ensucian ~35% menos que superficies inclinadas).
- **Confinamiento térmico BIPV**: k=1,3 (fachada adosada al muro, sellada) — en PVsyst se aproxima reduciendo el parámetro de ventilación/U-value de montaje (sin cámara de aire).
- **Montaje**: fachada adosada/sellada — sin ganancia trasera, no es un modelo bifacial.
- **Transparencia**: 40% del área es vidrio sin celda (solo el 60% opaco genera).

## 7. Resultado de la app, corrido en vivo el 27-ago-2026 (para comparar)

Generado ejecutando el motor real: `calculos.solar.obtener_tmy_pvgis()` (TMY real de PVGIS, no sintético) → `calculos.solar.calcular_poa()` (Hay-Davies) → `calculos.motor_optico.cascada_optica()` (IAM+soiling+térmico) → `calculos.produccion.simular_produccion_anual()` (SDM De Soto completo, `panel_tiene_sdm_completo()` = True para este panel).

| | Sin Motor Óptico (referencia simple) | Con Motor Óptico (IAM+soiling+térmico, recomendado) |
|---|---|---|
| POA anual usada | 807,8 kWh/m²/año (bruta) | 737,2 kWh/m²/año (post-IAM+soiling) |
| E_dc anual | 6.654 kWh/año | 6.109 kWh/año |
| E_ac anual | 6.554 kWh/año | **6.017 kWh/año** |
| Yield específico (Y_f) | 813 kWh/kWp | 746 kWh/kWp |
| PR | 100,6% | 101,2% |

⚠️ **Ambos PR salen por encima de 100%** — inusual para un sistema real (típico 75-85%). Causa más probable: la curva de eficiencia calibrada del panel (mejor FF a baja irradiancia, ver sección 3) — Bogotá rara vez alcanza el G=1000 W/m² de referencia STC, así que el sistema opera casi siempre en el rango donde este panel específico rinde relativamente mejor que su placa nominal. **No es un artefacto de timestamp/timezone**: el chequeo QCRad automático (`calculos/solar.py::verificar_consistencia_radiativa()`, integrado 27-ago-2026) confirmó 0% de horas inconsistentes en el TMY real usado para esta corrida, diferencia máxima 2,8 W/m².

## 8. Qué comparar primero cuando tengas el resultado de PVsyst

1. **PR de PVsyst**: si también sale inusualmente alto (>95%), confirma que es un comportamiento real del panel (curva de baja irradiancia). Si sale en el rango típico (75-85%), la diferencia probablemente esté en cómo cada software modela esa curva de baja irradiancia — no necesariamente un bug de ninguno de los dos lados, pero vale la pena entender por qué divergen antes de confiar en cualquiera de los dos números para una decisión financiera.
2. **POA anual** (GlobInc de PVsyst vs los 807,8/737,2 kWh/m²/año de arriba) — el chequeo más simple y menos dependiente del modelo de módulo.
3. **Cascada de pérdidas de PVsyst** (IAM, sombreado, térmico) — comparar cada etapa contra el desglose de Motor Óptico (factor global 0,9073 = IAM × soiling × térmico combinados).

## Actualización 31-ago-2026 — verificación cruzada con literatura + modelo independiente

Mientras se espera el resultado de PVsyst, se corrió una verificación con un modelo CdTe
completamente independiente (power-rating model de Huld/JRC, calibrado contra literatura
académica real de CdTe BIPV bajo clima tropical) sobre los mismos datos reales de Teusaquillo.
Resultado: PR=89,4% (vs. 100,6% del motor principal) — 11,2 puntos más bajo, con evidencia
convergente hacia que el >100% es un artefacto de la calibración del panel, no un comportamiento
físico genuino. Detalle completo en `DIAGNOSTICO_VERIFICACION_JRC_CDTE_TEUSAQUILLO.md`. El
resultado real de PVsyst sigue siendo el punto de comparación más directo y decisivo, aún pendiente.

## Pendiente

- [ ] Correr el proyecto en PVsyst con los datos de arriba.
- [ ] Completar esta tabla con el resultado real de PVsyst:

| | PVsyst |
|---|---|
| GlobInc (POA) anual | — |
| E_ac anual | — |
| PR (estándar) | — |
| PR bifacial (si aplica) | N/A — no es bifacial |

- [ ] Decidir si la diferencia (si la hay) requiere ajustar la curva de eficiencia del panel en la app, o si confirma que el modelo actual es correcto.
