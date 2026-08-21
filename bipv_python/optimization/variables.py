"""
Optimization Contract — Fase 3, Paso 1: vocabulario de variables.

Este paquete (optimization/) NO optimiza nada — eso es Fase 4 (optimización
numérica). Define qué significa "óptimo" para este motor: qué campos de
BIPVConfiguration/SuperficieBIPV son variables de decisión reales (con
límites tomados del código existente, no inventados) y cuáles son datos de
entrada fijos del proyecto.

Por qué esto importa antes de optimizar: un algoritmo de búsqueda (Fase 4)
necesita saber, para cada campo, si puede moverlo y dentro de qué rango. Sin
este contrato explícito, cualquier optimizador tendría que adivinarlo o un
agente de IA tendría que "inventar" límites — exactamente el tipo de
alucinación que el plan original identificó como el riesgo a evitar.
"""
from dataclasses import dataclass
from typing import Literal

TipoVariable = Literal["continua", "entera", "categorica"]


@dataclass(frozen=True)
class OptimizationVariable:
    nombre: str          # nombre del campo en BIPVConfiguration/SuperficieBIPV
    tipo: TipoVariable
    minimo: float | None = None
    maximo: float | None = None
    opciones: tuple | None = None   # solo para tipo="categorica"
    unidad: str = ""
    descripcion: str = ""
    # True cuando minimo y maximo son el MISMO punto físico (p.ej. azimuth:
    # 0°=360°=Norte). Un consumidor que compare directamente minimo vs
    # maximo para medir "cuánto importa esta variable" (ver
    # optimization/sensitivity.py) obtiene un resultado degenerado —
    # comparando Norte contra Norte, no explorando el rango real. Detectado
    # en producción: el Analista Técnico-Financiero señaló un impacto de
    # sensibilidad de exactamente 0 en un barrido de azimuth 0°→360° como
    # "bandera roja metodológica" antes de que nadie lo notara en el código.
    circular: bool = False


def variables_geometria(tipo_superficie: str | None = None) -> list[OptimizationVariable]:
    """
    tilt / azimuth de una superficie.

    Si se conoce el tipo de superficie (Fachada/Techo/Pérgola/Marquesina),
    los límites de tilt vienen de calculos.multi_superficie.TIPOS_SUPERFICIE
    (ya usados hoy en 9_Vista_3D.py para acotar los widgets) — no son un
    número que inventé para este contrato.
    """
    from calculos.multi_superficie import TIPOS_SUPERFICIE

    if tipo_superficie and tipo_superficie in TIPOS_SUPERFICIE:
        meta = TIPOS_SUPERFICIE[tipo_superficie]
        tilt_min, tilt_max = float(meta["tilt_min"]), float(meta["tilt_max"])
    else:
        tilt_min, tilt_max = 0.0, 90.0

    return [
        OptimizationVariable(
            "tilt", "continua", tilt_min, tilt_max, unidad="°",
            descripcion="Inclinación del plano — 0=horizontal, 90=fachada vertical.",
        ),
        OptimizationVariable(
            "azimuth", "continua", 0.0, 360.0, unidad="°",
            descripcion="Orientación — convención pvlib: 0=Norte, 90=Este, 180=Sur, 270=Oeste.",
            circular=True,   # 0°=360°=Norte — ver comentario en OptimizationVariable.circular
        ),
    ]


def variable_panel(catalogo: dict | None = None) -> OptimizationVariable:
    """Elección de panel — categórica sobre el catálogo real MODULOS_BIPV.

    `opciones` guarda las CLAVES del catálogo (str), no los dicts completos
    — mantiene el contrato liviano y legible para un agente. La resolución
    clave→dict real la hace optimization.scenario_generator al armar el
    candidato, no este módulo (aquí solo se define el vocabulario).

    Filtro real, no arbitrario: por defecto se excluyen los paneles sin
    Pmax_stc -- calculos.dimensionamiento.dimensionar_sistema() revienta con
    TypeError (N_paneles * None) si se les intenta dimensionar. Hallazgo al
    construir esta función: de los 7 paneles de MODULOS_BIPV, solo
    ASP-ST1-T40 tiene ficha completa (Pmax_stc/Imp_stc) -- los otros 6
    (T10/T20/T30/T50/T60/T70) son entradas de catálogo incompletas,
    preexistentes, nunca ejercitadas porque el proyecto real usa T40. Esto
    también afecta hoy a 📐 Dimensionamiento si alguien selecciona uno de
    esos paneles manualmente -- no es un problema nuevo de este módulo, solo
    el primer lugar que lo detecta y lo evita en vez de ofrecerlo como si
    fuera una opción válida.
    """
    if catalogo is None:
        from datos.tecnologias_bipv import MODULOS_BIPV as catalogo
        catalogo = {k: v for k, v in catalogo.items() if v.get("Pmax_stc") is not None}
    return OptimizationVariable(
        "panel", "categorica", opciones=tuple(catalogo.keys()),
        descripcion="Referencia del catálogo de paneles BIPV (datos.tecnologias_bipv.MODULOS_BIPV, "
                    "solo entradas con ficha completa).",
    )


def _catalogo_inversores_real() -> dict:
    """Catálogo de inversores real más completo disponible.

    Prioriza el catálogo Excel (datos/inversores_catalogo.xlsx vía
    datos.catalogo_inversores_excel.cargar_catalogo_inversores() — 105
    modelos reales, editable desde 🔌 Catálogo Inversores) sobre el Python
    hardcodeado (datos.catalogo_inversores.INVERSORES — 7 modelos). Mismo
    criterio de preferencia que ya usa pages/4b_⚖️_Comparador_Inversores.py
    para el comparador en vivo; hasta 2026-08-21 esta función (y por lo
    tanto variable_inversor()) usaba solo el catálogo angosto de 7, aunque
    el motor de Fase 4 no estaba conectado a ninguna página todavía.

    Import perezoso con fallback silencioso: optimization/ se mantiene sin
    depender de streamlit (no está instalado en el entorno de pruebas, y
    catalogo_inversores_excel.py lo importa a nivel de módulo para
    @st.cache_data) -- si el import falla, o el Excel no está disponible,
    o queda vacío, cae al catálogo Python sin propagar la excepción.

    Normaliza una diferencia real de forma entre las dos fuentes: el
    catálogo Python separa "fabricante"/"modelo"; el Excel solo trae
    "nombre" (la columna "Modelo" completa). Se agrega un alias "modelo"
    en las entradas del Excel que no lo traigan, para que un consumidor
    (p.ej. scenario_generator, sus tests) no tenga que conocer cuál de las
    dos fuentes resolvió cada candidato.
    """
    try:
        from datos.catalogo_inversores_excel import cargar_catalogo_inversores
        catalogo = cargar_catalogo_inversores()
    except Exception:
        catalogo = None

    if not catalogo:
        from datos.catalogo_inversores import INVERSORES
        return INVERSORES

    return {
        k: (v if "modelo" in v else {**v, "modelo": v.get("nombre", k)})
        for k, v in catalogo.items()
    }


def variable_inversor(catalogo: dict | None = None) -> OptimizationVariable:
    """Elección de inversor — categórica sobre el catálogo real más completo
    disponible (ver _catalogo_inversores_real()).

    Mismo patrón que variable_panel(): `opciones` guarda las claves, no los
    dicts. Elegir un inversor determina también eta_inversor (campo antes
    fijo en FIJOS_NO_OPTIMIZABLES) — scenario_generator sincroniza ambos al
    resolver la clave, para que nunca queden un inversor y una eficiencia
    de inversor distintos en el mismo candidato. El catálogo Excel no trae
    dato real de eficiencia (el datasheet fuente no la reporta para esos
    105 modelos) -- scenario_generator solo sincroniza eta_inversor cuando
    el dato real existe, nunca lo inventa.
    """
    if catalogo is None:
        catalogo = _catalogo_inversores_real()
    return OptimizationVariable(
        "inversor", "categorica", opciones=tuple(catalogo.keys()),
        descripcion="Referencia del catálogo real de inversores (Excel si está disponible, "
                    "si no datos.catalogo_inversores.INVERSORES).",
    )


def variables_string(N_serie_max: int = 40, N_strings_max: int = 20) -> list[OptimizationVariable]:
    """
    N_serie / N_strings_tracker — enteras.

    Los límites aquí son un techo genérico de catálogo (el mismo N_max=40
    que usa calculos.dimensionamiento.mapear_inversores_catalogo por
    defecto). El rango REALMENTE factible para un panel+inversor concreto
    es mucho más angosto y lo determina la ventana eléctrica Voc/Vmp — ver
    optimization.constraints.evaluar_compatibilidad_electrica() o, para un
    barrido completo, calculos.dimensionamiento.optimizar_n_serie(). No
    tratar estos límites como el criterio de factibilidad real.
    """
    return [
        OptimizationVariable(
            "N_serie", "entera", 1, N_serie_max,
            descripcion="Paneles en serie por string. Factibilidad real: optimization.constraints.",
        ),
        OptimizationVariable(
            "N_strings_tracker", "entera", 1, N_strings_max,
            descripcion="Strings en paralelo por entrada MPPT.",
        ),
    ]


def variable_k_bipv() -> OptimizationVariable:
    """
    Confinamiento térmico BIPV (IEA-PVPS T15) — documentado en
    calculos.produccion.simular_produccion_anual: 1.0=ventilado libre,
    1.3=fachada confinada típica, 1.5=sellado total.

    Se expone como variable exploratoria, pero en la práctica lo determina
    el diseño constructivo (cómo se ventila la cara trasera del panel), no
    una elección libre del optimizador — un agente no debería moverlo sin
    justificación constructiva.
    """
    return OptimizationVariable(
        "k_bipv", "continua", 1.0, 1.5, unidad="factor",
        descripcion="Confinamiento térmico BIPV — normalmente fijado por el diseño constructivo.",
    )


# ── Datos de entrada FIJOS — nunca variables de decisión del optimizador ──
# Nombre de campo → por qué no es optimizable en este contrato.
FIJOS_NO_OPTIMIZABLES: dict[str, str] = {
    # BIPVConfiguration / ProyectoMultiSuperficie
    "lat": "ubicación del proyecto — dato del sitio, no una decisión",
    "lon": "ubicación del proyecto — dato del sitio, no una decisión",
    "alt_m": "ubicación del proyecto — dato del sitio, no una decisión",
    "area_m2": "área disponible de la superficie — restricción física del edificio, no una decisión",
    "N_inversores": (
        "cuántos inversores idénticos tiene el proyecto (Granja FV típicamente) — "
        "una decisión de diseño de mayor nivel (cuántas unidades comprar), no algo "
        "que un barrido de tilt/azimuth/panel deba variar candidato a candidato. "
        "Ver la nota 'Multi-inversor' en simulation/schemas.py."
    ),
    "albedo": "reflectividad del entorno — dato del sitio",
    "puntos_horizonte": "perfil de obstáculos reales — dato del sitio (levantamiento/SketchUp)",
    "eta_inversor": (
        "queda determinado al elegir el inversor — no se optimiza por separado. "
        "Si 'inversor' SÍ es una variable de decisión (ver variable_inversor()), "
        "optimization.scenario_generator sincroniza eta_inversor automáticamente "
        "con la eficiencia del inversor sorteado en cada candidato."
    ),
    "pct_mismatch_fab": "pérdida de fabricación — supuesto técnico, no una decisión de diseño",
    "pct_soiling": "supuesto de mantenimiento/limpieza — política de O&M, no diseño",
    "pct_cableado": "supuesto de instalación eléctrica — no una decisión de diseño BIPV",
    # FinancialConfiguration
    "tarifa_cop_kWh": "tarifa eléctrica del sitio — dada por el mercado/contrato, no una decisión",
    "tipo_cambio": "TRM — dada por el mercado",
    "tasa_descuento": "supuesto financiero del inversionista (ver optimization.investor_profile)",
    "tasa_escalacion_tarifa": "supuesto macroeconómico",
    "tasa_degradacion_pct": "propiedad del panel elegido, no una decisión independiente",
    "opex_pct_capex": "supuesto de O&M — política, no diseño técnico",
    "capex_usd": (
        "NO es un dato exógeno real — depende del candidato técnico. En v1 no hay "
        "todavía una función que derive capex_usd automáticamente desde "
        "SimulationResult; debe estimarse con calculos.presupuesto.calcular_parametrico() "
        "o una cotización real antes de evaluar objetivos financieros. Ver "
        "optimization/objectives.py::estimar_capex_parametrico_usd()."
    ),
}
