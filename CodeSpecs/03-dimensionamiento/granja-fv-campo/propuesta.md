# Propuesta — 🌾 Granja FV, fase 1: campo de filas coherente con el proyecto

**Estado:** validación

## Objetivo

Una página propia para el campo de una granja que use los datos del proyecto
(módulos, panel, inclinación, azimut, modelo bifacial) y diga con colores si
todo coincide, y que 🗺️ Vista 3D dibuje la granja con el mismo cálculo.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026 («si prepara la Spec de la fase 1 con
su PR. Con coherencia y cero errores»).

- `calculos/granja_fv.py` (nuevo, puro): `dimensiones_modulo` (de
  `dimensiones_mm` de la ficha; estimadas desde el área si faltan),
  `calcular_campo` (mesa, huella, GCR, ángulo límite, corredor, filas que
  caben, módulos ubicados, suelo libre, rectángulos de las mesas),
  `sugerir_distribucion`, `modulos_del_proyecto` (Producción, si no
  Dimensionamiento), `geometria_desde_estado` (inclinación y azimut de 🏠
  Proyecto; valores iniciales desde el modelo bifacial), `coherencia_campo`
  y `trazas_campo` (3D).
- Página `9b_🌾_Granja_FV.py`: terreno, mesas y filas (guardados con el
  proyecto en `granja_fv`), «🪄 Sugerir distribución», resultados,
  coherencia (🟢/🟡/🟠/🔴) y 3D.
- 🗺️ Vista 3D: para «Granja fotovoltaica» dibuja con `calcular_campo` y
  `trazas_campo` y remite a 🌾 Granja FV; se quita su cuenta propia de
  matrices.
- Manual del Asistente, sección 93, con la cuenta de Apartadó.

## Alternativas descartadas

- Copiar Vista 3D para granjas: dos cálculos que se separan con el tiempo
  (el mismo tipo de incoherencia que motivó esta Spec).
- Escribir el GCR y la altura del campo en el modelo bifacial desde ya:
  cambia la energía; es la fase 2 (sombra entre filas y bifacial por
  geometría). En la fase 1 se avisa con el valor exacto a poner.

## Fuera de alcance

- Sombra entre filas, luz al cultivo, seguidores y eléctrico por bloques
  (fases 2 a 5).
- Superficies BIPV de Vista 3D (siguen igual).
