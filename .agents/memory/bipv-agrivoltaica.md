---
name: BIPV - factor de ocupación agrivoltaica
description: Cómo se maneja el % de terreno cubierto por paneles (cultivo bajo paneles) y qué páginas usan área bruta vs útil
---

# Factor de ocupación agrivoltaica

- Proyecto guarda `factor_ocupacion_pct` (5–100, clamp defensivo al cargar JSON) y `area_util_m2 = area_fachada_m2 × factor/100`.
- **Regla**: todo cálculo de cuántos paneles caben / producción / USD-m² debe usar el área ÚTIL, no `area_fachada_m2` (clave histórica = terreno bruto, no renombrar).
- Ya usan área útil: Proyecto (estimación ambos modos), Dimensionamiento (escalado de inversores + copy "área útil"), Presupuesto (densidad auto-clasificación), Reporte PDF (USD/m²).
- Pendiente (tareas propuestas): Vista 3D y sincronización con el slider GCR de Recurso Solar (mismo concepto físico — hoy independientes).
- **Why:** proyecto agrivoltaico real (sandías bajo paneles a 3 m, 3000 m², ~30% ocupación); al 100% salían 1040 paneles sin opción de ajuste y el cultivo no recibiría sol.
