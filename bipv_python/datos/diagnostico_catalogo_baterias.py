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

# ── Alias por campo (alineado con _CAMPO_ALIASES_SUGERIDOS de catalogo_baterias_excel.py) ──
# Cada valor es (alias_preferido, [todos_los_aliases], critico, importante)
CAMPOS = {
    "capacidad_kWh": {
        "alias": ["Capacidad (kWh)", "Capacidad kWh", "Capacidad_kWh",
                  "Energía Nominal (kWh)", "Energia Nominal (kWh)",
                  "Energy (kWh)", "Usable Capacity (kWh)"],
        "sugerido": "Capacidad (kWh)", "critico": True,  "importante": False,
    },
    "potencia_kW": {
        "alias": ["Potencia Continua (kW)", "Potencia kW", "Potencia_kW",
                  "Potencia Max (kW)", "Continuous Power (kW)", "Max Power (kW)"],
        "sugerido": "Potencia Continua (kW)", "critico": True, "importante": False,
    },
    "voltaje_V": {
        "alias": ["Voltaje Nominal (V)", "Voltaje V", "Voltaje_V",
                  "Tensión Nominal (V)", "Tension Nominal (V)", "Nominal Voltage (V)"],
        "sugerido": "Voltaje Nominal (V)", "critico": False, "importante": False,
    },
    "dod_pct": {
        "alias": ["DoD (%)", "DoD Máximo (%)", "DoD Maximo (%)", "DoD_pct",
                  "Profundidad Descarga (%)", "Depth of Discharge (%)"],
        "sugerido": "DoD Máximo (%)", "critico": False, "importante": True,
    },
    "ciclos_vida": {
        "alias": ["Ciclos de Vida", "Ciclos Vida", "Ciclos", "Cycle Life", "Cycles"],
        "sugerido": "Ciclos de Vida", "critico": False, "importante": True,
    },
    "eta_rte_pct": {
        "alias": ["Eficiencia RTE (%)", "Eficiencia (%)", "Eficiencia_rte_pct",
                  "Rendimiento (%)", "Round-trip Efficiency (%)", "RTE (%)"],
        "sugerido": "Eficiencia RTE (%)", "critico": False, "importante": True,
    },
    "tipo": {
        "alias": ["Tecnología", "Tecnologia", "Tipo", "Química", "Quimica", "Chemistry"],
        "sugerido": "Tecnología", "critico": False, "importante": False,
    },
    "costo_usd": {
        "alias": ["Costo (USD)", "Costo USD", "Costo Batería", "Costo Bateria",
                  "Precio (USD)", "Price (USD)"],
        "sugerido": "Costo (USD)", "critico": False, "importante": False,
    },
    "garantia_anos": {
        "alias": ["Garantía (años)", "Garantia (años)", "Garantía (anos)",
                  "Garantia (anos)", "Warranty (years)"],
        "sugerido": "Garantía (años)", "critico": False, "importante": False,
    },
}


def norm(c: str) -> str:
    return " ".join(str(c).strip().split())


def main():
    print("=" * 70)
    print("DIAGNÓSTICO — Catálogo de Baterías BIPV")
    print("=" * 70)

    # ── 1. Verificar que el Excel existe ──────────────────────────────────────
    if not EXCEL.exists():
        print(f"\n❌ Archivo no encontrado: {EXCEL}")
        print("   ➜ Confirma la ruta o ejecuta desde /var/www/bipv/calculadora-bipv/")
        sys.exit(1)

    import os
    mtime = EXCEL.stat().st_mtime
    size_kb = EXCEL.stat().st_size / 1024
    print(f"\n✓ Excel encontrado: {EXCEL.name}")
    print(f"  Tamaño: {size_kb:.1f} KB  ·  Modificado: {__import__('datetime').datetime.fromtimestamp(mtime):%Y-%m-%d %H:%M:%S}")

    # ── 2. Listar hojas ───────────────────────────────────────────────────────
    xl = pd.ExcelFile(EXCEL, engine="openpyxl")
    print(f"\nHojas disponibles ({len(xl.sheet_names)}): {xl.sheet_names}")

    sheet = next((s for s in SHEETS if s in xl.sheet_names), None)
    if not sheet:
        print(f"\n❌ Ninguna hoja de baterías encontrada.")
        print(f"   Se buscó (en orden): {SHEETS}")
        print(f"\n   ➜ Solución: agregar hoja con nombre exacto 'Catalogo_Baterias' al Excel")
        print(f"   ➜ Ejecuta: python bipv_python/datos/agregar_hoja_baterias.py")
        sys.exit(1)

    print(f"\n✓ Hoja usada: '{sheet}'")

    # ── 3. Detectar fila de header ────────────────────────────────────────────
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
            print(f"  header={h}: error — {e}")

    if df is None:
        print("\n❌ No se encontró fila de header con 'Modelo' (o alias) en las primeras 5 filas")
        print("   ➜ Verifica que la primera columna se llame 'Modelo', 'Nombre' o 'Battery Model'")
        sys.exit(1)

    print(f"✓ Header detectado en fila {header_row} (0-indexado)")

    # ── 4. Detectar columnas: mapeadas vs ausentes ────────────────────────────
    cols_excel = set(df.columns)
    print(f"\nColumnas en la hoja ({len(cols_excel)}):")
    for c in df.columns:
        # Determinar si esta columna está mapeada a algún campo interno
        campo_int = next(
            (k for k, info in CAMPOS.items() if c in info["alias"]),
            None
        )
        if campo_int:
            nivel = " [CRÍTICO]" if CAMPOS[campo_int]["critico"] else (" [importante]" if CAMPOS[campo_int]["importante"] else "")
            print(f"  ✅ {c}  →  {campo_int}{nivel}")
        elif c.lower() in ALIASES:
            print(f"  ✅ {c}  →  nombre (identificador de modelo)")
        else:
            print(f"  🔵 {c}  (no mapeada — no afecta la carga)")

    # ── 5. Campos sin ningún alias en el Excel ────────────────────────────────
    ausentes_criticos    = []
    ausentes_importantes = []
    ausentes_opcionales  = []

    for campo_int, info in CAMPOS.items():
        if not any(a in cols_excel for a in info["alias"]):
            entry = (campo_int, info["sugerido"])
            if info["critico"]:
                ausentes_criticos.append(entry)
            elif info["importante"]:
                ausentes_importantes.append(entry)
            else:
                ausentes_opcionales.append(entry)

    if ausentes_criticos:
        print(f"\n🔴 Campos CRÍTICOS sin columna en el Excel (bloquean dimensionamiento):")
        for campo, sug in ausentes_criticos:
            print(f"   ✗ {campo}  ←  agregar columna: '{sug}'")
    if ausentes_importantes:
        print(f"\n⚠  Campos IMPORTANTES sin columna (se usarán defaults: 80% DoD · 95% RTE · 3000 ciclos):")
        for campo, sug in ausentes_importantes:
            print(f"   ✗ {campo}  ←  agregar columna: '{sug}'")
    if ausentes_opcionales:
        print(f"\n🔵 Campos opcionales sin columna (no afectan el cálculo):")
        for campo, sug in ausentes_opcionales:
            print(f"   - {campo}")

    if not ausentes_criticos and not ausentes_importantes:
        print(f"\n✅ Todos los campos requeridos tienen columna en el Excel")

    # ── 6. Analizar modelos ───────────────────────────────────────────────────
    modelos_ok  = []
    modelos_inc = []

    for _, row in df.iterrows():
        # Buscar nombre del modelo
        nombre = None
        for a in ["Modelo", "modelo", "Nombre", "Battery Model", "Bateria"]:
            val = str(row.get(a, "")).strip()
            if val and val.lower() not in ("nan", "") and val.lower() not in ALIASES:
                nombre = val
                break
        if not nombre:
            continue
        if nombre.startswith("⚠") or nombre.startswith("*") or len(nombre) > 60:
            continue

        # Verificar campos críticos por fila
        falt = []
        for campo_int in ["capacidad_kWh", "dod_pct", "eta_rte_pct", "ciclos_vida"]:
            info = CAMPOS[campo_int]
            for a in info["alias"]:
                if a in df.columns:
                    try:
                        import math
                        v = float(row.get(a))
                        if not math.isnan(v):
                            break
                    except Exception:
                        pass
            else:
                falt.append(campo_int)

        if falt:
            modelos_inc.append((nombre, falt))
        else:
            modelos_ok.append(nombre)

    total = len(modelos_ok) + len(modelos_inc)
    print(f"\nModelos detectados: {total}  ({len(modelos_ok)} completos · {len(modelos_inc)} con valores vacíos)")

    if modelos_ok:
        print(f"\n  Modelos con datos COMPLETOS ({len(modelos_ok)}):")
        for m in modelos_ok:
            print(f"    ✅ {m}")

    if modelos_inc:
        print(f"\n  Modelos con valores VACÍOS ({len(modelos_inc)}):")
        for m, f in modelos_inc:
            print(f"    ⚠  {m}  —  campos vacíos: {', '.join(f)}")

    # ── 7. Veredicto final ────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    if ausentes_criticos:
        print("❌ FALLA: Faltan columnas críticas — ninguna batería puede dimensionarse")
        print("   Agrega las columnas indicadas arriba y ejecuta este script de nuevo.")
        sys.exit(1)
    elif not total:
        print("❌ FALLA: No se detectaron modelos de batería en la hoja")
        print("   Verifica que la hoja tenga filas de datos bajo el header.")
        sys.exit(1)
    else:
        print(f"✅ El catálogo cargará correctamente en la Página 11")
        if ausentes_importantes:
            print("⚠  Algunos campos usan defaults (DoD=80%, RTE=95%, ciclos=3000)")
        if modelos_inc:
            print(f"⚠  {len(modelos_inc)} modelos tienen celdas vacías — usarán defaults para esos campos")
        print(f"\n   ➜ Si acabas de modificar el Excel, usa el botón '🔄 Recargar catálogo'")
        print(f"     en la Página 11 para invalidar el caché sin reiniciar PM2.")


if __name__ == "__main__":
    main()
