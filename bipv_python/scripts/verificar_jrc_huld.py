# -*- coding: utf-8 -*-
"""Verificación cruzada CdTe/CIS (power-rating model de Huld/JRC) -- lee
CUALQUIER proyecto guardado en `datos/proyectos/*.json` (generalizado
31-ago-2026), y soporta tanto CdTe como CIS (generalizado el mismo día,
pedido explícito del usuario: "los sistemas BIPV necesitan también este
tipo de tecnología").

Lee el JSON del proyecto DIRECTAMENTE del disco, sin pasar por
`calculos.proyectos_manager` (esa API exige una sesión de Streamlit activa
para el aislamiento por usuario -- este es un script de terminal, no una
página de la app; ver `DIAGNOSTICO_VERIFICACION_JRC_CDTE_TEUSAQUILLO.md`
para el contexto completo de por qué existe esta verificación).

Uso:
    python scripts/verificar_jrc_huld.py --listar
    python scripts/verificar_jrc_huld.py <slug_del_proyecto>

El slug es el nombre del archivo sin ".json" (ver la salida de --listar).
La tecnología del panel del proyecto se detecta sola -- si no es CdTe ni
CIS, el script se detiene con un mensaje claro (los coeficientes de este
modelo no aplican a otras tecnologías todavía).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculos.solar import obtener_tmy_pvgis, calcular_poa  # noqa: E402
from calculos.modelo_jrc_huld import (  # noqa: E402
    calcular_pr_jrc,
    extraer_parametros_proyecto,
)

DIR_PROYECTOS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos", "proyectos"
)

# Rangos de PR reportados en la literatura real (Kumar et al., mismo grupo de
# autores, clima tropical de Malasia), verificados contra el texto completo
# de ambos papers -- ver docstring de calculos/modelo_jrc_huld.py.
REFERENCIA_LITERATURA_PR = {
    "CdTe": {"techo": (74.92, 77.36), "fachada": (66.42, 76.26)},
    "CIS": {"BIPV": (72.21, 73.92), "BAPV": (73.68, 75.46)},
}


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

    tecnologia = params["tecnologia"]
    print(f"Proyecto: {params['nombre_proyecto']} ({slug})")
    print(f"  Panel: {params['panel_nombre']} ({tecnologia}) · "
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

    print(f"\nCorriendo power-rating model de Huld/JRC para {tecnologia}...")
    r = calcular_pr_jrc(
        poa_wm2=poa_global.to_numpy(),
        t_ambiente_c=tmy["T2m"].to_numpy(),
        viento_ms=tmy["WS10m"].to_numpy(),
        p_stc_w=params["p_stc_total_w"],
        tecnologia=tecnologia,
    )

    print("\n" + "=" * 70)
    print(f"RESULTADO -- power-rating model JRC/Huld ({tecnologia}), sobre POA BRUTA")
    print("(sin Motor Óptico -- verificación cruzada del motor SDM principal,")
    print(" no un reemplazo; ver DIAGNOSTICO_VERIFICACION_JRC_CDTE_TEUSAQUILLO.md)")
    print("=" * 70)
    print(f"POA anual usada  : {r['POA_anual_kWh_m2']:.1f} kWh/m²/año")
    print(f"E_dc anual (JRC) : {r['E_anual_kWh']:.0f} kWh/año")
    print(f"PR (JRC)         : {r['PR_pct']:.2f}%")
    print()
    print(f"Referencia -- literatura {tecnologia} BIPV bajo clima tropical (Kumar et al.):")
    for etiqueta, (lo, hi) in REFERENCIA_LITERATURA_PR[tecnologia].items():
        print(f"  PR {etiqueta:8s}: {lo:.2f}% a {hi:.2f}%")


if __name__ == "__main__":
    main()
