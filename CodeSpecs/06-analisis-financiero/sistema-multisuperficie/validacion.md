# Validación — Financiero, Baterías y CO₂ con el sistema multi-superficie publicado

**Estado:** implementación

Entorno: Python 3.12 (igual que CI), Streamlit 1.36.0; rama `claude/mejoras-bipv`
sobre `main` `d20d8807`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con `main` `d20d8807`:
      `test_sistema_multisuperficie.py` no se puede recolectar
      (`calculos.sistema_multisuperficie` no existe); en
      `test_diseno_electrico_fisico_grupos.py`, `2 failed` (persistencia y
      publicación física del sistema).
- [x] Pruebas nuevas en verde: `test_sistema_multisuperficie.py` 17 pruebas;
      Asistente 24.
- [x] Suite completa (`python -m pytest tests/`): `1750 passed`, 0 fallidas,
      13 min 10 s; con el aviso fijo, `1755 passed`, 13 min 42 s.
- [x] `physics-guard` local limpio; auditoría SDD sin faltantes.
- [x] Prueba de humo con `AppTest` (escenario D5: fachada ASP-ST1-T40 6 × 3,
      techo SPR-E20-327 con G1 y G2 de 8 × 1; TMY sintético; **sin** 📊
      Producción; `P_stc_kW_sistema` 8,06 y `N_paneles_final` 128 de
      superficie única en la sesión):
      1. Vista 3D publica `multisup_sistema`: 6,3677 kWp, 34 módulos
         (ASP 18, SPR 16), completo; el reparto mensual suma la energía
         publicada.
      2. 💰 Financiero: «✅ Sistema multi-superficie — … · 6.37 kWp (34
         módulos)», sin «Producción no detectada»; costo por referencia de
         panel («Costo ASP-ST1-T40 (USD/módulo) · 18 módulos», «Costo
         SPR-E20-327 …»); módulos 34 × 65 USD en el CAPEX.
      3. 🔋 Baterías: «✅ Sistema multi-superficie — …, repartidos por mes»,
         sin «Producción no calculada».
      4. 🌿 CO₂: «Sistema: 6.37 kWp (34 módulos)».
      5. Sistema incompleto (techo sin grupos): 🔴 «No se calcula el análisis
         financiero… Sin grupos de strings en «Techo 1»…» y ninguna métrica.
- [x] Aviso fijo (prueba de humo con `AppTest`, después de publicar):
      cambiar Fachada G1 a N paralelo 2 muestra en «🔗 Integrar al análisis
      financiero» «ℹ️ La energía publicada en Financiero se retiró porque
      cambió el diseño eléctrico de «Fachada principal»…»; sigue en el rerun
      siguiente y desaparece al volver a publicar.
- [x] Guardar sin sombra 3D (hallado en D8): la prueba nueva reproduce el
      error de producción en rojo y pasa con la corrección; humo con
      `AppTest`: 🏠 Proyecto › 💾 Guardar con el escenario D5 sin sombra
      escribe el archivo y `restaurar_multisuperficie` lo carga con los
      grupos G1/G2 y `multisup_sistema` (34 módulos).
- [x] Prueba en producción: D5 y D6 aprobados (25-sep-2026).
- [x] H-D6 y regla 🔴 (humo con `AppTest`): con el estado publicado en 🔴,
      Financiero muestra «🔴 No se calcula el análisis financiero… describe un
      sistema que no se puede construir…» y ninguna métrica; con la energía
      retirada, Financiero, Baterías y CO₂ muestran «ℹ️ La energía
      multi-superficie de 🗺️ Vista 3D se retiró porque cambió el diseño
      eléctrico de «Fachada principal»…».
- [ ] Prueba en producción: D6, D7 y D8 con estas correcciones.

## Resultado

Validada en local. La prueba en producción se hace repitiendo D5.
