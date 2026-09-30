# Propuesta — 🌾 Granja FV, fase 3: agrivoltaica — luz para el cultivo, mapa de sombra y maquinaria

**Estado:** validación

## Objetivo

Que el diseñador vea la luz que recibe el cultivo en cada punto del suelo y
si la maquinaria cabe, con la misma geometría que usa la energía.

## Alternativa recomendada

Aprobada por el usuario el 30-sep-2026 («continua con lo pendiente»).

- `calculos/agrivoltaica.py`: corte de perfil entre dos filas infinitas
  (misma hipótesis que `infinite_sheds`), 60 franjas de suelo.
  - Luz directa horizontal (`G_h − Gd_h`) si la franja no está en la sombra
    de ninguna fila; la sombra se calcula hora a hora con la posición del sol.
  - Difusa horizontal × fracción de cielo que ve la franja (factor de vista
    2D, unión de los sectores que tapan las filas).
  - Resultado anual y mensual en % del campo abierto y kWh/m², luz bajo la
    mesa y entre filas, mínimo, máximo y homogeneidad.
  - `paso_maquinaria`: categoría I/II (DIN SPEC 91434, altura libre
    2,10 m), paso por debajo (altura + 0,30 m) y por el corredor (ancho +
    0,25 m por lado).
- 🌾 Granja FV, sección 6: altura y ancho de la maquinaria (se guardan con el
  proyecto), avisos, botón «🌱 Calcular la luz en el suelo», perfil anual y
  mapa de sombra mensual; el resultado se oculta si cambia la geometría.
- Texto de la página al día; manual del Asistente, sección 95.

## Alternativas descartadas

- Usar las funciones internas de pvlib (`_unshaded_ground_fraction`,
  `vf_ground_sky_2d`): son privadas o cambian entre versiones; se usan
  solo en las pruebas para validar el cálculo propio.
- Mapa 2D de todo el terreno: con filas largas la luz solo cambia de una
  fila a la otra; el corte mes a mes muestra lo mismo sin inventar detalle.
- Rendimiento agrícola por cultivo: depende del cultivo y del agrónomo; la
  app da la luz, no la cosecha.

## Fuera de alcance

- Luz reflejada por el suelo y por la cara inferior de los paneles (lado
  seguro, unos pocos %).
- Bordes del campo (primera y última fila) y postes de la estructura.
