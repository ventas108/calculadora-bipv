# Diseño — Panel por superficie en Vista 3D multi-superficie

**Estado:** diseño

## Entradas

- Por superficie: `panel_origen` (`"proyecto"` o `"catalogo"`), y si es
  catálogo, `panel_nombre` y `panel_ficha` (copia del dict elegido, para que
  el proyecto guardado no dependa de cambios del catálogo).
- `panel_dict` y `panel_nombre_dim` (📐 Dimensionamiento o 🧩 Comparador).
- Catálogo `MODULOS_BIPV`.
- `N_serie` de Dimensionamiento.

## Salidas

- Nuevo módulo puro `calculos/panel_superficie.py`:
  - `panel_de_superficie(sup, panel_dict, panel_nombre_dim) ->
    {"panel", "nombre", "origen", "es_proyecto"}`;
  - `eficiencia_panel(panel) -> float` (η en fracción, 0 < η < 1);
  - `opciones_panel_editor(panel_dict, panel_nombre_dim, catalogo)`;
  - `firma_panel_superficie(sup, panel_dict) -> str`.
- Energía simplificada por superficie con su η: resumen POA, Integrar,
  Producción por superficie y bypass. Columnas nuevas «Panel» y «η».
- `e_ac_total_multisup` y `produccion_superficie` reciben η por superficie
  (mapa `nombre → η`), sin valor por defecto 0,16 en la página.
- Bypass y MPPT: panel por superficie; `bypass_multisup_resultados` y
  `mppt_comb_panel` guardan el panel de cada superficie.
- Modo físico: `superficie_nueva(..., panel_de_superficie(...)["panel"], ...)`.
  `panel_dict` global solo es obligatorio si alguna superficie usa
  «Panel del proyecto».
- Persistencia: `_superficie_input` incluye `panel_origen`, `panel_nombre` y
  `panel_ficha`; `electrical.panel` se conserva. Sin cambio de
  `SCHEMA_VERSION`: los campos son opcionales y su ausencia significa
  «proyecto».

## Tipos de datos

- `panel_origen`: `str` del conjunto cerrado `{"proyecto", "catalogo"}`.
- `panel_ficha`: `dict` con el contrato de `MODULOS_BIPV`.
- η: `float`, calculado con `Pmax_stc` y `area_m2`; si falta `area_m2`, con
  `largo_mm × ancho_mm / 1e6`.

## Errores posibles

- Panel sin `Pmax_stc` o sin área, o η fuera de (0, 1): la superficie queda
  fuera de la energía simplificada con el aviso «el panel X no trae potencia
  o área: no se puede calcular su eficiencia». Nunca se usa 16 %.
- Superficie con «Panel del proyecto» y sin `panel_dict`: aviso «ejecuta 📐
  Dimensionamiento o elige un panel del catálogo».
- Bypass, MPPT o físico con un panel sin SDM completo: la superficie se
  lista y el cálculo se bloquea (misma regla que la Spec
  `panel-proyecto-bypass-mppt`, ahora por superficie).
- Panel distinto al del proyecto sin N serie en la superficie: `ValueError`
  con el nombre de la superficie; no se usa el N serie de Dimensionamiento.
- `panel_origen` desconocido al cargar un proyecto: se rechaza el payload
  con mensaje, no se adivina.

## Invalidación

- Cambiar `panel_origen`/`panel_nombre` de una superficie, o el
  `panel_dict` del proyecto cuando alguna superficie lo sigue, retira la
  energía publicada (`retirar_energia_multisuperficie`), los resultados de
  bypass y MPPT y `_multisup_proyecto_fisico`.
- No cambia `firma_poa` ni `firma_sombra`.

## Dependencias

- Módulos previos: `03-dimensionamiento` (`panel_dict`, `N_serie`),
  `08-interfaz/panel-proyecto-bypass-mppt`,
  `05/publicacion-energia-multisuperficie`,
  `05/persistencia-multisuperficie`.
- Capas: cálculo (`multi_superficie.py`, `strings_superficie.py`, módulo
  nuevo), estado (`superficies_bipv`, invalidación), interfaz (Vista 3D),
  persistencia, Asistente y manual.

## Criterios de aceptación

- Con el panel del proyecto `ASP-ST1-T40`, la fachada de 97,3 m² con POA
  1004 kWh/m² y PR 0,78 da 6.667 kWh/año (η 8,75 %), no 12.191.
- Fachada con `ASP-ST1-T40` y techo con otro panel del catálogo: cada una
  usa su η, su área de módulo y su SDM en simplificado, bypass, MPPT y
  físico; la tabla muestra el panel de cada una.
- Ninguna lectura de `eta_panel` con valor por defecto queda en la página.
- Cambiar el panel del techo retira la energía publicada y deja la POA
  vigente.
- Guardar y cargar conserva el panel de cada superficie; un proyecto
  guardado antes del cambio carga con «Panel del proyecto».

## Pruebas requeridas

- `eficiencia_panel`: `ASP-ST1-T40` = 0,0875; área por `largo_mm ×
  ancho_mm`; sin potencia o sin área → error.
- `panel_de_superficie`: proyecto, catálogo, sin `panel_dict`, origen
  inválido.
- Energía simplificada con dos paneles distintos: desglose por superficie
  y total = suma.
- Strings: área de módulo de cada superficie; panel distinto sin N serie →
  error.
- Modo físico: cada superficie recibe su panel; la huella `panel` de
  `transicion_multisuperficie` cambia solo en la superficie editada.
- Invalidación: cambio de panel retira publicación y resultados, conserva
  `firma_poa` y `firma_sombra`.
- Persistencia: ida y vuelta con dos paneles; payload antiguo sin campos.
- Página (AST): sin `get("eta_panel", 0.16)`; sin selector común
  `ms_bp_panel_sel`/`ms_mppt_panel_sel`.
- Regresión: suites de bypass, MPPT combinado, publicación, persistencia y
  vigencia POA.
