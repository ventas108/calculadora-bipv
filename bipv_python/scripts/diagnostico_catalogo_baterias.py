#!/usr/bin/env python3
"""
CLI de diagnóstico del catálogo de baterías.

Uso (desde bipv_python/, con el venv activo):
    python scripts/diagnostico_catalogo_baterias.py

Imprime el mismo diagnóstico que el expander "🔍 Diagnóstico detallado del
catálogo" de la página 11: hoja usada, modelos cargados, columnas no
reconocidas, modelos incompletos y modelos duplicados (#123).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datos.catalogo_baterias_excel import diagnostico_catalogo, excel_mtime  # noqa: E402


def main() -> int:
    info = diagnostico_catalogo(_mtime=excel_mtime())

    if info.get("error"):
        print(f"✗ ERROR: {info['error']}")
        return 1

    print(f"Hojas disponibles : {info.get('hojas_disponibles')}")
    if "hoja_usada" not in info:
        print(f"✗ {info.get('estado', 'Hoja de baterías no encontrada')}")
        return 1

    print(f"Hoja usada        : {info['hoja_usada']}")
    print(f"Modelos cargados  : {info.get('modelos_cargados', 0)}")
    for n in info.get("nombres", []):
        print(f"  · {n}")

    no_map = info.get("columnas_no_mapeadas", [])
    if no_map:
        print(f"\n① Columnas del Excel sin alias en el loader ({len(no_map)}):")
        for c in no_map:
            print(f"  · {c}")

    sin_col = info.get("campos_sin_columna_excel", [])
    if sin_col:
        print(f"\n② Campos internos sin columna en el Excel ({len(sin_col)}):")
        for c in sin_col:
            marca = "CRÍTICO" if c.get("critico") else ("importante" if c.get("importante") else "opcional")
            print(f"  · {c['campo']} [{marca}] — sugeridas: {c['columnas_sugeridas']}")

    incompletos = info.get("modelos_incompletos", [])
    if incompletos:
        print(f"\n③ Modelos con campos críticos vacíos ({len(incompletos)}):")
        for m in incompletos:
            falt = ", ".join(m["campos_faltantes"]) or "—"
            print(f"  · {m['modelo']}: {falt}")

    duplicados = info.get("modelos_duplicados", [])
    if duplicados:
        print(f"\n④ ⚠️ MODELOS DUPLICADOS en el Excel ({len(duplicados)}):")
        for d in duplicados:
            filas = ", ".join(str(f) for f in d["filas_excel"])
            print(f"  · {d['modelo']} — aparece {d['n']} veces (filas {filas}); "
                  f"solo se carga la ÚLTIMA fila")
        return 2
    else:
        print("\n④ Sin modelos duplicados ✓")

    return 0


if __name__ == "__main__":
    sys.exit(main())
