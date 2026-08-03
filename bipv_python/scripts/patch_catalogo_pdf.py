"""
Parche #65 — Agregar paneles al catálogo desde ficha técnica PDF
================================================================
Instala pdfplumber y verifica los tres archivos nuevos:

  A) calculos/pdf_panel_extractor.py    — motor de extracción regex + pdfplumber
  B) páginas/14_📋_Catálogo_PDF.py      — página Streamlit con upload + formulario
  C) datos/catalogo_paneles_excel.py    — añade función guardar_panel_excel()

No modifica archivos existentes: todos los cambios son aditivos.
"""
import sys, pathlib, subprocess

BASE  = pathlib.Path("/var/www/bipv/calculadora-bipv/bipv_python")
VENV  = BASE / "venv"
PIP   = VENV / "bin" / "pip"

# ── 1. Instalar pdfplumber ─────────────────────────────────────────────────────
print("\n[1] Instalando pdfplumber...")
if not PIP.exists():
    print(f"  [ERROR] No se encontró pip en {PIP}")
    print("  Ejecuta primero: bash bipv_python/scripts/setup_venv.sh")
    sys.exit(1)

try:
    result = subprocess.run(
        [str(PIP), "install", "pdfplumber==0.11.4", "--quiet"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"  [ERROR] pip install falló: {result.stderr.strip()}")
        sys.exit(1)
    # Verificar instalación
    import importlib.util
    spec = importlib.util.find_spec("pdfplumber")
    if spec is None:
        raise ImportError("pdfplumber no encontrado tras instalación")
    print("  [✓] pdfplumber instalado correctamente.")
except subprocess.TimeoutExpired:
    print("  [ERROR] Timeout al instalar — verifica conexión a internet.")
    sys.exit(1)
except ImportError:
    # Intentar verificar directamente
    venv_python = VENV / "bin" / "python3"
    r2 = subprocess.run(
        [str(venv_python), "-c", "import pdfplumber; print(pdfplumber.__version__)"],
        capture_output=True, text=True
    )
    if r2.returncode == 0:
        print(f"  [✓] pdfplumber {r2.stdout.strip()} disponible en venv.")
    else:
        print(f"  [ADVERTENCIA] No se pudo verificar pdfplumber: {r2.stderr.strip()}")

# ── 2. Verificar archivos nuevos ───────────────────────────────────────────────
ARCHIVOS = {
    "A": BASE / "calculos" / "pdf_panel_extractor.py",
    "B": BASE / "pages" / "14_📋_Catálogo_PDF.py",
}

print("\n[2] Verificando archivos nuevos...")
todo_ok = True
for tag, path in ARCHIVOS.items():
    if path.exists():
        size = path.stat().st_size
        print(f"  [{tag}] [✓] {path.name}  ({size:,} bytes)")
    else:
        print(f"  [{tag}] [ERROR] No encontrado: {path}")
        print(f"       Ejecuta: git pull origin main")
        todo_ok = False

# C: verificar guardar_panel_excel en catalogo_paneles_excel.py
F_CAT = BASE / "datos" / "catalogo_paneles_excel.py"
if F_CAT.exists() and "guardar_panel_excel" in F_CAT.read_text(encoding="utf-8"):
    print("  [C] [✓] guardar_panel_excel() presente en catalogo_paneles_excel.py")
else:
    print("  [C] [ERROR] guardar_panel_excel() no encontrado en catalogo_paneles_excel.py")
    todo_ok = False

print("\n" + "=" * 60)
if todo_ok:
    print("[✓] Parche #65 listo.")
    print("""
Próximo paso:
  pm2 restart streamlit-bipv

Uso:
  1. Navega a 📋 Catálogo PDF en el menú lateral
  2. Sube la ficha técnica PDF de cualquier panel
  3. Verifica los valores extraídos
  4. Clic en "Guardar en catálogo"
  5. El panel aparece inmediatamente en Dimensionamiento
""")
else:
    print("[ERROR] Algunos archivos faltan. Ejecuta:")
    print("  git pull origin main")
    print("  python3 bipv_python/scripts/patch_catalogo_pdf.py")
    sys.exit(1)
