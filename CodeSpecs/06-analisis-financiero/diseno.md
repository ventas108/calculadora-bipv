# Diseño — Análisis financiero

**Estado:** completado

## Entradas

- Archivo de persistencia por usuario (`datos/persistencia/*_resultados_produccion.json`),
  con `resultados` (incluye `produccion_run_signature_v1`) y `huella` (ciudad/coordenadas).
- Payload canónico (pre-hash) que Producción ya construye en
  `calcular_produccion_run_signature_v1()` — nuevo campo persistido, sin arrays.
- `session_state` actual de Finanzas/Presupuesto: solo `ciudad`, `lat_proyecto`,
  `lon_proyecto`, `auth_email` — nunca panel/inversor/TMY/POA en pestaña nueva.

## Salidas

- Resultados de Producción restaurados en `session_state` de Finanzas/Presupuesto
  únicamente cuando el payload persistido es consistente con la firma persistida.
- Ningún cambio en el contrato de `04-produccion-energia`: Producción sigue
  siendo la única fuente que calcula y guarda la firma original.

## Unidades

- Sin unidades físicas propias; opera sobre huellas SHA-256 (cadenas hex) y el
  payload JSON canónico ya definido en `04-produccion-energia`.

## Tipos de datos

- Payload persistido: `dict` serializable en JSON (mismos tipos que
  `_normalizar_valor()` en `calculos/produccion_vigencia.py`).
- Firma: cadena hex de 64 caracteres.

## Errores posibles

- Payload ausente en un archivo persistido antiguo (legacy, previo a este
  cambio): se rechaza la restauración, igual que hoy sin firma.
- Payload presente pero su SHA-256 no coincide con la firma persistida
  (corrupción o edición manual del JSON): se rechaza la restauración.
- Huella de ciudad/coordenadas no coincide con el proyecto activo: se
  rechaza antes de mirar la firma (regla ya existente, sin cambios).

## Dependencias

- Módulos previos: `01-datos-proyecto`, `04-produccion-energia`, `05-perdidas-y-temperatura`
- Módulos dependientes: `07-informes`

## Criterios de aceptación

- Producción persiste el payload canónico junto a `produccion_run_signature_v1`
  al guardar resultados (`guardar_resultados_produccion()`), sin cambiar la
  firma en sí ni su cálculo.
- `restaurar_resultados_produccion()` exige que `sha256(payload_persistido) ==
  firma_persistida` antes de restaurar cualquier agregado — reutilizando las
  funciones puras de `calculos/produccion_vigencia.py`, sin reimplementar la
  serialización canónica en `persistencia_resultados.py`.
- Finanzas y Presupuesto no necesitan cargar panel/inversor/TMY/POA para que
  la restauración funcione — el diseño no depende de estado en vivo.
- Legacy sin payload sigue rechazado, igual que hoy sin firma.

## Pruebas requeridas

- Guardar y restaurar con payload consistente: restaura correctamente.
- Payload ausente (legacy): no restaura.
- Payload presente pero alterado/inconsistente con la firma: no restaura.
- Huella de ciudad/coordenadas distinta: no restaura, sin llegar a evaluar el payload.

