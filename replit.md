# [Project name]

_Replace the heading above with the project's name, and this line with one sentence describing what this app does for users._

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

_Populate as you build — short repo map plus pointers to the source-of-truth file for DB schema, API contracts, theme files, etc._

## Architecture decisions

- La calculadora de sombreado seguirá una arquitectura híbrida: React/TypeScript para interfaz, carga de archivos y visualización; Python para el motor solar oficial, reproducible y compatible con BIPV.
- Antes de migrar cálculos se hará un inventario del código TypeScript actual. Se decidirá explícitamente qué queda como previsualización en React, qué pasa a Python y cuál será la única fuente oficial de resultados.
- La salida oficial será `FS_geometrico` con metadatos trazables, reutilizando el contrato y la cadena existentes de BIPV para Mismatch, bypass, Vista 3D y producción.

## Product

_Describe the high-level user-facing capabilities of this app once they exist._

## User preferences

- Priorizar una programación asertiva, coherente, limpia y verificable.
- Antes de modificar, revisar dependencias y reutilizar la lógica existente; evitar duplicaciones y soluciones improvisadas.
- Entregar cambios funcionales, con validaciones y pruebas proporcionales al riesgo.

## Gotchas

### Despliegue de la app BIPV Streamlit (servidor externo)

La app Streamlit (`bipv_python/`) corre en un servidor Ubuntu propio (Digital Ocean, `/var/www/bipv/calculadora-bipv`, proceso PM2 `streamlit-bipv`). El venv del servidor vive en `bipv_python/venv/` y **NUNCA debe estar en git** (está en `.gitignore`): el venv de Replit/NixOS no funciona en Ubuntu y sobreescribirlo deja la app caída.

**Actualización incremental (lo normal, cada parche):**
```bash
cd /var/www/bipv/calculadora-bipv && git pull && pm2 restart streamlit-bipv
```
El venv no se toca. Si el servidor tiene cambios locales, usar `git stash` antes de `git pull`.

**Primer despliegue, o si el venv se dañó / cambió `requirements.txt`:**
```bash
cd /var/www/bipv/calculadora-bipv && git pull
bash bipv_python/scripts/setup_venv.sh   # recrea el venv e instala requirements (~3-5 min)
pm2 restart streamlit-bipv
```

Nunca usar `git reset --hard` + borrado de untracked (`git clean -xdf`) en el servidor: eliminaría el venv. Si hay que forzar sincronización, usar `git fetch && git reset --hard origin/main` (no toca archivos ignorados) y solo reconstruir el venv con el script si la app no arranca.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
