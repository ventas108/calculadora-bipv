---
name: BIPV - login y monetización Fase 1
description: Sistema de usuarios/planes en calculos/auth.py; decisiones de seguridad y plan de monetización acordado
---

## Sistema de acceso (Fase 1, agosto 2026)
- `calculos/auth.py`: usuarios en SQLite `datos/usuarios.db` (gitignored, vive solo en el servidor). PBKDF2-SHA256. Roles admin/cliente; planes prueba/mensual/anual/ilimitado con `fecha_vencimiento`.
- Gate `requerir_login()` insertado en app.py (tras `bloquear_traduccion()`) y en TODAS las páginas justo después de `import streamlit as st`. Páginas nuevas DEBEN incluirlo.
- Panel admin: `pages/17_🔐_Administracion.py` (`requerir_login(solo_admin=True)`).

## Decisiones de seguridad (auditadas)
- Sesión persistente por token en query param `?s=` (Streamlit 1.36 no tiene cookies nativas). Mitigación aceptada: token de 7 días, **rotado en cada restauración**, hash en DB; revocación se verifica en CADA rerun (cambio de clave/desactivación cierra sesiones vivas).
- Bootstrap del primer admin protegido por código aleatorio de un solo uso en `datos/codigo_configuracion.txt` (leer por SSH; se borra al crear el admin). Sin esto cualquier visitante se volvería admin en el primer arranque.
- `extender_vencimiento` usa BEGIN IMMEDIATE (extensiones concurrentes no pierden días); si el vencimiento está en el futuro, suma sobre esa fecha, no sobre hoy.
- Pruebas: `scripts/test_auth.py` (28 checks, sin streamlit).

## Fase 2 (hecha)
- `calculos/pagos.py`: config comercial en `datos/config_pagos.json` (gitignored). Links de pago SOLO con hostname exacto en `DOMINIOS_WOMPI` (validados al guardar Y al cargar — anti-phishing incluso si alteran el JSON a mano). Botones aparecen en pantalla de vencido y sidebar (≤3 días).
- `scripts/setup_venv.sh` reconstruye el venv del servidor (`--rebuild`); el venv nunca va a git. Procedimiento documentado en replit.md.

## Plan de monetización acordado con el usuario
- Precio recomendado: $150.000 COP/mes o $1.400.000/año por empresa; "precio de fundador" $100.000/mes primeros 10 clientes. Trial 14 días por invitación (cuenta tipo prueba en el panel admin).
- Fase 2: links de pago Wompi + activación manual en el panel. Fase 3: webhook Wompi. La app corre en su Digital Ocean — integración directa con API Wompi, NO integraciones Replit.
- **Why:** el usuario quiere vender por fuera de Google (0% comisión); Wompi ~2,65%+IVA, transferencia 0%.
