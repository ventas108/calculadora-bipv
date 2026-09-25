# Tareas — Panel por superficie en Vista 3D multi-superficie

**Estado:** validación

Orden obligatorio: primero las pruebas (deben fallar con `main` `db7e96a6`),
luego el código, luego la validación completa.

## Pruebas nuevas (`bipv_python/tests/test_panel_por_superficie.py`)

- [x] `eficiencia_panel`: `ASP-ST1-T40` = 0,0875; área por `largo_mm ×
      ancho_mm`; sin potencia, sin área o η ≥ 100 % → error.
- [x] `panel_de_superficie`: proyecto por defecto, catálogo, mismo modelo del
      proyecto desde el catálogo, sin `panel_dict`, origen desconocido, ficha
      ausente.
- [x] `eficiencias_superficies`: η por superficie, errores separados,
      inactivas fuera.
- [x] Selector del editor (`seleccion_panel`, `opcion_panel_actual`): la
      ficha guardada se conserva si el modelo no cambia.
- [x] Criterio de aceptación: fachada 97,3 m², POA 1004, PR 0,78 → 6.667
      kWh/año con η 8,75 % (12.191,6 con el 16 % anterior).
- [x] Energía con paneles distintos: desglose con su η y total = suma;
      superficie activa sin η → error.
- [x] Strings: área del módulo de la superficie; panel distinto sin N serie →
      error; con el del proyecto se usa el N serie de Dimensionamiento.
- [x] Modo físico: cada superficie con su panel; huella `panel` cambia solo
      en la superficie editada; sin `panel_dict` solo falla la que lo sigue.
- [x] Invalidación: primera vez solo registra; cambio de panel de una
      superficie o del proyecto retira energía y resultados y conserva POA y
      sombra; el panel del proyecto no afecta a superficies con panel propio;
      firma estable del panel calibrado.
- [x] Persistencia: ida y vuelta con dos paneles; proyecto antiguo sin
      campos; panel distinto rechaza la carga; panel del proyecto distinto no
      bloquea si nadie lo sigue; origen desconocido rechazado.
- [x] Página (AST): sin `get("eta_panel"`; sin `ms_bp_panel_sel` ni
      `ms_mppt_panel_sel`; selector `spanel_{uid}`; `strings_superficie` con
      el indicador de panel del proyecto; Dimensionamiento invalida tras
      escribir `panel_dict`.
- [x] Asistente: la consulta «el techo lleva paneles de otra referencia»
      recupera la sección nueva.

## Implementación

- [x] `calculos/panel_superficie.py` (nuevo).
- [x] `multi_superficie.e_ac_total_multisup`: η por superficie.
- [x] `strings_superficie`: área por `area_modulo`; sin respaldo de
      Dimensionamiento para un panel distinto.
- [x] `adaptador_multisuperficie`: panel de cada superficie.
- [x] `persistencia_multisuperficie`: campos de panel por superficie.
- [x] `proyectos_manager`: reinicio de la huella de paneles al cargar.
- [x] Vista 3D: selector en el editor, η por superficie en resumen,
      publicación, vista, producción y bypass; bypass y MPPT sin selector
      común; invalidación por cambio de panel.
- [x] Dimensionamiento: invalidación al cambiar el panel del proyecto.
- [x] Asistente y manual (rev. 6, Markdown y Word).

## Validación

- [x] Pruebas nuevas en rojo con `main` y en verde con el cambio.
- [x] Suites relacionadas en verde.
- [x] Prueba de humo de la página con `AppTest`.
- [x] Suite completa de `bipv_python/tests` en verde.
- [x] Auditoría SDD sin bloqueos.
