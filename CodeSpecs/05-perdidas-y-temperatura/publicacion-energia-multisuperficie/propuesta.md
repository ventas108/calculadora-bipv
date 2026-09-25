# Propuesta — Publicación única de la energía multi-superficie

**Estado:** completado

## Objetivo

Que la energía multi-superficie oficial tenga un único punto de escritura,
un origen explícito y un conjunto de claves siempre coherente entre sí.

## Alternativas consideradas

1. **Solo advertir en la UI.** No corrige el descuadre de desglose ni el
   `_multisup_proyecto_fisico` huérfano.
2. **Eliminar dos de los tres caminos.** Pierde usos legítimos (comparar
   simplificado, bypass con CSV, físico).
3. **Función central `publicar_energia_multisuperficie`** en `calculos/`,
   usada por los tres botones, que escribe todas las claves de una vez,
   registra el origen y exige confirmación al reemplazar un origen distinto.
   Recomendada.

## Alternativa recomendada

La alternativa 3:

1. `publicar_energia_multisuperficie(session_state, origen, e_ac_total,
   desglose, poa_ponderada, area_total, proyecto_fisico=None)`, con `origen`
   en {`simplificado`, `bypass_csv`, `fisico`}. Escribe juntas las cinco
   claves de energía y `multisup_origen`; para `fisico` escribe además
   `_multisup_proyecto_fisico` y `multisup_perdida_bus_kWh`, y para los
   otros orígenes borra ambas.
2. `retirar_energia_multisuperficie(session_state)`: la usa «✖ Desactivar»,
   borra también `_multisup_proyecto_fisico`, `multisup_perdida_bus_kWh` y
   `multisup_origen`.
3. El bypass por superficie construye su desglose y su POA ponderada
   coherentes con su total antes de publicar.
4. Si ya hay una energía publicada con otro origen, la UI muestra el origen
   vigente y pide confirmación explícita antes de reemplazarla.
5. El banner muestra el origen; la persistencia guarda `multisup_origen`.
6. `_multisup_proyecto_fisico`, `multisup_perdida_bus_kWh` y
   `multisup_origen` se añaden a `calculos/invalidacion.py` junto a las demás
   claves multi-superficie.
