"""
Script de diagnóstico del catálogo de inversores (#122).

Verifica que la hoja Catalogo_Inversores carga correctamente y reporta:
hojas disponibles, columnas críticas/importantes ausentes, modelos duplicados
y modelos con campos críticos vacíos.

Uso en el servidor:
    cd /var/www/bipv/calculadora-bipv
    source bipv_python/venv/bin/activate
    python bipv_python/datos/diagnostico_catalogo_inversores.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datos.catalogo_inversores_excel import (   # noqa: E402
    diagnostico_catalogo_inversores, excel_mtime_inv,
)


def main() -> int:
    d = diagnostico_catalogo_inversores(_mtime=excel_mtime_inv())

    print("═" * 70)
    print("DIAGNÓSTICO — CATÁLOGO DE INVERSORES")
    print("═" * 70)
    print(f"Hojas en el Excel : {d.get('hojas_disponibles')}")
    print(f"Hoja usada        : {d.get('hoja_usada', '— (no encontrada)')}")
    print(f"Modelos cargados  : {d.get('modelos_cargados', 0)}")

    if d.get("detalle"):
        print(f"\n⚠️  {d['detalle']}")

    _cc = d.get("columnas_criticas_faltantes", [])
    _ci = d.get("columnas_importantes_faltantes", [])
    if _cc:
        print("\n🔴 Columnas CRÍTICAS ausentes (el dimensionamiento saldrá mal):")
        for c in _cc:
            print(f"   - {c}")
    if _ci:
        print("\n🟡 Columnas importantes ausentes:")
        for c in _ci:
            print(f"   - {c}")

    _dup = d.get("modelos_duplicados", [])
    if _dup:
        print("\n🟡 Modelos DUPLICADOS (solo la última fila se usa):")
        for x in _dup:
            print(f"   - {x['modelo']}  (filas Excel: {x['filas_excel']})")

    _inc = d.get("modelos_incompletos", [])
    if _inc:
        print(f"\n🟡 Modelos con campos críticos vacíos ({len(_inc)}):")
        for x in _inc:
            print(f"   - {x['modelo']}: faltan {', '.join(x['campos_faltantes'])}")

    _icono = {"ok": "🟢 OK", "parcial": "🟡 PARCIAL", "error": "🔴 ERROR"}
    print(f"\nEstado final: {_icono.get(d.get('estado'), d.get('estado'))}")
    return 0 if d.get("estado") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
