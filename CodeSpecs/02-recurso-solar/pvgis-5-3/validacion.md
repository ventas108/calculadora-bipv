# Validación — Elegir la versión de PVGIS (5.2 o 5.3) en ☀️ Recurso Solar

**Estado:** validación

## Checklist de validación del módulo

- [x] 16 pruebas nuevas en `tests/test_pvgis_version.py`: en `main` fallan 15
  (la que confirma que sin versión se sigue usando 5.2 ya pasaba); con el
  cambio pasan todas.
- [x] Prueba de humo de ☀️ Recurso Solar (AppTest, PVGIS simulado,
  Apartadó 7.8830 / −76.6259): por defecto 5.3; la descarga pide 5.3 y
  muestra el recuadro con el año de cada mes; cambiar a 5.2 invalida el
  recurso con aviso y descarga 5.2; volver a 5.3 restaura desde la caché de
  5.3 sin descargar. Nombres de caché: 5.2 sin sufijo, 5.3 con `_pvgis53`.
- [x] `cargar_proyecto`: proyecto sin versión → 5.2; con 5.3 → 5.3; no hereda
  la versión del proyecto anterior.
- [x] Compilación con `-W error::SyntaxWarning`.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 6 cumplidos. En espera de la revisión del PR y de la prueba en
producción contra el PVGIS real.
