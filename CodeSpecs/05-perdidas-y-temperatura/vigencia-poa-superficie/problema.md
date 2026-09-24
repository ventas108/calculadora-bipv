# Spec — Vigencia de la POA por superficie

**Estado:** diseño

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): ciclo de vida de
`st.session_state["poa_superficies"]` en `pages/9_🗺️_Vista_3D.py` y en
`calculos/multi_superficie.py`. No cambia la física de la POA
(`calcular_poa_superficie`) ni el modo físico, que calcula su propia POA en
`transicion_multisuperficie.recalcular_fisica_superficie`.

## Problema a resolver

La POA por superficie se calcula al pulsar «⚡ Calcular POA para todas las
superficies» (`pages/9_🗺️_Vista_3D.py`, línea 1325) y **nunca caduca**:

1. Editar tilt, azimuth, área, tipo o montaje de una superficie no la invalida.
2. Cambiar el TMY o las coordenadas del proyecto tampoco:
   `poa_superficies` no está en ninguna lista de `calculos/invalidacion.py`.
3. El diccionario se indexa por **nombre**; renombrar una superficie la
   desvincula de su POA sin aviso.
4. `calcular_poa_todas` (`multi_superficie.py`, líneas 153–154) captura
   cualquier excepción y guarda un DataFrame vacío, sin informar la causa.
5. La persistencia (`persistencia_multisuperficie.py`, líneas 149, 204 y
   242) compara un campo `firma_poa` que **ninguna función escribe**: la
   verificación de vigencia de la POA existe en el contrato pero siempre
   compara `None` con `None`.

Consumidores que hoy pueden usar una POA obsoleta: resumen POA,
«🔗 Usar sistema multi-superficie en Financiero», 🎨 Vista 3D
Multi-Superficie, 📊 Producción por Superficie (incluido el bypass por
superficie) y el mapa de calor de 🌞 Trayectoria Solar.

## Contexto

- El resto del flujo multi-superficie ya usa firmas deterministas
  (`firma_sombra`, `tmy_fingerprint`, `version_algoritmo`); la POA es el único
  resultado sin firma.
- Relacionada: la Spec `publicacion-energia-multisuperficie` exige POA
  vigente para publicar la energía simplificada; esta Spec va primero.
