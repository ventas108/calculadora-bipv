# Implementación — Publicación única de la energía multi-superficie

**Estado:** validación

## Cambios realizados

- Nuevo módulo `calculos/publicacion_multisuperficie.py`:
  - Orígenes `simplificado`, `bypass_csv` y `fisico` (conjunto cerrado) y
    `desconocido` para sesiones anteriores; etiquetas legibles
    (`ETIQUETA_ORIGEN`).
  - `preparar_publicacion` valida sin escribir: total finito y no negativo,
    desglose no vacío con nombres únicos y valores finitos, suma de áreas =
    área total (±0,1 m²), POA ponderada de 8760 h con valores finitos. En
    `simplificado` y `bypass_csv` la suma del desglose = total (±0,1 kWh) y
    no admite proyecto físico. En `fisico` exige el proyecto y publica
    `multisup_perdida_bus_kWh` = suma del desglose − total de buses.
  - `publicar_energia_multisuperficie` escribe todas las claves juntas con
    `multisup_origen`; si la energía vigente es de otro origen y no se
    confirmó el reemplazo, no escribe y retorna `requiere_confirmacion`. Un
    origen no físico retira `_multisup_proyecto_fisico` y la pérdida de bus.
  - `retirar_energia_multisuperficie` (botón «✖ Desactivar») y
    `resultados_multisuperficie_a_guardar`, que solo incluye el proyecto
    físico si el origen vigente es `fisico`.
- `calculos/adaptador_multisuperficie.py`: `aplicar_proyecto_a_session_state`
  arma el desglose como antes y delega en la publicación con origen
  `fisico`. Nuevo parámetro `confirmar_reemplazo` (por defecto `True`, que
  conserva el contrato de los llamadores existentes); retorna el resultado
  de la publicación.
- `calculos/invalidacion.py`: `multisup_origen`, `multisup_perdida_bus_kWh` y
  `_multisup_proyecto_fisico` en `KEYS_DERIVADOS_POA` (al final, sin mover
  `perdida_ohmica_unifilar`) y en `KEYS_MULTISUP_ESTADO`.
- `calculos/proyectos_manager.py`: claves nuevas excluidas del estado plano
  y reiniciadas al cargar; el guardado usa
  `resultados_multisuperficie_a_guardar`.
- `calculos/persistencia_multisuperficie.py`: restaura `multisup_origen` y
  `multisup_perdida_bus_kWh`; un payload con proyecto físico restaura origen
  `fisico` (proyectos guardados antes de esta Spec); un payload con origen
  `fisico` sin proyecto se rechaza.
- `pages/9_🗺️_Vista_3D.py`: «🔗 Usar sistema multi-superficie», «⚡ Calcular
  bypass por superficie» y «✅ Adoptar cálculo físico» publican solo por la
  función central. Si hay energía de otro origen aparece «¿Reemplazarla
  por…?» con «✅ Sí, reemplazar» / «✖ Cancelar»; al confirmar, la página
  vuelve a calcular con los datos actuales (el físico se revalida con
  `construir_y_recalcular_proyecto_fisico`). El bypass publica total,
  desglose, área y POA ponderada del mismo cálculo y solo si todas las
  superficies se simularon; su tabla dice «Activo en Financiero» solo con
  origen `bypass_csv`. El banner muestra el origen, la pérdida de bus en
  origen físico y un aviso para origen desconocido.

Ajuste posterior por uso en producción (24-sep-2026): la sección del bypass
muestra el origen vigente en su mensaje «✅ Activo en Financiero» y trae su
propio «✖ Desactivar modo multi-superficie» (misma
`retirar_energia_multisuperficie`), porque el banner del origen está en otra
sub-pestaña y el usuario no lo encontraba desde el bypass.

Desviaciones del diseño, con motivo:

- Origen desconocido: la página pide volver a publicar antes de guardar,
  pero no bloquea el guardado; el proyecto físico de una sesión sin origen
  no se guarda, así que un guardado nunca combina proyecto físico con
  energía de otro origen.
- La solicitud de confirmación guarda solo el origen; al confirmar se
  recalcula en vez de publicar datos de un rerun anterior (mismo criterio
  que la adopción física).
- Pruebas existentes actualizadas por el nuevo contrato: el guardado físico
  de `test_persistencia_multisuperficie.py` declara `multisup_origen`; el
  estado de `test_seleccion_poa_bypass_pagina5.py` incluye las claves nuevas;
  la prueba del Asistente «tres botones, gana el último» se reemplazó por
  «un solo origen, con confirmación».

## Archivos modificados

- `bipv_python/calculos/publicacion_multisuperficie.py` (nuevo)
- `bipv_python/calculos/adaptador_multisuperficie.py`
- `bipv_python/calculos/invalidacion.py`
- `bipv_python/calculos/proyectos_manager.py`
- `bipv_python/calculos/persistencia_multisuperficie.py`
- `bipv_python/pages/9_🗺️_Vista_3D.py`
- `bipv_python/tests/test_publicacion_energia_multisuperficie.py` (nuevo)
- `bipv_python/tests/test_persistencia_multisuperficie.py`
- `bipv_python/tests/test_seleccion_poa_bypass_pagina5.py`
- `bipv_python/tests/test_asistente_retrieval.py`
- `bipv_python/datos/base_conocimiento_asistente.md`
- `docs/MANUAL_VISTA_3D.md`, `entregables/MANUAL_VISTA_3D_BIPV.docx`
- `CodeSpecs/05-perdidas-y-temperatura/publicacion-energia-multisuperficie/`
- `CodeSpecs/00-director/registro-de-decisiones.md`

## Impacto en despliegue

- Solo la app Streamlit (`/var/www/bipv/calculadora-bipv`, reinicio de
  `streamlit-bipv`).
- Financiero, Baterías, CO₂, Reporte y Unifilar leen las mismas claves; no
  cambian.
- Proyectos guardados con proyecto físico se restauran con origen `fisico`;
  los demás proyectos guardados muestran «origen desconocido» hasta volver a
  publicar.
