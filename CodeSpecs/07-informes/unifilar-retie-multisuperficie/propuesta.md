# Propuesta — Diagrama Unifilar y Ficha RETIE con el sistema multi-superficie real

**Estado:** validación

## Objetivo

Que el diagrama y la ficha muestren y revisen el mismo sistema que se diseñó en
🗺️ Vista 3D, con todos sus elementos: strings, protecciones, cajas
combinadoras, optimizadores, inversores, batería, tablero y red.

## Alternativas consideradas

1. **Seguir pidiendo los datos a mano en cada página.** Descartada: el mismo
   sistema se escribe tres veces y se descoordina.
2. **Una topología eléctrica única, calculada desde Vista 3D, que leen las dos
   páginas.** Recomendada.
3. **Validar de nuevo cada string en la Ficha con fórmulas propias.**
   Descartada: duplicaría `validar_diseno_electrico` y podría dar otro
   resultado para el mismo string.

## Alternativa recomendada

Aprobada por el usuario el 28-sep-2026 («autorización completa»).


- **D1.** Nuevo módulo puro `calculos/topologia_electrica.py`: arma la topología
  (inversor → MPPT → grupos, caja combinadora, optimizadores, batería) desde
  las superficies, los inversores y el diagnóstico eléctrico.
- **D2.** ⚡ Diagrama Unifilar: con multi-superficie activo y grupos definidos,
  el dibujo sale solo de la topología: una rama por MPPT con sus strings,
  protección DC, caja combinadora cuando el diagnóstico la pide, bus DC por
  inversor, un bloque por inversor con su breaker AC, bus AC, breaker general,
  medidor y punto de conexión. El modo de una superficie no cambia.
- **D3.** Optimizadores: una opción de sistema «optimizadores MLPE, uno por
  módulo» (`sistema_optimizadores`), la misma en las dos páginas y guardada
  con el proyecto. Se dibuja en cada string y la Ficha la marca «por revisar»
  porque la app todavía no valida strings con optimizador. No cambia la
  energía.
- **D4.** Batería: se conecta al inversor elegido (`bateria_inversor_id`, por
  defecto el primero) y la compatibilidad se revisa con ese inversor.
- **D5.** 📋 Ficha RETIE: selector de origen de datos (sistema multi-superficie
  o 📐 Dimensionamiento). En multi-superficie las validaciones salen del
  diagnóstico eléctrico (verde = OK, amarillo = por revisar, rojo = error),
  más caja combinadora y fusibles gPV, batería, optimizadores, temperaturas
  de diseño, capacidad interruptiva y puesta a tierra. Los bloques del campo
  FV, de los inversores y la tabla de cargas muestran cada superficie y cada
  inversor con su potencia, corriente y breaker.
- **D6.** 🧭 Asistente: sección que explica qué revisa la app frente al RETIE y
  qué no, con el ejemplo del cliente; registro en el director.

## Fuera de alcance

- Validación eléctrica de strings con optimizador o microinversor (Spec B).
- Estudio de cortocircuito, coordinación de protecciones, análisis de riesgo
  por rayos y cálculo de la malla de tierra.
- Salida monofásica: la corriente AC sigue la fórmula trifásica de la app.
- La pérdida óhmica del cableado por longitud y calibre sigue siendo de una
  superficie: en modo multi-superficie la página no la muestra (la energía ya
  usa la cadena de pérdidas de cada superficie) y lo explica.
