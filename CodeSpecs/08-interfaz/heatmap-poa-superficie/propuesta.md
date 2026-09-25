# Propuesta — Error del mapa de calor POA con POA por superficie calculado

**Estado:** completado

## Objetivo

Que el mapa de calor use el POA de la superficie cuando existe y el POA
general cuando no, sin evaluar la verdad de un DataFrame.

## Alternativa recomendada

Reemplazar `a or b` por una comparación explícita con `None`:

```python
_poa_hm_df = st.session_state.get("poa_superficies", {}).get(nombre)
if _poa_hm_df is None:
    _poa_hm_df = _poa_s
```

Misma intención que el código original, sin cambiar qué serie se elige ni el
cálculo del mapa. Alternativas descartadas: `.empty` (un DataFrame vacío se
trataría como ausente, que no era la intención) y envolver en `try/except`
(ocultaría el error). Se agrega una prueba estática que impide volver a usar
`or` sobre series POA en la página.
