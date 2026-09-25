# Validación — Estado de sombra visible por superficie

**Estado:** completado

Entorno: Python 3.12 (igual que CI), `bipv_python/requirements.txt`,
`pytest` 9.1.1, Streamlit 1.36.0; rama `claude/mejoras-bipv` sobre el commit
`3b53a1a0`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con el código previo: no se pueden recolectar
      contra `3b53a1a0` (`cannot import name 'ESTADOS_DIAGNOSTICO_SOMBRA'`).
- [x] Pruebas nuevas en verde: `31 passed`, incluidas las diez comprobaciones
      de coherencia con `construir_proyecto_desde_session_state`.
- [x] Suite completa, mismo comando que CI (`python -m pytest tests/`):
      `1588 passed`, 0 fallidas, 17 min 21 s.
- [x] `physics-guard` local: sin fórmulas ni constantes físicas del SDM
      modificadas.
- [x] Auditoría SDD (`scripts/sdd-agent.ts`) sin documentos faltantes ni
      secciones incompletas.
- [x] Hallazgo reproducido y corregido con `AppTest`: antes, justo después
      de «🌳 Calcular sombra», ninguna superficie conservaba su sombra; ahora
      ambas quedan con `sombra_cero_calculada` y la sombra sobrevive a los
      reruns.
- [x] Prueba de humo: la tabla muestra 🟢 para las superficies calculadas y
      🔴 `error_geometrico` con el punto concreto dentro del volumen; al
      cambiar el tilt de una superficie, esa fila pasa a
      `invalidada_geometria` con «Se retiró la sombra porque cambió tilt» y
      la otra sigue 🟢.

## Resultado

Implementación validada en local. Queda para cerrar la Spec como
`completado`: CI en verde en el Pull Request, aprobación humana, merge a
`main`, despliegue de Streamlit y una prueba en producción: calcular la
sombra de un proyecto real y comprobar que la tabla y «🧪 Preparar
comparación con modelo físico» coinciden.

## Cierre

Pull Request #45 integrado a `main` con CI en verde y aprobación humana. Desplegado en Streamlit. Prueba en producción (24-sep-2026): tras calcular la sombra, la tabla mostró el estado de cada superficie; al cambiar el azimuth del techo de 180° a 170° la tabla lo marcó `invalidada_geometria` con el motivo, coincidiendo con lo que acepta el modo físico. El editor de superficies que revertía el valor se corrigió en el #47.

Resultado final: Spec completada.
