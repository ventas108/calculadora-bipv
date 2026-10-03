# Repetición de la prueba funcional Site Designer + multi-superficie

**Fecha:** 2026-09-21. **Repositorio:** `/workspaces/calculadora-bipv`. **Rama:**
`fix-cierre-brechas-multisuperficie`. Sin commit, sin push, sin despliegue, sin
modificar producción.

> ⚠️ **Aviso obligatorio:** las coordenadas x,y,z usadas en esta prueba son
> **SINTÉTICAS**, entregadas explícitamente para validar el flujo técnico
> end-to-end. **No representan la geometría real de los módulos de ningún
> proyecto** y esta prueba no aprueba esas coordenadas para producción — solo
> comprueba que el flujo (carga → sombra → adaptador → transición →
> inversor → agregados → adopción) funciona correctamente con datos reales de
> escena/TMY y coordenadas de ejemplo.

## Hallazgo de contexto (fuera de esta prueba, verificado antes de empezar)

Antes de tocar nada corrí `git status --short --branch` y `git log --oneline
--decorate -5` como exige la regla de seguridad de esta conversación.
Encontré que, **fuera de esta sesión**, `fix-cierre-brechas-multisuperficie`
ya fue mergeada a `main` y ambas ramas están sincronizadas con `origin` en el
mismo commit `c0caa213` ("Integra arquitectura multi-superficie BIPV"). El
repositorio estaba en `main` al iniciar esta tarea; cambié a
`fix-cierre-brechas-multisuperficie` (mismo commit, cambio no destructivo,
sin pérdida de cambios locales) para cumplir la instrucción de trabajar en
esa rama. No se hizo ningún commit ni push en esta ronda.

## 1. Batería de pruebas (10 archivos, exactamente como se pidió)

```
$ cd bipv_python && .venv/bin/python -m pytest \
    tests/test_sitedesigner_marsh.py tests/test_comparativo_sketchup_marsh.py \
    tests/test_adaptador_multisuperficie.py tests/test_cobertura_sombra_por_superficie.py \
    tests/test_flujo_fisico_multisuperficie_end_to_end.py tests/test_inversores_multisuperficie.py \
    tests/test_pagina_transicion_multisuperficie.py tests/test_sombras_por_superficie.py \
    tests/test_transicion_multisuperficie.py tests/test_vinculador_sombra_multisuperficie.py -q

110 passed, 64 warnings in 8.12s
```

0 fallos.

## 2. Prueba funcional real (script, sin mocks)

Se ejecutó un script standalone (no hay servidor Streamlit en este entorno)
que usa exclusivamente funciones productivas reales: el cargador
`cargar_escena_sitedesigner`, el TMY real de PVGIS (cacheado localmente para
no repetir la llamada de red), el motor de sombra real
`calcular_fs_horario_por_superficie`, y las funciones reales de
vinculación/adaptación/inversores. Ningún dato de sombra o TMY fue simulado.

### Ítem por ítem

| # | Verificación | Resultado |
| --- | --- | --- |
| 1 | Carga real del JSON Site Designer | ✅ `/workspaces/calculadora-bipv/attached_assets/site-designer-2026-07-14-1606-10_1786198985402.json` (3166 bytes) |
| 2 | Conversión mm → m | ✅ dimensiones malla 4.56×3.69×10.0 m (no mm/km) |
| 3 | `northOffset=7°` aplicado | ✅ verificado numéricamente contra la fórmula documentada (giro horario −θ) |
| 4 | Ubicación (lat 4.702, lon -74.147, elev 2548.4 m, UTC-5) | ✅ coincide exacto |
| 5 | Malla con un bloque/árbol | ✅ `n_bloques=1` |
| 6 | 5, 6 y 6 puntos por superficie | ✅ Fachada Sur=5, Techo inclinado=6, Marquesina=6 |
| 7 | `p_shade` de 8760 valores | ✅ `len(p_shade)==8760` en las 3 superficies |
| 8 | Firma TMY real | ✅ `tmy_fingerprint` presente y no vacío en las 3 firmas |
| 9 | Estado de cobertura y calidad por superficie | ✅ ver tabla siguiente |
| 10 | Bloqueo si falta una superficie o sus puntos | ✅ motor lanza `ValueError`; gate de UI queda deshabilitado |
| 11 | Invalidación al cambiar tilt o azimuth | ✅ cambiar tilt (90→60) o azimuth (180→90) retira `p_shade`/`firma_sombra`; solo renombrar no lo hace |
| 12 | Inversores dedicado/compartido | ✅ `derivar_tipo_inversor(1)="dedicado"`, `derivar_tipo_inversor(3)="compartido"`; `validar_inversores_y_asignaciones` corrige un `tipo` manual mal declarado en ambos sentidos |
| 13 | Comparación física sin tocar `multisup_*` | ✅ claves `multisup_*` idénticas antes/después de "calcular comparación" |
| 14 | Adopción explícita con revalidación | ✅ publica `multisup_*` solo tras recalcular de cero |
| 15 | Rollback si falla una superficie | ✅ inversor inexistente bloquea con `ValueError` antes de publicar; `destino_roto` nunca se toca |

### Estado, calidad y cobertura solar por superficie

| Superficie | estado_sombra | calidad_confianza | horas con sol calculadas | p_shade (min / max / media) |
| --- | --- | --- | --- | --- |
| Fachada Sur | `calculado_completo` | alta | 4409 / 4409 | 0.0000 / 1.0000 / 0.0932 |
| Techo inclinado | `calculado_completo` | alta | 4409 / 4409 | 0.0000 / 0.5000 / 0.0088 |
| Marquesina | `sombra_cero_calculada` | alta | 4409 / 4409 | 0.0000 / 0.0000 / 0.0000 |

`horas_con_sol_no_calculadas = 0` en las 3 → ningún cálculo incompleto.

### Claves `multisup_*`

**Antes** de "calcular comparación" (simulando un cálculo simplificado
previo): `E_ac_anual_kWh_multisup=1111.1`, `area_total_multisup=60.0`,
`multisup_desglose=[{"nombre": "simplificado_previo"}]`,
`multisup_activo=True`, `poa_df_multisup="valor_centinela_no_debe_cambiar"`.

**Después** de "calcular comparación": **idénticas, sin tocar** — confirma
que la comparación nunca escribe `multisup_*` directamente.

**Tras "adoptar"** (revalidación real, sí publica):
`E_ac_anual_kWh_multisup=6484.9`, `area_total_multisup=60.0`,
`multisup_activo=True`.

### Resultado físico total

`agregados` del proyecto candidato: `E_ac_total_kWh=6484.9`,
`E_dc_total_kWh=6685.5`, `area_total_m2=60.0`, `n_superficies=3`,
`n_inversores=1`.

**Nota de consistencia**: estas coordenadas sintéticas y esta geometría
(tilt/azimuth) son idénticas a las usadas en la prueba funcional de la ronda
anterior de esta conversación (antes del borrado accidental y en la
recuperación posterior). El resultado `E_ac_total_kWh=6484.9` es exactamente
el mismo que en esas dos rondas anteriores — confirma que el comportamiento
físico del flujo sigue siendo idéntico.

### Comparación y adopción

- **Comparación** (`construir_y_recalcular_proyecto_fisico`, "calcular
  comparación"): éxito, `multisup_*` sin modificar (ver arriba).
- **Adopción** (mismo llamado, revalidación real antes de publicar): éxito,
  publica `E_ac_anual_kWh_multisup=6484.9` y demás claves.
- **Rollback**: con `INV-NO-EXISTE` asignado a "Fachada Sur", la
  revalidación lanza `ValueError: Configuracion multi-superficie invalida:
  La superficie 'Fachada Sur' referencia el inversor 'INV-NO-EXISTE', que no
  existe.` **antes** de tocar el destino — `destino_roto` queda intacto.

## 3. Alcance y límites de esta prueba

- Sin servidor Streamlit interactivo en este entorno — se usó un script
  standalone que llama a las mismas funciones productivas que
  `pages/9_🗺️_Vista_3D.py` invoca internamente, no la UI en sí.
- **Las coordenadas son sintéticas** — repetido aquí explícitamente para que
  no se confunda esta prueba con una validación de un proyecto real.
- No se hizo commit, push ni despliegue.

## Comandos ejecutados

```
git status --short --branch
git log --oneline --decorate -5
git checkout fix-cierre-brechas-multisuperficie
cd bipv_python && .venv/bin/python -m pytest <10 archivos> -q
.venv/bin/python <script funcional con coordenadas sintéticas> 
git status --short --branch   # confirmación final: sin cambios de repo
```
