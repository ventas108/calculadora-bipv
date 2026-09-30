# Diseño — 🌾 Granja FV, fase 5: eléctrico por bloques — strings, inversores y cables que alimentan Unifilar y RETIE

**Estado:** validación

## Entradas

- Campo de `granja_fv.calcular_campo` (mesas con fila, x, y; ancho de mesa,
  lado del módulo, altura del centro, terreno).
- Panel (`Imp_stc`, `Vmp_stc`), `N_serie`, `reparto_strings_inversores`,
  `inversor_dict_dim` (`P_ac_nom_W`).
- `granja_electrico_cfg`: `ubicacion_inversor` (cabecera/centro),
  `punto_conexion` (esquina), `calibre_dc_mm2` (6), `calibre_ac_mm2` (70),
  `tension_ac_v` (400), `holgura` (0,10).

## Salidas

- `disenar_bloques(...) -> dict`: strings (fila, inversor, largo DC, caída,
  cruce, posición), bloques por inversor (strings, módulos, filas, DC medio
  y máximo, AC, corriente y caída AC), totales, caídas máximas, resistencia
  DC efectiva (mΩ), pérdida DC a STC (%), punto de conexión.
- `avisos_bloques` / `checks_retie`: `strings_completos`, `cruzan_filas`,
  `caida_dc_max_pct`, `caida_ac_max_pct`.
- `tramos_para_unifilar`: un tramo por string para `calcular_perdida_ohmica`.

## Tipos de datos

`dict`, `list[dict]`, `float`.

## Errores posibles

- Sin campo, sin panel o sin módulos en serie: `diseno_desde_estado` da
  `None` y las páginas no muestran nada nuevo.
- Módulos que no forman strings completos: aviso 🔴 (ERROR en la ficha).
- Proyecto que no es granja: Unifilar y RETIE no usan este diseño.

## Dependencias

`calculos/granja_fv.py`, `calculos/diagrama_unifilar.py` (resistividad y
`calcular_perdida_ohmica`), páginas 9b, 20 y 21.

## Criterios de aceptación

1. Apartadó: 11 strings de 28, 0 sobrantes, 4 cruzan filas; filas de 56
   módulos no cruzan.
2. Bloques 6 + 5 (168 y 140 módulos); reparto inválido → parejo.
3. Caídas DC y AC iguales a sus fórmulas; más calibre → menos caída; más
   holgura → más cable; inversor al centro → menos DC; punto lejano → más AC.
4. La resistencia DC efectiva es igual a la de `calcular_perdida_ohmica`
   con los tramos por string.
5. Avisos 🟢/🟠/🔴 y su formato en la ficha RETIE.
6. Granja, Unifilar y RETIE usan el mismo diseño recalculado; solo en
   proyectos tipo granja.
7. El manual del Asistente lo explica (sección 97).
