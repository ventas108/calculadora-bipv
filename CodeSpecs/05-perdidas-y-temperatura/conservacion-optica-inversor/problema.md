# Spec B — Conservación óptica al adoptar inversor

**Estado:** completado

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): transición de `session_state` al adoptar
una configuración en `pages/4b_⚖️_Comparador_Inversores.py`. La Spec protege el
estado vigente del Motor Óptico y mantiene la invalidación de resultados que sí
dependen del inversor o del diseño eléctrico.

## Problema a resolver

El comparador adopta hoy el nuevo inversor y luego invalida todas las claves de
`KEYS_DERIVADOS_POA` excepto `poa_efectiva_df`. Esa regla negativa conserva una
sola salida visual, pero elimina `poa_sin_termico_df`, `motor_optico_ok`, el
resumen y los parámetros ópticos/térmicos.

Cambiar el inversor o `N_serie` no cambia el TMY, la geometría, el panel, IAM,
soiling, NOCT ni la POA calculada por el Motor Óptico. Sin embargo, después de
adoptar, Producción puede encontrar `motor_optico_ok=False` o no disponer de
`poa_sin_termico_df`, su única entrada válida cuando el Motor Óptico está activo.
Esto obliga a repetir un cálculo físico independiente o permite que una corrida
posterior use una ruta distinta de la que estaba vigente antes de la adopción.

La energía, clipping, bypass, pérdida óhmica, resultados financieros y CO₂ sí
pueden depender del inversor, del número de unidades o de `N_serie`, y deben
seguir caducando.

## Contexto

La desviación está registrada en el contrato transversal del Director. La raíz
es de clasificación de estado, no de fórmula física: `KEYS_DERIVADOS_POA` mezcla
estado óptico reutilizable con resultados downstream. La corrección debe crear
una transición central y testeable para cambio de inversor, sin modificar el
Motor Óptico, las fórmulas de Producción, el comparador de orientación, el flujo
multi-superficie ni la vigencia de tablas/IA.
