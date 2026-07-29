---
name: BIPV server git pull procedure
description: El servidor Digital Ocean tiene archivos localmente modificados; procedimiento seguro para git pull
---

## Regla
Antes de `git pull` en el servidor siempre hacer `git stash` para evitar el error "Your local changes would be overwritten".

## Archivos con cambios locales frecuentes
- `bipv_python/datos/catalogo_inversores_excel.py` — aliases añadidos en sesiones anteriores que pueden diferir del repo

## Procedimiento seguro
```bash
cd /var/www/bipv/calculadora-bipv
git stash
git pull
git stash pop   # si hay conflicto → git checkout <archivo> && git pull
pm2 restart bipv-streamlit
```

**Why:** Los alias en los loaders se editan directo en el servidor Y vía GitHub desde el repl; el servidor queda "ahead" de los cambios del repl causando abort en pull.

**How to apply:** Cada vez que se pide al usuario correr `git pull` en el servidor, incluir el `git stash` antes.
