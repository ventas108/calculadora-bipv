# INFORME DE VIABILIDAD TÉCNICO-FINANCIERA
## Granja Fotovoltaica — Región de Urabá, Antioquia
**Fecha:** 1 de agosto de 2026 | **Herramienta:** Calculadora BIPV — calc.innovacionquimica.com.co

---

## 1. RESUMEN EJECUTIVO

| Indicador clave | Valor |
|---|---|
| Capacidad instalada | **743,6 kWp** |
| Energía anual producida (P50) | **1.100.213 kWh/año** |
| CAPEX bruto | **USD 404.350** (COP 1.617,4 M) |
| CAPEX neto con Ley 1715 | **USD 251.245** (COP 1.005,0 M) |
| Ahorro tributario Ley 1715 | **USD 153.105** (COP 612,4 M) |
| TIR P50 con Ley 1715 | **≈ 71,5 %** |
| Payback descontado (10 %) | **≈ 1,5 años** |
| VPN a 10 % WACC (P50) | **≈ USD 1.438.000** |
| LCOE | **214 COP/kWh (USD 0,053/kWh)** |
| Tarifa de compra evitada | **650 COP/kWh** |

> **Veredicto:** Proyecto con rentabilidad de clase mundial. Incluso en el escenario conservador bancario (producción P90, -10%) la TIR supera el 64% y el VPN es positivo. El riesgo financiero es bajo.

---

## 2. DATOS TÉCNICOS DEL SISTEMA

### 2.1 Localización y recurso solar

| Parámetro | Valor |
|---|---|
| Ubicación | Urabá, Antioquia, Colombia |
| Coordenadas (referencia) | ~7,88° N, 76,67° W |
| Área total instalación | 3.000 m² |
| POA bruta (irradiancia incidente) | **1.721 kWh/m²·año** |
| POA efectiva (tras desajuste) | **1.611 kWh/m²·año** |
| Temperatura media ambiente | 25,8 °C |
| Fuente recurso solar | TMY generado con API Open-Meteo |

### 2.2 Módulos fotovoltaicos

| Parámetro | Valor |
|---|---|
| Fabricante / Modelo | **JA Solar JAM66D46-715/LB** |
| Tecnología | Monocristalino N-type bifacial |
| Potencia pico (Pmp) | 715 Wp |
| Corriente de cortocircuito (Isc) | 18,55 A |
| Tensión en circuito abierto (Voc) | 52 V |
| Número de celdas en serie (Ns) | 66 |
| Coef. temperatura potencia (γ) | −0,290 %/°C |
| NOCT | 45 °C |
| Cantidad total | **1.040 módulos** |
| Potencia total instalada | **743,6 kWp** |

### 2.3 Inversores

| Parámetro | Valor |
|---|---|
| Modelo | **SOLIS-60K** |
| Potencia AC nominal | 60 kW |
| Tensión DC máxima | 1.100 V |
| N° trackers MPPT | 4 |
| Corriente máx. por tracker (Isc) | 47,63 A |
| Eficiencia (η_inv) | 97,5 % |
| Cantidad | **13 unidades** |
| Potencia AC total | 780 kW AC |

### 2.4 Configuración eléctrica

| Parámetro | Valor |
|---|---|
| Paneles por string (N óptimo) | **20** |
| Strings por tracker | **1** |
| Tensión Vmp por string | 770 V (máxima MPPT) |
| Configuración total | 13 inv × 4 trackers × 1 string × 20 paneles |
| Total paneles configurados | 1.040 ✓ |
| Cobertura de capacidad | **100 %** |
| Temperatura celda (operación realista) | 56 °C |
| Temperatura celda (extremo) | 66 °C |

---

## 3. PRODUCCIÓN ENERGÉTICA

### 3.1 Pérdidas del sistema — Cascada de Desajuste

| Etapa | Pérdida aplicada | POA resultante |
|---|---|---|
| POA bruta (referencia) | — | 1.721 kWh/m²·año |
| Sombreado de horizonte | **0,0 %** (campo abierto) | 1.721 |
| Mismatch de orientación | **0,0 %** (plano único 20°) | 1.721 |
| Mismatch de fabricación | **1,0 %** (JA Solar tier-1) | 1.704 |
| Suciedad / Soiling | **4,0 %** (zona agrícola tropical) | 1.636 |
| Cableado DC | **1,5 %** (strings 20 paneles) | 1.611 |
| **POA efectiva final** | **Pérdida acumulada: 6,4%** | **1.611 kWh/m²·año** |
| Factor global cascada | — | **93,6 %** |

> **Nota soiling 4%:** Urabá combina polvo de carreteras destapadas + aerosoles marinos del Golfo. Con plan de limpieza bimestral puede reducirse a 2,5%, mejorando el PR ~1,5 pp.

### 3.2 Métricas IEC 61724

| Métrica | Valor | Descripción |
|---|---|---|
| E_dc anual | 1.128.424 kWh | Energía DC antes de inversor |
| **E_ac anual (P50)** | **1.100.213 kWh** | Energía inyectada a la red |
| **E_ac anual (P90)** | **990.192 kWh** | Escenario conservador (−10%) |
| Y_r (Rendimiento referencia) | 1.611 h | POA efectiva / 1 kW/m² |
| Y_f (Rendimiento final) | 1.480 h | E_ac / P_instalada |
| **PR IEC 61724** | **91,9 %** | Calculado sobre POA_efectiva |
| **PR real vs POA bruta** | **86,0 %** | Y_f / Y_r_bruto = 1480/1721 |
| Factor de planta | 16,9 % | E_ac / (743,6 kWp × 8.760 h) |
| Pérdida por temperatura | −6,1 % | γ·ΔT, T_cel 56°C |
| Eficiencia inversor | 97,5 % | η_inv SOLIS-60K |

> El PR de 86% es coherente con granjas FV bien operadas en Colombia tropical (rango típico 83–88%).

---

## 4. INVERSIÓN (CAPEX)

### 4.1 Desglose del CAPEX bruto

| Componente | Base de cálculo | USD | COP (M) |
|---|---|---|---|
| Módulos FV (importación directa China) | 85 USD/ud × 1.040 | 88.400 | 353,6 |
| Inversores SOLIS-60K | 120 USD/kWp × 743,6 kWp | 89.232 | 356,9 |
| Estructura + cableado + protecciones | 200 USD/kWp × 743,6 kWp | 148.720 | 594,9 |
| Ingeniería + instalación + puesta en marcha | 18% sobre equipos | 54.999 | 220,0 |
| Imprevistos y contingencias | 5% sobre subtotal | 18.028 | 72,1 |
| **CAPEX bruto total** | | **404.350** | **1.617,4** |
| **Costo por Wp** | | **USD 0,54/Wp** | **1.680 COP/Wp** |

> **Sobre el costo del módulo:** El precio retail en Colombia (autosolar.co) es 555.000 COP ≈ USD 139/módulo. La importación directa de 1.040 unidades desde JA Solar China (FOB ~USD 64 + flete + nacionalización Ley 1715 exenta de arancel e IVA) resulta en **~USD 85/módulo puesto en obra** — un ahorro de USD 56.000 frente al retail local.

### 4.2 Beneficios Ley 1715 de 2012

| Artículo | Beneficio | Base | Valor USD | Valor COP |
|---|---|---|---|---|
| Art. 12 | Exclusión de IVA (19%) en equipos | 19% × 326.352 USD | **62.007** | $ 248,0 M |
| Art. 11 | Deducción renta (50% × tasa 35%) | 50% × 404.350 × 0,35 | **70.761** | $ 283,0 M |
| Art. 14 | Depreciación acelerada (diferencial VPN) | 5 años vs 10 años | **20.337** | $ 81,4 M |
| **Total Ley 1715** | | | **153.105** | **$ 612,4 M** |
| **CAPEX neto efectivo** | CAPEX − Ley 1715 | 404.350 − 153.105 | **251.245** | **$ 1.005,0 M** |

> ⚠️ **Condición:** Art. 11 y Art. 14 requieren declaración de renta con utilidades suficientes y certificación UPME previa. Art. 12 (IVA) es el único beneficio inmediato a la compra. Si la empresa no tiene renta suficiente en el primer año, el CAPEX efectivo sube a ~USD 313.000 y la TIR baja a ~55% — sigue siendo excelente.

---

## 5. PARÁMETROS OPERATIVOS Y FINANCIEROS

| Parámetro | Valor | Justificación |
|---|---|---|
| Tarifa eléctrica año 1 | 650 COP/kWh | Costo evitado real industria Colombia 2026 |
| Escalación anual tarifa | 5,0 %/año | Histórico indexación tarifaria Colombia |
| Tipo de cambio (TRM) | 4.000 COP/USD | Conservador — banco |
| O&M anual | **USD 7.000/año** | 9,4 USD/kWp·año — realista trópico + 13 inversores |
| Degradación módulos | 0,50 %/año | JA Solar N-type monocristalino Si |
| Tasa de descuento (WACC) | 10 % | Proyecto en USD, riesgo Colombia |
| Horizonte de análisis | **15 años** | Prudente para financiación bancaria |
| Escenario P90 | −10 % producción | Incertidumbre recurso solar TMY |

---

## 6. RESULTADOS FINANCIEROS

### 6.1 Tabla comparativa de escenarios

| Métrica | Sin Ley 1715 · P50 | **Con Ley 1715 · P50** | Con Ley 1715 · P90 |
|---|---|---|---|
| CAPEX efectivo (USD) | 404.350 | **251.245** | 251.245 |
| CAPEX efectivo (COP) | $ 1.617,4 M | **$ 1.005,0 M** | $ 1.005,0 M |
| **TIR (%)** | 45,0 % | **≈ 71,5 %** | **≈ 64,5 %** |
| **VPN a 10 % (USD)** | 1.284.525 | **≈ 1.437.630** | **≈ 1.263.418** |
| **VPN a 10 % (COP)** | $ 5.138 M | **≈ $ 5.751 M** | **≈ $ 5.054 M** |
| Payback simple (años) | 2,4 | **≈ 1,5** | **≈ 1,6** |
| Payback descontado (años) | 2,9 | **≈ 1,6** | **≈ 1,8** |
| LCOE (USD/kWh) | 0,0534 | 0,0534 | 0,0593 |
| LCOE (COP/kWh) | 214 | **214** | 237 |

> **Ajuste O&M:** Con O&M realista de USD 7.000/año (vs USD 4.044 de la app), la TIR baja ~2,5 pp y el VPN se reduce ~USD 22.000. El impacto es menor porque el O&M representa apenas el 2,8% del ingreso anual.

### 6.2 Flujo de caja proyectado — 15 años (escenario Con Ley 1715, P50, O&M USD 7.000)

| Año | Producción (kWh) | Ingreso energía (USD) | O&M (USD) | Flujo neto (USD) | Flujo acum. (USD) |
|---|---|---|---|---|---|
| 0 | — | — | — | −251.245 | **−251.245** |
| 1 | 1.100.213 | 178.785 | 7.000 | **+171.785** | **−79.460** |
| 2 | 1.094.712 | 186.785 | 7.000 | **+179.785** | **+100.325** |
| 3 | 1.089.238 | 195.144 | 7.000 | **+188.144** | **+288.469** |
| 4 | 1.083.792 | 203.877 | 7.000 | **+196.877** | **+485.346** |
| 5 | 1.078.373 | 213.000 | 7.000 | **+206.000** | **+691.346** |
| 6 | 1.072.981 | 222.532 | 7.000 | **+215.532** | **+906.878** |
| 7 | 1.067.616 | 232.490 | 7.000 | **+225.490** | **+1.132.368** |
| 8 | 1.062.278 | 242.894 | 7.000 | **+235.894** | **+1.368.262** |
| 9 | 1.056.967 | 253.764 | 7.000 | **+246.764** | **+1.615.026** |
| 10 | 1.051.682 | 265.117 | 7.000 | **+258.117** | **+1.873.143** |
| 11 | 1.046.424 | 276.971 | 7.000 | **+269.971** | **+2.143.114** |
| 12 | 1.041.192 | 289.345 | 7.000 | **+282.345** | **+2.425.459** |
| 13 | 1.035.986 | 302.254 | 7.000 | **+295.254** | **+2.720.713** |
| 14 | 1.030.806 | 315.717 | 7.000 | **+308.717** | **+3.029.430** |
| 15 | 1.025.652 | 329.752 | 7.000 | **+322.752** | **+3.352.182** |

> **Hito clave:** La inversión se recupera entre el año 1 y el año 2 (payback ~1,5 años). Los 13,5 años restantes son flujo libre positivo y creciente.

### 6.3 Análisis de sensibilidad — Tarifa eléctrica

| Escenario tarifa | COP/kWh | Ingreso año 1 (USD) | Payback | TIR estimada | Bancable |
|---|---|---|---|---|---|
| Autoconsumo industrial | **650** | 178.785 | 1,5 años | **~71,5 %** | ✅ Excelente |
| Medición neta alta | **450** | 123.774 | 2,2 años | **~38 %** | ✅ Sólido |
| PPA bilateral privado | **280** | 77.140 | 3,7 años | **~19 %** | ✅ Aceptable |
| Precio bolsa promedio | **220** | 60.512 | 4,8 años | **~12 %** | ⚠️ Límite |
| **Umbral VPN = 0 (10% WACC)** | **~137** | 37.750 | 15 años | **= 10 %** | ⛔ Mínimo |

> El precio de bolsa en Colombia nunca ha promediado anualmente por debajo de 150 COP/kWh en los últimos 20 años, incluso en años de alta hidrología. El umbral de 137 COP tiene margen de seguridad de ~10%.

---

## 7. INDICADORES DE DESEMPEÑO

| Indicador | Valor | Referencia |
|---|---|---|
| LCOE del proyecto | **214 COP/kWh** | Costo de generar 1 kWh |
| Tarifa de compra evitada | 650 COP/kWh | Precio de mercado |
| Margen sobre tarifa | **67 %** | Por cada peso que genera, 0,33 es costo |
| Factor de planta | 16,9 % | Típico Colombia 15–20% |
| PR real vs POA bruta | 86,0 % | Rango típico Colombia: 83–88% |
| Generación específica (Y_f) | 1.480 kWh/kWp·año | Alta para zona tropical |
| CO₂ evitado estimado | **~660 ton CO₂/año** | Factor emisión Colombia: 0,6 kg/kWh |
| Equivalente árboles plantados | ~30.000 árboles/año | Referencia comunicación |

---

## 8. ANÁLISIS DE RIESGOS

| Riesgo | Probabilidad | Impacto en TIR | Mitigación |
|---|---|---|---|
| Producción 10% menor (P90) | Media | −7 pp → TIR ~64,5% | Sigue bancable. Buen margen. |
| Art. 11 y 14 Ley 1715 no aplicables (sin renta) | Baja-Media | −15 pp → TIR ~56,5% | Planear con CAPEX bruto en año 0, capturar beneficios en años 1-3 |
| Tarifa eléctrica no escala (0%/año) | Baja | −8 pp → TIR ~63,5% | Contrato PPA a precio fijo con usuario ancla |
| O&M sube 50% (USD 10.500/año) | Baja | −1,5 pp → TIR ~70% | Impacto mínimo — O&M es <3% del ingreso |
| TRM sube a 5.000 COP/USD | Positivo | +5 pp → TIR ~76,5% | Favorece el proyecto |
| Degradación real 0,8%/año | Baja | −2 pp | JA Solar N-type históricamente <0,5% |

**Conclusión de riesgo:** El escenario de estrés (P90 + sin Ley 1715 + O&M alto) arroja TIR ~42%. Aún supera el WACC del 10% en 4x. El proyecto es **robusto ante escenarios adversos**.

---

## 9. BENEFICIOS LEY 1715 — RESUMEN PARA TRÁMITE

Para acceder a los beneficios se requiere:

1. **Art. 12 (IVA):** Certificación UPME previa a la compra de equipos. Aplica sobre módulos, inversores, estructura y cableado. Ahorro: **USD 62.007**.

2. **Art. 11 (Deducción renta):** 50% del valor del proyecto se descuenta de la base gravable en el año de la inversión. Requiere utilidades declaradas ≥ USD 202.175. Ahorro potencial: **USD 70.761**.

3. **Art. 14 (Depreciación acelerada):** Amortización en 5 años en lugar de los 10 estándar. Beneficio en VPN: **USD 20.337**.

---

## 10. RECOMENDACIONES ESTRATÉGICAS

1. **Asegurar consumidor ancla antes de construir.** La estrategia óptima es cubrir carga industrial propia (bananeras, palmicultoras, empacadoras de Urabá a 650 COP/kWh) y negociar PPA bilateral para excedentes a 220–260 COP/kWh. Esto protege el flujo de caja de la volatilidad de bolsa.

2. **Tramitar certificación UPME antes de la orden de compra.** El Art. 12 (IVA) se aplica en el momento de la factura. Si la certificación llega después de la compra, se pierde el beneficio. Tiempo estimado de trámite UPME: 45–90 días.

3. **Importar directamente desde JA Solar.** El ahorro frente al retail Colombia es USD 56.160 (1.040 módulos × USD 54 diferencia). El proceso de importación con Ley 1715 es exento de arancel y de IVA — simplifica la logística aduanera.

4. **Incluir contrato de O&M en el CAPEX.** USD 7.000/año (9,4 USD/kWp) cubre: limpieza bimestral de módulos, revisión semestral de inversores, monitoreo remoto y mantenimiento preventivo. Empresas locales en Medellín o Urabá pueden ofrecer este servicio.

5. **Contratar seguro de producción (P90).** Algunas aseguradoras colombianas ofrecen cobertura sobre el exceso de pérdida vs P90. Con payback de 1,5 años el riesgo es bajo, pero el seguro fortalece el expediente bancario.

---

## CONCLUSIÓN FINAL

La **Granja FV de Urabá de 743,6 kWp** es un proyecto con fundamentales técnicos y financieros sólidos:

- **Recurso solar excepcional:** 1.721 kWh/m²·año — de los mejores de Colombia
- **Tecnología probada:** JA Solar N-type + SOLIS-60K, configuración optimizada
- **Economía irresistible:** LCOE de 214 COP vs tarifa de 650 COP — genera valor desde el día 1
- **Retorno extraordinario:** TIR >70% con payback <2 años con Ley 1715
- **Resiliencia demostrada:** Positivo incluso en escenario P90 sin beneficios tributarios

La principal variable de riesgo no es técnica ni climática: es **comercial** — asegurar a quién se vende la energía y a qué precio. Resolverla con un contrato PPA o autoconsumo propio convierte este proyecto en un activo financiero de primer nivel para cualquier portafolio de inversión en Colombia.

---

*Informe generado con Calculadora BIPV — calc.innovacionquimica.com.co*
*Datos verificados: 1 de agosto de 2026*
*Todos los valores financieros en USD a TRM 4.000 COP/USD (escenario conservador bancario)*
