# Propuesta — 🌾 Granja FV, fase 5: eléctrico por bloques — strings, inversores y cables que alimentan Unifilar y RETIE

**Estado:** validación

## Objetivo

Que el diseño eléctrico de la granja salga de la geometría del campo y
llegue sin copiar números a ⚡ Diagrama Unifilar, 📊 Producción (pérdida
óhmica) y 📋 Ficha RETIE.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026 («si, empieza la fase 5»).

- `calculos/granja_electrico.py`:
  - `armar_strings`: recorre cada fila de izquierda a derecha, columna por
    columna; cada `N_serie` módulos forman un string; marca los que cruzan
    de fila y los módulos sobrantes.
  - `disenar_bloques`: llena los inversores con el reparto de
    Dimensionamiento (o parejo si no coincide); inversor en la cabecera o en
    el centro de su bloque; punto de conexión en una esquina; largo DC y AC
    en L con holgura; caída de tensión DC y AC trifásica (cobre a 45 °C);
    resistencia DC efectiva y pérdida a STC.
  - `avisos_bloques`, `checks_retie` (formato de la ficha),
    `tramos_para_unifilar` (un tramo por string) y `diseno_desde_estado`
    (recalcula siempre con los datos guardados: nunca un resultado viejo).
- 🌾 Granja FV, sección 8: ubicación del inversor, punto de conexión,
  calibres, tensión AC y holgura (se guardan en `granja_electrico_cfg`);
  avisos, tarjetas, tabla por inversor y plano eléctrico.
- ⚡ Diagrama Unifilar (granja, superficie única): casilla «🌾 Usar los
  cables de 🌾 Granja FV» que pone un tramo DC por string y el AC medio.
- 📋 Ficha RETIE (granja, superficie única): validaciones de strings,
  cruces y caída de tensión frente al 3 % de la NTC 2050.
- Manual del Asistente, sección 97.

## Alternativas descartadas

- Un solo tramo DC con el largo medio: subestima la pérdida porque la
  pérdida crece con el cuadrado de la corriente por tramo; un tramo por
  string da la suma exacta.
- Guardar el resultado en la sesión y leerlo en Unifilar y RETIE: podría
  quedar viejo si cambia el campo; se recalcula en cada página.

## Fuera de alcance

- Cajas combinadoras y centros de transformación de granjas grandes.
- Ruta real de zanjas; la app estima el recorrido en L.
- Modo multi-superficie de Vista 3D (tiene su propio diseño eléctrico).
