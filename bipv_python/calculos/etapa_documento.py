# -*- coding: utf-8 -*-
"""Etapa del documento del 📄 Reporte: etiqueta y aviso del encabezado.

Spec ``07-informes/etapa-documento`` (2-oct-2026). El reporte llevaba
«BORRADOR» fijo y un aviso dirigido al diseñador («Verifique los datos de
entrada antes de presentarlo al cliente») que terminaba en manos del
cliente. El diseñador elige la etapa; la etiqueta y el aviso (escritos para
el cliente, salvo el borrador interno) salen de aquí. El Word y el PDF se
arman desde el mismo HTML, así que heredan el encabezado. Módulo puro.
"""
from __future__ import annotations

import html as _html

ETAPA_DEFECTO = "prefactibilidad"

# Orden = orden del selector. «color» = (fondo, texto) de la etiqueta.
ETAPAS: dict[str, dict] = {
    "prefactibilidad": {
        "nombre": "Estudio de prefactibilidad",
        "etiqueta": "ESTUDIO DE PREFACTIBILIDAD",
        "icono": "📋",
        "aviso": (
            "Estudio de prefactibilidad elaborado con simulación hora a hora del recurso solar "
            "del sitio, modelo eléctrico de cada módulo y pérdidas reales de cableado. Los "
            "valores definitivos se confirman en la ingeniería de detalle, después de la visita "
            "técnica al sitio."
        ),
        "color": ("#e3eef9", "#1a569a"),
    },
    "propuesta": {
        "nombre": "Propuesta técnica",
        "etiqueta": "PROPUESTA TÉCNICA",
        "icono": "📋",
        "aviso": (
            "Propuesta técnica basada en simulación hora a hora del recurso solar del sitio y "
            "en el modelo eléctrico de los equipos ofertados. Las cantidades y el rendimiento "
            "se confirman en la ingeniería de detalle y la visita técnica."
        ),
        "color": ("#e3eef9", "#1a569a"),
    },
    "conceptual": {
        "nombre": "Diseño conceptual",
        "etiqueta": "DISEÑO CONCEPTUAL",
        "icono": "📐",
        "aviso": (
            "Diseño conceptual de la integración fotovoltaica en la edificación, con simulación "
            "hora a hora del recurso solar y del sistema eléctrico. La ingeniería de detalle "
            "definirá el montaje, las protecciones y el cableado definitivos."
        ),
        "color": ("#eaf7f0", "#16835d"),
    },
    "revision_cliente": {
        "nombre": "Versión para revisión del cliente",
        "etiqueta": "VERSIÓN PARA REVISIÓN DEL CLIENTE",
        "icono": "📝",
        "aviso": (
            "Versión para su revisión. Agradecemos sus comentarios sobre los supuestos y el "
            "alcance para emitir la versión final del estudio."
        ),
        "color": ("#fff3e3", "#a75a10"),
    },
    "borrador": {
        "nombre": "Borrador interno",
        "etiqueta": "BORRADOR INTERNO",
        "icono": "⚠️",
        "aviso": (
            "Este reporte es preliminar y fue generado automáticamente por la Calculadora BIPV "
            "Colombia. Verifique los datos de entrada antes de presentarlo al cliente."
        ),
        "color": ("#fdebd0", "#d35400"),
    },
}


def encabezado_etapa(clave: str | None) -> tuple[str, str]:
    """(etiqueta HTML junto al título, recuadro de aviso HTML) de la etapa."""
    e = ETAPAS.get(clave or "", ETAPAS[ETAPA_DEFECTO])
    fondo, texto = e["color"]
    etiqueta = _html.escape(e["etiqueta"])
    badge = (f'<span class="badge" style="background:{fondo};color:{texto};">{etiqueta}</span>')
    aviso = (f'<div class="aviso-etapa">{e["icono"]} <strong>{etiqueta}:</strong> '
             f'{_html.escape(e["aviso"])}</div>')
    return badge, aviso
