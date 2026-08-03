"""
extractor_inversor_core.py
Núcleo de extracción de texto plano → parámetros de inversor.
Expone `extraer_desde_texto(texto)` para uso directo en tests y debug,
sin necesitar un PDF real.

Delegación total: usa exactamente las mismas funciones que el extractor de
PDFs (`_extraer_campos`, `_extraer_multimodelo`, etc.) para que el harness
sintético ejercite el MISMO código que procesa las fichas reales — incluida
la ruta de folletos de familia (Voltronic).  Así cualquier mejora del
extractor de PDFs queda cubierta automáticamente y ninguna versión puede
quedar rezagada respecto a la otra.
"""
from calculos.pdf_inversor_extractor import (
    _HYBRID_RE,
    _extract_brand, _extract_model, _extract_arch,
    _extraer_campos, _extraer_multimodelo,
)
import re


def extraer_desde_texto(texto: str) -> dict:
    """
    Extrae parámetros de inversor desde texto plano (sin PDF).
    Útil para tests unitarios, debug de datasheets y harness de cobertura.
    """
    # Misma normalización que el extractor de PDFs
    texto = re.sub(r"\s*d\.c\.?\s*", " ", texto)
    texto = re.sub(r"\s*a\.c\.?\s*", " ", texto)
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texto)
    texto = re.sub(r"(\d),(\d{3})(?!\d)", r"\1\2", texto)

    marca        = _extract_brand(texto)
    modelo       = _extract_model(texto, marca)
    arquitectura = _extract_arch(texto)
    es_hibrido   = bool(_HYBRID_RE.search(texto[:2000]))

    campos = _extraer_campos(texto)

    # Multi-modelo: mismo código que el extractor de PDFs (columnas + familias)
    multimodel = _extraer_multimodelo(texto)

    # Si hay P_dc real por modelo, descartar la estimación global (AC × 1.5)
    tiene_pdc_pm = any(
        (v or {}).get("P_dc_max_W") and not (v or {}).get("P_dc_estimado")
        for v in multimodel.get("por_modelo", {}).values()
    )
    if campos.get("P_dc_estimado") and tiene_pdc_pm:
        campos["P_dc_max_W"] = None
        campos["P_dc_estimado"] = False

    campos.pop("P_dc_estimado", None)

    return {
        "modelo": modelo, "marca": marca,
        "arquitectura": arquitectura, "es_hibrido": es_hibrido,
        **campos,
        "modelos_detectados": multimodel.get('modelos', []),
        "valores_por_modelo": multimodel.get('por_modelo', {}),
    }
