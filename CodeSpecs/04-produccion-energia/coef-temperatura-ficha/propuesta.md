# Propuesta — Coeficientes de temperatura de la ficha en el modelo IV

**Estado:** validación

## Objetivo

Que el SDM estimado reproduzca γ Pmax de la ficha siempre, y β Voc hasta
donde lo permite el modelo de un diodo con parámetros físicos, avisando lo
que no se alcance.

## Alternativa recomendada

- Paso final en `estimar_sdm_desde_ficha` para todos los métodos:
  - ajustar una Eg efectiva dentro de ±0,4 eV de la nominal de la
    tecnología;
  - en cada prueba, re-ajustar mu_gamma a γ de la ficha.
- Guardar `EgRef` en el SDM. El resolutor común (`calcparams_pvsyst`) la usa,
  así los 5 motores quedan coherentes.
- Informar β y γ del modelo frente a la ficha, con `_aviso_temperatura` si
  la diferencia en β supera 0,03 %/°C.
- R_s mínimo de 1 % de Vmp/Imp en el ajuste de baja luz.

## Alternativas descartadas

- Liberar mu_gamma para ajustar β: γ (la energía) se alejaría de la ficha.
- Eg sin límites: valores no físicos (por debajo de 0,6 eV).
- Corregir el Voc fuera del modelo: rompería la coherencia de la curva I-V
  entre motores.

## Fuera de alcance

- Términos de recombinación de capa fina (d2mutau) para paneles estimados.
- Corregir el Ns del catálogo (ASP-LAM3: 348 celdas da 0,52 V por celda);
  se informa al usuario.
