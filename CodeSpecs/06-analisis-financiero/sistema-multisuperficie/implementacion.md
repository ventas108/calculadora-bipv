# Implementación — Financiero, Baterías y CO₂ con el sistema multi-superficie publicado

**Estado:** implementación

## Cambios realizados

- Nuevo `calculos/sistema_multisuperficie.py` (puro):
  - `resumen_sistema_multisuperficie`: potencia DC STC (Σ módulos × Pmax del
    panel de cada superficie), módulos y potencia por referencia de panel con
    su `costo_usd` del catálogo, `completo` y superficies sin grupos, y reparto
    mensual de la energía de cada superficie según su POA mensual.
  - `validar_sistema` (el reparto suma la energía del desglose ± 0,5 kWh),
    `sistema_desde_estado`, `estado_sistema_publicado` (problemas en palabras
    sencillas) y `df_mensual_multisuperficie` (formato de 📊 Producción).
- `calculos/publicacion_multisuperficie.py`: parámetro `sistema` y clave
  `multisup_sistema` en la publicación todo o nada, en el guardado y en la
  limpieza de publicaciones que no la traen.
- Publicadores: simplificado y bypass (Vista 3D) y físico
  (`adaptador_multisuperficie`, con la POA de las unidades de cada superficie).
- Registros: `invalidacion.py`, `proyectos_manager.py` (exclusión y cambio de
  proyecto) y `persistencia_multisuperficie.py` (restauración).
- 💰 Financiero: con el modo multi-superficie activo no exige 📊 Producción;
  energía, kWp y módulos del sistema publicado; tabla por panel en el
  desglose; costo por referencia de panel en el CAPEX manual (promedio
  ponderado); 🔴 y `st.stop()` si el sistema está incompleto o la publicación
  es anterior; Presupuesto desvinculado por defecto con aviso 🟡.
- 🔋 Baterías: balance mensual con el reparto mensual publicado; balance
  horario deshabilitado con aviso; 🔴 si el sistema no se puede usar.
- 🌿 CO₂: kWp y módulos del sistema publicado.
- 💼 Presupuesto: aviso 🟡 de que se arma con el sistema de superficie única.
- Aviso fijo de energía retirada (pedido en la prueba D6):
  `registrar_motivo_retiro` y `aviso_energia_retirada` en
  `publicacion_multisuperficie.py`. `invalidar_por_cambio_electrico` e
  `invalidar_por_cambio_panel` registran el motivo y las superficies que
  cambiaron solo si había energía publicada; publicar, retirar a mano y
  cambiar de proyecto lo borran. Vista 3D lo muestra en «🔗 Integrar al
  análisis financiero».
- Base de conocimiento del Asistente, contratos del director y registro de
  decisiones.

Desviaciones del diseño, con motivo:

- **Las páginas se prueban por el código fuente**, como el resto de pruebas de
  consumidores del repositorio: Financiero consulta la TRM en línea y una
  prueba con `AppTest` dependería de la red. La prueba de humo con `AppTest`
  se hizo en local.
- **El reparto mensual de bypass y físico** usa la forma de la POA de cada
  superficie (la energía anual sí es la del modelo); se declara en
  `reparto_mensual: "poa_superficie"`.

## Archivos modificados

- `bipv_python/calculos/sistema_multisuperficie.py` (nuevo)
- `bipv_python/calculos/`: `publicacion_multisuperficie.py`,
  `adaptador_multisuperficie.py`, `invalidacion.py`, `proyectos_manager.py`,
  `persistencia_multisuperficie.py`
- `bipv_python/pages/`: Vista 3D, Financiero, Presupuesto, Baterías y Balance,
  Impacto CO₂
- `bipv_python/tests/test_sistema_multisuperficie.py` (nuevo),
  `test_diseno_electrico_fisico_grupos.py`,
  `test_publicacion_energia_multisuperficie.py`,
  `test_seleccion_poa_bypass_pagina5.py`, `test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `CodeSpecs/06-analisis-financiero/sistema-multisuperficie/`,
  `CodeSpecs/00-director/contratos-entre-modulos.md`,
  `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- Solo Streamlit (`pm2 restart streamlit-bipv`).
- Una energía multi-superficie publicada antes de esta versión no trae
  `multisup_sistema`: Financiero lo dice en 🔴 y pide volver a publicarla.
- Con el modo multi-superficie activo, el CAPEX, el OPEX y el umbral de la
  Ley 1715 pasan a calcularse con los kWp y módulos del sistema multi-superficie.
