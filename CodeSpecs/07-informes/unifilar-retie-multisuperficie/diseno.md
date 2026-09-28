# Diseño — Diagrama Unifilar y Ficha RETIE con el sistema multi-superficie real

**Estado:** validación

## Entradas

- `superficies_bipv` (grupos `{gid, topologia, inversor_id, mppt, n_serie, n_paralelo}`),
  `multisup_inversores`, paneles por superficie
  (`diseno_electrico_multisup.paneles_superficies_estado`) y el diagnóstico de
  `validar_diseno_electrico`.
- `sistema_optimizadores` (bool) y `bateria_inversor_id` (str): claves de datos
  que se guardan con el proyecto.
- Batería: `bateria_ok`, `bateria_nombre`, `bateria_dict`, `bateria_dim`.
- Ficha: tensión de salida, factor continuo 1,25, Icc del PCC y esquema de
  tierra (como antes).

## Salidas

- `topologia_electrica.construir_topologia(...)` →
  `{"inversores": [{inversor_id, nombre, p_ac_kW, p_dc_kWp, ramas: [{mppt,
  caja_combinadora, strings, isc_diseno_A, grupos: [{superficie, gid, panel,
  n_serie, n_paralelo, modulos, p_dc_kWp}]}]}], "superficies": [{nombre,
  paneles, modulos, p_dc_kWp}], "optimizadores", "bateria", "sin_asignar",
  "n_modulos", "p_dc_kWp", "p_ac_kW"}`.
- `topologia_electrica.topologia_desde_estado(estado)` → la misma topología o
  `None` si no hay multi-superficie con grupos.
- `diagrama_unifilar.construir_config_unifilar(..., topologia=...)` →
  `config["topologia"]`; `generar_diagrama_unifilar` la dibuja.
- `ficha_validacion_retie.calcular_retie_multisuperficie(topologia, ...)` →
  mismas claves que `calcular_retie` más `por_inversor`;
  `validar_retie_multisuperficie(topologia, diagnostico, calc, ...)` → lista
  `{nivel, titulo, detalle}`; `generar_ficha_svg(cfg, calc, checks,
  topologia=...)`.

## Reglas

- Una rama por `(inversor, MPPT)`, en el orden del diagnóstico. Los grupos sin
  inversor o MPPT válidos van a `sin_asignar` y la ficha los reporta como error.
- Caja combinadora = `caja_combinadora` del MPPT en el diagnóstico.
- Fusible gPV por string (cuando hay caja): corriente mínima
  1,25 × 1,25 × Isc del panel; el máximo lo fija la ficha del módulo.
- Corriente AC por inversor = P AC ÷ (√3 × V); breaker = calibre comercial
  ≥ 1,25 × corriente. General: suma de inversores.
- Mapeo del diagnóstico: verde → OK, amarillo → nivel naranja (por revisar),
  rojo → ERROR.

## Tipos de datos

Números `float`/`int`; textos `str`; listas de dicts JSON-serializables.

## Errores posibles

- Superficie sin panel o grupo inválido: `sin_asignar` + error en la ficha.
- Inversor sin P AC: potencia, corriente y breaker en `None` (la ficha lo
  muestra en naranja, por revisar), sin inventar valores.
- `bateria_inversor_id` que ya no existe: se usa el primer inversor y la
  página lo avisa.

## Dependencias

`diseno_electrico_multisup` y `compatibilidad_bateria` (sin cambios),
`dimensionamiento.corriente_diseno_ac`.

## Criterios de aceptación

1. Con el sistema del cliente, la ficha usa sus dos paneles y su inversor: los
   Voc en frío y la ventana MPPT son los de ⚡ Diseño eléctrico, uno por grupo.
2. Un MPPT con más strings que entradas (y corriente dentro del límite) dibuja
   una caja combinadora y la ficha pide los fusibles gPV con su corriente
   mínima.
3. Con varios inversores: una rama por inversor con su breaker AC, bus AC y
   breaker general; la tabla de cargas tiene una fila por inversor.
4. Con batería: se dibuja en el inversor elegido y la ficha muestra la
   compatibilidad con ese inversor.
5. Con optimizadores: se dibujan en cada string y la ficha los marca por
   revisar; sin la opción no aparecen.
6. Sin multi-superficie, el diagrama y la ficha salen iguales que antes.
7. El unifilar ya no pide los módulos por superficie a mano cuando existen
   los grupos.
