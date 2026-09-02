# Investigación bibliográfica: razón Rsh_0/Rsh_ref de CdTe en la literatura académica

**Fecha**: 2 de septiembre de 2026
**Disparador**: tras la migración del motor a PVsyst v6 (`DIAGNOSTICO_MOTOR_PVSYST.md`), quedó
documentado que la razón `R_sh_0/R_sh_ref` que usa `estimar_sdm_desde_ficha()` para CdTe/CIGS
(≈13,76) no tiene una fórmula oficial de PVsyst como sí la tiene cristalino (`4×Rsh_ref`) — se
reutiliza la única razón real calibrada que tiene esta app (ASP-ST1-T40, panel curado con datos
de laboratorio propios). El usuario pidió buscar en la literatura académica algo que valide o
mejore ese fallback. **Esta es una investigación bibliográfica — no se modificó ningún valor del
código.**

## Fuentes revisadas

### 1. Bätzner, Romeo, Zogg, Tiwari (2001), "CdTe/CdS Solar Cell Performance under Low
Irradiance," 17th EC PVSEC Munich, Paper VB1.40

Fuente primaria real de "Batzner et al. 2001", citada en el docstring de `calcular_rsh_cdte()`
desde antes de esta investigación, pero nunca leída directamente hasta ahora. Celdas CdTe/CdS de
laboratorio (proceso HVE, área pequeña, medido en Ω·cm²). Datos reales extraídos de su Figura 5
(Rp vs. G, log-log, leídos con `pymupdf` a 4× zoom por no haber `poppler-utils` disponible):

| G (W/m²) | Rp (Ω·cm²) aprox. |
|---|---|
| ~0,5 | ~4,5-5×10⁵ |
| ~11 | ~7-8×10⁴ |
| ~30 | ~2×10⁴ |
| ~150 | ~4,5×10³ |
| 1000 (STC) | ~1,6×10³ |

Razón implícita Rsh_0/Rsh_ref ≈ **280-300**. Muy por encima del fallback actual de la app (13,76).
**No adoptado**: celdas de laboratorio de 2001, área pequeña, proceso HVE — no representativas de
módulos comerciales modernos. Riesgo real de sobre-ajustar el modelo a un régimen no aplicable.

### 2. Rangel-Kuoppa et al. (2018), "Shunt resistance and saturation current determination in
CdTe and CIGS solar cells. Part 1," Semiconductor Science and Technology 33, 045007,
DOI 10.1088/1361-6641/aab017

Paper solicitado explícitamente por el usuario. Búsqueda agotada: WebSearch, WebFetch directo a
IOPscience (solo extracto, de pago), WebFetch a ResearchGate (HTTP 403), API de Unpaywall
(`is_oa:false`), API de Semantic Scholar (`openAccessPdf.status:"CLOSED"`). **Confirmado: no
existe copia de acceso abierto en ningún repositorio conocido.** No se intentó ningún método
ilegítimo de acceso (sci-hub o similares). Alternativas legítimas ofrecidas al usuario (correo al
autor, compra, acceso institucional) — no ejecutadas, a la espera de decisión del usuario.

### 3. Xu, Gu, Wang, Zhu, Zhang, Zhang (2020), "Influences of Low Intensity on Diode Parameters
of CdTe Solar Cells," Materials (MDPI) 13, 2194, DOI 10.3390/ma13092194

**Acceso abierto real (CC BY 4.0, confirmado en el pie del PDF)**, moderno, cita directamente a
Bätzner 2001 (ref. [10]) y mejora su metodología de extracción. Dos celdas CdTe reales: celda #1
(módulo real de campo, NREL Outdoor Test Facility, proceso close-space sublimation) y celda #2
(fabricada en laboratorio, Chang'an University, proceso CSS, "Rsh por encima de 1000 Ω·cm²").

Datos reales extraídos de su Figura 8 (celda #2, la lectura más limpia de las dos — la celda #1
requiere el promedio de 9 puntos de su Figura 6/7 porque su extracción directa es más ruidosa):

| G (mW/cm²) | Rsh (×10³ Ω·cm²) aprox. |
|---|---|
| ~93 (≈STC) | ~1,35 |
| ~77 | ~1,5 |
| ~63 | ~1,7 |
| ~47 | ~2,1 |
| ~32 | ~2,6 |
| ~15 | ~5,7 |

Razón Rsh(150 W/m²)/Rsh(STC) ≈ **4,2** — pero es solo una **cota inferior** real: la medición se
detiene en G=150 W/m² con la curva todavía en pendiente pronunciada, sin aplanarse, así que el
verdadero Rsh_0 (asíntota a G→0 que usa el modelo PVsyst) sería más alto que ese valor. El paper
no mide más abajo de 150 W/m², así que no es posible extraer un Rsh_0/Rsh_ref definitivo de esta
fuente — solo un límite inferior real.

## Conclusión

Las dos fuentes reales con datos utilizables (Bätzner 2001 y Xu 2020) dan valores reales pero muy
distintos entre sí (≈4,2 de cota inferior vs. ≈280-300), dependiendo del dispositivo, la
antigüedad y el rango de irradiancia medido — ninguna es una fuente autorizada equivalente a la
fórmula oficial `4×Rsh_ref` que PVsyst documenta para cristalino. El fallback actual de la app
(13,76, calibrado con el único panel CdTe real con datos de laboratorio propios, ASP-ST1-T40)
queda dentro del rango real que sugiere la literatura (4-300×), sin ser ni absurdamente bajo ni
absurdamente alto frente a ninguna de las dos fuentes.

**No se modificó ningún valor de `estimar_sdm_desde_ficha()` ni de `tecnologias_bipv.py`.** Este
documento y la sección 25u de la base de conocimiento quedan como referencia bibliográfica de
respaldo para si en el futuro aparece una fuente más autorizada (por ejemplo, si se logra acceder
al paper de Rangel-Kuoppa 2018) o se decide recalibrar ese fallback con más evidencia.
