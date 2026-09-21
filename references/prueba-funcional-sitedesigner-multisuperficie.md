# Prueba funcional: Site Designer + multi-superficie

**Fecha:** 2026-09-21. **Rama:** `fix-cierre-brechas-multisuperficie` (misma rama aislada
de las rondas anteriores). **Copia web:** https://claude.ai/artifact/Cou1DNdxyhSksqLyvYpRc5
(documento vivo). Sin commit, sin despliegue, sin modificar consumidores downstream.

## Resumen ejecutivo

Prueba ejecutada como **script Python que usa las funciones productivas reales** (no hay
servidor Streamlit interactivo en este entorno). Sin mocks: cargador real de Site
Designer, TMY real descargado en vivo de PVGIS, motor de sombra real, frontera de
vinculación real, validación de inversores real.

**Resultado: los 15 puntos del objetivo se verificaron y los 15 se comportan como exige
el contrato.**

Hallazgo fuera del objetivo, no bloqueante: archivo extraviado dentro de `bipv_python/`
cuyo nombre es una ruta Windows completa — no usado en la prueba (ver "Fallos
encontrados").

## Localización del archivo

```
$ find /workspaces/calculadora-bipv -name 'site-designer-2026-07-14-1606-10.json' -print
(sin resultados)
```

El `find` exacto no encuentra nada — ningún archivo tiene ese nombre literal.

| Archivo | Ubicación | ¿Usado? |
| --- | --- | --- |
| `site-designer-2026-07-14-1606-10_1786198985402.json` | `attached_assets/` | **Sí** — metadatos coinciden exactamente con la escena descrita |
| `C:\Users\Mauricio\Desktop\PROFESOR HEBERT ARQUITECTO\calculos casa bogota\site-designer-2026-07-14-1606-10.json` | dentro de `bipv_python/` | No — artefacto de subida mal hecha |

**Ruta real usada:**
`/workspaces/calculadora-bipv/attached_assets/site-designer-2026-07-14-1606-10_1786198985402.json`
(3166 bytes).

## Cargador Site Designer real (`cargar_escena_sitedesigner`)

Metadatos extraídos por la función real:

```json
{
  "fuente": "externa_marsh",
  "lat": 4.702, "lon": -74.147, "timezone": -5, "elevacion_m": 2548.4,
  "north_offset_deg": 7.0,
  "n_bloques": 1,
  "dim_m": {"x": 4.56, "y": 3.69, "z": 10.0}
}
```

- Número de bloques: 1 (bloque tipo árbol).
- Malla: `trimesh.Trimesh`, 12 triángulos, 8 vértices.
- Dimensiones en metros: 4.56 × 3.69 × 10.0 m — confirma `ESCALA_MM_A_M=0.001` aplicada.
- `northOffset=7°` verificado numéricamente: centro con offset `(3.197, 1.421, 5.0)` vs.
  sin offset `(3.000, 1.800, 5.0)`; la fórmula documentada predice `(3.197, 1.421)` —
  coincide exactamente.
- `verificar_ubicacion` sin avisos (ubicación de sesión = ubicación del archivo).

## TMY real (PVGIS)

`calculos.solar.obtener_tmy_pvgis(4.702, -74.147)` — llamada de red real, cacheada en
disco durante la sesión. Forma `(8760, 7)`, columnas `G_h, Gb_n, Gd_h, T2m, WS10m, SP, RH`,
índice `2001-01-01 → 2001-12-31`, UTC.

## Puntos por superficie y limitación de tilt/azimuth

| Superficie | N° puntos | Coordenadas (x,y,z) m |
| --- | --- | --- |
| Fachada Sur | 5 | (8,0,2) (8,0,3.5) (8,0,5) (8,0,6.5) (8,0,8) |
| Techo | 6 | (8,6,6) (9.5,6,6.4) (11,6,6.8) (8,8,6.2) (9.5,8,6.6) (11,8,7) |
| Marquesina | 6 | (8,12,3) (9.5,12,3) (11,12,3) (8,14,3.2) (9.5,14,3.2) (11,14,3.2) |

**Limitación explícita:** el encargo no dio tilt/azimuth de sesión. Asignados por tipo —
Fachada Sur: 90°/180°; Techo: 15°/180°; Marquesina: 5°/180° — documentado como asunción.
No afecta la física de sombra (depende solo de las coordenadas reales de los puntos), sí
afecta la POA calculada en los pasos de adopción.

## Resultado de `calcular_fs_horario_por_superficie` (motor real)

| Superficie | len(p_shade) | estado | calidad | horas_sin_sol | horas_con_sol_calculadas | horas_no_calculadas | p_shade min/max/media | horas>0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fachada Sur | 8760 | calculado_completo | alta | 4351 | 4409 | **0** | 0.00/1.00/0.093 | 934 |
| Techo | 8760 | calculado_completo | alta | 4351 | 4409 | **0** | 0.00/0.50/0.009 | 213 |
| Marquesina | 8760 | sombra_cero_calculada | alta | 4351 | 4409 | **0** | 0.00/0.00/0.000 | 0 |

Firma generada (13 claves, presentes en las 3): `geometria, puntos_analisis,
malla_horizonte, tmy_fingerprint, fuente, tilt_deg, azimuth_deg, transparencia,
version_algoritmo, proveedor, resolucion_espacial, resolucion_temporal, zona_horaria`.

Nota física: el árbol de la escena real (4.56×3.69×10 m, centrado cerca del origen) queda
geométricamente lejos de los puntos sintéticos (x=8-11, y=0-14) para Marquesina —
validando con datos reales (no un caso diseñado) el estado `sombra_cero_calculada`.

## Los 15 puntos del objetivo, verificados

| # | Objetivo | Resultado |
| --- | --- | --- |
| 1 | App local en rama aislada | Rama `fix-cierre-brechas-multisuperficie`; sin servidor interactivo — ver limitaciones |
| 2-3 | Vista 3D → Superficies BIPV, cargar JSON | Replicado con las mismas llamadas que la página |
| 4 | Escena → malla 3D en metros | Sí — 4.56×3.69×10.0 m |
| 5 | northOffset=7° aplicado | Sí — verificado numéricamente |
| 6 | Puntos en superficies correspondientes | Sí — 5+6+6 puntos |
| 7 | "Calcular sombra de todas las superficies" | Replicado con la función real |
| 8 | p_shade de 8760 valores | Sí, las 3 |
| 9 | firma_sombra, estado, calidad presentes | Sí, las 3 |
| 10 | Horas con sol no quedan incompletas | Sí — 0 en las 3 |
| 11 | Superficie sin puntos bloquea el cálculo completo | Sí, en dos capas (motor + gate UI) |
| 12 | Cambiar tilt/azimuth invalida p_shade/firma_sombra | Sí |
| 13 | Modo físico opt-in | Sí — default False |
| 14 | Comparación no modifica multisup_* | Sí — byte a byte idénticas |
| 15 | Adopción revalida antes de publicar | Sí — candidato roto rechazado sin tocar el destino |

**15/15 se comportan según el contrato exigido.**

## Claves `multisup_*` antes y después

Antes (simulando un cálculo simplificado previo):
```
E_ac_anual_kWh_multisup = 1111.1
area_total_multisup     = 60.0
multisup_desglose       = [{'nombre': 'simplificado_previo'}]
multisup_activo         = True
poa_df_multisup         = 'valor_centinela_no_debe_cambiar'
```

Después de "calcular comparación": **idénticas, sin cambios**.

Tras la adopción explícita:
```
E_ac_anual_kWh_multisup = 6484.9
area_total_multisup     = 60.0
multisup_activo         = True
```

Agregados: `E_ac_total_kWh=6484.9, E_dc_total_kWh=6685.5, area_total_m2=60.0,
n_superficies=3, n_inversores=1`.

## Comandos ejecutados y resultados

```
$ cd /workspaces/calculadora-bipv/bipv_python
$ .venv/bin/python -m pytest \
    tests/test_sitedesigner_marsh.py \
    tests/test_sombras_por_superficie.py \
    tests/test_cobertura_sombra_por_superficie.py \
    tests/test_vinculador_sombra_multisuperficie.py \
    tests/test_pagina_transicion_multisuperficie.py -q

64 passed in 3.06s
```

Script funcional (sin mocks): `✅ PRUEBA FUNCIONAL COMPLETADA SIN EXCEPCIONES NO
CONTROLADAS.` — cubre las 15 verificaciones, resultados guardados en JSON en el
scratchpad de la sesión.

`git status --short` / `git branch --show-current`: sin cambios nuevos respecto a la
ronda de corrección anterior; rama `fix-cierre-brechas-multisuperficie`.

## Fallos encontrados

Ninguno bloqueante. Dos hallazgos fuera del objetivo, reportados por transparencia:

1. Archivo extraviado en `bipv_python/` cuyo nombre de archivo es una ruta Windows
   completa — probable artefacto de una subida mal hecha anterior a esta conversación.
   No tocado.
2. `RuntimeWarning: invalid value encountered in divide` (scipy) durante el SDM de
   Marquesina (sombra cero total) — mismo tipo de warning ya documentado como no
   bloqueante en la ronda anterior.

## Limitaciones de la prueba

- No hubo prueba manual en navegador — sin servidor Streamlit interactivo en este
  entorno; la prueba usa las mismas funciones que la página, en el mismo orden, sin
  mocks, pero no ejercita renderizado/clics/mensajes en pantalla.
- tilt/azimuth de las 3 superficies fueron asumidos (no dados por el encargo).
- Una sola escena con un solo bloque — no se probaron múltiples obstáculos.
- N_serie asumido = número de puntos dados, para evitar la advertencia de resolución
  insuficiente (ya cubierta por pruebas unitarias de la ronda anterior).
- Un solo inversor compartido para las 3 superficies — la combinación dedicado+compartido
  ya está cubierta con datos sintéticos en `test_flujo_fisico_multisuperficie_end_to_end.py`.
