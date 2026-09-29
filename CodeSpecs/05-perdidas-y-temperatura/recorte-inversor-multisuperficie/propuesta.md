# Propuesta — Vista 3D: recorte de cada inversor en los modos simplificado y bypass

**Estado:** validación

## Objetivo

Que la energía publicada por los modos simplificado y bypass reste, hora a
hora, lo que cada inversor no deja pasar por encima de su potencia AC.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («si prepara la Spec de Vista 3D con
su PR»).

- `cadena_superficie` devuelve la **forma horaria** de la AC de la superficie
  (`perfil_ac`, suma 1): la AC horaria del SDM o, sin SDM, la POA después de
  la temperatura.
- `calculos/recorte_inversores_multisup.factores_recorte`: AC de cada
  superficie = energía del año (POA bruta × módulos × Pmax × PR) × forma
  horaria; AC de cada grupo con sus módulos **donde están** (un string que
  cruza aporta desde las dos superficies); AC del inversor = suma de sus
  grupos; recorte = max(AC − Pnom, 0); el recorte de cada hora se reparte por
  el aporte de cada superficie.
- `cadena_superficies_estado` lo aplica después del string que cruza:
  PR × `f_recorte`, columna «Recorte inversor» en el desglose, resumen por
  inversor. Simplificado y bypass lo toman del PR de la cadena.
- Tabla «✂️ Recorte por inversor (hora a hora)» en Vista 3D; el aviso DC/AC
  de ⚡ Diseño eléctrico ya no dice que solo el modo físico lo calcula.
- La firma de la cadena incluye potencias AC y grupos (solo si hay inversores
  con potencia AC y grupos): cambiar la potencia vence la energía publicada.
- El mensaje de la relación DC/AC dice **1.00–1.35**, el rango que de verdad
  usa el cálculo (pedido del usuario el 29-sep-2026); el manual se corrige
  igual. Los límites no cambian.
- Manual del Asistente, sección 91.

## Alternativas descartadas

- Recortar con la energía anual (sin horas): el recorte ocurre solo en las
  horas de más sol; un cálculo anual no lo ve.
- Recortar cada superficie por separado: un inversor con grupos en dos
  fachadas recibe la suma de las dos; por separado se subestima.

## Fuera de alcance

- En el modo bypass el recorte se calcula antes de la sombra del CSV (queda
  un poco por encima del real); el modo físico ya lo hace con su bus.
- El modo físico no cambia.
