# Spec — Tensión máxima de sistema del módulo en el límite del Voc

**Estado:** validación

## Alcance de la fase

Límite del Voc en frío del string en 📐 Dimensionamiento, ⚖️ Comparador de
Inversores, 🗺️ Vista 3D (diseño eléctrico), 📋 Ficha RETIE, 📊 Producción y
📄 Reporte; dato nuevo en el 📋 Catálogo de Paneles.

## Problema a resolver

Teusaquillo (1-oct-2026): la ficha oficial del ASP-ST1-T40 (SolTech, vidrio
CdTe) dice «Voltaje máximo del sistema VSYS = 1.000 V». La app solo compara
el Voc en frío con la tensión DC máxima del inversor (1.100 V en el Sungrow
SG8.0RT y en el Growatt MID15KTL3-X). Con 8 módulos en serie el Voc en frío
es 988 V a 5 °C y 1.002 V a 0 °C: supera el límite del módulo y la app lo da
🟢 en todas las páginas. El optimizador propone 8 en serie.

La misma ficha limita el fusible de string a 2,0 A y no trae NOCT (el
51,1 °C del catálogo es una estimación por fórmula, según su propia nota).

## Contexto

La tensión máxima del sistema es el aislamiento del módulo (IEC 61730): un
string no puede superarla aunque el inversor aguante más. En módulos de
silicio suele ser 1.000 o 1.500 V; en vidrios BIPV es un límite real.
El catálogo de paneles (Excel) no tenía la columna; `datos/tecnologias_bipv.py`
tampoco. Los Excel del catálogo se editan en el servidor, así que el cambio
no los modifica en el repositorio.
