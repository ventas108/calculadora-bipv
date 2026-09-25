# Validación — Panel por superficie en Vista 3D multi-superficie

**Estado:** validación

Entorno: Python 3.12 (igual que CI), `bipv_python/requirements.txt`,
Streamlit 1.36.0; rama `claude/mejoras-bipv` sobre `main` `db7e96a6`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con `main` `db7e96a6`: no se pueden recolectar
      (`calculos.panel_superficie` no existe).
- [x] Pruebas nuevas en verde: `32 passed`.
- [x] Suites relacionadas (36 archivos de multi-superficie, Vista 3D,
      strings, persistencia y panel): `630 passed`.
- [x] Suite completa, mismo comando que CI (`python -m pytest tests/`):
      `1629 passed`, 0 fallidas, 16 min 20 s.
- [x] `physics-guard` local (`verificar_fisica_tiene_test.py --base
      origin/main`): sin fórmulas ni constantes físicas del SDM modificadas.
- [x] Auditoría SDD (`scripts/sdd-agent.ts`) sin documentos faltantes ni
      secciones incompletas.
- [x] Manual en Word regenerado y validado (`validate.py`: «All validations
      PASSED»).
- [x] Prueba de humo con `AppTest`, panel del proyecto `ASP-ST1-T40`, dos
      superficies (Sur 20 m², Techo 30 m²) y TMY sintético:
      1. El selector «Panel de esta superficie» arranca en «Panel del
         proyecto (ASP-ST1-T40)».
      2. Resumen POA: las dos superficies con η 8,75 %; Sur 1052 kWh/m² →
         1.435 kWh/año (= 1052 × 20 × 0,0875 × 0,78).
      3. Publicar: origen `simplificado`, desglose con `eta_panel` 0,0875.
      4. Cambiar el techo a `SPR-E20-327`: aviso «Cambió el panel…», energía
         retirada, sin aviso de POA no vigente; techo con η 20,06 %.
      5. Bypass y MPPT: «La superficie 'Techo' usa un panel distinto al del
         proyecto y no tiene N serie propio…».
      6. Un rerun no vuelve a retirar nada; al republicar, el desglose trae
         η 0,0875 y 0,20059. Sin excepciones en ningún paso.

## Auditoría posterior al merge (25-sep-2026)

- [x] Siete pruebas nuevas de los hallazgos H1–H4 (ver `implementacion.md`)
      en rojo con `main` `975b7a29` (6 fallidas; «renombrar» ya pasaba) y
      en verde con la corrección: `39 passed` en el archivo de la Spec.
- [x] Suite completa: `1636 passed`, 0 fallidas, 12 min 7 s.
- [x] Prueba de humo con `AppTest` repetida: mismos pasos 1–6 y, además,
      agregar una «Pérgola» con la energía publicada no la retira ni muestra
      «Cambió el panel…»; sin excepciones.

## Resultado

Implementación validada en local. Queda para cerrar la Spec como
`completado`: CI en verde en el Pull Request, aprobación humana y merge a
`main`, despliegue de Streamlit y una prueba en producción (Anexo A.6b del
manual): la fachada con ASP-ST1-T40 debe mostrar η 8,75 % y ≈ 6.667
kWh/año, y el techo con otro panel su propia η.
