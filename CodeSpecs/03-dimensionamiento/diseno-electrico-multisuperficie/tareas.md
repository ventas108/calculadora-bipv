# Tareas — Diseño eléctrico multi-superficie: inversores, MPPT y grupos de strings

**Estado:** implementación

Orden obligatorio por fase: primero las pruebas (deben fallar con el commit
previo), luego el código, luego la validación completa y la prueba en
producción. Una fase no empieza hasta que la anterior está integrada y
probada.

## Fase A1 — Modelo y validación, sin cambiar la energía

Pruebas nuevas (`bipv_python/tests/test_diseno_electrico_multisup.py`):

- [x] Migración: superficie antigua → G1; sin datos → sin grupos; grupos
      explícitos prevalecen; espejo de campos antiguos; inversor antiguo →
      manual; conjuntos cerrados de topología, clase y origen de ficha.
- [x] Normalización de fichas del Excel y del catálogo interno.
- [x] Temperaturas del proyecto frente a por defecto.
- [x] Rango de N serie del ejemplo de la Spec (ASP 3–8, SPR 5–14) y
      `None` sin ficha completa.
- [x] Grupo: verde con fórmula y fuente; Voc en frío > Vdc (criterio A1,
      1.369 V); Vmp bajo la ventana; inversor manual 🟡; grupo incompleto o
      topología no soportada 🔴; superficie sin grupos o sin panel 🔴.
- [x] MPPT: Isc total, strings por entrada, dos paneles 🔴, dos
      orientaciones 🟡.
- [x] Inversor: MPPT inexistente, relación DC/AC sumando todo el inversor,
      eficiencia obligatoria.
- [x] Superficie: módulos que no caben 🔴, cobertura baja 🟡 con área
      instalada; aviso de temperaturas por defecto; inactivas fuera y sin
      mutar entradas.
- [x] Página (AST): tabla «Diseño eléctrico», selector de ficha, MPPT por
      superficie y rango de N serie.
- [x] Asistente: la consulta sobre Voc en frío recupera la sección.

Implementación:

- [x] `calculos/diseno_electrico_multisup.py` (nuevo).
- [x] Vista 3D › 🔌 Inversores por superficie: ficha del inversor, grupo G1
      con MPPT, rango de N serie, tabla de diseño eléctrico y «Cómo se
      calcula cada valor».
- [x] Base de conocimiento del Asistente.

Validación:

- [x] Pruebas nuevas en rojo con `main` y en verde con el cambio.
- [x] Suites relacionadas y suite completa en verde.
- [x] Prueba de humo con `AppTest`.
- [ ] Prueba en producción de la fase A1.

## Fase A2 — Cálculos (por hacer, después de A1)

- [ ] Varios grupos por superficie en el editor.
- [ ] Modo físico por grupos con temperaturas del proyecto.
- [ ] Área instalada en la energía simplificada; bypass por grupo.
- [ ] Reglas hacia Financiero y `multisup_estado_electrico`.
- [ ] Invalidación por cambio eléctrico y persistencia de grupos.

## Fase A3 — Sección 6 unificada (por hacer, después de A2)

- [ ] Sección 6 con los MPPT de los grupos, sin selectores propios.
- [ ] Manual (Markdown y Word) y Asistente; cierre de la Spec.
