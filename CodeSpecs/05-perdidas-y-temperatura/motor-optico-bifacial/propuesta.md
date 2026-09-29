# Propuesta — Motor Óptico en modo bifacial

**Estado:** validación

## Objetivo

Que la cascada óptica conserve la energía (POA bruta − pérdidas = POA
efectiva) también con paneles bifaciales, y que la pantalla muestre factores
y avisos que se puedan comparar con un informe de la referencia estándar
internacional.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («prepara la spec con su PR para
corregir el Motor Óptico en modo bifacial»).

- Con POA bifacial (columnas `poa_front` y `poa_rear`), la cascada separa:
  - **Cara frontal** = `poa_front` (con el sombreado entre filas de
    `infinite_sheds`). Se le aplica el IAM con la misma proporción directa /
    difusa de las componentes clásicas de esa hora.
  - **Aporte trasero** = `poa_global − poa_front` (ya multiplicado por la
    bifacialidad). Se le aplica solo la IAM difusa (luz que llega de todos
    los ángulos), sin suciedad (la cara de abajo casi no se ensucia).
  - El factor térmico se aplica a la suma, como antes.
- Monofacial: exactamente la cascada de antes.
- Los factores promedio pasan a ser **ponderados por energía** (pérdida ÷
  energía de su etapa): su producto es el factor global y coinciden con los
  porcentajes de la cascada.
- Resultado nuevo `poa_trasera_optica` (hora a hora) y
  `aporte_trasero_kWh_m2` en el resumen; la página lo muestra.
- 🔆 Motor Óptico publica `poa_sin_termico_df` con `poa_front` coherente
  (global − aporte trasero), para que el recuadro «Aporte de la cara trasera»
  de 📊 Producción muestre el valor real.
- El aviso de la sección 5 depende de la inclinación: fachada (≥ 75°),
  superficie inclinada o superficie casi horizontal (granja o cubierta).
- Manual del Asistente con el caso Apartadó.

## Alternativas descartadas

- Aplicar el IAM de la cara frontal a la trasera: la luz trasera es reflejada
  por el suelo y llega de todos los ángulos; la IAM difusa es lo que la
  describe.
- Aplicar la suciedad también a la trasera: la referencia estándar
  internacional no lo hace y la cara de abajo casi no acumula polvo.

## Fuera de alcance

- Sombreado trasero y mismatch trasero (5 % y 10 % en el informe de
  Apartadó): la app no los tiene todavía; queda para otra Spec.
