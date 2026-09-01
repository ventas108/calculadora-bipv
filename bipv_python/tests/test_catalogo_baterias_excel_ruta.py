# -*- coding: utf-8 -*-
"""Hueco #3 de la auditoría de emparentamiento batería↔inversor (1-sep-2026):
`datos/catalogo_baterias_excel.py` tenía el path del Excel hardcodeado SOLO a
la ruta del servidor (`/var/www/bipv/calculadora-bipv/...`), sin el mismo
fallback relativo-al-módulo que `catalogo_inversores_excel.py` ya tiene desde
el 28-ago-2026 -- en cualquier entorno local (como este entorno de tests,
como el CI de GitHub Actions) el catálogo de baterías cargaba vacío en
silencio, sin ningún error visible. `inversores_catalogo.xlsx` sí está
versionado en git (`git ls-files` lo confirma), así que este test funcional
corre igual aquí y en CI -- no depende de simular el entorno."""
import os

from datos.catalogo_baterias_excel import cargar_catalogo_baterias, _EXCEL


def test_ruta_excel_resuelve_al_archivo_del_repo_no_solo_al_del_servidor():
    # Antes del fix, _EXCEL era el string literal fijo al servidor y este
    # archivo (que sí existe en el repo, versionado) nunca se probaba.
    assert os.path.exists(_EXCEL), (
        f"_EXCEL no resuelve a un archivo real en este entorno: {_EXCEL!r}"
    )


def test_catalogo_baterias_carga_datos_reales_en_entorno_local():
    # Antes del fix: 0 baterías cargadas en cualquier entorno que no fuera
    # el servidor de producción exacto -- verificado en vivo antes de este
    # cambio (cargar_catalogo_baterias() devolvía {} en este mismo entorno).
    cat = cargar_catalogo_baterias()
    assert len(cat) > 0
    # Ancla a un modelo real conocido del catálogo, no solo a "no está vacío".
    assert "BR172R" in cat


def test_ruta_excel_mantiene_fallback_al_servidor_para_produccion():
    # El servidor SIEMPRE ejecuta con __file__ dentro de
    # /var/www/bipv/calculadora-bipv/bipv_python/datos/ -- ahí la ruta
    # relativa ya resuelve al mismo path que el fallback histórico, así que
    # el fallback nunca cambia el comportamiento en producción (mismo path
    # de siempre). Se verifica que el fallback siga presente en el código
    # por si algún día el layout del servidor cambia.
    src = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "datos", "catalogo_baterias_excel.py"),
        encoding="utf-8",
    ).read()
    assert '"/var/www/bipv/calculadora-bipv/bipv_python/datos/inversores_catalogo.xlsx"' in src
