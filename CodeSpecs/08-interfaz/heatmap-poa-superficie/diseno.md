# Diseño — Error del mapa de calor POA con POA por superficie calculado

**Estado:** validación

## Entradas

- `st.session_state["poa_superficies"]`: `dict[str, DataFrame]` (puede faltar).
- `st.session_state["poa_df"]` (`_poa_s`): DataFrame general o `None`.
- Nombre de la superficie seleccionada en el mapa de calor.

## Salidas

- `_poa_hm_df`: el DataFrame de la superficie si existe; si no, `_poa_s`.
  El resto de la sección (longitud igual al índice solar, `poa_global`,
  respaldo de 300 W/m²) no cambia.

## Tipos de datos

`DataFrame | None`; la decisión se toma con `is None`, nunca con la verdad
del objeto.

## Errores posibles

- Reintroducir `or` sobre una serie POA en la página: lo detecta
  `test_vista3d_no_evalua_la_verdad_de_series_poa` (análisis AST de la página).

## Dependencias

- Módulos previos: `05-perdidas-y-temperatura/transicion-multisuperficie`
  (publica `poa_superficies`).
- Módulos dependientes: ninguno; es solo presentación.
- Capa afectada: interfaz Streamlit (`pages/9_🗺️_Vista_3D.py`).

## Criterios de aceptación

- Con POA por superficie calculado, la sección del mapa de calor no lanza
  `ValueError` y usa la serie de la superficie.
- Sin POA por superficie, usa `poa_df` igual que antes.
- La prueba nueva falla con `e677aba6` y pasa con la corrección.
- Suite completa de `bipv_python/tests` en verde.
