# Diseño — Puntos automáticos por módulo

**Estado:** validación

## Entradas

- Superficie: tilt, azimut, grupos (gid, n_serie, n_paralelo).
- Usuario: esquina (m), filas, columnas, orientación, largo y ancho del
  módulo (m), separaciones, distancia a la superficie, cableado.

## Salidas

- Puntos: nombre, x, y, z, fila, columna, tilt, azimut, string, posición.
- `sombra_por_string`: {"G1-S1": {"fraccion": 8760, "profundidad": 8760}}.
- Unidad física: `sombra_strings` = lista ordenada de (fracción,
  profundidad).
- `simular_bypass_por_strings(...)`: mismo contrato que
  `simular_bypass_horario`, más `por_string`.

## Tipos de datos

Coordenadas `float` en metros; series `np.ndarray` de 8760 valores.

## Errores posibles

- Filas × columnas ≠ módulos de los grupos: `ValueError` con ambos números.
- Medidas fuera de 0,2–3,5 m: «van en metros».
- Distancia < 0,10 m, cableado desconocido, filas o columnas < 1.
- Strings guardados que no cuadran con el grupo: `ValueError` que pide
  regenerar y pulsar «🌳 Calcular sombra».
- Texto editado tras generar: sin etiquetas; sombra por superficie con aviso.

## Dependencias

`calculos/puntos_modulo.py`, `calculos/sombras_3d.py`,
`calculos/mismatch_bypass.py`, `calculos/adaptador_multisuperficie.py`,
`calculos/transicion_multisuperficie.py`,
`calculos/vinculador_sombra_multisuperficie.py`,
`calculos/persistencia_multisuperficie.py`, `calculos/guia_vista_3d.py`,
`pages/9_🗺️_Vista_3D.py`.

## Criterios de aceptación

1. Fachada sur: centros 0,523 / 1,589 / 2,655 m, y = −0,30, z = 0,845.
2. n, u, v ortonormales; todos los puntos a la distancia pedida del plano
   para tilt 0°, 10°, 30° y 90° y azimuts 162°, 180° y 249°.
3. Strings por columnas y por filas, varios grupos, posiciones 1..n.
4. Cinco validaciones estrictas con mensajes claros.
5. Texto al milímetro; etiquetado solo con el texto generado.
6. Bypass por strings: strings idénticos = resultado por superficie; un string
   a media luz de dos → 25 %.
7. Modo físico: un string de dos a media luz → energía × 0,75 (±3 %).
8. La página genera 14 puntos en 2 strings y rechaza 21 módulos.
9. Guía y manual (secciones 125 y 126) sin nombres comerciales de otras
   apps.
