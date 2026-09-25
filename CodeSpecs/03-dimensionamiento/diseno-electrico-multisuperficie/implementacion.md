# Implementación — Diseño eléctrico multi-superficie: inversores, MPPT y grupos de strings

**Estado:** implementación

## Cambios realizados

### Fase A1

- Nuevo `calculos/diseno_electrico_multisup.py` (puro, sin Streamlit):
  - `normalizar_ficha_inversor`: contrato único para fichas del Excel
    (`n_trackers`, `n_strings_tracker`, `V_mppt_activo`) y del catálogo
    interno (`N_mppt`, `N_strings_nativo`, `eficiencia_max`). Sin MPPT mínimo
    activo usa el mínimo del MPPT.
  - `inversor_normalizado`: `clase` `string` y `origen_ficha` `manual` para
    inversores anteriores.
  - `grupos_de_superficie` (migración a G1) y `campos_legacy_desde_grupos`.
  - `temperaturas_diseno`: `T_min_diseno`, `T_cel_realista`, `T_cel_extremo`
    o, si faltan, −5 / 36,35 / 41,94 °C con origen `por_defecto`.
  - `rango_n_serie`: N que cumplen las mismas condiciones de tensión que
    `evaluar_compatibilidad_string`.
  - `validar_diseno_electrico`: diagnóstico por grupo, MPPT, inversor y
    superficie. Cada comprobación trae valor, límite, unidad, fórmula, fuente
    y estado; además devuelve bloqueos, avisos y estado global.
- `pages/9_🗺️_Vista_3D.py`, 🔌 Inversores por superficie:
  - Selector «Ficha del inversor»: del proyecto, del catálogo (Excel o
    interno) o manual; resumen de la ficha. La P AC sale de la ficha, salvo
    en manual.
  - Por superficie: Inversor, MPPT, N serie y N paralelo del grupo G1, y
    «Rango válido de N serie con <panel>: a–b».
  - Los campos siguen el patrón del editor de superficies (sin
    `value=`/`index=`), así que ya no pueden revertir el valor escrito.
  - Tabla «⚡ Diseño eléctrico — 🟢/🟡/🔴» (grupos, MPPT, inversores,
    superficies) con bloqueos, avisos y «🔎 Cómo se calcula cada valor». Una
    nota indica que todavía es informativa.
- Base de conocimiento del Asistente.

Desviaciones del diseño, con motivo:

- **Un solo grupo por superficie en el editor de A1.** El modelo, la
  migración y la validación ya aceptan varios grupos, pero el modo físico,
  el bypass y el MPPT siguen leyendo los campos de superficie hasta A2.
  Permitir varios grupos antes dejaría cálculos sin respaldo. Si una
  superficie ya tiene varios grupos, el editor lo dice y no los toca.
- **`rango_n_serie` recorre los N con `calcular_voc_string` y
  `calcular_vmp_string`** en lugar de llamar a `optimizar_n_serie`. Esa
  función exige `Vmppt_activo_min` y un N_min/N_max fijos (6–12). Las
  condiciones son las mismas de `evaluar_compatibilidad_string`.
- **El Asistente se actualiza ya en A1** y no esperó a A3, porque la
  pantalla cambia en esta fase.

### Fase A2

- `calculos/diseno_electrico_multisup.py`:
  - Caja combinadora: strings > entradas del MPPT con Isc × strings × 1,25 ≤
    límite → 🟡 con explicación sencilla (`caja_combinadora`, conteo
    `cajas_combinadoras` por inversor); si la corriente no cabe, 🔴.
  - Relación DC/AC: nunca 🔴; 🟡 fuera de 1,00–1,35 con explicación para
    quien empieza (inversor sobredimensionado o recorte en horas de sol). No
    se evalúa en un inversor sin grupos.
  - `_asegurar_mensajes`: cada comprobación 🔴 tiene su bloqueo y cada 🟡 su
    aviso, así la tabla y los mensajes nunca muestran colores distintos.
  - `resumen_estado_electrico`, `paneles_superficies_estado`,
    `diagnostico_electrico_estado`, `modulos_de_superficie`,
    `area_energia_superficie`, `superficies_para_energia`,
    `firma_diseno_electrico` e `invalidar_por_cambio_electrico`.
- `calculos/inversores_multisuperficie.py`: validación y asignaciones por
  grupo («Sur · G1»); los errores nombran el grupo.
- `calculos/adaptador_multisuperficie.py`: una unidad física por grupo con
  el área repartida por módulos y `temperaturas_diseno` del proyecto; el
  desglose vuelve a sumar por superficie; con 🔴 no publica.
- `calculos/transicion_multisuperficie.py`: compatibilidad con las
  temperaturas del proyecto.
- `calculos/publicacion_multisuperficie.py`: `multisup_estado_electrico` y
  `aviso_estado_electrico` (mismo mensaje en las cuatro páginas).
- `calculos/strings_superficie.py`: `strings_grupos_superficie` (strings de
  cada grupo, sin estimar nada con varios grupos),
  `perdida_ponderada_por_modulos`; `strings_superficie` rechaza superficies
  con varios grupos.
- `calculos/vinculador_sombra_multisuperficie.py`: el editor conserva los
  grupos al reconstruir la superficie y un cambio de N serie de un grupo
  retira la sombra, como el campo antiguo; `resumen_estado_fisico_superficies`
  revisa cada grupo.
- `calculos/persistencia_multisuperficie.py`, `proyectos_manager.py`,
  `invalidacion.py`: grupos validados y guardados, comparación al cargar,
  claves nuevas en los registros.
- Páginas: Vista 3D (editor de varios grupos, área instalada en resumen,
  integración, producción y vista, bypass por grupo, aviso de sección 6,
  estado eléctrico en el banner y en la comparación física, explicación
  sencilla y anchos de columna); Financiero, Baterías y CO₂ muestran el
  estado eléctrico publicado.
- Base de conocimiento del Asistente y contratos del director.

Desviaciones del diseño, con motivo:

- **La sección 6 deja fuera las superficies con varios grupos**, con aviso
  explícito. Su unificación con los MPPT de los grupos es la fase A3;
  simularlas antes con un solo string por superficie inventaría el diseño.
- **La pérdida de bypass de la superficie se pondera por módulos.** Todos los
  grupos de una superficie ven la misma POA y la misma sombra, así que su
  energía es proporcional a sus módulos.
- **Las horas de bypass de una superficie con varios grupos son las del grupo
  con más horas**, para no sumar horas que ocurren a la vez.
- **Error encontrado en la prueba de humo:** el editor de superficies
  reconstruye cada superficie en cada rerun y perdía los grupos («➕ Agregar
  grupo» no tenía efecto). `preservar_o_invalidar_campos_fisicos` ahora
  conserva `grupos`; hay una prueba para ello.

### Complemento de A2 antes de A3

- `calculos/diseno_electrico_multisup.py`: comprobación «Mismo N serie en el
  MPPT» (🔴 si los strings de un MPPT tienen distinto número de módulos). El
  bloqueo nombra cada grupo con su largo, explica por qué (strings en
  paralelo al mismo voltaje) y da la solución. Los grupos sin N serie válido
  no cuentan: ya tienen su propio 🔴. Como todo 🔴, impide adoptar el modo
  físico.
- `calculos/campos_editor.py` (nuevo): `sincronizar_campo`, usado por los
  editores de Vista 3D. La referencia `_ref_<clave>` ahora guarda el valor
  que queda en el campo (el que la página guarda), no el dato de entrada.
  Antes, un segundo cambio seguido del mismo campo se revertía; lo detectó la
  prueba de humo de esta regla y también afectaba al azimuth de las
  superficies.
- Página: columna «N serie de los strings» en la tabla de MPPT y entrada
  «Mismo N serie en el MPPT» en la explicación sencilla.
- Base de conocimiento del Asistente.

## Archivos modificados

### Fase A1

- `bipv_python/calculos/diseno_electrico_multisup.py` (nuevo)
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_diseno_electrico_multisup.py` (nuevo),
  `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/03-dimensionamiento/diseno-electrico-multisuperficie/`
- `CodeSpecs/00-director/registro-de-decisiones.md`

### Fase A2

- `bipv_python/calculos/`: `diseno_electrico_multisup.py`,
  `inversores_multisuperficie.py`, `adaptador_multisuperficie.py`,
  `transicion_multisuperficie.py`, `publicacion_multisuperficie.py`,
  `strings_superficie.py`, `vinculador_sombra_multisuperficie.py`,
  `persistencia_multisuperficie.py`, `proyectos_manager.py`, `invalidacion.py`
- `bipv_python/pages/`: Vista 3D, Financiero, Baterías y Balance, Impacto CO₂
- `bipv_python/tests/test_diseno_electrico_fisico_grupos.py` (nuevo),
  `test_diseno_electrico_multisup.py`, `test_asistente_retrieval.py`,
  `test_publicacion_energia_multisuperficie.py`,
  `test_seleccion_poa_bypass_pagina5.py`, `test_panel_por_superficie.py`,
  `test_panel_proyecto_bypass_mppt.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/03-dimensionamiento/diseno-electrico-multisuperficie/`,
  `CodeSpecs/00-director/contratos-entre-modulos.md`,
  `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

### Fase A1

- Solo Streamlit (`pm2 restart streamlit-bipv`).
- Ninguna energía cambia. Un inversor que el usuario pase a «del proyecto» o
  «del catálogo» toma la P AC de la ficha, que es el límite de recorte del
  modo físico: es una elección explícita del usuario, no un cambio de
  fórmula.

### Fase A2

- Solo Streamlit (`pm2 restart streamlit-bipv`).
- La energía simplificada de una superficie con grupos de strings usa ahora
  el área instalada (módulos × área del módulo) en vez del área completa de
  la superficie: es menor cuando los módulos no cubren toda la superficie.
  Las energías publicadas antes deben volver a publicarse.
- Los proyectos guardados antes cargan cada superficie como un grupo G1.
