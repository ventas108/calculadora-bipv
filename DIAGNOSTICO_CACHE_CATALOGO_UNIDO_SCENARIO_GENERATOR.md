# Causa real de la lentitud de CI: catálogo unido reconstruido en cada intento del muestreo

**Fecha**: 4 de septiembre de 2026
**Disparador**: el usuario pidió auditar por qué el CI venía tardando cada vez más (5 → 93 min en
14 corridas del día), sospechando que no era normal. Se le dijo primero (incorrectamente) que no
era el catálogo, basándose solo en que el tiempo TOTAL de la suite se mantenía estable en local
(~20-21 min). Con acceso real a los logs de CI (token con permiso `Actions: read-only`, solo este
repo) se hizo el desglose por test y se encontró la causa concreta.

## El hallazgo real (con logs de CI, no solo inferencia)

3 tests de `tests/test_optimization_fase4.py` explicaban solos ~42 de los ~64 minutos totales de
la corrida analizada (commit `4d7feb2f`):

| Test | CI | Local (antes del fix) |
|---|---|---|
| `test_generar_candidatos_con_panel_e_inversor_varia_ambos` | 1198.5s | 27.5s |
| `test_generar_candidatos_sincroniza_eta_inversor_con_el_inversor_sorteado` | 827.2s | 18.1s |
| `test_generar_candidatos_panel_inversor_es_reproducible_con_seed` | 486.8s | 10.6s |

**Factor real de ~44x** entre CI (runner compartido gratuito, 2 vCPU) y local para este camino
específico — mucho más que el 2-5x normal del resto de la suite.

## Causa raíz

`optimization/variables.py::_catalogo_paneles_real()` y `_catalogo_inversores_real()` **no
tenían ningún caché** — reconstruían el diccionario unido completo (hasta ~3.100 paneles / ~2.450
inversores) en **cada llamada**. `optimization/scenario_generator.py::_resolver_categoricas_de_catalogo()`
las llama en **cada intento** del muestreo aleatorio de `generar_candidatos()` — hasta
`n_candidatos × max_intentos_por_candidato` veces (hasta 1.800 intentos en el test más lento).

Es trabajo puro de Python (fusión de diccionarios, sin numpy/vectorización) — exactamente el tipo
de carga que un CPU compartido y más débil penaliza desproporcionadamente frente a un desktop local
moderno, explicando el factor 44x (mucho mayor que la variabilidad normal 2-5x del resto de la
suite, que sí usa cálculo numérico vectorizado).

## Fix (sin tocar física ni tolerancias de ningún test)

Se cachea el resultado de ambas funciones, con invalidación real por `mtime` del archivo Excel
subyacente (mismo patrón #26 ya usado por `datos/catalogo_inversores_excel.py::excel_mtime_inv()`
para permitir edición en vivo sin reiniciar el servidor). Se agregó el helper equivalente
`excel_mtime()` para paneles (no existía).

**Bug real encontrado y corregido en el mismo cambio**: la primera versión del fix usaba una clave
de caché fija (`0.0`) cuando el módulo real no estaba disponible (import falla) — esto rompía el
aislamiento entre tests que monkeypatchean catálogos falsos distintos en `sys.modules`: un test
recibía en silencio el catálogo falso de OTRO test que corrió antes en el mismo proceso. Detectado
de inmediato al correr la suite (6 tests de `test_catalogo_inversores_real.py` fallaron con
exactamente ese síntoma). Corregido: si el módulo real no está disponible, se **evita el caché por
completo** (llamada directa sin memoizar) en vez de usar una clave inventada — mismo comportamiento
que antes del fix para ese caso, cero riesgo de contaminación cruzada entre tests.

## Verificación

- Los 3 tests lentos: de 56.16s a **<1s combinados** en local.
- `tests/test_optimization_fase4.py` completo: de 62.47s a **7.00s**.
- `tests/test_catalogo_inversores_real.py` + `tests/test_optimization_contract.py`: 33/33 pasan
  (incluidos los 6 que fallaron con la primera versión del fix, antes de la corrección de
  aislamiento).
- Suite completa ejecutada tras el fix final (ver resultado en el commit).

## Qué NO cambió

Ningún dato físico, tolerancia, criterio de compatibilidad eléctrica, ni el comportamiento
observable de `generar_candidatos()` — el fix es puramente de rendimiento interno (evitar
recomputar un resultado determinista). El comportamiento de "editar el Excel en producción se
refleja sin reiniciar el servidor" se preserva exacto (misma invalidación por mtime que ya usaba
el catálogo de inversores; el de paneles GANA esa misma precisión, que antes solo tenía un TTL de
1 hora a nivel del loader — una mejora real, no una regresión).
