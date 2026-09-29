# Spec — Vista 3D: string que cruza dos superficies

**Estado:** validación

## Alcance de la fase

🗺️ Vista 3D, modo multi-superficie: modelo de datos de los grupos de strings
(`calculos/diseno_electrico_multisup.py`), la cadena de pérdidas por
superficie (`calculos/cadena_perdidas_multisup.py`, que usan los modos
simplificado y bypass), el modo físico (`calculos/adaptador_multisuperficie.py`)
y la sección «🔀 6. Strings de distinta orientación en un mismo MPPT».

## Problema a resolver

En Vista 3D cada grupo de strings pertenece a **una** superficie: un string
nunca mezcla orientaciones. En obra es común que un string cruce una esquina
(parte en la fachada Este y parte en la Oeste) o pase del techo a la fachada.
Hoy la app no puede declararlo; se modela como dos strings separados y **no
resta la pérdida en serie** del string mixto, que con la Spec
`05/mismatch-orientacion-horario` se mide en Apartadó así:

| Mezcla en el mismo string | Pérdida hora a hora (diodos de bypass) |
|---|---|
| Fachadas Este/Oeste 50/50 | 14.9 % |
| Fachadas Sur/Este 70/30 | 15.9 % |
| Techo 10° Sur / fachada Sur 80/20 | 7.9 % |

Además, la sección «🔀 6» (strings de distinta orientación **en paralelo**
en el mismo MPPT) es solo informativa: ese caso sigue sin cambiar la energía
oficial y queda fuera de esta Spec.

## Contexto

En los modos simplificado y bypass la energía de cada superficie es
POA × área × η × PR, con el PR de su cadena de pérdidas; el área sale de los
módulos de la superficie. El modo físico convierte cada grupo en una unidad
con la geometría y la sombra 3D de su superficie.
