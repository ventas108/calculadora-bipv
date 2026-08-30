# Hallazgo: N/string=18 de Urabá no cumple el piso MPPT del Growatt con temperatura real

**Fecha:** 29-ago-2026
**Origen:** corrida real de "▶️ Optimizar N paneles/string" para el proyecto Agrivoltaico Urabá (panel JA Solar JAM66D46-720/LB, 2× Growatt MAX 100KTL3 LV), usando el TMY real de Urabá (lat 7,884° / lon -76,635°) recién cargado en ☀️ Recurso Solar — **confirmado por el usuario** que las temperaturas de diseño (T_realista=54,5°C, T_extremo=66°C) vienen de ese TMY real, no de un valor genérico.

## El hallazgo

El diseño documentado como "ya validado contra PVsyst" para Urabá usa **N=18 módulos/string** (306 módulos = 17 strings × 18). Corriendo el barrido eléctrico real de la app con las temperaturas reales de Urabá:

| N/string | Vmp realista (V) | Vmp extremo (V) | ¿Cumple Vmppt_activo_min=850V? |
|---|---|---|---|
| 18 | 686,7 | 665,4 | 🔴 NO — muy por debajo |
| 21 | 801,2 | 776,3 | 🔴 NO |
| 22 | 839,3 | 813,3 | 🔴 NO |
| 23 | 877,5 | 850,3 | 🟡 Al límite (margen <7,5%) |
| 24 | 915,7 | 887,2 | 🟡 Vmp extremo al límite |
| **25–28** | 953,8–1.068,3 | 924,2–1.035,1 | 🟢 **SÍ, con margen de seguridad real** |
| 29–30 | 1.106,4–1.144,6 | — | 🟡 Voc se acerca al Vdc_max (1500V) |

**N óptimo real (0 riesgos, mayor utilización MPPT): N=28.**

## Por qué el N=18 "ya validado" no detectó esto

El único test del repo que menciona explícitamente "N=18, proyecto real Urabá" (`tests/test_compatibilidad_string.py::test_uraba_18_en_serie_usa_vmppt_activo_min_no_vmppt_min`) usa como insumo **T_frio=-5,0°C, T_real=36,35°C, T_extremo=41,94°C** — estos son valores genéricos de Bogotá (los mismos usados para Teusaquillo), reutilizados como insumo de prueba para verificar una regla de código distinta (que la función usara `Vmppt_activo_min` en vez de `Vmppt_min`), **no una validación con el clima real de Urabá**. Urabá es zona costera tropical (Antioquia, cerca del mar Caribe) — mucho más caliente que Bogotá — así que el Vmp cae más de lo que ese test generic asumía, y N=18 (que en el test SÍ pasaba con las temperaturas de Bogotá) deja de ser válido con el calor real de Urabá.

La validación de producción ya publicada (`DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md`, E_ac=339.033 kWh/año bifacial vs PVsyst) valida el **modelo de producción/POA**, no pasó por este chequeo eléctrico de compatibilidad de string — son dos verificaciones independientes del mismo proyecto.

## Implicación real, no resuelta en esta sesión

Si N=28 es el string correcto para el clima real de Urabá, **306 módulos ya no es un número limpio** (306 ÷ 28 = 10,93, no es múltiplo entero) — el diseño de 17 strings × 18 módulos tendría que revisarse: o se cambia el N/string (con el conteo total de módulos ajustado a un múltiplo de 28), o se reconsidera si el proyecto real, tal como está construido/cotizado con N=18, necesita una revisión de compatibilidad eléctrica con el fabricante del inversor (el margen de 850V puede tener tolerancia real de operación que la app no modela, o el proyecto puede estar operando con un derateo aceptado).

**Esto no se resolvió ni se decidió en esta sesión** — es un hallazgo que requiere decisión de ingeniería/negocio (revisar con el diseño as-built real, o con Growatt directamente sobre el margen real de 850V), no un cambio de código. Documentado aquí para que quede como referencia auditable antes de dar por buena cualquier cifra de producción/financiero basada en el N=18 original para Urabá.
