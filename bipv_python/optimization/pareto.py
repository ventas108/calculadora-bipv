"""
Fase 4, Paso 4: frente de Pareto.

No es una metaheurística multiobjetivo (NSGA-II, etc.) — el plan original
advertía explícitamente contra comprometerse a un algoritmo de búsqueda sin
antes medir la dimensionalidad y el costo real de las simulaciones. Esto es
lo que sí hace falta primero y es honesto sobre su propio alcance: dado un
conjunto YA evaluado de candidatos (numerical_optimizer.evaluar_candidatos),
quedarse con los no-dominados. Suficiente para explorar decenas de
candidatos generados por muestreo aleatorio; migrar a una metaheurística
que genere sus propios candidatos de forma dirigida es un cambio aislado a
scenario_generator.py, no a esta pieza.
"""
from optimization.numerical_optimizer import ResultadoCandidato
from optimization.objectives import OBJETIVOS


def domina(a: dict, b: dict, nombres_objetivos: list[str]) -> bool:
    """
    True si el candidato `a` domina a `b`: es igual o mejor en TODOS los
    objetivos listados (según la dirección max/min de cada uno en
    optimization.objectives.OBJETIVOS) y estrictamente mejor en al menos
    uno.

    Un objetivo en None en cualquiera de los dos (p.ej. IRR sin solución
    real) se IGNORA para esa comparación — no se trata como -infinito ni
    rompe la comparación de los demás objetivos.
    """
    hay_alguno_comparable = False
    estrictamente_mejor_en_alguno = False

    for nombre in nombres_objetivos:
        objetivo = OBJETIVOS[nombre]
        va, vb = a.get(nombre), b.get(nombre)
        if va is None or vb is None:
            continue
        hay_alguno_comparable = True

        mejor_o_igual = va >= vb if objetivo.direccion == "max" else va <= vb
        if not mejor_o_igual:
            return False
        if va != vb:
            estrictamente_mejor_en_alguno = True

    return hay_alguno_comparable and estrictamente_mejor_en_alguno


def frente_pareto(
    resultados: list[ResultadoCandidato],
    nombres_objetivos: list[str],
) -> list[ResultadoCandidato]:
    """Conserva solo los candidatos que ningún otro domina."""
    no_dominados = []
    for i, candidato in enumerate(resultados):
        dominado = any(
            domina(otro.objetivos, candidato.objetivos, nombres_objetivos)
            for j, otro in enumerate(resultados)
            if j != i
        )
        if not dominado:
            no_dominados.append(candidato)
    return no_dominados
