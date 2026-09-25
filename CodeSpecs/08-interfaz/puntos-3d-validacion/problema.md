# Spec — Validación visible de los puntos 3D por superficie

**Estado:** completado

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): captura de puntos 3D por superficie
en la sección «🌳 Sombra 3D por superficie» de `pages/9_🗺️_Vista_3D.py`.
No cambia el ray-casting ni el formato de los puntos que recibe el motor.

## Problema a resolver

El texto de puntos se interpreta en la propia página (líneas 1121–1139):

1. Cada línea se divide por comas tras reemplazar `;` por `,`. Si no quedan
   exactamente 3 números, o alguno no es numérico, la línea **se descarta en
   silencio** (`except ValueError: pass`).
2. Con coma decimal, habitual en Colombia, `8,5;0;2` se convierte en
   `8,5,0,2`: cuatro valores y la línea desaparece sin aviso.
3. Los puntos dentro de un sólido o a menos de 10 cm de la malla solo se
   detectan al calcular (`validar_puntos` dentro de
   `calcular_fs_horario_por_superficie`), y el resultado queda en
   `error_geometrico` sin que el usuario lo vea (ver la Spec `estado-sombra-superficie`).
4. Los puntos se guardan por **nombre** de superficie
   (`multisup_puntos_por_superficie`); renombrar una superficie los
   desvincula.

## Contexto

- El manual documenta el riesgo como precaución de uso.
- Relacionada: la Spec `estado-sombra-superficie`; esta Spec va antes porque
  previene errores que C solo mostraría después.
