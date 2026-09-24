# Spec — Publicación única de la energía multi-superficie

**Estado:** diseño

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): escritura de las claves
`E_ac_anual_kWh_multisup`, `multisup_desglose`, `poa_df_multisup`,
`area_total_multisup`, `multisup_activo` y `_multisup_proyecto_fisico`, que
consumen 💰 Financiero, 🔋 Baterías, 🌿 CO₂, 📄 Reporte PDF, ⚡ Diagrama
Unifilar, 🔀 Mismatch y la persistencia del proyecto. No cambia ninguna
fórmula de energía.

## Problema a resolver

Tres caminos escriben la energía oficial y **gana el último pulsado**:

Camino  │  Dónde (`pages/9_🗺️_Vista_3D.py`)  │  Claves que escribe

«🔗 Usar sistema multi-superficie en Financiero»  │  líneas 1403–1412  │  las cinco claves

«⚡ Calcular bypass por superficie»  │  líneas 2053–2056  │  solo `E_ac_anual_kWh_multisup` y `multisup_activo`

«✅ Adoptar cálculo físico»  │  línea 1499 (`aplicar_proyecto_a_session_state`)  │  las cinco claves y `_multisup_proyecto_fisico`

Consecuencias verificadas en el código:

1. Adoptar el cálculo físico y después pulsar cualquiera de los otros dos
   botones reemplaza la energía física sin aviso.
2. El bypass cambia el total pero **no** `multisup_desglose` ni
   `poa_df_multisup`: el total y el desglose por superficie que muestran
   Financiero, Reporte y Unifilar quedan descuadrados.
3. `_multisup_proyecto_fisico` no se borra al publicar por otro camino ni al
   pulsar «✖ Desactivar modo multi-superficie» (líneas 1385–1389), y no
   está en `calculos/invalidacion.py`. Al guardar
   (`proyectos_manager.py`, líneas 246–248) se persiste junto a una energía
   que ya no es la física.
4. Ninguna clave registra qué camino produjo la cifra vigente.

## Contexto

- El banner «✅ Modo multi-superficie activo» muestra la cifra pero no su
  origen.
- Depende de la Spec `vigencia-poa-superficie`: los caminos simplificado
  y bypass deben exigir POA vigente.
- Fuera de alcance: que el bypass recorte también la difusa (Spec física
  aparte, ya identificada en `sombra-cara-trasera`).
