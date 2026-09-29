# Propuesta — Cantidad de inversores del proyecto elegida por el diseñador

**Estado:** validación

## Objetivo

Que la cantidad de inversores sea una decisión del diseño, la misma en todos
los módulos, y que Producción recorte con la potencia AC de todos ellos.

## Alternativa recomendada

Aprobada por el usuario el 29-sep-2026 («si prepara la Spec de inversores
con su PR»).

- **Campo nuevo** en 📐 Dimensionamiento: «Cantidad de inversores del
  proyecto (0 = la calcula la app)», clave `N_inversores_proyecto` (se guarda
  con el proyecto), ligada al modelo (`N_inversores_proyecto_ref`): al
  cambiar de inversor vuelve a 0.
- **Regla única** `resolver_inversores(strings, capacidad, fijado)`: sin
  fijar, el mínimo ⌈strings ÷ capacidad⌉; fijada, se respeta entre ese
  mínimo y un string por inversor, y si no es posible se ajusta con aviso 🟠.
- **Sugerencia** `inversores_para_dcac`: menos inversores con DC/AC ≤ 1,3;
  se muestra 💡 cuando la cantidad automática deja DC/AC más alto.
- **📊 Producción:** `escalar_p_ac_nom_por_inversores` redondea hacia
  arriba (igual que Dimensionamiento) y acepta la cantidad fijada
  (`inversores_fijados_vigentes`, solo si es del mismo modelo). La potencia
  AC total y el recorte hora a hora usan esa cantidad; la firma de vigencia
  ya incluye `n_inversores`.
- **Unifilar y RETIE:** siguen tomando `N_inv_total` (ahora la cantidad
  efectiva). **💼 Presupuesto:** cotiza `N_inv_total` inversores.
- Manual del Asistente, sección 90, con el caso Apartadó.

## Alternativas descartadas

- Calcular siempre los inversores por DC/AC 1,3: cambiaría en silencio todos
  los proyectos guardados; la sugerencia queda como 💡 y el diseñador decide.
- Leer `N_inv_total` en Producción sin validarlo: podría no corresponder al
  `N_paneles` o al inversor de Producción (bug del 29-ago-2026).

## Fuera de alcance

- 💰 Financiero estima el costo del inversor en USD por kW (sin cantidad);
  no cambia en esta fase.
- Multi-superficie (🗺️ Vista 3D define sus inversores por grupo).
