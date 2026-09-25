# Implementación — Panel y strings del proyecto en bypass y MPPT por superficie

**Estado:** completado

## Cambios realizados

- Nuevo `calculos/strings_superficie.py`:
  - `opciones_panel_superficie(panel_dict, panel_nombre, catalogo)`:
    primera opción «Panel del proyecto (nombre)» con `panel_dict` tal cual
    (esté o no en el catálogo) si `tiene_sdm_completo`; si no hay panel o no
    tiene SDM, retorna el aviso y solo el catálogo con SDM completo.
  - `es_panel_del_proyecto(opcion, panel_nombre)`.
  - `strings_superficie(superficie, n_serie_dim, panel)` →
    `{"n_serie", "n_paralelo", "origen", "aviso"}` con origen `superficie`,
    `dimensionamiento` (N serie de 📐 Dimensionamiento, paralelo por área) o
    `estimado_por_area` (N serie de la superficie, paralelo por área). Toda
    estimación trae aviso; sin N serie válido o sin área del panel para
    estimar, `ValueError`.
- `pages/9_🗺️_Vista_3D.py`:
  - Bypass por superficie: selector de panel con el del proyecto por
    defecto; sin panel utilizable el selector queda vacío y el botón
    deshabilitado. Cada superficie simula con sus strings. La tabla agrega
    «Panel usado», «Panel del proyecto», «N serie × paralelo» y «Origen
    strings» (se guardan en `bypass_multisup_resultados`).
  - MPPT combinado: mismo selector y mismos strings por superficie; el
    resultado guarda y muestra el panel usado, si es el del proyecto y los
    strings con su origen (`mppt_comb_panel`).

Desviaciones del diseño, con motivo:

- Se retiraron los campos «Módulos en serie» comunes de ambas secciones en
  lugar de conservarlos como sobrescritura: el N serie y el N paralelo se
  editan en un solo lugar (⚙️ Superficies BIPV), que es el que usa también el
  modo físico. Cambiar de panel sigue siendo posible y queda marcado.
- Los selectores usan claves nuevas (`ms_bp_panel_sel`,
  `ms_mppt_panel_sel`) para que una selección guardada con las claves
  anteriores no se imponga sobre el panel del proyecto.

## Archivos modificados

- `bipv_python/calculos/strings_superficie.py` (nuevo)
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_panel_proyecto_bypass_mppt.py` (nuevo)
- `bipv_python/datos/base_conocimiento_asistente.md`
- `docs/MANUAL_VISTA_3D.md`, `entregables/MANUAL_VISTA_3D_BIPV.docx`
- `CodeSpecs/08-interfaz/panel-proyecto-bypass-mppt/`
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- Solo la app Streamlit (reinicio de `streamlit-bipv`). No cambia
  `mismatch_bypass.py` ni `mppt_combinado.py`.
- Un bypass publicado antes con el panel por defecto del catálogo debe
  recalcularse para usar el panel y los strings del proyecto.
