"""
Script de diagnóstico: verifica que el catálogo de baterías carga correctamente
y reporta columnas encontradas, modelos detectados y campos faltantes.

Uso en el servidor:
    cd /var/www/bipv/calculadora-bipv
    source bipv_python/venv/bin/activate
    python bipv_python/datos/diagnostico_catalogo_baterias.py
"""
import sys
from pathlib import Path
import pandas as pd

EXCEL  = Path("/var/www/bipv/calculadora-bipv/bipv_python/datos/inversores_catalogo.xlsx")
SHEETS = ["Catalogo_Baterias", "Baterias", "Storage"]
ALIASES = {"modelo", "nombre", "model", "battery model", "bateria"}

CAMPOS_CRITICOS = [
    "Modelo", "Capacidad (kWh)", "DoD (%)", "Eficiencia RTE (%)",
    "Ciclos de Vida", "Potencia Continua (kW)", "Voltaje Nominal (V)",
]

def norm(c):
    return " ".join(str(c).strip().split())

def main():
    print("=" * 65)
    print("DIAGNÓSTICO — Catálogo de Baterías BIPV")
    print("=" * 65)

    if not EXCEL.exists():
        print(f"❌ Archivo no encontrado: {EXCEL}")
        sys.exit(1)

    xl = pd.ExcelFile(EXCEL, engine="openpyxl")
    print(f"✓ Excel abierto: {EXCEL.name}")
    print(f"  Hojas disponibles: {xl.sheet_names}")

    sheet = next((s for s in SHEETS if s in xl.sheet_names), None)
    if not sheet:
        print(f"\n❌ Ninguna hoja de baterías encontrada.")
        print(f"   Se buscó: {SHEETS}")
        print(f"\n   ➜ Solución: agregar hoja 'Catalogo_Baterias' al Excel")
        sys.exit(1)

    print(f"\n✓ Hoja encontrada: '{sheet}'")

    # Detectar fila de header
    df = None
    header_row = None
    for h in range(5):
        try:
            df_c = pd.read_excel(EXCEL, sheet_name=sheet, header=h, engine="openpyxl")
            cols = [norm(c) for c in df_c.columns]
            if any(c.lower() in ALIASES for c in cols):
                df_c.columns = cols
                df = df_c
                header_row = h
                break
        except Exception as e:
            print(f"  row={h}: error — {e}")

    if df is None:
        print("\n❌ No se encontró fila con 'Modelo' en las primeras 5 filas")
        sys.exit(1)

    print(f"✓ Header detectado en fila {header_row} (0-indexado)")
    print(f"\nColumnas encontradas ({len(df.columns)}):")
    for c in df.columns:
        marker = "✅" if c in CAMPOS_CRITICOS else "  "
        print(f"  {marker} {c}")

    # Campos críticos faltantes
    faltantes = [c for c in CAMPOS_CRITICOS if c not in df.columns]
    if faltantes:
        print(f"\n⚠  Columnas críticas NO encontradas: {faltantes}")
        print("   Revisar nombres exactos de columna en el Excel")
    else:
        print(f"\n✅ Todas las columnas críticas encontradas")

    # Filas de datos
    modelos_ok = []
    modelos_inc = []
    for _, row in df.iterrows():
        m = str(row.get("Modelo", "")).strip()
        if not m or m.lower() in ("nan", "") or m.lower() in ALIASES:
            continue
        cap = row.get("Capacidad (kWh)")
        dod = row.get("DoD (%)")
        rte = row.get("Eficiencia RTE (%)")
        cic = row.get("Ciclos de Vida")
        falt = []
        try: float(cap)
        except: falt.append("Capacidad")
        try: float(dod)
        except: falt.append("DoD")
        try: float(rte)
        except: falt.append("RTE")
        try: float(cic)
        except: falt.append("Ciclos")

        if falt:
            modelos_inc.append((m, falt))
        else:
            modelos_ok.append(m)

    print(f"\nModelos con datos COMPLETOS ({len(modelos_ok)}):")
    for m in modelos_ok:
        print(f"  ✅ {m}")

    print(f"\nModelos con datos INCOMPLETOS ({len(modelos_inc)}):")
    for m, f in modelos_inc:
        print(f"  ⚠  {m} — faltan: {', '.join(f)}")

    print(f"\nTotal modelos detectados: {len(modelos_ok) + len(modelos_inc)}")
    print("\n" + "=" * 65)
    if not faltantes and (modelos_ok or modelos_inc):
        print("✅ El catálogo cargará correctamente en la Página 11")
        if modelos_inc:
            print("⚠  Modelos incompletos usarán defaults (DoD=80%, RTE=95%)")
    else:
        print("❌ Revisar los problemas indicados antes de probar la app")

if __name__ == "__main__":
    main()
