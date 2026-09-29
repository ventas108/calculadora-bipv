# Diseño — Elegir la versión de PVGIS (5.2 o 5.3) en ☀️ Recurso Solar

**Estado:** validación

## Entradas

- `version` (`"5.2"` o `"5.3"`) del selector de ☀️ Recurso Solar, guardada
  en `st.session_state["pvgis_version"]`.
- JSON de PVGIS: `outputs.tmy_hourly`, `outputs.months_selected`,
  `inputs.meteo_data` (`radiation_db`, `meteo_db`, `year_min`, `year_max`).

## Salidas

`calculos/solar.py`:

- `PVGIS_URLS_TMY`, `PVGIS_VERSION_DEFAULT = "5.3"`,
  `PVGIS_VERSION_LEGADA = "5.2"`, `CLAVE_VERSION_PVGIS = "pvgis_version"`.
- `url_tmy_pvgis(version) -> str`; versión desconocida → `ValueError`.
- `version_pvgis_de_estado(estado) -> str`: la guardada si es válida; si no,
  5.3.
- `version_pvgis_de_proyecto_guardado(estado_guardado) -> str`: la guardada si
  es válida; si no, 5.2.
- `sufijo_cache_pvgis(version) -> str`: `""` para 5.2, `"_pvgis53"` para 5.3.
- `metadatos_pvgis(data, version) -> dict`: `version`, `radiation_db`,
  `meteo_db`, `year_min`, `year_max`, `meses` (lista de `(mes, año)`);
  claves ausentes → `None` o lista vacía.
- `texto_meses_tmy(meta) -> str`: «Ene 2012 · Feb 2018 · …».
- `obtener_tmy_pvgis(lat, lon, timeout=30, version="5.2")`: llama a la URL de
  la versión y deja los metadatos en `df.attrs["pvgis"]`.

`pages/2_☀️_Recurso_Solar.py`:

- Nombres de caché con el sufijo de versión antes del de albedo.
- Guarda `_solar_pvgis_guardada`; si difiere de la versión elegida, invalida
  como un cambio de coordenadas.

`calculos/proyectos_manager.py::cargar_proyecto`: fija `pvgis_version` con
`version_pvgis_de_proyecto_guardado`.

## Tipos de datos

`str` para la versión; `dict` para los metadatos; `pd.DataFrame` para el TMY.

## Errores posibles

- Versión desconocida en un proyecto guardado: se usa 5.2.
- PVGIS no manda metadatos, o el TMY viene de una caché antigua sin
  `attrs`: el recuadro dice que no hay metadatos y el cálculo sigue igual.

## Dependencias

`requests`, `pandas` (ya instaladas).

## Criterios de aceptación

1. `obtener_tmy_pvgis(..., version="5.3")` llama a `/api/v5_3/tmy`; sin
   versión, a `/api/v5_2/tmy`.
2. Los metadatos (base, periodo, año por mes) quedan en `df.attrs["pvgis"]`.
3. Proyecto nuevo → 5.3; proyecto guardado sin versión → 5.2; versión
   guardada válida → esa.
4. Los nombres de caché de 5.2 no cambian; los de 5.3 son distintos.
5. Cambiar la versión invalida el recurso solar y sus derivados.
6. El manual del Asistente responde qué versión usa la app y por qué no
   coincide mes a mes con PVsyst.
