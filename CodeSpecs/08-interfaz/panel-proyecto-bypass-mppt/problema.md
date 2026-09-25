# Spec — Panel y strings del proyecto en bypass y MPPT por superficie

**Estado:** completado

## Alcance de la fase

App hermana Streamlit (`bipv_python/`): secciones «⚡ 5. Bypass diodes por
superficie» y «🔀 6. Strings de distinta orientación en un mismo MPPT» de
`pages/9_🗺️_Vista_3D.py`. No cambia `mismatch_bypass.py` ni
`mppt_combinado.py`.

## Problema a resolver

1. **Panel por defecto ajeno al proyecto.** Ambos selectores arrancan en
   `ASP-ST1-T40` (líneas 1973–1978 y 2096–2100), no en el panel del proyecto
   (`panel_nombre_dim` / `panel_dict`, escritos por 📐 Dimensionamiento,
   líneas 577–578). Si el usuario no lo cambia, la pérdida por bypass y la del
   MPPT compartido se calculan con otro panel.
2. **Panel fuera del catálogo.** Los selectores solo ofrecen
   `MODULOS_BIPV`; un panel del proyecto que viene del catálogo Excel no se
   puede elegir.
3. **Strings desconectados de la configuración eléctrica.** «Módulos en
   serie» arranca en 8 (líneas 1980–1983 y 2103–2105) y es independiente del
   «N serie» asignado por superficie en ⚙️ Superficies BIPV y del `N_serie`
   de Dimensionamiento. Los strings en paralelo se calculan por área, no con
   el «N paralelo» ya configurado.

El bypass por superficie publica energía oficial (ver la Spec `publicacion-energia-multisuperficie`), así que un
panel o un N en serie equivocados contaminan Financiero, Baterías y CO₂.

## Contexto

- El modo físico usa `panel_dict` y los `n_serie`/`n_paralelo` por
  superficie; estas dos secciones no, y por eso sus resultados no son
  comparables con él.
- Relacionada: la Spec `publicacion-energia-multisuperficie`.
