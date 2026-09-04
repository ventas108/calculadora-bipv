# Ampliación del catálogo de inversores: 2.343 modelos reales del dataset Sandia/CEC (NREL/SAM)

**Fecha**: 4 de septiembre de 2026
**Disparador**: el usuario pidió replicar con inversores el mismo trabajo de ampliación de catálogo
ya hecho con 8 fabricantes de paneles, exigiendo explícitamente que siga funcionando "como PVsyst"
en compatibilidad de string por tracker y arreglo en cadena para el diagrama unifilar.

## Investigación previa: por qué esto NO es análogo al import de paneles

Se investigó primero si existía una fuente de datos equivalente a la usada para paneles (CEC
Modules.csv + Sandia JPV 2025). Se encontró `CEC Inverters.csv` (NREL/SAM, 2.343 modelos reales),
que usa el **modelo eléctrico Sandia** (Paco, Pdco, Vdco, C0-C3, Pnt, Vdcmax, Idcmax, Mppt_low/high)
— el mismo estándar que usa `pvlib.inverter.sandia()`.

**Diferencia crítica con paneles**: se revisó qué campos usa realmente
`calculos/comparador_inversores.py::filtrar_inversores_compatibles()` y
`optimization/variables.py` para los chequeos de compatibilidad de string, y son **datos
mecánicos** que el modelo eléctrico Sandia **no contiene en absoluto**: `N Trackers`,
`N Strings/Tracker`, `Corriente Máxima Tracker (A)`, `Corriente Cortocircuito Max Tracker (A)`.
Se confirmó que NREL/SAM no publica un segundo dataset con esta información (a diferencia de
paneles, donde el paper Sandia JPV 2025 sí completaba justo lo que faltaba). La base de datos
completa de inversores de PVsyst (que sí trae estos datos mecánicos, .OND) tampoco está disponible
localmente en bloque — PVsyst la descarga bajo demanda desde sus servidores dentro del programa,
datos propietarios no descargables en bloque de forma pública.

## Estrategia adoptada: importar lo real, excluir automáticamente lo incompleto de la optimización

En vez de fabricar `N_mppt`/corriente por tracker (lo que arriesgaría una recomendación de
stringing incorrecta, justo lo que este proyecto ha evitado activamente todo este mes), se optó
por:

1. **Importar los 2.343 modelos reales** con los campos que el modelo Sandia SÍ garantiza:
   `Vdc_max`=Vdcmax, `Rango MPPT Min/Max`=Mppt_low/Mppt_high, `Potencia AC nominal (kW)`=Paco/1000.
   `Potencia FV Max Recomendada (W)`=Pdco, etiquetado en `Notas` como la potencia DC de referencia
   del modelo Sandia (a Vdc=Vdco produce exactamente Paco), **no** necesariamente el límite oficial
   de sobredimensionamiento del fabricante.
2. Todos quedan con `Datos completos (Si/No)` = **"No"** (le faltan los 4 campos mecánicos).
3. **Extender el filtro real de `variable_inversor()`** (antes solo lo tenía `variable_panel()`)
   para excluir del optimizador de Fase 4 cualquier inversor sin `Vdc_max`, `Vmppt_max`,
   `Isc_max_tracker`/`I_max_tracker`, o `N_mppt`/`n_trackers` — mismo criterio que ya exigía
   `filtrar_inversores_compatibles()` para no marcar "Ficha incompleta".

## Hallazgo colateral real: 4 inversores YA existentes tenían el mismo problema

Antes de aplicar el nuevo filtro se verificó contra los 108 inversores previos: **4 ya estaban
incompletos** (`POWEST-1KVA-12V`, `POWEST-3KVA-24V` — sin corriente máxima por tracker; `LSP 100K`
— sin `Vmppt_max`; `Woodward IDS SOLO 500` — sin datos mecánicos completos). Estaban expuestos al
mismo riesgo real (`calculos/dimensionamiento.py` cae a `N_mppt or 1` en algunos caminos) sin que
nada los excluyera del optimizador antes de este fix. El nuevo filtro los cierra también a ellos,
no solo a los nuevos.

## Bug real encontrado y corregido durante la verificación: colisión de claves

Al verificar el import con el loader real (`cargar_catalogo_inversores()`), el total esperado
(108+2.343=2.451) no coincidía (solo 2.432 sobrevivían). Se encontró que **19 modelos del dataset
CEC comparten el mismo string de "Modelo" bajo 2 fabricantes distintos** (rebadge/OEM real, ej.
`"MIN 10000TL-XH-US {240V}"`), y el diccionario de `catalogo_inversores_excel.py` se armaba
usando solo `Modelo` como clave — un fabricante pisaba al otro en silencio. **Corregido**: la
clave se desambigua con `f"{modelo} [{marca}]"` únicamente cuando hay colisión real detectada
(conteo de `Modelo` > 1) — las claves sin colisión (incluidos los 108 previos) quedan exactamente
igual que antes.

## Verificación

- `CEC Inverters.csv`: 2.343 filas de datos reales, 0 con campos núcleo faltantes (Vac, Paco,
  Pdco, Vdco, Vdcmax, Mppt_low, Mppt_high), 0 nombres duplicados, 100% con patrón
  "Fabricante: Modelo {Vac}".
- Catálogo real: 108 → **2.451** inversores.
- `variable_inversor()`: 104 candidatos elegibles para el optimizador (igual que antes del
  import — los 104 previos completos siguen intactos), **2.347 excluidos** (2.343 nuevos + 4
  previos ya incompletos).
- `filtrar_inversores_compatibles()` verificado en vivo contra ASP-ST1-T40/N_serie=8: 2.347 con
  motivo "Ficha incompleta (tensiones/corrientes/trackers)", 7 compatibles — ningún dato inventado
  se cuela al resultado.
- Página 🔌 Dimensionamiento: ya mostraba advertencia visible ("🟡 Inversor incompleto — faltan:
  ...") para selección manual antes de este cambio — mismo patrón de transparencia que el resto
  del proyecto, no bloqueante, consistente con paneles.

## Scripts

- `datos/agregar_inversores_cec_nrel.py` — import de producción, protegido contra duplicados por
  (Marca, Modelo).
- Fix en `datos/catalogo_inversores_excel.py::_cargar_catalogo_inversores_cached()` — desambiguación
  de clave por colisión real.
- Fix en `optimization/variables.py::variable_inversor()` — filtro de ficha completa.
- Nueva función `calculos/comparador_inversores.py::inversores_excluidos_por_ficha_incompleta()`.
