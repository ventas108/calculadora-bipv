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
- [ ] Prueba en producción de la fase A1: tabla «Diseño eléctrico» con el
      proyecto real y el rango de N serie del techo con su panel.

## Resultado

Fase A1 validada en local. Las fases A2 y A3 se validan en sus propios
Pull Requests.
