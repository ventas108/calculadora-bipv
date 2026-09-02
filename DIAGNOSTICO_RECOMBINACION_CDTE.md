# Modelo de recombinación en capa intrínseca (Merten 1998 / PVsyst) — implementado, no activado

**Fecha**: 2 de septiembre de 2026
**Disparador**: al validar el motor CdTe (`DIAGNOSTICO_MOTOR_PVSYST.md`) contra una corrida real
de PVsyst 8.1.5 para el panel ASP-ST1-T40 (Teusaquillo, fachada vertical), quedó un patrón mensual
sin explicar: nuestro motor daba un PR aislado (irradiancia+temperatura) casi plano todo el año
(88-104%), mientras PVsyst real variaba fuerte por mes (67%-81%, cota inferior en marzo/septiembre).
Ajustar Gamma/Rsh/Rs no cerraba esa forma estacional. Revisando la pestaña "Pérdida de
recombinación" del propio PVsyst para ese módulo (reconstruido y validado), apareció un parámetro
real y activo — `d²/µτ = 1,13 1/V` — que nuestro motor no modela en absoluto.

## La física real (Merten et al. 1998 + documentación oficial de PVsyst)

Merten, Asensi, Voz, Shah, Platz, Andreu (1998), "Improved Equivalent Circuit and Analytical Model
for Amorphous Silicon Solar Cells and Modules," IEEE Trans. Electron Devices 45, 423-429,
DOI 10.1109/16.658676 — adoptado por PVsyst para capa fina CdTe/a-Si (confirmado en su página
oficial "Thin film modules: Recombination losses"). Agrega una corriente de recombinación en la
capa intrínseca (uniones p-i-n) al modelo estándar de un diodo:

```
I = I_L − I_rec − I_o[exp(q(V+I·Rs)/(N_s·γ·k·T)) − 1] − (V+I·Rs)/R_sh
I_rec = I_L · (d²/μτ) / [N_s·V_bi − (V + I·Rs)]
```

`d²/μτ` (grosor² de la capa intrínseca ÷ longitud de difusión) y `V_bi` (voltaje interno de la
unión, típico ~0,9V para uniones amorfas) son los dos parámetros nuevos. El término es puramente
**aditivo** — no reemplaza I_L, I_o, Rs, Rsh, Gamma, que siguen siendo el mismo modelo PVsyst v6
ya migrado.

## pvlib ya lo implementa — verificado en la versión pineada

`pvlib.singlediode.bishop88()` / `bishop88_mpp()` / `bishop88_i_from_v()` / `bishop88_v_from_i()`
aceptan `d2mutau` y `NsVbi` (=N_s×V_bi) directamente, ambos en **Voltios**. Verificado con
`pip download pvlib==0.11.1` (la versión exacta pineada en `requirements.txt`, no la que estaba
instalada localmente por otra sesión — mismo tipo de riesgo que el bug real de
`fit_desoto_batzelis` documentado en `modelo_iv.py`): el parámetro existe en esa versión exacta.

## Ambigüedad de unidades resuelta con el usuario

PVsyst/pvlib documentan `d²/µτ` en **Voltios** (valor típico ~1,4V para paneles amorfos). La
pantalla real de PVsyst 8.1.5 mostró **"1,13 1/V"** (voltios inversos) — confirmado explícitamente
por el usuario tras pedirle que revisara el texto literal. Se interpreta como el inverso:
`d2mutau_pvlib = 1 / 1.13 = 0.885 V` — mismo orden de magnitud que el "~1,4V" típico documentado,
razonable para una tecnología (CdTe) distinta a la que Merten estudió originalmente (a-Si).

## Implementación (código nuevo, real, testeado)

- `calculos/modelo_iv.py`:
  - `_parametros_recombinacion(panel)` — lee `panel["d2mutau"]`/`panel["V_bi"]`; por defecto
    (ausentes) devuelve `(0.0, inf)`, que anula el término y reproduce EXACTO el modelo estándar
    (verificado bit-a-bit, `rtol=1e-9`, contra 5 paneles reales del catálogo).
  - `calcular_pmax_vectorizado(G, T_cel, panel)` — nueva función centralizada: llama
    `trasladar_parametros_gt()` y decide entre `pvlib.pvsystem.singlediode` (sin recombinación,
    comportamiento idéntico a antes) o `pvlib.singlediode.bishop88_mpp` (con recombinación) según
    si el panel trae `d2mutau` calibrado.
  - `resolver_curva_iv()` — mismo criterio, usando además `bishop88_i_from_v`/`bishop88_v_from_i`
    para Isc/Voc/curva completa cuando aplica.
- `produccion.py` y `produccion_iv.py` — ahora llaman `calcular_pmax_vectorizado()` en vez de
  reimplementar la llamada a `pvsystem.singlediode()` por su cuenta (centralización adicional,
  mismo espíritu que `DIAGNOSTICO_MOTOR_PVSYST.md`).
- `mismatch_bypass.py` — rama con `bishop88_mpp`/`bishop88_i_from_v` cuando `d2mutau>0`.
- `mppt_combinado.py` — `_params_grupo()` y `_voc_grupo()` extendidos: `d2mutau` no escala con
  serie/paralelo (propiedad de material, por celda); `NsVbi` sí escala ×N_serie, igual que `nNsVth`.

## Bug real encontrado y corregido durante la implementación

`calcular_pmax_vectorizado()` usaba `np.asarray(...)` en vez de `np.array(...)` para envolver el
resultado de `pvsystem.singlediode()` — `np.asarray()` no copia si el array ya es un ndarray, y el
que devuelve pvlib internamente puede ser de solo lectura. Los 3 llamadores mutan el resultado
in-place (`pmax[G < 5.0] = 0.0`), así que esto rompía con `ValueError: assignment destination is
read-only` — no en el panel CdTe (que no llega a esa rama), sino en **todos** los paneles normales
que pasan por la rama sin recombinación (49 tests fallaron en cascada, incluida toda la suite de
simulación). Corregido usando `np.array()` (copia) en ambas ramas.

## Por qué NO se activó para ASP-ST1-T40 (ni ningún panel real)

Se probó agregar `d2mutau=0.885V`/`V_bi=0.9V` directamente al panel ASP-ST1-T40 ya calibrado
(R_s=25,51Ω, R_sh_ref=1340,6Ω — valores reales, ajustados contra los 10 puntos de la hoja
`FF_vs_Irradiancia` del XLSM auditado, **sin** término de recombinación). Resultado:
**FF@G=200W/m² cayó a 47,06%, contra el 76,28% real medido en laboratorio** (Batzner et al. 2001)
— una ruptura catastrófica, no un desvío de tolerancia. Causa: nuestro R_s real ya "absorbe"
implícitamente el efecto de recombinación (fue ajustado SIN ese término aparte, así que una parte
de su valor real de 25,51Ω está compensando exactamente lo que ahora el nuevo término también
resta) — sumarlos por separado cuenta el mismo efecto dos veces.

Activarlo correctamente para este panel requeriría re-calibrar **I_L_ref, I_o_ref, R_s, R_sh_ref
TODOS JUNTOS** contra los 10 puntos reales de laboratorio, con el término de recombinación ya
incluido desde el inicio del ajuste — no se hizo por no tener esos puntos crudos disponibles en
esta sesión.

## Validación del mecanismo en sí (aislado de la calibración del panel real)

Con el set COMPLETO de parámetros que PVsyst 8.1.5 ajustó de verdad para el módulo reconstruido
(R_s=12,347Ω, R_sh_ref=2600Ω, γ=2,15, d2mutau=0,885V, V_bi=0,9V — ninguno mezclado con nuestros
propios valores de laboratorio), resolviendo I_L_ref/I_o_ref por autoconsistencia en Isc=0,80A/
Voc=116,0V: **Pmax_STC=60,87W, a 0,5% del 60,59W que PVsyst calculó internamente para esa misma
corrida** (implícito de su eficiencia STC reportada, 8,45%). El mecanismo reproduce bien el ajuste
real de PVsyst cuando se usa con SU set de parámetros, consistente.

**Pero no cierra la brecha mensual que buscábamos explicar**: con este set completo, el PR aislado
mensual de nuestro motor sigue relativamente plano (89,9%-91,0%, brecha de 9,0 a 24,0 puntos contra
PVsyst real) — prácticamente igual que sin el término (91,04% anual, brecha 9,7-24,6 puntos). El
patrón estacional real de PVsyst (mínimo marcado en marzo/septiembre) sigue sin explicarse.

## Hipótesis abiertas para el patrón mensual

1. ~~`V_bi=0,9V` es un valor típico genérico (Merten 1998, a-Si), no calibrado para CdTe.~~
   **Investigada y descartada (2-sep-2026)**: tanto la literatura real de CdTe como la propia
   documentación de pvlib/PVsyst confirman que **0,9V es el valor por defecto que PVsyst usa para
   CUALQUIER unión simple** (a-Si o CdTe por igual) — solo tándem/triple-unión usan defaults
   distintos (1,8V/2,7V). Ya se usó ese mismo valor. Descartada como causa: no estábamos
   desviados del propio default real de PVsyst.
   Nota aparte (no descarta el mecanismo, pero sí matiza su base física): CdTe comercial suele ser
   una unión p-n, no p-i-n como el a-Si real que motivó el modelo de Merten — el ajuste de d²/µτ
   para CdTe es, según la propia documentación de PVsyst, una adaptación semi-empírica del modelo,
   no una derivación de primeros principios para esta tecnología.
2. ~~PVsyst documenta una tercera corrección para capa fina: corrección espectral.~~
   **Investigada y descartada (2-sep-2026)**: PVsyst tiene DOS modelos espectrales distintos —
   CREST/Loughborough (para a-Si, rango real ~30%, UF 0,5-0,65, no calibrado para CdTe) y
   FirstSolar (Lee & Panchula 2016, IEEE PVSC, específico para CdTe, fórmula
   `M = c₁+c₂·AMₐ+c₃·Pw+c₄·√AMₐ+c₅·√Pw+c₆·AMₐ/√Pw`, con AMₐ=masa de aire absoluta, Pw=agua
   precipitable). Ambos disponibles en pvlib (`pvlib.spectrum.spectral_factor_firstsolar`,
   verificado en la versión pineada 0.11.1) sin necesidad de reimplementar física. Calculado el
   rango real para Teusaquillo (altitud 2620m, AMₐ 0,7-1,8, Pw 1-4cm plausibles): **M entre 0,987
   y 1,041 — solo ±2-4%**, un orden de magnitud menor que el ~20-30 puntos de brecha mensual que
   buscamos explicar. Además, ninguna corrida de PVsyst que revisamos mostró una línea de pérdida
   espectral en su diagrama, sugiriendo que ni siquiera estaba activada. **Descartada como
   explicación principal** — quedaría como mejora de precisión menor si se implementa a futuro,
   no como el mecanismo que cierra la brecha.
3. Posible diferencia en cómo PVsyst pondera/distribuye la irradiancia sub-horaria real vs. el TMY
   horario promedio que usamos. **Parcialmente investigada (2-sep-2026)**: se verificó que
   `calculos.solar.calcular_poa()` (misma fuente PVGIS TMY que reporta PVsyst, mismo sitio) pasa
   limpio el chequeo de cierre físico `verificar_consistencia_radiativa()` que existe
   específicamente para atrapar la clase de bug documentada en
   `DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md` (desfase de huso horario en TMY) — 0 de 4109 horas
   inconsistentes, diferencia media 0,3 W/m². **Nuestro propio pipeline de irradiancia/posición
   solar está limpio.** Sigue sin poder descartarse un desfase o resampleo distinto del lado de
   PVsyst (su archivo `.MET` interno vs. nuestra llamada en vivo a la misma API) — no verificable
   sin una exportación horaria real de PVsyst, que ya se intentó obtener sin éxito (solo se pudo
   extraer resumen mensual).

## Estado actual de la investigación (2-sep-2026)

De las 3 hipótesis abiertas para el patrón mensual, **2 quedaron descartadas** (corrección
espectral: magnitud real demasiado pequeña, ±2-4%; V_bi: ya se usaba el valor por defecto real de
PVsyst) y la tercera (granularidad sub-horaria / desfase TMY del lado de PVsyst) **no se puede
avanzar más sin datos que no logramos obtener** (exportación horaria real de PVsyst). El patrón
estacional real de PVsyst (PR aislado 67%-81% variando por mes) sigue sin una causa identificada
más allá de las ya investigadas y descartadas.

## Verificación

- 6 tests nuevos (`tests/test_recombinacion_cdte.py`): equivalencia exacta con d2mutau=0 (5 paneles
  reales, rtol=1e-9), no-regresión de escribibilidad del array (el bug real de arriba), reducción
  de Pmax al activar el mecanismo, y ancla real de STC (60,87W vs 60,59W implícito de PVsyst,
  0,5%).
- `test_consistencia_sdm_entre_modulos.py::test_las_5_implementaciones_centralizan_en_trasladar_parametros_gt`
  actualizado para reflejar que `produccion.py`/`produccion_iv.py` ahora centralizan un nivel más
  arriba (`calcular_pmax_vectorizado`), mientras `mismatch_bypass.py`/`mppt_combinado.py` siguen
  necesitando el tuple completo de `trasladar_parametros_gt()`.
- Suite completa: **933/933** (927 previos + 6 nuevos).
- Ningún panel del catálogo (incluido ASP-ST1-T40) cambia de comportamiento — `d2mutau` queda en
  0.0 (inactivo) para todos.
