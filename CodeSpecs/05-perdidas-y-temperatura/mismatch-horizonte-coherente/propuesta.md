# Propuesta — 🔀 Mismatch: horizonte hora a hora y cascada coherente

**Estado:** validación

## Objetivo

Que cada pérdida de 🔀 Mismatch llegue a 📊 Producción **una sola vez**, en la
hora en que ocurre y sobre la parte de la luz que afecta; y que la pantalla
muestre exactamente lo que Producción va a aplicar.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («Spec A — Horizonte y coherencia de
Mismatch (puntos 1, 2, 3, 5, 6, 7, 8 y 9)», «verifica que todo entre limpio y
coherente al módulo de producción»).

1. **Horizonte físico:** en las horas con el sol detrás del obstáculo se
   quita solo la luz directa de la cara frontal (`poa_direct`); la difusa y el
   aporte trasero siguen. `factor_sombra_anual` pasa a ser esa pérdida ÷ POA.
2. **Hora a hora:** Producción multiplica la POA de cada hora por su factor de
   horizonte (calculado con la máscara y la POA vigente); el factor escalar
   (`factor_global_mismatch`, `factor_mismatch_sin_soiling`) ya no incluye el
   horizonte. Marca `mismatch_version = 2`: un estado anterior (sin la marca)
   se usa como antes, con aviso de recalcular, para no contar el horizonte dos
   veces.
3. **Bypass:** en las horas de horizonte el FS 3D se pone en 0 (no hay luz
   directa que sombrear: ya la quitó el horizonte). Se retira la casilla que
   combinaba el horizonte como sombra total.
4. **Suciedad con Motor Óptico:** el control de 🔀 Mismatch queda deshabilitado
   con el valor que aplica el Motor Óptico; la cascada lo muestra como «la
   aplica 🔆 Motor Óptico».
5. **Cascada:** solo las pérdidas sobre la irradiancia (horizonte, mismatch de
   orientación, suciedad); tabla aparte con las que Producción aplica sobre
   la potencia (calidad, mismatch, cableado DC y AC). «Factor sobre la
   irradiancia» en lugar de «Factor global PR».
6. **Vigencia:** el horizonte y el mismatch de orientación se recalculan solos
   si cambian sus datos o la POA.
7. **Valores por defecto en un solo lugar** (`DEFAULTS_MISMATCH`); Producción
   avisa cuando 🔀 Mismatch no se ha abierto y aplica 0 %.
8. **Bifacial sin Motor Óptico:** la suciedad solo sobre la cara frontal.
9. Producción guarda el factor que aplicó (`factor_mismatch_aplicado`) y el
   📄 Reporte PDF muestra ese.

## Alternativas descartadas

- Seguir con el máximo hora a hora en el bypass y quitar el horizonte de la
  base de Producción: la energía base (sin bypass) quedaría sin horizonte y
  la del bypass seguiría borrando la difusa.
- Aplicar los valores por defecto de 🔀 Mismatch en Producción aunque no se
  abra la página: cambiaría la firma de los proyectos guardados sin que el
  usuario lo decida.
- Descontar la difusa por el perfil de horizonte (factor de vista del cielo):
  pérdida pequeña; queda anotada para otra Spec.

## Fuera de alcance

- Mismatch por orientación hora a hora (Spec B).
- Fila propia del horizonte en el Loss Diagram de Producción.
