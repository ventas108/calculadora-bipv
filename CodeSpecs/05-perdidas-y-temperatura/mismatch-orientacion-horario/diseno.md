# Diseño — Mismatch por orientación hora a hora

**Estado:** validación

## Entradas

- TMY, coordenadas, configuraciones `[{azimuth, tilt, fraccion, label}]`,
  `albedo_suelo`, `bifacial_cfg` (si `bifacial_activo`).

## Salidas

- `calculos/mismatch.perdida_string_bypass(poas, fracciones) -> (ideal, string)`:
  arrays horarios de potencia relativa ideal y del string.
- `calcular_mismatch_orientacion(tmy, lat, lon, alt_m, configuraciones,
  albedo=0.20, bifacial=None)` agrega:
  - `factor_horario` (pd.Series: string ÷ ideal, 1 sin luz),
  - `factor_mismatch_pct` = pérdida ponderada por energía (%),
  - `factor_mismatch_pct_anual_aprox` (σ²/(2μ²) anual, referencia),
  - `modelo = "bypass_horario"`, `firma`.
- `firma_orientacion(configuraciones, tmy, albedo, bifacial) -> str`.
- `publicar_cascada_mismatch`: si `res_mismatch_or` trae `factor_horario`, los
  factores escalares no llevan la orientación y marca
  `mismatch_or_horario = True`.
- `factores_mismatch_produccion`: con `mismatch_or_horario`, multiplica el
  factor horario por el de la orientación.

## Tipos de datos

`numpy.ndarray`, `pandas.Series`, `dict`, `str`.

## Errores posibles

- Una sola orientación o sin luz: pérdida 0 y factor 1.
- Factor horario con otras horas que la POA de Producción: no se aplica y se
  avisa «recalcula el mismatch de orientación».

## Dependencias

Ninguna nueva.

## Criterios de aceptación

1. Casos a mano: 800/100 W/m² con 50/50 → string 400, ideal 450 (11.1 %);
   iguales → 0 %; 1000/900 → string 900, ideal 950.
2. Este/Oeste 50/50 en Apartadó: ≈ 14.9 % (antes 0.00 %).
3. Una orientación: 0 % y factor 1.
4. La POA de cada orientación usa el albedo y el panel bifacial del proyecto.
5. Producción recibe la orientación hora a hora y el escalar no la repite;
   un resultado anterior se usa como antes.
6. La página recalcula sola si cambian orientaciones, albedo, bifacial o TMY.
7. De punta a punta con las páginas: la irradiancia que entra al motor de
   Producción es POA × horizonte × orientación × suciedad, hora a hora.
8. El manual del Asistente lo explica con números.
