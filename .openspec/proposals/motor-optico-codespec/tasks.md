# Tasks: CodeSpec del Motor Óptico BIPV

## Revisión del contrato

- [x] Identificar página, motor puro y entradas desde Recurso Solar/Dimensionamiento/Proyecto.
- [x] Separar `poa_sin_termico_df` de `poa_efectiva_df` para evitar doble conteo en SDM.
- [x] Documentar IAM, soiling, autolavado, factor térmico, transparencia y k_BIPV.
- [x] Identificar consumidores: Producción, Financiero, Reporte PDF, IA, comparadores y Diagnóstico.
- [x] Registrar limitaciones: k=1.15 estimado y Faiman pendiente.

## Validación

- [x] Ejecutar suite focal del Motor Óptico en el venv real: 40 passed in 2.38s.
- [ ] Confirmar que todas las etapas de la cascada son monotónicas y no negativas.
- [ ] Confirmar que tau no altera `poa_efectiva` cuando el panel ya incorpora transparencia.
- [ ] Confirmar que Producción usa `poa_sin_termico_df` y conserva `k_BIPV`/NOCT.
- [ ] Confirmar invalidación completa ante ciudad/coordenadas nuevas.

## Implementación futura

- [ ] Evaluar modo opcional Faiman `Uc/Uv` con viento TMY, sin sustituir NOCT×k por defecto.
- [ ] Añadir registro reproducible por proyecto de parámetros y versión de catálogo.
- [ ] Pasar `status` a `validated` solo con evidencia fresca de pruebas.