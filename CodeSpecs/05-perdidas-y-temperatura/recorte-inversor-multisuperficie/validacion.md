# Validación — Vista 3D: recorte de cada inversor en los modos simplificado y bypass

**Estado:** validación

## Checklist de validación del módulo

- [x] 10 pruebas nuevas en `tests/test_recorte_inversor_multisup.py`: en
  `main` el archivo no se puede cargar (no existe
  `calculos.recorte_inversores_multisup`); con el cambio pasan. Cubren la
  forma horaria, el inversor grande (sin cambio), el recorte exacto hora a
  hora contra un cálculo a mano, dos inversores, el string que cruza, el
  resumen por inversor, la energía publicada, la firma y la página.
- [x] Pruebas existentes de la cadena multi-superficie, el string que cruza,
  el diseño eléctrico y Vista 3D siguen verdes (336).
- [x] Prueba con la página real (AppTest, fachadas Este/Oeste de 13 kWp con
  un string que cruza, un inversor): 15 kW → publicado 14.920 kWh sin
  columna de recorte; 3 kW → «Recorte inversor» 23,9 % / 24,3 %, tabla
  «✂️ Recorte por inversor» 3.596 kWh (24,10 %, 2.940 h), publicado
  11.324 kWh = 14.920 − 3.596.
- [x] Mensaje DC/AC: prueba de referencia en
  `test_consistencia_sdm_entre_modulos.py` (0,97 🟠; 1,00 y 1,35 🟢 con
  «1.00–1.35»; 1,36 🟠; sin 0,95). Manual corregido a 1,00–1,35.
- [x] Suite completa de `bipv_python`.

## Resultado

Criterios 1 a 10 cumplidos. En espera de la revisión del PR.
