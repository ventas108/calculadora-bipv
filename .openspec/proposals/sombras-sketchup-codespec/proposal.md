# Proposal: CodeSpec del módulo Sombras SketchUp

## Objetivo

Formalizar el contrato de la página `bipv_python/pages/5a_🌳_Sombras_SketchUp.py` y del motor puro `bipv_python/calculos/sombras_3d.py`, incluyendo la entrada de modelos extraídos/exportados desde Solar Shading Calculator, SketchUp y Site Designer, el cálculo horario, el CSV compatible con Mismatch y el Sky View Factor difuso.

## Arquitectura actual

- La página Streamlit recibe un modelo 3D de obstáculos y puntos de análisis.
- `sombras_3d.py` normaliza la geometría a metros, alinea el norte, calcula posición solar con pvlib y ejecuta ray-casting con trimesh.
- `sitedesigner_marsh.py` traduce JSON de Andrew Marsh/Site Designer a la misma malla interna; no implementa una física paralela.
- El resultado horario se exporta con `FS_geometrico`, `Fachada`, `Punto` y trazabilidad opcional de obstáculos.
- Mismatch/Bypass consume el CSV; Producción y Financiero consumen el resultado derivado.
- SVF es una ruta separada: reduce difusa isotrópica y obliga a invalidar Recurso Solar para recalcular POA.

## Hallazgos iniciales

- Existe prueba de equivalencia OBJ SketchUp vs JSON Site Designer, incluida equivalencia con `northOffset`.
- Existen pruebas de contrato JSON/CSV, Site Designer y SVF difuso.
- La página invalida resultados cuando cambia la firma de archivo, unidades, norte, transparencia, ubicación, TMY o puntos.
- El cálculo bloquea si no existe TMY del proyecto para evitar desfase horario.
- El contrato de consumidor exige `FS_geometrico`; las nubes no pueden activar bypass.

## Alcance

Documentar y proteger el contrato existente antes de cualquier refactor o ampliación de formatos. Esta propuesta no cambia las fórmulas ni el formato público todavía.
