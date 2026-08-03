"""
patch_catalogo_inv_pdf.py
Verifica e instala las dependencias necesarias para la extracción de fichas
técnicas de inversores desde PDF (motor idéntico al de paneles #65/#129).

Ejecutar en el servidor:
    cd /var/www/bipv/calculadora-bipv
    source bipv_python/venv/bin/activate
    python bipv_python/scripts/patch_catalogo_inv_pdf.py
"""
import subprocess, sys, importlib

VENV_PY = "/var/www/bipv/calculadora-bipv/bipv_python/venv/bin/python"
PIP     = [VENV_PY, "-m", "pip", "install", "--quiet"]

def check(pkg, import_as=None):
    try:
        importlib.import_module(import_as or pkg)
        return True
    except ImportError:
        return False

print("=" * 60)
print("PATCH — Catálogo Inversores PDF (motor extracción)")
print("=" * 60)

# ── 1. pdfplumber ─────────────────────────────────────────────────────────────
if check("pdfplumber"):
    print("✅ pdfplumber ya instalado")
else:
    print("📦 Instalando pdfplumber…")
    r = subprocess.run(PIP + ["pdfplumber"], capture_output=True, text=True)
    print("  ✅ OK" if r.returncode == 0 else f"  ❌ ERROR: {r.stderr[:300]}")

# ── 2. openpyxl (para guardar_inversor_excel) ─────────────────────────────────
if check("openpyxl"):
    print("✅ openpyxl ya instalado")
else:
    print("📦 Instalando openpyxl…")
    r = subprocess.run(PIP + ["openpyxl"], capture_output=True, text=True)
    print("  ✅ OK" if r.returncode == 0 else f"  ❌ ERROR: {r.stderr[:300]}")

# ── 3. pdf2image + pytesseract (OCR para PDFs escaneados) ────────────────────
if check("pdf2image") and check("pytesseract"):
    print("✅ OCR (pdf2image + pytesseract) ya disponibles")
else:
    print("📦 Instalando pdf2image y pytesseract…")
    r = subprocess.run(PIP + ["pdf2image==1.17.0", "pytesseract==0.3.13"],
                       capture_output=True, text=True)
    print("  ✅ OK" if r.returncode == 0 else f"  ❌ ERROR: {r.stderr[:300]}")

# ── 4. Tesseract binario del sistema ─────────────────────────────────────────
import shutil
if shutil.which("tesseract"):
    result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
    ver = result.stdout.split("\n")[0] if result.stdout else "desconocida"
    print(f"✅ Tesseract binario disponible ({ver})")
else:
    print("📦 Instalando Tesseract (sistema)…")
    r = subprocess.run(
        ["apt-get", "install", "-y", "tesseract-ocr", "tesseract-ocr-spa", "poppler-utils"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        ver = result.stdout.split("\n")[0] if result.stdout else "instalado"
        print(f"  ✅ Tesseract instalado ({ver})")
    else:
        print(f"  ❌ Error instalando Tesseract: {r.stderr[:300]}")

# ── 5. Verificar que el extractor importa correctamente ──────────────────────
print("\n🔍 Verificando módulo de extracción de inversores…")
sys.path.insert(0, "/var/www/bipv/calculadora-bipv/bipv_python")
try:
    from calculos.pdf_inversor_extractor import pdf_disponible, ocr_disponible
    print(f"  ✅ pdf_inversor_extractor importado correctamente")
    print(f"     pdf_disponible  = {pdf_disponible()}")
    print(f"     ocr_disponible  = {ocr_disponible()}")
except Exception as e:
    print(f"  ❌ Error al importar pdf_inversor_extractor: {e}")

# ── 6. Verificar funciones de escritura en catálogo_inversores_excel ──────────
print("\n🔍 Verificando módulo de catálogo de inversores…")
try:
    from datos.catalogo_inversores_excel import (
        guardar_inversor_excel,
        eliminar_inversor_excel,
        actualizar_inversor_excel,
    )
    print("  ✅ guardar_inversor_excel   OK")
    print("  ✅ eliminar_inversor_excel  OK")
    print("  ✅ actualizar_inversor_excel OK")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("PATCH completado. Reinicia Streamlit:")
print("  pm2 restart streamlit-bipv")
print("=" * 60)
