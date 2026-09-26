# Validación — Catálogos editables y potencia AC nominal de los inversores

**Estado:** implementación

Entorno: Python 3.12 (igual que CI), Streamlit 1.36.0; rama `claude/mejoras-bipv`
sobre `main` `9801ef3f`.

## Checklist de validación del módulo

- [x] Pruebas nuevas en rojo con `main` `9801ef3f`:
      `test_catalogo_inversores_pestana_editar.py` 5 fallidas (pestañas en
      blanco en los dos catálogos); `test_potencia_ac_inversor.py` y
      `test_edicion_catalogo_inversores.py` no se pueden recolectar (los
      módulos no existen). Con el cambio pasan todas.
- [x] Criterio 1: AppTest de las páginas 14 y 15 sin PDF: sin excepciones y
      con los botones de guardar y eliminar; guardia AST para todas las páginas.
- [x] Criterio 2: con una copia del Excel real, la corrección del Growatt
      MID15KTL3-X (200 V, 250 V, 2 strings, 27 A, 33,8 A) se guarda y el
      catálogo la devuelve; la fila «MID 15KTL3-X» recibe 15 kW.
- [x] Criterio 3: sin la columna, `P_ac_nom_W` es `None` (antes 19.200 W y
      21.600 W inventados); 105 de 111 inversores del Excel versionado.
- [x] Criterio 4: con la ficha real MID15~25KTL3-X, el extractor devuelve
      15 kW global y 15/17/20/22/25 kW por modelo.
- [x] Criterios 5 y 6: formulario con campo obligatorio; tabla con columna,
      aviso «105 de 111» y filtro (AppTest).
- [x] Criterio 7: mensaje en Vista 3D, Dimensionamiento y Producción.
- [x] `physics-guard` local limpio.
- [x] Suite completa (`python -m pytest tests/`): `1794 passed`, 0 fallidas, 17 min 22 s.
- [x] Auditoría SDD sin documentos ni secciones faltantes.

Pendiente tras el despliegue: corregir el Growatt desde la tabla en producción y
ver INV-2 con DC/AC 1,134 🟢 y 2/2 strings.

## Resultado

Aprobado para revisión: pruebas nuevas de rojo a verde, suite completa en verde,
`physics-guard` limpio y prueba de humo con AppTest de las dos páginas.
