# Tasks: CodeSpec del módulo Sombras SketchUp

## Revisión del contrato

- [x] Identificar página, motor puro y adaptador Site Designer.
- [x] Documentar formatos de entrada y conversión de unidades.
- [x] Documentar ejes, rotación de norte y alineación con TMY.
- [x] Documentar CSV de salida y consumidores Mismatch/Producción/Financiero.
- [x] Documentar estado, firma de invalidación y ruta SVF.
- [x] Confirmar pruebas de equivalencia OBJ vs Site Designer y pruebas de SVF.

## Validación pendiente

- [ ] Ejecutar la suite focal del módulo en el venv real.
- [ ] Confirmar cobertura de invalidación cuando cambia cada entrada de la firma.
- [ ] Confirmar rechazo o advertencia para puntos duplicados, pesos negativos y fachadas vacías.
- [ ] Confirmar que `exportar_csv_fs()` mantiene columnas requeridas para `cargar_csv_fs()`.
- [ ] Confirmar que la fuente (`sketchup` / `externa_marsh`) llega a Producción y Reporte PDF.

## Implementación futura

- [ ] Añadir versión explícita al CSV si el contrato entre apps hermanas lo requiere.
- [ ] Añadir registro reproducible por proyecto: hash de geometría, TMY, parámetros y commit.
- [ ] Mantener separación entre sombra directa horaria y reducción difusa SVF.
- [ ] Cambiar `status` a `validated` solo con evidencia fresca de pruebas.