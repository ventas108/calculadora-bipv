---
name: BIPV - git pull en servidor
description: Procedimiento correcto para sincronizar el servidor con origin/main, incluyendo conflictos de venv y páginas locales.
---

# BIPV — Sincronización git en servidor Digital Ocean

## Regla principal
El servidor (`/var/www/bipv/calculadora-bipv/`) tiene siempre cambios locales que NUNCA deben sobreescribirse sin stash. Las páginas con cambios locales frecuentes:
- `bipv_python/datos/ciudades_colombia.py` (tarifas y ciudades locales)
- `bipv_python/pages/1_🏠_Proyecto.py`
- `bipv_python/pages/2_☀️_Recurso_Solar.py`
- `bipv_python/pages/7_💰_Financiero.py`
- `bipv_python/pages/8_💼_Presupuesto.py`

## Procedimiento estándar (pull incremental)
```bash
git stash
git pull origin main
git stash pop
# si hay conflicto en páginas (los parches las actualizan de todas formas):
# git checkout --theirs "bipv_python/pages/<archivo_conflicto>.py"
```

## Procedimiento de reset total (ramas divergentes)
Cuando el historial diverge (ej: tras un force push desde Replit):
```bash
git stash
git fetch origin
git reset --hard origin/main   # 43k archivos — incluye venv de Replit (INCOMPATIBLE)
git stash pop
# Luego SIEMPRE reconstruir el venv (ver abajo)
```

## ⚠️ Problema crítico: venv en git
`bipv_python/venv/` está rastreado por git. El venv de Replit (NixOS) es incompatible con el servidor (Ubuntu). Después de cualquier `git reset --hard`, el venv queda roto:
```
-bash: /var/www/bipv/.../venv/bin/python3: No such file or directory
```

**Solución — reconstruir venv:**
```bash
deactivate 2>/dev/null || true
rm -rf bipv_python/venv
python3 -m venv bipv_python/venv
source bipv_python/venv/bin/activate
pip install --upgrade pip
pip install -r bipv_python/requirements.txt   # ~3-5 min
```

**Fix permanente pendiente:** agregar `bipv_python/venv/` a `.gitignore` (tarea #126).

## Conflictos típicos de stash pop
- `__pycache__/*.pyc` → siempre usar `--theirs` (se regeneran)
- páginas modificadas → usar `--theirs` + ejecutar los parches correspondientes
- `ciudades_colombia.py` → revisar antes de `--theirs`; puede tener ciudades locales

## Nombre del proceso PM2
```
pm2 restart streamlit-bipv      # id 3, puerto 8501
pm2 restart calculadora-bipv   # id 0, proceso separado
```
NO usar `streamlit-bipvcd` ni `streamlit-bipvUse` — esos no existen.

## Scripts de parche
Ubicados en `bipv_python/scripts/patch_*.py`. Todos son idempotentes.
Corren con el venv activado: `python3 bipv_python/scripts/patch_X.py`

## SameFileError en patch_vista3d
patch_vista3d.py usa `shutil.copy2(src, dst)`. Cuando src y dst son el mismo archivo (el reset ya trajo los archivos), lanza SameFileError. El script compara con `.resolve()` antes de copiar — si son el mismo, muestra `[OK]` y continúa.
**Why:** Los scripts de parche están en el mismo repo que los archivos destino. En el servidor, origen y destino son rutas distintas solo si los archivos se copian desde fuera del repo.
