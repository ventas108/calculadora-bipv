# Recuperación multi-superficie BIPV tras borrado accidental

**Fecha:** 2026-09-21. **Rama:** `fix-cierre-brechas-multisuperficie` (misma rama aislada,
`HEAD` en `46c7e36c` = GitHub/main). **Copia web:** https://claude.ai/artifact/5wfLh4oNYhxYEeWagNfyPy
(documento vivo). Sin commit, sin push, sin despliegue, sin tocar DigitalOcean.

## Resumen ejecutivo

La arquitectura multi-superficie quedó **recuperada y funcional**. Punto de partida: 4
módulos `calculos/*` y la integración en `Vista_3D.py` ya estaban reconstruidos
parcialmente antes de esta ronda; mi auditoría de esa reconstrucción encontró **3 bugs
reales** (invalidación por TMY convertida en no-op, estado `error_geometrico` nunca
alcanzable, POA ponderada rota para 2+ superficies) y **UI entera faltante** (inversores,
modo físico, comparación/adopción) — los tres bugs se corrigieron y la UI completa se
reconstruyó.

**Prueba decisiva**: reejecuté el mismo script funcional de la ronda anterior (JSON Site
Designer real, TMY real de PVGIS, sin mocks) y obtuve los mismos números exactos que
antes del borrado (`E_ac_total_kWh=6484.9`, Marquesina en `sombra_cero_calculada`, etc.).

**Batería de pruebas**: `0 → 110 passed` en el conjunto multi-superficie completo.
`py_compile` y `git diff --check` limpios.

## Regla crítica cumplida

```
$ git status --short --branch
## fix-cierre-brechas-multisuperficie
 M CodeSpecs/00-director/contratos-entre-modulos.md
 M CodeSpecs/00-director/registro-de-decisiones.md
 M bipv_python/calculos/sombras_3d.py
 M bipv_python/pages/9_🗺️_Vista_3D.py
?? (14 archivos nuevos)

$ git log --oneline --decorate -5
46c7e36c (HEAD -> fix-cierre-brechas-multisuperficie, origin/main, main, ...) feat: ...
```

Nunca se usaron `git clean`, `git reset --hard`, `rm -rf`, restauraciones masivas sin
revisar, ni ningún comando que elimine archivos. Única acción "destructiva": matar un
`pip install` de un build lento de pandas desde fuente (no tocó archivos del repo). Sin
commit, sin push, sin despliegue.

## Auditoría de lo reconstruido (antes de corregir nada)

Leí completos `sombras_3d.py`, `adaptador_multisuperficie.py`,
`inversores_multisuperficie.py`, `vinculador_sombra_multisuperficie.py` y `Vista_3D.py`.
La firma TMY real y el bloqueo de sombra por estado sobrevivieron correctamente.
Encontré 3 regresiones reales:

| # | Regresión | Evidencia |
| --- | --- | --- |
| 1 | `invalidar_sombra_por_cambio_tmy` era un no-op: `return [dict(s) for s in superficies_bipv]` | Lectura directa; no se llamaba desde `construir_y_recalcular_proyecto_fisico` |
| 2 | Estado `error_geometrico` definido pero nunca alcanzable | `validar_puntos()` nunca se llamaba dentro de `calcular_fs_horario_por_superficie` |
| 3 | `poa_df_multisup` solo se calculaba con exactamente 1 superficie: `filas[0] if len(filas)==1 else None` | Con 2+ superficies (caso normal) siempre daba `None` |

Además, en `Vista_3D.py` faltaban por completo: preservar/invalidar en el editor de
geometría, UI de inversores, toggle de modo físico, y comparación/adopción.

## Correcciones aplicadas

1. **`invalidar_sombra_por_cambio_tmy` restaurada**: calcula la huella real del TMY
   vigente (`huella_horaria`, misma fórmula que la transición) y retira
   `p_shade`/`firma_sombra` de superficies con firma desactualizada. Reconectada dentro
   de `construir_y_recalcular_proyecto_fisico`.
2. **Estado `error_geometrico` restaurado**: se agregó la llamada a `validar_puntos()`
   (que ya existía en el módulo) con precedencia sobre los demás estados.
3. **`poa_df_multisup` ponderado por área, restaurado**: nueva `_poa_ponderada()`.
   Verificado numéricamente: 2 superficies (área 10 y 30 m², POA 400 y 800 W/m²) dan
   `(10×400+30×800)/40 = 700` — exacto.
4. **Extra de consistencia**: constantes `ESTADO_*`/`ESTADOS_SOMBRA_ACEPTABLES`
   restauradas en `sombras_3d.py`, usadas por `vinculador`/`adaptador` en vez de cadenas
   sueltas repetidas.

## UI recuperada en Vista_3D.py

- Editor de geometría: `preservar_o_invalidar_campos_fisicos` reemplaza la fusión
  ingenua que preservaba `p_shade` obsoleto en silencio.
- Inversores por superficie: agregar/eliminar, ID, eficiencia, potencia AC, asignación
  por superficie, `n_serie`/`n_paralelo`. El `tipo` nunca es editable — se deriva
  siempre.
- Modo físico opt-in + comparación (no toca `multisup_*`) + adopción que revalida antes
  de publicar (nunca confía en el candidato guardado).
- Site Designer + puntos por superficie: auditado, ya era correcto.

## 7 archivos de prueba recreados desde cero

| Archivo | Pruebas |
| --- | --- |
| `test_sombras_por_superficie.py` | 5 |
| `test_cobertura_sombra_por_superficie.py` | 5 |
| `test_vinculador_sombra_multisuperficie.py` | 20 |
| `test_inversores_multisuperficie.py` | 13 |
| `test_adaptador_multisuperficie.py` | 21 |
| `test_pagina_transicion_multisuperficie.py` | 11 |
| `test_flujo_fisico_multisuperficie_end_to_end.py` | 7 |

Total: 82 pruebas nuevas + 28 que sobrevivieron = **110 passed**, 0 fallos.

## Prueba funcional real con el JSON Site Designer

Reejecuté el mismo script de la ronda anterior. Resultado idéntico palabra por palabra:
malla 12 triángulos 4.56×3.69×10.0 m, `northOffset` verificado, Fachada Sur y Techo en
`calculado_completo`, Marquesina en `sombra_cero_calculada`, `E_ac_total_kWh=6484.9`
exacto, bloqueos y revalidación comportándose igual que antes del borrado.

## Entorno de pruebas

```
$ find /workspaces/calculadora-bipv -maxdepth 4 \( -path '*/bin/python' -o -path '*/bin/pytest' \) -print
(sin resultados)
```

No había otro entorno de proyecto utilizable. Se reconstruyó `bipv_python/.venv`
(`python3 -m venv .venv`, local al proyecto) con las mismas versiones modernas sin pin
ya usadas en rondas anteriores (numpy 2.5.3, pandas 3.0.6, pvlib 0.15.2) — los pines
exactos de `requirements.txt` no tienen wheel para Python 3.14 y fuerzan una
compilación desde fuente de ~15 minutos.

## Validación final

```
$ git diff --check          → exit 0, sin salida
$ python -m py_compile ...  → exit 0, sin salida
$ pytest (10 archivos multi-superficie) -q
110 passed in 7.28s

$ pytest tests/ -q          (regresión completa del proyecto, sin exclusiones)
1 failed, 1393 passed, 113 warnings in 930.36s (0:15:30)
```

El único fallo es `test_solar_svf.py::test_reduccion_svf_baja_isotropica_en_la_proporcion_exacta`,
**preexistente y no relacionado** con esta recuperación: `git status` confirma cero cambios
locales en `calculos/solar.py` ni en `tests/test_solar_svf.py`. Es el mismo fallo por
desfase de versión de `pvlib` (0.15.2 instalado vs. 0.11.1 al que está pineado el código:
renombró columnas del componente Hay-Davies de `isotropic` a `poa_isotropic`) que apareció
idéntico en las rondas anteriores de esta misma conversación (turnos de auditoría y
corrección de brechas). Cero regresiones nuevas introducidas por esta ronda de recuperación.

## Archivos y brechas abiertas

**Modificados:** `sombras_3d.py`, `vinculador_sombra_multisuperficie.py`,
`adaptador_multisuperficie.py`, `pages/9_🗺️_Vista_3D.py`.

**Recreados desde cero:** los 7 archivos de prueba.

**Sin tocar, confirmado íntegro:** `transicion_multisuperficie.py`,
`inversores_multisuperficie.py`, `sitedesigner_marsh.py`, `multi_superficie.py`,
`mismatch_bypass.py`, `CodeSpecs/.../transicion-multisuperficie/` (incluido
`mockup-ui.md`).

**Brechas abiertas:**
1. UI de puntos por superficie sigue siendo texto manual, no editor gráfico.
2. Verificación manual con la app en navegador — no posible en este entorno.
3. `test_solar_svf.py` sigue fallando por desfase de versión de `pvlib` (preexistente, no
   introducido por esta ronda; fuera del alcance de esta recuperación).
