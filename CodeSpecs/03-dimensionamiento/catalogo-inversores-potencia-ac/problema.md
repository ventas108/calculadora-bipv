# Spec — Catálogos editables y potencia AC nominal de los inversores

**Estado:** implementación

## Alcance de la fase

App Streamlit (`bipv_python/`): 🔌 Catálogo Inversores PDF, 📋 Catálogo
Paneles, el cargador `datos/catalogo_inversores_excel.py`, el extractor
`calculos/pdf_inversor_extractor.py` y los consumidores de la relación DC/AC
(🗺️ Vista 3D, 📐 Dimensionamiento, 📊 Producción). Evidencia verificada
contra `main` `9801ef3f` el 26-sep-2026, preparando el proyecto de un cliente
con el Growatt MID15KTL3-X.

## Problema a resolver

1. **La pestaña ✏️ Editar / Eliminar queda en blanco** en los dos catálogos.
   La pestaña ➕ Agregar desde PDF termina con `st.stop()` cuando no hay un
   PDF subido, y `st.stop()` detiene la página entera: no se puede corregir
   ningún inversor ni panel.
2. **«💾 Guardar cambios» del catálogo de inversores falla.** Compara filas
   con `getattr(fila, "Vdc_max_V")` sobre `itertuples()`, pero pandas
   renombra a `_1`, `_2`… las columnas con espacios o paréntesis:
   AttributeError en cada guardado.
3. **La potencia AC nominal se inventa.** Si la ficha no la trae en el Excel,
   el cargador usa 0,96 × «Potencia FV máx. recomendada». Growatt
   MID15KTL3-X: 22.500 W × 0,96 = 21.600 W, cuando la ficha dice 15.000 W; la
   fila duplicada «MID 15KTL3-X» mostraba 19.200 W (20.000 × 0,96). Con eso la
   relación DC/AC del techo del cliente salía 0,79 🟡 en vez de 1,13 🟢.
   105 de los 111 inversores del Excel del repositorio usan la estimación.
4. **El formulario no pide la potencia AC** y la tabla editable no la muestra,
   así que no hay cómo completarla. El extractor sí la lee de la ficha, pero
   solo para estimar la potencia FV máxima, y luego la descarta.

## Contexto

La relación DC/AC decide si el inversor está bien dimensionado (Spec
`03/diseno-electrico-multisuperficie`, fase A2) y la potencia AC limita la
producción (recorte). Quien usa la app está aprendiendo: un valor estimado que
se ve igual que uno de ficha lleva a conclusiones falsas sin ninguna pista.
