# Spec — Indicadores de Financiero con la tarifa de excedentes

**Estado:** validación

## Alcance de la fase

App Streamlit (`bipv_python/`): métrica «Ahorro energía año 1» y sección
«🔋 Impacto de la batería en la rentabilidad» de `pages/7_💰_Financiero.py`.
Sin cambios en el flujo de caja (`calculos/financiero.py`). Evidencia del
27-sep-2026 con el proyecto de un cliente en Bogotá.

## Problema a resolver

El flujo de caja ya valora los excedentes a la tarifa de excedentes (Res.
CREG 174/2021), pero dos indicadores valoran toda la energía a la tarifa de
compra:

1. **«Ahorro energía año 1»** usa `e_ac × tarifa_cop`. En el caso del cliente
   mostraba 6.155 kWh × 1.200 = 7,39 M COP. Con 826 kWh de excedentes a
   800 COP/kWh el valor correcto es 5.329 × 1.200 + 826 × 800 = 7,05 M COP.
2. **«Impacto de la batería»** aparece aunque no haya batería: basta con que
   haya excedentes (`_e_autoconsumo != e_ac`). Su escenario «sin batería»
   valora toda la energía a la tarifa de compra y sale mejor que el mismo
   sistema: TIR 18,0 % contra 17,2 %. Además rotula «Energía adicional:
   −826 kWh/año», que son los excedentes y no una pérdida.

3. **Sistema mucho mayor que el consumo sin balance (26-sep-2026).** Con
   24,07 kWp (26.669 kWh/año) para 5.738 kWh/año de consumo y sin correr
   🔋 Baterías y Balance, Financiero valoró toda la energía a la tarifa de
   compra (800 COP/kWh, escrita en ese campo por error) y mostró TIR 28,9 %,
   aunque unos 20.900 kWh/año serían excedentes pagados a precio de bolsa.
   No había ningún aviso.
4. **Las tarjetas del CAPEX no suman el CAPEX bruto.** Faltaban los
   imprevistos: 23.480 + 3.550 + 10.545 = 37.575 USD contra 39.454.

## Contexto

- `frac_exportada` y `tarifa_excedentes_cop` salen de 🔋 Baterías y Balance y
  del campo «Tarifa de excedentes» de Financiero.
- Spec `06-analisis-financiero/sistema-multisuperficie`: el balance mensual
  usa el reparto mensual del sistema publicado.
- El balance (mensual u horario) reparte la producción en autoconsumo
  directo + excedente; la batería solo desplaza excedente a autoconsumo.
