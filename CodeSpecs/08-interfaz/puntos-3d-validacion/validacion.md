# Validación — Validación visible de los puntos 3D por superficie

**Estado:** validación

Entorno: Python 3.12 (igual que CI), `bipv_python/requirements.txt`,
`pytest` 9.1.1, Streamlit 1.36.0; rama `claude/mejoras-bipv` sobre el commit
`3b53a1a0`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con el código previo: no se pueden recolectar
      contra `3b53a1a0` (`No module named 'calculos.puntos_3d'`).
- [x] Pruebas nuevas en verde: `25 passed`.
- [x] Suite completa, mismo comando que CI (`python -m pytest tests/`):
      `1588 passed`, 0 fallidas, 17 min 21 s.
- [x] `physics-guard` local: sin fórmulas ni constantes físicas del SDM
      modificadas.
- [x] Auditoría SDD (`scripts/sdd-agent.ts`) sin documentos faltantes ni
      secciones incompletas.
- [x] Prueba de humo con `AppTest` (TMY sintético, escena de prueba): los
      puntos de una sesión antigua guardados por nombre se migran al `uid`;
      la línea `8,5,0,2` aparece en rojo con su número de línea y deshabilita
      «🌳 Calcular sombra»; la línea con error sigue en el recuadro tras tres
      reruns; `8,5;0;2` se acepta; un punto dentro de la caja muestra
      «está DENTRO del modelo» antes de calcular.

## Resultado

Implementación validada en local. Queda para cerrar la Spec como
`completado`: CI en verde en el Pull Request, aprobación humana, merge a
`main`, despliegue de Streamlit y una prueba en producción con una escena
real de Site Designer (línea mal escrita, coma decimal y punto dentro del
volumen).
