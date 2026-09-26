# Propuesta — Catálogos editables y potencia AC nominal de los inversores

**Estado:** implementación

## Objetivo

Que los dos catálogos se puedan corregir desde la app y que la potencia AC
nominal de un inversor venga siempre de su ficha: si falta, la app lo dice y
explica dónde completarla, en vez de inventarla.

## Alternativas consideradas

1. **Mantener la estimación del 96 % con un aviso.** Descartada: el aviso no
   corrige la DC/AC, que seguiría falsa en Vista 3D, Dimensionamiento y el
   comparador; y el factor no sirve (las fichas usan relaciones FV/AC de 1,3
   a 1,5).
2. **Completar el Excel deduciendo la potencia del nombre del modelo**
   («MID15KTL3-X» → 15 kW). Descartada: también es una suposición y editar el
   Excel versionado choca con las correcciones hechas en el servidor.
3. **Quitar la estimación, pedir el dato y hacerlo editable** (recomendada).

## Alternativa recomendada

- Sin la columna «Potencia AC nominal (kW)», `P_ac_nom_W` queda `None`. Todos
  los consumidores ya lo toleran: la DC/AC queda «no evaluable» y la
  producción se calcula sin recorte, ahora con un mensaje que explica cómo
  completar el dato.
- El formulario pide «Potencia AC nominal (kW)», precargada por el extractor,
  y la exige salvo para «Cargador off-grid puro».
- La tabla editable incluye la columna «P AC nominal (kW)», un contador de
  inversores sin el dato y un filtro para verlos.
- La pestaña ➕ se vuelve una función que sale con `return`; la tabla de
  inversores compara filas por nombre de columna.

## Fuera de alcance

- Completar la potencia AC de los 104 inversores restantes: requiere la ficha
  de cada uno y se hace desde la tabla.
- Los respaldos con `P_dc_max_W` en 💰 Financiero (costo USD/kW) y 🔋 Baterías
  (potencia del inversor frente al banco), que no son la DC/AC.
