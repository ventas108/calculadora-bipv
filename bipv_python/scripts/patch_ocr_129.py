#!/usr/bin/env python3
"""
patch_ocr_129.py — Instala soporte OCR para PDFs escaneados (#129).

Qué hace:
  1. Instala librerías de sistema: tesseract-ocr, tesseract-ocr-spa, poppler-utils
  2. Instala paquetes Python en el venv: pdf2image, pytesseract
  3. Verifica/copia los archivos Python actualizados
  4. Imprime instrucciones finales

Uso:
  python3 bipv_python/scripts/patch_ocr_129.py
"""

import os, sys, shutil, subprocess
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[2]   # raíz del repo
BIPV   = ROOT / "bipv_python"
VENV   = BIPV / "venv"
PIP    = VENV / "bin" / "pip"

OK  = "[OK]"
ERR = "[ERR]"
INF = "[INFO]"

def run(cmd, check=True, capture=False):
    kw = dict(capture_output=capture, text=True) if capture else {}
    r = subprocess.run(cmd, shell=True, **kw)
    if check and r.returncode != 0:
        print(f"{ERR} Falló: {cmd}")
        if capture:
            print(r.stderr)
    return r

# ── 1. Dependencias de sistema ────────────────────────────────────────────────
print("\n[1] Instalando dependencias de sistema…")
run("apt-get install -y tesseract-ocr tesseract-ocr-spa poppler-utils")

# Verificar tesseract
r = run("tesseract --version", check=False, capture=True)
if r.returncode == 0:
    ver = r.stdout.strip().splitlines()[0] if r.stdout else "?"
    print(f"{OK} tesseract instalado: {ver}")
else:
    print(f"{ERR} tesseract no encontrado en PATH. Puede que necesites reiniciar la sesión.")

# ── 2. Paquetes Python ────────────────────────────────────────────────────────
print("\n[2] Instalando paquetes Python en el venv…")
if not PIP.exists():
    print(f"{ERR} No se encontró pip en {PIP}. ¿Está el venv creado?")
    sys.exit(1)

for pkg in ["pdf2image==1.17.0", "pytesseract==0.3.13"]:
    r = run(f"{PIP} install {pkg}", check=False, capture=True)
    if r.returncode == 0:
        print(f"{OK} {pkg} instalado.")
    else:
        print(f"{ERR} Error instalando {pkg}:\n{r.stderr}")

# ── 3. Verificar archivos Python ──────────────────────────────────────────────
print("\n[3] Verificando archivos actualizados…")

archivos = [
    BIPV / "calculos" / "pdf_panel_extractor.py",
    BIPV / "pages" / "14_📋_Catálogo_PDF.py",
    BIPV / "datos" / "catalogo_paneles_excel.py",
]

for a in archivos:
    if a.exists():
        size = a.stat().st_size
        print(f"{OK} {a.name} ({size:,} bytes)")
    else:
        print(f"{ERR} No se encontró: {a}")

# ── 4. Verificar importación OCR ──────────────────────────────────────────────
print("\n[4] Verificando importación OCR en Python del venv…")
py = VENV / "bin" / "python3"
test_cmd = (
    f"{py} -c \""
    "from pdf2image import convert_from_bytes; "
    "import pytesseract; "
    "print('OCR listo:', pytesseract.get_tesseract_version())"
    "\""
)
r = run(test_cmd, check=False, capture=True)
if r.returncode == 0:
    print(f"{OK} {r.stdout.strip()}")
else:
    print(f"{ERR} No se pudo importar OCR:\n{r.stderr.strip()}")
    print(f"{INF} Esto NO impide que la app funcione — el OCR es opcional.")

# ── 5. Listo ──────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("Parche #129 listo.")
print("Próximo paso:")
print("  pm2 restart streamlit-bipv")
print("\nCuando el PDF es escaneado la app mostrará:")
print("  • OCR activado → extracción automática con Tesseract")
print("  • OCR no disponible → formulario vacío para ingreso manual")
print("="*60)
