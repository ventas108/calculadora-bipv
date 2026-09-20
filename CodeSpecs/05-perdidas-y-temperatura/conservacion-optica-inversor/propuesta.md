# Propuesta — Conservación óptica al adoptar inversor

**Estado:** completado

## Objetivo

Adoptar una configuración de inversor como una transición atómica que conserve
íntegro el estado óptico independiente del inversor e invalide únicamente los
resultados que deben recalcularse con el nuevo hardware o `N_serie`.

## Alternativas consideradas

1. **Mantener la exclusión actual de una sola clave.** Conserva
   `poa_efectiva_df`, pero borra la entrada real del SDM y parámetros ópticos;
   mantiene la incoherencia.
2. **No invalidar nada al adoptar.** Preserva el Motor Óptico, pero deja vivos
   Producción, clipping, bypass, Finanzas y CO₂ del inversor anterior; es
   inaceptable.
3. **Recalcular automáticamente Motor Óptico y Producción.** Añade trabajo
   costoso, efectos implícitos y riesgo de usar entradas distintas sin acción
   consciente del usuario.
4. **Definir en `calculos/invalidacion.py` un conjunto central de estado del
   Motor Óptico y una función idempotente de invalidación por cambio de
   inversor.** La página adopta el hardware y delega la limpieza a esa función.

## Alternativa recomendada

La alternativa 4:

1. Extraer las claves propias del Motor Óptico a una única constante central
   que incluya estado, ambas POA, resumen y parámetros publicados.
2. Componer `KEYS_DERIVADOS_POA` a partir de esa constante más los resultados
   downstream existentes, sin cambiar el comportamiento de invalidación por
   cambio de geometría o POA.
3. Definir `invalidar_por_cambio_inversor(session_state)` como operación
   idempotente: conserva el conjunto óptico y elimina el resto de resultados
   derivados actualmente afectados por la adopción.
4. Sustituir la lista local de la página por esa función y mostrar qué debe
   recalcularse, sin afirmar que el Motor Óptico caducó.
5. Probar la transición con y sin Motor Óptico, con cambio de `N_serie` y con
   claves desconocidas del usuario que no deben tocarse.

Quedan fuera de esta Spec la orientación multi-superficie, la firma de tablas e
IA, cambios de fórmulas físicas, recálculos automáticos y cualquier función de la
app React.
