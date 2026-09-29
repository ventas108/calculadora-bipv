# Propuesta — «Proyecto completo» cabe en el área y respeta el total de cadenas

**Estado:** validación

## Objetivo

Que «Proyecto completo» describa un sistema construible: nunca más módulos de
los que caben en el área útil, y exactamente las cadenas que el usuario
declara cuando las declara.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («si prepara la Spec para corregir
Proyecto completo»).

- Se cuentan **strings completos**, no inversores llenos:
  - con «N total de cadenas» declarado: ese número;
  - sin declararlo: los strings que caben en el área útil,
    ⌊área útil ÷ (N en serie × área del módulo)⌋.
- Inversores = ⌈strings ÷ (MPPT × strings por MPPT)⌉; los strings se reparten
  parejo entre inversores (11 en 2 → 6 + 5).
- Módulos = strings × N en serie; potencia y área salen de ahí.
- La cobertura se muestra sin tope; si lo declarado no cabe, aviso 🔴 con los
  m² que faltan (el cálculo sigue con lo declarado: es la decisión del usuario).
- DC/AC del proyecto = potencia DC total ÷ (inversores × potencia AC), además
  del inversor más cargado.
- Una sola función pura (`proyecto_completo`) para las dos secciones.
- Manual del Asistente con el caso Apartadó.

## Alternativas descartadas

- Redondear hacia abajo los inversores llenos: con 957 m² daría 1 inversor,
  280 módulos; deja sin usar área que sí cabe y no coincide con PVsyst.

## Fuera de alcance

- El reparto de cadenas por MPPT dentro de cada inversor (lo hace 🗺️ Vista 3D).
- `resolver_n_strings_tracker` (strings por MPPT) no cambia.
