"""
test_bloqueo_modelo_inversor.py — Prueba de regresión (Tarea #138).

Verifica la lógica PURA que decide si el botón "Guardar en catálogo" debe
bloquearse cuando una ficha técnica de inversor cubre varios modelos y el
usuario no ha elegido uno explícitamente.

Ejecutar:
    /tmp/venv/bin/python scripts/test_bloqueo_modelo_inversor.py
(desde bipv_python/)
"""
import os
import sys

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from calculos.seleccion_modelo_inversor import (
    PLACEHOLDER_MODELO,
    debe_bloquear_guardado,
    es_seleccion_valida,
    mensaje_bloqueo,
)

_fallos = []


def _check(cond, desc):
    estado = "OK " if cond else "FALLA"
    print(f"  [{estado}] {desc}")
    if not cond:
        _fallos.append(desc)


def main():
    modelos_multi = ["X3-FORTH 75K", "X3-FORTH 100K", "X3-FORTH 125K"]

    print("• Ficha multi-modelo sin elección → bloquear")
    _check(debe_bloquear_guardado(modelos_multi, None) is True,
           "modelo_elegido=None bloquea")
    _check(debe_bloquear_guardado(modelos_multi, PLACEHOLDER_MODELO) is True,
           "placeholder bloquea")
    _check(debe_bloquear_guardado(modelos_multi, "") is True,
           "cadena vacía bloquea")
    _check(debe_bloquear_guardado(modelos_multi, "   ") is True,
           "solo espacios bloquea")

    print("• Ficha multi-modelo con elección real → permitir")
    _check(debe_bloquear_guardado(modelos_multi, "X3-FORTH 100K") is False,
           "modelo elegido no bloquea")

    print("• Ficha de un solo modelo → nunca bloquear")
    _check(debe_bloquear_guardado(["X1-BOOST 3.0"], None) is False,
           "un modelo + None no bloquea")
    _check(debe_bloquear_guardado(["X1-BOOST 3.0"], PLACEHOLDER_MODELO) is False,
           "un modelo + placeholder no bloquea")

    print("• Sin modelos detectados → nunca bloquear")
    _check(debe_bloquear_guardado([], None) is False, "lista vacía no bloquea")
    _check(debe_bloquear_guardado(None, None) is False, "None no bloquea")

    print("• es_seleccion_valida")
    _check(es_seleccion_valida("X3-FORTH 100K") is True, "modelo real es válido")
    _check(es_seleccion_valida(None) is False, "None no es válido")
    _check(es_seleccion_valida(PLACEHOLDER_MODELO) is False, "placeholder no es válido")
    _check(es_seleccion_valida("  ") is False, "espacios no es válido")

    print("• mensaje_bloqueo incluye el conteo de modelos")
    msg = mensaje_bloqueo(modelos_multi)
    _check("3" in msg and "modelo" in msg.lower(),
           f"mensaje contiene N y 'modelo': {msg!r}")

    print()
    if _fallos:
        print(f"❌ {len(_fallos)} prueba(s) fallida(s).")
        return 1
    print("✅ Todas las pruebas pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
