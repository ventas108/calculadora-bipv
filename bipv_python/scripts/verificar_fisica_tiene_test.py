# -*- coding: utf-8 -*-
"""Regla: "fórmula física nueva = test de validación obligatorio en el mismo PR".

Verifica que, si un PR toca alguno de los archivos que implementan
constantes o fórmulas físicas del SDM (Rsh, coeficientes térmicos, De Soto
2006, Mermoud/PVsyst...), ese MISMO PR también toca al menos uno de los
tests que validan esas fórmulas contra una referencia real.

Motivación (25-ago-2026): el bug de Rsh sin saturar y el de Vmp con el
coeficiente térmico equivocado (PR #38) llevaban tiempo en el código sin
que nadie actualizara/revisara su test de referencia -- esta regla evita
que se repita: no impide el cambio, exige que su prueba de exactitud viaje
en el mismo PR, no "después".

Uso (en CI): python scripts/verificar_fisica_tiene_test.py --base <ref_base>
Sale con código 1 y un mensaje explicativo si la regla se incumple.
Se ejecuta solo en pull_request -- un push directo a main (ya fusionado)
no tiene "el mismo PR" contra el cual comparar.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

# Archivos que implementan constantes/fórmulas físicas del SDM. Si el PR
# toca cualquiera de estos, debe traer también al menos uno de los tests
# de ARCHIVOS_VALIDACION en el mismo diff.
ARCHIVOS_FISICOS = (
    "bipv_python/calculos/modelo_iv.py",
    "bipv_python/calculos/produccion.py",
    "bipv_python/calculos/produccion_iv.py",
    "bipv_python/calculos/mismatch_bypass.py",
    "bipv_python/calculos/mppt_combinado.py",
    "bipv_python/calculos/dimensionamiento.py",
    "bipv_python/datos/tecnologias_bipv.py",
)

# Tests que validan esas fórmulas contra una referencia auditada real (no
# contra sí mismas). Tocar cualquiera de estos cuenta como "trajo su test".
ARCHIVOS_VALIDACION = (
    "bipv_python/tests/test_validacion_vba.py",
    "bipv_python/tests/test_calcular_rsh_cdte.py",
    "bipv_python/tests/test_consistencia_sdm_entre_modulos.py",
)


def _archivos_modificados(base: str, head: str = "HEAD") -> list[str]:
    salida = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [l.strip() for l in salida.splitlines() if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True,
                    help="Ref/SHA de la rama base a comparar (ej. origin/main)")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()

    modificados = _archivos_modificados(args.base, args.head)
    tocó_fisica = [f for f in modificados if f in ARCHIVOS_FISICOS]
    tocó_validacion = any(f in ARCHIVOS_VALIDACION for f in modificados)

    if tocó_fisica and not tocó_validacion:
        print(
            "❌ Este PR modifica archivo(s) con fórmulas/constantes físicas del "
            "SDM, pero no toca ninguno de sus tests de validación:\n"
            + "\n".join(f"   - {f}" for f in tocó_fisica)
            + "\n\nAgrega o actualiza en ESTE MISMO PR al menos uno de:\n"
            + "\n".join(f"   - {f}" for f in ARCHIVOS_VALIDACION)
            + "\n\nRegla adoptada el 25-ago-2026 tras el bug de Rsh sin saturar / "
              "Vmp con coeficiente térmico equivocado (PR #38): una fórmula física "
              "sin su test de referencia en el mismo cambio es exactamente cómo "
              "ese bug pasó desapercibido tanto tiempo."
        )
        return 1

    if tocó_fisica:
        print("✅ Toca fórmula(s) física(s) y también su test de validación:")
        for f in tocó_fisica:
            print(f"   - {f}")
    else:
        print("✅ No se modificó ninguna fórmula/constante física del SDM.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
