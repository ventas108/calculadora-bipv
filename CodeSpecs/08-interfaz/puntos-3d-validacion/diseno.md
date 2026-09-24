# Diseño — Validación visible de los puntos 3D por superficie

**Estado:** validación

## Entradas

- Texto multilínea por superficie activa.
- Malla cargada (`multisup_malla_sombra`) o `None`.
- `uid` y nombre de la superficie.

## Salidas

- `parsear_puntos_3d` → `(puntos: list[dict], errores: list[dict])`;
  cada punto `{"nombre", "fachada", "x", "y", "z"}` (mismo contrato actual del
  motor); cada error `{"linea": int, "texto": str, "motivo": str}`.
- `st.session_state["multisup_puntos_por_superficie"]`: indexado por `uid`.
- Vista previa: lista de avisos de `validar_puntos` por punto.

## Tipos de datos

- Coordenadas `float` finitas, en metros (X = Este, Y = Norte, Z = altura).
- Reglas de separador:
  - con `;` → separador de campos `;`, y la coma dentro de cada campo es
    decimal;
  - sin `;` → separador `,` y decimal `.`;
  - mezcla que no dé exactamente 3 números → error con motivo explícito.

## Errores posibles

- Línea vacía o solo espacios: se ignora (no es error).
- Valor no numérico, `nan`/`inf`, o distinto de 3 campos: error de línea.
- Sesiones antiguas indexadas por nombre: se migran una vez al `uid` de la
  superficie con ese nombre; si no existe, se descartan con aviso.

## Dependencias

- Módulos previos: `05/sombra-cara-trasera` (`validar_puntos`,
  contrato de puntos).
- Módulos dependientes: la Spec `estado-sombra-superficie`.
- Capas: cálculo (parser nuevo en `calculos/`), estado (`session_state`),
  interfaz (Vista 3D).

## Criterios de aceptación

- `8,0,2`, `8.5,0,2`, `8;0;2` y `8,5;0;2` se interpretan correctamente.
- `8,5,0,2`, `8,0` y `8,a,2` producen error visible con su número de línea.
- Con errores, el botón de sombra queda deshabilitado con el motivo.
- Con malla cargada, un punto dentro del volumen o a menos de 10 cm se marca
  antes de calcular.
- Renombrar una superficie conserva sus puntos.

## Pruebas requeridas

- Tabla de casos del parser (válidos, ambiguos, incompletos, no numéricos,
  líneas vacías).
- Vista previa: punto dentro, punto a 5 cm, punto a 30 cm.
- Migración de puntos indexados por nombre.
- Prueba de página: el botón depende de la ausencia de errores (AST).
- Regresión: 10 suites de cierre multi-superficie.
