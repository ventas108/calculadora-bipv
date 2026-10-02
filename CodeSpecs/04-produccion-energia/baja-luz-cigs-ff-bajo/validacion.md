# Validación — Baja luz de CIGS con factor de forma bajo

**Estado:** validación

## Checklist de validación del módulo

- [x] Las pruebas nuevas fallan con el código anterior.
- [x] Ficha de factor de forma bajo, con y sin N_s:
  - 97,0 % a 200 W/m² (antes ~110 %);
  - factor de idealidad > 1;
  - STC reproducido.
- [x] MiaSolé FLEX-03 90N sin cambios: factor de idealidad 1,053 y 97,0 %.
- [x] Objetivo inalcanzable (60 %): queda avisado en `_error_ajuste_200`.
- [x] AppTest: tras «Usar este panel», FF vs G usa el panel CIGS elegido. Con
  el código anterior la gráfica mostraba el ASP-ST1-T40.
- [x] Ficha real del 70N: 97,0 % a 200 W/m², factor de idealidad 1,56, FF 64,8 %
  y Pmax 70,2 W en STC (ficha 70 W, +5/−0).
- [x] El SDM estimado trae NOCT 48 °C; sin NOCT en la ficha no agrega la clave.
- [x] Guardia de física: los 5 motores dan lo mismo con el caso nuevo.
- [x] Suite completa de `bipv_python`: ver el PR.

## Resultado

Criterios cumplidos. En espera de la revisión del PR.
