# Validación — «Proyecto completo» cabe en el área y respeta el total de cadenas

**Estado:** validación

## Checklist de validación del módulo

- [x] 15 pruebas nuevas en `tests/test_proyecto_completo.py`: en `main` el
  archivo no se puede ni cargar (la función no existe); con el cambio pasan.
- [x] Prueba de humo de 📐 Dimensionamiento (AppTest, catálogo real,
  Apartadó: 2,393 m² × 40 %, JAM66D46-720/LB, Growatt MAX 100KTL3 LV, N 28,
  1 string por MPPT):
  - sin declarar cadenas: 2 inversores, 308 módulos, 221.8 kWp, 957 m²,
    cobertura 100 %, reparto 6 + 5;
  - con 11 declaradas: lo mismo;
  - con 20 declaradas: 560 módulos, cobertura 181.7 % y aviso 🔴 «faltan
    782 m²»;
  - con la potencia AC de 100 kW: «Relación DC/AC del proyecto = 1.11» 🟢 e
    inversor más cargado 1.21; sin ella, el aviso de dónde completarla.
- [x] Compilación con `-W error::SyntaxWarning`.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 6 cumplidos. En espera de la revisión del PR.
