# -*- coding: utf-8 -*-
"""Verificación cruzada CdTe (power-rating model de Huld/JRC) -- generalizado
(31-ago-2026, pedido explícito del usuario) para leer CUALQUIER proyecto
guardado en `datos/proyectos/*.json`, no solo Teusaquillo.

Lee el JSON del proyecto DIRECTAMENTE del disco, sin pasar por
`calculos.proyectos_manager` (esa API exige una sesión de Streamlit activa
para el aislamiento por usuario -- este es un script de terminal, no una
página de la app; ver `DIAGNOSTICO_VERIFICACION_JRC_CDTE_TEUSAQUILLO.md`
para el contexto completo de por qué existe esta verificación).

Uso:
    python scripts/verificar_jrc_cdte.py --listar
    python scripts/verificar_jrc_cdte.py <slug_del_proyecto>

El slug es el nombre del archivo sin ".json" (ver la salida de --listar).
Solo aplica a proyectos con panel de tecnología CdTe -- para cualquier otro
panel, el script se detiene con un mensaje claro (los coeficientes de este
modelo no aplican a otras tecnologías).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculos.solar import obtener_tmy_pvgis, calcular_poa  # noqa: E402
from calculos.modelo_jrc_cdte import (  # noqa: E402
    calcular_pr_jrc_cdte,
    extraer_parametros_proyecto,
)

DIR_PROYECTOS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos", "proyectos"
)


def listar_proyectos_en_disco() -> list[str]:
    """Lista los slugs disponibles en datos/proyectos/ -- lectura directa de
    archivos, sin aislamiento por usuario (script de terminal/mantenimiento,
    no una vista multi-usuario de la app)."""
    if not os.path.isdir(DIR_PROYECTOS):
        return []
    return sorted(f[:-5] for f in os.listdir(DIR_PROYECTOS) if f.endswith(".json"))


def cargar_estado_proyecto(slug: str) -> dict:
    ruta = os.path.join(DIR_PROYECTOS, f"{slug}.json")
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No existe {ruta}. Usa --listar para ver los proyectos disponibles.")
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("estado", {})


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("--listar", "-l"):
        proyectos = listar_proyectos_en_disco()
        if not proyectos:
            print(f"No hay proyectos guardados en {DIR_PROYECTOS}.")
        else:
            print("Proyectos disponibles (usa el slug como argumento):")
            for slug in proyectos:
                print(f"  {slug}")
        return

    slug = sys.argv[1]
    estado = cargar_estado_proyecto(slug)

    try:
        params = extraer_parametros_proyecto(estado)
    except ValueError as e:
        print(f"⚠️  No se puede correr la verificación JRC/Huld para '{slug}':\n    {e}")
        return

    print(f"Proyecto: {params['nombre_proyecto']} ({slug})")
    print(f"  Panel: {params['panel_nombre']} ({params['tecnologia']}) · "
          f"{params['n_paneles']} módulos · {params['p_stc_total_w'] / 1000:.3f} kWp")
    print(f"  Sitio: {params['ciudad']} ({params['lat']}, {params['lon']}, {params['alt_m']:.0f} m)")
    print(f"  Geometría: tilt={params['tilt']:.0f}°, azimuth={params['azimuth']:.0f}°, "
          f"albedo={params['albedo']:.2f}")

    print(f"\nDescargando TMY real PVGIS para {params['ciudad']}...")
    tmy = obtener_tmy_pvgis(params["lat"], params["lon"])
    print(f"  {len(tmy)} horas descargadas.")

    print("Calculando POA (Hay-Davies, mismo modelo que usa la app)...")
    poa = calcular_poa(
        tmy, params["lat"], params["lon"], params["alt_m"],
        params["tilt"], params["azimuth"], params["albedo"],
    )
    poa_global = poa["poa_global"]
    print(f"  POA anual: {poa_global.sum() / 1000.0:.1f} kWh/m²/año")

    print("\nCorriendo power-rating model de Huld/JRC para CdTe...")
    r = calcular_pr_jrc_cdte(
        poa_wm2=poa_global.to_numpy(),
        t_ambiente_c=tmy["T2m"].to_numpy(),
        viento_ms=tmy["WS10m"].to_numpy(),
        p_stc_w=params["p_stc_total_w"],
    )

    print("\n" + "=" * 70)
    print("RESULTADO -- power-rating model JRC/Huld (CdTe), sobre POA BRUTA")
    print("(sin Motor Óptico -- verificación cruzada del motor SDM principal,")
    print(" no un reemplazo; ver DIAGNOSTICO_VERIFICACION_JRC_CDTE_TEUSAQUILLO.md)")
    print("=" * 70)
    print(f"POA anual usada  : {r['POA_anual_kWh_m2']:.1f} kWh/m²/año")
    print(f"E_dc anual (JRC) : {r['E_anual_kWh']:.0f} kWh/año")
    print(f"PR (JRC)         : {r['PR_pct']:.2f}%")
    print()
    print("Referencia -- literatura CdTe BIPV bajo clima tropical (Kumar et al.):")
    print("  PR techo   : 74,92% a 77,36%")
    print("  PR fachada : 66,42% a 76,26%")


if __name__ == "__main__":
    main()
