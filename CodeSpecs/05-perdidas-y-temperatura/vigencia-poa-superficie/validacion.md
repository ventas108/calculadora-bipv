# Validación — Vigencia de la POA por superficie

**Estado:** completado

Entorno: Python 3.12 (igual que CI), `bipv_python/requirements.txt`,
`pytest` 9.1.1, Streamlit 1.36.0; rama `claude/mejoras-bipv` sobre `main`
`38a56c81`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con el código previo: las dos pruebas nuevas no
      se pueden ni recolectar contra `main` `38a56c81` (`ImportError:
      cannot import name 'MOTIVO_POA_ERROR'`; `No module named
      'calculos.publicacion_multisuperficie'`).
- [x] Pruebas nuevas en verde: `26 passed` en
      `tests/test_vigencia_poa_superficie.py`.
- [x] Suites relacionadas (persistencia, adaptador, flujo físico end-to-end,
      página de transición, mapa de calor, selección de POA/invalidación,
      Asistente, sombra v2): `159 passed`.
- [x] Suite completa, mismo comando que CI (`python -m pytest tests/`):
      `1515 passed`, 0 fallidas, 17 min 08 s.
- [x] `physics-guard` local (`scripts/verificar_fisica_tiene_test.py --base
      origin/main`): sin fórmulas ni constantes físicas del SDM modificadas.
- [x] Prueba de humo de la página con `streamlit.testing.v1.AppTest` (TMY
      sintético, dos superficies): «⚡ Calcular POA» guarda la POA por `uid`
      y `firma_poa` en ambas superficies, la firma sobrevive al rerun;
      cambiar el tilt de una superficie retira solo su `firma_poa`, muestra
      el aviso «no tienen POA vigente» y deshabilita «Usar sistema
      multi-superficie»; sin excepciones en ningún paso.
- [x] Manual en Word regenerado y validado (`validate.py`: «All validations
      PASSED»).
- [x] Auditoría SDD (`scripts/sdd-agent.ts`) sin documentos faltantes ni
      secciones incompletas.

## Resultado

Implementación validada en local. Queda para cerrar la Spec como
`completado`: CI en verde en el Pull Request, aprobación humana y merge a
`main`, despliegue de la app Streamlit y una prueba en producción: calcular
la POA, cambiar el tilt de una superficie y ver el aviso y el botón
deshabilitado; recalcular y ver el aviso desaparecer.

## Cierre

Pull Request #45 integrado a `main` con CI en verde y aprobación humana; el aviso del mapa de calor que faltaba llegó en el #48 (Tests #221 en `main` en verde). Desplegado en Streamlit. Prueba en producción (24-sep-2026): al cambiar el tilt sin recalcular aparece el aviso «no tiene POA vigente (POA sin calcular)» y se deshabilita «Usar sistema multi-superficie»; al recalcular el aviso desaparece. En 🌞 Trayectoria Solar, «Fachada principal» a 85° sin POA calculada muestra el aviso de que los colores usan la POA general de ☀️ Recurso Solar.

Resultado final: Spec completada.
