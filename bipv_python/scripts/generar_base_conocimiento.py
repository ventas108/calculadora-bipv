# -*- coding: utf-8 -*-
"""Convierte el Manual de Usuario (docx) en la base de conocimiento markdown
que consume el Asistente (calculos/asistente.py). Ejecutar cuando el manual
cambie de versión y commitear el .md resultante."""
import glob
import os
import sys

from docx import Document

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(AQUI)
DESTINO = os.path.join(AQUI, "datos", "base_conocimiento_asistente.md")


def encontrar_manual() -> str:
    candidatos = sorted(glob.glob(os.path.join(RAIZ, "entregables", "MANUAL_CALCULADORA_BIPV_v*.docx")))
    if not candidatos:
        sys.exit("No se encontró el manual en entregables/")

    def version(ruta: str) -> tuple:
        import re
        m = re.search(r"_v(\d+)(?:\.(\d+))?_", os.path.basename(ruta))
        return (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)

    return max(candidatos, key=version)


def convertir(ruta: str) -> str:
    doc = Document(ruta)
    lineas = [f"# Manual de Usuario — Calculadora BIPV (fuente: {os.path.basename(ruta)})", ""]
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        estilo = p.style.name
        if estilo == "Heading 1":
            lineas += [f"## {t}", ""]
        elif estilo == "Heading 2":
            lineas += [f"## {t}", ""]
        elif estilo == "Heading 3":
            lineas += [f"### {t}", ""]
        elif estilo.startswith("List"):
            lineas.append(f"- {t}")
        else:
            lineas += [t, ""]
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    ruta = encontrar_manual()
    md = convertir(ruta)
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Base de conocimiento generada desde {os.path.basename(ruta)}: "
          f"{DESTINO} ({len(md):,} caracteres)")
