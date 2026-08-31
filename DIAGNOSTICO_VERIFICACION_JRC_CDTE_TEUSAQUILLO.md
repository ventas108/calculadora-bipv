# Verificación cruzada CdTe: power-rating model JRC/Huld vs. SDM De Soto (Teusaquillo)

**Fecha**: 31 de agosto de 2026
**Disparador**: el usuario pidió analizar, "como un científico", un paper académico real
(`S2214157X18303940.htm` y la familia de papers relacionados de Kumar/Sudhakar/Samykano sobre
CdTe BIPV bajo clima tropical) para sacarle provecho práctico a la app. La corrida real del
proyecto Teusaquillo (fachada CdTe vertical, ver `FICHA_PVSYST_TEUSAQUILLO.md`) había dado
PR=100,6%/101,2% con el motor principal — inusualmente alto para un sistema real, y una duda
abierta desde el 27-ago-2026.

## Fuente académica real (no un resumen — texto completo verificado)

De los 3 papers relacionados encontrados, se logró descargar y leer el **texto completo** de:

> Kumar, N.M. (2019). "Performance of single-sloped pitched roof cadmium telluride (CdTe)
> building-integrated photovoltaic system in tropical weather conditions." *Beni-Suef University
> Journal of Basic and Applied Sciences*, 8:2. DOI: 10.1186/s43088-019-0003-2 (Open Access, CC BY).

**Corrección importante a la premisa inicial del usuario**: este paper (y con alta probabilidad
los otros 2 de la misma familia de autores, dado que comparten metodología) usa **PVGIS**
(European Commission JRC), no PVsyst, para simular el sistema.

Metodología real (Tabla 2 del paper): power-rating model de Huld et al. (2011), un ajuste
empírico polinómico calibrado contra mediciones reales de módulos CdTe en el ESTI europeo —
NO un circuito equivalente físico como el SDM De Soto que usa esta app.

```
P(I',T') = I'·P_STC·[1 + t1·ln(I') + t2·ln(I')² + t3·T' + t4·T'·ln(I') + t5·T'·ln(I')² + t6·T'²]
Coeficientes CdTe: t1=-0,046689  t2=-0,072844  t3=-0,002262  t4=0,000276  t5=0,000159  t6=-0,000006
T_módulo: Faiman con n=23,37, n*=5,44 (coeficientes de temperatura específicos de CdTe)
```

Resultados reales del paper (CdTe, techo, 7 kWp, Malasia tropical, 7 ángulos 15°-45°):
**PR entre 74,92% y 77,36%**, pérdidas totales entre -23,63% y -25,08%. Un segundo paper de la
misma familia (fachadas CdTe, resumen consultado) reporta **PR entre 66,42% y 76,26%**. Ningún
estudio de la literatura revisada reporta PR por encima de 78% para CdTe BIPV bajo clima tropical.

## La verificación: implementar el modelo y correrlo contra datos REALES de Teusaquillo

Nuevo módulo `calculos/modelo_jrc_cdte.py`: reimplementa el power-rating model con los
coeficientes CdTe exactos del paper, usando `pvlib.temperature.faiman()` (ya en el repo) con
`u0=23,37, u1=5,44` en vez de los genéricos de pvlib (calibrados para c-Si). 6 tests nuevos,
incluyendo el ancla física más simple: a condiciones STC exactas (I'=1, T'=0), el modelo debe
reproducir exactamente P_STC (el corchete se reduce a 1).

`scripts/verificar_jrc_teusaquillo.py`: descarga el TMY REAL de PVGIS para Bogotá (mismas
coordenadas que usa la app: 4,711°N, -74,072°O, 2.600 m), calcula la POA con
`calculos.solar.calcular_poa()` (el mismo pipeline Hay-Davies que usa la app en producción, no
uno paralelo) para una fachada vertical (tilt=90°, azimut=180°), y corre el modelo JRC/Huld sobre
esa serie horaria real con los 128 módulos ASP-ST1-T40 (8,064 kWp).

## Resultado

| | POA anual | E_dc anual | **PR** |
|---|---|---|---|
| App (SDM De Soto, sin Motor Óptico) | 807,8 kWh/m²/año | 6.554 kWh/año | **100,6%** |
| **JRC/Huld (este script, mismos datos reales)** | 807,8 kWh/m²/año | 5.825 kWh/año | **89,4%** |
| Literatura (Kumar, CdTe techo, Malasia tropical) | — | — | 74,9%-77,4% |
| Literatura (Kumar, CdTe fachada, Malasia tropical) | — | — | 66,4%-76,3% |

La POA anual coincide EXACTAMENTE (807,8 kWh/m²/año) entre el script y la app — confirma que
ambos parten de los mismos datos reales de recurso solar, así que la diferencia de PR es
atribuible al modelo de módulo, no a una discrepancia de entrada.

## Conclusión científica

El modelo JRC/Huld, corriendo con los mismos datos reales de Teusaquillo, da un PR **11,2 puntos
porcentuales más bajo** que el motor SDM principal de la app (89,4% vs 100,6%) — un modelo de
CdTe completamente independiente, calibrado contra mediciones reales de otro laboratorio, no
reproduce el >100%.

Al mismo tiempo, el 89,4% de JRC sigue estando **12 a 23 puntos por encima** del rango que reporta
la literatura real para CdTe BIPV en clima tropical (66-77%) — pero esto SÍ tiene una explicación
física razonable: Bogotá (14°C media, 2.600 m) es mucho más fría que Malasia tropical (donde CdTe
opera con más pérdida térmica), y el coeficiente de temperatura de CdTe favorece climas fríos. Un
PR más alto que Malasia es esperable; el modelo JRC ya incorpora esa diferencia climática real
(usa T_ambiente y viento reales de Bogotá) y aun así queda muy por debajo del resultado de la app.

**Con esto, la hipótesis (b) queda más respaldada que la (a)**: el >100% de PR del motor principal
de la app parece ser, con evidencia cuantitativa (no solo sospecha), un artefacto de la curva
FF-vs-irradiancia calibrada específicamente para el ASP-ST1-T40 en el SDM De Soto — no un
comportamiento físico genuino de CdTe a baja irradiancia/clima frío, que el modelo JRC (calibrado
también para CdTe, pero contra mediciones de otro panel/laboratorio) no reproduce en la misma
magnitud.

## Qué NO se concluye (límites honestos de esta verificación)

- No es una prueba definitiva de bug — es evidencia convergente de 2 fuentes independientes
  (literatura + modelo alterno) apuntando en la misma dirección. El resultado real de PVsyst
  (pendiente, ver `FICHA_PVSYST_TEUSAQUILLO.md`) sigue siendo el tercer punto de comparación más
  directo y aún no está disponible.
- El modelo JRC/Huld está calibrado contra módulos CdTe genéricos de laboratorio, no contra el
  ASP-ST1-T40 específico (que sí tiene su propia curva FF-vs-irradiancia calibrada, validada
  contra Batzner et al. 2001) — es razonable esperar CIERTA diferencia entre ambos modelos incluso
  si el SDM de la app fuera correcto; la pregunta es si 11 puntos es "cierta diferencia esperada" o
  señal de una calibración específicamente inflada. No se decide aquí cuál es.
- Este módulo es una verificación cruzada puntual, no reemplaza al motor principal ni se integró a
  la UI de la app — queda como herramienta de diagnóstico en `scripts/`, disponible para volver a
  correrla si se ajusta la calibración del panel o cuando llegue el resultado real de PVsyst.

## Verificación técnica

6 tests nuevos en `tests/test_modelo_jrc_cdte.py` (ancla STC exacta, comportamiento nocturno,
orden de magnitud a baja irradiancia, diferenciación de los coeficientes de temperatura CdTe vs.
los genéricos de pvlib, caso sintético día completo, caso sin irradiancia). Suite completa:
**827/827**. El script de verificación reutiliza `calculos.solar.obtener_tmy_pvgis()` y
`calculos.solar.calcular_poa()` reales (no una reimplementación paralela) — la coincidencia exacta
de la POA anual (807,8 kWh/m²/año) confirma que la comparación es de manzanas contra manzanas.
