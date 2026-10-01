# Propuesta — Modelo IV de paneles BIPV de capa fina (CIGS) sin parámetros de laboratorio

**Estado:** validación

## Objetivo

Que un panel BIPV de capa fina con una ficha normal quede bien representado
en Motor IV, Producción y Vista 3D sin datos de laboratorio.

## Alternativa recomendada

Aprobada por el usuario el 1-oct-2026 («sí, prepara la Spec… y te envío este
panel flexible CIGS como ejemplo»).

1. `normalizar_tecnologia(texto)`: «CIGS», «CIS», «Copper Indium» → CIGS;
   «HJT», «TOPCon», «PERC» → Mono-Si; «a-Si», «Thin Film», «Otro» o vacío →
   Mono-Si **marcado como supuesto**, con aviso.
2. El estimador usa las constantes de CIGS (banda prohibida, factor de
   idealidad 1,35, resistencia en paralelo de capa fina) y coeficientes por
   defecto de CIGS cuando la ficha no los trae.
3. Sin número de celdas: se estima con Voc ÷ Voc por celda típica de la
   tecnología (punto medio del rango ya usado por `verificar_ns_halfcut`) y
   se marca como estimado.
4. Dato opcional «eficiencia relativa a 200 W/m² (%)» (columna
   `EficRel200Pct`): si está, se ajusta el factor de idealidad (con la
   resistencia en serie re-anclada a la potencia de la ficha) para que el
   modelo reproduzca ese valor a 25 °C. Para CIGS sin el dato se usa el −3 %
   (97 %) por defecto de la referencia estándar internacional: los valores
   típicos de CIGS sin ajuste daban 91,6 %. La resistencia en paralelo se
   probó primero y solo movía el resultado entre 91,1 y 92,0 %.
5. Motor IV muestra el origen: tecnología usada, celdas estimadas, ajuste a
   200 W/m² o aviso de tecnología supuesta.
6. Nombres del catálogo iguales a los del Excel real: «CIGS» y «Poli-Si»
   en el formulario, la tabla de edición y el lector de fichas (antes «CIS»
   y «Poly-Si»); los valores viejos se leen con el nombre nuevo
   (`tecnologia_catalogo`). Pedido del usuario: «es para que no haya más
   confusiones en el catálogo».
7. Manual del Asistente, sección 112.

## Alternativas descartadas

- Pedir I_L, I_o, Rs, Rsh y a_ref en el catálogo: las fichas no los traen.
- Constantes de a-Si en esta fase: no hay una ficha real para validarlas;
  queda marcado como supuesto y avisado.

## Fuera de alcance

- Lectura automática del dato de 200 W/m² desde el PDF (se escribe en la
  tabla de edición).
