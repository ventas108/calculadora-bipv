# Propuesta — Integración de la transición transaccional multi-superficie con Streamlit

**Estado:** aprobado para iniciar integración opt-in, sin activar el modo físico por defecto

## Objetivo

Integrar `calculos/transicion_multisuperficie.py` a `pages/9_🗺️_Vista_3D.py`
como un modo experimental **opt-in**, sin tocar las 7 páginas que hoy
consumen las claves `multisup_*`, sin reemplazar el modelo simplificado
hasta que una comparación explícita lo respalde, y sin resolver todavía las
dos ampliaciones de fondo que quedan fuera de alcance (sombra por
superficie, Motor Óptico por superficie).

## Alternativas consideradas

1. **Migrar los 8 consumidores a leer `proyecto["agregados"]["E_ac_total_kWh"]`
   directamente.** Descartada: obliga a importar
   `calculos.transicion_multisuperficie` en 8 archivos, duplica la lógica
   de prioridad `multisup > bypass > base` que ya existe, y mantiene dos
   contratos de energía multi-superficie en paralelo mientras dure la
   migración.
2. **Reemplazar de inmediato el modelo simplificado por el físico.**
   Descartada: el modelo físico exige datos que `session_state` no tiene
   (inversor/`p_shade`/firmas por superficie); reemplazar sin ellos
   bloquearía a cualquier usuario con un proyecto multi-superficie ya
   configurado.
3. **Dejar el módulo físico sin integrar hasta resolver sombra y Motor
   Óptico por superficie primero.** Descartada como *bloqueante total*:
   permite congelar meses de trabajo ya validado (27 pruebas) esperando dos
   ampliaciones de alcance mayor. Se prefiere una integración parcial
   honesta (opt-in, con las limitaciones declaradas) sobre no integrar nada.
4. **Adaptador que traduce `session_state` ↔ `proyecto` canónico y escribe
   el resultado en las MISMAS 5 claves `multisup_*` que ya existen, detrás
   de un toggle opt-in con comparación obligatoria antes de adoptar.**

## Alternativa recomendada

La alternativa 4:

1. Un adaptador de entrada (`session_state → proyecto`) que **falla
   explícito** si a una superficie le falta un dato requerido — nunca
   inventa un inversor, una máscara de sombra o una firma por defecto.
2. Un adaptador de salida (`proyecto["agregados"] → session_state`) que
   escribe en `E_ac_anual_kWh_multisup`, `area_total_multisup`,
   `multisup_desglose` (mismas 5 sub-claves que ya arma
   `e_ac_total_multisup()`), `multisup_activo` y `poa_df_multisup` — los 8
   consumidores existentes no cambian.
3. Un toggle opt-in (`multisup_usar_fisico`, default `False`, mismo patrón
   que `produccion_usar_iv` del Motor IV) que, cuando está activo, corre
   AMBOS modelos y exige ver la comparación antes de permitir adoptar el
   resultado físico.
4. Dos ampliaciones declaradas **explícitamente fuera de esta Spec**, con
   su propia Spec futura: sombra por superficie (`calculos.sombras_3d`) y
   Motor Óptico por superficie (página 5b). Mientras no existan, toda
   superficie con `motor_optico_vigente=True` o sin `p_shade` real queda
   bloqueada por el propio módulo físico (ya lo hace hoy, ver
   `_validar_firma_sombra`/`_validar_firma_poa_optica`), nunca con un
   valor inventado.
5. UI de asignación de inversor por superficie (dedicado/compartido) como
   pieza de producto a diseñar en `diseno.md`, no asumida como trivial.

Quedan fuera de esta Spec: la implementación en sí (ninguna línea de
Streamlit se escribe todavía), la ampliación de `sombras_3d.py` a sombra
por superficie, la ampliación de Motor Óptico a corridas por superficie, y
cualquier decisión de reemplazar el modelo simplificado de forma
permanente.
