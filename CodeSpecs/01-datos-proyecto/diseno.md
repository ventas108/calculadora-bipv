# Diseño — Datos del proyecto

**Estado:** completado

## Entradas

- `nombre_proyecto` (texto, identificación del proyecto).
- `ciudad` (selección de `LISTA_CIUDADES`, define coordenadas y clima de referencia).
- `lat_proyecto`, `lon_proyecto`, `alt_proyecto` (opcional, coordenadas exactas del
  predio; por defecto las del centro de la ciudad).
- `tipo_instalacion` (selección de `TIPOS_INSTALACION`: Fachada BIPV, Techo inclinado,
  Techo plano, Pérgola, Marquesina, Granja fotovoltaica).
- `area_fachada_m2` (número, 10–500 000 m²).
- `factor_ocupacion_pct` (número, 5–100%; solo relevante <100% en Granja fotovoltaica).
- `densidad_Wm2` (número, 30–300 W/m²; se autocompleta desde `panel_dict` si hay panel
  activo seleccionado).
- `PR` (número, 0.40–0.98).
- `tarifa_cop_kwh` (número, 100–2000 COP/kWh; ver regla de precedencia abajo).
- Modo "consumo": `consumo_kwh_mes` o `factura_cop`, y `cobertura_pct` (10–100%).

## Salidas

- `area_util_m2` = `area_fachada_m2 * factor_ocupacion_pct / 100`.
- `energia_anual_estimada` (kWh/año, modo área) o `area_nec` (m², modo consumo).
- `tarifa_cop_kwh`, `tarifa_fuente`, `tarifa_ciudad_origen`, `tarifa_operador`
  (estado global consumido también por `06-analisis-financiero`).
- Coordenadas activas del sitio (`lat_proyecto`, `lon_proyecto`, `alt_proyecto`),
  consumidas por `02-recurso-solar` para la descarga TMY/PVGIS.
- `PR`, `densidad_Wm2`, `tilt_default` — consumidos por `03-dimensionamiento`.

## Unidades

- Área: m². Potencia/densidad: W/m². Energía: kWh. Tarifa: COP/kWh. Coordenadas:
  grados decimales (lat -5..15, lon -82..-66). Altitud: m.s.n.m.

## Tipos de datos

- Todos los campos numéricos son `float` (Python) validados con `min_value`/`max_value`
  en los widgets de Streamlit; no hay validación adicional server-side porque la app
  corre en un único proceso Streamlit con estado en `session_state`.

## Errores posibles

- Tarifa fuera de rango razonable (`<300`, `<500` o `>1800` COP/kWh): se advierte pero
  no se bloquea el guardado.
- PR o densidad fuera del rango recomendado para el `tipo_instalacion`: advertencia,
  no bloqueo.
- Cambio de ciudad con una tarifa corregida manualmente: **hoy se sobreescribe sin
  aviso** (defecto documentado en `problema.md`; la corrección propuesta agrega el
  aviso en vez de sobreescribir).
- JSON de proyecto guardado corrupto o con `factor_ocupacion_pct` fuera de [5, 100]:
  se recorta defensivamente (`min(max(...))`) al cargar.

## Dependencias

- Módulos previos: (ninguno, es el módulo inicial)
- Módulos dependientes: `02-recurso-solar`, `03-dimensionamiento`, `06-analisis-financiero`

## Criterios de aceptación

- Cambiar de ciudad invalida las claves de recurso solar/producción ya calculadas
  (comportamiento actual, se mantiene).
- Cambiar de ciudad **no** sobreescribe una tarifa con `tarifa_fuente` manual
  (`"Proyecto"` o `"Financiero"`) sin mostrar antes un aviso explícito.
- Cambiar `tipo_instalacion` resetea `densidad_Wm2`, `PR` y `tilt_default` a los
  defaults del nuevo tipo (comportamiento actual, se mantiene), salvo
  `factor_ocupacion_pct`, que solo se resetea a 100% si el tipo nuevo no es
  "Granja fotovoltaica" (comportamiento actual, se mantiene).

## Pruebas requeridas

- Test que simule: tarifa con `tarifa_fuente = "Proyecto"`, luego cambio de ciudad →
  debe conservar el valor manual y mostrar aviso, no sobreescribir.
- Test que confirme que `tarifa_fuente = "catálogo"` sí se actualiza al cambiar de
  ciudad (comportamiento sin cambios para el caso no editado manualmente).
- Test de rango: `factor_ocupacion_pct` cargado fuera de [5, 100] se recorta al cargar
  un proyecto guardado.
