"""
seleccion_modelo_inversor.py
Lógica pura (sin Streamlit) para decidir si el guardado en el catálogo de
inversores debe bloquearse cuando una ficha técnica cubre varios modelos.

Regla de negocio (Tarea #138):
  Si la ficha detecta ≥ 2 modelos y el usuario NO ha elegido explícitamente
  uno, hay que DESHABILITAR el botón Guardar para evitar que el catálogo se
  llene con los valores del modelo equivocado (el primero de la lista).

Se aísla aquí para poder testearla sin levantar la UI de Streamlit y para que
las páginas 15 y 16 compartan exactamente la misma decisión.
"""

# Valor centinela que las páginas usan como primera opción del selectbox para
# forzar una elección explícita del usuario (no un modelo por defecto).
PLACEHOLDER_MODELO = "— Elige un modelo —"


def es_seleccion_valida(modelo_elegido) -> bool:
    """Retorna True si `modelo_elegido` representa una elección real (no el
    placeholder ni un valor vacío)."""
    if modelo_elegido is None:
        return False
    txt = str(modelo_elegido).strip()
    if not txt:
        return False
    if txt == PLACEHOLDER_MODELO:
        return False
    return True


def debe_bloquear_guardado(modelos_detectados, modelo_elegido) -> bool:
    """
    Decide si el botón Guardar debe estar DESHABILITADO.

    Args:
        modelos_detectados: lista de modelos detectados en la ficha (o None).
        modelo_elegido:     modelo seleccionado por el usuario (o None / placeholder).

    Returns:
        True  → bloquear guardado (ficha multi-modelo sin elección explícita).
        False → permitir guardado.
    """
    modelos = modelos_detectados or []
    if len(modelos) >= 2:
        return not es_seleccion_valida(modelo_elegido)
    return False


def mensaje_bloqueo(modelos_detectados) -> str:
    """Mensaje claro para el usuario cuando el guardado está bloqueado."""
    n = len(modelos_detectados or [])
    return (
        f"Elige el modelo antes de guardar — la ficha contiene {n} modelos."
    )
