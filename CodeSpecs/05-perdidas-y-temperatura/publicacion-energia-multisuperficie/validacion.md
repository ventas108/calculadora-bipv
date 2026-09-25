# Validación — Publicación única de la energía multi-superficie

**Estado:** completado

Entorno: Python 3.12 (igual que CI), `bipv_python/requirements.txt`,
`pytest` 9.1.1, Streamlit 1.36.0; rama `claude/mejoras-bipv` sobre `main`
`38a56c81`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con el código previo:
      `tests/test_publicacion_energia_multisuperficie.py` no se puede
      recolectar contra `main` `38a56c81` (`No module named
      'calculos.publicacion_multisuperficie'`).
- [x] Pruebas nuevas en verde: `24 passed`; persistencia con origen
      (3 pruebas nuevas) en verde.
- [x] Suites relacionadas (persistencia, adaptador, flujo físico end-to-end,
      página de transición, mapa de calor, selección de POA/invalidación,
      Asistente, sombra v2): `159 passed`.
- [x] Suite completa, mismo comando que CI (`python -m pytest tests/`):
      `1515 passed`, 0 fallidas, 17 min 08 s.
- [x] `physics-guard` local: sin fórmulas ni constantes físicas del SDM
      modificadas.
- [x] Prueba de humo de la página con `streamlit.testing.v1.AppTest`:
      «Usar sistema multi-superficie» publica origen `simplificado`
      (E_ac 14.124,5 kWh/año, 50,0 m²); con energía de origen `fisico`
      vigente el botón no escribe y muestra «¿Reemplazarla por…?»;
      «✅ Sí, reemplazar» publica `simplificado` y retira el proyecto físico
      y la solicitud; «✖ Desactivar» deja la sesión sin claves de energía.
      Con un CSV de sombreado sintético: «⚡ Calcular bypass por superficie»
      sobre energía `simplificado` pide confirmación; al confirmar publica
      `bypass_csv` con total 12.512,9 kWh/año = suma del desglose, 50,0 m² y
      POA ponderada de 8760 h, y la tabla muestra «Activo en Financiero»;
      «✖ Cancelar» en una nueva solicitud no cambia el origen. Sin
      excepciones en ningún paso.
- [x] Invariantes verificados por prueba en los tres orígenes: suma de áreas
      = área total; suma del desglose = total en `simplificado` y
      `bypass_csv`; pérdida de bus = suma del desglose − total en `fisico`.
- [x] Auditoría SDD (`scripts/sdd-agent.ts`) sin documentos faltantes ni
      secciones incompletas.

## Resultado

Implementación validada en local. Queda para cerrar la Spec como
`completado`: CI en verde en el Pull Request, aprobación humana y merge a
`main`, despliegue de la app Streamlit y una prueba en producción de los
tres botones: el banner debe mostrar el origen y el reemplazo de un origen
distinto debe pedir confirmación.

## Cierre

Pull Requests #45 y #46 integrados a `main` con CI en verde y aprobación humana. Desplegado en Streamlit. Prueba en producción (24-sep-2026): el bypass con CSV pidió confirmación antes de reemplazar el origen vigente, publicó `bypass_csv` y la sección del bypass muestra el origen y el botón «✖ Desactivar modo multi-superficie».

Resultado final: Spec completada.
