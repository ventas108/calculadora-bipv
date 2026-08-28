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


def _catalogo_paneles_real() -> dict:
    """Catálogo de paneles real más completo disponible -- UNIÓN (no solo
    preferencia) de dos fuentes, con prioridad explícita:

    1. datos.tecnologias_bipv.MODULOS_BIPV (7 variantes ASP-ST1, T10-T70):
       parámetros SDM De Soto 2006 calibrados por ajuste de curva contra la
       hoja FF_vs_Irradiancia del XLSM auditado, validados contra Batzner
       et al. 2001 -- la fuente de mayor precisión para las variantes que
       cubre.
    2. datos.catalogo_paneles_excel.cargar_catalogo_excel() (65 paneles
       reales, catálogo editable desde 📋 Catálogo Paneles / usado por
       📐 Dimensionamiento) -- cobertura mucho más amplia, pero ninguna
       entrada trae los 5 parámetros SDM completos (I_L_ref/I_o_ref/R_s/
       R_sh_ref/a_ref) -- solo ficha de placa (Voc/Isc/Vmp/Imp/Pmax) y, para
       algunos, un NsA/n_idealidad ESTIMADO (no curve-fit) que no equivale
       al a_ref calibrado.

    A diferencia de _catalogo_inversores_real() (que solo PREFIERE el
    catálogo grande y no tiene fuente pequeña que perder), aquí se hace una
    UNIÓN con el catálogo chico ganando los conflictos: verificado
    (27-ago-2026) que las 7 claves "ASP-ST1-T10".."ASP-ST1-T70" existen en
    AMBAS fuentes con el MISMO nombre -- para esas 7, el Excel trae
    I_L_ref/I_o_ref/R_s/R_sh_ref en None (solo un NsA=196,1 estimado, no
    calibrado) mientras MODULOS_BIPV trae los 5 parámetros SDM reales. Si se
    prefiriera el Excel a secas (como con inversores), el proyecto
    Teusaquillo -- el único ya auditado contra el XLSM esta sesión -- perdería
    su modelo de diodo único sin necesidad y caería al modelo simplificado.

    Los ~58 paneles del Excel sin equivalente en el catálogo chico se
    agregan tal cual -- se simularán con el modelo lineal simplificado (ver
    calculos.produccion.panel_tiene_sdm_completo()), no con SDM; esa
    distinción ya la reporta simular_produccion_anual() (clave
    "uso_modelo_simplificado") -- no es un caso nuevo que este módulo tenga
    que inventar cómo manejar, ya existe en el resto de la app.

    Import perezoso con fallback silencioso, mismo criterio que
    _catalogo_inversores_real(): optimization/ se mantiene sin depender de
    streamlit -- si el Excel no carga, se usa solo el catálogo chico
    (comportamiento anterior a esta función, sin romper nada).
    """
    from datos.tecnologias_bipv import MODULOS_BIPV
    catalogo = dict(MODULOS_BIPV)
    try:
        from datos.catalogo_paneles_excel import cargar_catalogo_excel
        excel = cargar_catalogo_excel() or {}
    except Exception:
        excel = {}
    for clave, panel in excel.items():
        if clave not in catalogo:
            catalogo[clave] = panel
    return catalogo


def variable_panel(catalogo: dict | None = None) -> OptimizationVariable:
    """Elección de panel — categórica sobre el catálogo real más completo
    disponible (ver _catalogo_paneles_real()): unión de las 7 variantes
    ASP-ST1 (T10-T70, con SDM calibrado) y el catálogo Excel de paneles
    reales (65 modelos, sin SDM propio).

    `opciones` guarda las CLAVES del catálogo (str), no los dicts completos
    — mantiene el contrato liviano y legible para un agente. La resolución
    clave→dict real la hace optimization.scenario_generator al armar el
    candidato (contra el MISMO catálogo unido, no MODULOS_BIPV a secas —
    ver el comentario en _resolver_categoricas_de_catalogo(), mismo tipo de
    bug ya evitado para inversor).

    Filtro real, no arbitrario: cuando se usa el catálogo por defecto (sin
    pasar `catalogo`), se excluyen los paneles sin Pmax_stc --
    calculos.dimensionamiento.dimensionar_sistema() revienta con TypeError
    (N_paneles * None) si se les intenta dimensionar. Verificado 27-ago-2026:
    los 65 paneles del catálogo Excel real SÍ traen Pmax_stc (ninguno se
    excluye por este filtro hoy); no es SDM lo que este filtro exige, ver
    docstring de _catalogo_paneles_real() para esa distinción.

    Si se pasa un `catalogo` explícito, NO se filtra -- contrato preexistente
    del que depende calculos.comparador_paneles.paneles_excluidos_por_ficha_incompleta()
    para poder mostrarle al usuario, con un catálogo propio, cuáles paneles
    quedarían excluidos (necesita ver las entradas sin Pmax_stc, no que ya
    vengan quitadas). Regresión real que se coló al conectar el catálogo
    Excel (el filtro había quedado aplicándose siempre, incluso con catálogo
    explícito) -- encontrada releyendo esa función antes de darla por no
    afectada, corregida en el mismo commit.
    """
    if catalogo is None:
        catalogo = _catalogo_paneles_real()
        catalogo = {k: v for k, v in catalogo.items() if v.get("Pmax_stc") is not None}
    return OptimizationVariable(
        "panel", "categorica", opciones=tuple(catalogo.keys()),
        descripcion="Referencia del catálogo real de paneles (unión de datos.tecnologias_bipv.MODULOS_BIPV "
                    "y el catálogo Excel real, solo entradas con Pmax_stc).",
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
