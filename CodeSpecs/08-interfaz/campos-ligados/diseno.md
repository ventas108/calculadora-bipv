# Diseño — Campos ligados a su dato en Dimensionamiento, Mismatch y Producción

**Estado:** validación

## Entradas

- Datos `N_str_tr`, `bypass_n_series`, `bypass_n_parallel`,
  `bypass_panel`, `produccion_usar_iv` y sus valores por defecto de cada
  página.

## Salidas

- Widgets `_w_<clave>` sincronizados y el dato actualizado en cada
  ejecución con lo que escribe el usuario.

## Tipos de datos

`int`, `str`, `bool`.

## Errores posibles

- Dato fuera de rango: se recorta. Opción inexistente: valor por defecto.

## Dependencias

`calculos/campos_editor.sincronizar_campo`; lectores de las claves:
`calculos/dimensionamiento.py`, `calculos/escenarios_fase4.py`,
`calculos/produccion_vigencia.py`.

## Criterios de aceptación

1. Los valores sobreviven al cambio de página (antes: 1, valor por defecto,
   apagado).
2. Un cambio del dato desde fuera (cargar proyecto, recálculo) actualiza el
   campo y luego se puede editar.
3. Rango y opciones se respetan.
4. Ninguna de las tres páginas usa la clave del dato como widget.
5. Ninguna página usa como widget un dato que lee otro módulo.
6. El manual del Asistente lo explica (sección 100).
