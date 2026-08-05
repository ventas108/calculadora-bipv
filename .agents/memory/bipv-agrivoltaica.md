---
name: BIPV - factor de ocupación agrivoltaica
description: Cómo se maneja el % de terreno cubierto por paneles (cultivo bajo paneles) y qué páginas usan área bruta vs útil
---

# Factor de ocupación agrivoltaica

- Proyecto guarda `factor_ocupacion_pct` (5–100, clamp defensivo al cargar JSON) y `area_util_m2 = area_fachada_m2 × factor/100`.
- **Regla**: todo cálculo de cuántos paneles caben / producción / USD-m² debe usar el área ÚTIL, no `area_fachada_m2` (clave histórica = terreno bruto, no renombrar).
- Ya usan área útil: Proyecto (estimación ambos modos), Dimensionamiento (escalado de inversores + copy "área útil"), Presupuesto (densidad auto-clasificación), Reporte PDF (USD/m²).
- Vista 3D tiene modo granja (tipo "Granja fotovoltaica"): terreno verde L×L con filas Mesh3d espaciadas por pitch = ancho_colector/GCR, a 3 m si factor<100; se omiten building box y sun ray en ese branch.
- El slider GCR de Recurso Solar se inicializa desde factor_ocupacion_pct solo si no hay gcr guardado en la config bifacial; aviso si difieren >15 puntos.
- OJO: los merges de task agents pueden reintroducir attached_assets con tokens ya redactados — GitHub push protection bloquea el push; redactar con filter-branch sobre los commits sin publicar antes de reintentar.
- **Why:** proyecto agrivoltaico real (sandías bajo paneles a 3 m, 3000 m², ~30% ocupación); al 100% salían 1040 paneles sin opción de ajuste y el cultivo no recibiría sol.
