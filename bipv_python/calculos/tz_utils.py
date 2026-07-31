"""
Utilidades de zona horaria para visualización solar — América Latina y Caribe.

IMPORTANTE: los cálculos físicos de pvlib permanecen siempre en UTC.
Este módulo solo afecta las ETIQUETAS de visualización (ejes de heatmaps,
texto de hover en diagramas solares).  No convierte datos de irradiancia.

Cobertura: Colombia, Ecuador, Perú, Venezuela, Bolivia, Chile, Argentina,
Brasil, Paraguay, Uruguay, México, Centroamérica y Caribe.
"""


def utc_offset_latam(lat: float, lon: float) -> int:
    """
    Retorna el offset UTC estimado en horas enteras para la ubicación dada.

    Parámetros
    ----------
    lat, lon : coordenadas decimales (positivo = Norte/Este)

    Retorna
    -------
    int: offset en horas (p. ej. -5 para Colombia, -3 para Argentina)

    Nota: no maneja horario de verano (DST) — en América Latina la mayoría
    de países no aplica DST o lo aplica de forma irregular.  Para proyectos
    BIPV el efecto es < 1 h y no afecta el análisis energético anual.
    """

    # ── Cono Sur ─────────────────────────────────────────────────────────────
    # Argentina, Uruguay: UTC-3
    if lat <= -22 and -75 <= lon <= -48:
        return -3

    # Chile continental: UTC-4 (oficial sin DST)
    if lat <= -17 and -76 <= lon <= -65:
        return -4

    # Paraguay: UTC-4
    if -28 <= lat <= -14 and -63 <= lon <= -54:
        return -4

    # ── Brasil ───────────────────────────────────────────────────────────────
    # Brasil extremo oeste (Acre): UTC-5
    if -12 <= lat <= -6 and -74 <= lon <= -68:
        return -5

    # Brasil oeste / Amazonas: UTC-4
    if -15 <= lat <= 5 and -68 <= lon <= -50:
        return -4

    # Brasil leste (Brasilia, São Paulo, Rio): UTC-3
    if -35 <= lat <= 6 and -50 <= lon <= -32:
        return -3

    # ── Andina ───────────────────────────────────────────────────────────────
    # Bolivia: UTC-4
    if -23 <= lat <= -8 and -70 <= lon <= -56:
        return -4

    # Colombia, Ecuador, Perú, Panamá: UTC-5
    if -18 <= lat <= 12 and -82 <= lon <= -66:
        return -5

    # Venezuela: UTC-4
    if 0 <= lat <= 13 and -73 <= lon <= -59:
        return -4

    # ── Centroamérica ────────────────────────────────────────────────────────
    # Guatemala, Honduras, El Salvador, Nicaragua, Costa Rica: UTC-6
    if 7 <= lat <= 18 and -92 <= lon <= -82:
        return -6

    # Belice: UTC-6
    if 15 <= lat <= 19 and -90 <= lon <= -87:
        return -6

    # ── Caribe ───────────────────────────────────────────────────────────────
    # Cuba, Jamaica, Haití, República Dominicana: UTC-5
    if 17 <= lat <= 24 and -85 <= lon <= -68:
        return -5

    # Puerto Rico, Islas Vírgenes: UTC-4
    if 17 <= lat <= 19 and -68 <= lon <= -64:
        return -4

    # ── México ───────────────────────────────────────────────────────────────
    # México zona sureste (Quintana Roo — sin DST): UTC-5
    if 18 <= lat <= 22 and -88 <= lon <= -86:
        return -5

    # México zona central y sur (la mayoría): UTC-6
    if 14 <= lat <= 32 and -102 <= lon <= -85:
        return -6

    # México noroeste (Sonora — sin DST): UTC-7
    if 26 <= lat <= 33 and -115 <= lon <= -108:
        return -7

    # México Baja California: UTC-8
    if 22 <= lat <= 33 and -118 <= lon <= -115:
        return -8

    # ── Fallback: aproximación geométrica por longitud ────────────────────────
    return int(round(lon / 15))


def tz_label(offset: int) -> str:
    """Retorna etiqueta legible del offset.  Ej: -5 → 'UTC-5', 0 → 'UTC'."""
    if offset == 0:
        return "UTC"
    sign = "+" if offset > 0 else "-"
    return f"UTC{sign}{abs(offset)}"


def hora_local(hora_utc: int, offset: int) -> int:
    """Convierte hora UTC (0-23) a hora local aplicando el offset."""
    return (hora_utc + offset) % 24


def etiquetas_hora_local(offset: int) -> list:
    """
    Retorna lista de 24 etiquetas 'HH:00' en hora local, ordenadas
    de 00:00 a 23:00.  Se usa como eje Y en heatmaps.
    """
    return [f"{h:02d}:00" for h in range(24)]
