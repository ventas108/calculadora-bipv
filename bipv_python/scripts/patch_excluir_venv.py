"""
Parche #126 — Excluir venv de git para evitar downtime en deploys
=================================================================
Ejecutar UNA VEZ en el servidor. Hace tres cosas:

1. Elimina bipv_python/venv/ del índice git (deja de rastrear el venv
   del repo de Replit que es incompatible con Ubuntu del servidor).
2. Verifica que .gitignore ya tenga bipv_python/venv/ excluido.
3. Crea/reemplaza scripts/setup_venv.sh — script para (re)crear el venv
   en el servidor de forma limpia.

Después de este parche, git pull / git reset --hard NUNCA tocan el venv
del servidor. Para recrear el venv manualmente: bash bipv_python/scripts/setup_venv.sh
"""
import sys, os, pathlib, subprocess, shutil, datetime, textwrap

BASE = pathlib.Path("/var/www/bipv/calculadora-bipv")
VENV = BASE / "bipv_python" / "venv"
GITIGNORE = BASE / ".gitignore"
SETUP_VENV = BASE / "bipv_python" / "scripts" / "setup_venv.sh"

if not (BASE / ".git").exists():
    print(f"[ERROR] No es un repositorio git: {BASE}")
    sys.exit(1)

# ── 1. Eliminar venv del índice git ──────────────────────────────────────────
print("\n[1] Eliminando bipv_python/venv/ del índice git...")
result = subprocess.run(
    ["git", "rm", "-r", "--cached", "--ignore-unmatch", "bipv_python/venv/"],
    cwd=BASE, capture_output=True, text=True
)
if result.returncode != 0:
    print(f"  [ADVERTENCIA] git rm retornó {result.returncode}: {result.stderr.strip()}")
else:
    removed = result.stdout.strip().count("\n") + (1 if result.stdout.strip() else 0)
    if removed:
        print(f"  [✓] {removed} archivos eliminados del índice.")
    else:
        print("  [OK] venv ya no estaba en el índice git.")

# ── 2. Verificar .gitignore ───────────────────────────────────────────────────
print("\n[2] Verificando .gitignore...")
if GITIGNORE.exists():
    gi = GITIGNORE.read_text(encoding="utf-8")
    if "bipv_python/venv/" in gi:
        print("  [OK] bipv_python/venv/ ya está en .gitignore")
    else:
        # Añadir al .gitignore del servidor
        gi += "\n# Python venv — no rastrear en git\nbipv_python/venv/\n**/venv/\n**/__pycache__/\n*.pyc\n"
        GITIGNORE.write_text(gi, encoding="utf-8")
        print("  [✓] bipv_python/venv/ añadido a .gitignore")
else:
    GITIGNORE.write_text("bipv_python/venv/\n**/venv/\n**/__pycache__/\n*.pyc\n", encoding="utf-8")
    print("  [✓] .gitignore creado con bipv_python/venv/")

# ── 3. Crear setup_venv.sh ────────────────────────────────────────────────────
print("\n[3] Creando scripts/setup_venv.sh...")
SETUP_VENV.write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    # setup_venv.sh — Crea/recrea el venv de Python en el servidor
    # Usar tras git reset --hard o primer despliegue.
    # Ejecutar desde /var/www/bipv/calculadora-bipv/
    set -e
    cd "$(dirname "$0")/../.."

    echo "[1/4] Desactivando venv anterior..."
    deactivate 2>/dev/null || true

    echo "[2/4] Eliminando venv antiguo..."
    rm -rf bipv_python/venv

    echo "[3/4] Creando venv limpio con Python del sistema..."
    python3 -m venv bipv_python/venv

    echo "[4/4] Instalando dependencias (~3-5 min)..."
    source bipv_python/venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r bipv_python/requirements.txt

    echo ""
    echo "✓ venv listo. Para activar:"
    echo "  source bipv_python/venv/bin/activate"
    echo "  pm2 restart streamlit-bipv"
"""), encoding="utf-8")
os.chmod(SETUP_VENV, 0o755)
print(f"  [✓] setup_venv.sh creado en {SETUP_VENV}")

# ── Resumen ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("[✓] Parche #126 aplicado.")
print("""
Desde ahora:
  • git pull / git reset --hard NUNCA toca bipv_python/venv/
  • Para recrear el venv: bash bipv_python/scripts/setup_venv.sh
  • El venv actual del servidor sigue funcionando sin cambios.
""")
