# La Salle Torre 5 y East2 sobre main (PR #113) — 3-oct-2026

**Clasificación:** reconstrucción provisional, no validación. La escena de la
Torre 5 sigue siendo la reconstrucción del 22-sep (bloque único, ancho SO
asumido); no hay un JSON real de Site Designer de Bosques de Castilla ni torres
vecinas. El registro de decisiones del 22-sep mantiene la validación SO/SE
bloqueada hasta tener esa escena.

## 1. Qué se hizo

- Rama `borrador/lasalle-sobre-main`, creada desde `origin/main` (PR #113).
  Respaldo completo del Codespace en `borrador/validacion-lasalle` (c007c0ba).
- Se trajeron solo archivos que no son de la app: scripts `lasalle_torre5_*`,
  pruebas de La Salle y East2 y `references/`. Los parches de la app sin
  integrar quedan en `references/parches-app-sin-integrar-lasalle.diff`.
- `VERSION_ALGORITMO_FS_POR_SUPERFICIE` = `sombras_3d.ray_casting_por_superficie.v2` ✅.

### Ajustes solo en archivos provisionales

| Archivo | Ajuste | Motivo |
|---|---|---|
| scripts 2, 3 y 4 | Rutas relativas al repositorio (`references/lasalle_torre5_geom/`) | Tenían rutas fijas del Codespace. |
| script 3 | Punto SO a la mitad de `ANCHO_SE_M` (longitud real de la cara SO) | Usaba `ancho_so/2`; solo afectaba las sensibilidades de 12 m y 25 m. |
| script 4 | Huella de la escena calculada en el script; sin el argumento `fuente=` | Ambos venían de los parches sin integrar; main no los tiene. |
| script 4 y prueba La Salle | `read_epw(..., coerce_year=2023)` | El EPW IWEC de El Dorado mezcla 9 años (1982-1997) y el resumen mensual del Motor Óptico daba 180 meses. La app no lee EPW (usa PVGIS), así que no la afecta. |
| prueba East2 | Anclas DC/AC/horas actualizadas | La física multi-superficie ahora aplica la cadena óptica, calidad del módulo, mismatch y cables: −8,1 % en DC. POA (1.038,81) y `p_shade` idénticas. |
| prueba La Salle | El residual frente a la app estándar de referencia pasa de «> 0» a «> −5 %» | La premisa «la app no modela cables ni mismatch» quedó obsoleta: hoy el residual es −2,2 %. |

La orientación de cada fachada se pasa en `geometria_por_superficie` (SE 162°,
SO 249°); no aparece la advertencia `orientacion_desconocida` ✅.

## 2. Tabla comparativa (EPW IWEC Bogotá-El Dorado, SPR-MAX3-400, 10S×7P por fachada, Fronius Primo 15)

| Magnitud | Fachada | 22-sep sin escena | 22-sep con escena central | **Hoy (main #113), escena central** | Hoy + árboles SO | Tesis / la app estándar de referencia |
|---|---|---|---|---|---|---|
| POA (kWh/m²) | SE | 831,73 | 831,73 | **831,64** | 831,64 | 777,3 |
| POA (kWh/m²) | SO | 831,25 | 831,25 | **831,35** | 831,35 | 858,0 |
| E_ac (kWh/año) | SE | 21.766,3 | 16.045,0 | **19.935,1** | 19.935,1 | no publicado |
| E_ac (kWh/año) | SO | 21.743,1 | 13.451,8 | **20.107,4** | 19.462,6 | no publicado |
| Rend. específico (kWh/kWp) | SE | 777,26 | 572,95 | **711,87** | 711,87 | 718,33 (agregado) |
| Rend. específico (kWh/kWp) | SO | 776,43 | 480,35 | **718,02** | 694,99 | 718,33 (agregado) |
| PR | SE | 0,9345 | 0,6889 | **0,856** | 0,856 | 0,868 (agregado) |
| PR | SO | 0,9340 | 0,5779 | **0,864** | 0,836 | 0,868 (agregado) |
| Horas con p_shade > 1 % | SE | 0 % | 20,80 % | **0 %** | 0 % | no publicado |
| Horas con p_shade > 1 % | SO | 0 % | 25,07 % | **0 %** | 16,47 % | no publicado |
| Pérdida por sombra | SE | 0 % | 26,29 % | **0 %** | 0 % | 3,7 % (agregado) |
| Pérdida por sombra | SO | 0 % | 38,13 % | **0 %** | 3,2 % (p_shade media 1,97 %) | 3,7 % (agregado) |
| Asimetría E_ac SO/SE | — | 0,11 % (SE>SO) | 16,16 % (SE>SO) | **0,86 % (SO>SE)** | 2,4 % (SE>SO) | 9,40 % (SO>SE) |

**Sensibilidad al ancho de la fachada SO (12 / 17,29 / 25 m):** hoy los tres
casos dan exactamente lo mismo, porque una torre aislada no sombrea sus propias
fachadas. El 22-sep la asimetría iba de 14,6 % a 17,7 % según el ancho.

Rendimiento agregado de la app (ambas fachadas): 714,9 kWh/kWp frente a 718,33
de la app estándar de referencia (−0,5 %).

## 3. Por qué cambió frente al 22-sep

1. **La sombra del 22-sep era un artefacto.** Una torre aislada y convexa no
   puede hacerse sombra a sí misma. Con el algoritmo anterior, sin la
   orientación de la fachada, las horas con el sol detrás de la fachada se
   contaban como «sombra» (26-38 %). La versión `.v2` de la Spec
   `sombra-cara-trasera` exige la orientación y descarta esas horas: hoy la
   sombra propia es 0 %, lo físicamente correcto.
2. **Cadena de pérdidas multi-superficie (PR #50 a #113).** La energía sin
   sombra baja de 21.766 a 19.935 kWh en SE (−8,4 %). Ahora entran la
   reflexión del vidrio y la suciedad del Motor Óptico, la calidad del módulo,
   el mismatch y los cables. El PR pasa de 0,93 (irreal) a 0,86, que coincide
   con el 0,868 de la app estándar de referencia.

## 4. Veredicto

- **Rendimiento y PR:** ✅ la app coincide con la app estándar de referencia dentro de ±1 %
  (714,9 frente a 718,3 kWh/kWp; PR 0,856-0,864 frente a 0,868).
- **¿Se reproduce la asimetría SO > SE de la app estándar de referencia?** Solo en dirección, no en
  magnitud: 0,86 % frente a 9,40 %.
- **¿La pérdida por sombra se acerca al 3,7 %?** No sin entorno: 0 % con la
  torre sola y ≈ 1,6 % agregado con los árboles asumidos junto a SO.
- **Causa probable de la asimetría: la base climática y la transposición, no
  la sombra.** La app estándar de referencia ya tiene la asimetría en la POA (SO 858,0 frente a SE
  777,3, un 10,4 % más), y eso explica casi todo su 9,40 % en energía. Con el
  EPW IWEC, la app da la misma POA en las dos fachadas (831,4 y 831,6). La
  diferencia está en el recurso (otra base de datos meteorológica u otro
  modelo de difusa), antes de cualquier sombra.
- **Causa probable de la brecha de sombra (0-1,6 % frente a 3,7 %): torres
  vecinas ausentes en la escena.** La reconstrucción solo tiene la Torre 5 y
  los árboles asumidos.

## 5. Siguientes pasos sugeridos

1. Conseguir la base climática que usó la tesis (Meteonorm u otra) o su POA
   mensual por fachada, para aislar la diferencia de recurso.
2. Escena real de Site Designer de Bosques de Castilla con las torres vecinas.
3. Hasta entonces, mantener La Salle como reconstrucción provisional, no como
   validación.

## 6. Pruebas

- Pruebas de La Salle y East2 sobre main (PR #113): 29 pasan, tras los ajustes de la sección 1.
- Suite completa de la rama: **2.508 pasan**, sin fallos.
- Datos de la tesis para la escena real: `references/lasalle-torre5-datos-escena-real.md` y
  `references/lasalle-sombra-por-modulo-referencia-tablas-19-20.csv`.
