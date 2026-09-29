# Implementación — Elegir la versión de PVGIS (5.2 o 5.3) en ☀️ Recurso Solar

**Estado:** validación

## Cambios realizados

- `calculos/solar.py`: URLs por versión, versión por defecto (5.3) y de
  proyectos guardados (5.2), sufijo de caché, metadatos (`metadatos_pvgis`,
  `texto_meses_tmy`) y parámetro `version` en `obtener_tmy_pvgis`.
- `pages/2_☀️_Recurso_Solar.py`: selector «🛰️ Versión de PVGIS», caché de
  disco y de memoria por versión, invalidación al cambiar la versión, versión
  en los mensajes y recuadro «🛰️ Qué descargó PVGIS».
- `calculos/proyectos_manager.py`: `cargar_proyecto` fija `pvgis_version`.
- `pages/1_🏠_Proyecto.py`: el cambio de ciudad borra `_solar_pvgis_guardada`.
- Manual del Asistente, sección 79.

## Archivos modificados

- `bipv_python/calculos/solar.py`
- `bipv_python/pages/2_☀️_Recurso_Solar.py`
- `bipv_python/calculos/proyectos_manager.py`
- `bipv_python/pages/1_🏠_Proyecto.py`
- `bipv_python/tests/test_pvgis_version.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/00-director/contratos-entre-modulos.md`
- `CodeSpecs/00-director/registro-de-decisiones.md`
