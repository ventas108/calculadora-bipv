# Spec — Error del mapa de calor POA con POA por superficie calculado

**Estado:** validación

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): sección del mapa de calor POA
hora × mes de `pages/9_🗺️_Vista_3D.py`. Sin cambios de cálculo, estado ni API.

## Problema a resolver

Al abrir el mapa de calor de una superficie después de calcular el POA por
superficie, Streamlit corta la página con:

```
ValueError: The truth value of a DataFrame is ambiguous.
File ".../pages/9_🗺️_Vista_3D.py", line 2457
    st.session_state.get("poa_superficies", {}).get(_sup_hm.get("nombre", ""))
```

La serie se elegía con `poa_superficies.get(nombre) or poa_df`. Cuando la
superficie ya tiene POA calculado ese valor es un DataFrame y `or` evalúa su
verdad, lo que pandas prohíbe. Sin POA por superficie el valor es `None` y
el error no aparece, por eso pasó inadvertido.

## Contexto

- Reportado en producción (Streamlit, `main` `e677aba6`) el 2026-09-24.
- La línea viene del commit `e0c76cc9` (2026-09-07); el PR #42 no tocó
  `Vista_3D.py` (`git diff 9398948e..e677aba6` vacío para ese archivo).
- Las demás lecturas de `poa_superficies` en la página (líneas 1333, 1515,
  1801) no evalúan la verdad de un DataFrame.
