# Spec — Motor Óptico en modo bifacial: la cara trasera no se pierde

**Estado:** validación

## Alcance de la fase

`calculos/motor_optico.cascada_optica` (cascada IAM → suciedad → térmico), la
página 🔆 Motor Óptico (resultados, factores promedio y aviso de la sección 5),
la POA que 🔆 Motor Óptico publica para 📊 Producción (`poa_sin_termico_df`)
y la cadena de pérdidas multi-superficie, que usa la misma cascada.

## Problema a resolver

Con un panel bifacial, ☀️ Recurso Solar calcula la POA global como
**cara frontal + bifacialidad × cara trasera** (pvlib `infinite_sheds`). La
cascada óptica toma la POA bruta de esa columna, pero arma la POA después del
IAM solo con las componentes de la cara frontal (`poa_direct` +
`poa_sky_diffuse` + `poa_ground_diffuse`). El aporte trasero desaparece sin
aparecer como pérdida:

- Proyecto agrivoltaico de Apartadó (comparación con la referencia estándar
  internacional, 29-sep-2026): POA bruta 1,861 kWh/m²; IAM −55, suciedad −62,
  térmica −90; la POA efectiva debería ser 1,654 y la pantalla muestra
  **1,497**. Faltan ≈ 157 kWh/m² (8.4 %), el aporte trasero.
- Reproducido con el motor de `main` (`5aab6241`), TMY sintético de
  Apartadó, inclinación 10°, bifacialidad 0.80: POA bruta 2,647.6, aporte
  trasero 228.0, y la suma de pérdidas deja un hueco de **223.8 kWh/m²**.

Consecuencias:

1. 📊 Producción recibe como irradiancia la POA después de IAM y suciedad
   (`poa_sin_termico_df`), así que **la granja pierde ≈ 8 % de energía** y el
   recuadro «Aporte de la cara trasera» de Producción sale en 0.
2. En la cadena multi-superficie, el aporte trasero perdido se contaba como
   «pérdida IAM» de las superficies bifaciales.
3. El aviso de la sección 5 («sobreestimación 19.6 % — significativa para una
   fachada vertical») se infla con esa pérdida y dice «fachada vertical» para
   cualquier inclinación (texto fijo).
4. «Factores promedio» muestra el promedio simple por hora (IAM 0.8942, 10.6 %)
   mientras la pérdida de energía por IAM es 3.0 %: confunde al comparar.

## Contexto

La cascada monofacial no tiene el problema (la POA global es igual a la suma
de sus componentes) y no debe cambiar.
