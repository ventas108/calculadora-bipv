# Diseño — Estado de sombra visible por superficie

**Estado:** completado

## Entradas

- `st.session_state["superficies_bipv"]` (activas).
- TMY vigente (`tmy_df` con `T2m`) o `None`.
- `VERSION_ALGORITMO_FS_POR_SUPERFICIE`.

## Salidas

- `diagnostico_sombra_superficies(...)` → `list[dict]` con:
  `nombre`, `estado` (uno de: `calculado_completo`, `sombra_cero_calculada`,
  `calculo_incompleto`, `error_geometrico`, `sin_calcular`,
  `invalidada_tmy`, `invalidada_version`, `invalidada_geometria`),
  `utilizable` (`bool`), `motivo` (`str`), `horas_con_sol_calculadas`,
  `calidad`, `n_puntos`, `accion` (`str`).
- Tabla en la página con semáforo: 🟢 utilizable, 🔴 no utilizable,
  ⚪ sin calcular.

## Tipos de datos

- Estados: constantes del motor (`sombras_3d.ESTADO_*`) más las cuatro nuevas
  de diagnóstico, definidas una sola vez en el vinculador.
- `motivo` y `accion`: texto en español, sin jerga interna (`p_shade` se
  explica como «sombra horaria»).

## Errores posibles

- TMY ausente: las sombras calculadas se reportan como
  `invalidada_tmy` con acción «calcula ☀️ Recurso Solar».
- Superficie con `sombra_invalidada_motivo` y sin sombra:
  `invalidada_geometria` citando el campo cambiado.
- La función no debe mutar `session_state` (de solo lectura).
- Otro estado del motor no listado (por ejemplo `resolucion_insuficiente`,
  que esta página no produce hoy) se muestra tal cual como no utilizable.

## Dependencias

- Módulos previos: `05/sombra-cara-trasera` (versión v2),
  `05/transicion-multisuperficie`, la Spec `puntos-3d-validacion`.
- Módulos dependientes: ninguno; solo presentación y diagnóstico.
- Capas: estado (vinculador), interfaz (Vista 3D).

## Criterios de aceptación

- Tras calcular la sombra, cada superficie activa aparece en la tabla con su
  estado y motivo.
- Un punto dentro de la malla muestra `error_geometrico` con el aviso del
  punto concreto.
- Una sombra v1 o de otro TMY aparece como invalidada con su motivo, antes de
  entrar al modo físico.
- Cambiar tilt/azimuth/área muestra `invalidada_geometria` con el campo.
- El diagnóstico de sombra coincide con lo que el modo físico acepta o
  rechaza por motivos de sombra.

## Pruebas requeridas

- Diagnóstico para cada uno de los ocho estados.
- Coherencia: `utilizable=True` si y solo si la sombra de la superficie pasa
  las mismas validaciones de sombra que el modo físico (`p_shade` de 8760
  valores en [0, 1], `firma_sombra` con TMY y versión vigentes), sin
  considerar la configuración eléctrica.
- `advertencias_sombra` se conserva en estados no aceptables.
- Función de solo lectura (el estado de entrada no cambia).
- Prueba de página: la tabla se construye desde el diagnóstico.
