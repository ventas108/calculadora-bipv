# Proposal: CodeSpec del Motor Óptico BIPV

## Objetivo

Formalizar el contrato del Motor Óptico (`bipv_python/calculos/motor_optico.py` y `bipv_python/pages/5b_🔆_Motor_Optico.py`) para que sus correcciones IAM, soiling, temperatura BIPV y transparencia sean trazables y no se apliquen dos veces en Producción o Financiero.

## Estado actual

El motor recibe el TMY y la POA bruta producida por Recurso Solar y aplica una cascada vectorizada:

1. IAM ASHRAE sobre la componente directa y factor medio sobre difusa.
2. Soiling mensual Colombia, con autolavado por viento y ajuste de fachada vertical.
3. Factor térmico NOCT × `k_BIPV`.
4. Transparencia `tau` solo informativa, porque la ficha eléctrica real ya incorpora su efecto en `Isc_stc/Pmax_stc`.

La temperatura térmica se separa deliberadamente del POA entregado al SDM: Producción consume `poa_sin_termico_df` (IAM + soiling) y aplica la temperatura dentro del modelo eléctrico con `k_BIPV`; `poa_efectiva_df` conserva la cascada completa para visualización, resúmenes y Financiero.

## Coherencias verificadas

- Funciones puras vectorizadas, independientes de Streamlit.
- Auto-llenado desde panel y tipo de instalación.
- Defaults de montaje clasificados por tipo y robustos al reordenamiento del catálogo.
- Invalidación del recurso solar y de derivados al cambiar ciudad/coordenadas.
- Desglose PVsyst de IAM/soiling/térmico probado sin doble conteo.
- `Y_r` y `PR` usan la POA bruta real, no la POA ya corregida.

## Limitaciones explícitas

- `k_BIPV=1.15` es una interpolación documentada, no una medición.
- El modo térmico actual es NOCT × `k_BIPV`; el modelo Faiman `Uc/Uv` con viento real queda como mejora futura opcional.
- La transparencia se muestra como impacto informativo y no se descuenta de la POA que entra a Producción.
