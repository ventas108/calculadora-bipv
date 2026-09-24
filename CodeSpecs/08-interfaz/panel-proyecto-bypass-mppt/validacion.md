# Validación — Panel y strings del proyecto en bypass y MPPT por superficie

**Estado:** validación

Entorno: Python 3.12 (igual que CI), `bipv_python/requirements.txt`,
`pytest` 9.1.1, Streamlit 1.36.0; rama `claude/mejoras-bipv` sobre el commit
`3b53a1a0`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con el código previo: no se pueden recolectar
      contra `3b53a1a0` (`No module named 'calculos.strings_superficie'`).
- [x] Pruebas nuevas en verde: `16 passed`.
- [x] Suite completa, mismo comando que CI (`python -m pytest tests/`):
      SUITE_COMPLETA.
- [x] `physics-guard` local: sin fórmulas ni constantes físicas del SDM
      modificadas.
- [x] Auditoría SDD (`scripts/sdd-agent.ts`) sin documentos faltantes ni
      secciones incompletas.
- [x] Prueba de humo con `AppTest` (panel del proyecto fuera de catálogo
      «Panel-Proyecto-X», N serie 6 en Dimensionamiento, superficie «Sur» con
      8 × 1 y «Techo» sin strings): ambos selectores arrancan en «Panel del
      proyecto (Panel-Proyecto-X)»; el bypass simula Sur con 8 × 1
      («configurado en la superficie») y Techo con 6 × 7 («N serie de
      Dimensionamiento, paralelo por área») y publica origen `bypass_csv`; el
      MPPT combinado corre con el mismo panel y strings y guarda su origen.

## Resultado

Implementación validada en local. Queda para cerrar la Spec como
`completado`: CI en verde en el Pull Request, aprobación humana, merge a
`main`, despliegue de Streamlit y una prueba en producción con el panel real
del proyecto: el bypass debe arrancar con él y mostrar los strings de cada
superficie.
