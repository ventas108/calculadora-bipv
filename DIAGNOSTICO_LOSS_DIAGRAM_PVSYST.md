# Tabla de balance energético alineada con el Loss Diagram de PVsyst

**Fecha**: 1 de septiembre de 2026
**Disparador**: el usuario armó una ficha manual (`PRUEBA PVSYST VS MI APP.txt`) para replicar el
proyecto real Teusaquillo en PVsyst y comparar contra el motor de la app — el PR de la app salió
100,6%–101,2% (inusual, típico real 75–85%). Mientras preparaba esa comparación encontró un paper
científico (Kadir et al. 2023, *J. Phys.: Conf. Ser.* 2550 012005, DOI
10.1088/1742-6596/2550/1/012005 — simulación PVsyst 7.2 de un sistema on-grid de 16,20 kWp c-Si en
Malasia) y pidió analizarlo para construir "nuestro seguimiento de cálculo para comparar con
PVsyst".

## Qué aporta realmente el paper

No los números de Malasia en sí (clima tropical, panel c-Si distinto, nada comparable
directamente a Teusaquillo) — sino la **estructura oficial del "Loss Diagram" de PVsyst**: la
cascada de 12 etapas nombradas con la que PVsyst reporta cualquier simulación, de GHI a energía
inyectada a red:

`GHI → POA (transposición) → IAM factor → Soiling loss → Effective irradiation →
[eficiencia STC] → Array nominal energy → irradiance level loss → temperature loss →
module quality loss → mismatch loss (módulos/strings) → ohmic wiring loss →
Array virtual energy at MPP → inverter efficiency loss → (over-power/voltage/current) →
Available energy at inverter output = energía a red`

Y confirma con un caso real y auditable que un PR ~80% es lo típico esperado para un sistema
on-grid normal — el mismo rango que la ficha de Teusaquillo ya anticipaba como referencia sana.

## Qué tenía la app antes de este cambio

- `calculos/produccion.py::perdidas_desglosadas()` — ya era una tabla de balance con espíritu
  idéntico (E_ref STC → efecto SDM → E_dc → pérdida inversor → clipping → E_ac), pero:
  - IAM y soiling se calculaban aparte en `calculos/motor_optico.py::cascada_optica()` y llegaban
    a Producción ya fundidos en un único `factor_pr_mismatch` — sin filas propias en la tabla.
  - La fila "② Efecto SDM" comparaba siempre contra la **POA bruta**, no contra la POA ya
    corregida por IAM+soiling.

## El riesgo real encontrado antes de tocar nada (y descartado)

Antes de extender la tabla, se verificó que NO hay doble conteo de temperatura entre Motor Óptico
y el SDM: `pages/6_📊_Producción.py` ya usa `poa_sin_termico_df` (IAM+soiling, SIN el factor
térmico `f_term` de Motor Óptico) como la irradiancia real que alimenta el SDM — con un comentario
explícito en el código ("Usar poa_efectiva_df (con f_term) causaría doble conteo térmico"),
evidencia de que esto ya se había corregido en una sesión anterior. La corrección térmica real la
aplica solo el SDM, vía `T_cell(k_bipv)`. `poa_efectiva_df` (con `f_term`) se reserva solo para
visualización/Financiero. Este cambio no toca esa separación — se construye sobre ella.

## Qué se corrigió/agregó

`perdidas_desglosadas()` ahora acepta un parámetro opcional `motor_optico_summary` (el dict que ya
devuelve `cascada_optica()`, disponible en `session_state["motor_optico_summary"]` cuando 🔆 Motor
Óptico corrió). Si trae las claves reales, inserta 2 filas nuevas ANTES de "② Efecto SDM":

- **①a Pérdida IAM** — `P_stc × POA_post_IAM`, Δ = `-P_stc × pérdida_IAM` (kWh/m² real de
  `cascada_optica()`).
- **①b Pérdida soiling** — igual, con la POA post-soiling.

Y **la referencia de "② Efecto SDM" cambia de la POA bruta a la POA post-IAM+soiling** — sin este
cambio, IAM y soiling habrían quedado contados dos veces: una en sus propias filas nuevas, otra
escondidos dentro del delta de SDM (que ya corre sobre irradiancia corregida). Verificado con
aritmética exacta en los tests (no solo "se ve razonable").

Si no se pasa `motor_optico_summary` (o Motor Óptico no corrió en la sesión), la tabla sale
**exactamente igual que antes** — comportamiento por defecto sin cambios, nunca inventa un
desglose que no se calculó de verdad.

## Lo que deliberadamente NO se modela (declarado, no ocultado)

Dos categorías del Loss Diagram de PVsyst no tienen equivalente en esta app hoy — y la tabla lo
dice explícitamente en un `st.caption()`, no las omite en silencio:

- **"Module quality loss"** — PVsyst la usa para modelar dispersión de fabricación entre módulos
  de un mismo lote; esta app no tiene esa información por panel.
- **"Ohmic wiring loss"** — pérdida resistiva de cableado DC/AC; no hay un modelo de longitud de
  cable / calibre / caída de tensión en esta app todavía.

## Actualización (1-sep-2026): irradiancia vs. temperatura, separadas de verdad

El usuario preguntó explícitamente qué herramientas hacían falta para separar "irradiance level
loss" de "temperature loss" como hace PVsyst. La respuesta, verificada leyendo el código real: **no
hacía falta nada externo** — el motor SDM (`_calcular_pmax_vectorizado()` / `_pmp_iv_vectorizado()`
en el camino Motor IV) YA se llamaba una segunda vez internamente, con la misma `G_eff` real pero
`T_cel` fija en 25°C, para calcular `perdida_temp_kWh` (la pérdida por horas calientes). Ese
resultado intermedio (`pmax_stc_g` / `pmp_stc_g`) nunca se sumaba ni se exponía como su propio
total — solo hacía falta sumarlo.

**Qué se agregó**: una nueva clave `E_dc_a_T25_kWh` en el dict que devuelven tanto
`calculos/produccion.py::simular_produccion_anual()` como `calculos/produccion_iv.py::
simular_produccion_iv()` — la energía anual con la irradiancia real de cada hora pero temperatura
de celda fija en 25°C. Mismo SDM ya validado, sin ninguna fórmula física nueva — solo una segunda
corrida con un insumo distinto.

`perdidas_desglosadas()` ahora usa esa clave (si está presente) para descomponer la fila "②
Efecto SDM" en:
- **②a Pérdida por nivel de irradiancia** (T=25°C fijo) — no linealidad del panel a baja luz,
  aislada de temperatura.
- **②b Efecto temperatura** (T real vs. 25°C) — el efecto neto de temperatura, con signo (ganancia
  en clima frío, pérdida en clima cálido).

Los dos deltas suman **exacto** el delta ya existente de la fila ②, verificado con aritmética
exacta en tests — es una descomposición, no una estimación aparte que podría no cuadrar. Se
conservó además la fila informativa vieja "↳ Solo horas calientes" (que ignora las horas con
ganancia por frío) porque responde una pregunta distinta y ya alimentaba otra parte de la UI.

Si `res` no trae `E_dc_a_T25_kWh` (resultado de una versión anterior en caché, o un caller propio
que no pasa por estas 2 funciones), la fila ② queda combinada exactamente como antes — mismo
principio de nunca inventar un desglose que no se calculó de verdad.

5 tests nuevos en `tests/test_perdidas_desglosadas_pvsyst.py`: sin la clave no aparecen las filas,
con la clave aparecen con los valores correctos, **los dos deltas reconcilian exacto contra el
delta de ②** (el test que garantiza que no se pierde ni se inventa energía), el split funciona
también sin Motor Óptico, y `produccion_iv.py` expone el mismo campo. Suite completa: **917/917**.

## Verificación

6 tests nuevos en `tests/test_perdidas_desglosadas_pvsyst.py` con aritmética exacta y sintética
(número redondos, no datos reales — esto prueba el bookkeeping de la función, no una afirmación
física; la física de SDM/IAM/soiling ya tiene su propia cobertura real en otros archivos de test):
compatibilidad hacia atrás exacta sin `motor_optico_summary`, `{}` se comporta igual que `None`,
las filas IAM/soiling se insertan con los valores correctos, **"② Efecto SDM" ya NO cuenta
IAM+soiling dos veces** (el bug concreto que este cambio evita), el `% de E_ref` sigue normalizado
contra la POA bruta original (igual que el "% of GlobHor" de PVsyst), y el resultado final (E_ac)
no cambia se pase o no el resumen — el desglose es solo de presentación.

2 tests nuevos en `tests/test_pagina_produccion_loss_diagram.py` (patrón AST/substring): la página
pasa el resumen real a la tabla, y declara explícitamente las 2 categorías no modeladas.

Suite completa: **911/911**.
