# Spec — 📊 Producción: recorte del inversor y γ bien presentados

**Estado:** validación

## Alcance de la fase

📊 Producción: la tabla «📋 Ver tabla de producción mensual completa» y la
nota de la fila «↳ Solo horas calientes» de la tabla de balance IEC 61724.
Solo presentación: ningún kWh cambia.

## Problema a resolver

Al revisar el proyecto Apartadó en el servidor (29-sep-2026):

1. La columna «Recorte inversor (kWh)» se ve sin formato
   (`4927.475563`), mientras las demás columnas se ven como `31,580`. La
   página formatea solo cuatro columnas; la del recorte quedó por fuera.
2. La nota de «↳ Solo horas calientes» dice `Tk_gamma=—%/°C` aunque el panel
   tenga γ = −0.29 %/°C. `perdidas_desglosadas` lee `res["Tk_gamma_pct"]`,
   pero ninguno de los dos motores (`simular_produccion_anual`,
   `simular_produccion_iv`) devuelve esa clave.

## Contexto

El recorte del inversor es el dato que explica la diferencia de Apartadó
contra la referencia estándar internacional (≈ 49,000 kWh/año con un solo
inversor de 100 kW); debe leerse sin esfuerzo.
