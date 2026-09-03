# Rsh_exp de CdTe (Sandia PVPMC=2.0 / PVsyst≈3.0) — investigado, NO se activa

**Fecha**: 2 de septiembre de 2026
**Disparador**: revisando la página oficial de PVPMC (PV Performance Modeling Collaborative,
Sandia National Laboratories) sobre el modelo de módulo PVsyst, aparece una tabla de valores por
defecto de `Rsh_exp` por tecnología: **CdTe = 2.0**, µc-Si = 3.0, todas las demás = 5.5. El
catálogo real de la app (`datos/tecnologias_bipv.py::CONSTANTES_TECNOLOGIA["CdTe"]["c_Rsh"]`) usa
**5.5** — el mismo valor genérico que cristalino, no 2.0. Esto ya se había detectado antes, de
forma independiente, investigando la documentación oficial de PVsyst (sección 25t del manual:
"Rsh_exp=5,5 'constante independiente de la tecnología' (excepción real CdTe~3)") y había quedado
sin corregir en el código.

## Hipótesis a probar

Dado que el defecto estructural de la "joroba" de eficiencia relativa >100% en CdTe (que motivó
reemplazar el SDM por JRC/Huld como motor de energía, ver `DIAGNOSTICO_JRC_HULD_PRIMARIO_CDTE.md`)
viene de la forma de la curva `Rsh(G)` exponencial, y `Rsh_exp` controla directamente esa forma,
se investigó si usar el valor real de CdTe (2.0 según Sandia, ~3.0 según PVsyst) en vez del 5.5
genérico reduce o elimina esa joroba, para el panel real ASP-ST1-T40.

## Metodología

Se recalculó la curva de eficiencia relativa (`Pmax(G,T=25°C)/Pmax_stc / (G/1000)`) con
`pvlib.pvsystem.calcparams_pvsyst` usando los parámetros YA calibrados del panel real
(`I_L_ref=0.8152A, I_o_ref=1.35e-13A, R_s=25.5090Ω, R_sh_ref=1340.6Ω, R_sh_0=18450.0Ω`,
`gamma_ref=1.0922, N_s=141` — sin cambios), variando SOLO `R_sh_exp` entre 5.5 (actual), 3.0
(PVsyst) y 2.0 (Sandia PVPMC).

## Resultado — contraintuitivo: empeora el problema, no lo mejora

| `Rsh_exp` | Pico de eficiencia relativa | G del pico | FF@G=200W/m² |
|---|---|---|---|
| 5.5 (actual) | 106.1% | 200 W/m² | 75.02% |
| 3.0 (PVsyst) | 109.6% | 300 W/m² | 77.09% |
| 2.0 (Sandia) | 111.0% | 300 W/m² | 77.80% |

Real de laboratorio (Batzner et al. 2001): FF@G=200W/m² = 76.28%.

**Bajar `Rsh_exp` empeora la joroba** (106.1%→109.6%→111.0%), aunque el ajuste puntual de FF a
G=200W/m² mejora ligeramente con 3.0 (77.09%, 0.81pp sobre el real, contra 1.26pp por debajo con
5.5). Es decir: un solo punto de ajuste (FF en un G específico) y la forma completa de la curva
(la joroba en todo el rango 100-500 W/m²) responden en direcciones distintas a este parámetro —
no se puede optimizar ambos con un solo número.

## Por qué no es una comparación mezclada inválida (a diferencia del episodio d²/µτ)

A diferencia del intento de activar recombinación (`DIAGNOSTICO_RECOMBINACION_CDTE.md`), aquí NO
se mezclaron calibraciones de fuentes distintas de forma incoherente: se mantuvo el mismo
`R_sh_0=18450Ω` y `R_sh_ref=1340.6Ω` ya calibrados contra los 10 puntos reales de laboratorio
(XLSM auditado), cambiando solo el exponente. Es una prueba de sensibilidad legítima, no una
mezcla de dos ajustes incompatibles. El resultado es real y directo: este `R_sh_0` fue calibrado
específicamente CON `c_Rsh=5.5` — un ajuste conjunto nuevo (minimax de `R_sh_0` y `R_s` contra los
10 puntos reales, esta vez con `c_Rsh=2.0` o `3.0` desde el inicio) podría en principio dar una
curva distinta, pero no se hizo aquí por no tener certeza de que el origen de esos 10 puntos sea
un dataset externo verdaderamente independiente (revisando el XLSM auditado, las hojas
`FF_vs_Irradiancia`/`FF_vs_G_TReal` contienen SALIDA del propio motor de la app, no mediciones de
laboratorio crudas etiquetadas como tales) — haría falta localizar el origen real de esos 10
puntos antes de invertir en un refit completo.

## Conclusión

No se activa `Rsh_exp` específico de CdTe (2.0 ni 3.0) en el código. Evidencia directa: con los
parámetros ya calibrados y validados del panel real, ese cambio agrava el defecto estructural que
JRC/Huld ya resuelve como motor de energía. Confirma indirectamente que la solución correcta para
CdTe en Producción era reemplazar el motor (JRC/Huld), no seguir ajustando parámetros dentro de la
familia de modelos de un diodo con Rsh exponencial — la forma funcional en sí es la limitación,
no un valor de exponente mal elegido. `c_Rsh=5.5` permanece sin cambios para CdTe en
`CONSTANTES_TECNOLOGIA`; sigue siendo relevante solo para Motor IV/Mismatch/MPPT combinado
(que siguen en SDM para todas las tecnologías) y no para Producción de CdTe (JRC/Huld, no usa
`Rsh_exp` en absoluto).

## Verificación

Investigación numérica pura — ningún valor de código cambió. Sin tests nuevos (no hay
comportamiento nuevo que anclar; el catálogo real sigue con `c_Rsh=5.5` para CdTe, sin cambios).
Suite completa sin modificar: 942/942 (ver commits previos de la sesión).
