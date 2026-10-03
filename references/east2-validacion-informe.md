# Informe de validación — East2 FS_geometrico (reconstrucción angular)

## ⚠️ ADVERTENCIA — LEER ANTES DE USAR

**Este conjunto de archivos es una RECONSTRUCCIÓN A PARTIR DE UNA TABLA PUBLICADA,
NO el DSM, la malla 3D ni los puntos de análisis originales de East2.** No existe
en este proyecto ni fue proporcionado ningún modelo 3D real del edificio del
artículo de referencia (CIEMAT, Madrid). El motor oficial de sombreado de la
Calculadora BIPV (`docs/contratos/shading-engine-contract.v1.json`) exige
`points` y `triangles` 3D reales, que **no existen para East2**.

Lo que sí se hizo: transcribir literalmente la **Tabla 4** del artículo (DOI
[10.3390/buildings16091668](https://doi.org/10.3390/buildings16091668)),
titulada *"Linear shading factor for the beam component based on solar
azimuth-to-elevation angle combinations using a DSM for the East2 array,
calculated with PVsyst"* — una rejilla real de 19 acimutes × 10 elevaciones
(190 valores) calculada por los autores a partir de un DSM (LiDAR) real —,
convertirla de convención PVsyst a convención brújula, e interpolarla
bilinealmente a resolución horaria. **Es un dato publicado real y específico
de East2** (no una digitalización aproximada de una figura ni una invención),
pero sigue siendo una rejilla discreta e interpolada, no el DSM continuo
original, y **puede mezclar el corte por autoorientación del panel con la
sombra real de vegetación** (ver limitación 4 más abajo). **No es válida para
homologación oficial.**

## Archivos generados

| Archivo | Contenido |
| --- | --- |
| `east2-mascara-angular.json` | Transcripción de la Tabla 4 del artículo (rejilla acimut→elevación→factor), con metadatos de fuente, método y limitaciones |
| `generar_east2_fs_angular.py` | Script que calcula la posición solar horaria (reutilizando `posiciones_solares` de `bipv_python/calculos/sombras_3d.py`, sin modificarlo) e interpola bilinealmente la rejilla |
| `east2-fs-angular-reconstruido.csv` | Salida horaria: `Mes,Dia,Hora,FS_geometrico,Fachada,Punto,Fila` |
| `east2-validacion-informe.md` | Este informe |

## Parámetros usados

| Parámetro | Valor |
| --- | --- |
| Latitud | 40.45 |
| Longitud | -3.74 |
| Zona horaria | Europe/Madrid |
| Fachada | East2 |
| Azimut del arreglo | 82.65° |
| Inclinación | 90° |
| Periodo | Año horario completo (2023, hora local), filtrado a horas con elevación solar > 1.0° (mismo umbral `ALTURA_SOLAR_MIN_DEG` del motor oficial) |
| Convención FS_geometrico | 0 = sin sombra, 1 = sombra geométrica total; valores intermedios = sombra parcial (tal como los publica la Tabla 4 original) |

## Verificaciones solicitadas

### 1. Existencia de los cuatro archivos

Verificado con `ls -la` sobre los cuatro archivos en `/workspaces/calculadora-bipv/references/` — los cuatro existen físicamente (ver salida de verificación al final de la conversación).

### 2. Número de filas del CSV

**4357 filas de datos** (más 1 fila de encabezado). Corresponde a las horas del año con elevación solar > 1.0°.

### 3. Rango mínimo y máximo de FS_geometrico

- Mínimo: **0.0**
- Máximo: **1.0**

### 4. Ausencia de valores fuera de [0,1]

**0 filas** fuera del rango [0,1] (verificado programáticamente en el script generador; la tabla fuente ya está acotada a [0,1] y la interpolación bilineal entre valores de [0,1] no puede salir de ese rango).

### 5. SHA-256 del PDF de referencia

```
39683bfdaecc085a3c9e75308350d528cead1e6303f51b7bfae450e899f41e1d  references/buildings-16-01668-v2.pdf
```

### 6. Resumen estadístico adicional

De las 4357 horas con sol:
- **3765 horas (86.4%)** tienen `FS_geometrico > 0` (algún grado de sombra/no visibilidad del sol).
- **2389 horas (54.8%)** tienen `FS_geometrico ≈ 1` (sombra total según la tabla).

Este porcentaje tan alto de "sombra total" es esperable si la tabla incluye el
corte por autoorientación del panel (ver limitación 4), ya que una fachada
vertical solo recibe haz directo durante una fracción del día.

## Limitaciones explícitas

1. La Tabla 4 es una rejilla discreta (paso 20° en acimut, 10° en elevación); la interpolación bilineal entre puntos es una aproximación respecto al DSM continuo original, especialmente en los bordes de sombra donde el factor cambia bruscamente entre celdas vecinas.
2. El artículo no aclara si esta tabla es idéntica para East1/East2/East3 o exclusiva de East2; se transcribió tal como el artículo la etiqueta explícitamente ("for the East2 array").
3. La transcripción fue manual (verificada con un control de continuidad circular: el valor en acimut -180° debe coincidir con el de +180° en cada fila, lo cual se cumple en las 10 filas transcritas), pero no hay una segunda fuente independiente para contrastarla.
4. **Posible mezcla de convenciones (no confirmada):** al inspeccionar los valores, el factor vale 1 en una franja amplia de acimutes que coincide aproximadamente con "detrás del plano" del array, y solo muestra valores parciales (0.08–0.94) en una franja estrecha alrededor del propio acimut del array (82.65°). Esto sugiere que la tabla de PVsyst podría incluir el corte por autoorientación del panel (cos(AOI)≤0) además de la sombra real de vegetación — a diferencia de `FS_geometrico` en `bipv_python/calculos/sombras_3d.py` de este proyecto, que es puro choque rayo-obstáculo, independiente de la orientación del panel. **Si el motor oficial del proyecto aplica su propio corte de ángulo de incidencia aguas abajo, usar este CSV tal cual podría duplicar esa pérdida.** Esto no fue confirmado con los autores del artículo.
5. No se modificó ningún archivo de código productivo del proyecto; `generar_east2_fs_angular.py` solo importa (sin alterar) `posiciones_solares` y `ALTURA_SOLAR_MIN_DEG` de `bipv_python/calculos/sombras_3d.py`.

## Validación de carga y alineación en BIPV

Validación ejecutada el 20-sep-2026, sin modificar código:

- `cargar_csv_fs()` aceptó el archivo como fuente `geometrico` y eligió
	`FS_geometrico`, no `FS_climatico` ni `FS` combinado.
- Filas cargadas: `4357`.
- Duplicados en `(mes, dia, hora)`: `0`.
- Cobertura exacta contra un índice horario 2023 de `Europe/Madrid`: `4357/8760`
	(`49.7%`).
- Cobertura por `(mes, hora)`: `4626/8760` (`52.8%`). Esto no significa que
	falten meses: los 12 meses están presentes; la cobertura menor se debe a que
	la salida solo contiene horas con elevación solar superior a `1°`.
- Serie alineada en modo `exacto`: promedio `p_shade = 0.3553`, con `3765`
	horas mayores que cero.
- Serie alineada en modo `mensual`: promedio `p_shade = 0.3859`, con `4139`
	horas mayores que cero.

La alimentación queda validada hasta la frontera de datos. No se ejecutó una
comparación energética automática porque `run_bipv_simulation()` no admite un
argumento de FS horario y su contrato v1 declara explícitamente que no incluye
bypass de diodos. Pasar el CSV como `fs_horario` produce un `TypeError`; por
tanto, estas métricas prueban carga y alineación, no homologación de producción.

## Corrida experimental mediante el ejecutor de escenarios

Con autorización del 20-sep-2026 se ejecutó la ruta existente
`calculos.ejecutor_escenarios.ejecutar_escenarios()`, que sí acepta el CSV como
`df_fs_actual`, alinea `FS_geometrico` y llama al modelo
`simular_bypass_horario()`. No se modificó `run_bipv_simulation()` ni código
productivo.

### Entradas experimentales

- East2: latitud `40.45`, longitud `-3.74`, tilt `90°`, azimut `82.65°`.
- Configuración eléctrica: `14` módulos, `7S x 2P`, eta inversor `0.97`.
- Panel: `SPR-E20-327 (E20-327NE-WHT-D)`, añadido al catálogo Python y al Excel
	visible. Sus parámetros SDM son estimados desde la ficha pública porque el
	fabricante no publica `I_L_ref`, `I_o_ref`, `R_s`, `R_sh_ref` ni `n`.
- TMY: año horario determinista `2023`, Madrid, clear-sky Ineichen, temperatura
	ambiente constante de `20 °C` y altitud asumida de `667 m`.
- Comparación: referencia con `p_shade=0` frente al CSV East2 reconstruido.

Estas entradas son un **experimento del pipeline**, no los datos medidos del
artículo. La ficha E20-327 pasa la validación interna de placa: Voc e Isc con
`0.00%` de error, Vmp con `1.53%`, Imp con `1.56%` y Pmax con `0.00%`, todos
dentro de la tolerancia del `6%`.

### Resultados

| Modo de alineación | E_AC referencia | E_AC East2 | Pérdida | Horas sombra | Horas bypass |
|---|---:|---:|---:|---:|---:|
| Mensual | `4236.4 kWh` | `2255.7 kWh` | `1980.7 kWh` (`46.75%`) | `3563` | `3563` |
| Exacto | `4236.4 kWh` | `2263.0 kWh` | `1973.4 kWh` (`46.58%`) | `3536` | `3536` |

Promedio `p_shade` anual: `0.3859` en modo mensual y `0.3553` en modo exacto.
La energía sombreada fue menor que la referencia en ambos modos, como exige la
coherencia física básica.

Energía DC: referencia `4367.4 kWh`; East2 `2325.5 kWh` en modo mensual y
`2332.9 kWh` en modo exacto. El bypass disipó `2041.9 kWh` y `2034.5 kWh`,
respectivamente.

Huellas reproducibles de la serie `p_shade`:

- Mensual: `1a8747baa99b477d5cb1c6caebaa048285477f0b391a9c57931ced47b739ce56`.
- Exacto: `2b1f7b9d8aa66eeda95a74cd9c605af6c97d2e6822f68ab083090f4cf1c857ad`.

### Interpretación y límite

El resultado muestra que la APP puede consumir el `FS_geometrico` reconstruido
y producir una comparación base/sombreada mediante bypass usando el mismo
modelo de panel declarado por el artículo, con parámetros SDM estimados. No
demuestra que la APP homologue al artículo: la máscara es interpolada, el SDM
no fue publicado por SunPower, el TMY es sintético y no se comparó contra la
producción medida 2017–2023.
Además, la Tabla 4 podría incluir corte por ángulo de incidencia; si es así,
parte de la pérdida calculada podría duplicar pérdidas ópticas ya tratadas por
la APP.
