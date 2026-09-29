# Propuesta — Temperaturas de diseño estables en 📐 Dimensionamiento

**Estado:** validación

## Objetivo

Que las temperaturas de diseño salgan siempre del TMY vigente cuando existe,
que sobrevivan al cambio de página y al guardado, y que nunca queden en 0.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («verifica y soluciona el problema»).

- Los tres campos usan `campo_persistente`: el dato vive en su clave de
  siempre y el campo en una clave temporal `_w_…`.
- Firma del TMY (mínima, P95 y máxima de T2m, horas y NOCT del panel) en la
  clave `dim_temps_tmy_firma`, que se guarda con el proyecto. Si el TMY o el
  NOCT cambian, las temperaturas se recalculan; si no, se respeta lo que el
  usuario escribió.
- «💾 Guardar configuración» ya no pisa temperaturas calculadas desde un
  TMY; cambiar de ciudad borra la firma.
- Sin TMY y sin datos (o con las tres en 0): valores de la ciudad, nunca 0.
- Manual del Asistente con el caso Apartadó.

## Fuera de alcance

- La fórmula de las temperaturas (mínima del TMY; P95 + (NOCT − 20)/800 × 800;
  máxima + (NOCT − 20)/800 × 1000) no cambia.
