---
name: BIPV Streamlit servidor y fixes
description: Calculadora BIPV en Digital Ocean Ubuntu 24.04, repo ventas108/calculadora-bipv, bugs corregidos y pendientes
---

## Servidor
- IP: 198.199.75.160 · hostname: bipv-colombia · dominio: calc.innovacionquimica.com.co
- App: Streamlit puerto 8501, PM2 nombre `bipv-streamlit` (id 1)
- Nginx HTTPS Let's Encrypt, vence oct 2026
- Repo: ventas108/calculadora-bipv · rama main
- **Path actual del repo:** `/var/www/bipv/calculadora-bipv` (confirmado agosto 2026)
- Path anterior (obsoleto): `/root/BIPV_Streamlit` — ya NO existe
- Venv: /var/www/bipv/calculadora-bipv/bipv_python/venv/
- Pages están en: /var/www/bipv/calculadora-bipv/bipv_python/pages/ (NO en /pages/ raíz)

## Catálogos Excel (fuente de datos dinámica)
- **Paneles**: `bipv_python/datos/paneles_catalogo.xlsx` → hoja `Paneles_Comparativa`, header fila 5 (pandas header=4)
  - Loader: `bipv_python/datos/catalogo_paneles_excel.py`
  - Filtro: columna `Incluir (Si/No)` == "Si" → 42 paneles válidos
  - Clave especial: `NsA (n×Ns)` = a_ref del modelo SDM
- **Inversores**: `bipv_python/datos/inversores_catalogo.xlsx` → hoja `Catalogo_Inversores`, header fila 3 (pandas header=2)
  - Loader: `bipv_python/datos/catalogo_inversores_excel.py`
  - Filtro: columna `Datos completos (Si/No)` == "Si" → 66 inversores válidos
  - Brand se extrae del campo `Archivo origen` (primer token antes de `_`)

## Para agregar panel/inversor nuevo
1. Abrir Excel en PC, agregar fila con Incluir/Datos completos = Si
2. `scp archivo.xlsx root@198.199.75.160:/var/www/bipv/calculadora-bipv/bipv_python/datos/`
3. La app lo muestra automáticamente (cache TTL=3600s, reiniciar PM2 para efecto inmediato)

## SCP desde PC Windows (PowerShell)
- Ejecutar SIEMPRE desde PowerShell local, NUNCA desde la sesión SSH
- `&&` no funciona en PowerShell antiguo — usar comandos separados
- Ruta del proyecto en PC: `C:\Users\Mauricio\Desktop\OPTIMIZADOR PARA CALCULOS BIPV\CALCULADORA RAPIDA INVERSOR ESTRING\`

## Git
- Rama activa: `main`
- Remote: https://github.com/ventas108/calculadora-bipv.git
- Cambios locales frecuentes en archivos de catalogo -> siempre `git stash` antes de `git pull`

## PM2
- Nombre del proceso: `bipv-streamlit` (id 1)
- `pm2 list` para confirmar nombre real
- Si no existe: `pm2 start "bipv_python/venv/bin/streamlit run bipv_python/app.py --server.port 8501 --server.address 0.0.0.0" --name bipv-streamlit && pm2 save`

## Bugs corregidos (commits en orden)
1. `7dca2bf4` — `pages/7_Financiero.py`: NameError tipo_cambio (mover definicion antes del bloque CAPEX)
2. `02f3916d` — `calculos/temperatura.py`: faiman() usaba noct= (eliminado en pvlib 0.9+) -> noct_sam()
3. `d3ed4fc2` — `calculos/modelo_iv.py`: singlediode() recibia ivcurve_pnts= (eliminado en pvlib 0.9+) -> curva IV manual con i_from_v() + np.linspace
4. `5b77df0d` — `pages/4_Dimensionamiento.py`: number_input sin key= no persistia T_min/T_cel/N_str en session_state -> agregar key="T_min_diseno" etc. con default 5.0 (no -5.0)
5. `efa3fc..` — `datos/ciudades_colombia.py`: Bogota T_min_diseno=-5.0 -> 5.0 (offset -19 C era outlier vs patron -9 a -15 C del resto de ciudades)
6. `b115ab0` — Selector paneles desde Excel (42 modelos)
7. `100edfa` — Loader inversores desde Excel creado
8. `10edfa1b` — Fix inversor lookup linea 39: usa obtener_inversor_excel() no seleccionar_inversor()

## Patron session_state en Streamlit multipage
- Proyecto.py guarda T_min_diseno desde CIUDADES[ciudad] solo al hacer clic "Guardar"
- Dimensionamiento.py lee session_state con get(key, default)
- Sin key= en number_input: el valor manual se pierde al navegar entre paginas
- Con key="nombre": Streamlit sincroniza widget <-> session_state automaticamente
- **Why:** la causa raiz siempre es el diccionario de ciudades; cambiar defaults sin corregir la fuente solo aplaza el problema

## pvlib version 0.9+ cambios importantes
- singlediode() NO acepta ivcurve_pnts -> usar i_from_v() manualmente
- temperature.faiman() NO acepta noct= -> usar noct_sam(noct=NOCT, ...)
- pvlib.inverter.pvwatts() es modelo LOCAL (no API web)

## PVWatts vs PVGIS (pendiente)
- El proyecto solo usa PVGIS actualmente
- Para comparar: llamar pvwatts/v8.json con tilt=0 -> solrad_annual (kWh/m2/anio) = GHI comparable
- Requiere API key gratuita de NREL: https://developer.nrel.gov/signup/
- Endpoint: GET https://developer.nrel.gov/api/pvwatts/v8.json?api_key=KEY&lat=X&lon=Y&system_capacity=1&dataset=intl&tilt=0&azimuth=180&array_type=0
