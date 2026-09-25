# Implementación — Panel por superficie en Vista 3D multi-superficie

**Estado:** validación

## Cambios realizados

- Nuevo `calculos/panel_superficie.py`:
  - `area_modulo(panel)`: `area_m2` o `largo_mm × ancho_mm`.
  - `eficiencia_panel(panel)`: Pmax_stc / (área × 1000); error si falta un
    dato o η no está en (0, 1).
  - `panel_de_superficie(sup, panel_dict, panel_nombre_dim)` →
    `{"panel", "nombre", "origen", "es_proyecto"}`.
  - `eficiencias_superficies(...)` y `eficiencias_superficies_estado(ss)` →
    `(etas, paneles, errores)` por nombre.
  - `firma_panel_superficie`, `firma_paneles_superficies` e
    `invalidar_por_cambio_panel(ss)` con la huella en
    `_multisup_firma_paneles`.
  - `seleccion_panel` y `opcion_panel_actual` para el editor.
- `multi_superficie.e_ac_total_multisup`: `eta_panel` acepta un mapa
  `nombre → η`; el desglose agrega `eta_panel`. Un número sigue funcionando
  para los llamadores existentes.
- `strings_superficie`: parámetro `panel_es_del_proyecto`; el área del
  módulo sale de `area_modulo`.
- `adaptador_multisuperficie`: `panel_dict` global solo se exige para las
  superficies que siguen al panel del proyecto.
- `persistencia_multisuperficie`: `_superficie_input` guarda `panel_origen`,
  `panel_nombre` y `panel_ficha`; la verificación de contexto compara el
  panel de cada superficie y el del proyecto solo si alguna lo sigue.
- `proyectos_manager`: `_multisup_firma_paneles` se reinicia al cargar.
- `pages/9_🗺️_Vista_3D.py`:
  - Editor: «Panel de esta superficie» (`spanel_{uid}`) con el panel del
    proyecto primero y el catálogo (Excel, o `MODULOS_BIPV` si no hay
    Excel); la ficha elegida pasa por `resolver_panel_calibrado`. Muestra
    Pmax, η y área del módulo.
  - Resumen POA, publicación simplificada, tabla del mes, Producción por
    superficie y bypass: η de cada panel; columnas «Panel» y «η (%)».
    Superficies sin panel utilizable: aviso y fuera de la energía; el botón
    de publicar queda deshabilitado.
  - Bypass y MPPT: sin selector común; panel, SDM y strings de cada
    superficie; bloqueo con nombre de la superficie si falta SDM o N serie.
  - Invalidación por cambio de panel después del editor, con aviso.
- `pages/4_📐_Dimensionamiento.py`: invalidación tras escribir `panel_dict`.

Desviaciones del diseño, con motivo:

- `firma_panel_superficie` no recibe solo `(sup, panel_dict)` sino también
  `panel_nombre_dim`, porque el nombre del panel del proyecto forma parte de
  lo que se muestra y se guarda.
- La huella de paneles se guarda aparte (`_multisup_firma_paneles`) en vez de
  dentro de la publicación, para cubrir también los resultados de bypass y
  MPPT, que no son publicaciones.
- `test_panel_proyecto_bypass_mppt.py`: dos pruebas de la Spec anterior se
  ajustaron. Una exigía el selector común de panel, retirado por esta Spec.
  La otra esperaba error sin `area_m2`, y ahora el área sale de largo × ancho.

## Auditoría posterior al merge (25-sep-2026)

Revisión del código ya integrado (#50), antes de la prueba en producción:

| # | Hallazgo | Severidad | Corrección |
|---|---|---|---|
| H1 | Agregar, eliminar o desactivar una superficie cambiaba la huella global y mostraba «Cambió el panel de una superficie…», retirando la energía publicada sin que ningún panel cambiara | Media | La huella se guarda por `uid` y solo se comparan las superficies que ya existían |
| H2 | Si `resolver_panel_calibrado` lanzaba `ValueError` (SDM manual que ya no reproduce la ficha), el editor se caía | Media | `seleccion_panel` convierte el error en `PanelSuperficieError`, que el editor muestra junto al selector |
| H3 | La comparación simplificado vs físico (`multisup_proyecto_fisico_candidato`) seguía mostrando el valor calculado con el panel anterior; adoptar sí recalculaba | Baja | Se retira junto con los demás resultados al cambiar un panel |
| H4 | Con una superficie fuera por panel inválido, el resumen decía «Producción total del sistema» | Baja | Dice «de las superficies con POA vigente y panel utilizable» |

Revisado sin hallazgos: adopción del físico (recalcula con el estado
actual), bypass y MPPT bloqueados si falta SDM o N serie, publicación
bloqueada si una superficie no tiene η, persistencia de fichas calibradas,
validación de inversores (no usa el panel), cambio del nombre del panel del
proyecto (el selector se resincroniza). Queda fuera, ya registrado: PR fijo
0,78.

## Archivos modificados

- `bipv_python/calculos/panel_superficie.py` (nuevo)
- `bipv_python/calculos/multi_superficie.py`
- `bipv_python/calculos/strings_superficie.py`
- `bipv_python/calculos/adaptador_multisuperficie.py`
- `bipv_python/calculos/persistencia_multisuperficie.py`
- `bipv_python/calculos/proyectos_manager.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`, `bipv_python/pages/4_📐_Dimensionamiento.py`
- `bipv_python/tests/test_panel_por_superficie.py` (nuevo),
  `test_panel_proyecto_bypass_mppt.py`, `test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `docs/MANUAL_VISTA_3D.md`, `entregables/MANUAL_VISTA_3D_BIPV.docx`
- `CodeSpecs/05-perdidas-y-temperatura/panel-por-superficie/`
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- Solo la app Streamlit (reinicio de `streamlit-bipv`).
- La energía multi-superficie publicada antes con origen `simplificado` o
  `bypass_csv` usó η = 16 %: hay que volver a publicarla.
- Sin cambios en fórmulas físicas del SDM, del bypass ni del MPPT.
