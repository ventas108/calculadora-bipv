# Spec — 🔀 Mismatch: horizonte hora a hora y cascada coherente con Producción

**Estado:** validación

## Alcance de la fase

`calculos/mismatch.py` (sombreado de horizonte, factores que se publican),
`calculos/mismatch_bypass.py` (horizonte en el bypass), la página
🔀 Mismatch (secciones 1 a 5), la entrada de 📊 Producción (POA y factor de
pérdidas, avisos) y el «Factor Mismatch aplicado» del 📄 Reporte PDF. No
cambia el mismatch por orientación (Spec B), ni las fórmulas del SDM.

## Problema a resolver

Auditoría del 29-sep-2026 pedida por el usuario tras el error bifacial del
Motor Óptico. Mediciones con el motor de `main` + #80, Apartadó (7.883,
−76.6259), TMY sintético de cielo despejado:

1. **Horizonte contado dos veces con el bypass.** Producción multiplica la
   irradiancia de todas las horas por (1 − factor de sombra anual) y, además,
   resta la pérdida del bypass, que por defecto («🏔️ Incluir el perfil de
   horizonte en el bypass», marcada) toma las horas de horizonte como sombra
   total. Sin Motor Óptico hay una tercera vez: el bypass parte de
   POA × `factor_global_mismatch`, que ya trae el horizonte.
2. **El horizonte borra también la difusa.** En las horas con el sol detrás
   del obstáculo se quita toda la POA. Con un horizonte de 15° en los cuatro
   puntos cardinales la app quita 1.85 % (837 h); la luz directa de esas horas
   es 0.93 %: la pérdida sale al doble.
3. **Factor anual en todas las horas.** La máscara hora a hora existe, pero a
   Producción llega un escalar: 3,632 horas sin sombra pierden igual 1.8 % y
   las sombreadas pierden de menos (temperatura, baja irradiancia y recorte
   del inversor salen con un perfil falso).
5. **Dos suciedades.** Con 🔆 Motor Óptico activo, la suciedad de 🔀 Mismatch
   no se usa y la página no lo dice (paso 4 de la comparación de Apartadó:
   suciedad 0 en Mismatch y el Motor Óptico restó 3.3 %).
6. **Cascada con filas en 0.** «Mismatch fabricación» y «Cableado DC» salen
   siempre en 0 (Producción las aplica sobre la potencia), no aparece la
   calidad y «Factor global PR» no es un PR.
7. **Resultados viejos.** Editar el horizonte o las orientaciones sin pulsar
   el botón deja vigente el resultado anterior; cambiar la POA (otra versión
   de PVGIS, otra orientación) tampoco lo invalida.
8. **Abrir la página cambia la energía.** Al abrir 🔀 Mismatch se guardan
   mismatch 1.0 % y cableado DC 1.5 %; sin abrirla Producción aplica 0 %, sin
   avisar.
9. **Bifacial sin Motor Óptico.** Suciedad y horizonte se aplican también al
   aporte trasero.

Además: el 📄 Reporte PDF muestra `factor_global_mismatch` como «Factor
Mismatch aplicado» también cuando Producción usó otro factor.

## Contexto

Producción firma la POA hora a hora (`poa_global_fingerprint`) y el factor
escalar: cualquier cambio de estos dos queda en la vigencia del resultado.
Los proyectos guardados no persisten `res_sombra` (se recalcula al abrir
🔀 Mismatch).
