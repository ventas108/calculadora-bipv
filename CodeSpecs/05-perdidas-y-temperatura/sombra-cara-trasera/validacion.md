# Validación — Sombra falsa con el sol detrás del plano del módulo

**Estado:** validación

Entorno: Python 3.12.3 (igual que CI), `bipv_python/requirements.txt`,
`pytest` 9.1.1; rama `claude/mejoras-bipv`, commit `0eb349a0`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con el código previo: `30 failed` en
      `tests/test_sombra_cara_trasera.py` contra `main` `9398948e`.
- [x] Pruebas nuevas en verde: `30 passed`.
- [x] 10 suites de la prueba de cierre multisuperficie + contrato + SVF +
      nuevas: `161 passed` (línea base de las 10 suites: `110 passed`).
- [x] Suite completa, mismo comando que CI
      (`PYTHONUTF8=1 python -m pytest tests/`): `1456 passed`, 0 fallidas,
      14 min 02 s.
- [x] `physics-guard` local
      (`scripts/verificar_fisica_tiene_test.py --base origin/main`): sin
      fórmulas ni constantes físicas del SDM modificadas.
- [x] Prueba TypeScript del contrato (`server/shadingEngineContract.test.ts`):
      `2 passed`.
- [x] Evidencia de la Spec repetida con el motor corregido:

  | Caso | Antes | Después |
  |---|---|---|
  | Torre 5 convexa, horas con sombra por cara (70,5° / 160,5° / 250,5° / 340,5°) | 2.172 / 2.021 / 2.225 / 2.302 | 0 / 0 / 0 / 0 |
  | Escena sintética de cierre, Fachada Sur, solo árbol (horas-punto) | 4.080 | 678 |
  | Misma escena con el edificio de la fachada (horas-punto) | 10.908 | 678 |

- [x] Horas con sol delante del plano idénticas con y sin orientación
      (prueba `test_sin_orientacion_conserva_comportamiento_previo_con_advertencia`).
- [x] Sombras persistidas de `sombras_3d` `v1` retiradas por
      `construir_y_recalcular_proyecto_fisico`; `v2` y otras fuentes
      conservadas.
- [x] Auditoría SDD (`scripts/sdd-agent.ts`) sin documentos faltantes ni
      secciones incompletas.

## Resultado

Implementación validada en local con la suite completa en verde. Queda para
cerrar la Spec como `completado`: CI en verde en el Pull Request, aprobación
humana y merge a `main`, despliegue en las dos copias del servidor
(Streamlit y app web) y la corrida real de Torre 5 en el Codespace con la
orientación de cada fachada. Esa corrida es la que actualiza la tabla
comparativa con PV·SOL; esta Spec no la sustituye.
