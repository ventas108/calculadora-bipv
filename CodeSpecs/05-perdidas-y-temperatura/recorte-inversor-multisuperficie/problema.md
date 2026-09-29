# Spec — Vista 3D: recorte de cada inversor en los modos simplificado y bypass

**Estado:** validación

## Alcance de la fase

🗺️ Vista 3D, energía multi-superficie de los modos **simplificado** y
**bypass** (`calculos/cadena_perdidas_multisup.py`), la tabla de desglose y el
texto de la relación DC/AC de ⚡ Diseño eléctrico. El modo físico no cambia.

## Problema a resolver

En Vista 3D el diseñador elige los inversores y asigna cada grupo de strings a
uno. Solo el **modo físico** limita la salida de cada inversor a su potencia
AC nominal (suma horaria de su bus). Los modos simplificado y bypass publican
POA × área × η × PR por superficie **sin ese límite**: con un inversor chico
(DC/AC alto) la energía publicada sale más alta de lo que el inversor puede
entregar. ⚡ Diseño eléctrico avisa en 🟡 («el modo físico calcula cuánto»),
pero el número que va a 💰 Financiero no lo resta.

Además, el mensaje de la relación DC/AC (`evaluar_relacion_dc_ac`) decía
«rango típico de diseño (0.95–1.35)», pero el cálculo pone 🟢 desde **1,00**:
una relación de 0,97 salía 🟠 «por debajo del rango típico (0.95–1.35)». El
manual del Asistente (sección de la relación DC/AC) repetía 0,95.

Por último, en 📐 Dimensionamiento el campo «Cantidad de inversores del
proyecto» en **0** (automático) parecía vacío: el usuario esperaba ver ahí los
2 inversores de Apartadó, que la app sí calculaba más abajo en «🏭 Proyecto
completo».

## Contexto

Pregunta del usuario el 29-sep-2026, tras encontrar en Apartadó que 📊
Producción (superficie única) simulaba 1 inversor en vez de 2 (Spec
`03/inversores-del-proyecto`). En Vista 3D ese redondeo no existe (los
inversores se eligen), pero faltaba el recorte en dos de los tres modos.
