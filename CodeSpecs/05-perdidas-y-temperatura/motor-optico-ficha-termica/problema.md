# Spec — Motor Óptico: NOCT y γ coherentes con la ficha del panel

**Estado:** validación

## Alcance de la fase

🔆 Motor Óptico (auto-llenado y campos NOCT y γ) y 📊 Producción (NOCT que
recibe el modelo del panel), en superficie única.

## Problema a resolver

Apartadó contra la referencia estándar internacional (30-sep-2026): al abrir
el proyecto guardado, el Motor Óptico quedó con **NOCT 35 °C y γ −0,70 %/°C**
(valores viejos guardados con el proyecto). La ficha del JAM66D46-720/LB dice
**45 °C y −0,29 %/°C**. El auto-llenado solo corre cuando cambia el panel
(`mo_panel_ref`), así que no los corrigió, y nada lo avisaba.

📊 Producción inyecta el NOCT del Motor Óptico en el panel del modelo
(`_panel_sdm["NOCT"] = motor_optico_noct`): con 35 °C y k = 1,0 la pérdida
por temperatura bajó de ≈ 6,3 % a 3,8 % y E_ac subió ≈ 9.000 kWh en silencio
(351.269 frente a ≈ 342.000 kWh). El γ del Motor Óptico solo cambia la
pérdida térmica informativa de esa página (9,5 % en vez de ≈ 6 %).

## Contexto

El NOCT del Motor Óptico es la fuente de verdad de la temperatura de celda
en Producción (misma que usa la cascada óptica). El usuario puede cambiarlo
a propósito si tiene un dato medido, así que no se debe pisar sin avisar.
