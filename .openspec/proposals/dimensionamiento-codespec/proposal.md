# Proposal: CodeSpec del módulo Dimensionamiento

## Objetivo

Formalizar el contrato funcional del módulo `bipv_python/pages/4_📐_Dimensionamiento.py` y su lógica pura en `bipv_python/calculos/dimensionamiento.py`, preservando la compatibilidad eléctrica, la vigencia del diseño confirmado y la propagación coherente hacia Producción, Unifilar, RETIE, Financiero y reportes.

## Estado actual

Dimensionamiento combina cinco fuentes de entrada:

- catálogo de paneles e inversores;
- temperaturas de diseño derivadas de ciudad/TMY y editables por el usuario;
- configuración de área, ocupación, tipo de instalación y proyecto activo;
- número de cadenas/trackers y rango de exploración de módulos en serie;
- estado persistido de Motor IV, batería y selección de equipos.

La lógica eléctrica principal es pura y reutilizable: `evaluar_compatibilidad_string`, `optimizar_n_serie`, `dimensionar_sistema`, `mapear_inversores_catalogo`, `resolver_n_strings_tracker` y `diseno_electrico_confirmado`.

## Alcance

Esta propuesta documenta y protege el contrato antes de cualquier refactor de la página Streamlit. No cambia todavía fórmulas ni nombres públicos de `session_state`.

## Riesgos identificados

- mezclar el panel/inversor actual con un `N_serie` confirmado para otro diseño;
- consumir `N_str_tr` vivo en lugar de `N_str_tr_usado` confirmado;
- usar temperaturas mágicas o de otra ciudad;
- presentar un prorrateo preliminar después de cambiar panel, inversor o cadenas;
- perder la coherencia entre resultado por inversor y proyecto completo;
- confundir compatibilidad eléctrica con relación DC/AC o con disponibilidad de Motor IV.
