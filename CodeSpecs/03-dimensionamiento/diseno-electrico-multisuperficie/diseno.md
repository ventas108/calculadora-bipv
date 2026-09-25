# Diseño — Diseño eléctrico multi-superficie: inversores, MPPT y grupos de strings

**Estado:** implementación

## Entradas

- Por superficie (`superficies_bipv`): geometría, POA, sombra (`p_shade`) y
  panel (`05/panel-por-superficie`), más la lista `grupos`.
- Inversores (`multisup_inversores`) con ficha.
- Catálogo de inversores (`cargar_catalogo_inversores`, el mismo de 📐
  Dimensionamiento) e inversor del proyecto (`inversor_dict_dim`,
  `inversor_nombre_dim`).
- Temperaturas de diseño del proyecto: `T_min_diseno`, `T_cel_realista`,
  `T_cel_extremo` (`calculos/temperatura.KEYS_TEMPS_DISENO`).

## Tipos de datos

### Grupo de strings (dentro de cada superficie, lista `grupos`)

| Campo | Tipo | Fase | Descripción |
|---|---|---|---|
| `gid` | `str` | A | Identificador estable dentro de la superficie («G1», «G2»…) |
| `topologia` | `str` | A | Conjunto cerrado; en esta Spec solo `"string"`. La Spec B agrega `"microinversor"` y `"optimizador"` |
| `inversor_id` | `str` | A | Inversor asignado |
| `mppt` | `int` ≥ 1 | A | Entrada MPPT del inversor |
| `n_serie` | `int` ≥ 1 | A | Módulos en serie por string |
| `n_paralelo` | `int` ≥ 1 | A | Strings en paralelo del grupo |
| campos de la topología | — | B | La Spec B agrega los suyos (p. ej. módulos por equipo) sin tocar los anteriores |

Módulos del grupo = `n_serie × n_paralelo`.

### Inversor (`multisup_inversores`)

| Campo | Tipo | Descripción |
|---|---|---|
| `inversor_id` | `str` | Identificador (como hoy) |
| `clase` | `str` | Conjunto cerrado; en esta Spec solo `"string"` (central incluido). La Spec B agrega `"microinversor"` y `"optimizado"` |
| `origen_ficha` | `str` | `"proyecto"` · `"catalogo"` · `"manual"` |
| `nombre` | `str` | Modelo del catálogo o del proyecto; vacío si es manual |
| `ficha` | `dict` | Contrato del catálogo: `Vdc_max`, `Vmppt_min`, `Vmppt_activo_min`, `Vmppt_max`, `I_max_tracker`, `Isc_max_tracker`, `N_mppt`, `n_strings_tracker`, `P_ac_nom_W` |
| `eta_inversor` | `float` (0, 1] | Siempre explícita: el catálogo no la trae |
| `P_ac_nom_W` | `float` | De la ficha; editable si es manual |
| `tipo` | derivado | `dedicado`/`compartido` según los grupos asignados (como hoy) |

### Migración de proyectos anteriores

Una superficie sin `grupos` y con `inversor_id`, `n_serie` y `n_paralelo` se
lee como un grupo `G1`, con topología `string` y MPPT 1. Un inversor sin
`origen_ficha` se lee como `manual`. La migración es pura
(`grupos_de_superficie(sup)`), no muta y se hace una vez al cargar.

## Salidas

- Nuevo módulo puro `calculos/diseno_electrico_multisup.py`:
  - `grupos_de_superficie(sup) -> list[dict]` (con migración).
  - `ficha_inversor(inv, inversor_dict_dim, catalogo) -> dict` (resuelve
    `origen_ficha`).
  - `temperaturas_diseno(ss) -> {"T_frio", "T_real", "T_extremo", "origen"}`,
    con origen `proyecto` o `por_defecto` (este último con aviso).
  - `rango_n_serie(panel, ficha, temps) -> (n_min, n_max) | None`, con
    `optimizar_n_serie` como base.
  - `validar_diseno_electrico(superficies, inversores, paneles, temps) ->
    DiagnosticoElectrico` (ver abajo).
  - `firma_diseno_electrico(superficies, inversores) -> dict[uid, str]` e
    `invalidar_por_cambio_electrico(ss)`, con el mismo criterio por `uid`
    que `invalidar_por_cambio_panel`.
- `DiagnosticoElectrico`:
  - `grupos`: por grupo, `{uid, gid, superficie, panel, inversor_id, mppt,
    n_serie, n_paralelo, rango_n_serie, checks, estado}`;
  - `mppt`: por (inversor, MPPT), `{grupos, paneles, orientaciones,
    strings, isc_total, checks, estado}`;
  - `inversores`: por inversor, `{mppt_usados, mppt_disponibles,
    P_dc_stc_kW, relacion_dc_ac, checks, estado}`;
  - `superficies`: por superficie, `{modulos, area_instalada_m2, area_m2,
    cobertura_pct, checks, estado}`;
  - `estado_global` (`"verde"`/`"amarillo"`/`"rojo"`), `bloqueos` y `avisos`
    (texto listo para mostrar).
  - Cada check es `{nombre, valor, limite, unidad, formula, fuente, estado}`.

## Reglas de validación

Temperaturas: las del proyecto (`temperaturas_diseno`).

| Nivel | Regla | Fuente | 🔴 | 🟡 |
|---|---|---|---|---|
| Grupo | Voc en frío ≤ Vdc máx.; Vmp real y extremo dentro de [MPPT mín. activo, MPPT máx.] | `evaluar_compatibilidad_string` con `N_strings_tracker` = strings del MPPT | `compatible = False` | `alerta_margen` o ficha sin datos (`evaluable = False`) |
| MPPT | Isc × strings × 1,25 ≤ Isc máx. del tracker | ídem | supera | margen < 7,5 % |
| MPPT | Strings ≤ `n_strings_tracker` | ficha | supera | ficha sin dato |
| MPPT | Un solo panel por MPPT | grupos | dos paneles distintos | — |
| MPPT | Una sola orientación por MPPT | grupos | — | orientaciones distintas (la sección 6 cuantifica la pérdida) |
| Inversor | MPPT usados ≤ `N_mppt`; número de MPPT de cada grupo ≤ `N_mppt` | ficha | supera | ficha sin dato |
| Inversor | Relación DC/AC | `evaluar_relacion_dc_ac` sobre la suma del inversor | 🔴 de la función | 🟠 de la función |
| Superficie | Módulos × área del módulo ≤ área de la superficie | panel, grupos | > 100 % | < 80 % (área sin módulos) |
| Proyecto | Temperaturas del proyecto disponibles | `T_min_diseno`… | — | valores por defecto |

- Inversor manual o del catálogo sin `Vdc_max`, MPPT o corriente: sus grupos
  quedan 🟡 «no validado», nunca 🟢.
- Grupo sin inversor, MPPT fuera de rango o N no entero ≥ 1: 🔴.

## Energía y cálculos

- **Área instalada.** Si la superficie tiene grupos, la energía simplificada
  usa `área instalada = Σ módulos × área del módulo` (≤ área de la
  superficie) y lo indica en el resumen («área instalada 94,3 de 97,3 m²»).
  Sin grupos usa el área de la superficie con el aviso «estimación por área».
- **Modo físico.** `construir_proyecto_desde_session_state` crea una unidad
  física por grupo (`superficie_nueva` con el panel, POA y `p_shade` de su
  superficie y los N del grupo), con nombre «Superficie · G1». La etapa de
  inversor (`recalcular_etapa_inversor_bus`) no cambia. El desglose publicado
  agrega los grupos por superficie. La compatibilidad usa la ficha y las
  temperaturas del proyecto.
- **Bypass por superficie.** Se simula por grupo, con sus strings. La pérdida
  de la superficie es la media ponderada por módulos, aplicada a su energía
  simplificada; la tabla muestra cada grupo.
- **Sección 6.** Los MPPT y su asignación salen de los grupos; los grupos
  del mismo inversor y MPPT se simulan como strings en paralelo. Sigue siendo
  informativa.

## Reglas hacia Financiero

| Estado global | Modo físico | Simplificado y bypass |
|---|---|---|
| 🟢 | Publica | Publica |
| 🟡 | Publica, con aviso en el banner | Publica, con «diseño eléctrico no verificado» en el banner |
| 🔴 | **No publica**; lista los bloqueos | Publica, con «diseño eléctrico: 🔴 con fallas» en el banner |

El estado se guarda con la publicación (`multisup_estado_electrico`) y se
muestra en Financiero, Baterías y CO₂ donde ya aparece el banner
multi-superficie.

## Errores posibles

- Superficie activa sin grupos ni campos antiguos: 🔴 «sin diseño eléctrico».
- `topologia` o `clase` fuera del conjunto de esta Spec: 🔴 «topología no
  soportada todavía» (la Spec B la habilitará). Nunca se trata como string en
  silencio.
- `gid` duplicado en una superficie o `inversor_id` inexistente: 🔴.
- Payload con grupos inválidos: se rechaza la carga con el motivo.

## Invalidación

- Cambiar un grupo (inversor, MPPT, N) o la ficha o η de un inversor retira
  la energía publicada y los resultados de bypass, MPPT, físico y la
  comparación física. Agregar o quitar superficies no cuenta, por el mismo
  criterio por `uid` de `invalidar_por_cambio_panel`.
- No cambia `firma_poa` ni `firma_sombra`.

## Persistencia

- `_superficie_input` guarda `grupos`; `electrical.inversores` guarda
  `clase`, `origen_ficha`, `nombre` y `ficha`.
- Las asignaciones del payload pasan a ser por grupo. Un payload antiguo se
  migra con `grupos_de_superficie`.
- `_comparar_contexto` compara los grupos y los inversores con su ficha.

## Dependencias

- Previos: `03-dimensionamiento` (funciones eléctricas, temperaturas,
  inversor del proyecto), `05/panel-por-superficie`,
  `05/publicacion-energia-multisuperficie`, `05/persistencia-multisuperficie`.
- Dependiente: Spec B (microinversores y optimizadores) sobre `topologia` y
  `clase`.
- Capas: cálculo (módulo nuevo, adaptador físico, bypass), estado
  (superficies, inversores, invalidación), interfaz (Vista 3D), persistencia,
  Asistente y manual.

## Criterios de aceptación

- **A1:**
  - SPR-E20-327 con N serie 20 en un inversor Vdc 1000 V → 🔴 «Voc en frío
    1.369 V > Vdc máximo 1000 V», con la fórmula y T mín. del proyecto;
  - junto al N serie aparece «rango válido 5–14»;
  - la fachada ASP-ST1-T40 da rango 3–8 con la misma ficha;
  - dos paneles en el mismo MPPT → 🔴;
  - inversor manual sin ficha → grupos 🟡 «no validado»;
  - un proyecto guardado antes carga con un grupo G1 por superficie.
- **A2:**
  - una superficie con dos grupos en dos inversores da la misma E_ac física
    que dos superficies equivalentes de hoy;
  - con 🔴 el modo físico no publica;
  - el simplificado usa el área instalada;
  - cambiar un N serie retira la energía y conserva la POA;
  - guardar y cargar conserva grupos y fichas.
- **A3:**
  - la sección 6 usa los MPPT de los grupos y no tiene selectores propios;
  - el manual y el Asistente describen la tabla de diseño eléctrico.

## Pruebas requeridas

- Migración: superficie antigua → G1; inversor antiguo → manual.
- `rango_n_serie`: ASP-ST1-T40 = 3–8 y SPR-E20-327 = 5–14 con la ficha del
  ejemplo; ficha incompleta → `None`.
- Cada regla de la tabla de validación en 🟢, 🟡 y 🔴.
- Temperaturas: del proyecto frente a por defecto (aviso).
- Físico por grupos: equivalencia con superficies separadas; recorte por
  inversor sumando grupos de superficies distintas.
- Área instalada y cobertura; bypass ponderado por módulos.
- Reglas hacia Financiero con 🟢, 🟡 y 🔴.
- Invalidación por grupo e inversor, sin falsos positivos al agregar
  superficies.
- Persistencia: ida y vuelta con varios grupos, payload antiguo, grupos
  inválidos rechazados.
- Topología no soportada → 🔴, nunca string en silencio.
- Página (AST y `AppTest`): tabla de diseño eléctrico, sin selectores de MPPT
  propios en la sección 6 (A3).
- Regresión: suites de multi-superficie, bypass, MPPT, persistencia y
  Dimensionamiento.
