"""
Gráfico Plotly de compatibilidad eléctrica string-inversor.

Extraído a un módulo propio (30-ago-2026) porque el mismo gráfico se
visibiliza ahora en dos páginas -- 📊 Producción y 📐 Dimensionamiento -- y
mantener dos copias del código de construcción del gráfico habría arriesgado
exactamente el tipo de bug de coherencia entre módulos que esta app ya
corrigió antes (ver bipv_tipo_instalacion_coherencia): dos lugares mostrando
el mismo caso de forma distinta.

No contiene NINGUNA lógica de verificación eléctrica -- solo dibuja lo que
`calculos.dimensionamiento.curva_electrica_temperatura()` ya calculó.
"""
import plotly.graph_objects as go


def figura_compatibilidad_electrica(
    curva: dict,
    T_frio: float,
    T_real: float,
    T_extremo: float,
) -> go.Figure:
    """
    Construye la figura Voc(T)/Vmp(T) vs. ventana MPPT y límite Vdc máximo,
    a partir del dict que devuelve `curva_electrica_temperatura()`.
    """
    temps = curva["temps"]
    voc_c = curva["voc_curva"]
    vmp_c = curva["vmp_curva"]
    vdc_max = curva.get("vdc_max")
    vmppt_min = curva.get("vmppt_min")
    vmppt_max = curva.get("vmppt_max")
    ev = curva["evaluacion"]
    compatible = ev.get("compatible")

    fig = go.Figure()
    if vmppt_min is not None and vmppt_max is not None:
        fig.add_hrect(
            y0=vmppt_min, y1=vmppt_max,
            fillcolor="#2E7D32", opacity=0.08, line_width=0,
        )
        fig.add_hline(
            y=vmppt_min, line_dash="dash", line_color="#2E7D32",
            annotation_text=f"MPPT mín {vmppt_min:.0f} V", annotation_position="bottom right",
        )
        fig.add_hline(
            y=vmppt_max, line_dash="dash", line_color="#2E7D32",
            annotation_text=f"MPPT máx {vmppt_max:.0f} V", annotation_position="top right",
        )
    if vdc_max is not None:
        fig.add_hline(
            y=vdc_max, line_dash="dot", line_color="#C62828", line_width=2,
            annotation_text=f"Vdc máx {vdc_max:.0f} V", annotation_position="top left",
        )
    fig.add_trace(go.Scatter(
        x=temps, y=voc_c, name="Voc(T)",
        line=dict(color="#1565C0", width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=temps, y=vmp_c, name="Vmp(T)",
        line=dict(color="#EF6C00", width=2.5),
    ))
    color_pts = "#2E7D32" if compatible else ("#C62828" if compatible is False else "#999")
    fig.add_trace(go.Scatter(
        x=[T_frio, T_real, T_extremo],
        y=[ev.get("Voc_frio"), ev.get("Vmp_real"), ev.get("Vmp_extremo")],
        name="Puntos de diseño", mode="markers",
        marker=dict(size=11, color=color_pts, line=dict(width=1.5, color="white")),
    ))
    fig.update_layout(
        xaxis_title="Temperatura de celda (°C)",
        yaxis_title="Tensión (V)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig
