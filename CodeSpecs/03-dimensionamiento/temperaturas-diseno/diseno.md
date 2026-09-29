# Diseño — Temperaturas de diseño estables en 📐 Dimensionamiento

**Estado:** validación

## Entradas

- `T2m` del TMY de la sesión (`tmy_df`), NOCT del panel.
- Estado: las tres temperaturas y `dim_temps_tmy_firma`.

## Salidas

`calculos/temperatura.py`:

- `CLAVE_FIRMA_TEMPS_TMY = "dim_temps_tmy_firma"`.
- `temperaturas_diseno_desde_tmy(t2m, noct) -> dict` con las tres claves.
- `firma_temperaturas_tmy(t2m, noct) -> str`.
- `temperaturas_a_aplicar(estado, t2m, noct) -> dict | None`: las tres
  temperaturas y la firma si hay TMY y (la firma cambió, falta alguna o las
  tres están en 0); `None` en otro caso.

`pages/4_📐_Dimensionamiento.py`: aplica `temperaturas_a_aplicar`, luego
campos con `campo_persistente` (sin TMY, el valor por defecto es el de la
ciudad).

`pages/1_🏠_Proyecto.py`: «Guardar configuración» solo escribe las
temperaturas de la ciudad si no hay firma de TMY; el cambio de ciudad borra
la firma.

## Tipos de datos

`float` (°C), `str` (firma).

## Errores posibles

- TMY sin `T2m`: se usa la primera columna, como antes.
- Proyecto guardado antes del cambio (sin firma): al haber TMY se recalcula
  una vez.

## Dependencias

`calculos.campos_persistentes`.

## Criterios de aceptación

1. Mismo TMY y NOCT: no se recalcula (se respeta lo escrito por el usuario).
2. Otro TMY (otra versión de PVGIS u otras coordenadas) u otro NOCT: se
   recalcula.
3. Las tres en 0 o faltantes con TMY: se recalcula.
4. Al salir y volver a la página, los valores se mantienen.
5. «Guardar configuración» no pisa temperaturas del TMY.
6. Apartadó con PVGIS 5.3 y el JAM66D46-720/LB: 20.9 / 54.2 / 63.6 y N = 28
   sin riesgos.
7. El manual del Asistente explica de dónde salen y qué hacer.
