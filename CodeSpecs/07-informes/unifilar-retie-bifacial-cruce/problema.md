# Spec — ⚡ Diagrama Unifilar y 📋 Ficha RETIE coherentes con Motor Óptico, Mismatch y Vista 3D

**Estado:** validación

## Alcance de la fase

⚡ Diagrama Unifilar (`calculos/diagrama_unifilar.py`, página 20), 📋 Ficha
de validación RETIE (`calculos/ficha_validacion_retie.py`, página 21), la
topología eléctrica que comparten (`calculos/topologia_electrica.py`), el
diagnóstico eléctrico de 🗺️ Vista 3D (`calculos/diseno_electrico_multisup.py`)
y la tabla de pérdidas eléctricas de 🔀 Mismatch.

## Problema a resolver

Auditoría del 29-sep-2026, pedida por el usuario tras las Specs de
🔆 Motor Óptico bifacial (#80), 🔀 Mismatch (#81, #82) y el string que cruza
superficies en Vista 3D (Spec `05/string-cruza-superficies`):

1. **Corriente de diseño DC sin la cara trasera.** Conductores DC (ampacidad
   en el Unifilar), fusibles gPV de las cajas combinadoras (RETIE) y el límite
   de corriente del MPPT (Vista 3D) usan Isc × 1.25 con el Isc de la ficha
   (solo cara frontal, STC). Con panel bifacial la norma IEC 62548-1 pide la
   corriente en la irradiancia de placa bifacial (BNPI, IEC TS 60904-1-2:
   1000 W/m² al frente + 135 W/m² atrás): Isc_BNPI = Isc × (1 + φ × 0.135).
   JAM66D46-720/LB (φ = 0.80): 18.59 A → 20.60 A por string (+10.8 %). El
   🔆 Motor Óptico ya cuenta esa luz trasera en la energía; la ficha RETIE no.
2. **String que cruza superficies (Vista 3D).** El Unifilar y la RETIE cuentan
   los módulos del string en la superficie de origen, aunque parte esté en la
   otra, y no dicen que el string cruza.
3. **Cableado de 🔀 Mismatch.** La tabla «Pérdidas que 📊 Producción aplica
   sobre la potencia» muestra el % manual de cableado aunque haya un cálculo
   real del ⚡ Diagrama Unifilar (que Producción usa si está vigente). En
   multi-superficie el Unifilar dice «cables DC 1,5 %» fijo, aunque el valor
   de 🔀 Mismatch sea otro.

## Contexto

`topologia_electrica.topologia_desde_estado` alimenta el Unifilar y la ficha
multi-superficie; `validar_diseno_electrico` calcula `isc_total` por MPPT.
`evaluar_compatibilidad_string` solo usa Isc para el límite de corriente.
