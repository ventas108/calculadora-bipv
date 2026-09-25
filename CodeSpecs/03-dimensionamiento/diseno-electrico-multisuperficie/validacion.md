# Validación — Diseño eléctrico multi-superficie: inversores, MPPT y grupos de strings

**Estado:** implementación

Entorno: Python 3.12 (igual que CI), `bipv_python/requirements.txt`,
Streamlit 1.36.0; rama `claude/mejoras-bipv` sobre `main` `235d65dc`.

## Checklist de validación del módulo

### Fase A1

- [x] Pruebas nuevas en rojo con `main` `235d65dc`: no se pueden recolectar
      (`calculos.diseno_electrico_multisup` no existe).
- [x] Pruebas nuevas en verde: `32 passed`; Asistente `19 passed`.
- [x] Suites relacionadas (multi-superficie, Vista 3D, strings,
      persistencia, inversores, diseño eléctrico): `560 passed`.
- [x] Suite completa, mismo comando que CI (`python -m pytest tests/`):
      `1668 passed`, 0 fallidas, 12 min 8 s (sin contar la prueba del
      Asistente agregada después, que pasa sola).
- [x] `physics-guard` local: sin fórmulas ni constantes físicas del SDM
      modificadas.
- [x] Auditoría SDD sin documentos faltantes ni secciones incompletas.
- [x] Prueba de humo con `AppTest`. Datos: panel del proyecto ASP-ST1-T40,
      techo con SPR-E20-327, inversor del proyecto Growatt-MID15KTL3-X
      (Vdc 1100 V, MPPT activo 580–1000 V, 2 MPPT, 2 strings por MPPT) y
      temperaturas 5 / 55 / 65 °C. Resultados:
      1. Un inversor antiguo sin ficha carga como «Manual» sin errores.
      2. Al elegir «Inversor del proyecto» se guarda con `origen_ficha`
         proyecto y P AC 15.000 W de la ficha.
      3. El techo en MPPT 2 con N serie 20 queda 🔴 «Voc en frío 1369 V >
         Vdc máximo 1100 V». Rangos: ASP 8–8 y SPR 12–16. También salen
         🔴 las superficies con más módulos que área y el MPPT 1 con 4
         strings de 2 admitidos.
      4. Con N serie 16 el techo pasa a 🟢 en Voc (1094,9 / 1100 V) y Vmp
         (803,8 V en 580–1000 V), 🟡 por poco margen.
      5. Tras un rerun, N serie y MPPT conservan el valor escrito.
      6. Grupos guardados como G1 con espejo en los campos antiguos. Sin
         excepciones.
- [x] Prueba en producción de la fase A1 (casos C1–C6 con el proyecto real,
      inversor SG5.0RT; cálculos verificados a mano). Detectó la regla de la
      caja combinadora y la incoherencia de color del DC/AC, corregidas en A2.

### Fase A2

Rama `claude/mejoras-bipv` sobre `main` `5d5b98e0`.

- [x] Pruebas nuevas en rojo con `main` `5d5b98e0`:
      `test_diseno_electrico_fisico_grupos.py` no se puede recolectar
      (`aviso_estado_electrico` no existe); en `test_diseno_electrico_multisup.py`
      y `test_asistente_retrieval.py`, `21 failed, 51 passed` (caja
      combinadora, DC/AC, colores, resumen, área, invalidación y Asistente).
- [x] Pruebas nuevas y relacionadas en verde (diseño eléctrico, físico por
      grupos, panel por superficie, bypass/MPPT, publicación): `160 passed`;
      Asistente `22 passed`.
- [x] Suite completa, mismo comando que CI (`python -m pytest tests/`):
      `1719 passed`, 0 fallidas, 12 min 10 s.
- [x] `physics-guard` local: sin fórmulas ni constantes físicas del SDM
      modificadas.
- [x] Auditoría SDD sin documentos faltantes ni secciones incompletas.
- [x] Prueba de humo con `AppTest`. Datos: ASP-ST1-T40, inversor del
      proyecto Growatt-MID15KTL3-X (2 MPPT, 2 strings por MPPT), temperaturas
      5 / 55 / 65 °C; fachada Sur con G1 8 × 1 en MPPT 1 y techo con G1 8 × 1
      y G2 8 × 2 en MPPT 2. Resultados:
      1. «➕ Agregar grupo de strings» crea G2 y se conserva tras los reruns
         (antes de corregir `preservar_o_invalidar_campos_fisicos` se perdía).
      2. MPPT 2 con 3 strings y 2 entradas: 🟡 «Caben por corriente (3.0 A de
         33.8 A) … caja combinadora o conectores en Y», sin ningún 🔴.
      3. DC/AC 0,13 (2,02 kW de paneles para 15 kW): 🟡 «el inversor es más
         grande que los paneles…», igual en tabla y mensaje.
      4. Área usada: Sur 5,8 m² y techo 17,3 m² (8 y 24 módulos × 0,72 m²),
         base «instalada».
      5. Simplificado publicado con `multisup_estado_electrico` 🟡 y el banner
         «Energía publicada con 🟡 …».
      6. Bypass por grupo publicado: techo «G1 11,44 % (8 mód.) · G2 11,44 %
         (16 mód.)», pérdida de la superficie 11,44 %.
      7. Sección 6: aviso «'Techo' tiene(n) varios grupos de strings … no
         la(s) incluye».
      8. 🗑️ quita G2. Sin excepciones en ningún paso.
- [ ] Prueba en producción de la fase A2.

### Complemento de A2 antes de A3

Rama `claude/mejoras-bipv` sobre `main` `45362d79`.

- [x] Pruebas nuevas en rojo con `main` `45362d79`: `test_campos_editor.py`
      no se puede recolectar (`calculos.campos_editor` no existe); en las
      demás, `7 failed, 101 passed` (regla de largo, página, modo físico y
      Asistente).
- [x] Suite completa (`python -m pytest tests/`): `1730 passed`, 0 fallidas,
      12 min 15 s.
- [x] `physics-guard` local limpio; auditoría SDD sin faltantes.
- [x] Prueba de humo con `AppTest` (ASP-ST1-T40, Growatt-MID15KTL3-X; techo
      con G1 y G2 en MPPT 2):
      1. G2 con N serie 12 y G1 con 8: tabla de MPPT «N serie de los strings»
         🔴 «8 y 12 módulos», encabezado 🔴 y el mensaje «strings de distinto
         largo en el mismo MPPT (Techo · G2: 12 módulos, Techo · G1: 8
         módulos)… Solución: …».
      2. G2 de vuelta a 8: sin el 🔴; encabezado 🟡 (solo avisos).
      3. Cambios seguidos del mismo campo: azimuth 170 → 160 → 150 y N serie
         12 → 8 → 10 quedan cada uno como se escribió. Antes, el segundo
         cambio seguido volvía al valor anterior.

## Resultado

Fase A1 validada en producción. Fase A2 validada en local; su prueba en
producción se hace antes de empezar la fase A3, que se valida en su propio
Pull Request.
