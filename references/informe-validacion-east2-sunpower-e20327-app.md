# Informe de validación — Caso East2 (SunPower E20-327) reproducido en la APP

**Fecha:** 2026-09-21, actualizado 2026-09-22 (auditoría QCRad, §10) y 2026-09-22 tarde
(reauditoría de cierre, §13). **Rama:**
`validacion-east2-sunpower-e20327` (el repositorio avanzó a `main` por un proceso concurrente
durante la ronda del 21-sep; el trabajo de este informe se reubicó a esta rama aislada nueva,
sin commit, sin tocar `main`). **Commit/push/deploy:** ninguno.
**Copia web:** ver enlace entregado al final de la conversación (misma información, formato navegable).

## 1. Fuente científica utilizada

- Artículo: *Dealing with Shadows When Modelling BIPV Façades with Conventional PV Tools*.
  DOI `10.3390/buildings16091668`. PDF local: `references/buildings-16-01668-v2.pdf`
  (SHA-256 `39683bfdaecc085a3c9e75308350d528cead1e6303f51b7bfae450e899f41e1d`).
- Caso: **East2**, Building 42, campus CIEMAT, Madrid.
- Documentos de trabajo ya existentes en el repositorio, leídos antes de tocar código:
  `references/buildings-16-01668-east2-caso.md`, `references/east2-validacion-informe.md`,
  `references/informe-verificacion-pybdshadow-p-shade.md`, `references/east2-mascara-angular.json`,
  `references/generar_east2_fs_angular.py`, `references/east2-fs-angular-reconstruido.csv`.

## 2. Parámetros extraídos del artículo

| Campo | Valor | Estado |
|---|---|---|
| Latitud / Longitud | 40.45° N / -3.74° | Publicado |
| Módulo | SunPower E20-327 (E20-327NE-WHT-D) | Publicado |
| Potencia módulo | 327 W | Publicado |
| Eficiencia módulo | 20.1% | Publicado |
| Módulos del arreglo | 14, configuración 7S×2P | Publicado |
| Azimut del arreglo | 82.65° (convención brújula) | Publicado |
| Inclinación | 90° (fachada vertical) | Inferido por el artículo; no confirmado con los autores |
| Inversor | Fronius IG Plus 50 V-1 | Publicado (solo el modelo, no ficha eléctrica completa) |
| Albedo | 0.2 | Publicado |
| Periodo de medición real | 2017–2023, horario | Publicado (no reproducible aquí, ver §3) |
| Irradiancia real | CAMS (GHI/DNI/DHI) | Publicado (no reproducible aquí, ver §3) |
| Temperatura/viento real | PVGIS/ERA5 | Publicado (no reproducible aquí, ver §3) |
| DSM | LiDAR, 1 m | Publicado; archivo no compartido por el artículo |
| Factor de sombreado East2 | Tabla 4: 19 azimutes × 10 elevaciones (190 valores), PVsyst sobre DSM real | Publicado, transcrito íntegro en `east2-mascara-angular.json` |
| Energía anual East2 | **No publicada** en el artículo | Ausente |
| Error de herramientas vs. medición | SAM 3D nRMSE 26.6%, SAM DSM 6.8%, PVsyst 3D 7.5%, PVsyst DSM 11.6% | Publicado, pero es error de OTRAS herramientas frente a medición real, no una tolerancia aplicable a esta reconstrucción |

## 3. Parámetros faltantes y supuestos inevitables

El artículo **no publica**: la serie horaria real de irradiancia/temperatura (CAMS/ERA5
2017–2023), el DSM/malla 3D original, la ficha eléctrica completa del Fronius IG Plus 50 V-1,
ni una energía anual agregada de East2. Sin esos insumos, una homologación numérica exacta
contra el artículo **no es posible** con lo que hay en este repositorio. Se documentan y
reutilizan aquí los supuestos que la ronda de trabajo previa (`east2-validacion-informe.md`)
ya había fijado, para no introducir un segundo criterio distinto sin necesidad (regla 5 del
encargo):

| Supuesto | Valor usado | Origen |
|---|---|---|
| TMY | Sintético, clear-sky Ineichen (pvlib), año 2023, hora local `Europe/Madrid` | Ya documentado en `east2-validacion-informe.md` |
| Temperatura ambiente | 20 °C constante todo el año | Ya documentado en `east2-validacion-informe.md` |
| Altitud | 667 m | Ya documentado en `east2-validacion-informe.md` |
| `eta_inversor` | 0.97 | Ya documentado en `east2-validacion-informe.md` (el artículo no da la eficiencia exacta del Fronius para este cálculo) |
| SDM del panel | Estimado por `pvsyst_v6_defaults` desde la ficha pública (Voc/Isc/Vmp/Imp/coeficientes) | Ya existente en `datos/tecnologias_bipv.py`, sin modificar |
| Ficha eléctrica del inversor (Vdc_max, Vmppt, Isc_max) | **No asumida** — se deja vacía a propósito | Nueva decisión de esta ronda: el Fronius IG Plus 50 V-1 no está en `datos/catalogo_inversores.py` (solo existe un Fronius Primo 15.0-1, modelo distinto) y no se inventó una ficha sin verificar |
| `P_ac_nom_W` (clipping AC) | `None` (sin recorte AC modelado) | Misma limitación que la reconstrucción previa; no hay ficha verificada del inversor |

**Bloqueo reportado con precisión (regla 10):** la compatibilidad eléctrica string↔inversor y
la relación DC/AC quedan explícitamente `evaluable: False` en el resultado de la APP — el
pipeline no falla ni inventa un valor, informa la ausencia del dato.

## 4. Flujo exacto ejecutado

Punto de entrada correcto identificado tras leer `transicion_multisuperficie.py`,
`adaptador_multisuperficie.py` y `vinculador_sombra_multisuperficie.py`: la función pura
`calculos.vinculador_sombra_multisuperficie.construir_y_recalcular_proyecto_fisico(session_state,
tmy, lat, lon, alt_m)`, que es exactamente la que usa
`tests/test_flujo_fisico_multisuperficie_end_to_end.py`. Encadena, sin mezclarlas:

```
superficie_nueva()               → geometría + panel + config eléctrica (sin resultados)
  → recalcular_fisica_superficie() → POA (calcular_poa_superficie, pvlib real)
                                    → sombra (p_shade real del CSV East2)
                                    → temperatura + SDM + bypass (simular_bypass_horario, NOCT)
  → recalcular_etapa_inversor_bus() → inversor (eta, clipping si P_ac_nom_W existe)
  → recalcular_agregados_proyecto()  → agregados del proyecto
```

**Ningún archivo de código productivo fue modificado.** Todas las funciones ya existían y
pasaron sin cambios; solo se añadió un archivo de prueba nuevo:
`bipv_python/tests/test_escenario_validacion_east2_sunpower.py` (19 pruebas tras las rondas de
auditoría de §10 y §13; 11 en la reconstrucción original de esta sección).

### Comandos reproducibles

```bash
cd bipv_python
.venv/bin/python -m pytest tests/test_escenario_validacion_east2_sunpower.py -v

.venv/bin/python -m pytest \
  tests/test_transicion_multisuperficie.py \
  tests/test_sombras_por_superficie.py \
  tests/test_adaptador_multisuperficie.py \
  tests/test_persistencia_multisuperficie.py \
  tests/test_flujo_fisico_multisuperficie_end_to_end.py \
  tests/test_pagina_transicion_multisuperficie.py \
  tests/test_escenario_validacion_east2_sunpower.py -q
```

### Resultado de los comandos

- `test_escenario_validacion_east2_sunpower.py`: **19 passed**.
- Batería completa (6 archivos, incluye el nuevo): **101 passed**, 0 failed. Se observaron
  advertencias `RuntimeWarning: invalid value encountered in divide` de
  `scipy.optimize._chandrupatla`: no son QCRad ni bloquean las pruebas; este informe no
  las clasifica como preexistentes sin una línea base equivalente del mismo escenario.

## 5. Archivos modificados / añadidos

| Archivo | Cambio |
|---|---|
| `bipv_python/tests/test_escenario_validacion_east2_sunpower.py` | **Nuevo, ampliado en §10 y §13.** 19 pruebas: ejecución de punta a punta (mensual/exacto), determinismo, anclas numéricas de regresión (POA/DC/AC/horas/`p_shade` medio), resolución de ficha SunPower E20-327, no mezcla entre dos superficies, sensibilidad a tilt/azimuth/TMY/máscara de sombra, modificación real de `p_shade`, regeneración de sombra tras cambio de TMY, guarda contra sustituir `p_shade` por cero, y coherencia radiativa QCRad. |
| `references/informe-validacion-east2-sunpower-e20327-app.md` | **Nuevo.** Este informe. |
| Cualquier otro archivo de `calculos/`, `pages/`, `datos/` | **Sin cambios.** |

## 6. Comparación numérica

Todas las energías en kWh/año salvo que se indique otra unidad. "Reconstrucción previa" =
`east2-validacion-informe.md` (vía `calculos.ejecutor_escenarios`, sesión anterior, 20-sep-2026).
"APP ahora" = esta ronda, vía el pipeline físico multi-superficie real
(`construir_y_recalcular_proyecto_fisico`), 21-sep-2026.

| Magnitud | Artículo | Reconstrucción previa | APP ahora | Dif. absoluta | Dif. % | Fuente | Confianza | Explicación de la diferencia |
|---|---|---|---|---|---|---|---|---|
| Potencia DC instalada | 4.578 kWp (14×327 W nominales) | 4.578 kWp | 4.579 kW (`Pmax_stc=327.106 W` del catálogo efectivo) | +0.001 kW frente al nominal | +0.02% | Ficha publicada + catálogo efectivo | Alta | El artículo redondea a 327 W; la APP conserva el valor efectivo del catálogo y redondea a 3 decimales |
| Eficiencia del módulo | 20.1% | 20.1% (mismo catálogo) | 20.1% (mismo catálogo) | 0 | 0% | Ficha SunPower publicada | Alta | Verificación de placa, no depende del pipeline |
| POA anual (fachada, sin sombra) | No publicado | No reportado explícitamente (solo E_DC/E_AC) | 1038.81 kWh/m² | N/D | N/D | Calculado (pvlib `haydavies`, TMY sintético) | Media | No hay valor previo con el que comparar; depende enteramente del TMY sintético asumido, no del real CAMS/ERA5 |
| Energía DC anual — referencia (`p_shade=0`) | No publicado | 4367.4 kWh | 4450.8 kWh | +83.4 | +1.91% | Calculado, ambos con el mismo supuesto de TMY | Media | Ver nota (a) más abajo — brecha sistemática ~1.9–2.1% entre las dos reconstrucciones, causa no confirmada |
| Energía AC anual — referencia (`p_shade=0`) | No publicado | 4236.4 kWh | 4317.2 kWh | +80.8 | +1.91% | Calculado | Media | Misma nota (a) |
| Energía DC anual — East2, modo mensual | No publicado | 2325.5 kWh | 2373.9 kWh | +48.4 | +2.08% | Calculado, misma máscara angular Tabla 4 | Media | Nota (a); la sombra en sí coincide (ver horas abajo) |
| Energía AC anual — East2, modo mensual | No publicado | 2255.7 kWh | 2302.7 kWh | +47.0 | +2.08% | Calculado | Media | Nota (a) |
| Energía DC anual — East2, modo exacto | No publicado | 2332.9 kWh | 2379.8 kWh | +46.9 | +2.01% | Calculado | Media | Nota (a) |
| Energía AC anual — East2, modo exacto | No publicado | 2263.0 kWh | 2308.4 kWh | +45.4 | +2.01% | Calculado | Media | Nota (a) |
| Pérdida por sombra (%, AC), modo mensual | No publicado | 46.75% | 46.67% | -0.08 pp | -0.17% relativo | Calculado | **Alta** | Coincide dentro de redondeo — la brecha de energía absoluta (nota a) se cancela al expresar la pérdida como % de la propia referencia |
| Pérdida por sombra (%, AC), modo exacto | No publicado | 46.58% | 46.54% | -0.04 pp | -0.09% relativo | Calculado | **Alta** | Ídem |
| Horas de sombra/bypass, modo mensual | No publicado | 3563 h | 3563 h | 0 | 0% | Alineación de la máscara Tabla 4 sobre el mismo TMY (`alinear_fs_con_tmy`) | **Alta** | Coincidencia exacta — la lógica de alineación temporal es idéntica en ambas reconstrucciones |
| Horas de sombra/bypass, modo exacto | No publicado | 3536 h | 3536 h | 0 | 0% | Ídem | **Alta** | Coincidencia exacta |
| `p_shade` promedio anual, modo mensual | No publicado | 0.3859 | 0.38594 | +0.00004 | +0.01% | Calculado desde la Tabla 4 | **Alta** | Coincide dentro del redondeo publicado (4 decimales) |
| `p_shade` promedio anual, modo exacto | No publicado | 0.3553 | 0.35528 | -0.00002 | -0.01% | Calculado | **Alta** | Ídem |
| Clipping AC | No publicado | No modelado (sin ficha AC del inversor) | No modelado (`P_ac_nom_W=None`, 0.0 kWh) | N/D | N/D | Bloqueo documentado | Alta (como ausencia, no como cero verificado) | Ninguna reconstrucción tiene la ficha AC verificada del Fronius IG Plus 50 V-1; "0" es "no evaluado", no "sin pérdida" |
| Compatibilidad eléctrica string↔inversor | No publicado | No evaluada | `evaluable: False` (ficha AC ausente) | N/D | N/D | Bloqueo documentado | Alta | Igual que arriba |
| PR (Performance Ratio), referencia sin sombra | No publicado | No reportado (POA no publicada) | 90.8% (`Yf`=943.0 kWh/kWp, `Yr`=1038.81 h) | N/D | N/D | Derivado de POA+energía calculadas | Media | Solo calculable en la corrida de esta ronda, que sí guarda el POA anual |
| PR, East2 con sombra (mensual/exacto) | No publicado | No reportado | 48.4% / 48.5% | N/D | N/D | Derivado | Media | Ídem |
| Temperatura de módulo/ambiente | Serie ERA5 real horaria (no publicada como escalar) | 20 °C constante (supuesto) | 20 °C constante (mismo supuesto) | N/D | N/D | Supuesto reutilizado, no verificado contra ERA5 | Baja | Ninguna reconstrucción usa la temperatura real del artículo |
| Factor de sombreado (matriz angular) | Tabla 4 publicada (190 valores, PVsyst sobre DSM real) | Misma tabla, interpolada bilinealmente a horario | Misma tabla, misma interpolación (reutiliza el mismo CSV, sin recalcular) | — | — | Transcripción verificada dos veces (`east2-validacion-informe.md`) | Alta como transcripción; **media-baja** como sombra "pura" — ver limitación (b) | Es el mismo insumo en ambas reconstrucciones por diseño |
| nRMSE herramientas vs. medición (SAM/PVsyst) | 6.8–26.6% (SAM/PVsyst, 3D/DSM) | No aplicable | No aplicable | N/D | N/D | Publicado | — | Esas cifras comparan OTRAS herramientas contra la medición real 2017–2023; no hay medición real disponible aquí contra la cual calcular un nRMSE propio |

**Nota (a) — brecha sistemática ~1.9–2.1% en energía absoluta, causa no confirmada.** Tanto
la energía DC/AC de referencia (sin sombra) como la de East2 (con sombra) de la APP quedan un
~2% por encima de la reconstrucción previa, en una proporción casi constante entre las dos
reconstrucciones, mientras que la pérdida por sombra en % y las horas de sombra/bypass
coinciden casi exactamente. Esto apunta a una diferencia en cómo se calculó el POA en la
sesión anterior (ejecutor_escenarios recibe `poa_global` ya calculado como argumento externo;
el script que lo generó **no se conservó** en el repositorio), no a la lógica de sombreado
-- que es idéntica dado que las horas de sombra/bypass y el `p_shade` promedio coinciden. No
se pudo confirmar la causa exacta porque el script original que produjo la reconstrucción
previa no está disponible para inspeccionar. **No se declara equivalencia de entradas entre
ambas reconstrucciones en el cálculo de POA** — ver veredicto.

**Limitación (b) — mezcla de convenciones no confirmada en la Tabla 4** (ya documentada en
`east2-validacion-informe.md`): la propia tabla podría incluir el corte por autoorientación
del panel (`cos(AOI)≤0`) además de la sombra real de vegetación. Si es así, parte de la
pérdida del 46.5–46.7% que reporta esta reconstrucción (en ambas versiones) podría estar
duplicando una pérdida óptica que el modelo de bypass ya aplica indirectamente vía el SDM. No
confirmado con los autores del artículo ni con el DSM original.

## 7. Verificaciones exigidas por el encargo

- **Determinismo:** confirmado — `test_escenario_east2_es_determinista` compara huellas
  (`geometria`, `poa`, `sombra`, `resultados_dc`, `resultados_ac`) y energía AC entre dos
  corridas idénticas; coinciden exactamente.
- **SunPower E20-327 se resuelve correctamente:** confirmado — `Pmax_stc`/`Voc_stc`/`Isc_stc`/
  `Vmp_stc`/`Imp_stc` coinciden con la ficha citada por el artículo dentro de redondeo, la
  eficiencia calculada (20.1%) coincide exactamente, y la potencia DC del string (4.578 kWp)
  se resuelve correctamente en `resultados_ac["P_dc_stc_kW"]`.
- **Superficies, geometrías y sombras no se mezclan:** confirmado —
  `test_east2_no_mezcla_con_otra_superficie_del_mismo_proyecto` agrega una superficie de
  control (techo horizontal, sin sombra) al mismo proyecto e inversor compartido; las huellas
  de geometría/POA/sombra de East2 y del control son distintas, el control queda con 0 horas
  de sombra y East2 con >3000, y ambas coexisten correctamente bajo el mismo bus de inversor.
- **Sensibilidad a tilt/azimuth/TMY/sombra:** confirmado — cuatro pruebas dedicadas muestran
  que cambiar cualquiera de esos cuatro insumos cambia la huella y/o el resultado; cambiar el
  TMY además invalida correctamente la sombra ya calculada (`invalidar_sombra_por_cambio_tmy`),
  forzando el mismo rechazo que exige el flujo real de la app.
- La comparación `mensual`/`exacto` cambia la agregación temporal de una misma máscara;
  una prueba separada modifica efectivamente `p_shade` y confirma cambio de huella y energía.
- Para TMY, se prueban ambas ramas: una sombra antigua se rechaza y una sombra/firma
  regenerada permite recalcular y produce huellas y energía distintas.
- **`p_shade` real, nunca cero por defecto:** confirmado — `test_sombra_cero_no_sustituye_a_la_mascara_real`
  prueba que la energía con la máscara angular real es estrictamente menor que con `p_shade=0`.
- **Anclas numéricas de regresión:** confirmado — los modos `mensual` y `exacto` fijan POA anual,
  energía DC/AC, horas de sombra/bypass y media de `p_shade`. Son valores de esta reconstrucción
  sintética, no valores publicados por el artículo.

## 8. Limitaciones de la comparación

1. El artículo **no publica** una energía anual agregada de East2 -- la mayoría de las filas
   de la tabla numérica no tienen un valor de artículo contra el cual comparar directamente.
2. El TMY es sintético (clear-sky Ineichen, T_amb constante) en **ambas** reconstrucciones --
   ninguna usa la serie real CAMS/ERA5 2017–2023 del artículo.
3. La Tabla 4 es una rejilla discreta interpolada, no el DSM continuo original, y podría
   mezclar corte por autoorientación con sombra real (limitación b).
4. El SDM del panel es estimado desde la ficha pública, no calibrado contra curvas I-V reales
   de laboratorio del E20-327.
5. La ficha eléctrica AC del inversor (Vdc_max, Vmppt, Isc_max, P_ac_nom_W) no está verificada
   -- compatibilidad, relación DC/AC y clipping quedan explícitamente sin evaluar, no en cero
   encubierto.
6. La brecha ~2% en energía absoluta frente a la reconstrucción previa (nota a) no pudo
   confirmarse en su causa exacta porque el script de esa reconstrucción no se conservó.

## 9. Veredicto

**Parcialmente reproducido.**

- Reproducido con fidelidad: la ficha del módulo SunPower E20-327 (100% del catálogo interno
  coincide con la ficha pública citada), la configuración eléctrica (7S×2P, 14 módulos), la
  geometría (tilt 90°, azimut 82.65°, lat/lon), y el uso de la máscara de sombreado angular
  real (Tabla 4) en vez de `p_shade=0`.
- No reproducido ni verificable contra el artículo: cualquier energía anual (DC, AC, POA, PR),
  porque el artículo no las publica para East2; la temperatura y la irradiancia reales
  (2017–2023, CAMS/ERA5), sustituidas por un supuesto sintético ya documentado.
- Coincide casi exactamente con la reconstrucción previa del repositorio en horas de sombra/
  bypass y en `p_shade` promedio (dentro de 0.01–0.02%), pero difiere en un ~2% sistemático en
  energía absoluta cuya causa no se pudo confirmar (script previo no conservado).

No se declara "reproducido" ni "validado": no hay equivalencia de entradas entre esta
reconstrucción y las mediciones reales del artículo, y persiste una brecha del ~2% sin
explicar frente a la única reconstrucción previa disponible como referencia cruzada.

## 10. Auditoría QCRad (22-sep-2026) — el TMY de East2 no produce la advertencia

**Encargo:** se reportó que "el TMY sintético generado para East2 produce advertencias QCRad
de incoherencia radiativa" y se pidió determinar la causa exacta, corregirla si era real, y
no silenciarla si no lo era.

**Resultado de la auditoría: la premisa no se confirma.** El TMY sintético de East2, construido
en `test_escenario_validacion_east2_sunpower.py` (`_tmy_east2_clearsky()`, clear-sky Ineichen de
pvlib), tiene **0.0% de horas inconsistentes** en el chequeo QCRad
(`calculos.solar.verificar_consistencia_radiativa`, Long & Shi 2008) — verificado
cuantitativamente, no solo por ausencia de la advertencia:

| Verificación | Resultado |
|---|---|
| Horas evaluadas (elevación solar > mínimo) | 4205 |
| Horas inconsistentes | **0** |
| % inconsistente | **0.0%** |
| Diferencia media (W/m²) | 0.0 |
| Diferencia máxima (W/m²) | 0.0 |
| `UserWarning` emitida | Ninguna |

Esto se cumple en modo `mensual` y `exacto`, con la máscara de sombra real de East2 Y con
`p_shade=0` (la coherencia QCRad depende solo del TMY y la geometría/POA, nunca de la sombra),
y es determinista entre dos construcciones independientes del mismo TMY (mismo dict `qcrad`
byte a byte). Las cuatro pruebas correspondientes se detallan en §12.

### 10.1 Por qué el TMY de East2 es coherente por construcción

`_tmy_east2_clearsky()` construye `G_h`/`Gb_n`/`Gd_h` con una única llamada a
`pvlib.location.Location(...).get_clearsky(idx, model="ineichen")` sobre el mismo índice
`idx` que luego usa `calcular_poa()` (en `calculos/solar.py`) para calcular la posición solar
(`loc.get_solarposition(tmy.index)`). El modelo de cielo despejado de pvlib deriva GHI, DNI y
DHI de forma **matemáticamente cerrada** a partir de la MISMA posición solar — no hay ningún
punto en el que la irradiancia y la posición solar puedan desalinearse, porque ambas se derivan
del mismo índice en la misma llamada. Esto descarta, para el caso concreto de East2, las seis
causas que pedía investigar el encargo:

| Hipótesis del encargo | Verificado | Resultado |
|---|---|---|
| Zona horaria | Sí — se probó también con `tz="UTC"` en vez de `Europe/Madrid`, mismo resultado (0.0%) | Descartada como causa |
| Centrado horario | Sí — mismo índice para irradiancia y posición solar, sin desplazamiento | Descartada |
| Índices | Sí — `tmy.index` es el mismo objeto pasado a `get_clearsky()` y a `calcular_poa()` | Descartada |
| Conversión GHI/DNI/DHI | Sí — provienen directamente de `get_clearsky()`, sin transformación manual | Descartada |
| Construcción clear-sky Ineichen | Sí — es exactamente el modelo que el chequeo QCRad espera que cierre | Descartada |
| Falsa alarma por formato del TMY | **Parcial** — ver limitación en §10.3 | Ver abajo |

### 10.2 De dónde viene entonces la advertencia que aparece en la batería completa

Al correr East2 junto con `test_transicion_multisuperficie.py` y
`test_flujo_fisico_multisuperficie_end_to_end.py` (como se hizo en la ronda del 21-sep para
verificar que no hay regresión), la advertencia **sí aparece** en la salida de `pytest` — pero
atribuida explícitamente por el propio resumen de `pytest` a esos dos archivos, nunca a
`test_escenario_validacion_east2_sunpower.py`:

```
bipv_python/tests/test_transicion_multisuperficie.py: 28 warnings
bipv_python/tests/test_flujo_fisico_multisuperficie_end_to_end.py: 4 warnings
  .../calculos/solar.py:298: UserWarning: Inconsistencia radiativa: 1264/4110 horas de día
  (30.75%) no cumplen GHI≈DNI·cosZ+DHI ...
```

La causa real: el *fixture* `_tmy()` de esos dos archivos (preexistente, no creado en esta
ronda) construye `G_h`/`Gb_n`/`Gd_h` con una forma sinusoidal genérica —

```python
horas = idx.hour.to_numpy()               # idx en tz="UTC"
forma = np.where(dia, np.sin((horas - 6) / 12.0 * np.pi), 0.0)
G_h, Gb_n, Gd_h = 700.0*forma, 600.0*forma, 150.0*forma
```

— centrada en la hora de reloj UTC (pico en hora UTC 12), sin relación con la posición solar
real en `lat=4.65/4.71, lon=-74.08/-74.07` (Bogotá, UTC-5). El propio docstring de ese fixture
ya lo advierte: *"variación diurna/anual simple y físicamente razonable -- no pretende ser un
TMY real"*. Es un `TMY` de utilería para probar mezcla de superficies/inversores/agregados, no
para irradiancia física, y **no comparte TMY, sesión ni estado con East2** — ambos archivos se
ejecutan de forma completamente independiente. No es un hallazgo nuevo de esta ronda ni un
defecto introducido por el trabajo de East2.

### 10.3 Limitación real encontrada (no es un bug, es un límite de lo que QCRad puede detectar)

El encargo anterior (20/21-sep) ya había identificado un riesgo distinto: que el TMY de East2
y el CSV de sombra (`east2-fs-angular-reconstruido.csv`, en hora local Europe/Madrid) debían
compartir la misma convención horaria para que `alinear_fs_con_tmy()` empareje mes/día/hora
correctamente. Esta auditoría confirma **experimentalmente** que el chequeo QCRad **no puede
detectar ese riesgo**: construir el mismo TMY de East2 con `tz="UTC"` en vez de
`tz="Europe/Madrid"` (mismas horas de reloj, distinto instante absoluto) también da 0.0% de
inconsistencia QCRad, porque el chequeo solo valida que GHI/DNI/DHI cierren consistentemente
CONTRA LA POSICIÓN SOLAR DEL PROPIO ÍNDICE del TMY — nunca compara ese TMY contra un CSV externo
con su propia convención horaria. Es decir: **QCRad es una prueba correcta y necesaria de
cierre físico interno del TMY, pero no es la prueba adecuada para el riesgo de desalineación
horaria TMY↔CSV de sombra** — ese riesgo ya está cubierto por otro mecanismo (la construcción de
`tmy_index_madrid_local` coherente descrita en el informe original y por el hecho de que las
horas de sombra/bypass de East2 coinciden exactamente con la reconstrucción previa, §6).

### 10.4 Corrección aplicada

**No se modificó `calculos/solar.py`** ni la construcción del TMY de East2 (ya era coherente).
Tampoco se tocaron los fixtures de `test_transicion_multisuperficie.py` ni de
`test_flujo_fisico_multisuperficie_end_to_end.py` -- están fuera del alcance de East2, prueban
un comportamiento distinto (mezcla de superficies/inversores, no física de irradiancia), y
modificarlos sin que se pidiera arriesgaría cambiar silenciosamente el comportamiento de
pruebas ajenas (regla 3 del encargo). La única acción fue **añadir 4 pruebas nuevas** a
`test_escenario_validacion_east2_sunpower.py` que fijan como regresión permanente la coherencia
ya demostrada (§12) — si alguna vez alguien cambia la construcción del TMY de East2 de forma
que deje de cerrar físicamente, estas pruebas fallarán con el `pct_inconsistente` exacto, no con
un `UserWarning` que podría pasar inadvertido en la salida de la batería completa.

**Recomendación no aplicada (fuera de alcance, no autorizada por este encargo):** si en el
futuro se quisiera eliminar también la advertencia en `test_transicion_multisuperficie.py` /
`test_flujo_fisico_multisuperficie_end_to_end.py`, la opción más segura sería que esos dos
archivos adopten el mismo patrón `get_clearsky()` que ya usan `test_solar_qcrad.py`,
`test_solar_svf.py`, `test_simulation_pipeline.py` y ahora East2, en vez de la aproximación
sinusoidal -- pero eso es una decisión sobre pruebas ajenas al caso East2 y no se tomó aquí.

### 10.5 Comparación antes/después (East2)

No hubo "antes" con incoherencia real que corregir: el TMY de East2 ya cerraba físicamente
antes de esta auditoría. Para que quede explícito que nada cambió en los resultados físicos de
East2, se repitieron las magnitudes clave del §6 tras añadir las pruebas de esta auditoría:

| Magnitud | Antes de la auditoría QCRad (§6) | Después (22-sep) | Cambio |
|---|---|---|---|
| POA anual | 1038.81 kWh/m² | 1038.81 kWh/m² | Ninguno |
| E_DC anual, referencia | 4450.8 kWh | 4450.8 kWh | Ninguno |
| E_AC anual, referencia | 4317.2 kWh | 4317.2 kWh | Ninguno |
| E_DC anual, East2 mensual/exacto | 2373.9 / 2379.8 kWh | 2373.9 / 2379.8 kWh | Ninguno |
| E_AC anual, East2 mensual/exacto | 2302.7 / 2308.4 kWh | 2302.7 / 2308.4 kWh | Ninguno |
| Horas de sombra, mensual/exacto | 3563 / 3536 | 3563 / 3536 | Ninguno |
| `pct_inconsistente` QCRad | No medido explícitamente antes | 0.0% (medido y fijado en prueba) | Se hizo explícito y permanente |

No se esperaba cambio porque no se modificó ningún código de producción ni la construcción del
TMY de East2 -- este apartado deja constancia de que efectivamente no lo hubo.

## 11. Veredicto (sin cambios respecto a §9)

Se mantiene **parcialmente reproducido**. La auditoría QCRad no cambia el veredicto: no
agrega ni quita fidelidad frente al artículo (que sigue sin publicar energía anual para East2),
solo confirma con evidencia cuantitativa que el supuesto sintético de TMY usado (ya declarado
como supuesto, no como dato real) es al menos internamente coherente desde el punto de vista
radiativo. Esto **no equivale a una validación científica contra el artículo** ni sustituye la
serie CAMS/ERA5 real, que sigue sin estar disponible en este repositorio.

## 12. Pruebas añadidas en esta auditoría

Todas en `bipv_python/tests/test_escenario_validacion_east2_sunpower.py` (el mismo archivo de
la ronda anterior, sin tocar ningún otro archivo de producción):

- `test_tmy_east2_es_radiativamente_coherente_qcrad` — confirma 0 horas inconsistentes, 0.0%,
  diferencia media 0.0 W/m² y ninguna `UserWarning`, con evidencia del dict `qcrad` completo.
- `test_tmy_east2_coherente_con_y_sin_sombra` (parametrizada mensual/exacto) — confirma que la
  coherencia no depende de `p_shade`.
- `test_tmy_east2_coherencia_qcrad_es_determinista` — dos construcciones independientes del
  mismo TMY dan el mismo dict `qcrad` exacto.

### Comandos y resultado

```bash
cd bipv_python
.venv/bin/python -m pytest tests/test_escenario_validacion_east2_sunpower.py -v
→ 15 passed en esta ronda (11 de la reconstrucción original + 4 nuevas de coherencia QCRad)

.venv/bin/python -m pytest \
  tests/test_transicion_multisuperficie.py tests/test_sombras_por_superficie.py \
  tests/test_adaptador_multisuperficie.py tests/test_persistencia_multisuperficie.py \
  tests/test_flujo_fisico_multisuperficie_end_to_end.py tests/test_pagina_transicion_multisuperficie.py \
  tests/test_escenario_validacion_east2_sunpower.py -q
→ 97 passed, 0 failed en esta ronda (la advertencia QCRad de los otros dos archivos sigue
  apareciendo en la salida -- no se silenció -- pero atribuida correctamente a ellos, nunca a
  East2)
```

> **Nota de consistencia (§13):** entre esta auditoría (22-sep, mañana) y la de trazabilidad
> numérica/TMY (22-sep, tarde) se añadieron 3 pruebas más al mismo archivo
> (`test_resultados_numericos_east2_son_la_referencia_reproducible` ×2 parametrizaciones y
> `test_tmy_nuevo_con_sombra_regenerada_cambia_el_resultado`, más
> `test_mascara_de_sombra_realmente_alterada_cambia_huella_y_energia`), por lo que los conteos
> "15 passed" / "97 passed" de este bloque quedaron desactualizados frente a los 19/101 de §4 y
> §13 — ver §13 para los conteos vigentes y verificados de nuevo en esta ronda.

## 13. Reauditoría de cierre (22-sep-2026, tarde) — ¿están cerrados los 4 hallazgos?

**Encargo:** confirmar, con evidencia fresca (no solo releer §10-§12), si los cuatro hallazgos
de la auditoría anterior (trazabilidad numérica, coherencia QCRad, separación de la máscara de
sombra, y manejo del cambio de TMY) están realmente cerrados, y emitir veredicto.

Entre la auditoría de §10 y esta reauditoría, otro proceso de trabajo sobre este mismo
repositorio (visible por los cambios detectados en disco al iniciar esta ronda) amplió
`test_escenario_validacion_east2_sunpower.py` de 15 a **19 pruebas**, añadiendo exactamente las
piezas que motivaban dejar los hallazgos 1, 3 y 4 como "parcialmente cerrados": anclas
numéricas explícitas, una prueba que regenera sombra tras cambio de TMY, y una prueba que
altera `p_shade` de verdad. Esta reauditoría verifica esas piezas con evidencia propia, no da
por buena la palabra del código.

### 13.1 Hallazgo 1 — Trazabilidad numérica

**Estado: cerrado, verificado con evidencia independiente.**

`test_resultados_numericos_east2_son_la_referencia_reproducible` (parametrizada mensual/exacto)
fija `poa_anual_kWh_m2`, `E_dc_anual_kWh`, `E_ac_anual_kWh`, `horas_sombra`/`horas_bypass` y la
media de `p_shade`. Su docstring dice explícitamente: *"Fija la salida del TMY sintético y la
Tabla 4, no un valor del artículo... estos valores son anclas de regresión de esta
reconstrucción concreta"* — nunca se presentan como valores publicados. Se ejecutó el escenario
de nuevo en esta ronda (ver §13.5) y los valores obtenidos coinciden exactamente con los del
informe (§6): POA 1038.81 kWh/m²; DC/AC mensual 2373.9/2302.7 kWh; DC/AC exacto 2379.8/2308.4
kWh; horas 3563/3536; `p_shade` medio 0.38594211095890407/0.3552770547945206.

### 13.2 Hallazgo 2 — Coherencia QCRad

**Estado: cerrado, reconfirmado.**

Se repitió la verificación de §10 con la batería completa (comando en §13.5): la advertencia
QCRad sigue apareciendo únicamente atribuida a `test_transicion_multisuperficie.py` (28
warnings) y `test_flujo_fisico_multisuperficie_end_to_end.py` (4 warnings) — nunca a
`test_escenario_validacion_east2_sunpower.py`, que ahora corre 19 pruebas y sigue en 0
advertencias QCRad. No se silenció ninguna advertencia; sigue visible en la salida de la
batería completa tal como debe ser.

### 13.3 Hallazgo 3 — Separación de la máscara de sombra

**Estado: cerrado, verificado con evidencia independiente propia (no solo la aserción del test).**

`test_cambiar_mascara_de_sombra_cambia_el_resultado` confirma que `mensual`/`exacto` son modos
de **agregación temporal de la misma Tabla 4**, no dos máscaras científicas distintas (mismo
CSV, mismo `alinear_fs_con_tmy`, distinto `modo`). Por separado,
`test_mascara_de_sombra_realmente_alterada_cambia_huella_y_energia` reduce `p_shade` un 20% y
comprueba que la huella de sombra cambia y la energía sube. Se repitió este cálculo de forma
independiente en esta ronda:

| Verificación | Resultado |
|---|---|
| `p_shade` medio original (mensual) | 0.38594 |
| `p_shade` medio reducido 20% | 0.30875 |
| `huellas["sombra"]` distintas | Sí |
| `E_dc` original | 2373.9 kWh |
| `E_dc` con 20% menos sombra | 2789.5 kWh |
| Dirección física | Correcta — menos sombra → más energía |

### 13.4 Hallazgo 4 — Cambio de TMY

**Estado: cerrado, verificado con evidencia independiente propia, incluida la distinción exigida
entre huella geométrica de `p_shade` y firma de vigencia del TMY.**

Se repitió el escenario completo (TMY con `T2m=20°C` → TMY con `T2m=35°C`, mismo sitio, mismo
calendario) de forma independiente:

| Verificación | Resultado |
|---|---|
| Una sombra calculada con el TMY viejo se rechaza al usar el TMY nuevo sin regenerar | Sí — `test_cambiar_tmy_invalida_la_sombra_y_cambia_el_resultado`, `ValueError` con `p_shade`/`firma_sombra` |
| Regenerar `p_shade` + `firma_sombra` con el TMY nuevo permite recalcular | Sí — `test_tmy_nuevo_con_sombra_regenerada_cambia_el_resultado` |
| `p_shade` (array) idéntico entre TMY viejo y nuevo | Sí — mismo calendario/geometría, solo cambió `T2m` |
| `huellas["sombra"]` (geométrica) idéntica entre TMY viejo y nuevo | **Sí, correctamente** — la geometría/alineación no cambió |
| `_firma_sombra["tmy_fingerprint"]` (vigencia) distinta entre TMY viejo y nuevo | **Sí, correctamente** — es lo que sí cambió |
| `huellas["resultados_dc"]` distinta | Sí — el SDM usa `T_amb` para la temperatura de celda, así que el resultado eléctrico cambia aunque la sombra no |
| `E_ac_anual_kWh` cambia | Sí — 2302.7 kWh (T2m=20°C) → 2157.7 kWh (T2m=35°C); dirección física correcta (más calor → menor tensión/eficiencia → menos energía) |

Esto confirma exactamente lo que pedía no confundirse: la huella geométrica de `p_shade` (no
cambió, porque la sombra en sí no cambió) es una magnitud distinta de la firma de vigencia del
TMY (sí cambió, porque el TMY es otro), y el pipeline distingue correctamente ambas sin
mezclarlas.

### 13.5 Comandos ejecutados y salida exacta (esta ronda)

```bash
cd bipv_python
.venv/bin/python -m pytest tests/test_escenario_validacion_east2_sunpower.py -q
```
```
...................                                                      [100%]
19 passed, 43 warnings in 9.02s
```
(43 warnings = `RuntimeWarning: invalid value encountered in divide` de
`scipy.optimize._chandrupatla`, observadas durante el escenario East2; no son QCRad
ni bloquean las pruebas. No se atribuye aquí la condición de preexistentes sin una
línea base equivalente del mismo escenario.)

```bash
.venv/bin/python -m pytest \
  tests/test_transicion_multisuperficie.py \
  tests/test_sombras_por_superficie.py \
  tests/test_adaptador_multisuperficie.py \
  tests/test_persistencia_multisuperficie.py \
  tests/test_flujo_fisico_multisuperficie_end_to_end.py \
  tests/test_pagina_transicion_multisuperficie.py \
  tests/test_escenario_validacion_east2_sunpower.py -q
```
```
....................................................................... [ 71%]
.............................                                           [100%]
101 passed, 107 warnings in 17.28s
```

Advertencias observadas y su origen exacto en esta corrida:

| Advertencia | Cantidad | Archivo(s) que la emiten | Relacionada con East2 |
|---|---|---|---|
| `RuntimeWarning: invalid value encountered in divide` (scipy chandrupatla, SDM) | 28 + 4 + 43 = 75 | `test_transicion_multisuperficie.py`, `test_flujo_fisico_multisuperficie_end_to_end.py`, `test_escenario_validacion_east2_sunpower.py` | También aparece en East2; no es QCRad ni bloquea, pero su condición de preexistente no queda establecida sin una línea base equivalente |
| `UserWarning: Inconsistencia radiativa` (QCRad) | 28 + 4 = 32 | Únicamente `test_transicion_multisuperficie.py` y `test_flujo_fisico_multisuperficie_end_to_end.py` | **No** — cero instancias atribuidas a East2, confirmado de nuevo en esta ronda |

### 13.6 Diferencias entre artículo, reconstrucción previa y APP

Sin cambios respecto a §6 (no se modificó código productivo ni el TMY de East2 en ninguna
ronda) — la tabla completa sigue vigente: ninguna energía anual tiene valor publicado por el
artículo; la brecha ~1.9-2.1% entre "reconstrucción previa" (`ejecutor_escenarios`, script no
conservado) y "APP ahora" sigue sin causa confirmada (nota a); horas de sombra/bypass y
`p_shade` medio coinciden dentro de 0.01-0.02%.

### 13.7 Limitaciones que persisten (sin cambios)

Las seis limitaciones de §8 siguen todas vigentes: TMY sintético (no CAMS/ERA5), Tabla 4
discreta interpolada (posible mezcla con corte de AOI), SDM estimado sin calibración de
laboratorio, ficha AC del inversor no verificada, y la brecha ~2% sin causa confirmada frente a
la reconstrucción previa. Ninguna de estas depende de las pruebas añadidas — son limitaciones
de los datos de entrada, no del pipeline ni de la cobertura de pruebas.

### 13.8 Nuevo veredicto

**Se mantiene "parcialmente reproducido".** No hay evidencia nueva de CAMS/ERA5 real, DSM
original, ficha AC completa del Fronius IG Plus 50 V-1, ni energía anual East2 publicada por el
artículo — las únicas condiciones que, según el propio encargo, justificarían cambiar el
veredicto. Los cuatro hallazgos de la auditoría anterior están confirmados como cerrados con
evidencia fresca e independiente (no solo con la aserción de los tests): trazabilidad numérica
explícita y etiquetada como reconstrucción sintética, coherencia QCRad reconfirmada y con
advertencia correctamente atribuida cuando aparece, separación mensual/exacto con una prueba
que sí modifica `p_shade` en la dirección física esperada, y manejo de cambio de TMY que
distingue correctamente la huella geométrica de sombra de la firma de vigencia del TMY.

Corrección aplicada en esta ronda: los conteos desactualizados "11 pruebas"/"15 passed"/"97
passed" en §4, §5 y §12 (que quedaron obsoletos cuando otro proceso amplió el archivo de 15 a
19 pruebas entre auditorías) se corrigieron para reflejar los 19/101 verificados de nuevo aquí
— era la única inconsistencia real encontrada entre el informe y el estado actual del código;
no se encontró ninguna en el Director (`registro-de-decisiones.md`) ni en la base del Asistente
(`base_conocimiento_asistente.md`), cuyas entradas sobre East2 coinciden con lo verificado en
esta ronda.
