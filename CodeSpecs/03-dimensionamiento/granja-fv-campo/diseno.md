# Diseño — 🌾 Granja FV, fase 1: campo de filas coherente con el proyecto

**Estado:** validación

## Entradas

- Panel (`dimensiones_mm`, `area_m2`, `Pmax_stc`), `N_paneles_final`,
  `N_paneles_granja`, `tilt_fachada`, `azimuth_fachada`, `area_fachada_m2`,
  `factor_ocupacion_pct`, `bifacial_activo`, `bifacial_cfg` (`gcr`,
  `altura_m` = centro del panel), `multisup_activo`, `tipo_instalacion`.
- `granja_fv`: `ancho_terreno_m`, `largo_terreno_m`, `modulos_pendiente`,
  `orientacion`, `modulos_por_mesa`, `mesas_por_fila`, `pasillo_m`,
  `pitch_m`, `altura_libre_m`.

## Salidas

- `calcular_campo(geo, dims, n, pmax) -> dict`: `ancho_mesa_m`,
  `huella_ns_m`, `gcr`, `angulo_limite_deg`, `corredor_m`,
  `altura_superior_m`, `altura_centro_m`, `largo_fila_m`, `filas_caben`,
  `capacidad`, `modulos_colocados`, `faltan`, `filas_usadas`, `cabe`,
  `errores`, `kwp`, `area_modulos_m2`, `suelo_libre_pct`, `mesas`.
- `coherencia_campo(campo, estado) -> list[{id, nivel, texto}]` con ids
  `modulos`, `modulos_fuentes`, `gcr_bifacial`, `altura_bifacial`,
  `ocupacion`, `terreno`, `multisuperficie`, `tipo`.
- `sugerir_distribucion(n, dims, geo) -> dict | None`.
- `trazas_campo(campo, color) -> [Mesh3d suelo, Mesh3d mesas]`.

## Tipos de datos

`dict`, `list`, `float`, `int`, `plotly.graph_objects.Mesh3d`.

## Errores posibles

- Filas que se tocan (separación ≤ huella), fila más larga que el terreno o
  mesa más profunda que el terreno: 🔴 con qué cambiar.
- No caben todos los módulos: 🔴 con cuántos faltan.
- Ficha sin dimensiones: se estiman desde el área y se avisa.

## Dependencias

`calculos.campos_persistentes`, `calculos.campos_editor`, `plotly`.

## Criterios de aceptación

1. Apartadó (2 módulos horizontales, 10°, separación 6,60 m): ancho de mesa
   2,626 m, GCR 39,8 % (referencia 39,8–40,1 %), ángulo límite 6,5°
   (referencia 6,5°).
2. 5 filas de 31 × 2 alojan los 308 módulos (221,76 kWp) en 80 × 30 m.
3. Terreno chico, filas que se tocan o fila más larga que el terreno: 🔴.
4. «Sugerir distribución» deja todos los módulos dentro del terreno.
5. GCR o altura del modelo bifacial distintos del campo: 🟠 con el valor.
6. Producción y Dimensionamiento con distinto número de módulos: 🟠.
7. Energía multi-superficie publicada: 🟠.
8. 🗺️ Vista 3D dibuja la granja con el mismo cálculo (308, no 288).
9. La geometría se guarda con el proyecto; el manual lo explica.
