# Módulo 02 (Streamlit) — Recurso Solar

**Estado:** idea

## Alcance de la fase

App hermana `bipv_python` (`streamlit-bipv`, pm2): descarga de TMY vía PVGIS por
coordenadas, cálculo de POA (`calculos/solar.py::calcular_poa()`, incluye modelo
bifacial `infinite_sheds`), zona horaria y claves de estado expuestas a los
módulos siguientes. No incluye motor óptico (IAM/soiling) ni simulación de
producción.

## Problema a resolver

_(Pendiente de definir.)_

## Contexto

Ver [`../vision.md`](../vision.md) sección 2: el bug de timezone de
[DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md](../../../DIAGNOSTICO_TZ_TMY_SCRIPTS_URABA.md)
ya fue verificado como **ausente** en el motor real (`calcular_poa()`); solo
afectaba 4 scripts sueltos de análisis, ya corregidos. Hay una recomendación
abierta y distinta: el flujo agrivoltaico del manual del asistente salta la
página "Motor Óptico" (IAM), lo que sobreestima producción ~3% — pero eso
pertenece al módulo de producción/pérdidas, no a este.
