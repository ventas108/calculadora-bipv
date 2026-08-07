"""Utilidades de UI compartidas entre páginas."""
import streamlit as st
import streamlit.components.v1 as components


def mostrar_proyecto_activo():
    """#63 — Muestra el proyecto activo en la barra lateral de cada página.

    Con multi-proyectos, el usuario necesita saber en todo momento sobre qué
    proyecto está trabajando (y con qué ciudad), sin volver a 🏠 Proyecto.
    """
    _nombre = st.session_state.get("nombre_proyecto")
    if not _nombre:
        return
    _ciudad = st.session_state.get("ciudad", "")
    st.sidebar.markdown(
        f"📁 **{_nombre}**"
        + (f"  \n<span style='color:#888;font-size:0.85em'>📍 {_ciudad}</span>"
           if _ciudad else ""),
        unsafe_allow_html=True,
    )


def bloquear_traduccion():
    """Impide que Google Translate (Chrome) traduzca la app.

    El traductor automático modifica el DOM por fuera de React y provoca
    errores 'NotFoundError: removeChild' al re-renderizar Streamlit.
    La app ya está en español, así que se marca como no traducible.
    Debe llamarse DESPUÉS de st.set_page_config().
    """
    components.html(
        """
        <script>
        try {
            const doc = window.parent.document;
            doc.documentElement.setAttribute('translate', 'no');
            doc.documentElement.classList.add('notranslate');
            if (!doc.querySelector('meta[name="google"][content="notranslate"]')) {
                const meta = doc.createElement('meta');
                meta.name = 'google';
                meta.content = 'notranslate';
                doc.head.appendChild(meta);
            }
        } catch (e) { /* sin permisos: no romper la app */ }
        </script>
        """,
        height=0,
    )
