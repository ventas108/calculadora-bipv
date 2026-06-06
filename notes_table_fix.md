# Problemas identificados en la tabla de Puntos de Análisis

## Captura del usuario:
1. **Valores de FS Geom y FS Clim en miles**: Se ven valores como 146.300, 134.600, 211.100, 345.700, etc.
   - CAUSA: El Excel usa punto como separador de miles (ej: "146.300" = 146300 en realidad es 0.146300)
   - O bien el Excel tiene valores como porcentajes (14.63%) que se están parseando mal
   - Revisando: "Area Sombreada" muestra valores como 58.3, 50, 41.69, 36430 (!)
   - El valor 36430 confirma que el separador decimal del Excel es COMA y el punto es separador de miles
   - Entonces "146.300" = 146,300 = 146300 (no es un decimal, es un entero con separador de miles)
   - PERO los FS deberían estar entre 0 y 1... 
   - Mirando mejor: FS Geom = 146.300 y FS Clim = 134.600 → estos son PORCENTAJES? No tiene sentido
   - Revisando el Excel original: los valores reales del Excel son decimales con coma
   - El problema es que parseFloat("146,300") en JS da 146 (ignora la coma)
   - Y "0,583" se parsea como 0 → pero en la captura FS muestra 0.583... 
   
   CONCLUSIÓN: El archivo Excel usa COMA como separador decimal (formato español/colombiano)
   - "58,3" → se lee como "58.3" por xlsx? No...
   - Mirando la fila de "Solsticio de Junio": Obstáculo = 36430, FS = 364.300
   - Esto confirma: xlsx lee "36.430" (con punto como miles) como string "36430" o "36.430"
   - Y luego parseFloat("36.430") = 36.43 → pero se muestra como 36430...
   
   REAL PROBLEMA: La librería xlsx está leyendo los números con formato de locale colombiano
   donde el punto es separador de miles y la coma es decimal.
   - El Excel tiene: 0,583 (FS) → xlsx lo lee como string "0,583" → parseFloat("0,583") = 0
   - O bien: 146,300 (FS_geom como %) → xlsx lo lee como "146,300" → parseFloat = 146
   
   SOLUCIÓN: Necesito normalizar los valores numéricos reemplazando coma por punto
   y eliminando puntos de miles antes de parseFloat.

2. **Tipografía muy grande**: Reducir tamaño de fuente de la tabla
3. **Datos no visibles**: Los campos de día, hora están cortados o no se ven bien

## Correcciones necesarias:
1. En parseRowsToPoints: normalizar números (quitar punto de miles, reemplazar coma por punto)
2. Reducir font-size de toda la tabla a text-xs
3. Hacer las celdas más compactas (menos padding)
4. Verificar que shadowedArea = fs * 100 no multiplique valores ya en porcentaje
